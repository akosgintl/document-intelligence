# Hungarian identity documents: which printed labels statute actually prescribes

Researched 2026-08-04 from Hungarian statute, EU law and ICAO, resolving [#48](https://github.com/akosgintl/document-intelligence/issues/48).

## Why this file exists

[#47](https://github.com/akosgintl/document-intelligence/issues/47) transcribed the labels off PRADO specimen images and recorded them in `docs/research/hungarian-document-printed-labels.md`. That file is the empirical baseline; this one is the independent check. Three things were still open after it:

1. The passport's **bracketed field numbers** for expiry, authority and signature — unreadable at 600 px and deliberately not guessed.
2. **Cross-validation** — where statute and PRADO agree, a renderer can print with confidence; where they disagree, someone has to decide.
3. The statutory **collective terms** (`természetes személyazonosító adatai`) and the **minority-language name**, neither of which PRADO could resolve.

The ticket's framing is the important one and is preserved throughout: the *field set* was already settled well by [#40](https://github.com/akosgintl/document-intelligence/issues/40)–[#45](https://github.com/akosgintl/document-intelligence/issues/45). The gap is **printed label wording and its position on the card**. A decree saying the card "contains the holder's birth name" does not tell you whether it prints `Születési név` or `Születési családi és utóneve`. Below, every label is placed in exactly one of three buckets — **sourced**, **inferred**, **unsourced** — and the third bucket is the honest one: it is what the renderer must decide about explicitly.

**Scope: label wording, numbering and language only.** Nothing here supersedes the field-semantics notes (`hungarian-id-card-field-layout.md`, `hungarian-passport-field-layout.md`, `hungarian-driving-licence-field-layout.md`, `hungarian-other-id-documents.md`).

## Method, and its ceiling

Sources, all primary, all fetched in full and read rather than summarised:

| Source | How reached | Version read |
|---|---|---|
| Nemzeti Jogszabálytár (`njt.jog.gov.hu`) | direct HTTP, full consolidated text incl. annexes | per-instrument, dates below |
| EUR-Lex | **`eur-lex.europa.eu` returned an interstitial challenge page (HTTP 202, 2 KB) to every automated request**, including with browser headers. Reached instead through the Publications Office CELLAR endpoint `publications.europa.eu/resource/celex/<CELEX>`, which serves the identical EUR-Lex HTML. CELEX URLs below are the canonical citation. | consolidated where one exists |
| ICAO Doc 9303 Parts 3, 4, 5 | direct PDF from `icao.int`, read with `pdftotext -layout` | Eighth Edition 2021 consolidated, Amdt. as published |

njt consolidation dates as fetched: Nytv. 2026.08.03 · Utv. 2026.07.29 · 101/1998 2026.01.01 · 146/1993 2026.01.01 · 414/2015 2026.01.01 · 326/2011 2026.02.26 · 1996. évi XX. tv. 2026.01.22 · 2011. évi CLXXIX. tv. 2026.07.29 · 168/1999 **2015.08.01, its last version before repeal** (njt marks it `hatályát vesztette`).

**The ceiling, stated plainly:**

- **Hungarian statute almost never prescribes label wording.** It prescribes *data items* and, occasionally, a *rendering rule* (three-letter nationality code, `DD.MM.YY` order, "settlement name + country"). The driving licence is the single exception: 326/2011 Annex 5 does give Hungarian field names. Everywhere else, the printed caption is an administrative choice made by the document producer and is not in any instrument I could fetch.
- **No annex was an unreadable image.** All annexes of 414/2015, 146/1993 and 326/2011 render as text on njt. But 326/2011 Annex 5 contains a **stub**: it announces that a legend explaining the numbered items appears on the card and then prints only the word `Sorszám` where the legend's own wording should be (see §2.4). That is a gap in the *official consolidated text*, not in my fetch — `net.jogtar.hu` renders the same stub. So the licence legend's exact wording is **not** in the decree.
- **101/1998. (V. 22.) Korm. rendelet has no annex and no layout provision at all.** I fetched the whole decree and searched it; it mentions the passport's `aláírás rovata` (signature field) once and otherwise says nothing about the data page's captions, numbering or languages. The ticket named it as a route to the passport bracket numbers. It is not one.
- I did not attempt to read Magyar Közlöny's original typeset PDFs. Where the consolidated electronic text is incomplete (§2.4), that is where a future pass should go.

---

## 1. Passport — the bracketed field numbers (sub-question 1: **RESOLVED**)

### 1.1 The scheme those numbers belong to

The ticket asked to establish which numbering scheme the parenthesised digits belong to before asserting a value. They are **not ICAO's**.

ICAO Doc 9303-4 §4.1.1.1 numbers the VIZ **01–20** (Figure 4, "Sequence of data elements on front side of MRP data page"): `14 Date of issue`, `15 Authority or issuing office`, `16 Date of expiry`, `18 Holder's signature`, `19 Holder's portrait`. Read directly from [`9303_p4_cons_en.pdf`](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf). The Hungarian passport prints `Kiállítási dátum … (7)` and `Születési hely … (6)`. Those cannot be ICAO numbers.

They are the **EU uniform-passport scheme**, set by the Resolution of the Representatives of the Governments of the Member States meeting within the Council of 23 June 1981 (OJ C 241, 19.9.1981, p. 1), **Annex I, point E**, [CELEX 41981X0919](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:41981X0919). Quoting verbatim:

> "The laminated page and the conventional identification page will contain the same information, namely:
> 1. surname;
> 2. forename(s);
> 3. nationality;
> 4. date of birth;
> 5. sex;
> 6. place of birth;
> 7. date of issue;
> **8. date of expiry;**
> **9. authority;**
> **10. signature of holder.**
> This information will:
> — be given in the official language(s) of the State issuing the passport and in English and French,
> — be accompanied by numbers referring to an index stating the subject matter of such entries in the official languages of the Member States of the European Communities."

Annex I point **F** assigns 11–14 to a *following* page: `11. residence; 12. height; 13. colour of eyes; 14. extension of the passport.`

**The whole amendment chain was checked and none of it touches the numbering:**

| Instrument | CELEX | What it changes |
|---|---|---|
| 30 June 1982 supplementary resolution | [41982X0716](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:41982X0716) | format (ISO B7 + 2 mm), cover colour, security options, page layout freedom |
| 14 July 1986 supplementary resolution | [41986X0724](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:41986X0724) | adds Spanish and Portuguese to the index languages |
| 10 July 1995 supplementary resolution | [41995X0804](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:41995X0804) | "European Community" → "European Union"; adds Finnish and Swedish |
| 17 Oct 2000 supplementary resolution | [42000X1028](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:42000X1028) | minimum security requirements only |

The consolidated text [CELEX 01981X0919-19950710](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:01981X0919-19950710) ("1981Y0919 — EN — 10.07.1995 — 001.001") carries points E and F **unchanged**, item for item.

### 1.2 The answer

| Label (from PRADO §5) | Bracketed number | Bucket |
|---|---|---|
| `Érvényességi idő / Date of expiry / Date d'expiration` | **(8)** | sourced |
| `Kiállító hatóság / Authority / Autorité` | **(9)** | sourced |
| `Aláírás / Holder's signature / Signature du titulaire` | **(10)** | sourced |

**Independent corroboration, three ways.** (a) PRADO read 1, 2, 3, 4, 5, 6, 7 directly and all seven match the 1981 list exactly — surname 1, forename 2, nationality 3, DOB 4, sex 5, place of birth 6, date of issue 7. (b) `hungarian-passport-field-layout.md` §7.2 transcribed a 2006-era specimen at 4–6× zoom and read `Kiállítás kelte … (7)`, `Lejárat ideje … (8)`, `Kiállító hatóság … (9)`, `Aláírás … (10)` — a direct read of the three digits PRADO could not resolve, and it agrees with the Resolution. (c) The Resolution itself. Three independent lines converge; **8/9/10 can be printed.**

**Confidence caveat, honestly.** The 1981 instrument is a resolution of representatives of governments meeting within the Council — soft law, not a regulation or directive, and not transposed by any Hungarian instrument I could find. Hungary acceded in 2004 and adopted the model without a domestic re-enactment of the numbering. So the *legal* status of the number 8 on a Hungarian passport is "the published EU model says so"; the *evidential* status is "three independent reads agree". Both are strong; neither is a Hungarian decree.

### 1.3 The `(11)` on the birth-name field is a Hungarian deviation

The Hungarian data page prints `Születési név / Birth name / Nom à la naissance` with `(11)`. Under the 1981 scheme 11 is **residence**, and it belongs on a *following* page, not the data page (Annex I point F). Hungary has reused the number for a field the EU model does not define and ICAO does not name either (ICAO's nearest slot is Field 13, "optional personal data elements", 9303-4 §4.1.1.1).

The *data item* is statutory: **Utv. (1998. évi XII. törvény) 7. § (1) a)** — [njt](https://njt.jog.gov.hu/jogszabaly/1998-12-00-00) — "Az útlevél adatoldala tartalmazza … az állampolgár családi és utónevét, **születési családi és utónevét**, születési helyét, idejét, nemét, állampolgárságát, arcképmását és aláírását…". The *number* is not.

### 1.4 Passport resolution record

| Item | Bucket | Basis |
|---|---|---|
| Numbers (1)–(10) and their assignment | **sourced** | 1981 Resolution Annex I point E, CELEX 41981X0919 / 01981X0919-19950710. Agrees with PRADO on all seven PRADO could read. |
| Trilingual captions HU / EN / FR | **sourced** | Same, Annex I point E, third subparagraph: captions "in the official language(s) of the State issuing the passport and in English and French". Agrees with PRADO. ICAO 9303-3 §3.3 requires only national + **one** of EN/FR/ES; the EU model is the stricter rule and is the one the card follows. |
| `/` as the caption separator | **sourced** | ICAO 9303-3 §3.3: "the printed caption shall be followed by an oblique character (/) and the equivalent of the caption in English, French or Spanish". Agrees with PRADO. |
| Which fields carry a caption at all | **sourced** | ICAO 9303-3 §3.3: "Captions shall be used to identify all fields for mandatory data elements in the VIZ"; 9303-4 note (l) "The field caption shall be printed on the document", note (d) "The field caption is not printed on the document" for the fields so marked. |
| The data-page field *set* | **sourced** | Utv. 7. § (1) a)–c). Matches PRADO. |
| Number **(11)** for birth name | **unsourced** | Contradicts the 1981 scheme, which assigns 11 to residence on another page. Only PRADO and the 2006 specimen support it. |
| Hungarian caption wording (`Családi név`, `Utónév(-ek)`, `Útlevélszám`, `Kiállítási dátum`, `Érvényességi idő`, `Kiállító hatóság`, `Aláírás`, `Típus`, `Kód`) | **unsourced** | 101/1998 fetched in full: no layout provision, no annex. Utv. names the data items, never the caption. Use PRADO's transcription. |
| Caption *wording drift over time* | **unsourced** | The 2006 specimen prints `Kiállítás kelte` / `Lejárat ideje`; the 2012 PRADO specimen prints `Kiállítási dátum` / `Érvényességi idő`. Both are the same numbered fields (7) and (8). No instrument governs which. A renderer must pick a generation. |

---

## 2. Driving licence — cross-validation (sub-question 2: **RESOLVED, with three conflicts**)

### 2.1 What the Directive actually mandates

Directive 2006/126/EC, consolidated text `02006L0126 — EN — 22.07.2018 — 010.001`, [CELEX 02006L0126-20180722](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02006L0126-20180722), Annex I point 3.

- **The numbering is mandated.** Point 3(d): "information specific to the licence issued, **numbered as follows**: 1. surname of the holder; 2. other name(s) of the holder; 3. date and place of birth; 4. (a) date of issue … (b) date of expiry … (c) the name of the issuing authority (may be printed on page 2); (d) a different number from the one under heading 5, for administrative purposes (optional); 5. number of the licence; 6. photograph of the holder; 7. signature of the holder; **8. permanent place of residence, or postal address (optional)**; 9. category of vehicle(s)…". Page 2 carries 9, 10, 11, 12, 13, 14.
- **A legend is mandated, but only its *scope*, never its *wording*.** Point 3(b) (as amended by M2, Directive 2011/94/EU): "**an explanation of the following numbered items which appear on pages 1 and 2 of the licence: 1, 2, 3, 4(a), 4(b), 4(c), 5, 10, 11 and 12**". That is the whole of it. The Directive nowhere says what words the explanation uses.
- **A Hungarian-only legend is permitted.** Point 3(b), second subparagraph (M4): "If a Member State wishes to make the entries in a national language **other than one of the following languages**: Bulgarian, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, **Hungarian**, Italian, … it will draw up a bilingual version of the licence…". Hungarian is on the list, so **no second language is required**. This directly sources PRADO's finding that the licence legend is monolingual Hungarian while every other document here is bilingual or trilingual.
- **Date format on page 2 is mandated.** Items 10 and 11: "each field of the date shall be written with two digits and in the following sequence: **day.month.year (DD.MM.YY)**". **This agrees with PRADO's verso reading (`12.06.95`, `30.11.17.`) and says nothing about the recto**, which PRADO found prints `YYYY.MM.DD.` — so convention 9 of [#46](https://github.com/akosgintl/document-intelligence/issues/46) is now corrected from two directions, not one.
- Point 3(a): "the words 'Driving Licence' printed in large type **in the language or languages of the Member State issuing the licence**" — sources `VEZETŐI ENGEDÉLY`. Point 3(e) lists `Vezetői engedély` among the pink background renderings.

### 2.2 What the Hungarian decree adds — 326/2011 Annex 5

[326/2011. (XII. 28.) Korm. rendelet](https://njt.jog.gov.hu/jogszabaly/2011-326-20-22), **5. melléklet**, is the one place in Hungarian law that gives actual field-name wording. It is generation-sliced:

- **A.** licences issued up to 31 Dec 2000 (booklet form)
- **B.** card licences introduced 1 Jan 2001
- **C.** card licences issued after 19 April 2005 (per Directive 91/439/EEC as amended by 96/47/EC) — **governs `HUN-FO-03001`, first issued 01/03/2012**
- **D.** card licences issued after 19 January 2013 (per Directives 2006/126/EC and 2011/94/EU) — **governs `HUN-FO-04001`**

Parts C and D give the *identical* Hungarian wording for items 1–7; they diverge on 10–12.

### 2.3 Cross-validation against PRADO's two legends

PRADO's §4 table showed the two generations word the legend differently from each other. The decree explains why only for the older one.

**`HUN-FO-03001` (2012) vs Annex 5 Part C — near-total agreement:**

| No. | Annex 5 Part C (verbatim) | PRADO `HUN-FO-03001` | Verdict |
|---|---|---|---|
| 1 | `Családi név` | `Családi név` | **agree** |
| 2 | `Utónév` | `Utónév` | **agree** |
| 3 | `Születési hely, születési idő` | `Születési idő, Születési hely` | **order reversed on the card** |
| 4a | `Kibocsátási dátum` | `Kibocsátási dátum` | **agree** |
| 4b | `Érvényességi idő` | `Érvényességi idő` | **agree** |
| 4c | `Kibocsátó hatóság` | `Kibocsátó hatóság` | **agree** |
| 5 | `Sorszám` | `Sorszám` | **agree** |
| 10 | `Vizsga időpontja` | `Vizsga időpontja` | **agree** |
| 11 | `Kategória érvényessége` | `Kategória érvényessége` | **agree** |
| 12 | `Korlátozás kódja` | `Korlátozások kódja` | **card is plural** |

Eight exact, two near. On item 3 the card follows the *Directive's* order ("date and place of birth"), the decree reverses it.

**`HUN-FO-04001` (2013) vs Annex 5 Part D — near-total disagreement:**

| No. | Annex 5 Part D (verbatim) | PRADO `HUN-FO-04001` | Verdict |
|---|---|---|---|
| 1 | `Családi név` | `Családi név` | **agree** |
| 2 | `Utónév` | `Utónév` | **agree** |
| 3 | `Születési hely, születési idő` | `Születési idő és hely` | conflict |
| 4a | `Kibocsátási dátum` | `A kiállítás időpontja` | conflict |
| 4b | `Érvényességi idő` | `A lejárat időpontja` | conflict |
| 4c | `Kibocsátó hatóság` | `Kiállító hatóság` | conflict |
| 5 | `Sorszám` | `Az engedély száma` | conflict |
| 10 | *(descriptive prose, no label:* `az adott kategóriára vonatkozó engedély első kiadásának időpontja`*)* | `Érvényesség kezdete` | conflict |
| 11 | *(descriptive prose:* `az adott kategóriára vonatkozó engedély lejáratának időpontja`*)* | `Érvényesség vége` | conflict |
| 12 | `korlátozás kódja` | `Kódok` | conflict |

**This is the headline for sub-question 2.** Part D was written by copying Part C's wording forward for items 1–5 and replacing 10–12 with prose. The card issued from 19 Jan 2013 ignores it: its legend reads like a fresh translation of the Directive's English ("date of issue of the licence" → `A kiállítás időpontja`; "number of the licence" → `Az engedély száma`; "date of first issue of each category" → `Érvényesség kezdete`). **The decree and the current card do not agree, and the decree is the one that is out of date.** A renderer targeting the current card should use PRADO's wording, not the decree's; a renderer targeting the 2012 card can use either.

### 2.4 The legend-wording stub in Annex 5

Every one of Parts B, C and D ends with this italic line and then breaks off:

> "*Az első és a második oldalon megjelenő – az 1., 2., 3., 4. a), 4. b), 4. c), 5., 10., 11. és 12. számok magyarázata*
> *Sorszám*"

("Explanation of the numbers 1, 2, 3, 4a, 4b, 4c, 5, 10, 11 and 12 appearing on the first and second page" / "Serial number".) That is a faithful transposition of Directive Annex I point 3(b) — and then nothing. The legend's own wording is not reproduced. `net.jogtar.hu`'s rendering of the same annex is identical, so this is a gap in the official consolidated text rather than a fetch artefact; the original Magyar Közlöny typesetting (Annex 5 was established by 228/2012. (VIII. 23.) Korm. r. 7. § (17) and 5/2013. (I. 16.) Korm. r. 21. § (1), last amended by 425/2024. (XII. 23.) Korm. r. 17. § (1)) may carry a table the consolidation dropped. **Not checked** — that is the one place a future pass should go.

In Part D only, one further italic line follows:

> "*állampolgárság adat (többes állampolgárság esetén csak a magyar állampolgárság feltüntetése), születési név adat (ha eltér a viselt névtől)*"

### 2.5 The `nationality` conflict from #42 — resolved in the decree's favour

[#42](https://github.com/akosgintl/document-intelligence/issues/42) found 326/2011 conflicting with the European Commission's HU4 legend on `nationality`. The picture is now complete:

- The **Directive** defines no nationality heading at all. Its item 14 is "a space reserved for the possible entry by the Member State which issues the licence of information essential for administering the licence or related to road safety (optional). **If the information relates to one of the headings defined in this Annex, it should be preceded by the number of the heading in question.**"
- The **decree** puts nationality and birth name there — Annex 5 Part D's closing line (§2.4 above) — and 326/2011 **28. §** requires the country-code form: "A vezetői engedélybe az állampolgársági adatot az országkód … formájában kell feltüntetni".
- **PRADO** shows exactly that on the verso of both generations: `14. Államp:` valued `HUN`, plus `Sz.neve:` carrying the holder's birth name.

**Decree and card agree. The EC HU4 legend, which lists only 1–12, is the incomplete source.** #42's "conflict" was the Commission page omitting a field, not the decree inventing one.

The printed abbreviations `Államp:` and `Sz.neve:` are *not* in the decree — it names the data items (`állampolgárság adat`, `születési név adat`) and nothing more. Those two captions are **inferred**: the data items are statutory, the abbreviated wording is PRADO-only.

### 2.6 Two more conflicts, both about heading 8

**(a) The decree misnumbers the category field on page 1 of the current card.** Annex 5 Part C page 1 correctly reads `9. Érvényességi kategóriák`. Part D page 1 reads `8. [Érvényességi kategóriák (a nemzeti kategóriák másképpen nyomtatandók, mint a harmonizált kategóriák)]` — while Part D page 2 then reads `9. [Érvényességi kategóriák …]` again. Under the Directive, 8 is permanent place of residence and 9 is categories. Part D's "8." on page 1 is a drafting slip in the Hungarian text.

**(b) `hungarian-driving-licence-field-layout.md` §2 is wrong that Hungary prints field 8.** It relied on the EC HU4 legend listing "8 Permanent place of residence" and concluded "Field 8 (address) should be modeled as present (not optional) for the Hungarian card specifically". Both other sources contradict it: the decree's Annex 5 never allocates 8 to residence in any generation, and PRADO found no field 8 on either specimen (`hungarian-document-printed-labels.md` §4 lists the recto numbers as `1.`, `2.`, `3.`, `4(a)`, `4(b)`, `4(c)`, `5.`, `7.`, `9.`). **Two primary sources against one Commission summary page.** Presented, not silently decided — but a renderer should not print a field 8.

### 2.7 Licence resolution record

| Item | Bucket | Basis |
|---|---|---|
| The numbering 1–14 and what each number means | **sourced** | Directive 2006/126/EC Annex I point 3(d) and the page-2 list. Agrees with PRADO. |
| Which numbers get a legend entry (1, 2, 3, 4a, 4b, 4c, 5, 10, 11, 12) | **sourced** | Annex I point 3(b). Agrees with PRADO — "Neither legend lists 6, 7, 8, 13 or 14". |
| Legend may be Hungarian-only | **sourced** | Annex I point 3(b) second subpara. Agrees with PRADO. |
| `VEZETŐI ENGEDÉLY` title, `MAGYARORSZÁG`, `H` in a blue rectangle with 12 stars | **sourced** | Annex I point 3(a),(c); 326/2011 Annex 5 Part D §2, verbatim. |
| Legend wording for the **2012** card (items 1–5, 10–12) | **sourced** | 326/2011 Annex 5 Part C. Agrees with PRADO on 8 of 10; differs on item 3's order and item 12's plural. |
| Legend wording for the **2013/current** card | **conflict — statute superseded in practice** | 326/2011 Annex 5 Part D gives wording that the card does not use for 8 of 10 items. Both texts given in §2.3; not reconciled here. |
| `DD.MM.YY` on verso items 10, 11 | **sourced** | Annex I point 3(d), items 10 and 11. Agrees with PRADO. |
| `YYYY.MM.DD.` on recto items 3, 4a, 4b | **unsourced** | Neither the Directive nor Annex 5 specifies a format for items 3, 4(a), 4(b). PRADO-only. |
| Field 14 carries nationality (country code) and birth name | **sourced** | 326/2011 Annex 5 Part D closing line + 28. §; Directive Annex I item 14. Agrees with PRADO. |
| Captions `Államp:` and `Sz.neve:` | **inferred** | Data items statutory; abbreviated wording PRADO-only. |
| Legend orientation (horizontal 2012 / rotated 90° 2013), position on the verso panel | **unsourced** | No instrument addresses placement of the legend. |
| Field 8 (address) | **conflict** | Decree silent, PRADO absent, EC HU4 page says present. See §2.6(b). |

---

## 3. Identity card — 414/2015 and its predecessor (ticket's original scope)

### 3.1 The eID card (2016+, `HUN-BO-05001` / `HUN-BO-06001`)

**[414/2015. (XII. 23.) Korm. rendelet](https://njt.jog.gov.hu/jogszabaly/2015-414-20-22) has no card-layout annex.** Its three annexes are: 1. the *application*'s data content (28 items); 2. the list of secondary cards attachable to the eID; 3. an unrelated schedule. The nearest thing to a layout provision is **33. §**, whose own heading is "*A személyazonosító igazolvány adatainak bejegyzésére és külső megjelenítésére vonatkozó egyes szabályok*" — "certain rules on the entry and **external display** of the ID card's data". Read in full, it prescribes four rendering rules and **zero label captions**:

| 414/2015 § | Verbatim | What it fixes |
|---|---|---|
| 33. § (1) | "A nemzetiséghez tartozó polgár kérelmére családi és utónevét a személyazonosító igazolványba az anyakönyvbe bejegyzett **mindkét nyelven** be kell jegyezni." | minority name → see §5 |
| 33. § (3a) | "Származási helyként magyarországi település esetén a település elnevezése és **Magyarország**, külföldi település esetén a település elnevezése és az **ország ISO-kódja** kerül megjelenítésre." | rendering of *place of origin* |
| 33. § (4) | "…állampolgársági adatát a személyazonosító igazolványban – az országnevek kódjaira vonatkozó nemzeti szabvány alkalmazásával – **háromjegyű betűkód** formájában kell feltüntetni." | nationality as `HUN` |
| 33. § (5) | "…gépi olvasásra alkalmas adatsora az **ICAO 9303** számú dokumentum előírásai alapján épül fel." | MRZ |

33. § (3a) is worth noticing: it is the only place Hungarian statute prescribes a "settlement + country" print format, and it applies to `származási hely` (place of origin), **not** to `születési hely`. PRADO observed `DEBRECEN (MAGYARORSZÁG)` in the *place of birth* field. The parenthesised country there is **unsourced** — the register rule for birthplace, 146/1993 **15/B. §**, adds a country name only for births **abroad**: "Külföldön történt születés … esetén a nyilvántartás a helység hivatalos elnevezésén kívül az ország magyar nyelvű megnevezését is tartalmazza."

The printed *field set* is statutory, and in a fixed order — **Nytv. 29. § (2)**, [njt](https://njt.jog.gov.hu/jogszabaly/1992-66-00-00): "A személyazonosító igazolvány **vizuálisan észlelhető módon** tartalmazza a) a polgár nevét, b) a polgár születési helyét, c) a polgár születési idejét, d) a polgár állampolgárságát, e) a polgár anyja nevét, f) a polgár nemét, g) a polgár arcképmását, h) a polgár aláírását…, i) … érvényességi idejét, j) … okmányazonosítóját, k) … kiállításának idejét, l) … kiállító hatóság nevét, m) [travel restriction]". Nytv. 29. § (2a) adds `származási hely` **on request**.

**One real gap.** Nytv. 29. § (2) does **not** list birth name among the visually perceptible data. Yet every ID-card generation PRADO captured prints it (`Leánykori név` → `Születési név` → `Születési családi és utónév`). `Születési családi és utóneve(i)` appears only in 414/2015 Annex 1 as **application** data. So the birth-name field's presence on the ID card face has no statutory basis I could locate. (Contrast the passport, where Utv. 7. § (1) a) does name it.)

The bilingual document title is sourced, but from EU law rather than Hungarian: **Regulation (EU) 2019/1157 Art. 3(3)**, [CELEX 32019R1157](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R1157) — "The document shall bear the title 'Identity card' or another well-established national designation in the official language or languages of the issuing Member State, **and the words 'Identity card' in at least one other official language** of the institutions of the Union." That sources `SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY / IDENTITY CARD` as a *pattern*, not as wording; Art. 3(4) sources the blue-rectangle country code. Art. 3(2) delegates data elements to **ICAO 9303 Part 5** — whose TD1 directory numbers fields 01–14 (`9303_p5_cons_en.pdf`, Figure 5), a scheme the Hungarian eID prints **no trace of**: it is label-only, with no field numbers anywhere.

### 3.2 The pre-2016 laminated card — 168/1999 verified

The ticket asked to verify rather than trust the reference. **Verified.** [168/1999. (XI. 24.) Korm. rendelet](https://njt.jog.gov.hu/jogszabaly/1999-168-20-22) is the pre-2016 ID-card decree; njt's last consolidation is 2015.08.01 and the instrument is marked `hatályát vesztette`. Relevant provisions, verbatim:

- **7. § (1)**: "Az állandó személyazonosító igazolvány az Nytv. 29. § (2) bekezdésében meghatározott személy- és okmányazonosító adatokon kívül tartalmazza a személyazonosító igazolvány kiállításának keltét, a kiadó állam kódját és a kiállító hatóság nevét."
- **7. § (2)**: nationality as a three-letter code — the same rule 414/2015 § 33(4) later restates.
- **7. § (3)**: "…az (1) és (2) bekezdésben meghatározott adatokat **gépi olvasásra alkalmas adatsor formájában is** tartalmazza." (The MRZ predates 2016 — already established in `hungarian-id-card-field-layout.md` §4.)
- **8. §**: base colour blue for citizens, yellow for immigrants/settled/refugee/protected persons. **This confirms PRADO's finding that `HUN-HO-09xxx` is the same design in a different colour scheme**, and that the colour difference is statutory, not cosmetic.
- **30. § (1)**: "A személyazonosító igazolványba azt a családi és utónevet kell bejegyezni, amely a kérelmezőt az anyakönyvi bejegyzése szerint megilleti."
- **30. § (2)**: minority name in both languages — the predecessor of 414/2015 § 33(1).

**No label wording anywhere, and no annex describing the card face.** The `Sorszám:` → `Okmányazonosító:` change PRADO observed between the 2000 and 2012 generations tracks a change in the *statutory term* — Nytv. 5. § (12) defines "*Okmányazonosító: a személyi azonosítót és lakcímet igazoló hatósági igazolvány, illetőleg a személyazonosító igazolvány azonosítására alkalmazott jel*" — but no instrument says the card must print that word.

### 3.3 ID card resolution record

| Item | Bucket | Basis |
|---|---|---|
| Printed field set and its order | **sourced** | Nytv. 29. § (2) a)–m). Agrees with PRADO on every field except birth name. |
| Nationality printed as `HUN` (3-letter code) | **sourced** | 414/2015 § 33(4); 168/1999 § 7(2). Agrees with PRADO (`HUN`, `MAGYAR/HUN`). |
| Bilingual document title (national + one other EU language) | **sourced** | Reg. (EU) 2019/1157 Art. 3(3). Agrees with PRADO's `SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY / IDENTITY CARD`. Wording of the pairing itself is not prescribed. |
| MRZ per ICAO 9303 | **sourced** | 414/2015 § 33(5); 168/1999 § 7(3); Reg. 2019/1157 Art. 3(1). Agrees with PRADO's 3-line TD1. |
| Card colour blue (citizen) / yellow (non-citizen) | **sourced** | 168/1999 § 8(1)–(2). Agrees with PRADO's note on `HUN-HO-09xxx`. |
| `származási hely` rendered as "settlement + Magyarország" / "settlement + ISO code" | **sourced** | 414/2015 § 33(3a). **PRADO saw no such field on any captured specimen** — it is request-only (Nytv. 29. § (2a)). Not contradicted; simply absent from the sample. |
| CAN as a 6-digit code | **inferred** | ICAO 9303-4 §4.1.1.2 defines a 6-digit CAN and says it "should include a field caption"; Nytv. 29. § (5) requires the access code on the card. Neither prescribes the caption `CAN:` or its lack of translation. |
| Every Hungarian caption on the card face — `Családi és utónév/…`, `Nem/Sex`, `Születési idő/…`, `Érvényességi idő/…`, `Okmányazonosító/Doc. No.`, `Születési hely/…`, `Anyja születési neve/…`, `Kiállító hatóság/…` | **unsourced** | No Hungarian instrument prescribes caption wording for the ID card. PRADO is the only source. |
| Birth-name field on the card face at all | **unsourced** | Not in Nytv. 29. § (2). Appears only as application data (414/2015 Annex 1 item 3). Printed on all three generations per PRADO. |
| `(MAGYARORSZÁG)` after a Hungarian city in `Születési hely` | **unsourced** | 146/1993 15/B. § adds a country name only for births abroad. |
| Label drift across generations (`Leánykori név` → `Születési név` → `Születési családi és utónév`; `Neme` → `Nem`) | **unsourced** | No instrument tracks it. PRADO §2 is the only record. |
| Unlabelled issue date, vertical repeat of the document number | **unsourced** | Data items statutory (Nytv. 29. § (2) k), j)); their unlabelled/vertical presentation is not. |

---

## 4. Address card — the `természetes személyazonosító adatai` expansion (sub-question 3: **RESOLVED**)

### 4.1 The chain

**Nytv. 13. § (2)**: "A személyi azonosítót és lakcímet igazoló hatósági igazolvány tartalmazza a polgár **természetes személyazonosító adatait**, lakcímét …, személyi azonosítóját, az okmány azonosítóját, valamint tájékoztatás céljából a 14. életévét be nem töltött kiskorú esetén – a törvényes képviselő kérelemére – a kiskorú törvényes képviselőinek nevét és a kiállítás időpontja szerinti telefonszámát."

**146/1993. (X. 26.) Korm. rendelet 16. § (2)**, [njt](https://njt.jog.gov.hu/jogszabaly/1993-146-20-22): "A hatósági igazolvány az Nytv. 13. § (2) bekezdésében meghatározott adatokon kívül tartalmazza a hatósági igazolvány **okmányazonosítóját, kiállításának keltét és a kiállító hatóság megnevezését**." — and **16. § (3)**: "A hatósági igazolvány a személyi azonosítót gépi olvasásra alkalmas **vonalkód** formájában is tartalmazza."

**The collective term is defined — but not in the Nytv.** I searched the whole Nytv.: it uses `természetes személyazonosító adat` a dozen times and never defines it. The definition is in **1996. évi XX. törvény a személyazonosító jel helyébe lépő azonosítási módokról és az azonosító kódok használatáról, 4. § (4)**, [njt](https://njt.jog.gov.hu/jogszabaly/1996-20-00-00), verbatim:

> "**Természetes személyazonosító adat** a polgár
> a) családi és utóneve, születési családi és utóneve,
> b) születési helye,
> c) születési ideje és
> d) anyja születési családi és utóneve."

