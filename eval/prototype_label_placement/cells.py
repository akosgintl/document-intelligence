"""PROTOTYPE — the nine cells of #60's design, in one place.

Two axes, deliberately kept separate rather than crossed: placement varies a page's label
layout on two Document Types that carry labels, and the legend varies whether a *third* type
carries field names at all. Crossing them would mean drawing a licence at a label placement it
has no labels for.
"""

from dataclasses import dataclass

from pages import LEGEND_EXAMPLES, PLACEMENT_EXAMPLES, PLACEMENTS, at_placement

from fixtures.model import Example


@dataclass(frozen=True)
class Cell:
    """One (document, variant) pair — the unit both the probe and the analysis work in.

    The cell, not the call, is the analysis unit. #49's method note is the reason: five draws of
    one page are not five independent observations, and permuting individual calls instead
    reported an axis effect at p=0.009 that replication showed was pseudoreplication.
    """

    axis: str
    document: str
    variant: str
    example: Example

    @property
    def key(self) -> str:
        return f"{self.document}-{self.variant}"


CELLS: tuple[Cell, ...] = tuple(
    [
        Cell(
            axis="placement",
            document=document,
            variant=placement,
            example=at_placement(example, placement),
        )
        for document, example in PLACEMENT_EXAMPLES.items()
        for placement in PLACEMENTS
    ]
    + [
        Cell(axis="legend", document="driving_licence", variant=legend, example=example)
        for legend, example in LEGEND_EXAMPLES.items()
    ]
)
