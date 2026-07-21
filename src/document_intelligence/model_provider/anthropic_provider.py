import base64
import json
import time
from collections.abc import Sequence
from typing import Any

import anthropic

from document_intelligence.model_provider.errors import TransientProviderError
from document_intelligence.model_provider.recording import ModelCallType, report_model_call
from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractedField,
    ExtractionResult,
    Page,
    PageClassification,
)

DEFAULT_MODEL = "claude-sonnet-5"
_MAX_TOKENS = 4096


class AnthropicModelProvider:
    """Model Provider adapter for Anthropic's Messages API.

    Sends Page images directly to a vision-capable Claude model — no OCR
    step — and reads Classification/Extraction results off a forced tool
    call, per this repo's Confidence-via-self-report research
    (docs/research/confidence-via-anthropic-api.md).
    """

    def __init__(self, client: anthropic.AsyncAnthropic, *, model: str = DEFAULT_MODEL) -> None:
        self._client = client
        self._model = model

    async def classify_page(
        self, page: Page, document_types: Sequence[DocumentTypeSchema]
    ) -> PageClassification:
        tool = _page_classification_tool(document_types)
        result = await self._call_tool(
            pages=[page],
            tool=tool,
            prompt=_page_classification_prompt(document_types),
            call_type="page_classification",
        )
        if not result.get("matched"):
            return PageClassification(document_type_name=None)
        return PageClassification(
            document_type_name=_require(result, "documentTypeName", tool["name"])
        )

    async def classify_document(
        self, pages: Sequence[Page], document_types: Sequence[DocumentTypeSchema]
    ) -> DocumentClassification:
        tool = _document_classification_tool(document_types)
        result = await self._call_tool(
            pages=pages,
            tool=tool,
            prompt=_document_classification_prompt(document_types),
            call_type="document_classification",
        )
        if not result.get("matched"):
            return DocumentClassification(document_type_name=None, schema_version=None, confidence=None)
        return DocumentClassification(
            document_type_name=_require(result, "documentTypeName", tool["name"]),
            schema_version=_require(result, "schemaVersion", tool["name"]),
            confidence=_require(result, "confidence", tool["name"]),
        )

    async def extract(
        self,
        pages: Sequence[Page],
        document_type: DocumentTypeSchema,
        *,
        validation_errors: Sequence[str] | None = None,
    ) -> ExtractionResult:
        tool = _extraction_tool(document_type)
        result = await self._call_tool(
            pages=pages,
            tool=tool,
            prompt=_extraction_prompt(document_type, validation_errors),
            call_type="extraction",
        )
        fields = tuple(
            ExtractedField(
                name=name,
                value=_require(field, "value", tool["name"]),
                confidence=_require(field, "confidence", tool["name"]),
            )
            for name, field in result.items()
        )
        return ExtractionResult(fields=fields)

    async def _call_tool(
        self,
        *,
        pages: Sequence[Page],
        tool: dict[str, Any],
        prompt: str,
        call_type: ModelCallType,
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [_image_block(page) for page in pages]
        content.append({"type": "text", "text": prompt})

        start = time.monotonic()
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool["name"]},
                messages=[{"role": "user", "content": content}],
            )  # type: ignore[call-overload]  # built from dict[str, Any], not the SDK's TypedDicts
        except anthropic.APIConnectionError as exc:
            raise TransientProviderError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            if exc.status_code == 429:
                raise TransientProviderError(str(exc), retry_after=_retry_after_seconds(exc)) from exc
            if exc.status_code >= 500:
                raise TransientProviderError(str(exc)) from exc
            raise
        latency_ms = (time.monotonic() - start) * 1000

        result = _tool_input(response, tool["name"])
        await report_model_call(
            call_type=call_type,
            prompt=prompt,
            response=json.dumps(result),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=latency_ms,
        )
        return result


def _image_block(page: Page) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": page.media_type,
            "data": base64.standard_b64encode(page.image_bytes).decode("ascii"),
        },
    }


def _retry_after_seconds(exc: anthropic.APIStatusError) -> float | None:
    """Anthropic's `Retry-After` on a 429, in seconds, when present (ADR-0009) — always a
    plain integer count of seconds per Anthropic's API, never an HTTP-date."""
    header = exc.response.headers.get("retry-after")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:
        return None


def _tool_input(response: Any, tool_name: str) -> dict[str, Any]:
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise ValueError(f"Anthropic response contained no '{tool_name}' tool_use block")


