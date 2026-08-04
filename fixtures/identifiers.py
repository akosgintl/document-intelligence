"""Identifiers for synthetic fixtures: the right shape, the wrong check digit.

Every identifier a fixture prints is built here, and every one of them carries a **deliberately
invalid check digit**. That is not an oversight and must not be "fixed" — see `_BREAK` below.

Each family exposes three things: the published check-digit algorithm, a validator built on it,
and a constructor that produces a correctly-shaped value the validator rejects. The validators
exist so the tests can *prove* the fixtures are uncollidable rather than asserting it in a
comment, and so that a future fixture author can check their own hand-written value.
"""

from datetime import date

# Adding this to a correct check digit is what makes every identifier here unissuable. Any
# non-zero offset would do; the value matters less than that it is applied in exactly one place.
_BREAK = 1


def _broken(check_digit: str) -> str:
    """Shift a correct check digit to a wrong one.

    DO NOT REMOVE THIS CALL to make an identifier "valid". A fixture identifier that passed its
    check digit could — by construction, not by accident — be a real person's személyi azonosító
    or a real company's adószám. These fixtures are committed to a public repo and fed to a
    Model Provider, so they must be impossible to confuse with the real thing. Extraction is
    transcription: the Schemas explicitly say not to compute, correct or verify check digits, so
    a wrong one costs the eval nothing (#46, convention 8).
    """
    return str((int(check_digit) + _BREAK) % 10)


# --- adószám (Hungarian tax number) -------------------------------------------------------
#
# Printed as `12345678-1-42`: a seven-digit base plus its check digit, then a one-digit VAT code,
# then a two-digit county code. The check digit is weighted 9,7,3,1,9,7,3 over the base, summed,
# and subtracted from the next multiple of ten.


_WEIGHTS_9731 = (9, 7, 3, 1, 9, 7, 3)


def _check_digit_9731(base: str, *, what: str) -> str:
    """The digit that closes a seven-digit base weighted 9,7,3,1,9,7,3 to a multiple of ten.

    Shared by the adószám and the bank account number's GIRO CDV, which are separate schemes
    that happen to have been specified with the same weighting — not one derived from the other.
    Kept in one place because a transcription slip in either copy would be invisible: both
    produce a plausible digit for every input.
    """
    if len(base) != 7 or not base.isdigit():
        raise ValueError(f"{what} is seven digits, got {base!r}")
    total = sum(int(digit) * weight for digit, weight in zip(base, _WEIGHTS_9731, strict=True))
    return str((10 - total % 10) % 10)


def tax_number_check_digit(base: str) -> str:
    """The published check digit for an adószám's seven-digit base."""
    return _check_digit_9731(base, what="an adószám base")


def tax_number_is_valid(value: str) -> bool:
    """Whether a printed adószám carries its correct check digit."""
    base_with_check = value.split("-")[0]
    if len(base_with_check) != 8 or not base_with_check.isdigit():
        return False
    return base_with_check[7] == tax_number_check_digit(base_with_check[:7])


def tax_number(base: str, *, vat_code: int, county: int) -> str:
    """An adószám shaped exactly as one is printed, with a check digit that cannot be right."""
    return f"{base}{_broken(tax_number_check_digit(base))}-{vat_code}-{county:02d}"


# --- személyi azonosító (Hungarian personal identification number) -------------------------
#
# Eleven digits, printed on the address card hyphen-grouped as `N-YYMMDD-NNNN` (#47). The first
# digit encodes sex and century of birth, the next six the date of birth, then a three-digit
# serial and a check digit weighted 1..10 over the preceding ten digits, modulo eleven.


def personal_identifier_check_digit(first_ten: str) -> str:
    """The published check digit for a személyi azonosító's first ten digits."""
    if len(first_ten) != 10 or not first_ten.isdigit():
        raise ValueError(f"a személyi azonosító's base is ten digits, got {first_ten!r}")
    total = sum(int(digit) * weight for weight, digit in enumerate(first_ten, start=1))
    remainder = total % 11
    if remainder == 10:
        # Such a number is never issued, so a fixture must not build one — it would be
        # unbreakable, and an identifier this module cannot make invalid is a trap.
        raise ValueError(f"{first_ten!r} yields no valid check digit; choose another serial")
    return str(remainder)


def personal_identifier_is_valid(value: str) -> bool:
    """Whether a printed személyi azonosító carries its correct check digit."""
    digits = value.replace("-", "")
    if len(digits) != 11 or not digits.isdigit():
        return False
    try:
        return digits[10] == personal_identifier_check_digit(digits[:10])
    except ValueError:
        return False


