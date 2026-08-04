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

Every result is appended to `observations.jsonl` as it arrives. That breaks the "no persistence"
rule on purpose: these observations cost real money, and losing them to a closed terminal means
paying again.

## Findings

Run 2026-08-04, 37 billed calls (32 variants + 5 repeats), `schema_version` 1 throughout.

**Yes — they classify, and the `MINTA / SPECIMEN` marking can stay.** 32/32 landed on the
intended Document Type at `classified`. Nothing came back `unclassified`, nothing came back
`classification_needs_review`, and no call ever matched a *different* type. Confidence spanned
0.90–0.99 against the identity types' 0.9 Threshold. Extraction would have followed in every case.

### Per axis, over all four types

| Axis | On | Off | Effect |
|---|---|---|---|
| `MINTA / SPECIMEN` overlay | 0.978 | 0.979 | **−0.002 — nothing** |
| Photo placeholder box | 0.980 | 0.977 | +0.003 |
| Card chrome vs bare text | 0.982 | 0.974 | +0.008 |

All three effects are smaller than the 0.97↔0.90 jitter of a single repeated variant (below), so
only the direction of the chrome axis is worth anything — and it is worth it in one specific place.

1. **The SPECIMEN overlay is free.** This was the ticket's stated risk and it did not
   materialise: not one call read "MINTA" as "blank template". Convention 8's invalid check
   digits do **not** become the only fixture/forgery separator — the map keeps both.
2. **The photo axis is a non-issue, in both directions.** Convention 2's "no photo" costs the
   three types whose Schema says a photo is there essentially nothing (id_card −0.003,
   passport ±0.000, licence +0.005). The contradiction between convention 2 and those Schema
   descriptions is real on paper but does not bite at classification time. The control behaved
   too: the address card, whose Schema says "carrying no photograph", was not hurt by a photo
   box it should not have (0.968 with, 0.958 without).
3. **The address card is the weak one, and chrome is what rescues it.** Every one of the five
   lowest readings is an address card — it has no photo, no MRZ, and monolingual labels, so it
   is the least distinctive of the four by construction. Its worst variant, `S--`
   (SPECIMEN + bare text, no chrome), read **0.90 — exactly the Threshold, zero margin**.
   Adding chrome alone takes the same page to 0.98.
4. **That 0.90 is not a one-off.** Re-run 5× (6 draws total) it came back 0.97, 0.97, 0.97,
   **0.90**, 0.97 — bimodal, on the line roughly one draw in six, never under it. `0.90 < 0.9`
   is False so it classifies, but a fixture that samples the low mode has no room left.
5. **Invalid check digits cost nothing at classification time.** Every value on every page
   carried one; no reading suggests the model priced it in.

### Minimum fidelity

Bare text with the real printed labels from #47 is enough for the ID card, passport and
licence — all three held ≥0.97 in every variant including bare-text-plus-SPECIMEN. **For the
address card, draw the card outline and field grid.** It is the cheapest insurance in the whole
matrix (0.90 → 0.98) and it is the only place any axis mattered.

Cost shape, for #51's budgeting: ~3,690 input / 117 output tokens and ~3.2s per classification.
