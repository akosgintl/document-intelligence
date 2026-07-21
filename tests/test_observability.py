"""Observability (#22): every Model Provider call made while processing a Job is persisted
as a `ModelCall`, linked to that Job, with token usage and latency — captured at the
Provider-interface seam so the pipeline's call sites don't need to know about it."""

import json
import uuid
from pathlib import Path

import jsonschema
import pytest
from sqlalchemy import select

from document_intelligence.config import get_settings
from document_intelligence.db import ModelCall
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
    PageClassification,
)
from document_intelligence.observability import job_token_usage
from document_intelligence.pipeline import PipelineDeps, process_job
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_s3_client
from test_walking_skeleton import AUTH_HEADERS, INVOICE_SCHEMA, _one_page_pdf, _run_worker


def _write_registry(root: Path) -> SchemaRegistry:
    type_dir = root / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (type_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    return SchemaRegistry.load(root)


async def test_processing_a_job_persists_one_model_call_record_per_provider_call(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
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
        input_tokens=123,
        output_tokens=45,
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = uuid.UUID(response.json()["job_id"])

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    async with db_session_factory() as session:
        result = await session.execute(
            select(ModelCall).where(ModelCall.job_id == job_id).order_by(ModelCall.created_at)
        )
        calls = result.scalars().all()

    assert [call.call_type for call in calls] == [
        "page_classification",
        "document_classification",
        "extraction",
    ]
    for call in calls:
        assert call.input_tokens == 123
        assert call.output_tokens == 45
        assert call.latency_ms is not None
        assert call.prompt
        assert call.response


async def test_model_calls_for_an_unclassified_document_skip_extraction(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[PageClassification(None)],
        document_classifications=[DocumentClassification(None, None, None)],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = uuid.UUID(response.json()["job_id"])

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    async with db_session_factory() as session:
        result = await session.execute(select(ModelCall).where(ModelCall.job_id == job_id))
        calls = result.scalars().all()

    assert [call.call_type for call in calls] == ["page_classification", "document_classification"]


async def test_job_token_usage_sums_across_all_persisted_calls(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
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
        input_tokens=10,
        output_tokens=2,
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = uuid.UUID(response.json()["job_id"])

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    async with db_session_factory() as session:
        usage = await job_token_usage(session, job_id)

    # page + document classification + extraction: 3 calls at 10/2 tokens each.
    assert usage.input_tokens == 30
    assert usage.output_tokens == 6


async def test_job_token_usage_is_zero_for_a_job_with_no_model_calls(db_session_factory):
    async with db_session_factory() as session:
        usage = await job_token_usage(session, uuid.uuid4())

    assert usage.input_tokens == 0
    assert usage.output_tokens == 0


async def test_model_calls_survive_a_later_failure_in_the_same_jobs_processing(
    api_client, db_session_factory, tmp_path
):
    """Extraction validation failure (a real gap until #24) rolls back the Job's own
    transaction — Document/Field/Job-status changes are lost — but every `ModelCall` made
    up to that point must still be persisted, since debugging that exact failure is the
    whole point of this ticket."""
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[PageClassification("invoice")],
        document_classifications=[DocumentClassification("invoice", 1, 0.95)],
        extractions=[ExtractionResult((ExtractedField("invoiceNumber", "INV-100", 0.97),))],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = uuid.UUID(response.json()["job_id"])

    settings = get_settings()
    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=settings.s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )
        with pytest.raises(jsonschema.ValidationError):
            await process_job(deps, str(job_id))

    async with db_session_factory() as session:
        result = await session.execute(select(ModelCall).where(ModelCall.job_id == job_id))
        calls = result.scalars().all()

    assert [call.call_type for call in calls] == [
        "page_classification",
        "document_classification",
        "extraction",
    ]