def _require(result: dict[str, Any], key: str, tool_name: str) -> Any:
    if key not in result:
        raise ValueError(
            f"Anthropic '{tool_name}' tool call reported matched=True but omitted '{key}'"
        )
    return result[key]


def _matched_property(description: str) -> dict[str, Any]:
    return {"type": "boolean", "description": description}


def _document_type_name_property(document_types: Sequence[DocumentTypeSchema]) -> dict[str, Any]:
    return {
        "type": "string",
        "enum": [dt.name for dt in document_types],
        "description": "The matched Document Type's name. Required when matched is true.",
    }


def _page_classification_tool(document_types: Sequence[DocumentTypeSchema]) -> dict[str, Any]:
    return {
        "name": "classify_page",
        "description": (
            "Classify a single Page against the given Document Types, for finding Document "
            "boundaries only — not a final result, so no confidence is requested."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "matched": _matched_property(
                    "Whether this Page belongs to one of the given Document Types."
                ),
                "documentTypeName": _document_type_name_property(document_types),
            },
            "required": ["matched"],
            "if": {"properties": {"matched": {"const": True}}},
            "then": {"required": ["matched", "documentTypeName"]},
        },
    }


def _document_classification_tool(document_types: Sequence[DocumentTypeSchema]) -> dict[str, Any]:
    return {
        "name": "classify_document",
        "description": (
            "Classify a Document (all its Pages together) against the given Document Types' "
            "Schemas, settling the authoritative Schema version and a self-reported confidence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "matched": _matched_property(
                    "Whether this Document matches one of the given Document Types."
                ),
                "documentTypeName": _document_type_name_property(document_types),
                "schemaVersion": {
                    "type": "integer",
                    "description": (
                        "The matched Document Type's Schema version. Required when matched is true."
                    ),
                },
                "confidence": {
                    "type": "number",
                    "description": (
                        "Self-reported confidence, from 0 to 1, that documentTypeName and "
                        "schemaVersion are correct. Required when matched is true."
                    ),
                },
            },
            "required": ["matched"],
            "if": {"properties": {"matched": {"const": True}}},
            "then": {"required": ["matched", "documentTypeName", "schemaVersion", "confidence"]},
        },
    }


def _extraction_tool(document_type: DocumentTypeSchema) -> dict[str, Any]:
    source_properties: dict[str, Any] = document_type.json_schema.get("properties", {})
    properties = {
        field_name: {
            "type": "object",
            "properties": {
                "value": field_schema,
                "confidence": {
                    "type": "number",
                    "description": "Self-reported confidence, from 0 to 1, for this Field's value.",
                },
            },
            "required": ["value", "confidence"],
        }
        for field_name, field_schema in source_properties.items()
    }
    return {
        "name": "extract_fields",
        "description": (
            f"Extract {document_type.name} Fields from the given Pages, each with its own "
            "self-reported confidence."
        ),
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": list(properties.keys()),
        },
    }


def _page_classification_prompt(document_types: Sequence[DocumentTypeSchema]) -> str:
    guidance = _document_type_guidance(document_types)
    return (
        "Which Document Type, if any, does this Page belong to? This decides Document "
        "boundaries only — judge whether this Page continues the same Document Type as its "
        "neighbors, not the final classification for the Document as a whole.\n\n"
        f"Document Types:\n{guidance}"
    )


def _document_classification_prompt(document_types: Sequence[DocumentTypeSchema]) -> str:
    guidance = _document_type_guidance(document_types)
    return (
        "These Pages together form one Document. Settle its Document Type and the exact "
        "Schema version that should be used to extract it, with your self-reported "
        "confidence.\n\n"
        f"Document Types:\n{guidance}"
    )


def _extraction_prompt(
    document_type: DocumentTypeSchema, validation_errors: Sequence[str] | None
) -> str:
    prompt = (
        f"Extract the {document_type.name} Fields from these Pages, per the Schema given in "
        "the extract_fields tool."
    )
    if validation_errors:
        errors = "\n".join(f"- {error}" for error in validation_errors)
        prompt += f"\n\nThe previous attempt failed validation:\n{errors}\n\nCorrect these issues."
    return prompt


def _document_type_guidance(document_types: Sequence[DocumentTypeSchema]) -> str:
    return "\n".join(
        f"- {dt.name} (schema version {dt.schema_version}): "
        f"{dt.json_schema.get('description', '')}"
        for dt in document_types
    )
