import uuid
from typing import Any

from pydantic import BaseModel

from document_intelligence.db import Document, DocumentStatus, Job


class SubmissionAccepted(BaseModel):
    job_id: uuid.UUID
    status: str


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
                if document.status == DocumentStatus.EXTRACTED
                else None
            ),
        )


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
