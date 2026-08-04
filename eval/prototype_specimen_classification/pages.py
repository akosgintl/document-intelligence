"""PROTOTYPE — crude synthetic pages for the #49 probe. Not the fixture renderer (#51).

Deliberately crude: no expected.json, no data/page projection, no shared abstraction. This
draws something plausible enough to ask "does it classify", and nothing more. Every value
carries a deliberately invalid check digit (convention 8) so a probe page can never collide
with a real identifier.

Labels are transcribed from docs/research/hungarian-document-printed-labels.md (#47).
"""

import io
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# The system copy, on purpose — vendoring DejaVu into the repo is #51's job. ImageFont
# .load_default() renders Ő/Ö/Ű/Ü/é/á as one identical .notdef box, so it cannot draw any
# of these pages at all.
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
SANS = FONT_DIR / "DejaVuSans.ttf"
SANS_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
MONO = FONT_DIR / "DejaVuSansMono.ttf"


@dataclass(frozen=True)
class Variant:
    """One point in the ticket's 2x2x2 axis space."""

    specimen: bool  # MINTA / SPECIMEN overlay
    photo: bool  # photo placeholder box
    chrome: bool  # card outline + field grid, versus bare text on white

    @property
    def key(self) -> str:
        return "".join(
            letter if flag else "-"
            for letter, flag in (("S", self.specimen), ("P", self.photo), ("C", self.chrome))
        )

    @property
    def description(self) -> str:
        parts = [
            "MINTA overlay" if self.specimen else "no overlay",
            "photo box" if self.photo else "no photo",
            "card chrome" if self.chrome else "bare text",
        ]
        return ", ".join(parts)


VARIANTS: tuple[Variant, ...] = tuple(
    Variant(specimen=s, photo=p, chrome=c)
    for s in (False, True)
    for p in (False, True)
    for c in (False, True)
)


@dataclass(frozen=True)
class Face:
    title: list[str]
    rows: list[tuple[str, str]]
    mrz: list[str] = field(default_factory=list)
    wants_photo: bool = False


@dataclass(frozen=True)
class DocumentSpec:
    """A Document Type's probe page. `type_name` is the Schema Registry name it should classify as."""

    type_name: str
    label: str
    faces: list[Face]


# Shared holder, chosen to exercise Ő Ű É Á Ö Ü and a hyphenated surname.
_MRZ_NAME = "KOVACS<TOKE<<ORSEBET<URMOS"

