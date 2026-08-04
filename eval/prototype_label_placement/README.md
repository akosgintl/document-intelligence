# PROTOTYPE — does label placement reach Extraction, and does the licence need its legend?

**Throwaway code answering one question ([#60](https://github.com/akosgintl/document-intelligence/issues/60)). Not the fixture renderer — that is [#51](https://github.com/akosgintl/document-intelligence/issues/51), already shipped. The `label_style` widening and the `Legend` element on this branch are *candidates*, not decisions.**

## The question

[#60](https://github.com/akosgintl/document-intelligence/issues/60) must choose between widening `Geometry` and splitting `render.py` into per-type layout functions, and it flags one thing that could collapse the whole ticket:

> **Does label placement affect extraction accuracy at all?** [#49](https://github.com/akosgintl/document-intelligence/issues/49) measured every fidelity axis it tested as noise, but it measured **classification only**. Label/value *association* is exactly what Extraction reads, so #49's result does not transfer, and nobody has measured it.

So: **if placement is noise for extraction too, #60 collapses to "leave it, and drop the fidelity claim"** — and neither shape needs building. If it isn't noise, the ticket has to pick a shape and the measurement says how much is at stake.

The second half of #60 is a different question wearing the same clothes, and is probed separately:

> **The rotated legend is not optional in the same way.** If the licence prints no legend, the fixture prints no field names anywhere, which is a materially different document from the real one.

That is an argument, and it is a testable one. The licence prints **no label beside any value** — the recto shows bare EU numbers (`1.`, `2.`, `4a.`) and the verso table is headed only `9. 10. 11. 12.`. Every field *name* on the card lives in the legend. So the legend axis is not about where labels sit; it is about whether the document names its fields at all.

## Design

Two axes, deliberately not crossed — crossing them would mean drawing a licence at a label placement it has no labels for.

| Axis | Document | Variants |
|---|---|---|
| **Placement** | `hungarian_id_card` (2021 eID), `hungarian_address_card` | `stacked` (what `card` drew before this branch) / `inline` (what the eID really prints) / `column` (what the address card really prints) |
| **Legend** | `hungarian_driving_licence` | `absent` (what the renderer drew before this branch) / `horizontal` (the 2012 card) / `rotated` (the 2013 card) |

9 cells × 8 replicates = **72 billed Extractions**.

### Why only two types on the placement axis

The passport and the 2012 laminated identity card are *correctly* stacked per [#47](https://github.com/akosgintl/document-intelligence/issues/47). Drawing them at the other two placements would measure the axis on documents whose answer cannot change #60's decision — the eID and the address card are the two types `card` is knowingly wrong for, and they are the two that #58 and #55 will draw. The cost of that choice is generality: if placement turns out to matter, this probe says it matters *for these two types* and a wider sweep would be the follow-up.

### What is actually called

`extract([page], registered.schema)` against the real `AnthropicModelProvider` — **billed**, `claude-sonnet-5`. Classification is deliberately not probed; #49 already did that (197/197 correct, every fidelity axis noise), and this probe exists precisely because that result does not transfer to Extraction.

`probe.py` mirrors `pipeline._run_extraction`, including its exactly-one retry with validation errors fed back into the prompt (#24), and its status decision — any Field below the Confidence Threshold (0.9 for all three types) means `extraction_needs_review` rather than `extracted`.

Comparison is a **recursive** exact match, not `run_eval._values_match`: that applies its ±0.01 tolerance only at the top level, which is the bug [#52](https://github.com/akosgintl/document-intelligence/issues/52) exists to fix. Nothing on these pages is a number, so the probe needs recursion and no tolerance — and borrowing the harness's comparison would have made these results depend on a bug about to be removed. Array comparison is **order-sensitive**, which is one of the open questions #52 has to settle; this probe assumes order is part of the expectation and says so.

### Deliberate content choices

- **Real printed labels** from `docs/research/hungarian-document-printed-labels.md` (#47) — the 2021 eID generation, monolingual for the address card, the 2013 legend wording for the licence. A probe with invented labels answers a different question.
- **Accented Hungarian values** (`Ő`, `Ű`, `É`, `Á`, `Í`) in the vendored DejaVu.
- **Invalid check digits** throughout (convention 8) — személyi azonosító, ICAO TD1 — built through `fixtures.identifiers`, so this also shows whether they cost anything at extraction time as #49 showed they cost nothing at classification.
- **The pages are drafts, not fixtures.** #55 and #58 own the committed data tables. Where a row was dropped or moved between faces to fit an ID-1 face at the renderer's row height, `pages.py` says so in a comment — a reader taking these as a starting point needs to know which deviations are mine and which are the document's.

### The analysis unit, and why it is not the call

[#49](https://github.com/akosgintl/document-intelligence/issues/49)'s method note is the thing to get right: five draws of one page are not five independent observations, and permuting *individual calls* reported an axis effect at p=0.009 that replication showed was pseudoreplication.

The unit here is the **(document, Field) pair**, with that pair's accuracy under each variant averaged over its replicates first, compared by a **paired sign-flip permutation test**. Two Fields of one document are distinct measurements — different label, different value, different place on the page — where two draws of one page are not. Pairing on (document, Field) also removes the largest nuisance source outright: some Fields are simply harder than others.

**What this design can and cannot detect.** Twenty-odd pairs at eight replicates will find an effect that moves whole Fields between right and wrong. It will not resolve a couple of points of accuracy, and a null result should not be read as evidence of no effect at that scale — which is the right calibration for #60, since the ticket asks whether placement matters enough to justify building the knob, not whether it is exactly zero.

## Run it

```
uv run python eval/prototype_label_placement/run.py
```

`[r]` renders all nine variants to `pages_rendered/` for free — **look at them before spending anything.** `[1]`–`[9]` fire one variant, `[a]` fires all nine once.

One pass of `[a]` is **not** the answer: `anthropic_provider.py` sets no `temperature`, so the API default of 1.0 applies and every call is a draw from a distribution rather than a reading. It is there to eyeball a result and catch a broken page before the sequence spends seventy-two calls on the same mistake.

The answer comes from the replicated pass:

```
uv run python eval/prototype_label_placement/sequence.py   # 72 billed calls, ~6 min
uv run python eval/prototype_label_placement/analyse.py    # free, reads observations.jsonl
```

`sequence.py` shuffles 8 replicates of all 9 cells into **one seeded random order** and records each call's position, so ordering effects can be tested rather than assumed away.

Every result is appended to `observations.jsonl` as it arrives. That breaks the prototype no-persistence rule on purpose, for #49's reason: these observations cost real money, and losing them to a closed terminal means paying again.

## Cost

`claude-sonnet-5` at the introductory $2 / $10 per MTok (through 2026-08-31). One extraction is roughly 4k input and 1–2k output tokens, so **~$0.02 per call and ~$1.50 for the full replicated pass.** Extraction output is an order of magnitude larger than #49's classification (a full Field object per Field, each with its own confidence, against ~117 output tokens for a classification), which is why the per-call cost is higher even though the input is comparable.

## What this branch changes outside the prototype

The candidate implementation, so the probe measures the real renderer rather than a lookalike — and so that the diff itself is evidence about how small the "widen `Geometry`" option actually is:

- `Geometry.stacked: bool` → `Geometry.label_style: Literal["stacked", "inline", "column"]`, plus `Geometry.ruled` so the three card placements rule identically while the A4 invoice sheet keeps rendering byte-for-byte as it did on `main`.
- `CARD_INLINE` and `CARD_COLUMN`: the same ID-1 card with **only** `label_style` changed. Same size, same type sizes, same row height — so a page at one placement differs from the `card` page in label placement and in nothing else. That is what makes the axis an axis.
- A `Legend` element that proves no Field, drawn either in the body flow (2012) or composed upright and rotated a quarter turn into a reserved right-edge strip (2013). Pillow cannot draw rotated text, so the strip is the mechanism.

All 33 existing `tests/test_fixture_renderer.py` cases still pass and no committed fixture changes. **None of this is a decision** — if placement measures as noise, the widening comes back out and #60 drops the fidelity claim instead.

## Findings

*Not yet run. `sequence.py` has not been fired.*

Once it has, this section records: the per-cell accuracy and confidence with replicated ranges, the paired test for each axis, whether any variant ever landed a Document in `extraction_needs_review`, and — separately called out, because it is a free observation for [#54](https://github.com/akosgintl/document-intelligence/issues/54) rather than part of this probe's question — whether the licence's `DD.MM.YY.` category dates had their century inferred correctly, and at what Confidence.
