# PROTOTYPE — does a SPECIMEN-marked synthetic page classify at all?

**Throwaway code answering one question ([#49](https://github.com/akosgintl/document-intelligence/issues/49)). Not the fixture renderer — that is [#51](https://github.com/akosgintl/document-intelligence/issues/51), and nothing here should be lifted into it.**

## The question

Will a deliberately low-fidelity, `MINTA / SPECIMEN`-marked, photo-less synthetic page classify as
its intended Document Type at all — or will the Model Provider read "MINTA" and call it a blank
template?

This is [#46](https://github.com/akosgintl/document-intelligence/issues/46)'s load-bearing risk.
Conventions 2, 3 and 6 all assume synthetic fixtures are classifiable. If they aren't, the map's
destination needs redrawing before a renderer is built.

## Why the axes are these three

The ticket names them: the `MINTA / SPECIMEN` overlay, a photo placeholder box, and card chrome
(outline + field grid) versus bare text. All 8 combinations are probed, because reading the
Schema descriptions sharpens the *photo* axis in particular:

- `hungarian_id_card` — "It carries the holder's photograph and a machine-readable zone"
- `hungarian_passport` — "a booklet page bearing the holder's photograph"
- `hungarian_driving_licence` — "the holder's photograph and signature"
- `hungarian_address_card` — "carrying **no** photograph, no machine-readable zone"

So convention 2's "no photo" instructs the model to look for something three of the four Schemas
say is there. That is a contradiction between two settled conventions, not just a fidelity
question — and the address card is the control, since for it "no photo" is *correct*.

## What is actually called

`classify_document([page], registry.all_latest())` against the real `AnthropicModelProvider` —
**billed**. `classify_page` is deliberately not probed: `pipeline.py:141` short-circuits it for
single-Page Submissions, and every golden fixture is a single `submission.png`, so it never runs
for one. One API call per variant.

Status is computed the way `pipeline._classify_and_extract_group` computes it — the identity
types sit at Confidence Threshold **0.9**, the invoice at 0.8:

| Provider result | Status |
|---|---|
| `documentTypeName` is null | `unclassified` |
| confidence < threshold | `classification_needs_review` |
| otherwise | `classified` (extraction would follow) |

## Deliberate content choices

- **Real printed labels** from `docs/research/hungarian-document-printed-labels.md` (#47) — the
  2021 eID generation for the ID card, monolingual for the address card, bare EU numbers for the
  licence. A probe with invented labels answers a different question.
- **Accented Hungarian values** (`Ő`, `Ű`, `É`, `Á`, `Ö`, `Ü`) in system DejaVu. Deliberately the
  *system* copy at `/usr/share/fonts/truetype/dejavu/` — vendoring is #51's job, not a
  prototype's. `ImageFont.load_default()` cannot draw any of these.
- **Invalid check digits** throughout (convention 8), so this also shows whether they cost
  anything at classification time.

## Run it

```
uv run python eval/prototype_specimen_classification/run.py
```

`[r]` renders all 8 variants to `pages_rendered/` for free — **look at them before spending anything**.
`[1]`–`[8]` fire one variant, `[a]` fires all 8 for the current type. `[t]` cycles Document Type.

The answer, though, comes from the second pass — `run.py` fires each cell once, which turned out
to be too thin to support any claim about the axes:

```
uv run python eval/prototype_specimen_classification/sequence.py   # 160 billed calls, ~9 min
uv run python eval/prototype_specimen_classification/analyse.py    # free, reads observations.jsonl
```

`sequence.py` shuffles 5 replicates of all 32 cells into **one seeded random order** and records
each call's position, so ordering effects can be tested rather than assumed away. Why both
changes were needed is in *Findings*.

Every result is appended to `observations.jsonl` as it arrives. That breaks the "no persistence"
rule on purpose: these observations cost real money, and losing them to a closed terminal means
paying again.

## Findings

Two passes, **197 billed calls** total, `schema_version` 1 throughout.

| | calls | design |
|---|---|---|
| Pass 1 — `run.py --all` | 32 + 5 repeats | one draw per cell, fixed order |
| Pass 2 — `sequence.py` | 160 | 5 replicates × 32 cells, one seeded random order |

### The answer

**Yes — they classify, and the `MINTA / SPECIMEN` marking can stay.** Across all 197 calls, every
single one matched the intended Document Type at `classified`. Nothing came back `unclassified`,
nothing came back `classification_needs_review`, no call ever matched a *different* type, and
**not one call fell below its Confidence Threshold**. In the randomized pass the observed range was
0.95–0.99 against the identity types' 0.9.

### Why pass 1 wasn't enough

`anthropic_provider.py` sets no `temperature`, so the API default of 1.0 applies and every call is
a **draw from a distribution, not a reading**. Pass 1 measured each cell once and then compared
those single draws across axes. Two consequences, both visible in the data:

- **18 of 32 cells returned more than one distinct confidence across just 5 draws**, and 3 of
  pass 1's single draws fall outside their own cell's replicated range.
- Pass 1's variant order put all four non-SPECIMEN variants before all four SPECIMEN ones within
  each Document Type, so any session drift would have landed squarely on the axis being measured.

### All three axes are noise

Permuting at the **cell** level — 16 cells on versus 16 off, which is the correct unit, since five
draws of one page are not five independent observations:

| Axis | On | Off | Gap | p |
|---|---|---|---|---|
| `MINTA / SPECIMEN` overlay | 0.9810 | 0.9768 | +0.0042 | 0.234 |
| Photo placeholder box | 0.9794 | 0.9784 | +0.0010 | 0.808 |
| Card chrome vs bare text | 0.9808 | 0.9770 | +0.0038 | 0.293 |

None is distinguishable from noise. **Permuting individual calls instead would report the SPECIMEN
axis at p=0.009 and chrome at p=0.023** — that is pseudoreplication, not signal, and it is exactly
the mistake replication was added to avoid. Both are in `analyse.py`; the cell-level one governs.

So: the ticket's stated risk does not materialise, and it is not a near miss. Convention 8's
invalid check digits are **not** left as the only thing separating a fixture from a forgery.

### The order confound was real to worry about, and absent in fact

First half of the randomized sequence 0.9786, second half 0.9791, p=0.818. No drift — so pass 1's
fixed ordering did not actually corrupt it. Worth stating plainly: randomizing was the right call
*a priori* (every call is independent, but that is an argument, not a measurement), and it came
back clean.

### Withdrawn: the address-card chrome requirement

Pass 1 concluded that the address card's `S--` cell sat *exactly* on 0.90 with zero margin, and
that card chrome was needed to buy headroom. The replicated pass does not support that:

- That cell read **0.97 in all five randomized draws**. Pooling both passes it is 0.90 twice in 11
  draws — the low mode is real, but it never went *under*, and it did not recur when the call order
  stopped being predictable.
- The worst bare-text address card in the whole randomized pass is **0.95 — a margin of +0.05**.
- Chrome's effect on the address card is +0.0115, which is inside the noise band above.

The address card remains the weakest of the four (mean 0.968, min 0.95, versus 0.976–0.988 for the
rest) — no photo, no MRZ, monolingual, least distinctive by construction. But it has margin, and
**chrome is not a requirement for it.** Per type, in the randomized pass:

| Document Type | Mean | Min | Margin over threshold |
|---|---|---|---|
| `hungarian_passport` | 0.988 | 0.98 | +0.08 |
| `hungarian_id_card` | 0.984 | 0.98 | +0.08 |
| `hungarian_driving_licence` | 0.976 | 0.97 | +0.07 |
| `hungarian_address_card` | 0.968 | 0.95 | +0.05 |

### Minimum fidelity

Bare text with the real printed labels from #47 is enough for all four types, with or without the
SPECIMEN overlay and with or without a photo box. Nothing in the matrix needs to be sacrificed.

Invalid check digits cost nothing at classification time. Cost shape for #51's budgeting:
~3,690 input / 117 output tokens and ~3.2s per classification.