DOCUMENTS: dict[str, DocumentSpec] = {
    "id_card": DocumentSpec(
        type_name="hungarian_id_card",
        label="Identity card (2016/2021 eID, both faces)",
        faces=[
            Face(
                title=["MAGYARORSZÁG / HUNGARY", "SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY / IDENTITY CARD"],
                wants_photo=True,
                rows=[
                    ("Családi és utónév/Family name and Given name:", "KOVÁCS-TŐKE ŐRSÉBET ÜRMÖS"),
                    ("Nem/Sex:", "NŐ/F"),
                    ("Állampolgárság/Nationality:", "HUN"),
                    # The eID prints birth and expiry space-separated with no dots, and the
                    # issue date on the verso as YYYY.MM.DD — two formats on one card.
                    ("Születési idő/Date of birth:", "14 03 1982"),
                    ("Érvényességi idő/Date of expiry:", "14 03 2031"),
                    ("Okmányazonosító/Doc. No.:", "123456MI"),
                    ("CAN:", "481920"),
                    ("Aláírás/Signature:", "Kovács-Tőke Őrsébet"),
                ],
            ),
            Face(
                title=[],
                rows=[
                    ("Születési hely/Place of birth:", "DEBRECEN (MAGYARORSZÁG)"),
                    (
                        "Születési családi és utónév/Family name and Given name at birth:",
                        "SZŰCS ŐRSÉBET",
                    ),
                    ("Anyja születési neve/Mother's maiden name:", "NAGY ÉVA ILDIKÓ"),
                    ("Kiállító hatóság/Issuing authority:", "BELÜGYMINISZTÉRIUM"),
                    ("", "2021.09.01"),
                ],
                # TD1, 3x30. Check digits are wrong on purpose (convention 8) — do not "fix" them.
                mrz=[
                    "IDHUN123456MI30" + "<" * 15,
                    "8203140F3103140HUN" + "<" * 11 + "0",
                    _MRZ_NAME + "<" * 4,
                ],
            ),
        ],
    ),
    "passport": DocumentSpec(
        type_name="hungarian_passport",
        label="Passport (data page)",
        faces=[
            Face(
                title=["MAGYARORSZÁG", "ÚTLEVÉL / PASSPORT"],
                wants_photo=True,
                rows=[
                    ("Típus / Type / Type", "P"),
                    ("Kód / Code / Code", "HUN"),
                    ("Útlevélszám / Passport number / Numéro du passeport", "MI1234567"),
                    ("Családi név / Surname / Nom (1)", "KOVÁCS-TŐKE"),
                    ("Utónév(-ek) / Given names / Prénoms (2)", "ŐRSÉBET ÜRMÖS"),
                    ("Születési név / Birth name / Nom à la naissance (11)", "SZŰCS ŐRSÉBET"),
                    ("Állampolgárság / Nationality / Nationalité (3)", "MAGYAR/HUNGARIAN"),
                    # The passport prints every date as DD MMM/MMM YY with a bilingual month.
                    ("Születési idő / Date of birth / Date de naissance (4)", "14 MÁR/MAR 82"),
                    ("Nem / Sex / Sexe (5)", "N/F"),
                    ("Születési hely / Place of birth / Lieu de naissance (6)", "DEBRECEN"),
                    ("Kiállítási dátum / Date of issue / Date de délivrance (7)", "14 MÁR/MAR 22"),
                    # The bracketed numbers on these last three are unread at PRADO's 600px
                    # (#47) and deliberately not invented here.
                    ("Érvényességi idő / Date of expiry / Date d'expiration", "14 MÁR/MAR 32"),
                    ("Kiállító hatóság / Authority / Autorité", "KEK KH"),
                    ("Aláírás / Holder's signature / Signature du titulaire", "Kovács-Tőke Őrsébet"),
                ],
                # TD3, 2x44. Check digits deliberately invalid (convention 8).
                mrz=[
                    "P<HUN" + _MRZ_NAME + "<" * 13,
                    "MI12345670HUN8203140F3203140" + "<" * 14 + "00",
                ],
            )
        ],
    ),
    "address_card": DocumentSpec(
        type_name="hungarian_address_card",
        label="Address card (lakcímkártya, both faces)",
        # The control for the photo axis: this Schema says "carrying no photograph", so a
        # photo box here is the *wrong* thing rather than the missing thing.
        faces=[
            Face(
                title=["LAKCÍMET IGAZOLÓ HATÓSÁGI IGAZOLVÁNY", "000102 YL"],
                rows=[
                    ("Családi és utónév:", "KOVÁCS-TŐKE ŐRSÉBET ÜRMÖS"),
                    ("Születési név:", "SZŰCS ŐRSÉBET"),
                    ("Születési hely,idő:", "DEBRECEN, 1982.03.14"),
                    ("Anyja neve:", "NAGY ÉVA ILDIKÓ"),
                    ("Lakóhely:", "4025 DEBRECEN, PIAC UTCA 14. 3. em. 2."),
                    ("Bejelentési idő:", "2015.06.02"),
                    ("Tartózkodási hely:", "1075 BUDAPEST, KÁROLY KÖRÚT 9."),
                    ("Bejelentési idő:", "2021.11.30"),
                    ("Érvényességi ideje:", "HATÁROZATLAN"),
                    ("Kiállító hatóság:", "NYILVÁNTARTÓ HIVATAL"),
                    ("", "2021.12.01"),
                ],
            ),
            Face(
                title=["MAGYARORSZÁG", "SZEMÉLYI AZONOSÍTÓT IGAZOLÓ HATÓSÁGI IGAZOLVÁNY"],
                rows=[
                    # Hyphen-grouped N-YYMMDD-NNNN, with a deliberately invalid check digit.
                    ("Személyi azonosító:", "2-820314-4471"),
                    ("Családi és utónév:", "KOVÁCS-TŐKE ŐRSÉBET ÜRMÖS"),
                ],
            ),
        ],
    ),
    "driving_licence": DocumentSpec(
        type_name="hungarian_driving_licence",
        label="Driving licence (both faces)",
        # The licence prints no labels beside its values — only bare EU numbers, with the
        # wording in a legend. That is the hardest classification signal of the four.
        faces=[
            Face(
                # The multilingual stripe is from the Directive 2006/126/EC model, not from
                # PRADO — #47 transcribed the legend, not the stripe. #48 should source it.
                title=[
                    "EURÓPAI UNIÓ — MAGYARORSZÁG",
                    "VEZETŐI ENGEDÉLY · DRIVING LICENCE · PERMIS DE CONDUIRE",
                ],
                wants_photo=True,
                rows=[
                    ("1.", "KOVÁCS-TŐKE"),
                    ("2.", "ŐRSÉBET ÜRMÖS"),
                    ("3.", "1982.03.14. DEBRECEN"),
                    ("4a.", "2021.05.11."),
                    ("4b.", "2031.05.11."),
                    ("4c.", "BUDAPEST FŐVÁROS KORMÁNYHIVATALA"),
                    ("5.", "MI123456"),
                    ("7.", "Kovács-Tőke Őrsébet"),
                    ("9.", "AM A1 A2 A B"),
                ],
            ),
            Face(
                title=["9.        10.        11.        12."],
                rows=[
                    ("AM", "11.05.21        11.05.31"),
                    ("A1", "11.05.21        11.05.31"),
                    ("A2", "11.05.21        11.05.31"),
                    ("A", "11.05.21        11.05.31"),
                    ("B", "11.05.21        11.05.31        01."),
                    ("14. Államp:", "HUN"),
                    ("Sz.neve:", "KOVÁCS-TŐKE ŐRSÉBET ÜRMÖS"),
                    # The 2013 generation's legend — the only place the field names appear
                    # at all, since the recto prints bare numbers.
                    (
                        "1. Családi név  2. Utónév  3. Születési idő és hely  "
                        "4a. A kiállítás időpontja",
                        "4b. A lejárat időpontja  4c. Kiállító hatóság  5. Az engedély száma",
                    ),
                    (
                        "10. Érvényesség kezdete  11. Érvényesség vége  12. Kódok",
                        "12. 01. — Szemüveg vagy kontaktlencse",
                    ),
                ],
            ),
        ],
    ),
}


