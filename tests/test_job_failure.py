"""Job-level `failed` status & crash recovery/idempotency (#27, ADR-0005): a Job whose worker
task keeps failing exhausts a bounded number of attempts (mirroring `arq`'s `max_tries=5`
default) and moves to `failed`, distinct from any Document-level outcome — Documents that
already reached a terminal status stay visible on the Job. A resumed attempt at a Job that
crashed partway through must not repeat a Model Provider call for a Document already
committed by an earlier attempt.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from test_walking_skeleton import AUTH_HEADERS, INVOICE_SCHEMA, _n_page_pdf, _poll_until_complete

from document_intelligence.config import get_settings
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
    PageClassification,
)
from document_intelligence.pipeline import PipelineDeps, process_job
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
    """Raised in place of a worker actually dying, so a test can assert on exactly which
    attempt it happened on without depending on `arq`'s own crash-detection machinery."""


class _CrashingProvider:
    """Wraps a `FakeModelProvider`, letting the first `succeed_document_classifications`
    `classify_document` calls through to it and raising `SimulatedCrash` for every one after
    that — simulating a worker that finishes some Documents fine and then keeps crashing on
    the next one, every time it's retried."""

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


async def test_a_job_exhausting_retries_moves_to_failed_with_prior_documents_intact(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    # 2 pages -> 2 Documents (invoice, then receipt). The first Document's classification is
    # allowed through once; every attempt at the second Document's classification "crashes" —
    # simulating a worker task that keeps failing on this Job no matter how many times it's
    # retried.
    inner = FakeModelProvider(
        # 1 page classification each for the invoice and receipt pages on the first attempt —
        # every retry after that has only the still-unfinished receipt page left, which skips
        # classify_page entirely (#31), so no further page classification response is needed.
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

        # arq's default max_tries is 5: the worker task is invoked (and fails) exactly that
        # many times before the Job is given up on.
        for _ in range(5):
            with pytest.raises(SimulatedCrash):
                await process_job(deps, job_id)

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "failed"

    # The first Document reached a terminal status before the repeated failures and remains
    # visible even though the Job itself is `failed`.
    assert len(result["documents"]) == 1
    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["document_type"] == "invoice"
    assert document["fields"] == {"invoiceNumber": "INV-1", "vendorName": "Acme Corp"}

    # The already-finished Document was never reclassified or re-extracted on any retry.
    assert len(inner.document_classification_calls) == 1
    assert len(inner.extraction_calls) == 1


async def test_a_requeue_after_partial_completion_does_not_repeat_provider_calls(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
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
    first_attempt_provider = _CrashingProvider(inner, succeed_document_classifications=1)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(2), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    async with get_s3_client() as s3_client:
        # Simulate a crash right after the first Document (page 1, invoice) committed: the
        # second Document's classification "crashes" every time it's attempted.
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=first_attempt_provider,
            schema_registry=registry,
        )
        with pytest.raises(SimulatedCrash):
            await process_job(deps, job_id)

        # The resumed attempt gets a *different* Provider double that only knows about the
        # second Document's Page — if the implementation tried to re-render/reclassify the
        # first Document's Page, this Provider's scripted responses (for the receipt Page
        # only) would be consumed out of order or exhausted, and its own call log (asserted
        # below) would show more than the one remaining Document's worth of calls. The single
        # remaining Page also means classify_page is skipped entirely (#31), so its scripted
        # response is never consumed.
        resumed_provider = FakeModelProvider(
            page_classifications=[PageClassification("receipt")],
            document_classifications=[DocumentClassification("receipt", 1, 0.95)],
            extractions=[
                ExtractionResult(
                    (
                        ExtractedField("merchantName", "Corner Store", 0.93),
                        ExtractedField("total", 12.5, 0.88),
                    )
                )
            ],
        )
        resumed_deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=resumed_provider,
            schema_registry=registry,
        )
        await process_job(resumed_deps, job_id)

    assert len(resumed_provider.page_classification_calls) == 0
    assert len(resumed_provider.document_classification_calls) == 1
    assert len(resumed_provider.extraction_calls) == 1

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    assert len(result["documents"]) == 2

    documents_by_type = {document["document_type"]: document for document in result["documents"]}
    assert documents_by_type["invoice"]["status"] == "extracted"
    assert documents_by_type["invoice"]["fields"] == {
        "invoiceNumber": "INV-1",
        "vendorName": "Acme Corp",
    }
    assert documents_by_type["receipt"]["status"] == "extracted"
    assert documents_by_type["receipt"]["fields"] == {
        "merchantName": "Corner Store",
        "total": 12.5,
    }


async def test_a_requeued_task_for_an_already_failed_job_is_a_no_op(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    inner = FakeModelProvider(page_classifications=[PageClassification(None)])
    # Every classify_document call crashes from the start — the one Document this Submission
    # produces never gets past classification.
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
            with pytest.raises(SimulatedCrash):
                await process_job(deps, job_id)

        result = await _poll_until_complete(api_client, job_id)
        assert result["status"] == "failed"

        # A further requeue against the now-`failed` Job must be a safe no-op: no further
        # Model Provider calls at all.
        calls_before = len(inner.page_classification_calls)
        await process_job(deps, job_id)
        assert len(inner.page_classification_calls) == calls_before

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "failed"
