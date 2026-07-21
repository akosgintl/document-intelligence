import uuid
from dataclasses import dataclass
from typing import Any

import jsonschema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from document_intelligence.db import Document, DocumentStatus, Field, Job, JobStatus, Page
from document_intelligence.model_provider.protocol import ModelProvider
from document_intelligence.model_provider.recording import current_model_call_recorder
from document_intelligence.model_provider.types import Page as ProviderPage
from document_intelligence.observability import PersistingModelCallRecorder
from document_intelligence.rendering import render_single_page
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_object_bytes, put_object


@dataclass(frozen=True)
class PipelineDeps:
    """The resources `process_job` needs, bundled once so the worker's real startup wiring
    and a test's fake-Provider wiring (`tests/support.py`) build the same shape."""

    session_factory: async_sessionmaker[AsyncSession]
    s3_client: Any
    bucket: str
    model_provider: ModelProvider
    schema_registry: SchemaRegistry


async def process_job(deps: PipelineDeps, job_id: str) -> None:
    """Process one Job end to end: render its Submission's single Page, classify, extract,
    validate, and persist the result.

    Splitting/grouping across multiple Pages isn't implemented yet (#23) — a Job's Submission
    is assumed to already be exactly one Page (enforced synchronously at submission time).
    """
    async with deps.session_factory() as session:
        job = await _load_job(session, job_id)
        if job is None or job.status == JobStatus.COMPLETE:
            # Already finished by a prior attempt at this Job — the queue's at-least-once
            # delivery means a requeued Job must be a safe no-op once it's truly done.
            return

        if job.status == JobStatus.PENDING:
            job.status = JobStatus.PROCESSING
            await session.commit()

        recorder_token = current_model_call_recorder.set(
            PersistingModelCallRecorder(session_factory=deps.session_factory, job_id=job.id)
        )
        try:
            submission = job.submission
            raw_bytes = await get_object_bytes(
                deps.s3_client, bucket=deps.bucket, key=submission.storage_key
            )
            image_bytes, media_type = render_single_page(raw_bytes, submission.content_type)

            page_key = f"submissions/{submission.id}/pages/1"
            await put_object(
                deps.s3_client,
                bucket=deps.bucket,
                key=page_key,
                body=image_bytes,
                content_type=media_type,
            )

            provider_page = ProviderPage(image_bytes=image_bytes, media_type=media_type)
            document_types = deps.schema_registry.all_latest()

            # Page-level classification runs even though grouping is a no-op for a single Page,
            # to exercise the real two-phase shape from ADR-0001 (see #21).
            await deps.model_provider.classify_page(provider_page, document_types)
            document_classification = await deps.model_provider.classify_document(
                [provider_page], document_types
            )

            document = Document(job=job)
            session.add(document)

            if document_classification.document_type_name is None:
                document.status = DocumentStatus.UNCLASSIFIED
            else:
                document.status = DocumentStatus.CLASSIFIED
                document.document_type_name = document_classification.document_type_name
                document.schema_version = document_classification.schema_version
                await _extract_and_validate(
                    session=session,
                    document=document,
                    provider_page=provider_page,
                    model_provider=deps.model_provider,
                    schema_registry=deps.schema_registry,
                )

            session.add(
                Page(
                    document=document,
                    page_number=1,
                    storage_key=page_key,
                    media_type=media_type,
                )
            )

            job.status = JobStatus.COMPLETE
            await session.commit()
        finally:
            current_model_call_recorder.reset(recorder_token)


async def _extract_and_validate(
    *,
    session: AsyncSession,
    document: Document,
    provider_page: ProviderPage,
    model_provider: ModelProvider,
    schema_registry: SchemaRegistry,
) -> None:
    registered = schema_registry.get(document.document_type_name, document.schema_version)
    extraction = await model_provider.extract([provider_page], registered.schema)

    values = {extracted_field.name: extracted_field.value for extracted_field in extraction.fields}
    # No retry-on-validation-failure yet (#24) — a validation failure here is a real gap in
    # this ticket's scope and propagates as an unhandled error rather than degrading silently.
    jsonschema.validate(instance=values, schema=registered.schema.json_schema)

    for extracted_field in extraction.fields:
        session.add(
            Field(
                document=document,
                name=extracted_field.name,
                value=extracted_field.value,
                confidence=extracted_field.confidence,
            )
        )

    document.status = DocumentStatus.EXTRACTED


async def _load_job(session: AsyncSession, job_id: str) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == uuid.UUID(job_id)).options(selectinload(Job.submission))
    )
    return result.scalar_one_or_none()
