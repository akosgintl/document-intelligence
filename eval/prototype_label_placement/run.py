#!/usr/bin/env python3
"""PROTOTYPE — the terminal shell over #60's probe.

    uv run python eval/prototype_label_placement/run.py

`[r]` renders all 24 cells to `pages_rendered/` for free — **look at them before spending
anything.** `[1]`–`[24]` fire one cell, `[a]` fires all 24 once.

One pass of `[a]` is nine billed Extractions and is *not* the answer: `anthropic_provider.py`
sets no `temperature`, so every call is a draw from a distribution rather than a reading. It is
here to eyeball the shape of a result and catch a broken page before `sequence.py` spends
a hundred and forty-four calls on the same mistake. The answer comes from `sequence.py`.
"""

import asyncio
import sys
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parents[2]
# `fixtures` lives at the repo root and `document_intelligence` under src/; running this
# file by path puts only its own directory on sys.path, so both need adding by hand.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from cells import CELLS, Cell  # noqa: E402
from probe import Observation, extract, load_api_key, load_registry  # noqa: E402

from fixtures import render_png_bytes  # noqa: E402

RENDERED = Path(__file__).parent / "pages_rendered"

_BOLD = "\x1b[1m"
_DIM = "\x1b[2m"
_RESET = "\x1b[0m"


def _render_all() -> list[str]:
    """Draw every variant to disk. Free — no API call, no tokens."""
    RENDERED.mkdir(exist_ok=True)
    written = []
    for cell in CELLS:
        path = RENDERED / f"{cell.key}.png"
        path.write_bytes(render_png_bytes(cell.example))
        written.append(path.name)
    return written


def _frame(results: dict[str, Observation], note: str) -> None:
    print("\033[2J\033[H", end="")
    print(f"{_BOLD}#60 — placement x holder name, on the two cards that combine the name line{_RESET}")
    print(f"{_DIM}Each fired cell is one billed extract() call against claude-sonnet-5.{_RESET}\n")

    for index, cell in enumerate(CELLS, start=1):
        observation = results.get(cell.key)
        head = (f"  {_BOLD}[{index:>2}]{_RESET} {cell.document:<13} "
                f"{cell.name:<9} {cell.placement:<9}")
        if observation is None:
            print(f"{head} {_DIM}—{_RESET}")
            continue
        flag = "" if observation.status == "extracted" else "  <-- !"
        wrong = [f.name for f in map(_as_outcome, observation.outcomes) if not f.correct]
        print(
            f"{head} {observation.fields_correct}/{observation.fields_expected} fields  "
            f"conf {observation.mean_confidence:.3f} (min {observation.min_confidence:.2f})  "
            f"{observation.status}{flag}"
        )
        if wrong:
            print(f"       {_DIM}wrong: {', '.join(wrong)}{_RESET}")

    print(f"\n{_DIM}{note}{_RESET}")
    print(
        f"\n  {_BOLD}[r]{_RESET} render all (free)   {_BOLD}[1-24]{_RESET} fire one   "
        f"{_BOLD}[a]{_RESET} fire all 24   {_BOLD}[q]{_RESET} quit"
    )


class _Outcome:
    def __init__(self, raw: dict) -> None:
        self.name = raw["name"]
        self.correct = raw["correct"]


def _as_outcome(raw: dict) -> _Outcome:
    return _Outcome(raw)


async def _fire(cell: Cell, registry, client) -> Observation:
    return await extract(
        example=cell.example,
        document=cell.document,
        name_arm=cell.name,
        placement=cell.placement,
        holder=cell.holder,
        registry=registry,
        client=client,
    )


async def main() -> None:
    registry = load_registry()
    client = anthropic.AsyncAnthropic(api_key=load_api_key())
    results: dict[str, Observation] = {}
    note = "Nothing fired yet. Press [r] first and look at the pages."

    while True:
        _frame(results, note)
        try:
            key = input("\n> ").strip().lower()
        except EOFError:
            return

        if key == "q":
            return
        if key == "r":
            written = _render_all()
            note = f"Rendered {len(written)} pages to pages_rendered/ — free."
        elif key == "a":
            for cell in CELLS:
                results[cell.key] = await _fire(cell, registry, client)
                _frame(results, f"firing… {cell.key}")
            note = f"Fired all {len(CELLS)} cells once. One draw each — not an answer."
        elif key.isdigit() and 1 <= int(key) <= len(CELLS):
            cell = CELLS[int(key) - 1]
            results[cell.key] = await _fire(cell, registry, client)
            note = f"Fired {cell.key}. Appended to observations.jsonl."
        else:
            note = f"Unknown key {key!r}."


if __name__ == "__main__":
    asyncio.run(main())
