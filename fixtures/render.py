"""The other projection out of an Example's data table: the page itself.

Two geometries, one element vocabulary. `card` draws ID-1-proportioned faces with values stacked
under their labels, which is what fits an ID-1 card — a bilingual label is far too long to sit
beside a value in 85.6 mm. `sheet` draws an A4-proportioned page with a label column, and is
what an invoice uses.

The four identity types share the `card` geometry rather than each getting its own layout. That
much the PRADO transcription (#47) supports: all four print the same three things, a title
block, a run of label/value lines and an optional zone at the foot, so the *element* vocabulary
is genuinely shared and a fifth geometry would only be needed by a document that stops being a
stack of labelled values.

**Label placement is a different axis, and on it `card` is knowingly wrong for two of the four
types.** Per #47, the eID identity card sets its labels inline (`Hun/Eng:` with the value
following on the same line) and the address card sets them in a label column beside a value
column, where `card` stacks all four. The driving licence's verso legend is set rotated 90°
along the right edge, which this module cannot draw at all — and that legend is the only place
the licence's field names appear anywhere on the card. #51 shipped the seam and deliberately
did not add the knob; **#60 owns the decision** (widen `Geometry` versus per-type layout
functions) and must land before #53/#54/#55/#58 author fixtures against this. The conventions
this module enforces are recorded as an ADR by #50.

Deliberately low fidelity: text only, no photograph, no hologram, no OVD, no security printing,
and a MINTA / SPECIMEN wash across every page (#46, convention 2). #49 measured every fidelity
axis it tested as noise for classification, so nothing here needs to look convincing — only to
print the right words in the right places.
"""

import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import assert_never

from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont

from fixtures import fonts
from fixtures.model import Example, Face, Mrz, Row, Submission, Table

MARGIN = 36
_INK = "black"
_LABEL_INK = "#303030"
_RULE = "#b0b0b0"
_COLUMN_GUTTER = 20
# The floor `_fitted` shrinks a label to. Below this a bilingual label stops being legible at
# all, so a fixture that needs it is better off saying less.
_MINIMUM_TYPE = 9


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


@dataclass(frozen=True)
class Frame:
    """The horizontal band an element is drawn into, at the geometry it is drawn for.

    These three travel together through every drawing function; a face's own vertical position
    does not, because each function returns the y it finished at.
    """

    left: int
    right: int
    geometry: Geometry

    @property
    def width(self) -> int:
        return self.right - self.left


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
) -> FreeTypeFont:
    """The largest of `loader`'s sizes at or below `size` that draws `text` inside `max_width`.

    Bilingual and trilingual labels are long — `Születési családi és utónév/Family name and Given
    name at birth:` is one real label. Shrinking to fit keeps a fixture legible where overflowing
    would push a value off the page while its expectation still asserted it.
    """
    while size > _MINIMUM_TYPE:
        font = loader(size)
        if font.getlength(text) <= max_width:
            return font
        size -= 1
    return loader(_MINIMUM_TYPE)


def _draw_elements(
    draw: ImageDraw.ImageDraw,
    elements: Sequence[Row | Table],
    *,
    top: int,
    frame: Frame,
) -> int:
    """Draw every element top to bottom, returning the y the last one ended at."""
    y = top
    geometry = frame.geometry
    for element in elements:
        match element:
            case Row():
                if geometry.stacked:
                    draw.text(
                        (frame.left, y),
                        element.label,
                        font=_fitted(element.label, frame.width, fonts.sans, geometry.label),
                        fill=_LABEL_INK,
                    )
                    draw.text(
                        (frame.left, y + geometry.label + 6),
                        element.printed,
                        font=_fitted(element.printed, frame.width, fonts.sans_bold, geometry.value),
                        fill=_INK,
                    )
                    rule_y = y + geometry.row_height - 8
                    draw.line((frame.left, rule_y, frame.right, rule_y), fill=_RULE)
                else:
                    value_left = frame.left + geometry.value_column
                    draw.text(
                        (frame.left, y),
                        element.label,
                        font=_fitted(element.label, geometry.value_column - 20, fonts.sans, geometry.label),
                        fill=_LABEL_INK,
                    )
                    draw.text(
                        (value_left, y),
                        element.printed,
                        font=_fitted(
                            element.printed, frame.right - value_left, fonts.sans_bold, geometry.value
                        ),
                        fill=_INK,
                    )
                y += geometry.row_height
            case Table():
                y = _draw_table(draw, element, top=y, frame=frame)
            case _:
                # A new element type must be given a drawing *and* a projection, or a fixture
                # would assert a value its page never printed. mypy fails here rather than
                # letting it draw nothing — `expectations.py` carries the same guard.
                assert_never(element)
    return y


