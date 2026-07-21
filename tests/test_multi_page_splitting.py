"""End-to-end test for multi-page splitting & grouping (#23): a multi-Document Submission
splits by Document Type, each resulting Document gets its own authoritative document-level
Classification, and a run of unmatched Pages surfaces as an explicit `unclassified` Document —
driven entirely through the public HTTP API plus a real `arq` worker, with only the Model
Provider swapped for `FakeModelProvider`, per this repo's Testing Decisions.
"""

import json
from pathlib import Path

from test_walking_skeleton import (
    AUTH_HEADERS,
    INVOICE_SCHEMA,
    _n_page_pdf,
    _poll_until_complete,
    _run_worker,
)

from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    ExtractedField,
    ExtractionResult,
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


def _write_registry(root: Path) -> SchemaRegistry:
    invoice_dir = root / "invoice"
    invoice_dir.mkdir()
    (invoice_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (invoice_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    (invoice_dir / "v2.json").write_text(json.dumps(INVOICE_SCHEMA))

    receipt_dir = root / "receipt"
    receipt_dir.mkdir()
    (receipt_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (receipt_dir / "v1.json").write_text(json.dumps(RECEIPT_SCHEMA))

    return SchemaRegistry.load(root)


async def test_multi_document_submission_splits_by_document_type_and_settles_each_schema_version(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    # 5 pages: a 2-page invoice, 1 unmatched page, a 2-page receipt.
    provider = FakeModelProvider(
        page_classifications=[
            PageClassification("invoice"),
            PageClassification("invoice"),
            PageClassification(None),
            PageClassification("receipt"),
            PageClassification("receipt"),
        ],
        document_classifications=[
            # Document-level re-classification settles v2 even though every per-page result
            # carried no version at all (PageClassification has none) — ADR-0001.
            DocumentClassification("invoice", 2, 0.9),
            DocumentClassification(None, None, None),
            DocumentClassification("receipt", 1, 0.95),
        ],
        # Independent Documents' classify+extract sequences run concurrently (#31): the invoice
        # and receipt groups' `extract` calls race each other, so each is routed by its resolved
        # Document Type rather than by a shared call-order queue (see `FakeModelProvider`'s
        # `extractions_by_document_type` docstring).
        extractions_by_document_type={
            "invoice": ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-500", 0.95),
                    ExtractedField("vendorName", "Globex", 0.9),
                )
            ),
            "receipt": ExtractionResult(
                (
                    ExtractedField("merchantName", "Corner Store", 0.93),
                    ExtractedField("total", 12.5, 0.88),
                )
            ),
        },
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("bundle.pdf", _n_page_pdf(5), "application/pdf")},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    assert len(result["documents"]) == 3

    documents_by_type = {
        document["document_type"]: document
        for document in result["documents"]
        if document["document_type"] is not None
    }
    unclassified_documents = [d for d in result["documents"] if d["document_type"] is None]

    assert len(unclassified_documents) == 1
    assert unclassified_documents[0]["status"] == "unclassified"
    assert unclassified_documents[0]["fields"] is None

    invoice_doc = documents_by_type["invoice"]
    assert invoice_doc["status"] == "extracted"
    assert invoice_doc["schema_version"] == 2
    assert invoice_doc["fields"] == {"invoiceNumber": "INV-500", "vendorName": "Globex"}

    receipt_doc = documents_by_type["receipt"]
    assert receipt_doc["status"] == "extracted"
    assert receipt_doc["schema_version"] == 1
    assert receipt_doc["fields"] == {"merchantName": "Corner Store", "total": 12.5}

    # Every Page was classified once, every grouped Document was re-classified once, and
    # extraction ran once per classified Document (never for the unclassified one).
    assert len(provider.page_classification_calls) == 5
    assert len(provider.document_classification_calls) == 3
    assert len(provider.extraction_calls) == 2
    assert [len(pages) for pages, _, _ in provider.extraction_calls] == [2, 2]


async def test_a_multi_page_document_of_one_type_is_not_fragmented_per_page(
    api_client, db_session_factory, tmp_path
):
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[
            PageClassification("invoice"),
            PageClassification("invoice"),
            PageClassification("invoice"),
        ],
        document_classifications=[DocumentClassification("invoice", 1, 0.92)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-900", 0.9),
                    ExtractedField("vendorName", "Acme Corp", 0.9),
                )
            )
        ],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _n_page_pdf(3), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    assert len(result["documents"]) == 1
    assert result["documents"][0]["status"] == "extracted"
    assert result["documents"][0]["document_type"] == "invoice"

    assert len(provider.page_classification_calls) == 3
    assert len(provider.document_classification_calls) == 1
    assert len(provider.extraction_calls) == 1
    assert len(provider.extraction_calls[0][0]) == 3


async def test_document_level_classification_is_authoritative_over_page_level_grouping(
    api_client, db_session_factory, tmp_path
):
    """ADR-0001: the document-level call re-classifies for real, it doesn't just rubber-stamp
    whatever grouping decided from page-level results — so a boundary that page-level
    classification left unclassified can still resolve to a real Document Type once its Pages
    are considered together.
    """
    registry = _write_registry(tmp_path)
    provider = FakeModelProvider(
        page_classifications=[PageClassification(None), PageClassification(None)],
        document_classifications=[DocumentClassification("invoice", 1, 0.85)],
        extractions=[
            ExtractionResult(
                (
                    ExtractedField("invoiceNumber", "INV-777", 0.9),
                    ExtractedField("vendorName", "Initech", 0.9),
                )
            )
        ],
    )

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _n_page_pdf(2), "application/pdf")},
    )
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    assert len(result["documents"]) == 1

    document = result["documents"][0]
    assert document["status"] == "extracted"
    assert document["document_type"] == "invoice"
    assert document["schema_version"] == 1
    assert document["fields"] == {"invoiceNumber": "INV-777", "vendorName": "Initech"}

    assert len(provider.document_classification_calls) == 1
    assert len(provider.document_classification_calls[0][0]) == 2
