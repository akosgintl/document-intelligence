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

**72 billed Extractions**, `claude-sonnet-5`, run `randomized-r8`, seed 60. ~5,150 input / 737 output tokens and 7.3s per call. No session drift (first half 0.9435, second half 0.9428, Δ −0.0007), so the randomized order came back clean the way #49's did.

| axis | document | variant | accuracy | mean conf | statuses |
|---|---|---|---|---|---|
| legend | driving_licence | `absent` | **1.000** [1.000–1.000] | 0.931 | needs_review ×8 |
| legend | driving_licence | `horizontal` | **1.000** [1.000–1.000] | 0.948 | needs_review ×8 |
| legend | driving_licence | `rotated` | 0.969 [0.917–1.000] | 0.923 | needs_review ×8 |
| placement | address_card | `stacked` | **0.990** [0.917–1.000] | 0.923 | extracted ×4 |
| placement | address_card | `column` *(real)* | 0.958 [0.833–1.000] | 0.923 | extracted ×2 |
| placement | address_card | `inline` | 0.938 [0.833–1.000] | 0.895 | extracted ×3 |
| placement | id_card | `inline` *(real)* | 0.929 [0.929–0.929] | 0.943 | extracted ×7 |
| placement | id_card | `column` | 0.920 [0.857–1.000] | 0.937 | extracted ×4 |
| placement | id_card | `stacked` | **0.786** [0.714–1.000] | 0.925 | needs_review ×8 |

### The answer, and it is not the one the ticket offered

**The legend buys nothing measurable, and the rotated one is if anything worse.** The licence extracted **12 of 12 Fields correctly on all 8 draws with no field names printed anywhere on the card** — bare EU numbers `1.` `2.` `4a.` on the recto and a table headed `9. 10. 11. 12.` on the verso were enough. The horizontal legend was also 8/8 perfect; the rotated one lost `nationality` on 3 of 8 draws, plausibly because the rotated run sits beside `14. Államp:`. Every paired test on this axis is p=1.000.

So #60's argument — *"if the licence prints no legend, the fixture prints no field names anywhere, which is a materially different document from the real one"* — is **true as a fidelity statement and false as an extraction-accuracy one**. Building rotated-text support cannot be justified on extraction grounds. That is exactly the case #60's third bullet anticipated: a fidelity gap the eval cannot detect.

**Placement is noise for every unambiguous Field — and decisive for one thing.** Only 6 of 26 (document, Field) pairs ever differ across placements, and pooled the axis is indistinguishable from noise (`stacked` vs `inline` Δ −0.053 p=0.379; `stacked` vs `column` Δ −0.058 p=0.441; `inline` vs `column` Δ −0.005 p=1.000).

**Do not read that pooled null as "placement doesn't matter."** It is the average of two large, opposite-signed, document-specific effects on one operation: splitting a single printed name line into `surname` and `givenNames`.

| | `stacked` | `inline` | `column` |
|---|---|---|---|
| id_card `surname`/`givenNames` wrong | **7/8** | 0/8 | 0/8 |
| address_card `surname` wrong | 1/8 | **5/8** | 2/8 |

Under `stacked` the identity card returned `surname: "KOVÁCS-TŐKE ŐRSÉBET"`, `givenNames: "ÍRISZ"` on 7 of 8 draws — the split moved by one word. Under `inline` and `column` it was correct 8/8. The address card runs the other way: `stacked` is its best placement and `inline` swallowed the whole line into `surname` on 5 of 8 draws. **The direction of the effect reverses between two documents carrying the same name**, which is why they cancel, and why no single placement is safe for both.

Drawing each type at the placement #47 says it really uses beats forcing everything to `stacked` — 0.929 vs 0.786 on the identity card — at the cost of 0.958 vs 0.990 on the address card. Net, matching the document wins, and it wins where the ticket said it would: on the type `card` was knowingly wrong for.

**What this does not explain.** Why the flip. The identity card's label is long and bilingual (`Családi és utónév/Family name and Given name:`) and the address card's is short and monolingual (`Családi és utónév:`), so label length is the obvious suspect — but this probe did not vary label length and cannot say. Two documents is also two documents: the effect is large and consistent within each, and the claim that it *generalises* rests on nothing.

### Findings that are not about the axes

- **`surname`/`givenNames` split from one printed line is unreliable in its own right.** It failed under some placement on both types, and the address card got it wrong 5/8 under `inline` even though nothing on that page is ambiguous to a Hungarian reader. This is a risk [#58](https://github.com/akosgintl/document-intelligence/issues/58) and [#55](https://github.com/akosgintl/document-intelligence/issues/55) inherit, and arguably a question for [#40](https://github.com/akosgintl/document-intelligence/issues/40)'s Schema rather than for a fixture: the card prints one field and the Schema asks for two. A holder with two given names makes it worst, and real holders have two given names.
- **The MRZ did not survive character-exact.** `mrz` was wrong on 6–8 of 8 draws under *every* identity-card placement — always the same way, one filler character too many in line 1 (31 characters returned against TD1's 30). Constant across the axis, so it biases nothing here, but it is a direct answer to the question [#53](https://github.com/akosgintl/document-intelligence/issues/53) asks about the passport's TD3 zone: a long run of `<` is where transcription breaks, and #41's argument that verbatim capture preserves all five check digits should be tested rather than assumed.
- **Century inference held.** All 24 licence extractions returned `categories` exactly right, including `12.06.95.` → `1995-06-12` and `05.02.13.` → `2013-02-05`. That is the risk ADR-0010 knowingly accepted and [#54](https://github.com/akosgintl/document-intelligence/issues/54) wanted observed; on this fixture, at this fidelity, it did not materialise.
- **A correctly-null Field can hold a Document below its Threshold on its own.** Every one of the 24 licence extractions landed `extraction_needs_review` **while being 100% accurate**, because `generalRestrictionCodes` came back null at 0.60–0.85 confidence on all 24 draws. The address card's `surname` went as low as 0.30 and its `givenNames` to 0.30. This is [#57](https://github.com/akosgintl/document-intelligence/issues/57)'s warning arriving early, and it is sharper than the map's version: it is not that low-fidelity pages depress confidence generally, it is that a Field the page deliberately shows nothing for is reported at low confidence and drags the whole Document into review at threshold 0.9. A golden set built on nullable cases (convention 3) will hit this on every one of them.

### What the design could not have detected

Twenty-six Field-pairs at eight replicates finds effects that move whole Fields between right and wrong; it does not resolve a couple of accuracy points. The pooled nulls above are "no effect large enough to matter for #60's decision", not "no effect". Two documents on the placement axis and one on the legend axis is also the sampling frame — nothing here licenses a claim about the passport or the 2012 laminated card, which were deliberately left out.
