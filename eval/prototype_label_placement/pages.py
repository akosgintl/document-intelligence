"""PROTOTYPE — the pages #60's probe extracts from, and the two axes it now varies.

**Throwaway. These are not fixtures.** #55 and #58 own the committed golden data tables.

Labels and layout are quoted from `docs/research/hungarian-document-printed-labels.md` — §1–§5
for wording, **§6 for placement**, which was added after the first pass of this probe measured a
layout the specimens do not print. That is the whole reason the axes below look the way they do.

## Axis 1 — placement (4 levels)

`stacked` / `inline` / `column` force one placement onto every row. They are experimental
controls, not documents: #47 §6 found that the eID identity card and the address card each mix
three placements on one face, so **no uniform placement draws either card**.

`specimen` is the fourth arm and the only real one: each row places itself as PRADO shows it.
The eID stacks its name, pairs `Nem/Sex:` and `Állampolgárság/Nationality:` inline on one row,
and right-aligns its dates and document number; the address card runs `Családi és utónév:`
inline on the recto and **stacked** on the verso.

## Axis 2 — the holder's name (3 levels)

The first pass used `ŐRSÉBET`, which is not a Hungarian name (`ERZSÉBET` is) — it came from
`fixtures/catalogue.py`'s committed invoice fixture. That leaves the name-split result unable to
distinguish "layout matters" from "layout matters when the token is lexically unrecognisable".

- `nonce` — `KOVÁCS-TŐKE ŐRSÉBET ÍRISZ`. Plausible Hungarian orthography, correct accents, not a
  real name. A good nonce precisely because it looks like one.
- `real` — `KOVÁCS-TŐKE ERZSÉBET ÍRISZ`. Identical in every respect except that the given name
  exists, which is what isolates lexical recognition as the cause.
- `specimen` — each document's *own* holder, values and all, from its PRADO capture: the eID's
  `SZÉPENÉ KISS ROZÁLIA` (a two-word married surname, one given name) and the address card's
  `DEBRECENI-SZATMÁRI ANDREA`. This is the structure the real cards print, and it is harder than
  either arm above: cut `SZÉPENÉ KISS ROZÁLIA` one word early and you get a plausible-looking
  wrong answer.

The driving licence is not in this run. Its legend axis is settled — 12/12 Fields correct on
every draw with no field names printed at all, p=1.000 on every pairing — and it prints
`1.`/`2.` as separate rows, so it has no name split to vary.
"""

from dataclasses import dataclass, replace
from datetime import date

from fixtures import Cell, Column, Example, Face, Legend, Mrz, Pair, Row, Submission, Table, identifiers

PLACEMENTS: tuple[str, ...] = ("stacked", "inline", "column", "specimen")
_STYLE_FOR_PLACEMENT = {
    "stacked": "card",
    "inline": "card_inline",
    "column": "card_column",
    "specimen": "card_specimen",
}

NAMES: tuple[str, ...] = ("nonce", "real", "specimen")


@dataclass(frozen=True)
class Holder:
    """Every name-shaped value on a card, so one arm of the name axis is one object."""

    surname: str
    given_names: str
    birth_name: str
    mothers_name: str

    @property
    def full(self) -> str:
        return f"{self.surname} {self.given_names}"


# Identical but for the given name: `ŐRSÉBET` is not a word, `ERZSÉBET` is. Everything else —
# the hyphenated surname, the second given name, the accents — is held constant, which is what
# makes the pair a test of lexical recognition rather than of anything else.
_NONCE = Holder("KOVÁCS-TŐKE", "ŐRSÉBET ÍRISZ", "SZŰCS ŐRSÉBET ÍRISZ", "TÓTH ILONA ÁGNES")
_REAL = Holder("KOVÁCS-TŐKE", "ERZSÉBET ÍRISZ", "SZŰCS ERZSÉBET ÍRISZ", "TÓTH ILONA ÁGNES")

# Straight off the specimens, including the mother's names.
_SPECIMEN_ID = Holder("SZÉPENÉ KISS", "ROZÁLIA", "KISS ROZÁLIA", "KALCSÓ VILMA")
_SPECIMEN_ADDRESS = Holder(
    "DEBRECENI-SZATMÁRI", "ANDREA", "DEBRECENI ANDREA", "KISZELY ÉVA BORBÁLA"
)

HOLDERS: dict[str, dict[str, Holder]] = {
    "nonce": {"id_card": _NONCE, "address_card": _NONCE},
    "real": {"id_card": _REAL, "address_card": _REAL},
    "specimen": {"id_card": _SPECIMEN_ID, "address_card": _SPECIMEN_ADDRESS},
}

_DATE_OF_BIRTH = date(1979, 6, 30)
_PLACE_OF_BIRTH = "DEBRECEN (MAGYARORSZÁG)"
_ID_DOCUMENT_NUMBER = "500500AA"
_ID_EXPIRY = date(2031, 9, 1)


