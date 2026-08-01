# Hungarian Driving Licence (Vezetői Engedély) Field Layout

**Scope.** This document researches, from primary sources, what fields a Hungarian driving licence (vezetői engedély) prints, per the EU harmonized driving-licence model (Council/EP Directive 2006/126/EC, "on driving licences (Recast)") and Hungary's national implementing regulation, Government Decree 326/2011. (XII. 28.) Korm. rendelet ("a közúti közlekedési igazgatási feladatokról, a közúti közlekedési okmányok kiadásáról és visszavonásáról"). It covers the standard EU numbered fields and which of them are actually printed on the Hungarian card, the category-table structure (the nested "line items"-shaped part of the layout: category code + per-category issue date, expiry date, restriction codes), and Hungary-specific category and restriction-code conventions. This is a fact-gathering document for a later schema-design ticket — it captures facts with citations, not JSON Schema.

Every claim below is either (a) a direct quote or close paraphrase of text fetched from a cited primary source, or (b) explicitly marked **not confirmed by a fetched primary source** where the investigation came up empty or a tool could only summarize rather than quote verbatim.

---

## Summary of findings

| Question | Finding |
|---|---|
| Which EU numbered fields (1–12) does the Hungarian card print? | **All of them, including the optional address field.** The European Commission's own Hungary-HU4 legend lists fields 1–12 exactly matching Directive Annex I, with field 8 as "Permanent place of residence" — confirming Hungary prints the (directive-optional) address field. |
| EU category codes on the card | AM, A1, A2, A, B1, B, BE, C1, C1E, C, CE, D1, D1E, D, DE — all defined in Directive Article 4, all confirmed usable on Hungarian licences via Decree 326/2011 Annex 2. |
| Category-table shape (fields 9–12) | A per-category row: category code (heading 9), first-issue date (heading 10), expiry date (heading 11), restriction/code list (heading 12) — codes that apply to *all* categories on the licence may instead be printed once under headings 9/10/11 rather than per row. |
| Hungary-specific national categories | **K** (garden tractor / animal-drawn vehicle), **T** (agricultural/forestry tractor + 2 heavy trailers, slow vehicle+trailer, garden tractor, animal-drawn vehicle), **M** (moped incl. "mopedautó", animal-drawn vehicle, garden tractor after age 16), **TR** (trolleybus, + several fallback vehicle types), **V** (garden tractor, animal-drawn vehicle) — printed in the same table as harmonised categories but "in a different type" per the Directive; TR is grouped with the EU commercial categories for administrative-validity purposes on the Hungarian card. |
| Restriction/code conventions | Codes 01–99 are the EU-harmonised codes verbatim (medical/adaptation/limited-use/administrative); codes ≥100 are national-only. Hungary's national code list (100, 101, 102, [103], 104, 105, 110, 111, [130–133], 181–187, 270) is reproduced below from two sources that partially disagree — flagged as an open discrepancy. |
| Administrative validity per category | EU baseline (Directive Art. 7(2)): 10 years (up to 15) for AM/A1/A2/A/B1/B/BE; 5 years for C/CE/C1/C1E/D/DE/D1/D1E. Hungary's actual age-banded implementation (per the EC's Hungary-HU4 page) is finer-grained than the EU floor: e.g. under-40 gets 10 years on B-class categories, tapering to 2 years above age 70. |

---

## 1. The EU harmonized model — numbered fields 1–14 (Directive 2006/126/EC, Annex I)

Fetched from the consolidated Directive text, `02006L0126 — EN — 22.07.2018 — 010.001` (EUR-Lex, [CELEX:02006L0126-20180722](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:02006L0126-20180722), Annex I §3). Quoting the directive's own field list:

> Page 1 shall contain: ... (d) information specific to the licence issued, numbered as follows:
> 1. surname of the holder;
> 2. other name(s) of the holder;
> 3. date and place of birth;
> 4. (a) date of issue of the licence;
>    (b) date of expiry of the licence or a dash if the licence is valid indefinitely under the provision of Article 7(2)(c);
>    (c) the name of the issuing authority (may be printed on page 2);
>    (d) a different number from the one under heading 5, for administrative purposes (optional);
> 5. number of the licence;
> 6. photograph of the holder;
> 7. signature of the holder;
> 8. permanent place of residence, or postal address (optional);
> 9. category of vehicle(s) the holder is entitled to drive (national categories shall be printed in a different type from harmonised categories);

