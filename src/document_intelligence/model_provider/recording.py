from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal, Protocol

ModelCallType = Literal["page_classification", "document_classification", "extraction"]


@dataclass(frozen=True)
class ModelCallRecord:
    """One completed Model Provider call, captured by the Provider itself at the point it
    has prompt/response/usage available — the pipeline never builds one directly."""

    call_type: ModelCallType
    prompt: str
    response: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float


class ModelCallRecorder(Protocol):
    """Sink a Provider reports its calls to. Bound to a specific Job by whoever sets
    `current_model_call_recorder`, so a Provider implementation never needs to know
    which Job it's serving."""

    async def record(self, record: ModelCallRecord) -> None: ...


current_model_call_recorder: ContextVar["ModelCallRecorder | None"] = ContextVar(
    "current_model_call_recorder", default=None
)


async def report_model_call(
    *,
    call_type: ModelCallType,
    prompt: str,
    response: str,
    input_tokens: int | None,
    output_tokens: int | None,
    latency_ms: float,
) -> None:
    """Report one completed call to whichever recorder is currently registered, if any.

    Shared by every Provider implementation so recording logic (the `if none, skip`
    guard and `ModelCallRecord` construction) lives in one place, not once per Provider.
    """
    recorder = current_model_call_recorder.get()
    if recorder is None:
        return
    await recorder.record(
        ModelCallRecord(
            call_type=call_type,
            prompt=prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
    )
