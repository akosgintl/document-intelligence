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

## ⚠️ Corrections after reviewing the PRADO specimens directly

Two of the findings below are wrong as written, and one is void. Recorded here rather than edited away, because the errors are the useful part.

1. **The identity card's name field is `stacked` on the real card, not `inline`.** The table below labels `inline` as the eID's *(real)* placement on the strength of #47's summary sentence "the eID identity card sets its labels inline". The `HUN-BO-06001` specimen does not support that: `Családi és utónév/Family name and Given name:` sits on its own line with `SZEPENÉ KISS ROZÁLIA` **below** it. What is inline on that card is `Nem/Sex:`, `CAN:` and (on the verso) `Kiállító hatóság:`; the dates and document number are label-left with the value **right-aligned** at the far edge. So the real eID mixes at least three placements *within one card*, and the name — the only field this probe's placement effect lives in — is stacked.

   This inverts the reading: **the placement Hungary actually prints for the name is the one that produced a 7-in-8 wrong split.** That is a sharper warning for #58 and for production than "match the document and you're fine", and it is a problem #60's framing cannot express, since both of its candidate shapes pick one placement per *type* and the real card needs one per *row*.

2. **The MRZ finding is void.** `pages.py` passed accented names straight into `mrz_td1`, so the zone this probe printed contained `Á`, `Ő`, `É` and `Í` — characters the MRZ alphabet does not have. The model was asked to transcribe a zone that cannot exist, so "the MRZ did not survive character-exact" measured nothing. `identifiers._transliterate` now applies ICAO Doc 9303 Part 3 §6.A and the document code is `I<` rather than `ID`, both confirmed against the specimen's `I<HUN000188KE<1…` / `SZEPENE<KISS<<ROZALIA<<<<<<<<<`. Re-measure before repeating the claim.

   Worth keeping alongside it: `docs/research/hungarian-passport-field-layout.md` §7.4 transcribes the passport specimen's MRZ line 1 as **45 characters** where TD3 has 44 — one filler too many. A human reading an MRZ off a PRADO image made the same off-by-one the model made. That is evidence about trailing-filler runs being the fragile part of an MRZ for *any* reader, and it is a better-founded version of what the void finding was reaching for.

3. **`ŐRSÉBET` is not a Hungarian name** (`ERZSÉBET` is). It came from `fixtures/catalogue.py`'s committed invoice fixture rather than being invented here, but it means the name-split cells may be measuring "layout matters when the token is lexically unrecognisable" rather than "layout matters". Untested; see the note at the end.

## Findings

Two passes. **The second supersedes the first**, which was measuring a bug.