### 4.2 The expansion mapped onto the printed labels

| Statutory item (1996. évi XX. tv. 4. § (4)) | Printed label (PRADO §3) | Match |
|---|---|---|
| `családi és utóneve` | `Családi és utónév:` | **exact**, minus the possessive suffix |
| `születési családi és utóneve` | `Születési név:` | **shortened on the card** |
| `születési helye` + `születési ideje` (**two items**) | `Születési hely,idő:` (**one label, two values**) | **merged on the card** |
| `anyja születési családi és utóneve` | `Anyja neve:` | **shortened on the card — but legally equivalent** |

The last row is the elegant one: **Nytv. 5. § (14)** defines "*A polgár anyja neve: a polgár anyja születési családi és utóneve*". So the card's four-character shortening is not a loss of precision; it is the statutory synonym.

The address fields come out of the same act. **Nytv. 5. § (2)**: "*A polgár lakóhelye: annak a lakásnak vagy szállásnak … a címe, amely a polgár állammal … való hivatalos kapcsolattartása … megalapozásául szolgál.*" **5. § (3)**: "*A polgár tartózkodási helye: annak a lakásnak a címe, ahol a polgár – a lakóhely-változtatás szándéka nélkül – három hónapnál hosszabb ideig tartózkodik.*" **5. § (4)**: "*A polgár lakcím adata: bejelentett lakóhelyének, illetve tartózkodási helyének címe (a továbbiakban együtt: lakcím).*" The card's `Lakóhely:` and `Tartózkodási hely:` are the statutory terms verbatim, and `lakcím` in Nytv. 13. § (2) is exactly the union of the two — which is *why* the card has two address rows rather than one.

