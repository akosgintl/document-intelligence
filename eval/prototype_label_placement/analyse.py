#!/usr/bin/env python3
"""PROTOTYPE — reads observations.jsonl and reports. Free; makes no API calls.

    uv run python eval/prototype_label_placement/analyse.py

## The analysis unit

#49's method note is the thing to get right: eight draws of one page are not eight independent
observations, and permuting *individual calls* reported an axis effect at p=0.009 that
replication showed was pseudoreplication.

The unit is the **(document, Field) pair**, with that pair's accuracy under each level averaged
over its replicates first, compared by a **paired sign-flip permutation test** — under the null
that a level does nothing, the sign of each pair's difference is arbitrary. Two Fields of one
document are distinct measurements where two draws of one page are not, and pairing on
(document, Field) removes the largest nuisance source: some Fields are simply harder.

## Two factors

Each is collapsed over the other before testing, and then the name-split Fields are reported
crossed, because that interaction is the question this run exists to answer: **does the
placement effect survive a real name?**

## What this design can and cannot detect

Twenty-odd Field-pairs at six replicates finds effects that move whole Fields between right and
wrong. It does not resolve a couple of accuracy points, and a null here is "no effect large
enough to matter for #60's decision", not "no effect".
"""

import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

OBSERVATIONS = Path(__file__).parent / "observations.jsonl"
RUN = "names-and-placement-r6"
PERMUTATIONS = 20000
SEED = 60
SPLIT_FIELDS = ("surname", "givenNames")


def load(run: str = RUN) -> list[dict[str, Any]]:
    if not OBSERVATIONS.is_file():
        raise SystemExit(f"No observations at {OBSERVATIONS} — run sequence.py first.")
    rows = [json.loads(line) for line in OBSERVATIONS.read_text().splitlines() if line.strip()]
    return [row for row in rows if row.get("run") == run]


def _paired_permutation(differences: list[float]) -> float:
    if not differences:
        return float("nan")
    observed = abs(statistics.fmean(differences))
    rng = random.Random(SEED)
    hits = sum(
        abs(statistics.fmean([d if rng.random() < 0.5 else -d for d in differences])) >= observed
        for _ in range(PERMUTATIONS)
    )
    return (hits + 1) / (PERMUTATIONS + 1)


def _field_accuracy(rows: list[dict[str, Any]], factor: str) -> dict[tuple[str, str, str], float]:
    """Mean correctness per (document, Field, level of `factor`), collapsed over the other."""
    tally: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        for outcome in row["outcomes"]:
            tally[(row["document"], outcome["name"], row[factor])].append(
                1 if outcome["correct"] else 0
            )
    return {key: statistics.fmean(values) for key, values in tally.items()}


def _compare(accuracy: dict[tuple[str, str, str], float], left: str, right: str) -> None:
    pairs = sorted(
        {(d, f) for d, f, level in accuracy if level == left}
        & {(d, f) for d, f, level in accuracy if level == right}
    )
    differences = [accuracy[(d, f, left)] - accuracy[(d, f, right)] for d, f in pairs]
    if not differences:
        return
    moved = [(d, f, x) for (d, f), x in zip(pairs, differences, strict=True) if x]
    print(
        f"  {left:<10} vs {right:<10}  Δ {statistics.fmean(differences):+.4f}  "
        f"p={_paired_permutation(differences):.3f}  "
        f"({len(moved)}/{len(pairs)} Field-pairs differ)"
    )
    for document, name, diff in sorted(moved, key=lambda m: -abs(m[2]))[:4]:
        print(f"      {document}.{name}: {diff:+.3f}")


