import uuid
from typing import Any

from pydantic import BaseModel

from document_intelligence.db import Document, DocumentStatus, Job


class SubmissionAccepted(BaseModel):
    job_id: uuid.UUID
    status: str


_FIELDS_VISIBLE_STATUSES = {DocumentStatus.EXTRACTED, DocumentStatus.EXTRACTION_NEEDS_REVIEW}


class DocumentResult(BaseModel):
    document_id: uuid.UUID
    status: str
    document_type: str | None
    schema_version: int | None
    fields: dict[str, Any] | None

    @classmethod
    def from_document(cls, document: Document) -> "DocumentResult":
        return cls(
            document_id=document.id,
            status=document.status.value,
            document_type=document.document_type_name,
            schema_version=document.schema_version,
            fields=(
                {field.name: field.value for field in document.fields}
                if document.status in _FIELDS_VISIBLE_STATUSES
                else None
            ),
        )


class DocumentReviewRequest(BaseModel):
    """Body for `POST /v1/documents/{document_id}/review` (ADR-0003). Which key is expected
    depends on the Document's current status, not on the request itself:

    - `classification_needs_review` expects `document_type` (a registered Document Type name,
      or `null` to confirm `unclassified`).
    - `extraction_needs_review`/`extraction_failed` expect `fields`, a complete replacement
      Field-value set.

    Both are optional here so one shared model covers either shape; the endpoint checks
    `model_fields_set` to tell "omitted" apart from "explicitly null".
    """

    document_type: str | None = None
    fields: dict[str, Any] | None = None


class JobResult(BaseModel):
    job_id: uuid.UUID
    status: str
    documents: list[DocumentResult]

    @classmethod
    def from_job(cls, job: Job) -> "JobResult":
        return cls(
            job_id=job.id,
            status=job.status.value,
            documents=[DocumentResult.from_document(document) for document in job.documents],
        )
