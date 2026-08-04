#!/usr/bin/env python3
"""PROTOTYPE — the randomized, replicated pass over #60's two axes. This is the answer.

    uv run python eval/prototype_label_placement/sequence.py     # 72 billed calls, ~6 min

REPLICATES draws of all nine cells are shuffled into a single seeded order and fired
sequentially, with each call's position recorded. Both halves of that are load-bearing, and #49
learned each of them the expensive way:

1. **Replication.** `anthropic_provider.py` sets no `temperature`, so the API default of 1.0
   applies and every call is a draw from a sampling distribution, not a reading. #49's first
   pass measured each cell once and found axis effects smaller than the noise inside one cell.

2. **Randomized order.** Firing cells grouped by variant puts every page of one variant before
   every page of another, so any drift over the session lands squarely on the axis being
   measured. Every call is independent — no conversation state, no prompt caching in the
   Provider — so there is no *known* mechanism for such drift. Randomizing removes it as an
   explanation anyway, which is cheaper than arguing about it.

Every result is appended to `observations.jsonl` as it arrives, because these cost real money
and losing them to a closed terminal means paying again.
"""

import asyncio
import random
import sys
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parents[2]
# `fixtures` lives at the repo root and `document_intelligence` under src/; running this
# file by path puts only its own directory on sys.path, so both need adding by hand.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from cells import CELLS  # noqa: E402
from probe import extract, load_api_key, load_registry  # noqa: E402

REPLICATES = 8
SEED = 60  # The ticket number. Any fixed value works; a fixed one makes the order reproducible.
RUN = "randomized-r8"


async def main() -> None:
    registry = load_registry()
    client = anthropic.AsyncAnthropic(api_key=load_api_key())

    schedule = [(cell, replicate) for cell in CELLS for replicate in range(REPLICATES)]
    random.Random(SEED).shuffle(schedule)

    print(
        f"{len(schedule)} billed calls, seed {SEED}, {REPLICATES} replicates of "
        f"{len(CELLS)} cells.\n"
    )

    for index, (cell, replicate) in enumerate(schedule):
        observation = await extract(
            example=cell.example,
            document=cell.document,
            axis=cell.axis,
            variant=cell.variant,
            registry=registry,
            client=client,
            run=RUN,
            sequence_index=index,
        )
        flag = "" if observation.status == "extracted" else "  <-- !"
        print(
            f"{index:>4}  {cell.document:<14}{cell.variant:<11}rep{replicate}  "
            f"{observation.fields_correct}/{observation.fields_expected}  "
            f"{observation.mean_confidence:.3f}  {observation.status}{flag}",
            flush=True,
        )

    print(f"\n{len(schedule)} calls appended to observations.jsonl as run={RUN!r}.")
    print("Now: uv run python eval/prototype_label_placement/analyse.py")


if __name__ == "__main__":
    asyncio.run(main())