def personal_identifier(*, sex_code: int, date_of_birth: date, serial: int) -> str:
    """A személyi azonosító as the address card prints it, with an unissuable check digit."""
    first_ten = f"{sex_code}{date_of_birth:%y%m%d}{serial:03d}"
    broken = _broken(personal_identifier_check_digit(first_ten))
    return f"{first_ten[0]}-{first_ten[1:7]}-{first_ten[7:]}{broken}"


# --- pénzforgalmi jelzőszám (Hungarian bank account number) --------------------------------
#
# Printed as `12345678-12345678`, or with a third group where the account needs one. Every group
# stands alone: weight its eight digits 9,7,3,1,9,7,3,1 and the products sum to a multiple of
# ten, which makes the eighth digit of each group its check digit.
#
# The first group's first seven digits are a routing code — three digits of bank, four of branch
# — and breaking a check digit cannot make those seven anything other than what they are, so a
# fixture cannot avoid resembling *some* real branch. What the broken eighth digit buys is that
# the printed number is not a valid account number anywhere, which is what stops it colliding
# with somebody's actual account.


def bank_account_check_digit(base: str) -> str:
    """The published check digit for one eight-digit group's seven-digit base."""
    return _check_digit_9731(base, what="a bank account group's base")


def bank_account_is_valid(value: str) -> bool:
    """Whether every group of a printed account number carries its correct check digit."""
    groups = value.split("-")
    if not groups or any(len(group) != 8 or not group.isdigit() for group in groups):
        return False
    return all(group[7] == bank_account_check_digit(group[:7]) for group in groups)


def bank_account_number(*bases: str) -> str:
    """An account number grouped as one is printed, with no group's check digit correct."""
    if not bases:
        raise ValueError("an account number needs at least one eight-digit group")
    return "-".join(f"{base}{_broken(bank_account_check_digit(base))}" for base in bases)


# --- machine-readable zone (ICAO Doc 9303) -------------------------------------------------
#
# TD1 is the three-line, thirty-column zone on an ID-1 card; TD3 the two-line, forty-four-column
# zone on a passport data page. Both pad with `<` and carry check digits over their own fields
# plus one composite. The Schemas model the zone as verbatim characters and explicitly forbid
# computing or correcting its check digits, so breaking them here costs the eval nothing.

FILLER = "<"


def _mrz_value(character: str) -> int:
    if character == FILLER:
        return 0
    if character.isdigit():
        return int(character)
    if "A" <= character <= "Z":
        return ord(character) - ord("A") + 10
    # 9303's zone alphabet is exactly A-Z, 0-9 and `<`. Anything else has no defined weight, and
    # letting it through would silently produce a check digit no reader could reproduce.
    raise ValueError(f"{character!r} is not an MRZ character")


def icao_check_digit(data: str) -> str:
    """The published 7-3-1 check digit over an MRZ field."""
    weights = (7, 3, 1)
    total = sum(_mrz_value(character) * weights[index % 3] for index, character in enumerate(data))
    return str(total % 10)


# ICAO Doc 9303 Part 3, §6.A "Transliteration of Multinational Latin-based Characters", for
# every accented letter Hungarian prints. Each of these carries exactly *one* recommended
# transliteration in that table, including both double-acutes — `Ő` (U+0150) is listed as `O`
# and `Ű` (U+0170) as `U`, with no two-letter variant offered.
_TRANSLITERATION = {
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ő": "O",
    "Ú": "U",
    "Ű": "U",
}

# The characters §6.A gives *more than one* recommended transliteration for. The choice belongs
# to the issuing State, and neither #47's PRADO transcription nor #48's statute pass found a
# Hungarian specimen or rule that settles it, so a fixture cannot know which one Hungary writes.
_STATE_DEPENDENT = {
    "Ö": "OE or O",
    "Ü": "UE or UXX or U",
    "Ä": "AE or A",
    "Å": "AA or A",
    "Ñ": "N or NXX",
}


class AmbiguousTransliteration(Exception):
    """A name carries a character 9303 does not transliterate one way.

    Raised rather than guessed: a fixture asserting `TOEROEK` where Hungary writes `TOROK` is a
    wrong expectation wearing a standard's clothes, and the eval would blame the model for it.
    """


