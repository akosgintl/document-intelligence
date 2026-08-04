"""The shared fixture renderer (#51) — the machinery both fixture surfaces are drawn by.

These tests are pure: no Postgres, no Redis, no Model Provider. They pin the properties a
fixture surface depends on — that Hungarian actually prints, that identifiers can never
collide with real ones, and that an example's page and its `expected.json` cannot drift apart.
"""

import re
from dataclasses import replace
from datetime import date
from pathlib import Path

import jsonschema
import pytest
from PIL import Image, ImageDraw

from document_intelligence.schema_registry import SchemaRegistry
from eval.run_eval import load_golden_examples
from fixtures import (
    Example,
    Face,
    Row,
    Submission,
    expectation,
    extracted_fields,
    fonts,
    identifiers,
    render_png_bytes,
    write_golden,
    write_sample,
)
from fixtures.catalogue import EXAMPLES
from fixtures.surfaces import REPO_ROOT, SAMPLE_ROOT

# Every accented character the five Document Types' values need. `ImageFont.load_default()`
# draws all of these as one identical `.notdef` box (#46), which is why DejaVu is vendored.
HUNGARIAN_ACCENTS = "ŐŰÉÁÖÜőűéáöü"


def _glyph_bitmap(font, character: str) -> bytes:
    image = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(image).text((8, 8), character, font=font, fill=255)
    return image.tobytes()


def test_vendored_font_draws_each_hungarian_accent_distinctly():
    font = fonts.sans(32)

    bitmaps = {character: _glyph_bitmap(font, character) for character in HUNGARIAN_ACCENTS}

    assert len(set(bitmaps.values())) == len(HUNGARIAN_ACCENTS)


def test_generated_tax_number_is_shaped_like_an_adoszam_but_fails_its_check_digit():
    tax_number = identifiers.tax_number("1234567", vat_code=1, county=42)

    assert re.fullmatch(r"\d{8}-\d-\d{2}", tax_number)
    assert not identifiers.tax_number_is_valid(tax_number)
    # Correcting only the check digit makes the same value valid — which is what shows the
    # validator rejected it for its check digit alone, and not for some other malformation.
    assert identifiers.tax_number_is_valid(f"1234567{identifiers.tax_number_check_digit('1234567')}-1-42")


def test_generated_personal_identifier_is_hyphen_grouped_but_fails_its_check_digit():
    personal_identifier = identifiers.personal_identifier(
        sex_code=2, date_of_birth=date(1982, 3, 14), serial=447
    )

    # `N-YYMMDD-NNNN` — the address card prints it grouped, not as a bare eleven-digit run (#47).
    assert re.fullmatch(r"\d-\d{6}-\d{4}", personal_identifier)
    assert personal_identifier.startswith("2-820314-447")
    assert not identifiers.personal_identifier_is_valid(personal_identifier)
    assert identifiers.personal_identifier_is_valid(
        f"2-820314-447{identifiers.personal_identifier_check_digit('2820314447')}"
    )


def test_icao_check_digit_follows_the_published_weighting():
    # ICAO Doc 9303's 7-3-1 weighting, worked by hand over "123456789":
    # 1*7 + 2*3 + 3*1 + 4*7 + 5*3 + 6*1 + 7*7 + 8*3 + 9*1 = 147, and 147 mod 10 = 7.
    assert identifiers.icao_check_digit("123456789") == "7"
    # `<` counts as zero and letters continue the alphabet from ten, so A is 10: 10*7 = 70.
    assert identifiers.icao_check_digit("<<A") == "0"


def test_icao_check_digit_refuses_a_character_the_zone_alphabet_has_no_weight_for():
    with pytest.raises(ValueError, match="not an MRZ character"):
        identifiers.icao_check_digit("KOVACS-TOKE")


def test_generated_passport_mrz_has_td3_geometry_but_no_check_digit_that_verifies():
    lines = identifiers.mrz_td3(
        document_code="P",
        issuing_state="HUN",
        surname="KOVACS-TOKE",
        given_names="ORSEBET URMOS",
        document_number="MI1234567",
        nationality="HUN",
        date_of_birth=date(1982, 3, 14),
        sex="F",
        date_of_expiry=date(2032, 3, 14),
    )

    assert len(lines) == 2
    assert [len(line) for line in lines] == [44, 44]
    printed_document_number, printed_check_digit = lines[1][:9], lines[1][9]
    assert printed_document_number == "MI1234567"
    assert printed_check_digit != identifiers.icao_check_digit(printed_document_number)


def test_generated_identity_card_mrz_has_td1_geometry():
    lines = identifiers.mrz_td1(
        document_code="ID",
        issuing_state="HUN",
        surname="KOVACS-TOKE",
        given_names="ORSEBET URMOS",
        document_number="123456MI",
        nationality="HUN",
        date_of_birth=date(1982, 3, 14),
        sex="F",
        date_of_expiry=date(2031, 3, 14),
    )

    assert [len(line) for line in lines] == [30, 30, 30]
    # The zone alphabet is A-Z, 0-9 and `<` only, so the hyphen of `KOVÁCS-TŐKE` becomes a filler.
    assert lines[2].startswith("KOVACS<TOKE<<ORSEBET<URMOS")


