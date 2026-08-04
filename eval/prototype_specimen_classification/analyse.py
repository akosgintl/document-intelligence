#!/usr/bin/env python3
"""PROTOTYPE — reads observations.jsonl and answers #49 from the randomized pass.

    uv run python eval/prototype_specimen_classification/analyse.py

Free; makes no calls. Everything here is descriptive except the permutation test, which is
the honest way to say "the SPECIMEN overlay costs nothing": with a bimodal per-cell
distribution, a difference in means is meaningless without knowing how big a difference the
noise alone produces.
"""

import json
import random
import statistics as stats
from collections import defaultdict
from pathlib import Path

OBSERVATIONS = Path(__file__).parent / "observations.jsonl"
AXES = (("SPECIMEN overlay", 0), ("photo box", 1), ("card chrome", 2))


def load() -> list[dict]:
    return [json.loads(line) for line in OBSERVATIONS.read_text().splitlines() if line.strip()]


def permutation_p(on: list[float], off: list[float], *, trials: int = 20000) -> tuple[float, float]:
    """How often does relabelling the two groups at random produce a gap this big?"""
    observed = abs(stats.mean(on) - stats.mean(off))
    pool = on + off
    cut = len(on)
    rng = random.Random(49)
    hits = 0
    for _ in range(trials):
        rng.shuffle(pool)
        if abs(stats.mean(pool[:cut]) - stats.mean(pool[cut:])) >= observed:
            hits += 1
    return observed, hits / trials


def main() -> None:
    everything = load()
    randomized = [o for o in everything if o.get("run") == "randomized-r5"]
    deterministic = [o for o in everything if o.get("run") is None and "repeat" not in o["variant_description"]]

    print(f"{'=' * 78}\nRANDOMIZED REPLICATED PASS — n={len(randomized)}\n{'=' * 78}")
    correct = sum(o["correct_type"] for o in randomized)
    classified = sum(o["status"] == "classified" for o in randomized)
    confidences = [o["confidence"] for o in randomized]
    print(f"intended Document Type: {correct}/{len(randomized)}")
    print(f"status `classified`:    {classified}/{len(randomized)}")
    print(f"confidence:             min {min(confidences):.2f}  median {stats.median(confidences):.2f}  max {max(confidences):.2f}")
    print(f"distinct values seen:   {sorted(set(confidences))}")
    other = {o["status"] for o in randomized} - {"classified"}
    print(f"any other status:       {other or 'none'}")

    print(f"\n{'-' * 78}\nDOES THE SPECIMEN MARKING COST ANYTHING? (permutation test, 20k trials)\n{'-' * 78}")
    for name, position in AXES:
        on = [o["confidence"] for o in randomized if o["variant"][position] != "-"]
        off = [o["confidence"] for o in randomized if o["variant"][position] == "-"]
        gap, p = permutation_p(on, off)
        verdict = "indistinguishable from noise" if p > 0.05 else "real"
        print(
            f"{name:<18} on {stats.mean(on):.4f} (n={len(on)})   off {stats.mean(off):.4f} (n={len(off)})"
            f"   gap {gap:.4f}   p={p:.3f}  {verdict}"
        )

    print(f"\n{'-' * 78}\nDID THE FIXED ORDER MATTER? (drift over the randomized sequence)\n{'-' * 78}")
    ordered = sorted(randomized, key=lambda o: o["sequence_index"])
    half = len(ordered) // 2
    first = [o["confidence"] for o in ordered[:half]]
    second = [o["confidence"] for o in ordered[half:]]
    gap, p = permutation_p(first, second)
    print(f"first half {stats.mean(first):.4f}   second half {stats.mean(second):.4f}   gap {gap:.4f}   p={p:.3f}")
    print("  (a real gap here would mean session drift exists and the first pass's fixed")
    print("   order — all non-SPECIMEN before all SPECIMEN — really was confounded)")

    print(f"\n{'-' * 78}\nAGREEMENT WITH THE FIRST, DETERMINISTIC PASS\n{'-' * 78}")
    by_cell: dict[tuple[str, str], list[float]] = defaultdict(list)
    for o in randomized:
        by_cell[(o["document"], o["variant"])].append(o["confidence"])
    disagreements = 0
    for o in sorted(deterministic, key=lambda o: (o["document"], o["variant"])):
        draws = by_cell[(o["document"], o["variant"])]
        if not (min(draws) <= o["confidence"] <= max(draws)):
            disagreements += 1
            print(
                f"  outside range: {o['document']:<16}{o['variant']:<6}"
                f"single draw {o['confidence']:.2f} vs replicated {min(draws):.2f}-{max(draws):.2f}"
            )
    print(f"{len(deterministic) - disagreements}/{len(deterministic)} single draws fall inside their cell's replicated range.")

    print(f"\n{'-' * 78}\nPER-CELL — every cell that ever came within 0.02 of its Threshold\n{'-' * 78}")
    print(f"  {'document':<16}{'axes':<6}{'draws':<28}{'min':<7}{'thr':<6}margin")
    rows = []
    for (document, variant), draws in by_cell.items():
        threshold = next(o["threshold"] for o in randomized if o["document"] == document)
        rows.append((min(draws) - threshold, document, variant, draws, threshold))
    for margin, document, variant, draws, threshold in sorted(rows)[:8]:
        shown = " ".join(f"{d:.2f}" for d in sorted(draws))
        print(f"  {document:<16}{variant:<6}{shown:<28}{min(draws):<7.2f}{threshold:<6.2f}{margin:+.2f}")

    below = [o for o in randomized if o["confidence"] < o["threshold"]]
    print(f"\ncalls that fell BELOW their Threshold: {len(below)}")


if __name__ == "__main__":
    main()