### 4.3 The two document titles

PRADO found the recto and verso carry **different** titles. Both are statutory phrases, and the split is deliberate:

- Verso `SZEMÉLYI AZONOSÍTÓT IGAZOLÓ HATÓSÁGI IGAZOLVÁNY` ← **Nytv. 13. § (4)**: "*A **személyi azonosítót igazoló hatósági igazolvány**t úgy kell kiállítani, hogy abból az érintett polgár személyi azonosítója és lakcím adata egyidejűleg ne váljon megismerhetővé.*"
- Recto `LAKCÍMET IGAZOLÓ HATÓSÁGI IGAZOLVÁNY` ← the same phrase used by Nytv. 26. § and by Pmt. (2017. évi LIII. tv.) 7. § (3).
- The instrument as a whole is `a személyi azonosítót és lakcímet igazoló hatósági igazolvány` (Nytv. 13. § (2)).

**The two-title design is the physical implementation of Nytv. 13. § (4)** — the identifier and the address must not be simultaneously knowable, so each face is titled for the one thing it certifies. That is a sourced explanation for a layout fact PRADO could only observe.

### 4.4 Address card resolution record

| Item | Bucket | Basis |
|---|---|---|
| `Családi és utónév:` | **sourced (near-verbatim)** | 1996. évi XX. tv. 4. § (4) a) via Nytv. 13. § (2). Agrees with PRADO. |
| `Születési név:` | **inferred** | Statute says `születési családi és utóneve`; the card shortens it. Same data item. |
| `Születési hely,idő:` | **inferred** | Statute has two separate items; the card merges them into one caption. The missing space after the comma is PRADO-only. |
| `Anyja neve:` | **sourced** | Nytv. 5. § (14) makes `anyja neve` the statutory synonym of `anyja születési családi és utóneve`. Agrees with PRADO. |
| `Lakóhely:` / `Tartózkodási hely:` | **sourced (verbatim terms)** | Nytv. 5. § (2)–(4) + 13. § (2). Agrees with PRADO, and explains why there are two rows. |
| `Személyi azonosító:` | **sourced (verbatim term)** | Nytv. 13. § (2), 5. § (11). Agrees with PRADO. |
| `Kiállító hatóság:` | **sourced** | 146/1993 16. § (2) `a kiállító hatóság megnevezése`. |
| Issue date printed (unlabelled, bottom right) | **sourced as a data item, unsourced as presentation** | 146/1993 16. § (2) `kiállításának kelte`. Statute does not say it is unlabelled. |
| 1-D barcode on the verso encoding the personal identifier | **sourced** | 146/1993 16. § (3), verbatim. Agrees with PRADO. |
| Two document titles, one per face | **sourced** | Nytv. 13. § (4) + 13. § (2). Explains PRADO's observation. |
| Monolingual Hungarian, no English | **inferred** | No EU instrument applies: the address card is not an identity card under Reg. 2019/1157 and not a travel document under ICAO. Nothing requires a second language. Consistent with PRADO. |
| `Bejelentési idő:` (twice) | **unsourced** | Neither Nytv. 13. § (2) nor 146/1993 16. § (2) lists the registration date among the card's contents. `a bejelentés időpontja` exists as a registry item (Nytv. 26. § (1) g)) but nothing requires it on the card, and nothing prescribes repeating the caption. |
| `Érvényességi ideje:` | **unsourced** | The card has no statutory expiry — `hungarian-other-id-documents.md` §1a records it as open-ended — yet PRADO saw the caption. Not in Nytv. 13. § (2) or 146/1993 16. § (2). |
| `Külföldi cím` as a value in `Lakóhely` | **inferred** | Nytv. 13. § (2a): for a citizen living abroad the card "certifies that the person has no Hungarian residence". The specific words printed are PRADO-only. |
| Personal identifier printed hyphen-grouped `2-720216-1673` | **unsourced** | 1996. évi XX. tv. Annex 3 governs how the number is *formed*, not how it is *typeset*. |
| Document number `000102 YL` printed unlabelled beside the title | **unsourced** | `okmányazonosító` is statutory (Nytv. 13. § (2), 5. § (12)); its unlabelled placement is not. |

