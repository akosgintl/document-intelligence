"""Every committed fixture, as a data table.

One entry per example. The page and the `expected.json` are both read out of the entry, so
editing a printed value here changes the expectation with it and the two can never disagree.

## Adding a Document Type

1. Write the data table below as `Row`/`Table`/`Mrz` elements, quoting the printed labels from
   `docs/research/hungarian-document-printed-labels.md` — that transcription, not statute and
   not a standard, is what these documents actually print (#47, #48). Watch the dates: there is
   no one format per document, and the 2012 identity card prints three on one card.
2. Give every value that proves a Field a keyword argument named for that Field.
3. Name the Fields the page deliberately shows nothing for in `absent`.
4. Build any identifier through `fixtures.identifiers`, never by hand — a hand-written one can
   accidentally be somebody's real number.
5. Run `uv run python -m fixtures.generate`.

Nothing else changes: the renderer needs no knowledge of a new Document Type, and the tests
pick the entry up from `EXAMPLES` automatically.

## What is here, and what is not

Only the invoice sample. The ten golden examples for the five Document Types are authored by
the tickets that own them — #53 (passport), #54 (driving licence), #55 (address card), #56
(invoice v2), #58 (identity card) — each of which adds entries here and nothing else.
"""

from fixtures import Cell, Column, Example, Face, Row, Submission, Table, identifiers

_SELLER_TAX_NUMBER = identifiers.tax_number("1234567", vat_code=2, county=42)

# A készpénzes számla: settled in cash, so it prints no bank account and no payment deadline —
# both documented null cases in the Schema rather than gaps in the fixture.
_INVOICE_SAMPLE = Example(
    key="invoice/sample",
    document_type="invoice",
    schema_version=2,
    sample="invoice",
    golden=False,
    absent=("paymentDueDate", "sellerBankAccountNumber", "buyerTaxNumber"),
    submission=Submission(
        style="sheet",
        faces=(
            Face(
                title=("SZÁMLA", "Ácsműhely Kft."),
                elements=(
                    Row("Számla sorszáma:", "2026/A/00123", invoiceNumber="2026/A/00123"),
                    Row("Kiállítás kelte:", "2026.07.01", invoiceDate="2026-07-01"),
                    Row("Teljesítés kelte:", "2026.06.30", deliveryDate="2026-06-30"),
                    Row("Fizetési mód:", "készpénz", paymentMethod="készpénz"),
                    Row("Pénznem:", "Ft", currency="Ft"),
                    Row("Eladó:", "Ácsműhely Kft.", sellerName="Ácsműhely Kft."),
                    Row("Eladó adószáma:", _SELLER_TAX_NUMBER, sellerTaxNumber=_SELLER_TAX_NUMBER),
                    Row(
                        "Eladó címe:",
                        "1075 Budapest, Károly körút 9.",
                        sellerAddress="1075 Budapest, Károly körút 9.",
                    ),
                    Row("Vevő:", "Kovács-Tőke Őrsébet", buyerName="Kovács-Tőke Őrsébet"),
                    Row(
                        "Vevő címe:",
                        "4025 Debrecen, Piac utca 14.",
                        buyerAddress="4025 Debrecen, Piac utca 14.",
                    ),
                    Table(
                        into="lineItems",
                        # The item table prints net amounts only; the gross figure appears solely in
                        # the totals block, which the Schema calls out as the common case.
                        absent=("grossAmount",),
                        columns=(
                            Column("Megnevezés", 380),
                            Column("Mennyiség", 110, align="right"),
                            Column("Egység", 80),
                            Column("Egységár", 140, align="right"),
                            Column("Nettó", 150, align="right"),
                            Column("ÁFA", 100, align="right"),
                            Column("ÁFA összeg", 160, align="right"),
                        ),
                        rows=(
                            (
                                Cell("Tölgyfa gerenda 10x10 cm", description="Tölgyfa gerenda 10x10 cm"),
                                Cell("12", quantity=12),
                                Cell("db", unitOfMeasure="db"),
                                Cell("8 500", unitPrice=8500),
                                Cell("102 000", netAmount=102000),
                                Cell("27%", vatRate="27%"),
                                Cell("27 540", vatAmount=27540),
                            ),
                            (
                                Cell("Asztalosipari munkadíj", description="Asztalosipari munkadíj"),
                                Cell("6", quantity=6),
                                Cell("óra", unitOfMeasure="óra"),
                                Cell("12 000", unitPrice=12000),
                                Cell("72 000", netAmount=72000),
                                Cell("27%", vatRate="27%"),
                                Cell("19 440", vatAmount=19440),
                            ),
                        ),
                    ),
                    Table(
                        into="vatSummary",
                        columns=(
                            Column("ÁFA kulcs", 200),
                            Column("Nettó", 200, align="right"),
                            Column("ÁFA", 200, align="right"),
                            Column("Bruttó", 200, align="right"),
                        ),
                        rows=(
                            (
                                Cell("27%", vatRate="27%"),
                                Cell("174 000", netAmount=174000),
                                Cell("46 980", vatAmount=46980),
                                Cell("220 980", grossAmount=220980),
                            ),
                        ),
                    ),
                    Row("Nettó összesen:", "174 000 Ft", netTotal=174000),
                    Row("ÁFA összesen:", "46 980 Ft", vatTotal=46980),
                    Row("Fizetendő összeg:", "220 980 Ft", grossTotal=220980),
                ),
            ),
        ),
    ),
)

EXAMPLES: tuple[Example, ...] = (_INVOICE_SAMPLE,)
