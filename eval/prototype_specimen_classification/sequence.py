#!/usr/bin/env python3
"""PROTOTYPE — the randomized, replicated pass over #49's axis space.

    uv run python eval/prototype_specimen_classification/sequence.py

The first pass (run.py --all) had two methodological holes, and this closes both:

1. **n=1 per cell.** `temperature` is unset in `anthropic_provider.py`, so the API default of
   1.0 applies and every call is a draw from a sampling distribution. The repeat of
   address_card `S--` came back 0.97/0.97/0.97/0.90/0.97 — bimodal — which means the axis
   effects computed from 32 single draws were smaller than the noise inside one cell.

2. **Fixed order.** `VARIANTS` is generated with `specimen` outermost, so within each Document
   Type all four non-SPECIMEN variants fired before all four SPECIMEN ones. Any drift over the
   session — server-side or otherwise — would land squarely on the axis being measured. Every
   call is independent (no conversation state, no prompt caching in the Provider), so there is
   no *known* mechanism for such drift; randomizing removes it as an explanation anyway, which
   is cheaper than arguing about it.

REPLICATES draws of all 32 cells are shuffled into a single seeded order and fired
sequentially, with each call's position recorded so drift can be tested for directly rather
than assumed away.
"""

import asyncio
import random
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from pages import DOCUMENTS, VARIANTS, render  # noqa: E402
from probe import classify, load_api_key, load_registry  # noqa: E402

REPLICATES = 5
SEED = 49  # The ticket number. Any fixed value works; a fixed one makes the order reproducible.
RUN = "randomized-r5"


async def main() -> None:
    registry = load_registry()
    client = anthropic.AsyncAnthropic(api_key=load_api_key())

    # Render once per (document, variant) — the bytes are deterministic, so re-rendering per
    # replicate would only add noise-free work.
    pages = {
        (document, variant.key): render(spec, variant)
        for document, spec in DOCUMENTS.items()
        for variant in VARIANTS
    }

    schedule = [
        (document, variant, replicate)
        for document in DOCUMENTS
        for variant in VARIANTS
        for replicate in range(REPLICATES)
    ]
    random.Random(SEED).shuffle(schedule)

    print(f"{len(schedule)} billed calls, seed {SEED}, {REPLICATES} replicates per cell.\n")

    for index, (document, variant, replicate) in enumerate(schedule):
        observation = await classify(
            image_bytes=pages[(document, variant.key)],
            document=document,
            intended_type=DOCUMENTS[document].type_name,
            variant_key=variant.key,
            variant_description=variant.description,
            registry=registry,
            client=client,
            run=RUN,
            sequence_index=index,
        )
        flag = "" if observation.correct_type and observation.status == "classified" else "  <-- !"
        print(
            f"{index:>4}  {document:<16}{variant.key:<6}rep{replicate}  "
            f"{observation.confidence}  {observation.status}{flag}",
            flush=True,
        )

    print(f"\n{len(schedule)} calls appended to observations.jsonl as run={RUN!r}.")


if __name__ == "__main__":
    asyncio.run(main())
