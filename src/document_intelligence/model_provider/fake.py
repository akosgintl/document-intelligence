import time
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from document_intelligence.model_provider.errors import TransientProviderError
from document_intelligence.model_provider.recording import ModelCallType, report_model_call
from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractionResult,
    Page,
    PageClassification,
)

_T = TypeVar("_T")


class _Script(Generic[_T]):
    """A queue of scripted responses.

    A single response repeats forever; multiple are consumed in order and then exhausted.
    """

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
        input_tokens: int = 100,
        output_tokens: int = 20,
        page_classification_transient_errors: int = 0,
        document_classification_transient_errors: int = 0,
        extraction_transient_errors: int = 0,
    ) -> None:
        self._page_classifications = _Script(page_classifications)
        self._document_classifications = _Script(document_classifications)
        self._extractions = _Script(extractions)
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        # Each counts down to 0: that many calls to the method raise `TransientProviderError`
        # (ADR-0009) before scripted responses start being consumed as normal — simulating a
        # Provider that fails transiently N times before recovering, or never recovering, at
        # whichever of the three call types a test targets.
        self._page_classification_transient_errors = page_classification_transient_errors
        self._document_classification_transient_errors = document_classification_transient_errors
        self._extraction_transient_errors = extraction_transient_errors

        self.page_classification_calls: list[tuple[Page, tuple[DocumentTypeSchema, ...]]] = []
        self.document_classification_calls: list[
            tuple[tuple[Page, ...], tuple[DocumentTypeSchema, ...]]
        ] = []
        self.extraction_calls: list[tuple[tuple[Page, ...], DocumentTypeSchema, tuple[str, ...]]] = []

    async def classify_page(
        self, page: Page, document_types: Sequence[DocumentTypeSchema]
    ) -> PageClassification:
        self.page_classification_calls.append((page, tuple(document_types)))
        if self._page_classification_transient_errors > 0:
            self._page_classification_transient_errors -= 1
            raise TransientProviderError("simulated transient page classification error")
        start = time.monotonic()
        result = self._page_classifications.next("page classification")
        await self._record(
            call_type="page_classification",
            prompt=f"classify 1 page against {len(document_types)} Document Type(s)",
            result=result,
            start=start,
        )
        return result

    async def classify_document(
        self, pages: Sequence[Page], document_types: Sequence[DocumentTypeSchema]
    ) -> DocumentClassification:
        self.document_classification_calls.append((tuple(pages), tuple(document_types)))
        if self._document_classification_transient_errors > 0:
            self._document_classification_transient_errors -= 1
            raise TransientProviderError("simulated transient document classification error")
        start = time.monotonic()
        result = self._document_classifications.next("document classification")
        await self._record(
            call_type="document_classification",
            prompt=f"classify {len(pages)} page(s) against {len(document_types)} Document Type(s)",
            result=result,
            start=start,
        )
        return result

    async def extract(
        self,
        pages: Sequence[Page],
        document_type: DocumentTypeSchema,
        *,
        validation_errors: Sequence[str] | None = None,
    ) -> ExtractionResult:
        self.extraction_calls.append((tuple(pages), document_type, tuple(validation_errors or ())))
        if self._extraction_transient_errors > 0:
            self._extraction_transient_errors -= 1
            raise TransientProviderError("simulated transient extraction error")
        start = time.monotonic()
        result = self._extractions.next("extraction")
        await self._record(
            call_type="extraction",
            prompt=f"extract {document_type.name} fields from {len(pages)} page(s)",
            result=result,
            start=start,
        )
        return result

    async def _record(self, *, call_type: ModelCallType, prompt: str, result: Any, start: float) -> None:
        await report_model_call(
            call_type=call_type,
            prompt=prompt,
            response=repr(result),
            input_tokens=self._input_tokens,
            output_tokens=self._output_tokens,
            latency_ms=(time.monotonic() - start) * 1000,
        )