---

## 5. The minority-language name (sub-question 4: **RESOLVED — no label is prescribed, and none should exist**)

Three instruments converge, and all three point the same way: the minority-language name is not a separate field. It is **the same name field, written in both languages**.

- **2011. évi CLXXIX. törvény a nemzetiségek jogairól, 16. §**, [njt](https://njt.jog.gov.hu/jogszabaly/2011-179-00-00):
  - (1) "A nemzetiséghez tartozó személynek joga, hogy anyanyelvén használja a családi és utónevét, és joga van családi és utónevének hivatalos elismeréséhez."
  - (3) "Kérésre **a személyazonosító igazolvány a nemzetiséghez tartozó személy nevét – az anyakönyvi bejegyzésben foglaltnak megfelelően – nemzetisége nyelvén is tartalmazza.** Jogszabály lehetővé teheti, hogy más hatósági igazolvány a nemzetiséghez tartozó személy nevét … nemzetisége nyelvén is tartalmazza."
- **414/2015. (XII. 23.) Korm. rendelet 33. § (1)**: "A nemzetiséghez tartozó polgár kérelmére **családi és utónevét a személyazonosító igazolványba az anyakönyvbe bejegyzett mindkét nyelven be kell jegyezni.**" — the predecessor rule, 168/1999 **30. § (2)**, is word-for-word the same.
- The passport has the same mechanism: **Utv. 7. § (7a)** (inserted by 2021. évi L. tv. 11. § (2)): "Kérelemre a magánútlevél a nemzetiséghez tartozó személy nevét – az anyakönyvi bejegyzésben foglaltnak megfelelően – nemzetisége nyelvén is tartalmazza." 101/1998 **19. § (2b)** carries the corresponding application rule.

**Answer to the ticket's question: no label is prescribed, because no separate field exists.** The statutory construction is `családi és utónevét … mindkét nyelven` — one field, two renderings. This *agrees* with PRADO's observation on `HUN-BO-05004` that "no distinct label was visible": there was nothing to see because there is nothing to label.

| Item | Bucket | Basis |
|---|---|---|
| Minority-language name is entered into the `családi és utónév` field, in both languages, on request | **sourced** | 2011. évi CLXXIX. tv. 16. § (3); 414/2015 § 33(1); 168/1999 § 30(2); Utv. 7. § (7a). Consistent with PRADO. |
| A distinct label for it | **sourced as absent** | No instrument prescribes one. |
| Its **position** — PRADO's index says the second rendering appears on the **verso** of `HUN-BO-05004`, while the primary name field is on the recto | **unsourced** | No instrument says where the second-language rendering is printed. A renderer needing this case must decide; nothing in law constrains it. |

---

## Conflicts, presented rather than resolved

| # | Subject | Statute says | PRADO / EC says | Note |
|---|---|---|---|---|
| 1 | Licence legend wording, current card | 326/2011 Annex 5 Part D: `Kibocsátási dátum`, `Érvényességi idő`, `Kibocsátó hatóság`, `Sorszám`, `Születési hely, születési idő` | `A kiállítás időpontja`, `A lejárat időpontja`, `Kiállító hatóság`, `Az engedély száma`, `Születési idő és hely` | 8 of 10 items differ. The card is real; the decree is stale. |
| 2 | Licence item 3 order | decree: place then date | both card generations: date then place | The cards follow the Directive; the decree reverses it. |
| 3 | Licence item 12 caption | decree: `Korlátozás kódja` (singular) | 2012 card: `Korlátozások kódja` (plural); 2013 card: `Kódok` | |
| 4 | Licence field 8 | 326/2011 Annex 5: never allocates 8 to residence; Part D even misprints category as "8." on page 1 | PRADO: no field 8 printed. **EC HU4 legend: "8 Permanent place of residence"** | Two primary sources against one Commission summary. Corrects `hungarian-driving-licence-field-layout.md` §2. |
| 5 | Licence nationality | 326/2011 Annex 5 Part D + 28. §: field 14 carries nationality as a country code | PRADO: `14. Államp:` = `HUN`. **EC HU4 legend: no nationality at all** | #42's conflict, resolved: decree and card agree; the EC page is incomplete. |
| 6 | ID card birth name | Nytv. 29. § (2) does **not** list it among visually perceptible data | all three PRADO generations print it | Statute appears to under-describe the card. |
| 7 | ID card place of birth | 146/1993 15/B. §: country name added only for births **abroad** | `DEBRECEN (MAGYARORSZÁG)` — country in parentheses for a Hungarian city | The card is more verbose than the register rule. |
| 8 | Passport birth-name number | 1981 Resolution: 11 = residence, on a following page | `(11)` on the data page for `Születési név` | Hungarian reuse of an EU-assigned number. |

---

## What could not be sourced

The honest residue. These are what the renderer must decide about explicitly, because no primary source constrains them:

1. **Every Hungarian caption on the passport, the ID card and (for the current generation) the driving licence.** Hungarian statute prescribes data items and rendering rules, never caption wording, with the sole exception of 326/2011 Annex 5 — which is generation-stale. PRADO remains the only source for what the documents actually print.
2. **The licence legend's own wording as an official text.** 326/2011 Annex 5 announces the legend and then prints only the stub `Sorszám` where the legend should be, in all of Parts B, C and D. `net.jogtar.hu` shows the same stub, so this is a gap in the official consolidated text. **Not checked:** the original Magyar Közlöny typesetting of 228/2012. (VIII. 23.) Korm. r. 7. § (17), 5/2013. (I. 16.) Korm. r. 21. § (1), and 425/2024. (XII. 23.) Korm. r. 17. § (1), which may carry a table the consolidation dropped.
3. **Physical placement of anything.** No instrument in this research says which face a field sits on, whether it is labelled or bare, whether the legend runs horizontally or rotated, or where the minority-language name rendering goes. The only exceptions are structural: Nytv. 13. § (4) (address card, identifier and address must not be simultaneously visible → the two-title design), Directive 2006/126/EC Annex I item 4(c) ("may be printed on page 2"), and ICAO 9303-4 §3.2.1 (signature may relocate to Zone VI).
4. **Date formats other than the licence's verso.** Only Directive Annex I items 10 and 11 (`DD.MM.YY`) are statutory. The passport's `DD MMM/MMM YY`, the ID card's three coexisting formats, the address card's `YYYY.MM.DD` and the licence's recto `YYYY.MM.DD.` have no legal source; PRADO's §"Date formats" table remains the only record.
5. **Sex value forms.** ICAO 9303-4 Field 11 mandates "a single national initial, followed by an oblique and the capital letter F for female, M for male, or X for unspecified" — which sources `N/F` and `F/M`. It does **not** source the full-word `NŐ/F` and `FÉRFI/M` that PRADO found on cards of the same era. Statute is silent; both forms are in circulation.
6. **Authority value strings** (`KEK KH`, `BELÜGYMINISZTÉRIUM`, `NYILVÁNTARTÓ HIVATAL`, `OKMÁNYIRODA, BM KÖZPONTI HIVATAL`). Statute requires "the name of the issuing authority" (Nytv. 29. § (2) l), 146/1993 16. § (2), Utv. 7. § (1) b)) and never fixes the string or its abbreviation. 146/1993 **16/A. §** is the one near-exception: it provides that where the registry body issues the address card, the issuer is the Government of Hungary, abbreviated **`MK`** on the document — a string PRADO did not observe.
7. **Document-number character formats.** 1996. évi XX. tv. Annex 3 governs how the *personal identifier* is formed. Nothing governs the `okmányazonosító`'s 6-digits-plus-2-letters shape, the passport's 2-letters-plus-7-digits, or the licence's 2-letters-plus-6-digits.
8. **The address card's `Bejelentési idő:` and `Érvényességi ideje:` captions.** Neither datum is among the card's statutory contents. The card prints both; the second is odd given the card has no statutory expiry.
