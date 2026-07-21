from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractionResult,
    Page,
    PageClassification,
)


@runtime_checkable
class ModelProvider(Protocol):
    """The pipeline's only way to reach a Model Provider vendor.

    Classification/extraction logic is written against this interface, never
    against a vendor SDK directly, so a new Provider can be added without
    changing pipeline logic.
    """

    async def classify_page(
        self, page: Page, document_types: Sequence[DocumentTypeSchema]
    ) -> PageClassification: ...

    async def classify_document(
        self, pages: Sequence[Page], document_types: Sequence[DocumentTypeSchema]
    ) -> DocumentClassification: ...

    async def extract(
        self,
        pages: Sequence[Page],
        document_type: DocumentTypeSchema,
        *,
        validation_errors: Sequence[str] | None = None,
    ) -> ExtractionResult: ...
