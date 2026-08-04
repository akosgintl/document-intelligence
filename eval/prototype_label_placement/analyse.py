#!/usr/bin/env python3
"""PROTOTYPE — reads observations.jsonl and reports. Free; makes no API calls.

    uv run python eval/prototype_label_placement/analyse.py

## What the analysis unit is, and why

#49's method note is the thing to get right here: five draws of one page are not five
independent observations, and permuting *individual calls* reported an axis effect at p=0.009
that replication showed was pseudoreplication.

The unit used below is the **(document, Field) pair**, with that pair's accuracy under each
variant averaged over its replicates first. Two Fields of the same document are distinct
measurements — different label, different value, different place on the page — where two draws
of the same page are not. Pairing on (document, Field) also removes the largest nuisance source
outright: some Fields are simply harder than others, and comparing `mrz` under one placement
against `nationality` under another would drown the axis in that.

The comparison is a **paired sign-flip permutation test** over those pairs: under the null that
placement does nothing, the sign of each pair's difference is arbitrary, so re-randomizing the
signs gives the null distribution of the mean difference directly.

**What this design can and cannot detect.** Twenty-odd pairs at eight replicates will find an
effect that moves whole Fields between right and wrong. It will not resolve a couple of points
of accuracy, and it should not be read as evidence of no effect at that scale — which is fine,
because #60 asks whether placement matters enough to justify building the knob, not whether it
is exactly zero.
"""

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

OBSERVATIONS = Path(__file__).parent / "observations.jsonl"
RUN = "randomized-r8"
PERMUTATIONS = 20000
SEED = 60


def load(run: str = RUN) -> list[dict[str, Any]]:
    if not OBSERVATIONS.is_file():
        raise SystemExit(f"No observations at {OBSERVATIONS} — run sequence.py first.")
    rows = [json.loads(line) for line in OBSERVATIONS.read_text().splitlines() if line.strip()]
    return [row for row in rows if row.get("run") == run]


def _paired_permutation(differences: list[float]) -> float:
    """Two-sided p for `mean(differences) == 0` under sign-flip randomization."""
    if not differences:
        return float("nan")
    observed = abs(statistics.fmean(differences))
    rng = random.Random(SEED)
    hits = sum(
        abs(statistics.fmean([d if rng.random() < 0.5 else -d for d in differences])) >= observed
        for _ in range(PERMUTATIONS)
    )
    return (hits + 1) / (PERMUTATIONS + 1)


def _field_accuracy(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], float]:
    """Mean correctness per (document, Field, variant), averaged over that cell's replicates."""
    tally: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        for outcome in row["outcomes"]:
            tally[(row["document"], outcome["name"], row["variant"])].append(
                1 if outcome["correct"] else 0
            )
    return {key: statistics.fmean(values) for key, values in tally.items()}


def _compare(accuracy: dict[tuple[str, str, str], float], left: str, right: str) -> None:
    pairs = sorted(
        {(document, name) for document, name, variant in accuracy if variant == left}
        & {(document, name) for document, name, variant in accuracy if variant == right}
    )
    differences = [accuracy[(d, f, left)] - accuracy[(d, f, right)] for d, f in pairs]
    if not differences:
        return
    moved = [(d, f, diff) for (d, f), diff in zip(pairs, differences, strict=True) if diff]
    print(
        f"  {left:<11} vs {right:<11}  "
        f"Δ {statistics.fmean(differences):+.4f}  "
        f"p={_paired_permutation(differences):.3f}  "
        f"({len(moved)}/{len(pairs)} Field-pairs differ at all)"
    )
    for document, name, diff in sorted(moved, key=lambda m: -abs(m[2]))[:5]:
        print(f"      {document}.{name}: {diff:+.3f}")


def _per_cell(rows: list[dict[str, Any]]) -> None:
    cells: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        cells[(row["axis"], row["document"], row["variant"])].append(row)

    print(f"\n{'axis':<10}{'document':<15}{'variant':<12}{'n':>3}  {'accuracy':<22}"
          f"{'mean conf':<11}{'min conf':<10}statuses")
    for (axis, document, variant), group in sorted(cells.items()):
        accuracies = [r["accuracy"] for r in group]
        confidences = [r["mean_confidence"] for r in group if r["mean_confidence"] is not None]
        minima = [r["min_confidence"] for r in group if r["min_confidence"] is not None]
        statuses = defaultdict(int)
        for r in group:
            statuses[r["status"]] += 1
        summary = " ".join(f"{k}×{v}" for k, v in sorted(statuses.items()))
        span = f"{statistics.fmean(accuracies):.3f} [{min(accuracies):.3f}-{max(accuracies):.3f}]"
        print(
            f"{axis:<10}{document:<15}{variant:<12}{len(group):>3}  {span:<22}"
            f"{statistics.fmean(confidences):<11.3f}{min(minima):<10.2f}{summary}"
        )


def _never_right(rows: list[dict[str, Any]]) -> None:
    """Fields no variant ever got right — a page or expectation problem, not an axis effect."""
    tally: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        for outcome in row["outcomes"]:
            tally[(row["document"], outcome["name"])].append(1 if outcome["correct"] else 0)
    dead = {key: values for key, values in tally.items() if not any(values)}
    if not dead:
        return
    print("\nNever correct under any variant — read these as fixture findings, not axis effects:")
    for document, name in sorted(dead):
        example = next(
            o for r in rows if r["document"] == document
            for o in r["outcomes"] if o["name"] == name
        )
        print(f"  {document}.{name}  expected {example['expected']!r}  got {example['actual']!r}")


def _drift(rows: list[dict[str, Any]]) -> None:
    """Was the randomized sequence stable end to end? Cheap, and #49 found it worth checking."""
    ordered = sorted(rows, key=lambda r: r["sequence_index"])
    half = len(ordered) // 2
    first = [r["accuracy"] for r in ordered[:half]]
    second = [r["accuracy"] for r in ordered[half:]]
    print(
        f"\nSession drift: first half {statistics.fmean(first):.4f}, "
        f"second half {statistics.fmean(second):.4f}, "
        f"Δ {statistics.fmean(second) - statistics.fmean(first):+.4f}"
    )


def main() -> None:
    rows = load()
    if not rows:
        raise SystemExit(f"No observations tagged run={RUN!r} — run sequence.py first.")
    print(f"{len(rows)} billed Extractions, run={RUN!r}.")

    _per_cell(rows)
    _never_right(rows)

    accuracy = _field_accuracy(rows)
    print("\nPlacement axis — paired sign-flip permutation over (document, Field) pairs:")
    for left, right in (("stacked", "inline"), ("stacked", "column"), ("inline", "column")):
        _compare(accuracy, left, right)

    print("\nLegend axis — same test, on the driving licence:")
    for left, right in (("absent", "horizontal"), ("absent", "rotated"), ("horizontal", "rotated")):
        _compare(accuracy, left, right)

    _drift(rows)
    print(
        "\nTokens: "
        f"{statistics.fmean([r['input_tokens'] for r in rows if r['input_tokens']]):.0f} in / "
        f"{statistics.fmean([r['output_tokens'] for r in rows if r['output_tokens']]):.0f} out, "
        f"{statistics.fmean([r['latency_ms'] for r in rows if r['latency_ms']]) / 1000:.1f}s "
        "per call."
    )


if __name__ == "__main__":
    main()
