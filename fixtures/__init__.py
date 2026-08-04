"""Synthetic document fixtures — one renderer, two surfaces (#51).

Every committed fixture in this repo is drawn from a *data table* in `catalogue.py`. The page
and its `expected.json` are both projections of that one table, so an image and the expectation
asserted against it cannot drift apart (#46, convention 7). Regenerate everything with:

    uv run python -m fixtures.generate

This module is the public surface — author a data table out of these names, and the two
projections follow. `catalogue.py` imports nothing else, and neither should a new one.
"""

from fixtures.expectations import expectation, extracted_fields
from fixtures.model import Cell, Column, Example, Face, Mrz, Row, Submission, Table
from fixtures.render import FixtureDoesNotFit, render_pdf_bytes, render_png_bytes, render_submission
from fixtures.surfaces import write_golden, write_sample

__all__ = [
    "Cell",
    "Column",
    "Example",
    "Face",
    "FixtureDoesNotFit",
    "Mrz",
    "Row",
    "Submission",
    "Table",
    "expectation",
    "extracted_fields",
    "render_pdf_bytes",
    "render_png_bytes",
    "render_submission",
    "write_golden",
    "write_sample",
]
