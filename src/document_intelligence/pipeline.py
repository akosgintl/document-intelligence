import asyncio
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
from document_intelligence.grouping import DocumentBoundary, group_pages_into_documents
from document_intelligence.model_provider.errors import TransientProviderError
from document_intelligence.model_provider.protocol import ModelProvider
from document_intelligence.model_provider.recording import current_model_call_recorder
from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractedField,
    ExtractionResult,
)
from document_intelligence.model_provider.types import Page as ProviderPage
from document_intelligence.observability import PersistingModelCallRecorder
from document_intelligence.rendering import render_pages
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_object_bytes, put_object

_MAX_EXTRACTION_ATTEMPTS = 2

# Matches `arq`'s default `max_tries` (worker.py keeps the library default rather than
# overriding it) — tracked independently in Postgres, not read from `arq`'s own Redis-backed
# retry count, so a Job's attempt count survives a real worker crash (#27).
_MAX_JOB_ATTEMPTS = 5


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
    whole group, never inferred from the per-page results. A single-Page Submission has
    nothing to find a boundary against, so page-level classification is skipped entirely and
    the trivial one-Page boundary is built directly (#31) — the per-Page result is never
    persisted anywhere, so skipping it is invisible to everything downstream.

    Independent Model Provider calls run concurrently rather than one at a time (#31): every
    Page's classify_page call, then every boundary group's classify_document → extract
    sequence (the two calls within one group stay sequential — extract needs the settled
    Document Type/Schema version — but different groups don't depend on each other).
    `AsyncSession` isn't safe for concurrent use, so each group's Model Provider calls are
    computed independently before any of them touch the session.

    Each Document is committed as soon as it's computed, in page order, rather than batching
    every Document into one final commit — so a Document that finished before a later boundary
    fails (or before this attempt exhausts its retries and the Job moves to `failed`) survives
    and stays visible on the Job (#27). A boundary whose computation raised stops this loop
    before it or any later boundary is applied — even if a later boundary's concurrent
    computation already finished — so the committed Documents stay exactly the Job's leading
    run of Pages, never a scattered subset, and a resumed attempt's `already_covered` count
    stays meaningful. A resumed attempt skips re-rendering, reclassifying, or re-extracting any
    leading run of Pages already covered by Documents committed by an earlier attempt, so a
    retry never repeats a Model Provider call for work already done.
    """
    async with deps.session_factory() as session:
        job = await _load_job(session, job_id)
        if job is None or job.status in (JobStatus.COMPLETE, JobStatus.FAILED):
            # Already finished — successfully or not — by a prior attempt at this Job. The
            # queue's at-least-once delivery means a requeued Job must be a safe no-op once
            # it's truly done, one way or the other.
            return

        job.attempt_count += 1
        attempt_number = job.attempt_count
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

            # Documents always partition a Submission's Pages, committed strictly in page
            # order (below) — so the Pages an earlier attempt already covered are always
            # exactly the Job's current Documents' leading Pages, never a scattered subset.
            already_covered = sum(len(document.pages) for document in job.documents)

            rendered_pages: list[_RenderedPage] = []
            for page_number, (image_bytes, media_type) in enumerate(
                render_pages(raw_bytes, submission.content_type), start=1
            ):
                if page_number <= already_covered:
                    continue
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

            if len(rendered_pages) == 1:
                # Nothing to find a boundary against with exactly one Page — skip the
                # classify_page round trip and build the trivial boundary directly (#31).
                boundaries: tuple[DocumentBoundary, ...] = (
                    DocumentBoundary(document_type_name=None, page_indices=(0,)),
                )
            else:
                page_classifications = await asyncio.gather(
                    *(
                        deps.model_provider.classify_page(rendered.provider_page, document_types)
                        for rendered in rendered_pages
                    )
                )
                boundaries = group_pages_into_documents(page_classifications)

            groups = [
                [rendered_pages[index] for index in boundary.page_indices] for boundary in boundaries
            ]
            group_outcomes = await asyncio.gather(
                *(
                    _classify_and_extract_group(
                        [rendered.provider_page for rendered in group],
                        document_types=document_types,
                        model_provider=deps.model_provider,
                        schema_registry=deps.schema_registry,
                    )
                    for group in groups
                ),
                return_exceptions=True,
            )

            for group, outcome in zip(groups, group_outcomes, strict=True):
                if isinstance(outcome, BaseException):
                    # See the docstring above: stop before applying this or any later boundary,
                    # so the Documents committed so far stay exactly the Job's leading Pages.
                    raise outcome

                document = Document(job=job)
                session.add(document)
                _apply_group_outcome(session=session, document=document, outcome=outcome)

                for page_number, rendered in enumerate(group, start=1):
                    session.add(
                        Page(
                            document=document,
                            page_number=page_number,
                            storage_key=rendered.storage_key,
                            media_type=rendered.provider_page.media_type,
                        )
                    )

                # Commit now, before moving to the next boundary — a later boundary's Model
                # Provider call failing (or this attempt running out of retries) must never
                # cost this already-finished Document (#27).
                await session.commit()

            job.status = JobStatus.COMPLETE
            await session.commit()
        except Exception:
            if attempt_number >= _MAX_JOB_ATTEMPTS:
                await mark_job_failed(deps.session_factory, job_id)
            raise
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


@dataclass(frozen=True)
class _ExtractionOutcome:
    """What one Extraction attempt loop (#24, #26) decided to persist onto a Document — no
    `AsyncSession` touches, so it can be computed concurrently with other Documents' Extractions
    (`_classify_and_extract_group`) before anything is written."""

    status: DocumentStatus
    fields: tuple[ExtractedField, ...] = ()


async def _run_extraction(
    *,
    provider_pages: Sequence[ProviderPage],
    document_type_name: str,
    schema_version: int | None,
    model_provider: ModelProvider,
    schema_registry: SchemaRegistry,
) -> _ExtractionOutcome:
    """Extract per the bound Schema, retrying exactly once on validation failure with the
    errors fed back into the prompt — a second failure means `extraction_failed` rather than
    retrying unboundedly (#24). A validated result whose Fields are all above the bound
    Schema's Confidence Threshold means `extracted`; any Field below it means
    `extraction_needs_review` instead (#26).
    """
    registered = schema_registry.get(document_type_name, schema_version)

    errors: Sequence[str] = ()
    for attempt_number in range(1, _MAX_EXTRACTION_ATTEMPTS + 1):
        try:
            extraction = await model_provider.extract(
                provider_pages, registered.schema, validation_errors=errors or None
            )
        except TransientProviderError:
            # Exhausted the transient-error retry budget without ever producing a scorable
            # result — routes into extraction_needs_review rather than extraction_failed,
            # since there was never a validatable result to fail (ADR-0009).
            return _ExtractionOutcome(status=DocumentStatus.EXTRACTION_NEEDS_REVIEW)
        errors = extraction_validation_errors(extraction, registered.schema.json_schema)
        decision = decide_extraction(attempt_number=attempt_number, errors=errors)
        if decision is not ExtractionDecision.RETRY:
            break

    if decision is ExtractionDecision.FAIL:
        return _ExtractionOutcome(status=DocumentStatus.EXTRACTION_FAILED)

    needs_review = any(
        extracted_field.confidence < registered.confidence_threshold
        for extracted_field in extraction.fields
    )
    status = DocumentStatus.EXTRACTION_NEEDS_REVIEW if needs_review else DocumentStatus.EXTRACTED
    return _ExtractionOutcome(status=status, fields=extraction.fields)


def _apply_extraction_outcome(
    *, session: AsyncSession, document: Document, outcome: _ExtractionOutcome
) -> None:
    for extracted_field in outcome.fields:
        session.add(
            Field(
                document=document,
                name=extracted_field.name,
                value=extracted_field.value,
                confidence=extracted_field.confidence,
            )
        )
    document.status = outcome.status


async def extract_and_validate(
    *,
    session: AsyncSession,
    document: Document,
    provider_pages: Sequence[ProviderPage],
    model_provider: ModelProvider,
    schema_registry: SchemaRegistry,
) -> None:
    """Run `_run_extraction` for `document` and persist the result onto it directly.

    Used by `process_document_extraction`, which runs this step for a Document a Review just
    assigned a Document Type to. `process_job` uses `_run_extraction`/`_apply_extraction_outcome`
    itself instead (via `_classify_and_extract_group`), so a Document's Extraction can be
    computed concurrently with other Documents' before either touches the session (#31).
    """
    assert document.document_type_name is not None, "caller must classify before extracting"
    outcome = await _run_extraction(
        provider_pages=provider_pages,
        document_type_name=document.document_type_name,
        schema_version=document.schema_version,
        model_provider=model_provider,
        schema_registry=schema_registry,
    )
    _apply_extraction_outcome(session=session, document=document, outcome=outcome)


@dataclass(frozen=True)
class _GroupOutcome:
    """What one Document boundary group's classify-then-extract sequence decided to persist —
    no `AsyncSession` touches, so independent boundary groups can run concurrently
    (`process_job`, #31) before any of them touch the session."""

    status: DocumentStatus
    classification_confidence: float | None
    document_type_name: str | None
    schema_version: int | None
    fields: tuple[ExtractedField, ...] = ()


async def _classify_and_extract_group(
    provider_pages: Sequence[ProviderPage],
    *,
    document_types: Sequence[DocumentTypeSchema],
    model_provider: ModelProvider,
    schema_registry: SchemaRegistry,
) -> _GroupOutcome:
    """Classify one Document boundary group and, if it settles on a Document Type above its
    Confidence Threshold, extract it too — the two calls stay sequential (extraction needs the
    settled Document Type/Schema version) but the whole sequence has no side effects, so
    `process_job` can run it concurrently across boundary groups.
    """
    try:
        document_classification: DocumentClassification | None = await model_provider.classify_document(
            provider_pages, document_types
        )
    except TransientProviderError:
        # Exhausted the transient-error retry budget without ever producing a scorable result —
        # routes into the same needs_review contract a low-confidence result would, rather than
        # failing the whole Job over one stubborn Document (ADR-0009).
        document_classification = None

    if document_classification is None:
        return _GroupOutcome(
            status=DocumentStatus.CLASSIFICATION_NEEDS_REVIEW,
            classification_confidence=None,
            document_type_name=None,
            schema_version=None,
        )

    confidence = document_classification.confidence
    if document_classification.document_type_name is None:
        return _GroupOutcome(
            status=DocumentStatus.UNCLASSIFIED,
            classification_confidence=confidence,
            document_type_name=None,
            schema_version=None,
        )

    registered = schema_registry.get(
        document_classification.document_type_name, document_classification.schema_version
    )
    assert confidence is not None, (
        "Model Provider contract: confidence is required whenever document_type_name is set"
    )
    if confidence < registered.confidence_threshold:
        return _GroupOutcome(
            status=DocumentStatus.CLASSIFICATION_NEEDS_REVIEW,
            classification_confidence=confidence,
            document_type_name=document_classification.document_type_name,
            schema_version=document_classification.schema_version,
        )

    extraction_outcome = await _run_extraction(
        provider_pages=provider_pages,
        document_type_name=document_classification.document_type_name,
        schema_version=document_classification.schema_version,
        model_provider=model_provider,
        schema_registry=schema_registry,
    )
    return _GroupOutcome(
        status=extraction_outcome.status,
        classification_confidence=confidence,
        document_type_name=document_classification.document_type_name,
        schema_version=document_classification.schema_version,
        fields=extraction_outcome.fields,
    )


def _apply_group_outcome(*, session: AsyncSession, document: Document, outcome: _GroupOutcome) -> None:
    document.classification_confidence = outcome.classification_confidence
    if outcome.document_type_name is not None:
        document.document_type_name = outcome.document_type_name
        document.schema_version = outcome.schema_version
    _apply_extraction_outcome(
        session=session,
        document=document,
        outcome=_ExtractionOutcome(status=outcome.status, fields=outcome.fields),
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


async def mark_job_failed(session_factory: async_sessionmaker[AsyncSession], job_id: str) -> None:
    """Transition a Job to `failed` in a fresh session, independent of whatever session/
    transaction the exhausted attempt left in a bad state (#27). Idempotent: a Job some other
    path already moved to `complete`/`failed` is left alone rather than reopened.
    """
    async with session_factory() as session:
        job = await _load_job(session, job_id)
        if job is None or job.status in (JobStatus.COMPLETE, JobStatus.FAILED):
            return
        job.status = JobStatus.FAILED
        await session.commit()


async def _load_job(session: AsyncSession, job_id: str) -> Job | None:
    result = await session.execute(
        select(Job)
        .where(Job.id == uuid.UUID(job_id))
        .options(
            selectinload(Job.submission),
            selectinload(Job.documents).selectinload(Document.pages),
        )
    )
    return result.scalar_one_or_none()


async def _load_document(session: AsyncSession, document_id: str) -> Document | None:
    result = await session.execute(
        select(Document)
        .where(Document.id == uuid.UUID(document_id))
        .options(selectinload(Document.pages))
    )
    return result.scalar_one_or_none()
