import enum
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import jsonschema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from document_intelligence.db import Document, DocumentStatus, Field, Job, JobStatus, Page
from document_intelligence.grouping import group_pages_into_documents
from document_intelligence.model_provider.protocol import ModelProvider
from document_intelligence.model_provider.recording import current_model_call_recorder
from document_intelligence.model_provider.types import ExtractionResult
from document_intelligence.model_provider.types import Page as ProviderPage
from document_intelligence.observability import PersistingModelCallRecorder
from document_intelligence.rendering import render_pages
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_object_bytes, put_object

_MAX_EXTRACTION_ATTEMPTS = 2


@dataclass(frozen=True)
class _RenderedPage:
    """One rendered Page, already uploaded to storage — bundles the two things every later
    step needs (the image to send a Model Provider, the key to persist) so they travel
    together instead of as parallel lists indexed by position."""

    provider_page: ProviderPage
    storage_key: str


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
    """Process one Job end to end: render its Submission's Pages, classify each Page to find
    Document boundaries (#23), then re-classify and extract per grouped Document.

    Two-phase classification per ADR-0001: page-level classification only finds boundaries
    (`grouping.group_pages_into_documents`) — the authoritative Document Type and Schema
    version for extraction always comes from the subsequent document-level call over the
    whole group, never inferred from the per-page results.
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
            rendered_pages: list[_RenderedPage] = []
            for page_number, (image_bytes, media_type) in enumerate(
                render_pages(raw_bytes, submission.content_type), start=1
            ):
                page_key = f"submissions/{submission.id}/pages/{page_number}"
                await put_object(
                    deps.s3_client,
                    bucket=deps.bucket,
                    key=page_key,
                    body=image_bytes,
                    content_type=media_type,
                )
                rendered_pages.append(
                    _RenderedPage(
                        provider_page=ProviderPage(image_bytes=image_bytes, media_type=media_type),
                        storage_key=page_key,
                    )
                )

            document_types = deps.schema_registry.all_latest()

            page_classifications = [
                await deps.model_provider.classify_page(rendered.provider_page, document_types)
                for rendered in rendered_pages
            ]
            boundaries = group_pages_into_documents(page_classifications)

            for boundary in boundaries:
                group = [rendered_pages[index] for index in boundary.page_indices]
                group_provider_pages = [rendered.provider_page for rendered in group]

                document_classification = await deps.model_provider.classify_document(
                    group_provider_pages, document_types
                )

                document = Document(job=job)
                session.add(document)
                document.classification_confidence = document_classification.confidence

                if document_classification.document_type_name is None:
                    document.status = DocumentStatus.UNCLASSIFIED
                else:
                    document.document_type_name = document_classification.document_type_name
                    document.schema_version = document_classification.schema_version
                    registered = deps.schema_registry.get(
                        document_classification.document_type_name,
                        document_classification.schema_version,
                    )
                    assert document_classification.confidence is not None, (
                        "Model Provider contract: confidence is required whenever "
                        "document_type_name is set"
                    )
                    if document_classification.confidence < registered.confidence_threshold:
                        document.status = DocumentStatus.CLASSIFICATION_NEEDS_REVIEW
                    else:
                        document.status = DocumentStatus.CLASSIFIED
                        await extract_and_validate(
                            session=session,
                            document=document,
                            provider_pages=group_provider_pages,
                            model_provider=deps.model_provider,
                            schema_registry=deps.schema_registry,
                        )

                for page_number, rendered in enumerate(group, start=1):
                    session.add(
                        Page(
                            document=document,
                            page_number=page_number,
                            storage_key=rendered.storage_key,
                            media_type=rendered.provider_page.media_type,
                        )
                    )

            job.status = JobStatus.COMPLETE
            await session.commit()
        finally:
            current_model_call_recorder.reset(recorder_token)


def extraction_validation_errors(
    extraction: ExtractionResult, json_schema: Mapping[str, Any]
) -> list[str]:
    """Every violation of an Extraction's Field values against its bound Schema, collected up
    front (not just the first) so a retry prompt can address everything wrong at once (#24).
    Empty means the Extraction validates.
    """
    values = {extracted_field.name: extracted_field.value for extracted_field in extraction.fields}
    validator_cls = jsonschema.validators.validator_for(json_schema)
    validator = validator_cls(json_schema)
    return [error.message for error in validator.iter_errors(values)]


class ExtractionDecision(enum.Enum):
    """What to do next after one Extraction attempt's validation errors are known."""

    ACCEPT = "accept"
    RETRY = "retry"
    FAIL = "fail"


def decide_extraction(*, attempt_number: int, errors: Sequence[str]) -> ExtractionDecision:
    """Pure validate/retry decision (#24): given which attempt just ran (1-indexed) and its
    validation errors, decide whether to accept the result, retry once more, or give up —
    exactly one retry total, never unbounded."""
    if not errors:
        return ExtractionDecision.ACCEPT
    if attempt_number < _MAX_EXTRACTION_ATTEMPTS:
        return ExtractionDecision.RETRY
    return ExtractionDecision.FAIL


async def extract_and_validate(
    *,
    session: AsyncSession,
    document: Document,
    provider_pages: Sequence[ProviderPage],
    model_provider: ModelProvider,
    schema_registry: SchemaRegistry,
) -> None:
    """Extract per the bound Schema, retrying exactly once on validation failure with the
    errors fed back into the prompt — a second failure lands the Document in
    `extraction_failed` rather than retrying unboundedly (#24). A validated result whose
    Fields are all above the bound Schema's Confidence Threshold lands in `extracted`; any
    Field below it lands in `extraction_needs_review` instead (#26).

    Shared by the automated pipeline (`process_job`) and by `process_document_extraction`,
    which runs this same step for a Document a Review just assigned a Document Type to.
    """
    assert document.document_type_name is not None, "caller must classify before extracting"
    registered = schema_registry.get(document.document_type_name, document.schema_version)

    errors: Sequence[str] = ()
    for attempt_number in range(1, _MAX_EXTRACTION_ATTEMPTS + 1):
        extraction = await model_provider.extract(
            provider_pages, registered.schema, validation_errors=errors or None
        )
        errors = extraction_validation_errors(extraction, registered.schema.json_schema)
        decision = decide_extraction(attempt_number=attempt_number, errors=errors)
        if decision is not ExtractionDecision.RETRY:
            break

    if decision is ExtractionDecision.FAIL:
        document.status = DocumentStatus.EXTRACTION_FAILED
        return

    for extracted_field in extraction.fields:
        session.add(
            Field(
                document=document,
                name=extracted_field.name,
                value=extracted_field.value,
                confidence=extracted_field.confidence,
            )
        )

    needs_review = any(
        extracted_field.confidence < registered.confidence_threshold
        for extracted_field in extraction.fields
    )
    document.status = (
        DocumentStatus.EXTRACTION_NEEDS_REVIEW if needs_review else DocumentStatus.EXTRACTED
    )


async def process_document_extraction(deps: PipelineDeps, document_id: str) -> None:
    """Run automated Extraction for a Document a Review resolution (ADR-0003) just assigned a
    Document Type to — the resolved Document proceeds through Extraction exactly like any
    other freshly `classified` Document. Never touches the Document's Job status: resolving a
    Document after its Job already reached `complete` must never reopen the Job (ADR-0003).
    """
    async with deps.session_factory() as session:
        document = await _load_document(session, document_id)
        if document is None or document.status != DocumentStatus.CLASSIFIED:
            # At-least-once queue delivery means a redelivered task against a Document already
            # moved on (or not actually awaiting Extraction) must be a safe no-op.
            return

        recorder_token = current_model_call_recorder.set(
            PersistingModelCallRecorder(session_factory=deps.session_factory, job_id=document.job_id)
        )
        try:
            provider_pages = [
                ProviderPage(
                    image_bytes=await get_object_bytes(
                        deps.s3_client, bucket=deps.bucket, key=page.storage_key
                    ),
                    media_type=page.media_type,
                )
                for page in document.pages
            ]
            await extract_and_validate(
                session=session,
                document=document,
                provider_pages=provider_pages,
                model_provider=deps.model_provider,
                schema_registry=deps.schema_registry,
            )
            await session.commit()
        finally:
            current_model_call_recorder.reset(recorder_token)


async def _load_job(session: AsyncSession, job_id: str) -> Job | None:
    result = await session.execute(
        select(Job).where(Job.id == uuid.UUID(job_id)).options(selectinload(Job.submission))
    )
    return result.scalar_one_or_none()


async def _load_document(session: AsyncSession, document_id: str) -> Document | None:
    result = await session.execute(
        select(Document)
        .where(Document.id == uuid.UUID(document_id))
        .options(selectinload(Document.pages))
    )
    return result.scalar_one_or_none()
