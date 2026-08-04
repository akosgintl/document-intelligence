"""One of the two projections out of an Example's data table: its `expected.json`.

Every asserted value is read back out of the elements that draw the page, so an expectation can
only exist for something printed. The single exception is `Example.absent`, which asserts a
Field is null *because* the page shows nothing for it — the nullable cases the golden set is
built around (#46, convention 3).
"""

import json
from pathlib import Path
from typing import Any, assert_never

from fixtures.model import Example, Face, Legend, Mrz, Row, Table


def _face_fields(face: Face) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for element in face.elements:
        match element:
            case Row():
                fields.update(element.fields)
            case Mrz():
                fields[element.into] = list(element.lines)
            case Table():
                unprinted = dict.fromkeys(element.absent_keys)
                fields[element.into] = [
                    unprinted | {key: value for cell in row for key, value in cell.fields.items()}
                    for row in element.rows
                ]
            case Legend():
                # A legend names Fields, it does not carry them — the licence's verso legend
                # says the value beside `3.` is a date and place of birth, and asserting
                # anything from that would assert the document's key rather than its content.
                pass
            case _:
                # A new element type must project as well as draw. mypy fails here rather than
                # letting a drawn value go unasserted — `render.py` carries the same guard.
                assert_never(element)
    return fields


def extracted_fields(example: Example) -> dict[str, Any]:
    """Every Field the Example's page proves, plus the ones it proves are null."""
    fields: dict[str, Any] = {}
    for face in example.submission.faces:
        fields.update(_face_fields(face))
    for name in example.absent:
        fields[name] = None
    return fields


def expectation(example: Example) -> dict[str, Any]:
    """The Example's `expected.json`, in the shape `eval/run_eval.py` loads."""
    return {
        "document_type": example.document_type,
        "schema_version": example.schema_version,
        "fields": extracted_fields(example),
    }


def write_expectation(example: Example, path: Path) -> None:
    path.write_text(json.dumps(expectation(example), ensure_ascii=False, indent=2) + "\n")
