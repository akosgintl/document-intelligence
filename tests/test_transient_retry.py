"""Transient Provider error retry/backoff + exhaustion routing (#28, ADR-0009): a rate limit,
network failure, or 5xx is retried up to 3 attempts total with exponential backoff, applied
uniformly at the Provider-interface seam. A Document whose document-level Classification or
Extraction call exhausts that budget routes into `classification_needs_review`/
`extraction_needs_review` — the existing needs_review statuses from #26 — rather than a new
status, and never escalates to Job-level `failed`.
"""

import json
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from test_walking_skeleton import (
    AUTH_HEADERS,
    INVOICE_SCHEMA,
    _n_page_pdf,
    _one_page_pdf,
    _poll_until_complete,
    _run_worker,
)

from document_intelligence.db import ModelCall
from document_intelligence.model_provider.errors import TransientProviderError
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.retry import RetryingModelProvider, compute_backoff_seconds
from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractedField,
    ExtractionResult,
    Page,
    PageClassification,
)
from document_intelligence.schema_registry import SchemaRegistry

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

_VALID_EXTRACTION = ExtractionResult(
    (ExtractedField("invoiceNumber", "INV-100", 0.97), ExtractedField("vendorName", "Acme Corp", 0.92))
)

INVOICE = DocumentTypeSchema(name="invoice", schema_version=1, json_schema=INVOICE_SCHEMA)
PAGE = Page(image_bytes=b"fake-bytes", media_type="image/png")


async def _no_delay(_seconds: float) -> None:
    """Stands in for the real backoff sleep so retry tests run instantly."""


def _recording_sleep(sleeps: list[float]):
    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    return sleep


def _write_invoice_registry(root: Path, *, confidence_threshold: float = 0.8) -> SchemaRegistry:
    type_dir = root / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": confidence_threshold}))
    (type_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    return SchemaRegistry.load(root)


def _write_invoice_and_receipt_registry(root: Path) -> SchemaRegistry:
    invoice_dir = root / "invoice"
    invoice_dir.mkdir()
    (invoice_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (invoice_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))

    receipt_dir = root / "receipt"
    receipt_dir.mkdir()
    (receipt_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (receipt_dir / "v1.json").write_text(json.dumps(RECEIPT_SCHEMA))

    return SchemaRegistry.load(root)


# --- Pure backoff logic --------------------------------------------------------------------


def test_compute_backoff_seconds_honors_retry_after_exactly():
    assert compute_backoff_seconds(attempt_number=1, retry_after=7.5) == 7.5
    assert compute_backoff_seconds(attempt_number=2, retry_after=0.1) == 0.1


def test_compute_backoff_seconds_doubles_from_one_second_when_no_retry_after():
    first = compute_backoff_seconds(attempt_number=1, retry_after=None)
    second = compute_backoff_seconds(attempt_number=2, retry_after=None)

    assert 0.5 <= first <= 1.0
    assert 1.0 <= second <= 2.0


def test_compute_backoff_seconds_caps_at_ten_seconds():
    far_attempt = compute_backoff_seconds(attempt_number=10, retry_after=None)

    assert 5.0 <= far_attempt <= 10.0


# --- RetryingModelProvider, tested directly against the fake --------------------------------


async def test_a_transient_error_that_resolves_within_budget_returns_the_eventual_success():
    inner = FakeModelProvider(
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        document_classification_transient_errors=2,
    )
    sleeps: list[float] = []
    provider = RetryingModelProvider(inner, sleep=_recording_sleep(sleeps))

    result = await provider.classify_document([PAGE], [INVOICE])

    assert result == DocumentClassification("invoice", 1, 0.95)
    # Two failed attempts, then a third that succeeds.
    assert len(inner.document_classification_calls) == 3
    # Slept between attempts 1->2 and 2->3 only — never after the final success.
    assert len(sleeps) == 2


async def test_a_transient_error_that_exhausts_the_budget_raises_after_three_attempts():
    inner = FakeModelProvider(document_classification_transient_errors=3)
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    with pytest.raises(TransientProviderError):
        await provider.classify_document([PAGE], [INVOICE])

    assert len(inner.document_classification_calls) == 3


async def test_the_retry_policy_covers_page_classification_too():
    """The retry policy is applied uniformly at the Provider-interface seam (#28) — page
    Classification gets it exactly like document Classification and Extraction, even though
    (per CONTEXT.md) only document-level Classification/Extraction exhaustion routes a
    Document to needs_review."""
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        page_classification_transient_errors=2,
    )
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    result = await provider.classify_page(PAGE, [INVOICE])

    assert result == PageClassification("invoice")
    assert len(inner.page_classification_calls) == 3


class _RateLimitedThenFakeProvider:
    """Raises a `TransientProviderError` carrying a `Retry-After` hint on the first
    `classify_document` call, then delegates to a real `FakeModelProvider` — so a test can
    assert the hint reaches the sleep call unmodified."""

    def __init__(self, inner: FakeModelProvider, *, retry_after: float) -> None:
        self._inner = inner
        self._retry_after = retry_after
        self._raised = False

    async def classify_document(
        self, pages: Sequence[Page], document_types: Sequence[DocumentTypeSchema]
    ) -> DocumentClassification:
        if not self._raised:
            self._raised = True
            raise TransientProviderError("rate limited", retry_after=self._retry_after)
        return await self._inner.classify_document(pages, document_types)

    async def classify_page(self, *args: Any, **kwargs: Any) -> PageClassification:
        return await self._inner.classify_page(*args, **kwargs)

    async def extract(self, *args: Any, **kwargs: Any) -> ExtractionResult:
        return await self._inner.extract(*args, **kwargs)


async def test_a_retry_after_hint_is_passed_through_to_the_sleep_call():
    """A 429's `Retry-After` (ADR-0009) is honored exactly, not folded into the exponential
    backoff — asserted here with a Retry-After far outside the ~1s exponential value attempt 1
    would otherwise produce."""
    inner = FakeModelProvider(document_classifications=[DocumentClassification("invoice", 1, 0.95)])
    provider = _RateLimitedThenFakeProvider(inner, retry_after=5.0)
    sleeps: list[float] = []
    retrying_provider = RetryingModelProvider(provider, sleep=_recording_sleep(sleeps))

    result = await retrying_provider.classify_document([PAGE], [INVOICE])

    assert result == DocumentClassification("invoice", 1, 0.95)
    assert sleeps == [5.0]


# --- End-to-end via the real pipeline: document Classification ------------------------------


async def test_document_classification_transient_error_resolves_within_budget(
    api_client, db_session_factory, tmp_path
):
    registry = _write_invoice_registry(tmp_path)
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[_VALID_EXTRACTION],
        document_classification_transient_errors=2,
    )
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(session_factory=db_session_factory, schema_registry=registry, model_provider=provider)

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}
    assert len(inner.document_classification_calls) == 3