Page 2:

> (a) 9. category of vehicle(s) the holder is entitled to drive (national categories shall be printed in a different type from harmonised categories);
> 10. date of first issue of each category (this date must be repeated on the new licence in the event of subsequent replacement or exchange); each field of the date shall be written with two digits ... day.month.year (DD.MM.YY);
> 11. date of expiry of each category; each field of the date shall be written with two digits ... day.month.year (DD.MM.YY);
> 12. additional information/restriction(s), in code form, facing the category affected.

Two further page-2 items exist but are administrative, not identity/entitlement data:

> 13. ... a space reserved for the possible entry by the host Member State of information essential for administering the licence;
> 14. a space reserved for the possible entry by the Member State which issues the licence of information essential for administering the licence or related to road safety (optional).

Field 4(c) (issuing authority) "may be printed on page 2" per the directive text — its physical placement is not fixed. Field 8 (address) and field 4(d) (secondary admin number) are explicitly marked **optional** by the directive itself. Fields 1–3, 4(a)/4(b), 5–7, and 9–12 are not marked optional and are mandatory on every EU model licence.

The directive also requires (Annex I §3(b), M2 amendment) an on-card **explanation of numbered items 1, 2, 3, 4(a), 4(b), 4(c), 5, 10, 11 and 12** — i.e. those specific items get printed legends, while 6, 7, 8, 9 do not (self-evident from a photo/signature/address/category-list, presumably).

## 2. Which of these fields the Hungarian card actually prints

Primary source: European Commission, DG MOVE's "Driving licence in Member States" comparison tool, the Hungary **HU4** model page (current model, issue period 19/01/2013–01/01/2038): [road-safety.transport.ec.europa.eu/.../hungary-hu4_en](https://road-safety.transport.ec.europa.eu/road-safety-member-states/driving-licence-member-states/driving-licence-models/hungary-hu4_en). This page's "Legend" section (fetched and reproduced verbatim below via `curl` + HTML-strip, not summarized) lists:

```
1   Surname of the holder
2   Other name(s) of the holder
3   Date and place of birth
4a  Date of issue of the licence
4b  Date of expiry of the licence
4c  Name of the issuing authority
5   Number of licence
6   Photograph of the holder
7   Signature of the holder
8   Permanent place of residence
9   category(ies) of vehicle(s) the holder is entitled to drive
10  Date of first issue of each category(ies)
11  Date of expiry of each category
12  Additional information/restriction(s)
```

This is a 1:1 match to the Directive's numbered list from §1 above, **including the optional field 8 ("Permanent place of residence")** — so unlike some Member States that omit the optional address field, Hungary's current card prints it. Field 4(d) (secondary admin number) is not listed in the legend, so it is either absent or not separately called out by the EC's summary — **not confirmed either way by a fetched primary source**.

Card physical description from the same page: ID-1 format, 85.6 × 53.98 mm, polycarbonate, pink colour, with "European Driving Licence" printed in pink letters in a horizontal stripe on the top third of the front, and "Driving licence" in the EU official languages in the lower third — consistent with the Directive's Annex I §3(e) requirement (confirmed separately in the Directive text itself, which lists `Vezetői engedély` as the Hungarian-language rendering of "Driving Licence" among all EU-language translations printed as the pink background text).

Hungary's card-issuing decree, [326/2011. (XII. 28.) Korm. rendelet](https://net.jogtar.hu/jogszabaly?docid=a1100326.kor) (Nemzeti Jogszabálytár), separately confirms (Article 24(10), quoted via fetch): *"A vezetői engedélyt a személyi adat- és lakcímnyilvántartással egyező személyi adatokkal kell kiállítani"* ("The driving licence must be issued with personal data matching the personal-data-and-address register") — consistent with address being sourced from, and printed from, Hungary's civil registry. The same decree, Article 28 (quoted via fetch): *"A vezetői engedélybe az állampolgársági adatot az országkód, az egészségi feltételeket vagy a korlátozásokat a 8. mellékletben meghatározott számkód formájában kell feltüntetni"* ("Nationality shall be entered as a country code, and health conditions or restrictions in the numerical-code form set out in Annex 8") — this is the legal basis for the code-list machinery in §5 below. Note: the decree fetch was done through a tool that paraphrased rather than rendered the full document, so beyond these two quoted sentences, the decree's exact field-by-field layout description (if it has one, e.g. in its own Annex 5) is **not confirmed by a fetched primary source** — the EC HU4 legend above is the stronger source for the actual on-card field list.

