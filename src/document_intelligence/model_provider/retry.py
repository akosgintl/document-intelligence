import asyncio
import random
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

from document_intelligence.model_provider.errors import TransientProviderError
from document_intelligence.model_provider.protocol import ModelProvider
from document_intelligence.model_provider.recording import ModelCallType, report_model_call
from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractionResult,
    Page,
    PageClassification,
)

# Three attempts total, doubling from ~1s and capped at 10s (ADR-0009) — never tuned per call
# type, since the policy is about the Provider-interface seam (#19) itself, not any one call.
_MAX_ATTEMPTS = 3
_BASE_DELAY_SECONDS = 1.0
_MAX_DELAY_SECONDS = 10.0

_T = TypeVar("_T")


def compute_backoff_seconds(*, attempt_number: int, retry_after: float | None) -> float:
    """How long to sleep after a failed attempt before the next one.

    Anthropic's own `Retry-After` (on a 429) is honored exactly when the Provider sent one —
    it knows better than a guess. Otherwise: exponential backoff from ~1s, doubling per
    attempt, capped at 10s, with jitter so many Documents retrying at once don't all wake up
    in lockstep.
    """
    if retry_after is not None:
        return retry_after
    capped = min(_MAX_DELAY_SECONDS, _BASE_DELAY_SECONDS * (2 ** (attempt_number - 1)))
    return capped / 2 + random.uniform(0, capped / 2)


class RetryingModelProvider:
    """Wraps any Model Provider with the transient-error retry policy (ADR-0009): up to 3
    attempts total, exponential backoff, honoring a `Retry-After` the Provider reports.

    Applied once, at the Provider-interface seam (#19), so page Classification, document
    Classification, and Extraction all get the exact same policy without the pipeline — or
    the wrapped Provider itself — knowing anything about retries. A wrapped Provider signals
    a transient failure uniformly via `TransientProviderError`; anything else propagates
    immediately, untouched.

    A successful attempt is recorded by the wrapped Provider itself, exactly like any other
    call (#22). Each *failed* attempt is recorded here instead, since the wrapped Provider
    never got far enough to report one of its own.
    """

    def __init__(
        self,
        inner: ModelProvider,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._inner = inner
        self._sleep = sleep

    async def classify_page(
        self, page: Page, document_types: Sequence[DocumentTypeSchema]
    ) -> PageClassification:
        return await self._call_with_retry(
            "page_classification", lambda: self._inner.classify_page(page, document_types)
        )

    async def classify_document(
        self, pages: Sequence[Page], document_types: Sequence[DocumentTypeSchema]
    ) -> DocumentClassification:
        return await self._call_with_retry(
            "document_classification",
            lambda: self._inner.classify_document(pages, document_types),
        )

    async def extract(
        self,
        pages: Sequence[Page],
        document_type: DocumentTypeSchema,
        *,
        validation_errors: Sequence[str] | None = None,
    ) -> ExtractionResult:
        return await self._call_with_retry(
            "extraction",
            lambda: self._inner.extract(pages, document_type, validation_errors=validation_errors),
        )

    async def _call_with_retry(
        self, call_type: ModelCallType, attempt: Callable[[], Awaitable[_T]]
    ) -> _T:
        for attempt_number in range(1, _MAX_ATTEMPTS + 1):
            start = time.monotonic()
            try:
                return await attempt()
            except TransientProviderError as error:
                await report_model_call(
                    call_type=call_type,
                    prompt=f"(transient-error retry, attempt {attempt_number}/{_MAX_ATTEMPTS})",
                    response=f"{type(error).__name__}: {error}",
                    input_tokens=None,
                    output_tokens=None,
                    latency_ms=(time.monotonic() - start) * 1000,
                )
                if attempt_number == _MAX_ATTEMPTS:
                    raise
                await self._sleep(
                    compute_backoff_seconds(
                        attempt_number=attempt_number, retry_after=error.retry_after
                    )
                )
        raise AssertionError("unreachable: the loop above always returns or raises")
