"""Extraction validation retry & `extraction_failed` (#24): a Schema validation failure is
retried exactly once with the validation errors fed back into the prompt; a second failure
lands the Document in `extraction_failed` rather than retrying unboundedly.
"""

import json
from pathlib import Path

from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
    PageClassification,
)
from document_intelligence.pipeline import (
    ExtractionDecision,
    decide_extraction,
    extraction_validation_errors,
)
from document_intelligence.schema_registry import SchemaRegistry
from test_walking_skeleton import AUTH_HEADERS, INVOICE_SCHEMA, _one_page_pdf, _run_worker

_VALID = ExtractionResult(
    (ExtractedField("invoiceNumber", "INV-100", 0.97), ExtractedField("vendorName", "Acme Corp", 0.92))
)
_MISSING_VENDOR = ExtractionResult((ExtractedField("invoiceNumber", "INV-100", 0.97),))


def _write_registry(root: Path) -> SchemaRegistry:
    type_dir = root / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (type_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    return SchemaRegistry.load(root)


# --- Pure validate/retry decision logic -------------------------------------------------


def test_extraction_validation_errors_is_empty_for_a_valid_extraction():
    errors = extraction_validation_errors(_VALID, INVOICE_SCHEMA)

    assert errors == []


def test_extraction_validation_errors_reports_a_missing_required_field():
    errors = extraction_validation_errors(_MISSING_VENDOR, INVOICE_SCHEMA)

    assert len(errors) == 1
    assert "vendorName" in errors[0]


def test_extraction_validation_errors_collects_every_violation_at_once():
    wrong_types = ExtractionResult(
        (ExtractedField("invoiceNumber", 12345, 0.9), ExtractedField("vendorName", 67890, 0.9))
    )

    errors = extraction_validation_errors(wrong_types, INVOICE_SCHEMA)

    assert len(errors) == 2


def test_a_valid_first_attempt_is_accepted():
    assert decide_extraction(attempt_number=1, errors=[]) == ExtractionDecision.ACCEPT


def test_an_invalid_first_attempt_is_retried():
    assert decide_extraction(attempt_number=1, errors=["bad date"]) == ExtractionDecision.RETRY


def test_a_valid_retry_is_accepted():
    assert decide_extraction(attempt_number=2, errors=[]) == ExtractionDecision.ACCEPT


def test_an_invalid_retry_fails_rather_than_retrying_again():
    assert decide_extraction(attempt_number=2, errors=["bad date"]) == ExtractionDecision.FAIL


# --- End-to-end via the real pipeline ---------------------------------------------------


async def test_a_valid_retry_after_one_validation_failure_lands_in_extracted(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[_MISSING_VENDOR, _VALID],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    response = await api_client.get(f"/v1/jobs/{job_id}", headers=AUTH_HEADERS)
    result = response.json()
    assert result["status"] == "complete"

    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}

    assert len(provider.extraction_calls) == 2
    first_pages, _, first_errors = provider.extraction_calls[0]
    second_pages, _, second_errors = provider.extraction_calls[1]
    assert first_errors == ()
    assert len(second_errors) == 1
    assert "vendorName" in second_errors[0]


async def test_a_second_validation_failure_lands_the_document_in_extraction_failed(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[_MISSING_VENDOR],  # single scripted response repeats for both attempts
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    response = await api_client.get(f"/v1/jobs/{job_id}", headers=AUTH_HEADERS)
    result = response.json()
    # The Job itself still completes — one Document failing extraction isn't a pipeline
    # failure (CONTEXT.md's Job/Document separation).
    assert result["status"] == "complete"

    document = result["documents"][0]
    assert document["status"] == "extraction_failed"
    assert document["fields"] is None

    # Exactly one retry: two extraction calls total, no more.
    assert len(provider.extraction_calls) == 2
    _, _, first_errors = provider.extraction_calls[0]
    _, _, second_errors = provider.extraction_calls[1]
    assert first_errors == ()
    assert len(second_errors) == 1