## 3. The category table — codes, and structure of fields 9–12

### 3a. EU-harmonised category codes and definitions (Directive 2006/126/EC, Article 4)

All fetched verbatim from the same consolidated EUR-Lex PDF as §1. Category, definition (paraphrased where the definition is long), and minimum age:

| Category | Definition (paraphrased/quoted) | Minimum age |
|---|---|---|
| AM | Mopeds/light quadricycles ≤45 km/h | 16 |
| A1 | Motorcycles ≤125 cm³, ≤11 kW, power/weight ≤0.1 kW/kg; tricycles ≤15 kW | 16 |
| A2 | Motorcycles ≤35 kW, power/weight ≤0.2 kW/kg, not derived from >2× power | 18 |
| A | Motorcycles (any); tricycles >15 kW. Access to A requires 2 years' A2 experience (waivable if ≥24) | 20 (24 if no A2 experience) |
| B1 | Quadricycles per Directive 2002/24/EC | 16 |
| B | Motor vehicles ≤3 500 kg MAM, ≤8 passengers + driver; may combine with trailer ≤750 kg (or up to 4 250 kg combined, with training/test) | 18 |
| BE | Category-B tractor + trailer/semi-trailer, trailer MAM ≤3 500 kg | 18 |
| C1 | Vehicles (not D1/D) 3 500–7 500 kg MAM, ≤8 passengers + driver; trailer ≤750 kg | 18 |
| C1E | C1 tractor + trailer >750 kg, combination ≤12 000 kg (also: B tractor + trailer >3 500 kg, combination ≤12 000 kg) | 18 |
| C | Vehicles (not D1/D) >3 500 kg MAM, ≤8 passengers + driver; trailer ≤750 kg | 21 |
| CE | C tractor + trailer >750 kg | 21 |
| D1 | Vehicles ≤16 passengers + driver, length ≤8 m; trailer ≤750 kg | 21 |
| D1E | D1 tractor + trailer >750 kg | 21 |
| D | Vehicles >8 passengers + driver; trailer ≤750 kg | 24 |
| DE | D tractor + trailer >750 kg | 24 |

