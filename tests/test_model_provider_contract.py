"""Contract tests run against every ModelProvider implementation.

These guard the fake and the Anthropic adapter from drifting apart on the
shape of a matched/unmatched result — each scenario below is scripted once
per implementation and must produce the same value object.
"""

from unittest.mock import AsyncMock

import pytest

from document_intelligence.model_provider.anthropic_provider import AnthropicModelProvider
from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.types import (
    DocumentClassification,
    DocumentTypeSchema,
    ExtractedField,
    ExtractionResult,
    Page,
    PageClassification,
)

INVOICE = DocumentTypeSchema(
    name="Invoice",
    schema_version=3,
    json_schema={"title": "Invoice", "properties": {"invoiceNumber": {"type": "string"}}},
)
PAGE = Page(image_bytes=b"fake-bytes", media_type="image/png")


def _anthropic_returning(tool_name: str, input_: dict) -> AnthropicModelProvider:
    block = AsyncMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = input_
    response = AsyncMock()
    response.content = [block]
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=response)
    return AnthropicModelProvider(client)


@pytest.mark.parametrize(
    "provider",
    [
        FakeModelProvider(page_classifications=[PageClassification("Invoice")]),
        _anthropic_returning("classify_page", {"matched": True, "documentTypeName": "Invoice"}),
    ],
    ids=["fake", "anthropic"],
)
async def test_classify_page_matched_shape_is_consistent_across_providers(provider):
    result = await provider.classify_page(PAGE, [INVOICE])

    assert result == PageClassification("Invoice")


@pytest.mark.parametrize(
    "provider",
    [
        FakeModelProvider(page_classifications=[PageClassification(None)]),
        _anthropic_returning("classify_page", {"matched": False}),
    ],
    ids=["fake", "anthropic"],
)
async def test_classify_page_unmatched_shape_is_consistent_across_providers(provider):
    result = await provider.classify_page(PAGE, [INVOICE])

    assert result == PageClassification(None)


@pytest.mark.parametrize(
    "provider",
    [
        FakeModelProvider(document_classifications=[DocumentClassification("Invoice", 3, 0.9)]),
        _anthropic_returning(
            "classify_document",
            {"matched": True, "documentTypeName": "Invoice", "schemaVersion": 3, "confidence": 0.9},
        ),
    ],
    ids=["fake", "anthropic"],
)
async def test_classify_document_matched_shape_is_consistent_across_providers(provider):
    result = await provider.classify_document([PAGE], [INVOICE])

    assert result == DocumentClassification("Invoice", 3, 0.9)


@pytest.mark.parametrize(
    "provider",
    [
        FakeModelProvider(
            document_classifications=[DocumentClassification(None, None, None)]
        ),
        _anthropic_returning("classify_document", {"matched": False}),
    ],
    ids=["fake", "anthropic"],
)
async def test_classify_document_unmatched_shape_is_consistent_across_providers(provider):
    result = await provider.classify_document([PAGE], [INVOICE])

    assert result == DocumentClassification(None, None, None)


@pytest.mark.parametrize(
    "provider",
    [
        FakeModelProvider(
            extractions=[ExtractionResult((ExtractedField("invoiceNumber", "INV-1", 0.9),))]
        ),
        _anthropic_returning("extract_fields", {"invoiceNumber": {"value": "INV-1", "confidence": 0.9}}),
    ],
    ids=["fake", "anthropic"],
)
async def test_extract_shape_is_consistent_across_providers(provider):
    result = await provider.extract([PAGE], INVOICE)

    assert result == ExtractionResult((ExtractedField("invoiceNumber", "INV-1", 0.9),))