def _address_card_example() -> Example:
    """A cut-down address card: enough of a data table to exercise every way a Field is proven."""
    return Example(
        key="hungarian_address_card/example",
        document_type="hungarian_address_card",
        schema_version=1,
        submission=Submission(
            faces=(
                Face(
                    title=("LAKCÍMET IGAZOLÓ HATÓSÁGI IGAZOLVÁNY",),
                    elements=(
                        Row("Családi és utónév:", "KOVÁCS-TŐKE ŐRSÉBET ÜRMÖS", surname="KOVÁCS-TŐKE",
                            givenNames="ŐRSÉBET ÜRMÖS"),
                        # One printed label, two values, two Fields — the card really does print
                        # place and date of birth on one line with no space after the comma (#47).
                        Row("Születési hely,idő:", "DEBRECEN, 1982.03.14", placeOfBirth="DEBRECEN",
                            dateOfBirth="1982-03-14"),
                        Row("Lakóhely:", "4025 DEBRECEN, PIAC UTCA 14.",
                            residence="4025 DEBRECEN, PIAC UTCA 14."),
                    ),
                ),
            ),
        ),
        absent=("temporaryResidence",),
    )


def test_expectation_is_projected_from_the_same_rows_that_draw_the_page():
    assert expectation(_address_card_example()) == {
        "document_type": "hungarian_address_card",
        "schema_version": 1,
        "fields": {
            "surname": "KOVÁCS-TŐKE",
            "givenNames": "ŐRSÉBET ÜRMÖS",
            "placeOfBirth": "DEBRECEN",
            "dateOfBirth": "1982-03-14",
            "residence": "4025 DEBRECEN, PIAC UTCA 14.",
            "temporaryResidence": None,
        },
    }


def test_a_table_carries_a_null_for_every_nested_key_it_prints_no_column_for():
    line_items = extracted_fields(EXAMPLES[0])["lineItems"]

    # ADR-0010 requires every nested property of an array Field to be present on every row, so a
    # column the page doesn't print still owes an explicit null rather than a missing key.
    assert [row["grossAmount"] for row in line_items] == [None, None]
    assert line_items[0]["netAmount"] == 102000


def test_rendering_the_same_example_twice_produces_identical_bytes():
    example = _address_card_example()

    # The images are committed, so a renderer that varied between runs would churn the repo on
    # every regeneration and make a real fixture change impossible to see in a diff.
    assert render_png_bytes(example) == render_png_bytes(example)


def _one_row_card(printed: str) -> Example:
    return Example(
        key="probe/one_row",
        document_type="hungarian_address_card",
        schema_version=1,
        submission=Submission(faces=(Face(elements=(Row("Családi és utónév:", printed),)),)),
    )


def test_accented_values_reach_the_page_rather_than_becoming_notdef_boxes():
    # Two pages differing only in their accents. Under `ImageFont.load_default()` they render
    # byte-identically: every accented character collapses to the same `.notdef` box (#46).
    assert render_png_bytes(_one_row_card("ŐRSÉBET ÜRMÖS")) != render_png_bytes(
        _one_row_card("ORSEBET URMOS")
    )


def test_a_written_golden_example_is_one_the_eval_harness_can_load(tmp_path: Path):
    example = _address_card_example()

    write_golden(example, tmp_path)

    loaded = load_golden_examples(tmp_path)
    assert [one.name for one in loaded] == ["hungarian_address_card/example"]
    assert loaded[0].submission_path.name == "submission.png"
    assert loaded[0].expected_document_type == "hungarian_address_card"
    assert loaded[0].expected_schema_version == 1
    assert loaded[0].expected_fields["surname"] == "KOVÁCS-TŐKE"
    assert loaded[0].expected_fields["temporaryResidence"] is None


def test_a_written_sample_gives_manual_test_both_a_png_and_a_pdf(tmp_path: Path):
    example = replace(_address_card_example(), sample="address_card")

    write_sample(example, tmp_path)

    assert (tmp_path / "address_card.png").read_bytes().startswith(b"\x89PNG")
    assert (tmp_path / "address_card.pdf").read_bytes().startswith(b"%PDF")


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.key)
def test_every_catalogued_example_asserts_only_fields_its_schema_defines(example: Example):
    registry = SchemaRegistry.load(REPO_ROOT / "schemas")
    properties = registry.get(example.document_type, example.schema_version).schema.json_schema[
        "properties"
    ]

    for name, value in extracted_fields(example).items():
        assert name in properties, f"{name} is not a Field of {example.document_type}"
        jsonschema.validate(value, properties[name])


@pytest.mark.parametrize(
    "example", [e for e in EXAMPLES if e.sample], ids=lambda example: example.key
)
def test_the_committed_sample_matches_a_fresh_render(example: Example):
    # The other half of convention 7: the expectation can't drift from the data table, and this
    # stops the committed *image* drifting from it either. Run `uv run python -m fixtures.generate`.
    committed = (SAMPLE_ROOT / f"{example.sample}.png").read_bytes()

    assert committed == render_png_bytes(example), (
        f"{example.sample}.png is stale — regenerate it with `uv run python -m fixtures.generate`"
    )