def render(spec: DocumentSpec, variant: Variant) -> bytes:
    """Draw one probe page as PNG bytes."""
    width = 1000
    margin = 40
    face_images = [_render_face(face, variant, width - 2 * margin) for face in spec.faces]
    height = margin + sum(img.height + margin for img in face_images)

    page = Image.new("RGB", (width, height), "white")
    y = margin
    for img in face_images:
        page.paste(img, (margin, y))
        y += img.height + margin

    buffer = io.BytesIO()
    page.save(buffer, format="PNG")
    return buffer.getvalue()


def _render_face(face: Face, variant: Variant, width: int) -> Image.Image:
    title_font = ImageFont.truetype(str(SANS_BOLD), 22)
    label_font = ImageFont.truetype(str(SANS), 13)
    value_font = ImageFont.truetype(str(SANS_BOLD), 19)
    mono_font = ImageFont.truetype(str(MONO), 17)

    # Label above value, the way the real cards print it — the bilingual labels are far too
    # long to sit beside their values.
    row_height = 44
    body_top = 30 + len(face.title) * 30
    height = body_top + len(face.rows) * row_height + (len(face.mrz) * 26 if face.mrz else 0) + 40

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    if variant.chrome:
        draw.rounded_rectangle((2, 2, width - 3, height - 3), radius=18, outline="black", width=3)

    text_left = 30
    photo_left = width
    photo_bottom = 0
    if variant.photo and face.wants_photo:
        photo_left, photo_bottom = width - 200, 250
        draw.rectangle((photo_left, 24, width - 30, photo_bottom), fill="#d0d0d0", outline="black", width=2)
        draw.text(((photo_left + width - 30) // 2, 140), "FOTÓ", font=value_font, fill="#606060", anchor="mm")

    y = 24
    for line in face.title:
        draw.text((text_left, y), line, font=title_font, fill="black")
        y += 30
    if face.title and variant.chrome:
        draw.line((text_left, y + 4, min(width - 30, photo_left - 20), y + 4), fill="black", width=2)

    y = body_top
    for label, value in face.rows:
        if variant.chrome:
            rule_right = photo_left - 20 if y < photo_bottom else width - 30
            draw.line((text_left, y + row_height - 6, rule_right, y + row_height - 6), fill="#b0b0b0")
        draw.text((text_left, y), label, font=label_font, fill="#303030")
        draw.text((text_left, y + 16), value, font=value_font, fill="black")
        y += row_height

    if face.mrz:
        y += 10
        for line in face.mrz:
            draw.text((text_left, y), line, font=mono_font, fill="black")
            y += 26

    if variant.specimen:
        image = _overlay_specimen(image)

    return image


def _overlay_specimen(image: Image.Image) -> Image.Image:
    """A diagonal MINTA / SPECIMEN wash, the way a real specimen is marked."""
    font = ImageFont.truetype(str(SANS_BOLD), 64)
    layer = Image.new("RGBA", (image.width * 2, image.height * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.text(
        (layer.width // 2, layer.height // 2),
        "MINTA / SPECIMEN",
        font=font,
        fill=(180, 20, 20, 120),
        anchor="mm",
    )
    rotated = layer.rotate(24, resample=Image.BICUBIC)
    cropped = rotated.crop(
        (
            image.width // 2,
            image.height // 2,
            image.width // 2 + image.width,
            image.height // 2 + image.height,
        )
    )
    combined = image.convert("RGBA")
    combined.alpha_composite(cropped)
    return combined.convert("RGB")
