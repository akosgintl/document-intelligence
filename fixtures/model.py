"""The data table an Example is: one description of a document, two projections out of it.

Nothing here draws or asserts anything — `render.py` turns these into a page and
`expectations.py` turns the *same* objects into an `expected.json`. That is the whole point of
the shape: a value can only reach the expectation by being printed, so an image and the
expectation asserted against it cannot drift apart (#46, convention 7).

Authoring reads as a table:

    Row("Lakóhely:", "4025 DEBRECEN, PIAC UTCA 14.", residence="4025 DEBRECEN, PIAC UTCA 14.")
     |   |            |                              |
     |   |            |                              `- the Field(s) this printed value proves
     |   |            `- what the page prints
     |   `- the label printed beside it, quoted from the PRADO transcription (#47)
     `- one printed line

Field values are given as keyword arguments, so a Field can never be named `label` or `printed`.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal


def _freeze(instance: object, **values: Any) -> None:
    """Assign onto a frozen dataclass from a hand-written `__init__`.

    Both `Row` and `Cell` write their own `__init__` so that a data table can name Fields as
    keyword arguments, and a frozen dataclass refuses ordinary assignment in one.
    """
    for name, value in values.items():
        object.__setattr__(instance, name, value)


@dataclass(frozen=True)
class Row:
    """One printed label/value line, and the Fields its value proves.

    A row proves zero Fields (a signature, a decorative line), one, or several — the address
    card prints place and date of birth against a single `Születési hely,idő:` label.
    """

    label: str
    printed: str
    fields: Mapping[str, Any]
    place: Literal["stacked", "inline", "column"] | None
    """PROTOTYPE (#60): where this row's label sits, when the geometry defers to the row.

    Ignored unless the geometry's `label_style` is `per_row`. #47 §6 is why it exists: the eID
    identity card stacks its name, sets two fields inline on one row, and right-aligns three
    more, so a placement chosen per Document Type cannot draw it.
    """
    align: Literal["left", "right"]
    """Whether the value sits against the label or against the face's right margin.

    The eID prints `Születési idő/Date of birth:` on the left and `30 06 1979` hard against the
    card's right edge. Meaningless when the row is stacked, where the value starts under its
    own label.
    """

    # Hand-written so a data table can name Fields as keyword arguments, which is what makes it
    # read like the document rather than like a dict literal.
    def __init__(
        self,
        label: str,
        printed: str,
        *,
        place: Literal["stacked", "inline", "column"] | None = None,
        align: Literal["left", "right"] = "left",
        **fields: Any,
    ) -> None:
        _freeze(self, label=label, printed=printed, fields=dict(fields), place=place, align=align)


@dataclass(frozen=True)
class Cell:
    """One printed cell of a table, and the Fields of its row's object that it proves."""

    printed: str
    fields: Mapping[str, Any]

    def __init__(self, printed: str, **fields: Any) -> None:
        _freeze(self, printed=printed, fields=dict(fields))


@dataclass(frozen=True)
class Column:
    heading: str
    width: int
    align: Literal["left", "right"] = "left"


@dataclass(frozen=True)
class Table:
    """A printed table that projects into one array Field — an invoice's `lineItems`, a driving
    licence's `categories`. Each printed row becomes one object, merged from its cells."""

    columns: Sequence[Column]
    rows: Sequence[Sequence[Cell]]
    into: str
    absent_keys: Sequence[str] = ()
    """Nested keys every row carries as null because the table prints no column for them.

    ADR-0010 requires every property of an array Field's rows to be listed `required` and to be
    a nullable union, so a row object must carry a key even where the page shows nothing — an
    item table printing net amounts only still owes `grossAmount: null`. Naming them here keeps
    that null a stated fact about the page rather than a gap in the expectation.

    Named `absent_keys`, not `absent`, because `Example.absent` nulls whole top-level Fields
    while this nulls a key inside every row of one.
    """
    title: str = ""
    """The caption printed above the table, where the document prints one.

    A Hungarian invoice heads its VAT breakdown `ÁFA összesítő` but leaves the item table above
    it uncaptioned, so two tables can abut with only one of them named. Proves no Field — it is
    the label of a block, not of a value.
    """


@dataclass(frozen=True)
class Mrz:
    """A machine-readable zone, drawn in mono at the foot of its face and proving one Field
    verbatim. Modelled as one opaque value, never decomposed — see CONTEXT.md's **MRZ**."""

    lines: Sequence[str]
    into: str = "mrz"


@dataclass(frozen=True)
class Legend:
    """PROTOTYPE (#60) — a block of field names set apart from the values it names.

    The driving licence prints no label beside any value: the recto shows bare EU numbers and
    the field names appear exactly once, as a legend on the verso — horizontally on the 2012
    card, rotated 90° along the right edge on the 2013 one (#47's transcription). It is the
    only place the licence's field names appear anywhere on the card.

    Proves no Field, which is what separates it from a `Row`: it is the document's own key,
    not a value an expectation could assert.
    """

    lines: Sequence[str]
    rotated: bool = True


@dataclass(frozen=True)
class Pair:
    """PROTOTYPE (#60) — two label/value pairs sharing one printed row.

    The eID prints `Nem/Sex: N/F` on the left of a line and
    `Állampolgárság/Nationality: HUN` on the right of the same line (#47 §6). Modelled as two
    `Row`s rather than a four-tuple so each half keeps its own Fields and its own placement,
    and so `expectations.py` can project it without knowing anything new.
    """

    left: Row
    right: Row


Element = Row | Table | Mrz | Legend | Pair


@dataclass(frozen=True)
class Face:
    """One physically distinct printed surface: a side of a card, or a sheet of paper.

    The Hungarian address card prints its personal identifier and its address on opposite faces
    by law, so a complete capture of one shows both — which is why a fixture is a sequence of
    these rather than a single drawing.

    There is no photograph, on any face: convention 2 of #46 is text-only, and #49 measured a
    photo placeholder as noise for classification (p=0.808). The three Schemas that describe a
    photograph do so as classification guidance, which #49 showed these pages clear without it.
    """

    title: Sequence[str] = ()
    elements: Sequence[Element] = ()


@dataclass(frozen=True)
class Submission:
    """Every face of one Document, drawn top to bottom into the single file a caller uploads.

    Named for what it becomes — `submission.png` — rather than a Page, which CONTEXT.md already
    spends on the atomic unit *inside* a Submission. All the faces here land on one Page.

    `style` picks the geometry, and is the only thing that differs between the four identity
    types and an invoice; the element vocabulary above is shared by both. The four identity
    types currently share one geometry — see `render.py` for what that costs and for #60, which
    owns the decision.
    """

    faces: Sequence[Face]
    style: Literal["card", "sheet", "card_inline", "card_column", "card_specimen"] = "card"
    """PROTOTYPE (#60): `card_inline` and `card_column` are the same ID-1 card at the two label
    placements `card` cannot draw. They exist for `eval/prototype_label_placement/` to render
    the same data table three ways; no committed fixture names one."""


@dataclass(frozen=True)
class Example:
    """One committed fixture: a data table plus where its two projections are written.

    `key` doubles as the golden directory (`eval/golden/<key>/`). `sample`, when set, also
    writes the page to `scripts/samples/<sample>.png` and `.pdf` for `scripts/manual_test.py`.
    """

    key: str
    document_type: str
    schema_version: int
    submission: Submission
    absent: Sequence[str] = ()
    sample: str | None = None
    golden: bool = True