(Minimum ages per Article 4(2)–(4) as amended by Directive (EU) 2018/645 ["M9"], which raised the C/CE/D1/D1E/D/DE minimum ages shown above from the original 2006 text's lower figures — the table reflects the current consolidated text.)

### 3b. Category-table field structure (page 2, headings 9–12)

Per Annex I §3 (quoted in §1): for each category the holder holds, the card prints a **row**: category code (heading 9) → date of first issue of that category (heading 10, DD.MM.YY) → date of expiry of that category (heading 11, DD.MM.YY) → any restriction code(s) applicable to that specific category (heading 12). This is confirmed as a genuine per-category row structure, not a flat list, by the directive's explicit instruction that heading-12 codes are "facing the category affected."

However, the directive (and Hungary's own code-list annex, §5 below) also documents an exception to strict per-row nesting: *"Where a code applies to all categories for which the licence is issued, it may be printed under headings 9, 10 and 11"* [once, not repeated per row] — i.e. a restriction code is not always scoped to exactly one category row; it can be document-scoped. This matters for the eventual schema: a restriction code is not necessarily a child of exactly one category line item.

### 3c. Hungary's national (non-harmonised) categories

Source: Hungarian Government Decree 326/2011 (XII. 28.), **Annex 2** ("Nemzetközi kategóriák a 2006/126/EK irányelvnek megfelelően" + "Nemzeti kategóriák"), fetched as a PDF hosted at a Hungarian driving-school site (`jogsivarazs.hu`) but titled and formatted as the verbatim official decree annex text — cross-checked against the EC's HU4 page (§2), which independently lists the same three of these five categories (K, T, M) with matching descriptions, giving reasonable confidence the annex text is accurate even though it was not fetched directly from `njt.gov.hu`. Quoted definitions:

| National category | Definition (Annex 2, verbatim) |
|---|---|
| K | "kerti traktor" (garden tractor); "állati erővel vont jármű" (animal-drawn vehicle) |
| T | "mezőgazdasági vontató (mezőgazdasági és erdészeti traktor) és két nehéz pótkocsi" (agricultural tractor + two heavy trailers); "lassú jármű és pótkocsi" (slow vehicle and trailer); "kerti traktor"; "állati erővel vont jármű hajtására" (driving animal-drawn vehicles); "segédmotoros kerékpár (ide értve a »mopedautót« is)" (moped, incl. "mopedautó") |
| M | "segédmotoros kerékpár (ide értve a »mopedautót« is)"; "állati erővel vont jármű hajtására"; "kerti traktor (16. életév betöltése után)" (garden tractor, after turning 16) |
| TR | "trolibusz" (trolleybus); + fallback rights to mezőgazdasági vontató+2 nehéz pótkocsi, segédmotoros kerékpár, lassú jármű és pótkocsi, kerti traktor, állati erővel vont jármű hajtására — "meghatározása nemzeti kategóriáknál" (its scope is defined under national categories) |
| V | "kerti traktor"; "állati erővel vont jármű hajtására" |

The EC HU4 page's own "National categories" table (§2's source) lists only K, T, M explicitly (not TR, V) with matching wording — e.g. T: *"Agricultural and forestry tractor and 2 heavy trailers, slow vehicle and trailer, garden tractor, animal-drawn vehicle."* TR does appear on the same EC page, but folded into the **commercial-category validity-period row** ("C1, C1E, C, CE, D1, D1E, D, DE, TR (trolleybus): until 60: 5 years; above 60: 2 years") rather than in the national-category description table — confirming TR is treated administratively like a harmonised commercial category on the Hungarian card even though it is a national code. V does not appear on the EC page at all — **its continued current use is not confirmed by the EC primary source**, only by the (third-party-hosted) decree annex text.

Per Directive Annex I §3(d)(9), these national categories are printed in the **same category table** as the harmonised ones, just "in a different type" (i.e., visually distinguished font/style) — they are not a separate section of the card.

## 4. Restriction/code conventions

### 4a. EU-harmonised codes 01–99 (Directive Annex I, as amended by "M7" / Commission Directive (EU) 2015/653)

Fetched verbatim from the consolidated EUR-Lex text. Full structure (grouped headings as printed in the directive):

- **DRIVER (medical reasons):** 01 Sight correction/protection (01.01 glasses, 01.02 contact lenses, 01.05 eye cover, 01.06 glasses or contact lenses, 01.07 specific optical aid); 02 Hearing/communication aid; 03 Prosthesis/orthosis (03.01 upper limb, 03.02 lower limb).
- **VEHICLE ADAPTATIONS:** 10 Modified transmission; 15 Modified clutch; 20 Modified braking systems (incl. 20.07 "Brake operation with maximum force of … N", a **parametric code** — the value is embedded in the code string, e.g. `20.07(300N)`); 25 Modified accelerator; 31 Pedal adaptations; 32 Combined service-brake+accelerator; 33 Combined service-brake+accelerator+steering; 35 Modified control layouts; 40 Modified steering (also parametric: `40.01(140N)`); 42 Modified rear/side-view devices; 43 Driver seating position; 44 Motorcycle modifications ("sub-code use obligatory"); 45 Motorcycle with side-car only; 46 Tricycles only; 47 Restricted to >2-wheel vehicles not requiring balance; 50 Restricted to a specific vehicle/chassis VIN (**free-text-parametric**). Sub-codes 01–44 may append a letter (a=left, b=right, c=hand, d=foot, e=middle, f=arm, g=thumb).
- **LIMITED USE CODES:** 61 daytime only; 62 radius-limited (parametric km); 63 no passengers; 64 speed-limited (parametric km/h); 65 accompanied driving only; 66 no trailer; 67 no motorways; 68 no alcohol; 69 alcohol-interlock required (optionally parametric with an expiry date, e.g. `69(01.01.2016)`).
- **ADMINISTRATIVE MATTERS:** 70 exchange of licence No…, issued by… (parametric, includes an EU/UN country code, e.g. `70.0123456789.NL`); 71 duplicate of licence No… (same shape, e.g. `71.987654321.HR`); 73 restricted to B1-type quadricycles; 78 automatic transmission only; 79 (…) restricted per Article 13, with sub-codes 79.01–79.06 for specific vehicle-type restrictions; 80 restricted to under-24 tricycle-A holders; 81 restricted to under-21 two-wheel-A holders; 95 CPC-holder, until date (parametric, e.g. `95(01.01.12)`); 96 B + heavy trailer combination 3 500–4 250 kg; 97 not authorised for tachograph-regulation-scope C1 vehicles.
- **Codes ≥100:** national codes, valid only within the issuing Member State.
- A restriction/code that applies to *all* categories the licence covers "may be printed under headings 9, 10 and 11" (i.e., once, document-scoped) rather than repeated per category row (also noted in §3b).

Hungary's own Annex 8 to Decree 326/2011 (fetched as a PDF, `jogsivarazs.hu`-hosted but titled/formatted as the verbatim decree annex, "8. melléklet a 326/2011. (XII. 28.) Korm. rendelethez") reproduces this exact 01–99 code list in Hungarian translation, one-for-one — no additions or omissions were found in codes 01–99 between the EU directive text and Hungary's Annex 8.

### 4b. Hungary-specific national codes (≥100)

Two primary/near-primary sources were fetched for Hungary's national code list and they **partially disagree** — flagged rather than silently reconciled:

**Source A** — Decree 326/2011 Annex 8 (`jogsivarazs.hu`-hosted copy, undated in the fetched text but the sibling Annex-2 file carries a 2017-02-24 PDF creation timestamp, suggesting this may be an earlier consolidated version):

| Code | Hungarian text | English gloss |
|---|---|---|
| 100 | Gépjárművezetésre egészségügyi szempontból alkalmatlan | Unfit to drive for health reasons |
| 101 | 1. egészségügyi csoportban alkalmas | Fit in health group 1 |
| 102 | 2. egészségügyi csoportban alkalmas | Fit in health group 2 |
| 104 | Csoportos személyszállítást nem végezhet | May not carry passenger groups |
| 105 | Megkülönböztető jelzést használó járművet nem vezethet | May not drive vehicles using distinguishing (emergency) signals |
| 110 | Tartalék szemüveg tartása kötelező | Spare glasses required |
| 111 | Kétoldali visszapillantó tükör kötelező | Rear-view mirrors on both sides required |
| 181 | Kezdő vezetői engedély minősítés meghosszabbítása | Extension of novice-licence classification |
| 182 | „A" korlátozott kategória | "A" restricted category |
| 183 | Nemzetközi kategóriától eltiltva | Barred from international category |
| 184 | Járműfajtától eltiltva | Barred from a vehicle type |
| 185 | „T" kategóriába tartozó mezőgazdasági vontató könnyű pótkocsival | Category-T tractor with light trailer |
| 186 | „K" kategóriában meghatározott járműveken kívül lassú járművet és pótkocsiját is vezetheti | May also drive a slow vehicle + trailer beyond K-category vehicles |
| 187 | „T" kategóriába tartozó mezőgazdasági vontató pótkocsival | Category-T tractor with trailer |
| 270 | A Magyar Honvédség kezelésében lévő autóbusz vezetéséhez külön jogszabály alapján megszerzett vezetési jogosultság, a 21. életév betöltését követően egyéb autóbuszok vezetésére is jogosít | Right to drive Hungarian Armed Forces buses under separate legislation; also authorises other buses after age 21 |

**Source B** — the EC's Hungary-HU4 "Codes" table (§2's source), which lists the same codes **plus four not present in Source A**: **103** ("Does not satisfy category 2 fitness requirements"), **130, 131, 132, 133** (a locomotor-disorder-related family: 130 "Authorised to drive if the conditions in the appendix to the driving licence are met," 131 "type of vehicle specified in appendix," 132 "converted vehicle specified in appendix," 133 "auxiliary equipment specified in appendix"). Source B's descriptions of the shared codes otherwise match Source A's one-for-one.

