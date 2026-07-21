"""Confidence & Review (#26): a Document's Classification/Extraction Confidence below its
Document Type's Confidence Threshold routes it to `classification_needs_review`/
`extraction_needs_review` instead of its usual terminal status; `POST
/v1/documents/{document_id}/review` resolves it per ADR-0003, driven entirely through the
public HTTP API plus a real `arq` worker, with only the Model Provider swapped for
`FakeModelProvider` — per this repo's Testing Decisions.
"""

import json
import uuid
from pathlib import Path

from test_walking_skeleton import (
    AUTH_HEADERS,
    INVOICE_SCHEMA,
    _one_page_pdf,
    _poll_until_complete,
    _run_worker,
)

from document_intelligence.config import get_settings
from document_intelligence.db import Document
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
    PageClassification,
)
from document_intelligence.schema_registry import SchemaRegistry


def _write_registry(root: Path, *, confidence_threshold: float = 0.8) -> SchemaRegistry:
    type_dir = root / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": confidence_threshold}))
    (type_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    return SchemaRegistry.load(root)


async def _submit_and_run(api_client, db_session_factory, registry, provider) -> str:
    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]
    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )
    return job_id


def _use_registry_dir(monkeypatch, tmp_path) -> None:
    """Point the API's per-request `SchemaRegistry` (`api/deps.get_schema_registry`) at the
    same directory a test's worker-side one was built from, so the review endpoint's Document
    Type/threshold lookups agree with whatever classified/extracted the Document."""
    monkeypatch.setenv("SCHEMA_REGISTRY_DIR", str(tmp_path))
    get_settings.cache_clear()


# --- Confidence gating during automated processing --------------------------------------


async def test_low_confidence_classification_lands_in_classification_needs_review(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.9)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.5)],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"

    document = result["documents"][0]
    assert document["status"] == "classification_needs_review"
    assert document["document_type"] == "invoice"
    assert document["schema_version"] == 1
    assert document["fields"] is None
    assert len(provider.extraction_calls) == 0


async def test_high_confidence_classification_still_proceeds_to_extraction(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.8)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-100", 0.97),
                    ExtractedField("vendorName", "Acme Corp", 0.92),
                )
            )
        ],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)

    result = await _poll_until_complete(api_client, job_id)
    document = result["documents"][0]
    assert document["status"] == "extracted"


async def test_low_confidence_field_lands_in_extraction_needs_review(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.8)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-100", 0.97),
                    ExtractedField("vendorName", "Acme Corp", 0.4),
                )
            )
        ],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"

    document = result["documents"][0]
    assert document["status"] == "extraction_needs_review"
    assert document["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}


# --- Review resolution: classification_needs_review --------------------------------------


async def test_review_resolves_classification_needs_review_then_proceeds_to_extraction(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.9)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.5)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-100", 0.97),
                    ExtractedField("vendorName", "Acme Corp", 0.92),
                )
            )
        ],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]
    assert result["documents"][0]["status"] == "classification_needs_review"
    assert result["status"] == "complete"

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"document_type": "invoice"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "classified"
    assert len(provider.extraction_calls) == 0  # extraction is queued, not run inline

    # The review's queued extraction runs on the next worker pass.
    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}
    assert len(provider.extraction_calls) == 1
    # Resolving after the Job already reached `complete` must never reopen it.
    assert result["status"] == "complete"


async def test_review_confirms_unclassified(api_client, db_session_factory, tmp_path, monkeypatch):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.9)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.5)],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"document_type": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unclassified"
    assert body["document_type"] is None
    assert body["schema_version"] is None

    result = await _poll_until_complete(api_client, job_id)
    assert result["documents"][0]["status"] == "unclassified"

    # Matches Document.classification_confidence's documented invariant: null whenever
    # there's no Document Type left to have been confident about.
    async with db_session_factory() as session:
        document = await session.get(Document, uuid.UUID(document_id))
        assert document.classification_confidence is None


async def test_review_unknown_document_type_is_rejected(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.9)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.5)],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"document_type": "not-a-real-type"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_submission"


# --- Review resolution: extraction_needs_review / extraction_failed ----------------------


async def test_review_resolves_extraction_needs_review_with_field_replacement(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.8)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-100", 0.97),
                    ExtractedField("vendorName", "Acme Corp", 0.4),
                )
            )
        ],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]
    assert result["documents"][0]["status"] == "extraction_needs_review"

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"fields": {"invoiceNumber": "INV-100", "vendorName": "Corrected Vendor"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "extracted"
    # A full replacement, not a merge: the old low-confidence value is gone.
    assert body["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Corrected Vendor"}

    result = await _poll_until_complete(api_client, job_id)
    assert result["documents"][0]["fields"] == {
        "invoiceNumber": "INV-100",
        "vendorName": "Corrected Vendor",
    }


async def test_review_resolves_extraction_failed_with_field_replacement(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.8)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        # missing vendorName -> validation fails on both automated attempts
        extractions=[ExtractionResult((ExtractedField("invoiceNumber", "INV-100", 0.97),))],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]
    assert result["documents"][0]["status"] == "extraction_failed"

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"fields": {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "extracted"


async def test_review_extraction_resolution_with_invalid_fields_fails_with_no_retry(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.8)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[ExtractionResult((ExtractedField("invoiceNumber", "INV-100", 0.97),))],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]
    assert result["documents"][0]["status"] == "extraction_failed"
    assert len(provider.extraction_calls) == 2

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"fields": {"invoiceNumber": "INV-100"}},  # still missing vendorName
    )
    assert response.status_code == 200
    assert response.json()["status"] == "extraction_failed"
    # No Model Provider round-trip for a Review resolution — no retry either.
    assert len(provider.extraction_calls) == 2


# --- Error paths --------------------------------------------------------------------------


async def test_review_on_non_resolvable_document_returns_409(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.8)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-100", 0.97),
                    ExtractedField("vendorName", "Acme Corp", 0.92),
                )
            )
        ],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]
    assert result["documents"][0]["status"] == "extracted"

    response = await api_client.post(
        f"/v1/documents/{document_id}/review",
        headers=AUTH_HEADERS,
        json={"fields": {"invoiceNumber": "INV-999", "vendorName": "Acme Corp"}},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_review_missing_required_key_for_current_status_is_rejected(
    api_client, db_session_factory, tmp_path, monkeypatch
):
    _use_registry_dir(monkeypatch, tmp_path)
    registry = _write_registry(tmp_path, confidence_threshold=0.9)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.5)],
    )

    job_id = await _submit_and_run(api_client, db_session_factory, registry, provider)
    result = await _poll_until_complete(api_client, job_id)
    document_id = result["documents"][0]["document_id"]
    assert result["documents"][0]["status"] == "classification_needs_review"

    response = await api_client.post(
        f"/v1/documents/{document_id}/review", headers=AUTH_HEADERS, json={"fields": {}}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_submission"


async def test_review_unknown_document_returns_404(api_client, db_session_factory):
    response = await api_client.post(
        "/v1/documents/00000000-0000-0000-0000-000000000000/review",
        headers=AUTH_HEADERS,
        json={"document_type": None},
    )
    assert response.status_code == 404


async def test_review_requires_api_key(api_client, db_session_factory):
    response = await api_client.post(
        "/v1/documents/00000000-0000-0000-0000-000000000000/review",
        json={"document_type": None},
    )
    assert response.status_code == 401