def _transliterate(name: str) -> str:
    """A name as the zone spells it: diacritics resolved per 9303, separators turned to fillers.

    9303-3 §4.6 requires the MRZ name "without diacritical marks", and leaves the issuing State
    to transliterate national characters into the zone's A–Z alphabet; §6.A is the table it
    transliterates them *to*. For the letters that make a name Hungarian that table is
    unambiguous — `Á→A`, `É→E`, `Í→I`, `Ó→O`, `Ú→U`, and both double-acutes, `Ő→O` and `Ű→U`.
    The genuine Hungarian specimen transcribed in
    `docs/research/hungarian-passport-field-layout.md` §7.4 agrees: its VIZ prints `ROZÁLIA` and
    its zone reads `ROZALIA`.

    `Ö` and `Ü` are the exception and are refused — see `_STATE_DEPENDENT`.

    Separators follow §4.6 as already recorded in that same research note: a hyphen or a space
    becomes one filler, an apostrophe is dropped with no filler at all. So `KOVÁCS-TŐKE` is
    written `KOVACS<TOKE` and `O'BRIEN` is written `OBRIEN`.
    """
    name = name.upper()
    ambiguous = sorted({character for character in name if character in _STATE_DEPENDENT})
    if ambiguous:
        detail = ", ".join(f"{c!r} ({_STATE_DEPENDENT[c]})" for c in ambiguous)
        raise AmbiguousTransliteration(
            f"{name!r} carries {detail} — 9303 §6.A offers more than one transliteration and the "
            f"choice is the issuing State's, which no Hungarian source settles. Choose a name "
            f"without it rather than asserting a zone the document may not print."
        )

    zone = "".join(
        FILLER if character in " -" else _TRANSLITERATION.get(character, character)
        for character in name
        if character != "'"
    )
    unwritable = sorted({c for c in zone if c != FILLER and not ("A" <= c <= "Z")})
    if unwritable:
        raise AmbiguousTransliteration(
            f"{name!r} transliterates to {zone!r}, which is not writable in the zone's A-Z "
            f"alphabet: {unwritable}. Add the character to _TRANSLITERATION with its 9303 §6.A "
            f"row, or use a name without it."
        )
    return zone


def _mrz_name(surname: str, given_names: str, width: int) -> str:
    """`SURNAME<<GIVEN<NAMES`, truncated and padded to width."""
    name = f"{_transliterate(surname)}{FILLER * 2}{_transliterate(given_names)}"
    return name[:width].ljust(width, FILLER)


def mrz_td3(
    *,
    document_code: str,
    issuing_state: str,
    surname: str,
    given_names: str,
    document_number: str,
    nationality: str,
    date_of_birth: date,
    sex: str,
    date_of_expiry: date,
    optional_data: str = "",
) -> list[str]:
    """A passport data page's two-line zone, every check digit deliberately wrong."""
    line1 = f"{document_code.ljust(2, FILLER)}{issuing_state}{_mrz_name(surname, given_names, 39)}"

    number = document_number.ljust(9, FILLER)
    birth = f"{date_of_birth:%y%m%d}"
    expiry = f"{date_of_expiry:%y%m%d}"
    optional = optional_data.ljust(14, FILLER)

    number_check = _broken(icao_check_digit(number))
    birth_check = _broken(icao_check_digit(birth))
    expiry_check = _broken(icao_check_digit(expiry))
    optional_check = _broken(icao_check_digit(optional))
    composite = _broken(
        icao_check_digit(
            f"{number}{number_check}{birth}{birth_check}{expiry}{expiry_check}{optional}{optional_check}"
        )
    )

    line2 = (
        f"{number}{number_check}{nationality}{birth}{birth_check}{sex}"
        f"{expiry}{expiry_check}{optional}{optional_check}{composite}"
    )
    return [line1, line2]


def mrz_td1(
    *,
    document_code: str,
    issuing_state: str,
    surname: str,
    given_names: str,
    document_number: str,
    nationality: str,
    date_of_birth: date,
    sex: str,
    date_of_expiry: date,
    optional_data: str = "",
    optional_data_2: str = "",
) -> list[str]:
    """An ID-1 card's three-line zone, every check digit deliberately wrong."""
    number = document_number.ljust(9, FILLER)
    number_check = _broken(icao_check_digit(number))
    line1 = (
        f"{document_code.ljust(2, FILLER)}{issuing_state}{number}{number_check}"
        f"{optional_data.ljust(15, FILLER)}"
    )

    birth = f"{date_of_birth:%y%m%d}"
    expiry = f"{date_of_expiry:%y%m%d}"
    birth_check = _broken(icao_check_digit(birth))
    expiry_check = _broken(icao_check_digit(expiry))
    optional2 = optional_data_2.ljust(11, FILLER)
    composite = _broken(
        icao_check_digit(
            f"{line1[5:30]}{birth}{birth_check}{expiry}{expiry_check}{optional2}"
        )
    )
    line2 = f"{birth}{birth_check}{sex}{expiry}{expiry_check}{nationality}{optional2}{composite}"

    return [line1, line2, _mrz_name(surname, given_names, 30)]
