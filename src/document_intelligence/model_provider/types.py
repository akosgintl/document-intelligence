from dataclasses import dataclass
from typing import Any


@dataclass
class Page:
    """One Page image, sent to a Model Provider directly — no OCR step."""

    image_bytes: bytes
    media_type: str


@dataclass
class DocumentTypeSchema:
    """A registered Document Type's Schema at one version.

    Doubles as classification guidance (title/description) and extraction
    target (properties), per this repo's Schema definition.
    """

    name: str
    schema_version: int
    json_schema: dict[str, Any]


@dataclass
class PageClassification:
    """Result of page-level Classification — Document Type only, never Confidence-gated."""

    document_type_name: str | None


@dataclass
class DocumentClassification:
    """Result of document-level Classification — settles the Schema version, with Confidence."""

    document_type_name: str | None
    schema_version: int | None
    confidence: float | None


@dataclass
class ExtractedField:
    """One extracted Field value with its own Confidence."""

    name: str
    value: Any
    confidence: float


@dataclass
class ExtractionResult:
    fields: tuple[ExtractedField, ...]