def _cells(rows: list[dict[str, Any]]) -> None:
    cells: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        cells[(row["document"], row["name_arm"], row["placement"])].append(row)
    print(
        f"\n{'document':<14}{'name':<10}{'placement':<11}{'n':>3}  {'accuracy':<21}"
        f"{'split ok':<10}{'mean conf':<11}statuses"
    )
    for (document, arm, placement), group in sorted(cells.items()):
        acc = [r["accuracy"] for r in group]
        conf = [r["mean_confidence"] for r in group if r["mean_confidence"] is not None]
        split = [
            o["correct"] for r in group for o in r["outcomes"] if o["name"] in SPLIT_FIELDS
        ]
        statuses = defaultdict(int)
        for r in group:
            statuses[r["status"]] += 1
        span = f"{statistics.fmean(acc):.3f} [{min(acc):.2f}-{max(acc):.2f}]"
        print(
            f"{document:<14}{arm:<10}{placement:<11}{len(group):>3}  {span:<21}"
            f"{sum(split):>2}/{len(split):<7}{statistics.fmean(conf):<11.3f}"
            + " ".join(f"{k.replace('extraction_', '')}×{v}" for k, v in sorted(statuses.items()))
        )


def _split_interaction(rows: list[dict[str, Any]]) -> None:
    """The name split, crossed. This grid is what the run is for."""
    grid: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        for outcome in row["outcomes"]:
            if outcome["name"] in SPLIT_FIELDS:
                grid[(row["document"], row["name_arm"], row["placement"])].append(
                    1 if outcome["correct"] else 0
                )
    placements = sorted({p for _, _, p in grid})
    arms = sorted({a for _, a, _ in grid})
    for document in sorted({d for d, _, _ in grid}):
        print(f"\n  surname+givenNames correct — {document}")
        print("    " + "name".ljust(10) + "".join(p.ljust(12) for p in placements))
        for arm in arms:
            cells = []
            for placement in placements:
                values = grid.get((document, arm, placement), [])
                cells.append(f"{sum(values)}/{len(values)}".ljust(12) if values else "—".ljust(12))
            print("    " + arm.ljust(10) + "".join(cells))


def _never_right(rows: list[dict[str, Any]]) -> None:
    tally: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        for outcome in row["outcomes"]:
            tally[(row["document"], outcome["name"])].append(1 if outcome["correct"] else 0)
    dead = sorted(key for key, values in tally.items() if not any(values))
    if not dead:
        return
    print("\nNever correct under any cell — fixture findings, not axis effects:")
    for document, name in dead:
        sample = next(
            o
            for r in rows
            if r["document"] == document
            for o in r["outcomes"]
            if o["name"] == name
        )
        print(f"  {document}.{name}")
        print(f"      expected {sample['expected']!r}")
        print(f"      got      {sample['actual']!r}")


def main() -> None:
    rows = load()
    if not rows:
        raise SystemExit(f"No observations tagged run={RUN!r} — run sequence.py first.")
    print(f"{len(rows)} billed Extractions, run={RUN!r}.")

    _cells(rows)
    _split_interaction(rows)
    _never_right(rows)

    placement = _field_accuracy(rows, "placement")
    print("\nPlacement, collapsed over name — paired sign-flip over (document, Field) pairs:")
    for left, right in (
        ("specimen", "stacked"),
        ("specimen", "inline"),
        ("specimen", "column"),
        ("stacked", "inline"),
    ):
        _compare(placement, left, right)

    arm = _field_accuracy(rows, "name_arm")
    print("\nHolder name, collapsed over placement — same test:")
    for left, right in (("nonce", "real"), ("nonce", "specimen"), ("real", "specimen")):
        _compare(arm, left, right)

    ordered = sorted(rows, key=lambda r: r["sequence_index"])
    half = len(ordered) // 2
    first = statistics.fmean([r["accuracy"] for r in ordered[:half]])
    second = statistics.fmean([r["accuracy"] for r in ordered[half:]])
    print(f"\nSession drift: first half {first:.4f}, second half {second:.4f}, Δ {second-first:+.4f}")
    print(
        f"Tokens: {statistics.fmean([r['input_tokens'] for r in rows if r['input_tokens']]):.0f} in / "
        f"{statistics.fmean([r['output_tokens'] for r in rows if r['output_tokens']]):.0f} out, "
        f"{statistics.fmean([r['latency_ms'] for r in rows if r['latency_ms']]) / 1000:.1f}s per call."
    )


if __name__ == "__main__":
    main()
