"""The shared fixture renderer (#51) — the machinery both fixture surfaces are drawn by.

These tests are pure: no Postgres, no Redis, no Model Provider. They pin the properties a
fixture surface depends on — that Hungarian actually prints, that identifiers can never
collide with real ones, and that an example's page and its `expected.json` cannot drift apart.
"""

import json
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
    Cell,
    Column,
    Example,
    Face,
    FixtureDoesNotFit,
    Row,
    Submission,
    Table,
    expectation,
    extracted_fields,
    fonts,
    identifiers,
    render_png_bytes,
    write_golden,
    write_sample,
)
from fixtures.catalogue import EXAMPLES
from fixtures.surfaces import GOLDEN_ROOT, REPO_ROOT, SAMPLE_ROOT

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


def test_generated_bank_account_number_is_giro_grouped_but_fails_its_check_digit():
    account = identifiers.bank_account_number("9876543", "1234567")

    # Two eight-digit groups, hyphen-separated, as a Hungarian invoice prints one (#43's
    # sellerBankAccountNumber description).
    assert re.fullmatch(r"\d{8}-\d{8}", account)
    assert not identifiers.bank_account_is_valid(account)
    assert identifiers.bank_account_is_valid(
        f"9876543{identifiers.bank_account_check_digit('9876543')}"
        f"-1234567{identifiers.bank_account_check_digit('1234567')}"
    )


def test_bank_account_check_digit_closes_its_group_to_a_multiple_of_ten():
    # The published rule is stated as a divisibility, not as a subtraction: weight an eight-digit
    # group by 9,7,3,1,9,7,3,1 and the products must sum to a multiple of ten. Worked here over
    # `1030000` + its check digit rather than trusting the constructor's own arithmetic.
    check = identifiers.bank_account_check_digit("1030000")
    weights = (9, 7, 3, 1, 9, 7, 3, 1)
    total = sum(int(d) * w for d, w in zip(f"1030000{check}", weights, strict=True))

    assert total % 10 == 0


def test_bank_account_validity_is_judged_group_by_group():
    sound = f"9876543{identifiers.bank_account_check_digit('9876543')}"
    other = f"1234567{identifiers.bank_account_check_digit('1234567')}"
    spoiled = f"{other[:7]}{(int(other[7]) + 1) % 10}"

    # Each eight-digit group carries its own check digit, so one sound group must not vouch for
    # a malformed neighbour, in either position.
    assert identifiers.bank_account_is_valid(f"{sound}-{other}")
    assert not identifiers.bank_account_is_valid(f"{sound}-{spoiled}")
    assert not identifiers.bank_account_is_valid(f"{spoiled}-{other}")


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


def _catalogued(key: str) -> Example:
    matching = [example for example in EXAMPLES if example.key == key]
    assert matching, f"no catalogued example keyed {key!r} — have {[e.key for e in EXAMPLES]}"
    return matching[0]


def test_a_table_carries_a_null_for_every_nested_key_it_prints_no_column_for():
    line_items = extracted_fields(_catalogued("invoice/sample"))["lineItems"]

    # ADR-0010 requires every nested property of an array Field to be present on every row, so a
    # column the page doesn't print still owes an explicit null rather than a missing key.
    assert [row["grossAmount"] for row in line_items] == [None, None]
    assert line_items[0]["netAmount"] == 102000


def test_the_happy_path_prints_a_forint_of_rounding_disagreement_between_its_two_blocks():
    fields = extracted_fields(_catalogued("invoice/happy_path"))
    line_vat = sum(row["vatAmount"] or 0 for row in fields["lineItems"])
    summary_vat = sum(row["vatAmount"] or 0 for row in fields["vatSummary"])
    summary_gross = sum(row["grossAmount"] or 0 for row in fields["vatSummary"])

    # #43 transcribes the ÁFA összesítő *and* the totals block though either could be derived
    # from the other, because NAV documents the two legitimately disagreeing by rounding: the
    # summary charges 27% on the summed net, the totals block adds up VAT already rounded per
    # line. This fixture is the one that makes that concrete, so a future change that reconciles
    # them — in the Schema, in the harness, or by "correcting" the data table — fails here
    # instead of quietly passing.
    assert fields["vatTotal"] == line_vat
    assert summary_vat == fields["vatTotal"] - 1
    assert summary_gross == fields["grossTotal"] - 1


