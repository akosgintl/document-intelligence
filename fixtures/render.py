"""The other projection out of an Example's data table: the page itself.

Two geometries, one element vocabulary. `card` draws ID-1-proportioned faces with values stacked
under their labels, the way the real cards set them — the bilingual labels are far too long to
sit beside a value. `sheet` draws an A4-proportioned page with a label column, and is what an
invoice uses.

The four identity types share the `card` geometry rather than each getting its own layout —
#51's open question. The PRADO transcription (#47) settled it: all four print the same three
things, a title block, a run of label/value lines and an optional zone at the foot, and they
differ only in *what* those lines say. The address card is monolingual where the identity card
is bilingual and the passport trilingual, and the licence's "labels" are bare EU numbers, but
none of that is layout. A fifth geometry would only be needed by a document that stops being a
stack of labelled values. The conventions this enforces are recorded as an ADR by #50.

Deliberately low fidelity: text only, no photograph, no hologram, no OVD, no security printing,
and a MINTA / SPECIMEN wash across every page (#46, convention 2). #49 measured every fidelity
axis it tested as noise for classification, so nothing here needs to look convincing — only to
print the right words in the right places.
"""

import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont

from fixtures import fonts
from fixtures.model import Element, Example, Face, Mrz, Row, Submission, Table

MARGIN = 36
_INK = "black"
_LABEL_INK = "#303030"
_RULE = "#b0b0b0"
_COLUMN_GUTTER = 20


class FixtureDoesNotFit(Exception):
    """A face's content does not fit the geometry it was drawn into.

    Raised rather than clipped or overrun: a fixture whose page silently loses a value its
    `expected.json` still asserts is exactly the drift the data table exists to prevent.
    """


@dataclass(frozen=True)
class Geometry:
    """Everything that differs between an ID-1 card and an A4 sheet, in one place.

    Type sizes are in points at the geometry's own resolution — a card is drawn at ~300 dpi
    across 85.6 mm, a sheet at 150 dpi across A4, so the two scales are not comparable.
    """

    size: tuple[int, int]
    outlined: bool
    stacked: bool
    title: int
    label: int
    value: int
    mono: int
    row_height: int
    title_height: int
    mrz_height: int
    pad: int
    value_column: int = 0

    @property
    def usable_width(self) -> int:
        return self.size[0] - 2 * self.pad


CARD = Geometry(
    size=(1012, 638),  # ID-1: 85.6 x 53.98 mm at ~300 dpi
    outlined=True,
    stacked=True,
    title=26,
    label=15,
    value=23,
    mono=18,
    row_height=56,
    title_height=34,
    mrz_height=27,
    pad=28,
)

SHEET = Geometry(
    size=(1240, 1754),  # A4 at 150 dpi
    outlined=False,
    stacked=False,
    title=40,
    label=21,
    value=22,
    mono=20,
    row_height=40,
    title_height=52,
    mrz_height=30,
    pad=56,
    value_column=320,
)

GEOMETRIES: dict[str, Geometry] = {"card": CARD, "sheet": SHEET}


def _fitted(
    text: str,
    max_width: int,
    loader: Callable[[int], FreeTypeFont],
    size: int,
    minimum: int = 9,
) -> FreeTypeFont:
    """The largest of `loader`'s sizes at or below `size` that draws `text` inside `max_width`.

    Bilingual and trilingual labels are long — `Születési családi és utónév/Family name and Given
    name at birth:` is one real label. Shrinking to fit keeps a fixture legible where overflowing
    would push a value off the page while its expectation still asserted it.
    """
    while size > minimum:
        font = loader(size)
        if font.getlength(text) <= max_width:
            return font
        size -= 1
    return loader(minimum)


def _draw_elements(
    draw: ImageDraw.ImageDraw,
    elements: Sequence[Element],
    *,
    top: int,
    left: int,
    right: int,
    geometry: Geometry,
) -> int:
    """Draw every element top to bottom, returning the y the last one ended at."""
    y = top
    width = right - left
    for element in elements:
        match element:
            case Row():
                if geometry.stacked:
                    draw.text(
                        (left, y),
                        element.label,
                        font=_fitted(element.label, width, fonts.sans, geometry.label),
                        fill=_LABEL_INK,
                    )
                    draw.text(
                        (left, y + geometry.label + 6),
                        element.printed,
                        font=_fitted(element.printed, width, fonts.sans_bold, geometry.value),
                        fill=_INK,
                    )
                    rule_y = y + geometry.row_height - 8
                    draw.line((left, rule_y, right, rule_y), fill=_RULE)
                else:
                    value_left = left + geometry.value_column
                    draw.text(
                        (left, y),
                        element.label,
                        font=_fitted(element.label, geometry.value_column - 20, fonts.sans, geometry.label),
                        fill=_LABEL_INK,
                    )
                    draw.text(
                        (value_left, y),
                        element.printed,
                        font=_fitted(element.printed, right - value_left, fonts.sans_bold, geometry.value),
                        fill=_INK,
                    )
                y += geometry.row_height
            case Table():
                y = _draw_table(draw, element, top=y, left=left, right=right, geometry=geometry)
    return y


