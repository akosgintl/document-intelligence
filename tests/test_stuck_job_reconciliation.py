"""Reconciliation sweep for a Job a hard worker crash orphans in `processing` (#32, follow-up
from #27/ADR-0005): a real process kill/OOM landing on exactly a Job's last permitted attempt
never runs any of our code for that attempt, so neither `process_job`'s own `except Exception`
handler nor `mark_job_failed` ever fires — confirmed against `arq`'s source: once a redelivered
job's `job_try` exceeds `max_tries`, `Worker._run_job` short-circuits straight to
`finish_failed_job` without invoking our coroutine at all. `reconcile_stuck_jobs` is the
mechanism that still catches it, independent of any single `process_job` invocation.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import update
from test_walking_skeleton import AUTH_HEADERS, INVOICE_SCHEMA, _n_page_pdf, _poll_until_complete

from document_intelligence.config import get_settings
from document_intelligence.db import Job, JobStatus
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
    PageClassification,
)
from document_intelligence.pipeline import PipelineDeps, mark_job_failed, process_job, reconcile_stuck_jobs
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_s3_client

RECEIPT_SCHEMA = {
    "title": "Receipt",
    "description": "A retail receipt.",
    "type": "object",
    "properties": {
        "merchantName": {"type": "string"},
        "total": {"type": "number"},
    },
    "required": ["merchantName", "total"],
}


class SimulatedCrash(Exception):
    """Raised in place of a worker actually dying, for the attempts that go through
    `process_job` itself — the final, genuinely-hard-crashed attempt is simulated separately
    below by mutating the Job's row directly, since a real process kill never raises anything
    in the crashed process at all."""


class _CrashingProvider:
    def __init__(self, inner: FakeModelProvider, *, succeed_document_classifications: int) -> None:
        self.inner = inner
        self._succeed_document_classifications = succeed_document_classifications
        self._delegated = 0

    async def classify_page(self, *args: Any, **kwargs: Any) -> PageClassification:
        return await self.inner.classify_page(*args, **kwargs)

    async def classify_document(self, *args: Any, **kwargs: Any) -> DocumentClassification:
        if self._delegated < self._succeed_document_classifications:
            self._delegated += 1
            return await self.inner.classify_document(*args, **kwargs)
        raise SimulatedCrash("simulated worker crash during document classification")

    async def extract(self, *args: Any, **kwargs: Any) -> ExtractionResult:
        return await self.inner.extract(*args, **kwargs)


def _write_registry(root: Path) -> SchemaRegistry:
    invoice_dir = root / "invoice"
    invoice_dir.mkdir()
    (invoice_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (invoice_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))

    receipt_dir = root / "receipt"
    receipt_dir.mkdir()
    (receipt_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (receipt_dir / "v1.json").write_text(json.dumps(RECEIPT_SCHEMA))

    return SchemaRegistry.load(root)


async def _go_stale(db_session_factory, job_id: str, *, attempt_count: int, age_seconds: int) -> None:
    """Simulate what a hard crash on the Job's final permitted attempt leaves behind: the
    attempt's own bookkeeping (`attempt_count` bumped, `status` already `processing`) already
    committed before the process died, but nothing else ever ran — no exception, no status
    transition. `updated_at` is pushed back directly (bypassing the ORM's `onupdate`, which
    would just stamp the current time again) so the sweep's staleness check has something to
    compare against without a real clock waiting `age_seconds`.
    """
    async with db_session_factory() as session:
        job = await session.get(Job, uuid.UUID(job_id))
        job.attempt_count = attempt_count
        await session.commit()

        stale_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=age_seconds)
        await session.execute(update(Job).where(Job.id == job.id).values(updated_at=stale_at))
        await session.commit()


async def test_reconcile_marks_a_hard_crashed_final_attempt_failed_with_prior_documents_intact(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    # 2 pages -> 2 Documents. The first Document's classification succeeds; every attempt at
    # the second Document's classification "crashes" — a Job that will exhaust every permitted
    # attempt no matter how many times it's retried.
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice"), PageClassification("receipt")],
        document_classifications=[DocumentClassification("invoice", 1, 0.9)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-1", 0.95),
                    ExtractedField("vendorName", "Acme Corp", 0.9),
                )
            )
        ],
    )
    provider = _CrashingProvider(inner, succeed_document_classifications=1)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(2), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )

        # Exhaust the first 4 (of 5) permitted attempts through `process_job` itself — each one
        # raises `SimulatedCrash`, caught by `process_job`'s own `except Exception` handler,
        # which re-raises without touching the Job's status since `attempt_number` (< 5) hasn't
        # hit the bound yet.
        for _ in range(4):
            try:
                await process_job(deps, job_id)
            except SimulatedCrash:
                pass
            else:
                raise AssertionError("expected SimulatedCrash")

    # The 5th and final permitted attempt is a genuine hard crash, not a raised exception:
    # `process_job` bumped `attempt_count` to 5 and left `status` at `processing` before the
    # process died, and nothing downstream of that (in particular, no exception handler) ever
    # ran. `arq` itself never invokes `process_job` again for this Job past this point.
    await _go_stale(db_session_factory, job_id, attempt_count=5, age_seconds=1000)

    marked = await reconcile_stuck_jobs(db_session_factory, stale_after_seconds=300)
    assert marked == 1

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "failed"

    # The first Document reached a terminal status before the crash and remains visible even
    # though the Job itself is `failed` (matches #27's existing guarantee).
    assert len(result["documents"]) == 1
    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["document_type"] == "invoice"
    assert document["fields"] == {"invoiceNumber": "INV-1", "vendorName": "Acme Corp"}


async def test_reconcile_leaves_a_job_still_within_its_staleness_window_alone(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    inner = FakeModelProvider(page_classifications=[PageClassification(None)])
    provider = _CrashingProvider(inner, succeed_document_classifications=0)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(1), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )
        for _ in range(4):
            try:
                await process_job(deps, job_id)
            except SimulatedCrash:
                pass
            else:
                raise AssertionError("expected SimulatedCrash")

    # attempt_count reaches the bound, but barely any time has passed — an attempt that's
    # still plausibly in flight must never be swept up as abandoned.
    await _go_stale(db_session_factory, job_id, attempt_count=5, age_seconds=1)

    marked = await reconcile_stuck_jobs(db_session_factory, stale_after_seconds=300)
    assert marked == 0

    async with db_session_factory() as session:
        job = await session.get(Job, uuid.UUID(job_id))
        assert job.status == JobStatus.PROCESSING


async def test_reconcile_leaves_a_stale_job_below_the_attempt_bound_alone(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    inner = FakeModelProvider(page_classifications=[PageClassification(None)])
    provider = _CrashingProvider(inner, succeed_document_classifications=0)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(1), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )
        try:
            await process_job(deps, job_id)
        except SimulatedCrash:
            pass
        else:
            raise AssertionError("expected SimulatedCrash")

    # Stale by wall-clock time, but attempt_count (1) is nowhere near the bound (5) — this Job
    # still has legitimate retries left and must be left for `process_job` to pick back up.
    await _go_stale(db_session_factory, job_id, attempt_count=1, age_seconds=1000)

    marked = await reconcile_stuck_jobs(db_session_factory, stale_after_seconds=300)
    assert marked == 0

    async with db_session_factory() as session:
        job = await session.get(Job, uuid.UUID(job_id))
        assert job.status == JobStatus.PROCESSING


async def test_reconcile_is_a_no_op_once_a_job_is_already_failed(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    inner = FakeModelProvider(page_classifications=[PageClassification(None)])
    provider = _CrashingProvider(inner, succeed_document_classifications=0)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(1), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )
        for _ in range(5):
            try:
                await process_job(deps, job_id)
            except SimulatedCrash:
                pass
            else:
                raise AssertionError("expected SimulatedCrash")

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "failed"

    marked = await reconcile_stuck_jobs(db_session_factory, stale_after_seconds=300)
    assert marked == 0


class _ConcurrentlyFailingProvider:
    """Wraps a `FakeModelProvider`; on `classify_document`, simulates the reconciliation sweep
    (#32) marking this Job `failed` out from under a still-genuinely-running attempt -- its
    only proxy for "stuck" is a stale `updated_at` that a single long-running call in the
    attempt's loop never refreshes, so a sweep can fire mid-attempt for a Job that's actually
    about to finish successfully. Exercises `process_job`'s guard against silently reviving a
    Job some other path already gave up on."""

    def __init__(self, inner: FakeModelProvider, *, session_factory, job_id: str) -> None:
        self.inner = inner
        self._session_factory = session_factory
        self._job_id = job_id

    async def classify_page(self, *args: Any, **kwargs: Any) -> PageClassification:
        return await self.inner.classify_page(*args, **kwargs)

    async def classify_document(self, *args: Any, **kwargs: Any) -> DocumentClassification:
        await mark_job_failed(self._session_factory, self._job_id)
        return await self.inner.classify_document(*args, **kwargs)

    async def extract(self, *args: Any, **kwargs: Any) -> ExtractionResult:
        return await self.inner.extract(*args, **kwargs)


async def test_a_job_marked_failed_mid_attempt_is_not_silently_revived_to_complete(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    inner = FakeModelProvider(
        document_classifications=[DocumentClassification("invoice", 1, 0.9)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-1", 0.95),
                    ExtractedField("vendorName", "Acme Corp", 0.9),
                )
            )
        ],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _n_page_pdf(1), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    async with get_s3_client() as s3_client:
        # A single-page Submission skips classify_page entirely (#31) and goes straight to
        # classify_document -- the one call this provider hijacks to inject the concurrent
        # `failed` transition partway through an otherwise-successful attempt.
        provider = _ConcurrentlyFailingProvider(
            inner, session_factory=db_session_factory, job_id=job_id
        )
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )
        await process_job(deps, job_id)

    async with db_session_factory() as session:
        job = await session.get(Job, uuid.UUID(job_id))
        # The attempt's own completion must not overwrite the concurrently-set `failed`
        # status -- once terminal, a Job's status must never flip back.
        assert job.status == JobStatus.FAILED

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "failed"
    # The Document this attempt computed before finishing is still visible even though the
    # Job itself is `failed` (ADR-0005) -- the guard drops only the Job's own status write,
    # not the Document commit that already happened.
    assert len(result["documents"]) == 1
    assert result["documents"][0]["status"] == "extracted"
