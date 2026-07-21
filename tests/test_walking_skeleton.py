"""End-to-end test for the walking skeleton (#21): submit -> classify -> extract -> poll,
driven entirely through the public HTTP API plus a real `arq` worker, with only the Model
Provider swapped for `FakeModelProvider` — per this repo's Testing Decisions.
"""

import io
import json
from pathlib import Path

import httpx
import pypdfium2 as pdfium
import pytest

from document_intelligence.config import get_settings
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
    PageClassification,
)
from document_intelligence.pipeline import PipelineDeps
from document_intelligence.schema_registry import SchemaRegistry
from support import run_worker_burst

INVOICE_SCHEMA = {
    "title": "Invoice",
    "description": "A commercial invoice.",
    "type": "object",
    "properties": {
        "invoiceNumber": {"type": "string"},
        "vendorName": {"type": "string"},
    },
    "required": ["invoiceNumber", "vendorName"],
}

AUTH_HEADERS = {"Authorization": f"Bearer {get_settings().api_key}"}


def _write_registry(root: Path, *, confidence_threshold: float = 0.8) -> SchemaRegistry:
    type_dir = root / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": confidence_threshold}))
    (type_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    return SchemaRegistry.load(root)


def _one_page_pdf() -> bytes:
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(200, 300)
    buffer = io.BytesIO()
    pdf.save(buffer)
    pdf.close()
    return buffer.getvalue()


def _n_page_pdf(n: int) -> bytes:
    pdf = pdfium.PdfDocument.new()
    for _ in range(n):
        pdf.new_page(200, 300)
    buffer = io.BytesIO()
    pdf.save(buffer)
    pdf.close()
    return buffer.getvalue()


async def _run_worker(*, session_factory, schema_registry: SchemaRegistry, model_provider) -> None:
    from document_intelligence.storage import get_s3_client

    settings = get_settings()
    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=session_factory,
            s3_client=s3_client,
            bucket=settings.s3_bucket,
            model_provider=model_provider,
            schema_registry=schema_registry,
        )
        await run_worker_burst(redis_url=settings.redis_url, deps=deps)


async def _poll_until_complete(client: httpx.AsyncClient, job_id: str) -> dict:
    response = await client.get(f"/v1/jobs/{job_id}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    return response.json()


async def test_single_page_pdf_submission_is_classified_and_extracted(
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
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    job_id = body["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    assert result["job_id"] == job_id
    assert result["status"] == "complete"
    assert len(result["documents"]) == 1

    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["document_type"] == "invoice"
    assert document["schema_version"] == 1
    assert document["fields"] == {"invoiceNumber": "INV-100", "vendorName": "Acme Corp"}

    assert len(provider.page_classification_calls) == 1
    assert len(provider.document_classification_calls) == 1
    assert len(provider.extraction_calls) == 1


async def test_unmatched_page_becomes_unclassified_document(api_client, db_session_factory, tmp_path):
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[PageClassification(None)],
        document_classifications=[DocumentClassification(None, None, None)],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("blank.pdf", _one_page_pdf(), "application/pdf")},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"

    document = result["documents"][0]
    assert document["status"] == "unclassified"
    assert document["document_type"] is None
    assert document["fields"] is None
    assert len(provider.extraction_calls) == 0


async def test_multi_page_pdf_is_rejected_at_submission_time(api_client):
    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("multi.pdf", _n_page_pdf(3), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_submission"


async def test_unsupported_content_type_is_rejected(api_client):
    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("doc.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_submission"


async def test_submission_without_api_key_is_rejected(api_client):
    response = await api_client.post(
        "/v1/submissions",
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_submission_with_wrong_api_key_is_rejected(api_client):
    response = await api_client.post(
        "/v1/submissions",
        headers={"Authorization": "Bearer wrong-key"},
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )

    assert response.status_code == 401


async def test_get_job_requires_api_key(api_client):
    response = await api_client.get("/v1/jobs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 401


async def test_get_unknown_job_returns_404(api_client):
    response = await api_client.get(
        "/v1/jobs/00000000-0000-0000-0000-000000000000", headers=AUTH_HEADERS
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.usefixtures("db_session_factory")
async def test_pending_job_is_visible_before_worker_runs(api_client):
    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    result = await _poll_until_complete(api_client, job_id)

    assert result["status"] == "pending"
    assert result["documents"] == []