async def test_document_classification_exhausting_the_budget_routes_to_needs_review(
    api_client, db_session_factory, tmp_path
):
    registry = _write_invoice_and_receipt_registry(tmp_path)
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice"), PageClassification("receipt")],
        # The first boundary's classify_document call exhausts its retry budget entirely
        # (3 transient errors scripted); the second boundary's call then proceeds normally
        # against the remaining scripted response.
        document_classifications=[DocumentClassification("receipt", 1, 0.9)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("merchantName", "Corner Store", 0.93),
                    ExtractedField("total", 12.5, 0.88),
                )
            )
        ],
        document_classification_transient_errors=3,
    )
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(2), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(session_factory=db_session_factory, schema_registry=registry, model_provider=provider)

    result = await _poll_until_complete(api_client, job_id)
    # The Job completes even though one Document's Provider exhaustion happened along the way
    # — a single Document's exhaustion never escalates to Job-level `failed` (ADR-0009).
    assert result["status"] == "complete"
    assert len(result["documents"]) == 2

    first, second = result["documents"]
    assert first["status"] == "classification_needs_review"
    assert first["document_type"] is None
    assert first["schema_version"] is None
    assert first["fields"] is None

    # The other Document in the same Job is unaffected and processes normally.
    assert second["status"] == "extracted"
    assert second["document_type"] == "receipt"
    assert second["fields"] == {"merchantName": "Corner Store", "total": 12.5}


# --- End-to-end via the real pipeline: Extraction -------------------------------------------


async def test_extraction_transient_error_resolves_within_budget(api_client, db_session_factory, tmp_path):
    registry = _write_invoice_registry(tmp_path)
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[_VALID_EXTRACTION],
        extraction_transient_errors=2,
    )
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(session_factory=db_session_factory, schema_registry=registry, model_provider=provider)

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}
    assert len(inner.extraction_calls) == 3


async def test_extraction_exhausting_the_budget_routes_to_needs_review(
    api_client, db_session_factory, tmp_path
):
    registry = _write_invoice_registry(tmp_path)
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extraction_transient_errors=3,
    )
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(session_factory=db_session_factory, schema_registry=registry, model_provider=provider)

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    document = result["documents"][0]
    # Classified successfully first (Confidence above threshold) — only Extraction's own
    # transient-error budget was exhausted, so the Document already has its Document Type.
    assert document["document_type"] == "invoice"
    assert document["status"] == "extraction_needs_review"
    assert document["fields"] == {}
    assert len(inner.extraction_calls) == 3


# --- Observability: each retry attempt is persisted -----------------------------------------


async def test_failed_transient_attempts_are_persisted_via_the_observability_layer(
    api_client, db_session_factory, tmp_path
):
    registry = _write_invoice_registry(tmp_path)
    inner = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[_VALID_EXTRACTION],
        extraction_transient_errors=2,
    )
    provider = RetryingModelProvider(inner, sleep=_no_delay)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = uuid.UUID(response.json()["job_id"])

    await _run_worker(session_factory=db_session_factory, schema_registry=registry, model_provider=provider)

    async with db_session_factory() as session:
        result = await session.execute(
            select(ModelCall)
            .where(ModelCall.job_id == job_id, ModelCall.call_type == "extraction")
            .order_by(ModelCall.created_at)
        )
        calls = result.scalars().all()

    # Two failed transient attempts, persisted here, plus the eventual success, persisted by
    # the wrapped Provider itself exactly like any other completed call (#22).
    assert len(calls) == 3
    assert calls[0].input_tokens is None
    assert calls[1].input_tokens is None
    assert calls[2].input_tokens is not None
