import pytest

from document_intelligence.model_provider.fake import FakeModelProvider
from document_intelligence.model_provider.protocol import ModelProvider
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


def test_satisfies_the_model_provider_protocol():
    assert isinstance(FakeModelProvider(), ModelProvider)


async def test_classify_page_returns_the_single_scripted_response_for_every_call():
    provider = FakeModelProvider(page_classifications=[PageClassification("Invoice")])

    first = await provider.classify_page(PAGE, [INVOICE])
    second = await provider.classify_page(PAGE, [INVOICE])

    assert first == PageClassification("Invoice")
    assert second == PageClassification("Invoice")


async def test_classify_page_consumes_multiple_scripted_responses_in_order():
    provider = FakeModelProvider(
        page_classifications=[PageClassification("Invoice"), PageClassification(None)]
    )

    first = await provider.classify_page(PAGE, [INVOICE])
    second = await provider.classify_page(PAGE, [INVOICE])

    assert first == PageClassification("Invoice")
    assert second == PageClassification(None)


async def test_classify_page_raises_once_scripted_responses_are_exhausted():
    provider = FakeModelProvider(
        page_classifications=[PageClassification("Invoice"), PageClassification(None)]
    )
    await provider.classify_page(PAGE, [INVOICE])
    await provider.classify_page(PAGE, [INVOICE])

    with pytest.raises(AssertionError):
        await provider.classify_page(PAGE, [INVOICE])


async def test_classify_page_records_calls_for_assertions():
    provider = FakeModelProvider(page_classifications=[PageClassification("Invoice")])

    await provider.classify_page(PAGE, [INVOICE])

    assert provider.page_classification_calls == [(PAGE, (INVOICE,))]


async def test_classify_document_returns_scripted_response():
    provider = FakeModelProvider(
        document_classifications=[DocumentClassification("Invoice", 3, 0.92)]
    )

    result = await provider.classify_document([PAGE], [INVOICE])

    assert result == DocumentClassification("Invoice", 3, 0.92)
    assert provider.document_classification_calls == [((PAGE,), (INVOICE,))]


async def test_extract_returns_scripted_response_and_records_validation_errors():
    fields = (ExtractedField("invoiceNumber", "INV-1", 0.99),)
    provider = FakeModelProvider(extractions=[ExtractionResult(fields)])

    result = await provider.extract([PAGE], INVOICE, validation_errors=["bad date"])

    assert result == ExtractionResult(fields)
    assert provider.extraction_calls == [((PAGE,), INVOICE, ("bad date",))]


async def test_classify_page_with_no_scripted_responses_raises_immediately():
    provider = FakeModelProvider()

    with pytest.raises(AssertionError):
        await provider.classify_page(PAGE, [INVOICE])