def _draw_table(
    draw: ImageDraw.ImageDraw,
    table: Table,
    *,
    top: int,
    left: int,
    right: int,
    geometry: Geometry,
) -> int:
    total = sum(column.width for column in table.columns)
    if total > right - left:
        raise FixtureDoesNotFit(
            f"table columns total {total}px but only {right - left}px is available — narrow them "
            f"rather than letting a column run off the page it is asserted from"
        )

    label_font = fonts.sans(geometry.label)
    value_font = fonts.sans_bold(geometry.value)

    def _cells(printed: Sequence[str], font: FreeTypeFont, ink: str, y: int) -> None:
        x = left
        # `strict` on purpose: a row with more cells than columns would still project its extra
        # Fields into `expected.json` while drawing nothing at all.
        for column, text in zip(table.columns, printed, strict=True):
            right_aligned = column.align == "right"
            # A right-aligned column ends a gutter short of the next one's left edge, so a wide
            # value can't run into its neighbour.
            anchor_x = x + column.width - _COLUMN_GUTTER if right_aligned else x
            draw.text((anchor_x, y), text, font=font, fill=ink, anchor="ra" if right_aligned else "la")
            x += column.width

    y = top + 16
    draw.line((left, y - 8, right, y - 8), fill=_INK, width=2)
    _cells([column.heading for column in table.columns], label_font, _LABEL_INK, y)
    y += geometry.row_height - 8

    for row in table.rows:
        _cells([cell.printed for cell in row], value_font, _INK, y)
        y += geometry.row_height - 6
    draw.line((left, y, right, y), fill=_INK, width=2)
    return y + 12


def _draw_mrz(
    draw: ImageDraw.ImageDraw,
    zones: Sequence[Mrz],
    *,
    left: int,
    right: int,
    bottom: int,
    geometry: Geometry,
) -> int:
    """Draw every machine-readable zone against the foot of the face, as a real one is printed,
    and return the y it starts at so the caller can check nothing above collides with it."""
    lines = [line for zone in zones for line in zone.lines]
    if not lines:
        return bottom
    font = _fitted(max(lines, key=len), right - left, fonts.mono, geometry.mono)
    top = bottom - len(lines) * geometry.mrz_height
    y = top
    for line in lines:
        draw.text((left, y), line, font=font, fill=_INK)
        y += geometry.mrz_height
    return top


def _render_face(face: Face, geometry: Geometry) -> Image.Image:
    width, height = geometry.size
    image = Image.new("RGB", geometry.size, "white")
    draw = ImageDraw.Draw(image)

    if geometry.outlined:
        draw.rounded_rectangle((3, 3, width - 4, height - 4), radius=22, outline=_INK, width=3)

    left = geometry.pad
    right = width - geometry.pad

    y = geometry.pad
    for line in face.title:
        draw.text(
            (left, y),
            line,
            font=_fitted(line, right - left, fonts.sans_bold, geometry.title),
            fill=_INK,
        )
        y += geometry.title_height
    if face.title:
        draw.line((left, y, right, y), fill=_INK, width=2)
        y += 16

    mrz_top = _draw_mrz(
        draw,
        [element for element in face.elements if isinstance(element, Mrz)],
        left=left,
        right=right,
        bottom=height - geometry.pad,
        geometry=geometry,
    )
    end = _draw_elements(
        draw,
        [element for element in face.elements if not isinstance(element, Mrz)],
        top=y,
        left=left,
        right=right,
        geometry=geometry,
    )
    if end > mrz_top:
        raise FixtureDoesNotFit(
            f"a face needs {end}px but only {mrz_top}px is free — split it across faces or "
            f"shorten it rather than letting the page clip what its expectation asserts"
        )
    return image


def _overlay_specimen(image: Image.Image) -> Image.Image:
    """The diagonal MINTA / SPECIMEN wash every fixture carries (#46, convention 2)."""
    font = fonts.sans_bold(max(48, image.width // 14))
    layer = Image.new("RGBA", (image.width * 2, image.height * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (layer.width // 2, layer.height // 2),
        "MINTA / SPECIMEN",
        font=font,
        fill=(180, 20, 20, 110),
        anchor="mm",
    )
    rotated = layer.rotate(24, resample=Image.Resampling.BICUBIC)
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


def render_submission(submission: Submission) -> Image.Image:
    """Draw every face of a Submission into one image, stacked top to bottom."""
    geometry = GEOMETRIES[submission.style]
    faces = [_render_face(face, geometry) for face in submission.faces]

    width = geometry.size[0] + 2 * MARGIN
    height = MARGIN + sum(face.height + MARGIN for face in faces)
    page = Image.new("RGB", (width, height), "white")
    y = MARGIN
    for face in faces:
        page.paste(face, (MARGIN, y))
        y += face.height + MARGIN

    return _overlay_specimen(page)


def render_png_bytes(example: Example) -> bytes:
    buffer = io.BytesIO()
    render_submission(example.submission).save(buffer, format="PNG")
    return buffer.getvalue()


def render_pdf_bytes(example: Example) -> bytes:
    """The same page as a single-page PDF.

    Unlike the PNG this is *not* byte-reproducible: Pillow stamps a `/CreationDate` into every
    PDF it writes, so regenerating a committed sample always shows a diff, and no test can pin
    it the way `test_the_committed_sample_matches_a_fresh_render` pins the PNG.
    """
    buffer = io.BytesIO()
    render_submission(example.submission).save(buffer, format="PDF")
    return buffer.getvalue()
