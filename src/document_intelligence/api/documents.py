import uuid
from typing import Annotated, Any

from arq import ArqRedis
from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from document_intelligence.api.deps import get_arq_pool, get_schema_registry, require_api_key
from document_intelligence.api.dto import DocumentResult, DocumentReviewRequest
from document_intelligence.api.errors import ConflictError, NotFoundError, ValidationError
from document_intelligence.db import Document, DocumentStatus, Field, get_session
from document_intelligence.model_provider.types import ExtractedField, ExtractionResult
from document_intelligence.pipeline import extraction_validation_errors
from document_intelligence.schema_registry import SchemaRegistry, SchemaRegistryError

router = APIRouter(prefix="/v1/documents", tags=["documents"])

# A Review-submitted replacement Field isn't scored by the Model Provider (CONTEXT.md's
# Confidence is specifically a Provider self-report) — it's the caller's own authoritative,
# terminal correction. ADR-0003 deliberately models Review as a stateless status transition
# with no separate Reviewer-identity/history record, so rather than adding a parallel signal
# just to mark "this came from Review", the existing Confidence column is set to full
# confidence — consistent with a replacement never re-triggering `extraction_needs_review`.
_REVIEWED_FIELD_CONFIDENCE = 1.0

_RESOLVABLE_STATUSES = {
    DocumentStatus.CLASSIFICATION_NEEDS_REVIEW,
    DocumentStatus.EXTRACTION_NEEDS_REVIEW,
    DocumentStatus.EXTRACTION_FAILED,
}


@router.post("/{document_id}/review", response_model=DocumentResult)
async def review_document(
    document_id: uuid.UUID,
    request: DocumentReviewRequest,
    _: Annotated[None, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
    schema_registry: Annotated[SchemaRegistry, Depends(get_schema_registry)],
) -> DocumentResult:
    result = await session.execute(
        select(Document).where(Document.id == document_id).options(selectinload(Document.fields))
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise NotFoundError(f"No Document with id {document_id}")

    if document.status not in _RESOLVABLE_STATUSES:
        raise ConflictError(
            f"Document {document_id} is not in a resolvable status (currently "
            f"'{document.status.value}')"
        )

    if document.status == DocumentStatus.CLASSIFICATION_NEEDS_REVIEW:
        if "document_type" not in request.model_fields_set:
            raise ValidationError(
                "Resolving a classification_needs_review Document requires 'document_type' "
                "(a registered Document Type name, or null to confirm unclassified)"
            )
        await _resolve_classification(
            document=document,
            document_type=request.document_type,
            arq_pool=arq_pool,
            schema_registry=schema_registry,
        )
    else:
        if "fields" not in request.model_fields_set or request.fields is None:
            raise ValidationError(
                "Resolving an extraction_needs_review/extraction_failed Document requires a "
                "'fields' replacement set"
            )
        await _resolve_extraction(
            session=session, document=document, fields=request.fields, schema_registry=schema_registry
        )

    await session.commit()
    await session.refresh(document, attribute_names=["fields"])
    return DocumentResult.from_document(document)


async def _resolve_classification(
    *,
    document: Document,
    document_type: str | None,
    arq_pool: ArqRedis,
    schema_registry: SchemaRegistry,
) -> None:
    """Assign a Document Type (bound to its latest Schema version) or confirm `unclassified`,
    without altering the Document's existing Pages (ADR-0003). A Document Type assignment
    proceeds through automated Extraction exactly like any other freshly `classified`
    Document — queued onto the same worker `process_job` already uses, not run inline in this
    request."""
    if document_type is None:
        document.status = DocumentStatus.UNCLASSIFIED
        document.document_type_name = None
        document.schema_version = None
        # Matches the invariant documented on Document.classification_confidence: null
        # whenever there's no Document Type left to have been confident about.
        document.classification_confidence = None
        return

    try:
        registered = schema_registry.get(document_type)
    except SchemaRegistryError as exc:
        raise ValidationError(f"Unknown Document Type '{document_type}'") from exc

    document.document_type_name = document_type
    document.schema_version = registered.schema.schema_version
    document.status = DocumentStatus.CLASSIFIED

    await arq_pool.enqueue_job("extract_document", str(document.id))


async def _resolve_extraction(
    *,
    session: AsyncSession,
    document: Document,
    fields: dict[str, Any],
    schema_registry: SchemaRegistry,
) -> None:
    """Validate a full replacement Field set against the Document's already-bound Schema,
    exactly like automated Extraction (ADR-0003) — no Model Provider round-trip, so a
    validation failure goes straight to `extraction_failed` with no retry."""
    assert document.document_type_name is not None, "a bound Document Type is required to review"
    registered = schema_registry.get(document.document_type_name, document.schema_version)

    extraction = ExtractionResult(
        tuple(
            ExtractedField(name, value, _REVIEWED_FIELD_CONFIDENCE) for name, value in fields.items()
        )
    )
    errors = extraction_validation_errors(extraction, registered.schema.json_schema)
    if errors:
        document.status = DocumentStatus.EXTRACTION_FAILED
        return

    await session.execute(delete(Field).where(Field.document_id == document.id))
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
