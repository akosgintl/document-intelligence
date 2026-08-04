"""PROTOTYPE — the pages #60's probe extracts from, and the two axes it varies.

**Throwaway. These are not fixtures.** #55 and #58 own the committed golden data tables; these
are drafts good enough to carry an extraction, deliberately trimmed to fit an ID-1 face at the
renderer's current row height. Where a row was dropped or moved to the other face to make it
fit, the comment says so — a reader taking these as a starting point for the real fixtures needs
to know which deviations are mine and which are the document's.

Labels are quoted from `docs/research/hungarian-document-printed-labels.md` (#47), never
invented, for the reason #49's probe gave: a probe with invented labels answers a different
question. Identifiers are built through `fixtures.identifiers`, so every check digit is
deliberately wrong (#46, convention 8).

## The two axes

**Placement** — the same data table drawn at each of `stacked` / `inline` / `column`. Applied to
the identity card and the address card, the two types whose real layout differs from what
`card` drew before this branch. The passport and the 2012 laminated card are *correctly* stacked
per #47, so drawing them at the other placements would measure the axis on documents whose
answer cannot change #60's decision; they are left out and the README says so.

**Legend** — the driving licence's verso field-name legend, at `absent` (what the renderer drew
before this branch) / `horizontal` (the 2012 card) / `rotated` (the 2013 card). This is a
different question from placement: the licence prints *no* label beside any value, so the legend
is not a placement of labels but the presence or absence of them.
"""

from dataclasses import replace
from datetime import date

from fixtures import Cell, Column, Example, Face, Legend, Mrz, Row, Submission, Table, identifiers

PLACEMENTS: tuple[str, ...] = ("stacked", "inline", "column")
_STYLE_FOR_PLACEMENT = {"stacked": "card", "inline": "card_inline", "column": "card_column"}

LEGENDS: tuple[str, ...] = ("absent", "horizontal", "rotated")

# One holder across every page, so a value that comes back wrong is wrong about the layout and
# not about which document it was reading. Accented throughout (`Ő`, `Ű`, `É`, `Á`) per
# convention 9 — the whole reason DejaVu is vendored.
_SURNAME = "KOVÁCS-TŐKE"
_GIVEN_NAMES = "ŐRSÉBET ÍRISZ"
_BIRTH_NAME = "SZŰCS ŐRSÉBET ÍRISZ"
_MOTHERS_NAME = "TÓTH ILONA ÁGNES"
_DATE_OF_BIRTH = date(1979, 6, 30)
_PLACE_OF_BIRTH = "DEBRECEN (MAGYARORSZÁG)"

_ID_DOCUMENT_NUMBER = "500500AA"
_ID_EXPIRY = date(2031, 9, 1)


# ---------------------------------------------------------------------------------------------
# Identity card — the 2021 eID generation (`HUN-BO-06001`), whose real labels are set **inline**.
#
# Deviation from the real card: #47 records the document number repeated vertically down the
# left edge beside the portrait. Convention 2 draws no portrait, and a second copy of a value
# the expectation already asserts would confound the placement axis with a redundancy axis.
# Not drawn.
# ---------------------------------------------------------------------------------------------

