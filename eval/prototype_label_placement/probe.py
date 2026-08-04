"""PROTOTYPE — the billed half of the #60 probe: one page in, one Observation out.

Kept free of terminal code so `run.py` is a thin shell over it, exactly as #49's probe was.

What is actually called: `extract([pages], registered.schema)` against the real
`AnthropicModelProvider` — **billed**. Classification is deliberately not probed: #49 already
measured it (197/197 correct, every fidelity axis noise), and label *placement* is a claim about
what Extraction reads, which is precisely why #49's result does not transfer.

Validation and the review decision are mirrored from `pipeline._run_extraction`, including its
one retry with the errors fed back — a Document whose Extraction only validates on the second
attempt is a different outcome from one that validates first time, and on a probe about page
layout that difference is a finding, not an implementation detail to smooth over.
"""

import json
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import anthropic

from document_intelligence.model_provider.anthropic_provider import AnthropicModelProvider
from document_intelligence.model_provider.recording import (
    ModelCallRecord,
    current_model_call_recorder,
)
from document_intelligence.model_provider.types import Page
from document_intelligence.pipeline import extraction_validation_errors
from document_intelligence.schema_registry.registry import SchemaRegistry
from fixtures import extracted_fields, render_png_bytes
from fixtures.model import Example

REPO_ROOT = Path(__file__).resolve().parents[2]
OBSERVATIONS = Path(__file__).parent / "observations.jsonl"


@dataclass
class FieldOutcome:
    """One Field of one Extraction, against what the data table that drew the page asserts."""

    name: str
    expected: Any
    actual: Any
    correct: bool
    confidence: float | None
    """`None` when the model omitted the Field entirely — distinct from returning null for it,
    which is a value and compares as one."""


@dataclass
class Observation:
    """One billed Extraction, plus how the pipeline would have judged it."""

    document: str
    axis: str
    variant: str
    document_type: str
    threshold: float
    status: str
    attempts: int
    validation_errors: Sequence[str]
    fields_expected: int
    fields_correct: int
    accuracy: float
    mean_confidence: float | None
    min_confidence: float | None
    outcomes: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None
    # Set by sequence.py, for the same reason #49 set them: `run` separates the randomized
    # replicated pass from any exploratory one, and `sequence_index` is the call's position in
    # the shuffled order, which makes session drift testable rather than assumed away.
    run: str | None = None
    sequence_index: int | None = None


class _UsageRecorder:
    """The Provider reports every call through this contextvar seam, so token counts and latency
    come for free without touching the Provider itself."""

    def __init__(self) -> None:
        self.last: ModelCallRecord | None = None

    async def record(self, record: ModelCallRecord) -> None:
        self.last = record


def load_api_key() -> str:
    """`.env` is where this repo's ANTHROPIC_API_KEY lives; a plain script doesn't get it."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_file = REPO_ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "ANTHROPIC_API_KEY" and value.strip():
                return value.strip()
    raise RuntimeError(
        "No ANTHROPIC_API_KEY in the environment or .env — this probe makes real calls"
    )


def load_registry() -> SchemaRegistry:
    return SchemaRegistry.load(REPO_ROOT / "schemas")


def values_match(expected: Any, actual: Any) -> bool:
    """Deep equality between an asserted value and an extracted one.

    Deliberately *not* `run_eval._values_match`: that applies its ±0.01 tolerance only at the
    top level, which #52 exists to fix. Nothing on these three pages is a number, so the probe
    needs recursion and no tolerance at all — and borrowing the harness's comparison would have
    made this probe's results depend on a bug #52 is about to remove.
    """
    if isinstance(expected, dict) and isinstance(actual, dict):
        return expected.keys() == actual.keys() and all(
            values_match(value, actual[key]) for key, value in expected.items()
        )
    if isinstance(expected, list) and isinstance(actual, list):
        # Order-sensitive: a licence prints its categories in a printed order, and #52 has to
        # settle whether that is part of the expectation. This probe assumes it is and says so.
        return len(expected) == len(actual) and all(
            values_match(a, b) for a, b in zip(expected, actual, strict=True)
        )
    return bool(expected == actual)


async def extract(
    *,
    example: Example,
    document: str,
    axis: str,
    variant: str,
    registry: SchemaRegistry,
    client: anthropic.AsyncAnthropic,
    run: str | None = None,
    sequence_index: int | None = None,
) -> Observation:
    """One real, billed Extraction of the Example's page against its bound Schema."""
    registered = registry.get(example.document_type, example.schema_version)
    provider = AnthropicModelProvider(client)
    recorder = _UsageRecorder()
    pages = [Page(image_bytes=render_png_bytes(example), media_type="image/png")]

    token = current_model_call_recorder.set(recorder)
    started = time.monotonic()
    try:
        errors: Sequence[str] = ()
        attempts = 0
        # Mirrors pipeline._run_extraction's exactly-one-retry loop (#24): one retry, with the
        # errors fed back into the prompt, and never more.
        while attempts < 2:
            attempts += 1
            result = await provider.extract(
                pages, registered.schema, validation_errors=errors or None
            )
            errors = extraction_validation_errors(result, registered.schema.json_schema)
            if not errors:
                break
    finally:
        current_model_call_recorder.reset(token)
    elapsed_ms = (time.monotonic() - started) * 1000

    returned = {f.name: f for f in result.fields}
    expected_fields = extracted_fields(example)
    outcomes = [
        FieldOutcome(
            name=name,
            expected=expected,
            actual=returned[name].value if name in returned else None,
            correct=name in returned and values_match(expected, returned[name].value),
            confidence=returned[name].confidence if name in returned else None,
        )
        for name, expected in expected_fields.items()
    ]
    confidences = [f.confidence for f in result.fields]

    observation = Observation(
        document=document,
        axis=axis,
        variant=variant,
        document_type=example.document_type,
        threshold=registered.confidence_threshold,
        status=_status(errors, confidences, registered.confidence_threshold),
        attempts=attempts,
        validation_errors=list(errors),
        fields_expected=len(outcomes),
        fields_correct=sum(1 for f in outcomes if f.correct),
        accuracy=sum(1 for f in outcomes if f.correct) / len(outcomes),
        mean_confidence=sum(confidences) / len(confidences) if confidences else None,
        min_confidence=min(confidences) if confidences else None,
        outcomes=[asdict(f) for f in outcomes],
        input_tokens=recorder.last.input_tokens if recorder.last else None,
        output_tokens=recorder.last.output_tokens if recorder.last else None,
        latency_ms=recorder.last.latency_ms if recorder.last else elapsed_ms,
        run=run,
        sequence_index=sequence_index,
    )
    _append(observation)
    return observation


def _status(errors: Sequence[str], confidences: Sequence[float], threshold: float) -> str:
    """Mirrors `pipeline._run_extraction`'s status decision: a second validation failure means
    `extraction_failed`; any Field below the Threshold means `extraction_needs_review`."""
    if errors:
        return "extraction_failed"
    if any(confidence < threshold for confidence in confidences):
        return "extraction_needs_review"
    return "extracted"


def _append(observation: Observation) -> None:
    """Billed results outlive the terminal. Deliberately breaks the prototype no-persistence
    rule, for #49's reason: re-running to recover a lost result costs money."""
    with OBSERVATIONS.open("a") as handle:
        handle.write(json.dumps(asdict(observation), ensure_ascii=False) + "\n")
