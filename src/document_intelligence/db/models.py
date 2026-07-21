import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class JobStatus(str, enum.Enum):
    """See CONTEXT.md's Job lifecycle. `failed` doesn't exist yet — that's #27."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"


class DocumentStatus(str, enum.Enum):
    """See CONTEXT.md's Document lifecycle. `classification_needs_review` and
    `extraction_needs_review` don't exist yet — that's #26.
    """

    PENDING = "pending"
    CLASSIFIED = "classified"
    UNCLASSIFIED = "unclassified"
    EXTRACTED = "extracted"
    EXTRACTION_FAILED = "extraction_failed"


class ModelCallType(str, enum.Enum):
    """Which of the Model Provider interface's three methods a `ModelCall` came from.

    Mirrors `model_provider.recording.ModelCallType` (a plain `Literal`, kept dependency-free
    of the db layer) one-to-one by value — the db layer defines its own enum rather than
    import from `model_provider`, matching every other status enum here.
    """

    PAGE_CLASSIFICATION = "page_classification"
    DOCUMENT_CLASSIFICATION = "document_classification"
    EXTRACTION = "extraction"


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(server_default=func.now())


class Submission(Base):
    """The file a caller uploads via `POST /v1/submissions`."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = _created_at()

    job: Mapped["Job"] = relationship(back_populates="submission")


class Job(Base):
    """The processing lifecycle of one Submission."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id"), nullable=False, unique=True
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=32, validate_strings=True),
        nullable=False,
        default=JobStatus.PENDING,
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    submission: Mapped[Submission] = relationship(back_populates="job")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="job", order_by="Document.created_at"
    )
    model_calls: Mapped[list["ModelCall"]] = relationship(
        back_populates="job", order_by="ModelCall.created_at"
    )


class Document(Base):
    """One logical unit found by splitting a Submission (CONTEXT.md).

    A Job's Documents always form a complete partition of its Submission's Pages —
    unclassified runs of Pages still become their own `unclassified` Document (#23).
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=32, validate_strings=True),
        nullable=False,
        default=DocumentStatus.PENDING,
    )
    document_type_name: Mapped[str | None] = mapped_column(String, nullable=True)
    schema_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    job: Mapped[Job] = relationship(back_populates="documents")
    pages: Mapped[list["Page"]] = relationship(
        back_populates="document", order_by="Page.page_number"
    )
    fields: Mapped[list["Field"]] = relationship(back_populates="document")


class Page(Base):
    """One Page image (CONTEXT.md) belonging to a classified/unclassified Document."""

    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    # 1-indexed position within this Document, not within the Submission it was split from.
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    media_type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = _created_at()

    document: Mapped[Document] = relationship(back_populates="pages")


class ModelCall(Base):
    """One completed Model Provider call (CONTEXT.md's Model Provider) — persisted at the
    Provider-interface seam (#19) for every call a Job's processing makes, so a specific
    misclassification/extraction can be debugged and a Job's token cost queried after the fact.
    """

    __tablename__ = "model_calls"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    call_type: Mapped[ModelCallType] = mapped_column(
        Enum(ModelCallType, native_enum=False, length=32, validate_strings=True),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(String, nullable=False)
    response: Mapped[str] = mapped_column(String, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = _created_at()

    job: Mapped[Job] = relationship(back_populates="model_calls")


class Field(Base):
    """One extracted Field value with its own Confidence (CONTEXT.md)."""

    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = _created_at()

    document: Mapped[Document] = relationship(back_populates="fields")
