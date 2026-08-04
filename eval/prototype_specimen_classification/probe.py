"""PROTOTYPE — the billed half of the #49 probe: one page in, one Observation out.

Kept free of terminal code so run.py is a thin shell over it.
"""

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import anthropic

from document_intelligence.model_provider.anthropic_provider import AnthropicModelProvider
from document_intelligence.model_provider.recording import (
    ModelCallRecord,
    current_model_call_recorder,
)
from document_intelligence.model_provider.types import Page
from document_intelligence.schema_registry.registry import SchemaRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
OBSERVATIONS = Path(__file__).parent / "observations.jsonl"


@dataclass
class Observation:
    """One billed classification, plus how the pipeline would have judged it."""

    document: str
    intended_type: str
    variant: str
    variant_description: str
    matched_type: str | None
    schema_version: int | None
    confidence: float | None
    threshold: float
    status: str
    correct_type: bool
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None
    # Set by sequence.py. `run` separates the randomized replicated pass from the first
    # deterministic one; `sequence_index` is the call's position in the shuffled order, which
    # is what makes drift testable rather than merely assumed away.
    run: str | None = None
    sequence_index: int | None = None


class _UsageRecorder:
    """The Provider reports every call through this contextvar seam, so token counts and
    latency come for free without touching the Provider itself."""

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
    raise RuntimeError("No ANTHROPIC_API_KEY in the environment or .env — this probe makes real calls")


def load_registry() -> SchemaRegistry:
    return SchemaRegistry.load(REPO_ROOT / "schemas")


async def classify(
    *,
    image_bytes: bytes,
    document: str,
    intended_type: str,
    variant_key: str,
    variant_description: str,
    registry: SchemaRegistry,
    client: anthropic.AsyncAnthropic,
    run: str | None = None,
    sequence_index: int | None = None,
) -> Observation:
    """One real, billed classify_document call against every registered Document Type.

    classify_page is not called: pipeline.py:141 short-circuits it for single-Page Submissions,
    and a golden fixture is exactly that.
    """
    provider = AnthropicModelProvider(client)
    recorder = _UsageRecorder()
    token = current_model_call_recorder.set(recorder)
    started = time.monotonic()
    try:
        result = await provider.classify_document(
            [Page(image_bytes=image_bytes, media_type="image/png")],
            registry.all_latest(),
        )
    finally:
        current_model_call_recorder.reset(token)
    elapsed_ms = (time.monotonic() - started) * 1000

    threshold = registry.get(intended_type).confidence_threshold
    observation = Observation(
        document=document,
        intended_type=intended_type,
        variant=variant_key,
        variant_description=variant_description,
        matched_type=result.document_type_name,
        schema_version=result.schema_version,
        confidence=result.confidence,
        threshold=threshold,
        status=_status(result.document_type_name, result.confidence, registry),
        correct_type=result.document_type_name == intended_type,
        input_tokens=recorder.last.input_tokens if recorder.last else None,
        output_tokens=recorder.last.output_tokens if recorder.last else None,
        latency_ms=recorder.last.latency_ms if recorder.last else elapsed_ms,
        run=run,
        sequence_index=sequence_index,
    )
    _append(observation)
    return observation


def _status(matched_type: str | None, confidence: float | None, registry: SchemaRegistry) -> str:
    """Mirrors pipeline._classify_and_extract_group — the Threshold is the matched type's own,
    which is not necessarily the intended one when the model picks the wrong Document Type."""
    if matched_type is None:
        return "unclassified"
    assert confidence is not None
    if confidence < registry.get(matched_type).confidence_threshold:
        return "classification_needs_review"
    return "classified"


def _append(observation: Observation) -> None:
    """Billed results outlive the terminal. Deliberately breaks the prototype no-persistence
    rule: re-running to recover a lost result costs money."""
    with OBSERVATIONS.open("a") as handle:
        handle.write(json.dumps(asdict(observation)) + "\n")
