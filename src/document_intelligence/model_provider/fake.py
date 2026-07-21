from collections.abc import Sequence
from typing import Generic, TypeVar

from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractionResult,
    Page,
    PageClassification,
)

_T = TypeVar("_T")


class _Script(Generic[_T]):
    """A queue of scripted responses: a single response repeats forever; multiple are consumed in order and then exhausted."""

    def __init__(self, responses: Sequence[_T]) -> None:
        self._responses = list(responses)
        self._repeat = len(self._responses) == 1

    def next(self, label: str) -> _T:
        if not self._responses:
            raise AssertionError(f"FakeModelProvider: no scripted {label} response left")
        if self._repeat:
            return self._responses[0]
        return self._responses.pop(0)


class FakeModelProvider:
    """Deterministic Model Provider test double — the only component this repo's tests swap for a fake.

    Configure each method's response(s) up front. A single scripted response
    is returned for every call; multiple responses are consumed in order, one
    per call, so a test can script a sequence (e.g. low confidence then a
    corrected retry).
    """

    def __init__(
        self,
        *,
        page_classifications: Sequence[PageClassification] = (),
        document_classifications: Sequence[DocumentClassification] = (),
        extractions: Sequence[ExtractionResult] = (),
    ) -> None:
        self._page_classifications = _Script(page_classifications)
        self._document_classifications = _Script(document_classifications)
        self._extractions = _Script(extractions)

        self.page_classification_calls: list[tuple[Page, tuple[DocumentTypeSchema, ...]]] = []
        self.document_classification_calls: list[
            tuple[tuple[Page, ...], tuple[DocumentTypeSchema, ...]]
        ] = []
        self.extraction_calls: list[tuple[tuple[Page, ...], DocumentTypeSchema, tuple[str, ...]]] = []

    async def classify_page(
        self, page: Page, document_types: Sequence[DocumentTypeSchema]
    ) -> PageClassification:
        self.page_classification_calls.append((page, tuple(document_types)))
        return self._page_classifications.next("page classification")

    async def classify_document(
        self, pages: Sequence[Page], document_types: Sequence[DocumentTypeSchema]
    ) -> DocumentClassification:
        self.document_classification_calls.append((tuple(pages), tuple(document_types)))
        return self._document_classifications.next("document classification")

    async def extract(
        self,
        pages: Sequence[Page],
        document_type: DocumentTypeSchema,
        *,
        validation_errors: Sequence[str] | None = None,
    ) -> ExtractionResult:
        self.extraction_calls.append((tuple(pages), document_type, tuple(validation_errors or ())))
        return self._extractions.next("extraction")