def id_card(holder: Holder) -> Example:
    """The 2021 eID (`HUN-BO-06001`), laid out per #47 §6.

    Deviation: #47 records the document number repeated vertically down the left edge beside the
    portrait. Convention 2 draws no portrait, and a second copy of a value the expectation
    already asserts would confound the axis with a redundancy axis. Not drawn.
    """
    return Example(
        key="prototype/id_card",
        document_type="hungarian_id_card",
        schema_version=1,
        submission=Submission(
            faces=(
                Face(
                    title=(
                        "MAGYARORSZÁG / HUNGARY",
                        "SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY / IDENTITY CARD",
                    ),
                    elements=(
                        # Stacked on the real card — the label on its own line, the name larger
                        # and bold beneath it. One label, two Fields.
                        Row(
                            "Családi és utónév/Family name and Given name:",
                            holder.full,
                            place="stacked",
                            surname=holder.surname,
                            givenNames=holder.given_names,
                        ),
                        # Two fields sharing one line, left and right.
                        Pair(
                            Row("Nem/Sex:", "N/F", place="inline", sex="N/F"),
                            Row(
                                "Állampolgárság/Nationality:",
                                "HUN",
                                place="inline",
                                nationality="HUN",
                            ),
                        ),
                        # Label left, value hard against the card's right edge.
                        # `DD MM YYYY`, space-separated and dotless — the 2016/2021 format.
                        Row(
                            "Születési idő/Date of birth:",
                            "30 06 1979",
                            place="column",
                            align="right",
                            dateOfBirth="1979-06-30",
                        ),
                        Row(
                            "Érvényességi idő/Date of expiry:",
                            "01 09 2031",
                            place="column",
                            align="right",
                            dateOfExpiry="2031-09-01",
                        ),
                        Row(
                            "Okmányazonosító/Doc. No.:",
                            _ID_DOCUMENT_NUMBER,
                            place="column",
                            align="right",
                            documentNumber=_ID_DOCUMENT_NUMBER,
                        ),
                        # CAN stands alone with no translation, and must stay visibly distinct
                        # from the document number — #40 spent its description budget on the pair.
                        Row("CAN:", "184620", place="inline", can="184620"),
                    ),
                ),
                Face(
                    elements=(
                        Row(
                            "Születési hely/Place of birth:",
                            _PLACE_OF_BIRTH,
                            place="stacked",
                            placeOfBirth=_PLACE_OF_BIRTH,
                        ),
                        Row(
                            "Születési családi és utónév/Family name and Given name at birth:",
                            holder.birth_name,
                            place="stacked",
                            birthName=holder.birth_name,
                        ),
                        Row(
                            "Anyja születési neve/Mother's maiden name:",
                            holder.mothers_name,
                            place="stacked",
                            mothersName=holder.mothers_name,
                        ),
                        Row(
                            "Kiállító hatóság/Issuing authority:",
                            "BELÜGYMINISZTÉRIUM",
                            place="inline",
                            issuingAuthority="BELÜGYMINISZTÉRIUM",
                        ),
                        # Printed unlabelled, bottom right.
                        Row(
                            "",
                            "2021.09.01",
                            place="column",
                            align="right",
                            dateOfIssue="2021-09-01",
                        ),
                        Mrz(
                            # `I<`, not `ID`: the specimen's zone reads `I<HUN000188KE<1…`.
                            # Accented names are transliterated per 9303 §6.A inside `mrz_td1`.
                            identifiers.mrz_td1(
                                document_code="I",
                                issuing_state="HUN",
                                surname=holder.surname,
                                given_names=holder.given_names,
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


_PERSONAL_IDENTIFIER = identifiers.personal_identifier(
    sex_code=2, date_of_birth=_DATE_OF_BIRTH, serial=167
)
_ADDRESS_DOCUMENT_NUMBER = "000102 YL"
_RESIDENCE = "4025 DEBRECEN, PIAC UTCA 14. 3. EM. 2."
_TEMPORARY_RESIDENCE = "1075 BUDAPEST, KÁROLY KÖRÚT 9. FSZT. 1."


def address_card(holder: Holder) -> Example:
    """The *lakcímkártya* (`HUN-HO-10001`), laid out per #47 §6.

    Deviations, forced by an ID-1 face at the renderer's row height: the real card prints
    `Bejelentési idő:` twice, once against each address, in a second right-hand column, and
    keeps `Érvényességi ideje:` and `Kiállító hatóság:` on the recto. Here there is one
    `Bejelentési idő:`, no `Érvényességi ideje:`, and the authority and issue date sit on the
    verso. Every placement arm carries the same rows, so this touches no axis.
    """
    return Example(
        key="prototype/address_card",
        document_type="hungarian_address_card",
        schema_version=1,
        submission=Submission(
            faces=(
                Face(
                    title=("LAKCÍMET IGAZOLÓ HATÓSÁGI IGAZOLVÁNY",),
                    elements=(
                        # Unlabelled, beside the title.
                        Row(
                            "",
                            _ADDRESS_DOCUMENT_NUMBER,
                            place="inline",
                            documentNumber=_ADDRESS_DOCUMENT_NUMBER,
                        ),
                        # Inline on the recto, with no space after the colon — and stacked on
                        # the verso. The same label, placed two ways on one card.
                        Row(
                            "Családi és utónév:",
                            holder.full,
                            place="inline",
                            surname=holder.surname,
                            givenNames=holder.given_names,
                        ),
                        Row(
                            "Születési név:",
                            holder.birth_name,
                            place="column",
                            birthName=holder.birth_name,
                        ),
                        # One label, two values, and no space after the comma as printed.
                        Row(
                            "Születési hely,idő:",
                            f"{_PLACE_OF_BIRTH},1979.06.30",
                            place="column",
                            placeOfBirth=_PLACE_OF_BIRTH,
                            dateOfBirth="1979-06-30",
                        ),
                        Row(
                            "Anyja neve:",
                            holder.mothers_name,
                            place="column",
                            mothersName=holder.mothers_name,
                        ),
                        Row("Lakóhely:", _RESIDENCE, place="column", residence=_RESIDENCE),
                        # Proves no Field: the Schema carries no registration date.
                        Row("Bejelentési idő:", "2015.05.01", place="column"),
                        Row(
                            "Tartózkodási hely:",
                            _TEMPORARY_RESIDENCE,
                            place="inline",
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
                            place="inline",
                            personalIdentifier=_PERSONAL_IDENTIFIER,
                        ),
                        # Stacked here, inline on the recto. Proves nothing a second time.
                        Row("Családi és utónév:", holder.full, place="stacked"),
                        Row(
                            "Kiállító hatóság:",
                            "NYILVÁNTARTÓ HIVATAL",
                            place="column",
                            issuingAuthority="NYILVÁNTARTÓ HIVATAL",
                        ),
                        Row(
                            "",
                            "2015.05.01",
                            place="column",
                            align="right",
                            dateOfIssue="2015-05-01",
                        ),
                    ),
                ),
            ),
        ),
    )


BUILDERS = {"id_card": id_card, "address_card": address_card}


def example(document: str, name: str, placement: str) -> Example:
    """One cell's page: a document, a holder, and a placement.

    The three uniform arms flatten every `Pair` into two ordinary rows, so that a control really
    is uniform — leaving the eID's `Nem/Sex:` and `Állampolgárság/Nationality:` sharing a line
    under `stacked` would be varying row packing alongside label placement.
    """
    built = BUILDERS[document](HOLDERS[name][document])
    style = _STYLE_FOR_PLACEMENT[placement]
    faces = built.submission.faces
    if placement != "specimen":
        faces = tuple(
            replace(
                face,
                elements=tuple(
                    element
                    for original in face.elements
                    for element in (
                        (original.left, original.right)
                        if isinstance(original, Pair)
                        else (original,)
                    )
                ),
            )
            for face in faces
        )
    return replace(
        built,
        key=f"prototype/{document}-{name}-{placement}",
        submission=replace(built.submission, faces=faces, style=style),  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------------------------------
# The driving licence, kept for the record rather than for this run: its legend axis is settled.
# --------------------------------------------------------------------------------------------

_LICENCE_NUMBER = "CM001267"

# 2013 wording. The line break falls after `4b.` — read off the rotated strip on the specimen,
# correcting the split this file used on the first pass.
_LEGEND_LINES = (
    "1. Családi név   2. Utónév   3. Születési idő és hely   4a. A kiállítás időpontja   "
    "4b. A lejárat időpontja",
    "4c. Kiállító hatóság   5. Az engedély száma   10. Érvényesség kezdete   "
    "11. Érvényesség vége   12. Kódok",
)

LEGEND_EXAMPLE = Example(
    key="prototype/driving_licence",
    document_type="hungarian_driving_licence",
    schema_version=1,
    absent=("address", "generalRestrictionCodes"),
    submission=Submission(
        faces=(
            Face(
                title=("MAGYARORSZÁG", "VEZETŐI ENGEDÉLY"),
                elements=(
                    Row("1.", "BÍRÓ", surname="BÍRÓ"),
                    Row("2.", "ILDIKÓ", givenNames="ILDIKÓ"),
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
            Face(
                elements=(
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
                                Cell("12.06.95.", dateOfFirstIssue="1995-06-12"),
                                Cell("30.11.27.", dateOfExpiry="2027-11-30"),
                                Cell("102", restrictionCodes=["102"]),
                            ),
                            (
                                Cell("A2", categoryCode="A2"),
                                Cell("05.02.13.", dateOfFirstIssue="2013-02-05"),
                                Cell("05.02.23.", dateOfExpiry="2023-02-05"),
                                Cell("186", restrictionCodes=["186"]),
                            ),
                        ),
                    ),
                    Row("14. Államp:", "HUN", nationality="HUN"),
                    Row("Sz.neve:", "BÍRÓ ILDIKÓ"),
                    Legend(_LEGEND_LINES, rotated=True),
                ),
            ),
        ),
    ),
)
