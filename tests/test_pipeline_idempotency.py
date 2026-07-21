"""Crash-recovery idempotency: `arq`'s at-least-once delivery means a Job can be requeued
mid-flight. A Job stuck in `processing` (crashed before finishing) must still complete when
reprocessed; a Job already `complete` must be left alone rather than reprocessed."""

import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from document_intelligence.config import get_settings
from document_intelligence.db import DocumentStatus, Job, JobStatus
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import DocumentClassification, PageClassification
from document_intelligence.pipeline import PipelineDeps, process_job
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_s3_client
from test_walking_skeleton import (
    AUTH_HEADERS,
    INVOICE_SCHEMA,
    _one_page_pdf,
    _poll_until_complete,
    _run_worker,
)


def _write_registry(root: Path) -> SchemaRegistry:
    type_dir = root / "invoice"
    type_dir.mkdir()
    (type_dir / "config.json").write_text(json.dumps({"confidence_threshold": 0.8}))
    (type_dir / "v1.json").write_text(json.dumps(INVOICE_SCHEMA))
    return SchemaRegistry.load(root)


async def test_a_crashed_job_stuck_in_processing_is_safely_reprocessed(
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
    job_id = response.json()["job_id"]

    # Simulate a worker crash right after the PENDING -> PROCESSING commit, before any
    # Document/Field rows or the final COMPLETE commit landed.
    async with db_session_factory() as session:
        job = await session.get(Job, uuid.UUID(job_id))
        job.status = JobStatus.PROCESSING
        await session.commit()

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )

    result = await _poll_until_complete(api_client, job_id)
    assert result["status"] == "complete"
    assert result["documents"][0]["status"] == "unclassified"


async def test_an_already_complete_job_is_not_reprocessed(api_client, db_session_factory, tmp_path):
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
    job_id = response.json()["job_id"]

    await _run_worker(
        session_factory=db_session_factory, schema_registry=registry, model_provider=provider
    )
    assert (await _poll_until_complete(api_client, job_id))["status"] == "complete"
    assert len(provider.document_classification_calls) == 1

    # A redelivered/requeued attempt at the same (already complete) Job must be a no-op —
    # in particular, it must not call the Model Provider again.
    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=db_session_factory,
            s3_client=s3_client,
            bucket=get_settings().s3_bucket,
            model_provider=provider,
            schema_registry=registry,
        )
        await process_job(deps, job_id)

    assert len(provider.document_classification_calls) == 1

    async with db_session_factory() as session:
        result = await session.execute(
            select(Job).where(Job.id == uuid.UUID(job_id)).options(selectinload(Job.documents))
        )
        job = result.scalar_one()
        assert job.status == JobStatus.COMPLETE
        assert job.documents[0].status == DocumentStatus.UNCLASSIFIED