| | calls | design |
|---|---|---|
| Pass 1 — `randomized-r8` | 72 | 3 uniform placements × 2 documents, plus 3 legend variants; nonce holder name; **invalid MRZ** |
| Pass 2 — `names-and-placement-r6` | 144 | 4 placements (incl. the specimen's own) × 3 holder names × 2 documents; MRZ per 9303 §6.A |

### The answer: both factors are noise, and pass 1's effect was my own bug

**Placement has no detectable effect on extraction** — including the `specimen` arm, which draws each card as PRADO prints it, against three crude uniform controls:

| comparison | Δ | p | Field-pairs differing |
|---|---|---|---|
| `specimen` vs `stacked` | −0.009 | 1.000 | 3 / 26 |
| `specimen` vs `inline` | −0.017 | 1.000 | 2 / 26 |
| `specimen` vs `column` | −0.002 | 1.000 | 5 / 26 |
| `stacked` vs `inline` | −0.009 | 0.502 | 2 / 26 |

**The holder's name has no detectable effect either.** `nonce` (`ŐRSÉBET`, not a word) versus `real` (`ERZSÉBET`, identical in every other respect) is Δ −0.005, p=0.750. The `specimen` arm — `SZÉPENÉ KISS ROZÁLIA`, a two-word married surname that invites cutting one word early — is no worse than either (p=0.375, p=0.876). Lexical recognisability of the given name is not what was driving pass 1.

**What was driving it: an MRZ that could not exist.** Pass 1's `pages.py` fed accented names into `mrz_td1`, so the identity card printed `KOVÁCS<TŐKE<<ŐRSÉBET<ÍRISZ` — characters the zone's alphabet does not have. Holding everything else constant, the single comparable cell moves:

| id_card, `nonce` name, `stacked` placement | `surname`+`givenNames` correct | MRZ character-exact |
|---|---|---|
| Pass 1 — accented, unwritable zone | **2 / 16** | 3 / 24 |
| Pass 2 — transliterated per §6.A, `I<` document code | **11 / 12** | 70 / 72 |

The only thing that changed in that cell is the zone. **A valid MRZ hands the model the name split**: `KOVACS<TOKE<<ORSEBET<IRISZ` marks the primary/secondary boundary with `<<`, and printing a zone the model cannot trust throws that away. The 7-in-8 split failure that pass 1 attributed to label placement was an artifact of a broken fixture.

### What this means for #60

The empirical question the ticket raised — *"does label placement affect extraction accuracy at all?"* — answers **no**, now that it is asked against a page whose MRZ is writable and against the layout the card actually prints. Combined with the legend axis from pass 1 (12/12 Fields correct with no field names printed anywhere, p=1.000 on every pairing), **neither half of #60 can be justified on extraction-accuracy grounds.**

That is exactly the case the ticket's third bullet anticipated: *"whether a fidelity gap that the eval cannot detect is worth code at all"*. The measurement says the eval cannot detect it. Whether the fixtures should still look like the documents is a judgement for the ticket, not a finding this probe can supply.

One thing the probe does supply: **#60's decision as framed cannot be made.** Both candidate shapes pick one label placement per Document Type, and #47 §6 shows neither card prints one — the eID stacks its name, pairs two fields inline on a row, and right-aligns three more. The `Row.place` / `Row.align` / `Pair` machinery on this branch is the per-row third shape, and it is small: one field on `Row`, one match arm, one element type.

### Findings that outlive the axes

- **The MRZ transcribes character-exact 70 times in 72**, once the zone is writable. Both misses are the same failure: one filler too many in a trailing run (31 characters where TD1 has 30). This answers what [#53](https://github.com/akosgintl/document-intelligence/issues/53) asks about the passport's TD3 zone — the risk is not the check digits, it is counting `<`. Note the same off-by-one appears in `hungarian-passport-field-layout.md` §7.4's hand transcription, so it is not a model-specific weakness.
- **A machine-readable zone disambiguates the name split for free.** The two types that combine `surname` and `givenNames` on one printed line are the identity card and the address card; only the identity card has an MRZ. This is worth knowing for [#55](https://github.com/akosgintl/document-intelligence/issues/55), whose address card has no such backstop, and it is an argument for the Schemas' insistence that the zone be captured verbatim.
- **`sex` is the one field the specimen layout made worse**: `N/F` returned 9 times in 18 under `specimen` against 15–18 in 18 under the uniform arms. Under `specimen` it sits in a `Pair`, sharing a row with `Állampolgárság/Nationality:`. One field at n=18 is a hypothesis, not a finding — but if a fixture wants two fields on one row, this is the thing to watch.
- **`extraction_needs_review` remains near-universal.** 92 of 144 Extractions landed in review, many of them at 100% accuracy, because a single Field below the 0.9 Threshold is enough. Convention 3 builds a nullable case per Document Type, so [#57](https://github.com/akosgintl/document-intelligence/issues/57) should expect this on every one of them rather than treating it as a fixture defect.
- No session drift: first half 0.9818, second half 0.9815. ~4,930 in / 727 out tokens, 7.5s per call.

### What this design could not have detected

Twenty-six Field-pairs at six replicates finds effects that move whole Fields between right and wrong; it does not resolve a couple of accuracy points. Every null above is "no effect large enough to matter for #60's decision", not "no effect". Two Document Types is the sampling frame — nothing here licenses a claim about the passport or the 2012 laminated card. And pass 2 changed several things at once relative to pass 1 (the zone, the document code, the name arms, the specimen layout), so the attribution of pass 1's effect to the MRZ rests on the single held-constant cell tabulated above, not on a designed comparison.