Given the timestamp discrepancy, the most likely explanation is that codes 103 and 130–133 were added to the Hungarian national code list at some point after Source A's document was produced, and Source B (the EC's actively maintained comparison page) reflects the current state — but **this is not confirmed**; no dated amendment to Decree 326/2011's Annex 8 was fetched to verify when/whether these four codes were introduced. Treat the current authoritative Hungarian national code list as: 100, 101, 102, 103\*, 104, 105, 110, 111, 130\*, 131\*, 132\*, 133\* (\*not independently confirmed against the decree text itself), 181, 182, 183, 184, 185, 186, 187, 270.

## 5. Administrative validity periods (relevant to the per-category date fields)

EU floor, Directive Article 7(2) (quoted, fetched from the same consolidated text as §1 and §3a):

> (a) ... licences issued by Member States for categories AM, A1, A2, A, B, B1 and BE shall have an administrative validity of 10 years. A Member State may choose to issue such licences with an administrative validity of up to 15 years;
> (b) ... licences issued by Member States for categories C, CE, C1, C1E, D, DE, D1, D1E shall have an administrative validity of 5 years;

Hungary's actual implementation, per the EC's Hungary-HU4 page (§2 source), is age-banded and *shorter* than the EU ceiling in older age brackets:

| Category group | Validity |
|---|---|
| A1, A2, A, B1, B, BE | Until 40: 10 years; 40–59: 5 years; 60–69: 3 years; above 70: 2 years |
| C1, C1E, C, CE, D1, D1E, D, DE, TR (trolleybus) | Until 60: 5 years; above 60: 2 years |