def _draw_table(
    draw: ImageDraw.ImageDraw,
    table: Table,
    *,
    top: int,
    frame: Frame,
) -> int:
    left, right, geometry = frame.left, frame.right, frame.geometry
    total = sum(column.width for column in table.columns)
    if total > frame.width:
        raise FixtureDoesNotFit(
            f"table columns total {total}px but only {frame.width}px is available — narrow them "
            f"rather than letting a column run off the page it is asserted from"
        )

    label_font = fonts.sans(geometry.label)
    value_font = fonts.sans_bold(geometry.value)

    def _cells(printed: Sequence[str], font: FreeTypeFont, ink: str, y: int, *, what: str) -> None:
        x = left
        # `strict` on purpose: a row with more cells than columns would still project its extra
        # Fields into `expected.json` while drawing nothing at all.
        for column, text in zip(table.columns, printed, strict=True):
            # A cell is never shrunk to fit the way a Row's label is: shrinking one cell and not
            # its neighbours would leave a table set in mixed sizes. It is refused instead, for
            # the reason the whole table is — text that runs under the next column makes two
            # values unreadable while the expectation still asserts both.
            needed = font.getlength(text)
            if needed > column.width - _COLUMN_GUTTER:
                raise FixtureDoesNotFit(
                    f"{what} {text!r} needs {needed:.0f}px but column {column.heading!r} leaves "
                    f"{column.width - _COLUMN_GUTTER}px — widen the column or shorten the text "
                    f"rather than letting it run under its neighbour"
                )
            right_aligned = column.align == "right"
            # A right-aligned column ends a gutter short of the next one's left edge, so a wide
            # value can't run into its neighbour.
            anchor_x = x + column.width - _COLUMN_GUTTER if right_aligned else x
            draw.text((anchor_x, y), text, font=font, fill=ink, anchor="ra" if right_aligned else "la")
            x += column.width

    y = top + 16
    if table.title:
        draw.text(
            (left, y - 8),
            table.title,
            font=_fitted(table.title, right - left, fonts.sans_bold, geometry.label),
            fill=_INK,
        )
        y += geometry.label + 10
    draw.line((left, y - 8, right, y - 8), fill=_INK, width=2)
    _cells([column.heading for column in table.columns], label_font, _LABEL_INK, y, what="heading")
    y += geometry.row_height - 8

    for row in table.rows:
        _cells([cell.printed for cell in row], value_font, _INK, y, what="cell")
        y += geometry.row_height - 6
    draw.line((left, y, right, y), fill=_INK, width=2)
    return y + 12


def _draw_mrz(
    draw: ImageDraw.ImageDraw,
    zones: Sequence[Mrz],
    *,
    bottom: int,
    frame: Frame,
) -> int:
    """Draw every machine-readable zone against the foot of the face, as a real one is printed,
    and return the y it starts at so the caller can check nothing above collides with it."""
    lines = [line for zone in zones for line in zone.lines]
    if not lines:
        return bottom
    geometry = frame.geometry
    font = _fitted(max(lines, key=len), frame.width, fonts.mono, geometry.mono)
    top = bottom - len(lines) * geometry.mrz_height
    y = top
    for line in lines:
        draw.text((frame.left, y), line, font=font, fill=_INK)
        y += geometry.mrz_height
    return top


def _render_face(face: Face, geometry: Geometry) -> Image.Image:
    width, height = geometry.size
    image = Image.new("RGB", geometry.size, "white")
    draw = ImageDraw.Draw(image)

    if geometry.outlined:
        draw.rounded_rectangle((3, 3, width - 4, height - 4), radius=22, outline=_INK, width=3)

    frame = Frame(left=geometry.pad, right=width - geometry.pad, geometry=geometry)

    y = geometry.pad
    for line in face.title:
        draw.text(
            (frame.left, y),
            line,
            font=_fitted(line, frame.width, fonts.sans_bold, geometry.title),
            fill=_INK,
        )
        y += geometry.title_height
    if face.title:
        draw.line((frame.left, y, frame.right, y), fill=_INK, width=2)
        y += 16

    # Partitioned once, and typed: a machine-readable zone is set against the foot of the face
    # while everything else flows from the top, so the two are drawn from opposite ends and meet
    # in the middle. `body` is a `list[Row | Table]`, which is what lets `_draw_elements` prove
    # its match is exhaustive.
    zones = [element for element in face.elements if isinstance(element, Mrz)]
    body = [element for element in face.elements if not isinstance(element, Mrz)]

    mrz_top = _draw_mrz(draw, zones, bottom=height - geometry.pad, frame=frame)
    end = _draw_elements(draw, body, top=y, frame=frame)
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
