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


@dataclass(frozen=True)
class Row:
    """One printed label/value line, and the Fields its value proves.

    A row proves zero Fields (a signature, a decorative line), one, or several — the address
    card prints place and date of birth against a single `Születési hely,idő:` label.
    """

    label: str
    printed: str
    fields: Mapping[str, Any]

    # Hand-written so a data table can name Fields as keyword arguments, which is what makes it
    # read like the document rather than like a dict literal.
    def __init__(self, label: str, printed: str, **fields: Any) -> None:
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "printed", printed)
        object.__setattr__(self, "fields", dict(fields))


@dataclass(frozen=True)
class Cell:
    """One printed cell of a table, and the Fields of its row's object that it proves."""

    printed: str
    fields: Mapping[str, Any]

    def __init__(self, printed: str, **fields: Any) -> None:
        object.__setattr__(self, "printed", printed)
        object.__setattr__(self, "fields", dict(fields))


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
    absent: Sequence[str] = ()
    """Nested keys every row carries as null because the table prints no column for them.

    ADR-0010 requires every property of an array Field's rows to be listed `required` and to be
    a nullable union, so a row object must carry a key even where the page shows nothing — an
    item table printing net amounts only still owes `grossAmount: null`. Naming them here keeps
    that null a stated fact about the page rather than a gap in the expectation.
    """


@dataclass(frozen=True)
class Mrz:
    """A machine-readable zone, drawn in mono at the foot of its face and proving one Field
    verbatim. Modelled as one opaque value, never decomposed — see CONTEXT.md's **MRZ**."""

    lines: Sequence[str]
    into: str = "mrz"


Element = Row | Table | Mrz


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
    types and an invoice; the element vocabulary above is shared by both. See `render.py` for
    why the four identity types did not need a layout each.
    """

    faces: Sequence[Face]
    style: Literal["card", "sheet"] = "card"


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
