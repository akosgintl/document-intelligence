# Hungarian identity documents: the printed field labels

Transcribed 2026-08-01 from PRADO specimen images, resolving [#47](https://github.com/akosgintl/document-intelligence/issues/47).

## Why this file exists

The five Document Type schemas ([#40](https://github.com/akosgintl/document-intelligence/issues/40)–[#45](https://github.com/akosgintl/document-intelligence/issues/45)) deliberately used *semantic descriptions* rather than quoted label text, because PRADO 403'd throughout that research and ADR-0007 would have frozen a guessed label into v1. A renderer has no such escape — it must print something. This file records what the documents actually print.

**Scope: label wording and layout only.** Sections 1–5 were transcribed 2026-08-01 and cover **wording**; **§6 covers placement** and was added 2026-08-05, after the wording-only sections were read downstream as if they described layout. §7 lists the corrections that re-reading produced. The other research notes (`hungarian-id-card-field-layout.md`, `hungarian-passport-field-layout.md`, `hungarian-driving-licence-field-layout.md`, `hungarian-other-id-documents.md`) remain the reference for field *semantics*; nothing here supersedes them.

## Provenance and the copyright constraint

Source: PRADO (Council of the EU public register of authentic identity and travel documents), specimen images, saved as MHTML in a human's browser because PRADO 403s automated fetches.

**No PRADO image is committed to this repo.** The specimen images are © Council of the European Union and are not redistributable. The captures live outside version control — `docs/prado/` is in `.gitignore` — and only the extracted label *text* below is committed. If you need to re-verify a label, re-fetch the page yourself; do not commit the image.

## Method, and its ceiling

PRADO's structured index fields describe **construction and security features** (substrate, OVD type, UV features, validity rules) and never transcribe biodata field wording. The labels exist only as pixels on the specimen images. Index pages embed those at ~171 px thumbnails, which are illegible; the full-size image is a separate page (`.../HUN-<cat><sub>-<5 digits>/image-<id>.html`) carrying a **600 px-wide** JPEG.

600 px across an 86 mm card is ~175 dpi. That is enough to read every field label confidently, and enough for most bracketed field numbers on the passport — but **not** all of them. Upscaling does not help; the information is not in the file. Everything below is either read directly off the image or explicitly marked unread. Nothing is inferred from expected standards.

## Document inventory

Confirmed from the PRADO index pages that were captured:

| PRADO ref | Category | First issued | Document |
|---|---|---|---|
| `HUN-AO-03001` | A – Passport | 01/03/2012 | Biometric passport, 88×125 mm, 32 pages |
| `HUN-BO-03001/03002/03005` | B – Identity card | 2000 / 2001 | Laminated ID card, "MAGYAR KÖZTÁRSASÁG" era |
| `HUN-BO-04001/04002` | B – Identity card | 01/03/2012 | Laminated ID card, "MAGYARORSZÁG" era |
| `HUN-BO-05001–05004` | B – Identity card | 01/01/2016 | eID card (chip) |
| `HUN-BO-06001` | B – Identity card | 02/08/2021 | eID card, current |
| `HUN-FO-03001` | F – Driving licence | 01/03/2012 | Card licence |
| `HUN-FO-04001` | F – Driving licence | 19/01/2013 | Card licence, current |
| `HUN-HO-09001/09002/09003` | H – Residence-related | 2000 / 2001 / 2012 | ID card issued to non-nationals |
| `HUN-HO-10001` | H – Residence-related | 01/03/2012 | **Address card** (*lakcímkártya*) |

Two findings worth flagging against the ticket's assumptions:

- **The address card is catalogued** — as `HUN-HO-10001` under **H – Residence-related**, not under P or X where the ticket looked.
- **`HUN-HO-09xxx` is not a separate document design.** It is the same ID card issued to non-Hungarian nationals: identical label set and layout to `HUN-BO-04001`, differing only in colour scheme (green/yellow rather than blue/yellow). A renderer needs no variant for it.

---

## 1. Identity card — current eID (`HUN-BO-05001`, `HUN-BO-06001`)

Bilingual Hungarian/English throughout, label and translation separated by `/`.

**Recto**

| Printed label | Field |
|---|---|
| `MAGYARORSZÁG / HUNGARY` | header |
| `SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY / IDENTITY CARD` | document title |
| `Családi és utónév/Family name and Given name:` | full name, one line |
| `Nem/Sex:` | `NŐ/F` observed |
| `Állampolgárság/Nationality:` | `HUN` |
| `Születési idő/Date of birth:` | |
| `Érvényességi idő/Date of expiry:` | |
| `Okmányazonosító/Doc. No.:` | |
| `CAN:` | 6 digits, **no translation** — CAN stands alone |
| `Aláírás/Signature:` | |

The document number is also printed **vertically** down the left edge beside the portrait, repeating the `Okmányazonosító` value.

**Verso**

| Printed label | Field |
|---|---|
| `Születési hely/Place of birth:` | `DEBRECEN (MAGYARORSZÁG)` — city with country in parentheses |
| `Születési családi és utónév/Family name and Given name at birth:` | |
| `Anyja születési neve/Mother's maiden name:` | |
| `Kiállító hatóság/Issuing authority:` | `BELÜGYMINISZTÉRIUM` on the 2021 card |
| *(unlabelled, bottom right)* | issue date, e.g. `2021.09.01` |
| *(unlabelled)* | 3-line TD1 MRZ |

**No `személyi azonosító` appears anywhere on the ID card** — neither face. It lives on the address card (§3).

## 2. Identity card — laminated generations

The label set is *not* stable across generations. Differences are real and a renderer must pick one generation.

### 2012 (`HUN-BO-04001`, `HUN-BO-04002`, and `HUN-HO-09003`)

**Recto:** `MAGYARORSZÁG` / `HUNGARY` / `SZEMÉLYAZONOSÍTÓ IGAZOLVÁNY` / `IDENTITY CARD`; `Okmányazonosító:`; `Kód/Code:` (`HUN`); `Családi és utónév/Surname and Given name:`; `Aláírás/Signature:`; `Érvényességi ideje/Date of expiry:`.

**Verso:** `Születési név/Birth name:`; `Születési hely/Place of birth:`; `Születési idő/Date of birth:`; `Neme/Sex:` (`NŐ/F`); `Állampolgárság/Nationality:` (`MAGYAR/HUN`); `Anyja születési neve/Mother's name:`; `Kiállító hatóság/Authority:` (`KEK KH`); unlabelled issue date; 3-line MRZ.

### 2000–2001 (`HUN-BO-03001`, `HUN-HO-09001`)

**Recto:** `MAGYAR KÖZTÁRSASÁG` / `REPUBLIC OF HUNGARY` — the pre-2012 country name; `Sorszám:` for the document number, **not** `Okmányazonosító:`; otherwise as 2012.

**Verso:** `Leánykori név/Maiden name:` — **not** `Születési név/Birth name:`; `Anyja neve/Mother's name:`; `Kiállító hatóság/Authority:` (`OKMÁNYIRODA, BM KÖZPONTI HIVATAL`); otherwise as 2012.

### Label drift across ID card generations

| Concept | 2000–2001 | 2012 | 2016 / 2021 |
|---|---|---|---|
| Country | `MAGYAR KÖZTÁRSASÁG` | `MAGYARORSZÁG` | `MAGYARORSZÁG / HUNGARY` |
| Doc. number | `Sorszám:` | `Okmányazonosító:` | `Okmányazonosító/Doc. No.:` |
| Name | `Családi és utónév/Surname and Given name:` | same | `Családi és utónév/Family name and Given name:` |
| Birth name | `Leánykori név/Maiden name:` | `Születési név/Birth name:` | `Születési családi és utónév/…at birth:` |
| Mother | `Anyja neve/Mother's name:` | `Anyja születési neve/Mother's name:` | `Anyja születési neve/Mother's maiden name:` |
| Sex | `Neme/Sex:` | `Neme/Sex:` | `Nem/Sex:` |
| Expiry | `Érvényességi ideje/Date of expiry:` | same | `Érvényességi idő/Date of expiry:` |

## 3. Address card — *lakcímkártya* (`HUN-HO-10001`)

**Monolingual Hungarian. No English on either face.** This is the sharpest contrast with every other document here.

The two faces carry **different document titles**:

**Recto — `LAKCÍMET IGAZOLÓ HATÓSÁGI IGAZOLVÁNY`**

| Printed label | Notes |
|---|---|
| `Családi és utónév:` | |
| `Születési név:` | |
| `Születési hely,idő:` | one label, two values; **no space after the comma** as printed |
| `Anyja neve:` | |
| `Lakóhely:` | permanent address; `Külföldi cím` ("foreign address") observed as a value |
| `Bejelentési idő:` | registration date, paired with `Lakóhely` |
| `Tartózkodási hely:` | temporary address |
| `Bejelentési idő:` | **repeats**, paired with `Tartózkodási hely` |
| `Érvényességi ideje:` | |
| `Kiállító hatóság:` | `NYILVÁNTARTÓ HIVATAL` observed |
| *(unlabelled, bottom right)* | issue date |

The document number (`000102 YL`) sits unlabelled beside the title on both faces.

**Verso — `MAGYARORSZÁG` / `SZEMÉLYI AZONOSÍTÓT IGAZOLÓ HATÓSÁGI IGAZOLVÁNY`**

| Printed label | Notes |
|---|---|
| `Személyi azonosító:` | printed as `2-720216-1673` — **grouped with hyphens**, `N-YYMMDD-NNNN` |
| `Családi és utónév:` | repeated from recto |
| *(unlabelled)* | 1-D barcode |

That `Bejelentési idő:` appears twice on one face, and that the personal identifier is hyphen-grouped rather than a bare 11-digit run, both matter for a renderer.

## 4. Driving licence (`HUN-FO-03001`, `HUN-FO-04001`)

**The licence prints no field labels next to its values.** The recto shows only bare numbers — `1.`, `2.`, `3.`, `4(a).`, `4(b).`, `4(c).`, `5.`, `7.`, `9.` — against the values, per the EU standard layout. The verso category table is headed only `9.` `10.` `11.` `12.`.

The field names appear **once**, as a legend, and the two generations word it differently:

| No. | `HUN-FO-03001` (2012) | `HUN-FO-04001` (2013) |
|---|---|---|
| 1 | `Családi név` | `Családi név` |
| 2 | `Utónév` | `Utónév` |
| 3 | `Születési idő, Születési hely` | `Születési idő és hely` |
| 4a | `Kibocsátási dátum` | `A kiállítás időpontja` |
| 4b | `Érvényességi idő` | `A lejárat időpontja` |
| 4c | `Kibocsátó hatóság` | `Kiállító hatóság` |
| 5 | `Sorszám` | `Az engedély száma` |
| 10 | `Vizsga időpontja` | `Érvényesség kezdete` |
| 11 | `Kategória érvényessége` | `Érvényesség vége` |
| 12 | `Korlátozások kódja` | `Kódok` |

On the 2012 card the legend is printed horizontally on the verso right-hand panel; on the 2013 card it is **rotated 90°** and set in two lines along the right edge. Neither legend lists 6, 7, 8, 13 or 14.

Also on the verso, both generations: `14. Államp:` (`HUN`) and `Sz.neve:` (holder's name), plus a `13.` grey box and a bare `12.` bottom-left.

**Note on `#42`'s heading claim:** headings 9–12 are indeed on page 2 — confirmed. The category table lists code, pictogram, then columns 10, 11, 12.

## 5. Passport (`HUN-AO-03001`)

**Trilingual Hungarian/English/French**, with a bracketed field number after each label.

| Printed label | No. |
|---|---|
| `MAGYARORSZÁG` (header), `ÚTLEVÉL` / `PASSPORT` (title, left panel) | — |
| `Típus / Type / Type` | — |
| `Kód / Code / Code` | — |
| `Útlevélszám / Passport number / Numéro du passeport` | — |
| `Családi név / Surname / Nom` | (1) |
| `Utónév(-ek) / Given names / Prénoms` | (2) |
| `Születési név / Birth name / Nom à la naissance` | (11) |
| `Állampolgárság / Nationality / Nationalité` | (3) |
| `Születési idő / Date of birth / Date de naissance` | (4) |
| `Nem / Sex / Sexe` | (5) |
| `Születési hely / Place of birth / Lieu de naissance` | (6) |
| `Kiállítási dátum / Date of issue / Date de délivrance` | (7) |
| `Érvényességi idő / Date of expiry / Date d'expiration` | **unread** |
| `Kiállító hatóság / Authority / Autorité` | **unread** |
| `Aláírás / Holder's signature / Signature du titulaire` | **unread** |

Two-line TD3 MRZ at the foot. `KEK KH` observed as the authority value.

**Unread, honestly:** the bracketed numbers on the last three labels are a smear at 600 px and I could not resolve them. The *label text* on all three is legible and is quoted above with confidence; only the parenthesised digits are unknown. They are conventionally 8/9/10 in some order, but this file does not assert what it could not read — resolve them from a higher-resolution scan or from statute before printing them.

---

## 6. Label placement — added 2026-08-05, and the gap that made it necessary

**This file claimed "label wording and layout" as its scope and delivered only wording.** Every section above is a `label → field` table; none of them says where on the card the label sits relative to its value. Downstream that gap got filled by guessing: [#60](https://github.com/akosgintl/document-intelligence/issues/60) and `fixtures/render.py`'s module docstring both assert, citing this file, that "the eID identity card sets its labels **inline**". This file never said that, and the specimen does not support it.

Re-read from the same PRADO captures, at 4–5× upscale.

### The eID identity card mixes three placements on one face

`HUN-BO-06001`, recto:

| Rows | Placement |
|---|---|
| `Családi és utónév/Family name and Given name:` | **stacked** — label on its own line, `SZÉPENÉ KISS ROZÁLIA` set larger and bold below it |
| `Nem/Sex:` and `Állampolgárság/Nationality:` | **inline, two per row** — `Nem/Sex: N/F` on the left and `Állampolgárság/Nationality: HUN` on the right of the *same* line |
| `Születési idő/…`, `Érvényességi idő/…`, `Okmányazonosító/…` | **label left, value right-aligned** to the card's right margin |
| `CAN:` | **inline** |

Verso: `Születési hely/…`, `Születési családi és utónév/…` and `Anyja születési neve/…` are all **stacked**; `Kiállító hatóság/Issuing authority: BELÜGYMINISZTÉRIUM` is **inline**; the issue date is right-aligned and unlabelled.

So the eID is not "an inline card". It is a card on which the name is stacked, two fields share an inline row, three are right-aligned, and one more is inline — and the same distinction repeats on the verso. **A renderer that picks one label placement per Document Type cannot draw this card**, which is a constraint neither of #60's two candidate shapes was framed around.

### The address card mixes placements too — and places the same label two ways

`HUN-HO-10001`. Recto: `Családi és utónév:DEBRECENI-SZATMÁRI ANDREA` runs **inline with no space after the colon**; `Születési név:`, `Anyja neve:`, `Lakóhely:` and `Kiállító hatóság:` put their values at a **tab stop** (a label column); and there is a **second column at the right** carrying `Bejelentési idő:` against each address, plus `Érvényességi ideje:` and the unlabelled issue date.

Verso: `Személyi azonosító: 2-720216-1673` is **inline**, but `Családi és utónév:` is **stacked** — the same label, placed differently on the two faces of one card.

### Summary, replacing the placement claims made elsewhere

| Type | What it actually does |
|---|---|
| Passport (`HUN-AO-03001`) | Label above value throughout; `Családi név` (1) and `Utónév(-ek)` (2) are **separate labelled fields**, not one combined line |
| Identity card, eID 2016/2021 | **Mixed** — stacked name, inline pairs, right-aligned values (above) |
| Identity card, laminated 2000/2012 | Label above value |
| Address card | **Mixed** — inline, label column, and a right-hand second column (above) |
| Driving licence | No labels beside values; bare EU numbers, plus the rotated verso legend |

### The name split is genuinely ambiguous on the two cards that combine it

The passport and the licence print surname and given names as separate fields. The eID and the address card print **one combined line**, and the specimens show why that is hard:

- eID: `SZÉPENÉ KISS ROZÁLIA` — a two-word married surname (`Szépéné` = wife of Szépe) plus one given name. Cut it one word early and you get `SZÉPENÉ` / `KISS ROZÁLIA`.
- Address card: `DEBRECENI-SZATMÁRI ANDREA` — hyphenated surname, one given name.

A fixture author choosing a holder name for these two types is choosing how hard this is; the Schemas ask for `surname` and `givenNames` separately while the card prints one string. Measured on a drawn fixture in `eval/prototype_label_placement/`, the split failed on 7 of 8 draws under one placement and 0 of 8 under another.

## 7. Corrections to the sections above

Found while re-reading the captures on 2026-08-05. Each replaces or sharpens a claim made earlier in this file.

- **§4, licence category table.** The table lists **every EU category** — `AM A1 A2 A B1 B C1 C D1 D BE C1E CE D1E DE T K`, 17 rows — not only the ones held. Each row prints a **pictogram** beside its code in column `9.`, and a category the holder does not hold prints an **en dash `–`** in columns 10, 11 and 12. Restriction codes in column 12 are **three digits** on this specimen (`102`, `186`), not the two-digit EU harmonised codes. The `DD.MM.YY.` format with trailing dot recorded above is **correct for both** columns 10 and 11 (`12.06.95.` / `30.11.17.`).
- **§4, the rotated legend, transcribed in full.** Two lines, rotated 90° along the right edge of the verso, reading bottom to top:
  1. `1. Családi név 2. Utónév 3. Születési idő és hely 4a. A kiállítás időpontja 4b. A lejárat időpontja`
  2. `4c. Kiállító hatóság 5. Az engedély száma 10. Érvényesség kezdete 11. Érvényesség vége 12. Kódok`

  The per-number wording in §4's table was correct; what is new is the line break, which falls **after** `4b.`
- **§1, the MRZ.** The eID's zone is TD1, three lines of 30, and its document code is **`I<`** — `I` padded with one filler — not `ID`. The specimen reads `I<HUN000188KE<1…`, and its name line reads `SZEPENE<KISS<<ROZALIA<<<<<<<<<` against a VIZ of `SZÉPENÉ KISS ROZÁLIA`.
- **MRZ transliteration is settled by ICAO Doc 9303 Part 3 §6.A** for every letter Hungarian prints, each with a single recommended transliteration: `Á→A`, `É→E`, `Í→I`, `Ó→O`, `Ú→U`, and both double-acutes `Ő→O` (U+0150) and `Ű→U` (U+0170). The specimen agrees (`SZÉPENÉ`→`SZEPENE`, `ROZÁLIA`→`ROZALIA`), as does the passport in `hungarian-passport-field-layout.md` §7.4 (`ROZÁLIA`→`ROZALIA`).

  **`Ö` and `Ü` are not settled.** §6.A gives `OE or O` and `UE or UXX or U`, and the choice belongs to the issuing State. No specimen captured here carries either letter in a name, and [#48](https://github.com/akosgintl/document-intelligence/issues/48)'s statute pass found no rule. `fixtures/identifiers.py` refuses them rather than guessing; a fixture should choose a holder name without them.
- **The passport MRZ transcription in `hungarian-passport-field-layout.md` §7.4 is one character too long.** Its line 1 is transcribed at 45 characters where TD3 has 44 — one filler too many in the trailing run. Worth knowing generally: a trailing run of `<` is where MRZ transcription fails, for a human reading a specimen as much as for a model reading a fixture.
- **The driving licence carries no address.** Confirmed on `HUN-FO-04001`'s verso, which holds only `13.`, `14. Államp:`, `Sz.neve:` and the category table. This agrees with [#48](https://github.com/akosgintl/document-intelligence/issues/48)'s reading of 326/2011 Annex 5 against the single Commission summary page `hungarian_driving_licence/v1.json`'s nullable `address` rests on. Whether the Schema should keep the field is a question for [#33](https://github.com/akosgintl/document-intelligence/issues/33), not for a fixture.

## Date formats — the single most surprising result

Hungarian identity documents do **not** share one date format. Several print more than one format on the same document.

| Document | Field | Printed as | Example |
|---|---|---|---|
| Passport | all dates | `DD MMM/MMM YY`, bilingual month | `22 FEB/FEB 78`, `01 MÁR/MAR 12` |
| ID card 2000–2012 | date of birth (verso) | Hungarian long form, **lowercase month, trailing dot** | `1979. június 30.` |
| ID card 2000–2012 | expiry (recto) | `YYYY MMM/MMM DD`, bilingual month | `2022 MÁR/MAR 18`, `2010 JAN/JAN 11` |
| ID card 2000–2012 | issue (verso) | `YYYY.MM.DD.` | `2012.03.18.` |
| ID card 2016/2021 | birth, expiry | `DD MM YYYY`, **space-separated, no dots** | `30 06 1979` |
| ID card 2021 | issue (verso) | `YYYY.MM.DD` | `2021.09.01` |
| Address card | all dates | `YYYY.MM.DD` | `1972.02.16`, `2015.05.01` |
| Licence | recto fields 3, 4a, 4b | `YYYY.MM.DD.` | `1975.05.27.`, `2013.02.05.` |
| Licence | verso table cols 10, 11 | `DD.MM.YY.` | `12.06.95`, `30.11.17.` |

**This corrects an assumption on the map.** Convention 9 of [#46](https://github.com/akosgintl/document-intelligence/issues/46) records "each type's real printed date format — including the licence's `DD.MM.YY`". That is right for the **verso category table** and wrong for the **recto**, which prints `YYYY.MM.DD.`. The licence carries both formats simultaneously. A fixture that uses `DD.MM.YY` on the recto would be wrong.

The 2012-era ID card is the extreme case: **three** formats on one card.

## Other values worth reusing in fixtures

- Sex is printed as a Hungarian/English pair separated by `/`. Observed values, verbatim: `NŐ/F` (`HUN-BO-05001` eID, `HUN-BO-04001`), `FÉRFI/M` (`HUN-BO-03001`), `N/F` (`HUN-BO-06001` eID, and the passport). Both the full-word and single-letter Hungarian forms occur on cards of the same era, so a renderer should choose one deliberately rather than assume.
- Nationality: `MAGYAR/HUN` on cards, `MAGYAR/HUNGARIAN` on the passport, bare `HUN` on the eID.
- Place of birth is printed as `CITY (COUNTRY)` — `DEBRECEN (MAGYARORSZÁG)`, `BUDAPEST 08 (MAGYARORSZÁG)`. Budapest districts appear as a two-digit suffix (`BUDAPEST 07`, `BUDAPEST 13`).
- Authority values seen: `KEK KH` (passport, 2012 ID card), `BELÜGYMINISZTÉRIUM` (2021 eID), `NYILVÁNTARTÓ HIVATAL` (address card), `OKMÁNYIRODA, BM KÖZPONTI HIVATAL` (2000 ID card).
- Document numbers: ID card `000188KE`, `000230PA`, `500500AA` — 6 digits + 2 letters. Passport `BD0002028` — 2 letters + 7 digits. Licence `CM001267` — 2 letters + 6 digits.
- Specimens are marked `SPECIMEN` (diagonal, red) on the cards and passport, and `SPECIMEN`/`MINTA` overprints appear on the address card.

## What could not be sourced

Per the ticket's resolution requirement, these are the labels a renderer must invent or take from statute rather than from PRADO:

1. **The passport's bracketed numbers for expiry, authority and signature** — see §5. Label text known; digits unread.
2. **The passport's non-biodata pages.** Only the biodata page was captured; observation pages, the endorsements page and the cover carry text this file does not cover.
3. **The address card's own field-number scheme** — it has none; the card is label-only, so nothing is missing, but a renderer cannot fall back on numbering here.
4. **Any label on the eID chip surface or the licence's field 8** (address) — field 8 is not printed on the Hungarian licence specimens captured, and no label for it exists to quote.
5. **Minority-language name rendering.** `HUN-BO-05004`'s PRADO index notes "Holder's name in a 'national language' (of a national minority) features on verso", but the captured verso image does not show a distinct label for it. If a fixture needs that case, the label is unsourced.
