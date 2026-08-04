"""Every committed fixture, as a data table.

One entry per example. The page and the `expected.json` are both read out of the entry, so
editing a printed value here changes the expectation with it and the two can never disagree.

## Adding a Document Type

1. Write the data table below as `Row`/`Table`/`Mrz` elements, quoting the printed labels from
   `docs/research/hungarian-document-printed-labels.md` — that transcription, not statute and
   not a standard, is what these documents actually print (#47, #48). Watch the dates: there is
   no one format per document, and the 2012 identity card prints three on one card.
2. Give every value that proves a Field a keyword argument named for that Field.
3. Name the Fields the page deliberately shows nothing for in the Example's `absent` — and, for
   a key that every row of a table lacks because no column prints it, the Table's `absent_keys`.
4. Build any identifier through `fixtures.identifiers`, never by hand — a hand-written one can
   accidentally be somebody's real number.
5. Run `uv run python -m fixtures.generate`.

Nothing else changes: the renderer needs no knowledge of a new Document Type, and the tests
pick the entry up from `EXAMPLES` automatically.

## What is here, and what is not

The invoice sample and the two invoice v2 golden examples (#56). The remaining eight golden
examples are authored by the tickets that own them — #53 (passport), #54 (driving licence),
#55 (address card), #58 (identity card) — each of which adds entries here and nothing else.
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
                        absent_keys=("grossAmount",),
                        columns=(
                            Column("Megnevezés", 370),
                            Column("Mennyiség", 135, align="right"),
                            Column("Egység", 100),
                            Column("Egységár", 125, align="right"),
                            Column("Nettó", 140, align="right"),
                            Column("ÁFA", 90, align="right"),
                            Column("ÁFA összeg", 150, align="right"),
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

# --- invoice v2 golden examples (#56) ------------------------------------------------------
#
# Both are Hungarian. #43 kept `invoice` as the one general commercial-invoice Type and made
# `sellerTaxNumber` nullable so a foreign invoice still meets a Schema describing what it is —
# and with only two slots, that reasoning goes untested here deliberately. A foreign invoice
# would mostly stress classification, which #49 measured as having margin to spare, whereas the
# simplified case below is the *Schema* decision #43 could most plausibly have got wrong.

# County codes are the last two digits of an adószám and they must agree with the address the
# invoice prints: 08 Győr-Moson-Sopron, 05 Borsod-Abaúj-Zemplén, 02 Baranya, 41-44 Budapest.
_HAPPY_SELLER_TAX_NUMBER = identifiers.tax_number("2468135", vat_code=2, county=8)
_HAPPY_BUYER_TAX_NUMBER = identifiers.tax_number("3574091", vat_code=2, county=5)
_HAPPY_BANK_ACCOUNT = identifiers.bank_account_number("6291470", "3805162")

# The NAV-complete happy path: every one of the Schema's eighteen Fields is printed, so nothing
# is asserted null at the top level.
#
# The figure worth protecting is the **1 Ft disagreement** between the two printed blocks. The
# ÁFA összesítő charges 27% on the summed net (174 500 -> 47 115,00 exactly); the totals block
# adds up the per-line VAT the item table already rounded (27 634,50 -> 27 635 and 19 480,50 ->
# 19 481, so 47 116). Both are right, by different arithmetic, which is why #43 transcribes both
# blocks rather than deriving one — and why a future change that "fixes" the inconsistency, in
# the Schema or in a caller, should fail `test_the_happy_path_prints_a_forint_of_rounding_...`
# rather than quietly pass.
_INVOICE_HAPPY_PATH = Example(
    key="invoice/happy_path",
    document_type="invoice",
    schema_version=2,
    submission=Submission(
        style="sheet",
        faces=(
            Face(
                title=("SZÁMLA", "Fűrészáru és Építőanyag Zrt."),
                elements=(
                    Row("Számla sorszáma:", "2026/B/00417", invoiceNumber="2026/B/00417"),
                    Row("Kiállítás kelte:", "2026.05.11", invoiceDate="2026-05-11"),
                    Row("Teljesítés kelte:", "2026.04.30", deliveryDate="2026-04-30"),
                    Row("Fizetési határidő:", "2026.05.25", paymentDueDate="2026-05-25"),
                    Row("Fizetési mód:", "átutalás", paymentMethod="átutalás"),
                    Row("Pénznem:", "Ft", currency="Ft"),
                    Row("Eladó:", "Fűrészáru és Építőanyag Zrt.", sellerName="Fűrészáru és Építőanyag Zrt."),
                    Row(
                        "Eladó adószáma:",
                        _HAPPY_SELLER_TAX_NUMBER,
                        sellerTaxNumber=_HAPPY_SELLER_TAX_NUMBER,
                    ),
                    Row("Eladó címe:", "9024 Győr, Bécsi út 122.", sellerAddress="9024 Győr, Bécsi út 122."),
                    Row(
                        "Eladó bankszámlaszáma:",
                        _HAPPY_BANK_ACCOUNT,
                        sellerBankAccountNumber=_HAPPY_BANK_ACCOUNT,
                    ),
                    Row("Vevő:", "Zöldövezet Építőipari Kft.", buyerName="Zöldövezet Építőipari Kft."),
                    Row("Vevő adószáma:", _HAPPY_BUYER_TAX_NUMBER, buyerTaxNumber=_HAPPY_BUYER_TAX_NUMBER),
                    Row(
                        "Vevő címe:",
                        "3529 Miskolc, Tűzköves utca 7/B",
                        buyerAddress="3529 Miskolc, Tűzköves utca 7/B",
                    ),
                    Table(
                        into="lineItems",
                        # Net amounts only, as the sample's table is: the gross figure appears in
                        # the totals block, which the Schema calls out as the common case.
                        absent_keys=("grossAmount",),
                        columns=(
                            Column("Megnevezés", 230),
                            Column("Mennyiség", 135, align="right"),
                            Column("Egység", 100),
                            Column("Egységár", 135, align="right"),
                            Column("Nettó", 150, align="right"),
                            # Wide enough for `fordított adózás` spelled out: an enum was refused
                            # for `vatRate` precisely so these markings survive as printed.
                            Column("ÁFA kulcs", 225),
                            Column("ÁFA összeg", 145, align="right"),
                        ),
                        rows=(
                            (
                                Cell("Fenyő palló", description="Fenyő palló"),
                                Cell("250", quantity=250),
                                Cell("fm", unitOfMeasure="fm"),
                                Cell("409,40", unitPrice=409.40),
                                Cell("102 350", netAmount=102350),
                                Cell("27%", vatRate="27%"),
                                Cell("27 635", vatAmount=27635),
                            ),
                            (
                                Cell("Asztalosmunka", description="Asztalosmunka"),
                                # A decimal comma and a thousands space in one figure — the
                                # `1 234 567,89` case ADR-0010 requires read as a JSON number.
                                Cell("12,5", quantity=12.5),
                                Cell("óra", unitOfMeasure="óra"),
                                Cell("5 772,00", unitPrice=5772),
                                Cell("72 150", netAmount=72150),
                                Cell("27%", vatRate="27%"),
                                Cell("19 481", vatAmount=19481),
                            ),
                            (
                                # Reverse-charged (Áfa tv. 142. §): billed as a lump sum, so the
                                # line prints no quantity, no unit and no unit price, and carries
                                # no VAT of its own. Four nulls on one row, each of them a stated
                                # fact about the page rather than a gap.
                                Cell("Építési munka", description="Építési munka"),
                                Cell("", quantity=None),
                                Cell("", unitOfMeasure=None),
                                Cell("", unitPrice=None),
                                Cell("4 800 000", netAmount=4800000),
                                Cell("fordított adózás", vatRate="fordított adózás"),
                                Cell("", vatAmount=None),
                            ),
                            (
                                # Tárgyi adómentes: letting a storage yard is exempt under Áfa tv.
                                # 86. § (1) l), so this line too carries a marking where a rate
                                # would go, and no VAT amount.
                                #
                                # TAM rather than the AAM #56 also named: alanyi adómentesség is a
                                # status of the *seller*, so an AAM marking cannot share an invoice
                                # with the 27% lines above it. Printing both would draw a document
                                # that could not exist, which is worse than leaving one branch of
                                # `vatRate` to a later fixture.
                                Cell("Raktárbérlet", description="Raktárbérlet"),
                                Cell("1", quantity=1),
                                Cell("hónap", unitOfMeasure="hónap"),
                                Cell("65 000", unitPrice=65000),
                                Cell("65 000", netAmount=65000),
                                Cell("TAM", vatRate="TAM"),
                                Cell("", vatAmount=None),
                            ),
                        ),
                    ),
                    Table(
                        into="vatSummary",
                        # The one captioned block on the page. Without it the breakdown is a
                        # second unlabelled table abutting the item table, which is not the
                        # `ÁFA összesítő` a NAV-complete invoice prints.
                        title="ÁFA összesítő",
                        columns=(
                            Column("ÁFA kulcs", 230),
                            Column("Nettó", 160, align="right"),
                            Column("ÁFA", 150, align="right"),
                            Column("Bruttó", 160, align="right"),
                        ),
                        rows=(
                            (
                                Cell("27%", vatRate="27%"),
                                Cell("174 500", netAmount=174500),
                                Cell("47 115", vatAmount=47115),
                                Cell("221 615", grossAmount=221615),
                            ),
                            (
                                Cell("fordított adózás", vatRate="fordított adózás"),
                                Cell("4 800 000", netAmount=4800000),
                                Cell("", vatAmount=None),
                                Cell("4 800 000", grossAmount=4800000),
                            ),
                            (
                                Cell("TAM", vatRate="TAM"),
                                Cell("65 000", netAmount=65000),
                                Cell("", vatAmount=None),
                                Cell("65 000", grossAmount=65000),
                            ),
                        ),
                    ),
                    Row("Nettó összesen:", "5 039 500 Ft", netTotal=5039500),
                    Row("ÁFA összesen:", "47 116 Ft", vatTotal=47116),
                    Row("Fizetendő összeg:", "5 086 616 Ft", grossTotal=5086616),
                ),
            ),
        ),
    ),
)

_SIMPLIFIED_SELLER_TAX_NUMBER = identifiers.tax_number("8103726", vat_code=2, county=2)

# The nullable case: an egyszerűsített számla. #43 absorbed the simplified invoice into this one
# Type **by shape, not by a category flag**, and the distinction is about the *Schema*, not the
# paper: the page is titled EGYSZERŰSÍTETT SZÁMLA and cites Áfa tv. 176. §, because a real one
# is and does (#46, convention 9) — but no Field captures either, and none was added. So a
# caller reading the extracted Document has only `netAmount is null` on a gross-only line to
# read it by, and this is the only fixture that puts that to the test. Its VAT figure is an ÁFA
# tartalom (27/127 = 21,26%), a share of the gross rather than a rate added to a net, which is
# why `vatRate` had to stay a verbatim string.
#
# A retail counter sale, so it also carries the buyer nulls the Schema calls legitimate on
# exactly this document, and prints no ÁFA összesítő at all — `vatSummary` null as a whole,
# which no other fixture shows.
_INVOICE_SIMPLIFIED = Example(
    key="invoice/simplified",
    document_type="invoice",
    schema_version=2,
    absent=(
        "deliveryDate",
        "paymentDueDate",
        "sellerBankAccountNumber",
        "buyerName",
        "buyerTaxNumber",
        "buyerAddress",
        "vatSummary",
        "netTotal",
        "vatTotal",
    ),
    submission=Submission(
        style="sheet",
        faces=(
            Face(
                title=("EGYSZERŰSÍTETT SZÁMLA", "Kőrisfa Papírbolt Kft."),
                elements=(
                    Row("Számla sorszáma:", "2026/K/00517", invoiceNumber="2026/K/00517"),
                    Row("Kiállítás kelte:", "2026.04.07", invoiceDate="2026-04-07"),
                    Row("Fizetési mód:", "készpénz", paymentMethod="készpénz"),
                    Row("Pénznem:", "Ft", currency="Ft"),
                    Row("Eladó:", "Kőrisfa Papírbolt Kft.", sellerName="Kőrisfa Papírbolt Kft."),
                    Row(
                        "Eladó adószáma:",
                        _SIMPLIFIED_SELLER_TAX_NUMBER,
                        sellerTaxNumber=_SIMPLIFIED_SELLER_TAX_NUMBER,
                    ),
                    Row(
                        "Eladó címe:",
                        "7621 Pécs, Király utca 8.",
                        sellerAddress="7621 Pécs, Király utca 8.",
                    ),
                    # No `Vevő` block at all: an unnamed counter customer is what makes the three
                    # buyer Fields null, and printing "készpénzes vásárló" would give the model
                    # something to transcribe into `buyerName` instead.
                    Table(
                        into="lineItems",
                        # The whole point of the fixture: a gross-only table, so every line owes a
                        # null net and a null VAT amount.
                        absent_keys=("netAmount", "vatAmount"),
                        columns=(
                            Column("Megnevezés", 240),
                            Column("Mennyiség", 135, align="right"),
                            Column("Egység", 110),
                            Column("Egységár", 140, align="right"),
                            Column("ÁFA tartalom", 170),
                            Column("Bruttó", 145, align="right"),
                        ),
                        rows=(
                            (
                                Cell("Írómappa A4", description="Írómappa A4"),
                                Cell("3", quantity=3),
                                Cell("db", unitOfMeasure="db"),
                                # Gross on a simplified invoice, per the Schema's unitPrice.
                                Cell("1 290,00", unitPrice=1290),
                                Cell("21,26%", vatRate="21,26%"),
                                Cell("3 870,00", grossAmount=3870),
                            ),
                            (
                                Cell("Golyóstoll kék", description="Golyóstoll kék"),
                                Cell("10", quantity=10),
                                Cell("db", unitOfMeasure="db"),
                                Cell("249,00", unitPrice=249),
                                Cell("21,26%", vatRate="21,26%"),
                                Cell("2 490,00", grossAmount=2490),
                            ),
                            (
                                Cell("Fűzőgép kapocs", description="Fűzőgép kapocs"),
                                Cell("2", quantity=2),
                                Cell("doboz", unitOfMeasure="doboz"),
                                Cell("890,00", unitPrice=890),
                                Cell("21,26%", vatRate="21,26%"),
                                Cell("1 780,00", grossAmount=1780),
                            ),
                        ),
                    ),
                    Row("Fizetendő összeg:", "8 140,00 Ft", grossTotal=8140),
                    Row("Megjegyzés:", "Áfa tv. 176. § szerinti egyszerűsített adattartalmú számla"),
                ),
            ),
        ),
    ),
)

EXAMPLES: tuple[Example, ...] = (_INVOICE_SAMPLE, _INVOICE_HAPPY_PATH, _INVOICE_SIMPLIFIED)
