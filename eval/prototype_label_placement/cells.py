"""PROTOTYPE — the 24 cells of #60's second design, in one place.

Two crossed axes on two Document Types: 4 placements × 3 holder names × 2 documents. The
driving licence is not here — its legend axis came back settled (12/12 Fields correct on every
draw with no field names printed at all, p=1.000 on every pairing) and it prints `1.` and `2.`
as separate rows, so it has no combined name line to vary.
"""

from dataclasses import dataclass

from pages import HOLDERS, NAMES, PLACEMENTS, example

from fixtures.model import Example

DOCUMENTS: tuple[str, ...] = ("id_card", "address_card")


@dataclass(frozen=True)
class Cell:
    """One (document, name, placement) triple.

    Analysis pairs on (document, Field) and averages a cell's replicates first. #49's method
    note is the reason: eight draws of one page are not eight independent observations, and
    permuting individual calls instead reported an axis effect at p=0.009 that replication
    showed was pseudoreplication.
    """

    document: str
    name: str
    placement: str
    example: Example

    @property
    def key(self) -> str:
        return f"{self.document}-{self.name}-{self.placement}"

    @property
    def holder(self) -> str:
        """The full printed name this cell's page carries, for the record in each Observation."""
        return HOLDERS[self.name][self.document].full


CELLS: tuple[Cell, ...] = tuple(
    Cell(
        document=document,
        name=name,
        placement=placement,
        example=example(document, name, placement),
    )
    for document in DOCUMENTS
    for name in NAMES
    for placement in PLACEMENTS
)
