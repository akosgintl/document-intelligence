import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from document_intelligence.model_provider.anthropic_provider import AnthropicModelProvider
from document_intelligence.model_provider.protocol import ModelProvider
from document_intelligence.model_provider.recording import (
    ModelCallRecord,
    current_model_call_recorder,
)
from document_intelligence.model_provider.types import DocumentTypeSchema, Page

INVOICE = DocumentTypeSchema(
    name="Invoice",
    schema_version=3,
    json_schema={
        "title": "Invoice",
        "description": "A vendor-issued invoice.",
        "properties": {
            "invoiceNumber": {"type": "string", "description": "Unique invoice identifier."},
            "totalAmount": {"type": "number"},
        },
    },
)
RECEIPT = DocumentTypeSchema(
    name="Receipt", schema_version=1, json_schema={"title": "Receipt", "description": "A receipt."}
)
PAGE = Page(image_bytes=b"\x89PNG-fake-bytes", media_type="image/png")


def _tool_use_response(tool_name: str, input_: dict, *, input_tokens: int = 50, output_tokens: int = 10):
    block = AsyncMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = input_
    response = AsyncMock()
    response.content = [block]
    response.usage = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


def _client_returning(tool_name: str, input_: dict) -> AsyncMock:
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=_tool_use_response(tool_name, input_))
    return client


class _RecordingRecorder:
    def __init__(self) -> None:
        self.records: list[ModelCallRecord] = []

    async def record(self, record: ModelCallRecord) -> None:
        self.records.append(record)


def test_satisfies_the_model_provider_protocol():
    assert isinstance(AnthropicModelProvider(AsyncMock()), ModelProvider)


async def test_classify_page_sends_the_page_image_and_a_forced_tool_choice():
    client = _client_returning("classify_page", {"matched": True, "documentTypeName": "Invoice"})
    provider = AnthropicModelProvider(client, model="claude-sonnet-5")

    result = await provider.classify_page(PAGE, [INVOICE, RECEIPT])

    assert result.document_type_name == "Invoice"
    call = client.messages.create.await_args.kwargs
    assert call["model"] == "claude-sonnet-5"
    assert call["tool_choice"] == {"type": "tool", "name": "classify_page"}
    [message] = call["messages"]
    image_blocks = [block for block in message["content"] if block["type"] == "image"]
    assert len(image_blocks) == 1
    assert image_blocks[0]["source"]["media_type"] == "image/png"
    tool_schema = call["tools"][0]
    assert tool_schema["input_schema"]["properties"]["documentTypeName"]["enum"] == [
        "Invoice",
        "Receipt",
    ]


async def test_classify_page_maps_unmatched_result_to_none():
    client = _client_returning("classify_page", {"matched": False})
    provider = AnthropicModelProvider(client)

    result = await provider.classify_page(PAGE, [INVOICE])

    assert result.document_type_name is None


async def test_classify_document_sends_all_pages_and_maps_confidence():
    client = _client_returning(
        "classify_document",
        {"matched": True, "documentTypeName": "Invoice", "schemaVersion": 3, "confidence": 0.87},
    )
    provider = AnthropicModelProvider(client)
    pages = [PAGE, Page(image_bytes=b"page-2", media_type="image/png")]

    result = await provider.classify_document(pages, [INVOICE])

    assert result.document_type_name == "Invoice"
    assert result.schema_version == 3
    assert result.confidence == 0.87
    call = client.messages.create.await_args.kwargs
    [message] = call["messages"]
    image_blocks = [block for block in message["content"] if block["type"] == "image"]
    assert len(image_blocks) == 2


async def test_classify_document_maps_unmatched_result_to_none_fields():
    client = _client_returning("classify_document", {"matched": False})
    provider = AnthropicModelProvider(client)

    result = await provider.classify_document([PAGE], [INVOICE])

    assert result.document_type_name is None
    assert result.schema_version is None
    assert result.confidence is None


async def test_extract_wraps_each_source_property_with_a_confidence_field():
    client = AsyncMock()
    client.messages.create = AsyncMock(
        return_value=_tool_use_response(
            "extract_fields",
            {
                "invoiceNumber": {"value": "INV-10293", "confidence": 0.95},
                "totalAmount": {"value": 50.0, "confidence": 0.6},
            },
        )
    )
    provider = AnthropicModelProvider(client)

    result = await provider.extract([PAGE], INVOICE)

    by_name = {field.name: field for field in result.fields}
    assert by_name["invoiceNumber"].value == "INV-10293"
    assert by_name["invoiceNumber"].confidence == 0.95
    assert by_name["totalAmount"].value == 50.0
    assert by_name["totalAmount"].confidence == 0.6

    tool_schema = client.messages.create.await_args.kwargs["tools"][0]
    invoice_number_schema = tool_schema["input_schema"]["properties"]["invoiceNumber"]
    assert invoice_number_schema["properties"]["value"] == {
        "type": "string",
        "description": "Unique invoice identifier.",
    }
    assert invoice_number_schema["properties"]["confidence"]["type"] == "number"


async def test_extract_feeds_previous_validation_errors_back_into_the_prompt():
    client = _client_returning(
        "extract_fields", {"invoiceNumber": {"value": "INV-1", "confidence": 0.9}}
    )
    provider = AnthropicModelProvider(client)

    await provider.extract([PAGE], INVOICE, validation_errors=["totalAmount must be a number"])

    call = client.messages.create.await_args.kwargs
    [message] = call["messages"]
    [text_block] = [block for block in message["content"] if block["type"] == "text"]
    assert "totalAmount must be a number" in text_block["text"]


async def test_tool_use_block_missing_raises_a_clear_error():
    response = AsyncMock()
    response.content = []
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=response)
    provider = AnthropicModelProvider(client)

    with pytest.raises(ValueError, match="classify_page"):
        await provider.classify_page(PAGE, [INVOICE])


async def test_calls_are_reported_to_the_registered_recorder_with_usage_and_latency():
    client = _client_returning(
        "classify_document",
        {"matched": True, "documentTypeName": "Invoice", "schemaVersion": 3, "confidence": 0.87},
    )
    provider = AnthropicModelProvider(client)
    recorder = _RecordingRecorder()
    token = current_model_call_recorder.set(recorder)
    try:
        await provider.classify_document([PAGE], [INVOICE])
    finally:
        current_model_call_recorder.reset(token)

    [record] = recorder.records
    assert record.call_type == "document_classification"
    assert record.input_tokens == 50
    assert record.output_tokens == 10
    assert record.latency_ms >= 0
    assert "Invoice" in record.prompt
    assert json.loads(record.response)["documentTypeName"] == "Invoice"


async def test_no_recorder_registered_means_no_recording_attempted():
    client = _client_returning("classify_page", {"matched": False})
    provider = AnthropicModelProvider(client)

    # Should not raise even though no recorder is set (the default ContextVar state).
    result = await provider.classify_page(PAGE, [INVOICE])

    assert result.document_type_name is None