ID_CARD = Example(
    key="prototype/id_card",
    document_type="hungarian_id_card",
    schema_version=1,
    submission=Submission(
        faces=(
            Face(
                title=("MAGYARORSZÁG / HUNGARY", "SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY / IDENTITY CARD"),
                elements=(
                    # One label, two Fields: the eID prints family and given names on one line.
                    Row(
                        "Családi és utónév/Family name and Given name:",
                        f"{_SURNAME} {_GIVEN_NAMES}",
                        surname=_SURNAME,
                        givenNames=_GIVEN_NAMES,
                    ),
                    Row("Nem/Sex:", "N/F", sex="N/F"),
                    Row("Állampolgárság/Nationality:", "HUN", nationality="HUN"),
                    # `DD MM YYYY`, space-separated and dotless — the 2016/2021 format (#47).
                    Row("Születési idő/Date of birth:", "30 06 1979", dateOfBirth="1979-06-30"),
                    Row("Érvényességi idő/Date of expiry:", "01 09 2031", dateOfExpiry="2031-09-01"),
                    Row(
                        "Okmányazonosító/Doc. No.:",
                        _ID_DOCUMENT_NUMBER,
                        documentNumber=_ID_DOCUMENT_NUMBER,
                    ),
                    # CAN stands alone with no translation, and must stay visibly distinct from
                    # the document number — #40 spent its description budget on exactly that pair.
                    Row("CAN:", "184620", can="184620"),
                ),
            ),
            Face(
                elements=(
                    Row(
                        "Születési hely/Place of birth:",
                        _PLACE_OF_BIRTH,
                        placeOfBirth=_PLACE_OF_BIRTH,
                    ),
                    Row(
                        "Születési családi és utónév/Family name and Given name at birth:",
                        _BIRTH_NAME,
                        birthName=_BIRTH_NAME,
                    ),
                    Row(
                        "Anyja születési neve/Mother's maiden name:",
                        _MOTHERS_NAME,
                        mothersName=_MOTHERS_NAME,
                    ),
                    Row(
                        "Kiállító hatóság/Issuing authority:",
                        "BELÜGYMINISZTÉRIUM",
                        issuingAuthority="BELÜGYMINISZTÉRIUM",
                    ),
                    # The issue date is printed unlabelled, bottom right, on the real card.
                    Row("", "2021.09.01", dateOfIssue="2021-09-01"),
                    Mrz(
                        # `I<`, not `ID`: the HUN-BO-06001 specimen's zone reads
                        # `I<HUN000188KE<1...`. `mrz_td1` pads a one-character code with a filler.
                        identifiers.mrz_td1(
                            document_code="I",
                            issuing_state="HUN",
                            surname=_SURNAME,
                            given_names=_GIVEN_NAMES,
                            document_number=_ID_DOCUMENT_NUMBER,
                            nationality="HUN",
                            date_of_birth=_DATE_OF_BIRTH,
                            sex="F",
                            date_of_expiry=_ID_EXPIRY,
                        )
                    ),
                ),
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------------------------
# Address card — `HUN-HO-10001`, monolingual Hungarian, whose real labels sit in a **column**.
#
# Deviations, both forced by the ID-1 face at the renderer's row height: the two `Bejelentési
# idő:` rows are reduced to one (the real card repeats the label, paired with each address),
# and `Érvényességi ideje:`, `Kiállító hatóság:` and the issue date move to the verso. On the
# real card the first two are on the recto. Neither deviation touches the placement axis, since
# every variant carries the same rows.
# ---------------------------------------------------------------------------------------------

_PERSONAL_IDENTIFIER = identifiers.personal_identifier(
    sex_code=2, date_of_birth=_DATE_OF_BIRTH, serial=167
)
_ADDRESS_DOCUMENT_NUMBER = "000102 YL"
_RESIDENCE = "4025 DEBRECEN, PIAC UTCA 14. 3. EM. 2."
_TEMPORARY_RESIDENCE = "1075 BUDAPEST, KÁROLY KÖRÚT 9. FSZT. 1."

ADDRESS_CARD = Example(
    key="prototype/address_card",
    document_type="hungarian_address_card",
    schema_version=1,
    submission=Submission(
        faces=(
            Face(
                title=("LAKCÍMET IGAZOLÓ HATÓSÁGI IGAZOLVÁNY",),
                elements=(
                    # Unlabelled beside the title on the real card.
                    Row(
                        "",
                        _ADDRESS_DOCUMENT_NUMBER,
                        documentNumber=_ADDRESS_DOCUMENT_NUMBER,
                    ),
                    Row(
                        "Családi és utónév:",
                        f"{_SURNAME} {_GIVEN_NAMES}",
                        surname=_SURNAME,
                        givenNames=_GIVEN_NAMES,
                    ),
                    Row("Születési név:", _BIRTH_NAME, birthName=_BIRTH_NAME),
                    # One label, two values, and no space after the comma as printed (#47).
                    Row(
                        "Születési hely,idő:",
                        f"{_PLACE_OF_BIRTH},1979.06.30",
                        placeOfBirth=_PLACE_OF_BIRTH,
                        dateOfBirth="1979-06-30",
                    ),
                    Row("Anyja neve:", _MOTHERS_NAME, mothersName=_MOTHERS_NAME),
                    Row("Lakóhely:", _RESIDENCE, residence=_RESIDENCE),
                    # Proves no Field: the Schema carries no registration date.
                    Row("Bejelentési idő:", "2015.05.01"),
                    Row(
                        "Tartózkodási hely:",
                        _TEMPORARY_RESIDENCE,
                        temporaryResidence=_TEMPORARY_RESIDENCE,
                    ),
                ),
            ),
            Face(
                title=("MAGYARORSZÁG", "SZEMÉLYI AZONOSÍTÓT IGAZOLÓ HATÓSÁGI IGAZOLVÁNY"),
                elements=(
                    Row(
                        "Személyi azonosító:",
                        _PERSONAL_IDENTIFIER,
                        personalIdentifier=_PERSONAL_IDENTIFIER,
                    ),
                    # Repeated from the recto on the real card, and proving nothing a second time.
                    Row("Családi és utónév:", f"{_SURNAME} {_GIVEN_NAMES}"),
                    Row(
                        "Kiállító hatóság:",
                        "NYILVÁNTARTÓ HIVATAL",
                        issuingAuthority="NYILVÁNTARTÓ HIVATAL",
                    ),
                    Row("", "2015.05.01", dateOfIssue="2015-05-01"),
                ),
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------------------------
# Driving licence — `HUN-FO-04001` (2013), the legend axis.
#
# The recto prints bare EU field numbers and no words at all; the verso category table is headed
# only `9. 10. 11. 12.`. Every field *name* on this document lives in the legend, which is why
# its absence is a different kind of gap from a mis-placed label.
#
# `address` and `generalRestrictionCodes` are absent: #47 found field 8 is not printed on any
# Hungarian specimen captured, and no code is printed once for all categories here.
# ---------------------------------------------------------------------------------------------

_LICENCE_NUMBER = "CM001267"

# 2013 wording, per #47's generation table. Two lines, because that is how the rotated legend is
# set along the right edge; the horizontal variant prints the same two lines flat.
_LEGEND_LINES = (
    "1. Családi név   2. Utónév   3. Születési idő és hely   4a. A kiállítás időpontja",
    "4b. A lejárat időpontja   4c. Kiállító hatóság   5. Az engedély száma   "
    "10. Érvényesség kezdete   11. Érvényesség vége   12. Kódok",
)


def _licence(legend: str) -> Example:
    """The licence at one of the three legend variants."""
    verso_elements: list[object] = [
        Table(
            into="categories",
            columns=(
                Column("9.", 100),
                Column("10.", 230),
                Column("11.", 230),
                Column("12.", 230),
            ),
            rows=(
                (
                    Cell("B", categoryCode="B"),
                    # `DD.MM.YY.` — the verso table format, and the only one on the card with a
                    # legal source (#48). The two-digit year is exactly the century inference
                    # ADR-0010 knowingly accepted and #54 wants observed.
                    Cell("12.06.95.", dateOfFirstIssue="1995-06-12"),
                    Cell("30.11.27.", dateOfExpiry="2027-11-30"),
                    Cell("01", restrictionCodes=["01"]),
                ),
                (
                    Cell("A2", categoryCode="A2"),
                    Cell("05.02.13.", dateOfFirstIssue="2013-02-05"),
                    Cell("05.02.23.", dateOfExpiry="2023-02-05"),
                    Cell("78", restrictionCodes=["78"]),
                ),
            ),
        ),
        Row("14. Államp:", "HUN", nationality="HUN"),
        # Proves nothing — the holder's name is already proven on the recto.
        Row("Sz.neve:", f"{_SURNAME} {_GIVEN_NAMES}"),
    ]
    if legend == "horizontal":
        verso_elements.append(Legend(_LEGEND_LINES, rotated=False))
    elif legend == "rotated":
        verso_elements.append(Legend(_LEGEND_LINES, rotated=True))

    return Example(
        key=f"prototype/driving_licence_{legend}",
        document_type="hungarian_driving_licence",
        schema_version=1,
        absent=("address", "generalRestrictionCodes"),
        submission=Submission(
            faces=(
                Face(
                    title=("MAGYARORSZÁG", "VEZETŐI ENGEDÉLY"),
                    elements=(
                        Row("1.", _SURNAME, surname=_SURNAME),
                        Row("2.", _GIVEN_NAMES, givenNames=_GIVEN_NAMES),
                        # `YYYY.MM.DD.` on the recto — the *other* format on this same card.
                        Row(
                            "3.",
                            f"1979.06.30. {_PLACE_OF_BIRTH}",
                            dateOfBirth="1979-06-30",
                            placeOfBirth=_PLACE_OF_BIRTH,
                        ),
                        Row("4a.", "2013.02.05.", dateOfIssue="2013-02-05"),
                        Row("4b.", "2023.02.05.", dateOfExpiry="2023-02-05"),
                        Row(
                            "4c.",
                            "BUDAPEST FŐVÁROS KORMÁNYHIVATALA",
                            issuingAuthority="BUDAPEST FŐVÁROS KORMÁNYHIVATALA",
                        ),
                        Row("5.", _LICENCE_NUMBER, documentNumber=_LICENCE_NUMBER),
                    ),
                ),
                Face(elements=tuple(verso_elements)),  # type: ignore[arg-type]
            ),
        ),
    )


PLACEMENT_EXAMPLES: dict[str, Example] = {
    "id_card": ID_CARD,
    "address_card": ADDRESS_CARD,
}

LEGEND_EXAMPLES: dict[str, Example] = {legend: _licence(legend) for legend in LEGENDS}


def at_placement(example: Example, placement: str) -> Example:
    """The same data table drawn at one of the three label placements.

    Only `Submission.style` changes, so the expectation the Example projects is identical across
    placements by construction — which is what lets a difference in extracted values be
    attributed to the page rather than to the assertion.
    """
    style = _STYLE_FOR_PLACEMENT[placement]
    return replace(example, submission=replace(example.submission, style=style))  # type: ignore[arg-type]
