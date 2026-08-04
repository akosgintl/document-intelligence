#!/usr/bin/env python3
"""PROTOTYPE — the #49 probe's terminal shell. Throwaway; the answer is what survives.

    uv run python eval/prototype_specimen_classification/run.py

One keystroke fires at most one billed call, so spending is always deliberate. `[r]` renders
every variant for free — look at the pages before paying for opinions about them.

    uv run python eval/prototype_specimen_classification/run.py --all

`--all` gives up the keystroke-per-call safety and fires every Document Type × variant in one
go — 32 billed calls, no prompt. Only for a run that has already been decided on.
"""

import asyncio
import sys
import termios
import tty
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from pages import DOCUMENTS, VARIANTS, render  # noqa: E402
from probe import Observation, classify, load_api_key, load_registry  # noqa: E402

PAGES_DIR = Path(__file__).parent / "pages_rendered"

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RESET = "\x1b[0m"


class State:
    def __init__(self) -> None:
        self.document_keys = list(DOCUMENTS)
        self.index = 0
        self.observations: dict[tuple[str, str], Observation] = {}
        self.calls = 0
        self.message = "[r] renders all 8 variants for free. Everything else costs money."

    @property
    def document_key(self) -> str:
        return self.document_keys[self.index]


def render_frame(state: State) -> None:
    print("\033[2J\033[H", end="")
    spec = DOCUMENTS[state.document_key]
    print(f"{BOLD}#49 — does a SPECIMEN-marked synthetic page classify at all?{RESET}")
    print(f"{DIM}classify_document against the real AnthropicModelProvider — billed{RESET}\n")
    print(f"{BOLD}Document{RESET}  {spec.label}")
    print(f"{DIM}          {spec.type_name}, Confidence Threshold {_threshold(spec.type_name)}{RESET}")
    print(f"{BOLD}Calls{RESET}     {state.calls}\n")

    print(f"{DIM}  #  {'axes':<9}{'what varies':<38}{'matched':<23}{'conf':<6} status{RESET}")
    for number, variant in enumerate(VARIANTS, start=1):
        observation = state.observations.get((state.document_key, variant.key))
        if observation is None:
            result = f"{DIM}not run{RESET}"
        else:
            result = _format_result(observation)
        print(f"  {number}  {BOLD}{variant.key:<9}{RESET}{DIM}{variant.description:<38}{RESET}{result}")

    print(f"\n{state.message}\n")
    print(
        f"{BOLD}[1-8]{RESET}{DIM} run one variant{RESET}   {BOLD}[a]{RESET}{DIM} run all 8{RESET}   "
        f"{BOLD}[t]{RESET}{DIM} next Document Type{RESET}   {BOLD}[r]{RESET}{DIM} render only{RESET}   "
        f"{BOLD}[q]{RESET}{DIM} quit{RESET}"
    )


def _threshold(type_name: str) -> float:
    return load_registry().get(type_name).confidence_threshold


def _format_result(observation: Observation) -> str:
    colour = {
        "classified": GREEN,
        "classification_needs_review": YELLOW,
        "unclassified": RED,
    }[observation.status]
    matched = observation.matched_type or "—"
    if not observation.correct_type:
        matched = f"{RED}{matched}{RESET}"
    confidence = "—" if observation.confidence is None else f"{observation.confidence:.2f}"
    padding = " " * max(0, 23 - len(observation.matched_type or "—"))
    return f"{matched}{padding}{confidence:<6} {colour}{observation.status}{RESET}"


def read_key() -> str:
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def render_all(state: State) -> None:
    PAGES_DIR.mkdir(exist_ok=True)
    spec = DOCUMENTS[state.document_key]
    for variant in VARIANTS:
        path = PAGES_DIR / f"{state.document_key}-{variant.key}.png"
        path.write_bytes(render(spec, variant))
    state.message = f"Rendered 8 pages to {PAGES_DIR.relative_to(Path.cwd())}/ — no calls made."


async def run_variant(state: State, variant_index: int, registry, client) -> None:
    spec = DOCUMENTS[state.document_key]
    variant = VARIANTS[variant_index]
    state.message = f"Calling the Model Provider for {variant.key} ({variant.description})…"
    if "--all" not in sys.argv:
        render_frame(state)
    observation = await classify(
        image_bytes=render(spec, variant),
        document=state.document_key,
        intended_type=spec.type_name,
        variant_key=variant.key,
        variant_description=variant.description,
        registry=registry,
        client=client,
    )
    state.observations[(state.document_key, variant.key)] = observation
    state.calls += 1
    state.message = (
        f"{variant.key}: {observation.status}"
        f"{DIM} — {observation.input_tokens} in / {observation.output_tokens} out,"
        f" {observation.latency_ms:.0f}ms{RESET}"
    )


async def run_everything() -> None:
    """Every Document Type × every variant, sequentially, no terminal. 32 billed calls."""
    registry = load_registry()
    client = anthropic.AsyncAnthropic(api_key=load_api_key())
    state = State()
    render_all(state)

    for index in range(len(state.document_keys)):
        state.index = index
        for variant_index in range(len(VARIANTS)):
            await run_variant(state, variant_index, registry, client)
            observation = state.observations[(state.document_key, VARIANTS[variant_index].key)]
            print(
                f"{state.document_key:<16}{VARIANTS[variant_index].key:<6}"
                f"{str(observation.matched_type):<28}"
                f"{'—' if observation.confidence is None else f'{observation.confidence:.2f}':<6}"
                f"{observation.status}",
                flush=True,
            )
    print(f"\n{state.calls} billed calls. Results in observations.jsonl.")


async def main() -> None:
    if "--all" in sys.argv:
        await run_everything()
        return

    registry = load_registry()
    client = anthropic.AsyncAnthropic(api_key=load_api_key())
    state = State()

    while True:
        render_frame(state)
        key = await asyncio.to_thread(read_key)

        if key == "q":
            print("\033[2J\033[H", end="")
            print(f"{state.calls} billed calls. Results in observations.jsonl.")
            return
        if key == "t":
            state.index = (state.index + 1) % len(state.document_keys)
            state.message = ""
        elif key == "r":
            render_all(state)
        elif key in "12345678":
            await run_variant(state, int(key) - 1, registry, client)
        elif key == "a":
            for index in range(len(VARIANTS)):
                await run_variant(state, index, registry, client)
            state.message = f"All 8 variants run for {state.document_key}."


if __name__ == "__main__":
    asyncio.run(main())