The EC page footnotes: *"This refers to the administrative validity of the document and does not necessarily reflect the holder's right to drive."* This age-banding is consistent with Directive Article 7(3)'s permission for Member States to *"reduce the period of administrative validity ... of driving licences of holders ... having reached the age of 50 years in order to apply an increased frequency of medical checks"* — Hungary's implementation is a specific instance of that general EU-level allowance, not a deviation from it.

Also from the same EC page: Hungary's professional-driver fields are both "NO" — *"Certificate of professional competence is issued: NO"* and *"Code 95 is marked on the driving licence: NO"* — i.e. although code 95 (CPC) exists in Hungary's harmonised code list (§4a/Hungary's Annex 8, which reproduces it), the EC's data indicates it is not actually used/printed on Hungarian licences in practice. This is worth flagging for schema design as a field that is structurally possible but empirically absent on real Hungarian cards.

## 6. Sources not usable

- **PRADO** (Council of the EU's Public Register of Authentic Documents), which independently catalogues Hungary's driving-licence specimens including a provisional/temporary licence variant (`IDEIGLENES VEZETŐI ENGEDÉLY`), returned **HTTP 403 Forbidden** on fetch (`consilium.europa.eu/prado/en/HUN-FP-01001/index.html`) and could not be used as a source. Its existence and general contents were only seen via search-result snippets, not verified against the page itself — **not confirmed by a fetched primary source**, mentioned here only as a pointer for a future research pass if PRADO access becomes available.
- Decree 326/2011's own **Annex 5** (the annex most likely to contain Hungary's own official diagram/description of the card's physical field layout, referenced but not reproduced by Article 24(10)) was not successfully fetched — the `net.jogtar.hu` fetch tool paraphrased the decree rather than rendering its annexes, and no other copy of Annex 5 specifically was located. The EC HU4 legend (§2) is used as the best-available substitute for "what fields are on the card," since it is an independently maintained, image-backed EU source, but a future pass should try to obtain Decree 326/2011 Annex 5 directly (e.g. via Magyar Közlöny, the official gazette) if more precision is needed.

---

## Implications for the eventual JSON Schema (facts only, no schema drafted here)

- The category table is genuinely a **repeating group / nested array** structure: each entry needs (category code, first-issue date, expiry date, restriction codes) — confirmed by Annex I directly.
- The category-code value space spans **19 codes**: the 14 EU-harmonised categories (§3a) plus at least K, T, M, TR, and possibly V (§3c) — Hungary visually distinguishes national from harmonised categories but they occupy the same table/column.
- Restriction codes are not always scoped to one category row — a code can be document-scoped (§3b) — so a naive "restrictionCodes belongs to exactly one category entry" model would be wrong for that case, though the common case (code facing one category) is still the norm.
- Several restriction codes are **parametric** (a numeric or date value embedded in the code string itself, e.g. `20.07(300N)`, `69(01.01.2016)`, `70.0123456789.NL`) rather than a bare enum value — this affects whether restriction codes should be modeled as plain strings/enums or as a small structured object (code + optional parameter).
- Hungary's national code range (100–187, 270, per §4b) is a known, bounded, mostly-enumerable set unlike the free-form 100+ "up to each Member State" of the directive text — a closed enum for Hungary specifically is plausible, with the caveat noted in §4b that four codes (103, 130–133) have only one of two sources confirming them.
- Field 8 (address) should be modeled as present (not optional) for the Hungarian card specifically, contrary to the EU baseline where it's optional — confirmed in §2.