def test_no_field_records_that_the_simplified_invoice_is_simplified():
    example = _catalogued("invoice/simplified")
    fields = extracted_fields(example)

    # The page says so twice — its title and its Áfa tv. 176. § note, as a real one does. What
    # #43 settled is that *no Field* carries either, so an extracted Document is readable as
    # simplified only by shape: a gross-only line with a null net.
    printed = " ".join(line for face in example.submission.faces for line in face.title)
    assert "EGYSZERŰSÍTETT" in printed
    assert not any("egyszer" in str(value).lower() for value in fields.values())
    assert all(row["netAmount"] is None and row["vatAmount"] is None for row in fields["lineItems"])
    assert all(row["grossAmount"] is not None for row in fields["lineItems"])
    assert (fields["netTotal"], fields["vatTotal"]) == (None, None)
    # The whole array null, not rows of nulls — a simplified invoice prints no breakdown table.
    assert fields["vatSummary"] is None
    assert fields["grossTotal"] == 8140


def test_vat_rate_carries_markings_an_enum_of_percentages_would_have_rejected():
    rates = {
        row["vatRate"]
        for key in ("invoice/happy_path", "invoice/simplified")
        for row in extracted_fields(_catalogued(key))["lineItems"]
    }

    # ADR-0010 refused `enum` outright, and `vatRate` is where that bites: a rate, a VAT-content
    # share of the gross, an exemption marking and a reverse-charge marking all print in the same
    # column. Anything narrower than a verbatim string fails a legitimate invoice.
    assert {"27%", "21,26%", "fordított adózás", "TAM"} <= rates


def test_rendering_the_same_example_twice_produces_identical_bytes():
    example = _address_card_example()

    # The images are committed, so a renderer that varied between runs would churn the repo on
    # every regeneration and make a real fixture change impossible to see in a diff.
    assert render_png_bytes(example) == render_png_bytes(example)


def _one_cell_sheet(heading: str, printed: str, width: int) -> Example:
    return Example(
        key="probe/one_cell",
        document_type="invoice",
        schema_version=2,
        submission=Submission(
            style="sheet",
            faces=(
                Face(
                    elements=(
                        Table(
                            into="lineItems",
                            columns=(Column(heading, width),),
                            rows=((Cell(printed, description=printed),),),
                        ),
                    ),
                ),
            ),
        ),
    )


def test_a_cell_wider_than_its_column_is_refused_rather_than_drawn_over_its_neighbour():
    # The far commoner failure than a table overrunning the page: one long description slides
    # under the next column's value, and both become unreadable while the expectation still
    # asserts each of them.
    with pytest.raises(FixtureDoesNotFit, match="Megnevezés"):
        render_png_bytes(_one_cell_sheet("Megnevezés", "Építési-szerelési munkadíj, 2026. II. n.év", 200))


def test_a_column_heading_too_wide_for_its_own_column_is_refused_too():
    with pytest.raises(FixtureDoesNotFit, match="heading"):
        render_png_bytes(_one_cell_sheet("ÁFA összeg mindösszesen", "27 635", 120))


def test_a_cell_that_fits_its_column_draws_without_complaint():
    assert render_png_bytes(_one_cell_sheet("Megnevezés", "Fenyő palló", 320)).startswith(b"\x89PNG")


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


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.key)
def test_every_catalogued_example_fits_the_page_it_is_drawn_into(example: Example):
    # The renderer's refusals — a table wider than the page, a cell wider than its column, a face
    # taller than its geometry — only fire while drawing, so a catalogue entry nothing renders is
    # a catalogue entry nothing checks.
    assert render_png_bytes(example).startswith(b"\x89PNG")


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


@pytest.mark.parametrize(
    "example", [e for e in EXAMPLES if e.golden], ids=lambda example: example.key
)
def test_the_committed_golden_example_matches_a_fresh_projection(example: Example):
    # A golden directory is what the billed eval run actually reads, so it is the copy that must
    # not drift — and unlike the sample it was, until #56, never pinned to its data table at all.
    directory = GOLDEN_ROOT / example.key
    stale = f"eval/golden/{example.key} is stale — run `uv run python -m fixtures.generate`"

    assert (directory / "submission.png").read_bytes() == render_png_bytes(example), stale
    assert json.loads((directory / "expected.json").read_text()) == expectation(example), stale
