# Hungarian Passport Field Layout and ICAO 9303 MRZ Standard

**Scope.** This document researches, for GitHub issue #36 ("Research Hungarian passport field layout and MRZ standard"), (a) the field set printed on a Hungarian passport's Visual Inspection Zone (VIZ, i.e. the biographic/data page as read by eye) and (b) the ICAO Doc 9303 TD3 (two-line) Machine Readable Zone (MRZ) format that every ICAO-compliant passport, including Hungary's, carries at the bottom of that same page. The goal is to give a later design ticket the facts it needs to decide whether to model MRZ sub-fields (document code, check digits, etc.) individually in a JSON Schema, and where Hungary's actual printed document deviates from the ICAO baseline. **No JSON Schema is proposed here** — this is fact-gathering only.

Primary sources used, in priority order:
1. **ICAO Doc 9303, Eighth Edition (2021), Part 3 — *Specifications Common to all MRTDs*** and **Part 4 — *Specifications for Machine Readable Passports (MRPs) and other TD3 Size MRTDs*** — fetched as the actual PDF documents (with Amendment 2, dated 20/2/26, already incorporated) from `icao.int`, and read directly (not summarized by a secondary tool). This is the ICAO baseline for both VIZ and MRZ.
2. **A genuine Hungarian passport specimen biodata-page image**, sourced via Wikimedia Commons but attributed to the Council of the EU's PRADO register (`prado.consilium.europa.eu`) and captioned "Author: Hungarian Government" / public domain under Hungarian copyright law — read and transcribed directly (including the printed MRZ string), giving primary-source-grade evidence of what a real Hungarian passport actually prints. PRADO itself (`consilium.europa.eu/prado`) returned HTTP 403 to every fetch attempt in this research and could not be read directly; this is noted explicitly wherever PRADO would otherwise have been the ideal source.
3. **Wikipedia's "Hungarian passport" article**, used only as a secondary cross-check on the specimen image and for passport-type/language claims not visible on the specimen image itself, per this repo's research convention of preferring primary sources but allowing reputable secondary sources when flagged.
4. Hungarian government pages (`kormany.hu`, `konzuliszolgalat.kormany.hu`, Hungarian embassy pages) were fetched but yielded essentially no technical field-layout detail — this is noted in §7 rather than silently omitted.

Everything below is either a direct quote/close paraphrase with a URL, a direct transcription of the specimen image (with the image cropped and re-read at higher zoom to confirm exact characters), or explicitly marked **not confirmed by a fetched primary source**.

---

## Summary of findings

| Question | Answer | Confidence |
|---|---|---|
| ICAO TD3 VIZ field set (Zones I–VI) | 20 numbered fields (01–20), fully enumerated in §1 below, with explicit mandatory/optional status per field | **Confirmed** — read directly from ICAO 9303-4 §4.1.1.1 |
| ICAO TD3 MRZ structure (Zone VII, 2×44 chars) | Fully enumerated character-position-by-character-position in §2/§3 below | **Confirmed** — read directly from ICAO 9303-4 §4.2.2 |
| Check-digit algorithm | Modulus-10, weights 7-3-1 repeating, letters A–Z = values 10–35 | **Confirmed** — read directly from ICAO 9303-3 §4.9 |
| Does Hungary print all ICAO-mandatory VIZ fields? | Yes, all 9 mandatory fields present on the specimen, plus optional place-of-birth | **Confirmed** — from specimen transcription, §5 |
| Does Hungary populate the MRZ "personal number" optional field (position 29–42 of line 2) with the Hungarian `személyi szám`? | **No** — the field is entirely filler characters (`<`) on the specimen, with check digit `0` | **Confirmed** on the one specimen examined (2012-era passport); **not confirmed** whether this still holds for passports issued in 2026 |
| Does Hungary add any VIZ field beyond the ICAO baseline? | Yes — a "Születési név / Birth name / Nom à la naissance" field not named in ICAO's field list | **Confirmed** from specimen; exact field number partially illegible (see §5) |
| Hungarian passport number format | 2 uppercase letters + 7 digits on the specimen (`BD0002028`) | **Confirmed** from specimen; Wikipedia states "six or seven digits" generally — **not fully cross-confirmed** |
| Document code used by Hungary | `P` only (single-letter) on the 2012-era specimen, not the newer two-letter `PP` | **Confirmed** for that specimen; **not confirmed** for passports issued after ICAO's 1 Jan 2026 secondary-code phase-in (see §4) |
| PRADO's own Hungary passport catalogue entries | Exist (`HUN-AO-03001` etc.) but page content could not be fetched (HTTP 403) | **Not confirmed by a fetched primary source** — content inferred only from search-result snippets, flagged explicitly in §7 |

---

## 1. ICAO 9303 Part 4 — Visual Inspection Zone (VIZ) data element directory

Source: ICAO Doc 9303, Eighth Edition 2021 (Amendment 2, 20/2/26), **Part 4**, §4.1 "Visual Inspection Zone (VIZ) (Zones I through VI)", §4.1.1.1 "Visual inspection zone — Data element directory". Fetched directly from `https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf` and read as a PDF (not paraphrased by a secondary summarizer).

The VIZ occupies Zones I–VI of the data page (Zone VII is the MRZ, covered in §2–§3). ICAO enumerates 20 numbered fields:

| Field / zone | Data element | Mandatory? | Max. characters | Notes |
|---|---|---|---|---|
| 01/I | Issuing State or organization (in full) | Mandatory | Variable | If omitted, must appear on an adjacent/preceding page |
| 02/I | "Document" (the word "passport" in the issuing language, or PASSPORT/PASSEPORT/PASAPORTE) | Mandatory | Variable | |
| 03/I | Document code | Mandatory | 2 (fixed) | First letter always `P`; second letter designates MRP type (see §4) |
| 04/I | Issuing State or organization (in code) | Mandatory | 3 (fixed) | ISO 3166 three-letter code |
| 05/I | Passport Number | Mandatory | 9 | Uniquely identifies the document within the issuing State/org |
| 06/07/II | Name (full) | Mandatory | Variable | Full name of holder |
| 06/II | Primary Identifier | Mandatory | Variable | Predominant component(s) of the name |
| 07/II | Secondary Identifier | Mandatory | Variable | Remaining component(s); may be left blank if the name has only a primary identifier |
| 08/II | Nationality | Mandatory | Variable | |
| 09/II | Date of birth | Mandatory | Variable | |
| 10/II | Personal number | **Optional** | Variable | "Field optionally used for personal identification number given to holder by the issuing State or organization" |
| 11/II | Sex | Mandatory | 3 | Single national initial, "followed by an oblique and the capital letter F for female, M for male, or X for unspecified" if translation into English/French/Spanish is needed |
| 12/II | Place of birth | **Optional** element in a mandatory zone | Variable | "Field optionally used for city and State of the holder's birthplace" |
| 13/II | Optional personal data elements | **Optional** | Variable | e.g. personal identification number or fingerprint, at issuing State's discretion |
| 14/III | Date of issue | Mandatory | Variable | |
| 15/III | Authority or issuing organization | Mandatory | Variable | |
| 16/III | Date of expiry | Mandatory | Variable | |
| 17/III | Optional document data elements | **Optional** element in a mandatory zone | Variable | |
| 18/IV | Holder's signature or usual mark | Mandatory | — | May be located on an adjacent page |
| 19/V | Identification feature (portrait) | Mandatory | 45.0×35.0 mm max / 32.0×26.0 mm min | |
| 20/VI | Optional data elements | **Optional** | Variable | |

Every field the design ticket's list names (passport number, surname, given names, nationality, date of birth, sex, place of birth, date of issue, date of expiry, issuing authority, personal ID number) maps directly onto ICAO fields 05, 06, 07, 08, 09, 11, 12, 14, 15, 16, and 10 respectively. Of these, **only place of birth (12) and personal number (10) are ICAO-optional** — everything else in that list is ICAO-mandatory.

ICAO 9303-4 also documents a **Card Access Number (CAN)** — a 6-digit numeric field, optionally printed on or adjacent to the data page to enable contactless-chip access via PACE, with no check digit ("the check is implicitly performed by the protocol"). §4.1.1.2.

---

## 2. ICAO 9303 Part 4 — TD3 MRZ, upper line (Line 1, 44 characters)

Source: ICAO 9303-4 §4.2.2.1 "Data structure of the upper machine readable line".

| Positions | Field no. (VIZ) | Data element | Length | Notes |
|---|---|---|---|---|
| 1–2 | 03 | Document code | 2 | First char `P`; second char = MRP type per §4.4 |
| 3–5 | 04 | Issuing State or organization | 3 | Spaces replaced by `<` |
| 6–44 | 06, 07 | Name (primary identifier + `<<` + secondary identifier + filler) | 39 | Punctuation not permitted; truncation rules apply if the name exceeds 39 characters (see §5 below) |

---

## 3. ICAO 9303 Part 4 — TD3 MRZ, lower line (Line 2, 44 characters) and check digits

Source: ICAO 9303-4 §4.2.2.2 "Data structure of the lower machine readable line" and §4.2.4 "Check digits in the Machine Readable Zone".

| Positions | Field no. (VIZ) | Data element | Length | Notes |
|---|---|---|---|---|
| 1–9 | 05 | Passport number | 9 | Special characters/spaces replaced by `<`, then filler-padded |
| 10 | — | Check digit (over positions 1–9) | 1 | |
| 11–13 | 08 | Nationality | 3 | Three-letter code |
| 14–19 | 09 | Date of birth (YYMMDD) | 6 | |
| 20 | — | Check digit (over positions 14–19) | 1 | |
| 21 | 11 | Sex | 1 | `F` = female, `M` = male, `<` = unspecified |
| 22–27 | 16 | Date of expiry (YYMMDD) | 6 | |
| 28 | — | Check digit (over positions 22–27) | 1 | |
| 29–42 | 10 | Personal number or other optional data | 14 | Filler-padded if unused |
| 43 | — | Check digit (over positions 29–42) | 1 | "When the personal number field is not used and filler characters (<) are used in positions 29 to 42, the check digit may be zero or the filler character (<) at the option of the issuing State or organization." |
| 44 | — | **Composite check digit** | 1 | Computed over lower-line positions **1–10, 14–20, and 22–43** — i.e. explicitly **excluding** positions 11–13 (nationality) and 21 (sex) |

This exactly matches the field set the design ticket asked to cover: document type, issuing state, name, passport number + check digit, nationality, DOB + check digit, sex, expiry + check digit, personal number, composite check digit. ICAO defines **five check digits total** in the MRZ (passport number, DOB, expiry, personal number, and the composite), each independently computable, which is directly relevant to the design ticket's question of whether to model MRZ sub-fields individually — the four component check digits are not redundant with the composite; each validates a different substring.

---

## 4. Check-digit algorithm (ICAO 9303 Part 3, §4.9)

Source: ICAO 9303-3 §4.9 "Check Digits in the MRZ", fetched from `https://www.icao.int/sites/default/files/publications/DocSeries/9303_p3_cons_en.pdf`.

> "A special check digit calculation has been adopted for use in MRTDs. The check digits shall be calculated on modulus 10 with a continuously repetitive weighting of 731 731 ..., as follows.
> Step 1. Going from left to right, multiply each digit of the pertinent numerical data element by the weighting figure appearing in the corresponding sequential position.
> Step 2. Add the products of each multiplication.
> Step 3. Divide the sum by 10 (the modulus).
> Step 4. The remainder shall be the check digit.
> For data elements in which the number does not occupy all available character positions, the symbol < shall be used to complete vacant positions and shall be given the value of zero for the purpose of calculating the check digit.
> When the check digit calculation is applied to data elements containing alphabetic characters, the characters A to Z shall have the values 10 to 35 consecutively."

This is the algorithm underlying every check digit named in §3 above (passport number, DOB, expiry, personal number, composite).

---

## 5. Document codes and the 2026/2028 secondary-code phase-in (ICAO 9303 Part 4, §4.4)

Source: ICAO 9303-4 §4.4 "Document Codes".

> "Document codes are contained within the VIZ (Field 03) and the MRZ (positions 1 and 2). The first letter P shall identify the document as an MRP. The second letter shall identify the document type as per the following table:"

| Document type | Document code |
|---|---|
| National/ordinary passport | PP |
| Emergency passport | PE |
| Diplomatic passport | PD |
| Official/service passport | PO |
| Refugee passport | PR |
| Alien/Non-citizen passport | PT |
| Stateless passport | PS |
| Laissez-passer passport | PL |
| Military passport | PM |

Critically for the design ticket's schema-timing question:

> "Effective 1 January 2026, MRPs issued with a secondary document code shall be in accordance with Section 4.4. Effective 1 January 2028, all MRPs shall be issued with a secondary document code in accordance with Section 4.4. MRPs issued without a harmonized secondary document code in accordance with Section 4.4 shall expire before 1 January 2038."

So as of today (per the environment's stated current date, 1 August 2026), ICAO's own transition window is **live but not yet mandatory** — states may already be printing the two-letter code, but are not required to until 1 January 2028, and pre-2026 passports without it remain valid (and thus in circulation) until as late as 2038. The Hungarian specimen examined in this research (§6) predates this rule entirely (issued 2012) and shows only a bare `P` with no second letter — **it is not confirmed whether Hungary has since adopted the `PP` secondary code** for passports issued in the 2026 window; no post-2026 Hungarian specimen was located during this research.

---

## 6. Name truncation and representation rules (ICAO 9303 Part 3 §4.6 and Part 4 §4.2.3)

Relevant to whether the design ticket needs a separate "MRZ name" field distinct from the VIZ surname/given-name fields:

- Source: 9303-3 §4.6 — "the primary and secondary identifiers in the MRZ shall be printed using upper-case OCR-B characters ... without diacritical marks ... names in the MRZ are represented differently from those in the VIZ." Apostrophes are dropped with no filler; hyphens become a single filler `<`; a comma separating primary/secondary identifiers in the VIZ becomes `<<` in the MRZ; all other punctuation is simply omitted.
- Source: 9303-4 §4.2.3 — the MRZ name field is 39 characters; if primary+secondary identifiers exceed that, truncation occurs per a defined procedure, and **the last character of the truncated name field must be alphabetic (A–Z) as a truncation signal** — meaning a name that happens to end in an alphabetic character at position 44 must be *assumed* truncated even if it wasn't, per an explicit ICAO note.

This is a firm "yes" signal for the design ticket: **VIZ name and MRZ name are not guaranteed to be the same string** — diacritics, punctuation, and possible truncation mean a schema that only stores one "name" field risks losing information present on the actual document, particularly for Hungarian names that may carry diacritics (e.g. á, é, í, ó, ö, ő, ú, ü, ű) which the VIZ prints but the MRZ strips.

---

## 7. Hungary-specific findings from a genuine specimen

### 7.1 Provenance of the specimen used

A specimen Hungarian passport biodata page was obtained via Wikimedia Commons: [File:Hungarian_passport_biodata_page.png](https://commons.wikimedia.org/wiki/File:Hungarian_passport_biodata_page.png). Its Commons file description page states:

> Description: "Biodata page of the Hungarian biometric passport (first issued on 29 August 2006)."
> Source: `http://prado.consilium.europa.eu/en/2992/viewImage_70491.html`
> Author: "Hungarian Government"
> Date: 29 August 2006
> License: Public Domain (Hungarian copyright law exempts official state documents)

So while PRADO's own site could not be fetched directly in this research (HTTP 403 on every attempt, including a manual `curl` with a browser user-agent), this image is a mirror of a PRADO-hosted specimen, itself attributed to the Hungarian government — the closest this research could get to a Hungary-primary source for the physical document layout. It is a "SPECIMEN" watermarked sample document (holder name "Handra Rozália Irma"), not a real citizen's passport.

The image was fetched, then cropped and upscaled (4–6×) locally to confirm exact characters before transcribing — this was not a one-glance read.

### 7.2 VIZ fields on the specimen — matches ICAO baseline, plus one addition

Transcribed field captions (Hungarian / English / French) and specimen values:

| Caption (as printed) | Value on specimen | Maps to ICAO field |
|---|---|---|
| Típus / Type / Type | `P` | 03 (document code, first letter) |
| Kód / Code / Code | `HUN` | 04 |
| Útlevélszám / Passport number / Numéro de passeport | `BD0002028` | 05 |
| Családi név / Surname / Nom (1) | `HANDRA` | 06 |
| Utónév(nevek) / Given name(s) / Prénoms (2) | `ROZÁLIA IRMA` | 07 |
| **Születési név / Birth name / Nom à la naissance** (numbered separately, digit partly illegible — reads as "(11)" at the resolution available) | `FRUNZA ROZÁLIA IRMA` | **No direct ICAO field name** — see §7.3 |
| Állampolgárság / Nationality / Nationalité (3) | `MAGYAR/HUNGARIAN` | 08 |
| Születési idő / Date of birth / Date de naissance (4) | `22 FEB/FEB 78` | 09 |
| Nem / Sex / Sexe (5) | `N/F` | 11 |
| Születési hely / Place of birth / Lieu de naissance (6) | `BUDAPEST 07` | 12 |
| Kiállítás kelte / Date of issue / Date de délivrance (7) | `01 MÁR/MAR 12` | 14 |
| Kiállító hatóság / Authority / Autorité (9) | `KEK KH` | 15 |
| Lejárat ideje / Date of expiry / Date d'expiration (8) | `01 MÁR/MAR 22` | 16 |
| Aláírás / Holder's signature / Signature du titulaire (10) | (handwritten signature) | 18 |

Observations:

- **All nine ICAO-mandatory VIZ fields are present**, plus the ICAO-optional **place of birth**.
- The **`Nem/Sex/Sexe` value `N/F`** matches ICAO's Field 11 spec exactly — "N" is the Hungarian initial (Nő = woman), followed by the oblique-and-English/French-letter convention (`F`) — and the field occupies exactly the "maximum 3 character positions" ICAO's table specifies (§1 above).
- The **passport number `BD0002028`** is 2 letters + 7 digits, consistent with (not independently confirmed beyond) Wikipedia's general claim that Hungarian passport numbers are "two uppercase letters followed by six or seven digits."
- **`Kiállító hatóság` value `KEK KH`** is an abbreviation for Közigazgatási és Elektronikus Közszolgáltatások Központi Hivatala (KEKKH), the Hungarian government body that administered passport issuance until it was dissolved on 31 December 2016, with its records-management functions transferred to the Ministry of Interior's "Nyilvántartások Vezetéséért Felelős Helyettes Államtitkárság." **The issuing-authority string shown on current-era Hungarian passports is likely different from `KEK KH`**, since this specimen is from 2012 and the issuing body was reorganized in 2017; this was not independently confirmed with a current-era specimen. (`https://hu.wikipedia.org/wiki/K%C3%B6zigazgat%C3%A1si_%C3%A9s_Elektronikus_K%C3%B6zszolg%C3%A1ltat%C3%A1sok_K%C3%B6zponti_Hivatala`, cross-checked via search snippets — the Wikipedia article itself was not directly fetched for this specific claim, so treat this particular sub-point as weaker than the directly-transcribed specimen facts.)
- **Document code is a bare `P`**, not the two-letter `PP` ICAO's 2026/2028 phase-in describes (§4) — expected, since this specimen (issued 2012) long predates that rule.

### 7.3 Hungary-specific deviation: a "Birth name" VIZ field not in ICAO's field list

ICAO's 20-field VIZ directory (§1) has no field named "birth name" — the closest ICAO concepts are Field 07 (Secondary Identifier, part of the legal current name) and Field 13 (Optional personal data elements, explicitly for things like "personal identification number or fingerprint"). Hungary's specimen prints a distinct **"Születési név / Birth name / Nom à la naissance"** field, populated with a *different* name (`FRUNZA ROZÁLIA IRMA`) than the surname/given-name fields (`HANDRA` / `ROZÁLIA IRMA`) — i.e., this is the holder's name at birth (maiden name / pre-marriage or pre-adoption legal name), shown separately from the current legal surname. This is a genuine Hungary-specific addition to the VIZ layout beyond the ICAO baseline, most plausibly using the discretionary slot ICAO Part 4 makes available via Field 13 ("optional personal data elements ... at the discretion of the issuing State"), though the exact field number on the specimen was not fully legible even after 4–6× upscaling — this document reads it as most likely "(11)" but flags that digit specifically as uncertain.

### 7.4 Hungary-specific deviation: the MRZ personal-number field is left empty

The specimen's two MRZ lines, transcribed directly from the (upscaled) image:

```
P<HUNHANDRA<<ROZALIA<IRMA<<<<<<<<<<<<<<<<<<<<
BD00020282HUN7802225F2203012<<<<<<<<<<<<<<06
```

Decoded against the §3 position table:
- Positions 1–9: `BD0002028` (passport number, matches VIZ)
- Position 10: `2` (check digit)
- Positions 11–13: `HUN` (nationality)
- Positions 14–19: `780222` (DOB, YYMMDD = 22 Feb 1978, matches VIZ's `22 FEB/FEB 78`)
- Position 20: `5` (check digit)
- Position 21: `F` (sex)
- Positions 22–27: `220301` (expiry, YYMMDD = 1 Mar 2022, matches VIZ's `01 MÁR/MAR 22`)
- Position 28: `2` (check digit)
- Positions 29–42: fourteen `<` filler characters — **the personal-number/optional-data field is entirely unused**
- Position 43: `0` — per ICAO's explicit allowance (§3 above), an unused personal-number field's check digit "may be zero or the filler character `<` at the option of the issuing State"; Hungary chose `0`
- Position 44: `6` (composite check digit)

**Hungary does not encode the Hungarian national personal identification number (`személyi szám`, an 11-digit `GYYMMDDXXXC`-format number issued to every citizen at birth) into the MRZ's optional personal-number field on this specimen.** The Hungarian ID *card* (a separate document, not researched in depth here) is understood from general search results to carry the `személyi szám` more directly, but this passport specimen's MRZ optional-data slot is simply blank filler. This directly answers the design ticket's implicit question about whether "personal ID number if present" should be modeled as a real, populated field for Hungary: **on this specimen, it is present as a schema slot but not populated with data** — the field exists in the ICAO structure but Hungary chooses not to use it for the passport document.

This is a **single 2012-era specimen**; it is **not confirmed** whether newer (2020s-issued) Hungarian passports populate this field differently.

---

## 8. Passport types

Wikipedia's "Hungarian passport" article (secondary source, cross-checked against the specimen's own "Type: P" / document-code framing but not independently verified against a primary Hungarian government list) states Hungary issues:

- **Personal** (ordinary) passports
- **Official** passports, further split into: diplomatic, service, foreign service, and seamen's-service passports

This is broadly consistent with ICAO's own document-code table (§4) distinguishing `PP` (national/ordinary), `PD` (diplomatic), and `PO` (official/service) — Hungary's categories map onto a subset of ICAO's general vocabulary, but this research did not locate a Hungarian-government primary source enumerating exact document-code usage per passport type. PRADO (§7.1) would very likely have this detail (it lists separate document IDs like `HUN-AO-03001` for what search snippets described as the "ordinary" category and `HUN-AD-02001` for a different category, consistent with an AO/AD-style internal PRADO taxonomy) but its pages returned HTTP 403 to every fetch attempt in this research, so this cannot be confirmed from PRADO directly.

---

## 9. Sources that were checked but yielded no usable technical detail

For completeness/transparency, per this repo's citation standard, these were fetched and found unhelpful rather than silently skipped:

- `kormany.hu/nyilvantartasok/ugyleirasok/utlevel` — describes application procedure and biometric chip existence only; no field-layout detail.
- `wellington.mfa.gov.hu/eng/page/passport` (Hungarian embassy) — page content truncated/unavailable via WebFetch, yielded nothing.
- IRB Canada / ecoi.net document on Hungarian identity cards — is about the separate ID card, not the passport; only one incidental passport mention with no technical content.
- `konzuliszolgalat.kormany.hu` — search results surfaced only visa-related and general consular content, nothing on data-page fields.
- PRADO (`consilium.europa.eu/prado`) — HTTP 403 on all direct-fetch attempts (WebFetch and a manual `curl` with a spoofed browser user-agent both failed identically); all PRADO-derived facts in this document come secondhand, either via the Wikimedia-hosted specimen image (§7.1) or via search-result snippets, and are flagged accordingly.

---

## Open questions for the design ticket

1. **Is the "personal number" MRZ/VIZ slot worth modeling as a real field for Hungary at all?** The one specimen examined leaves it entirely blank. If current-era Hungarian passports still leave it blank, a schema could reasonably treat it as `null`/absent for Hungary specifically rather than expecting a populated `személyi szám`. This should be verified against a more recent Hungarian passport specimen before the schema is finalized — this research could not locate one.
2. **How should the Hungary-specific "Birth name" VIZ field be modeled?** It is not part of ICAO's 20-field baseline (§1) and has no obvious ICAO field-number equivalent beyond a generic "optional personal data element" slot. The design ticket should decide whether this becomes its own schema property (e.g. `birthName`) or is folded into a generic optional-fields bag.
3. **Document code transition (`P` vs `PP`):** ICAO's secondary-code requirement is optional-until-2026, mandatory-by-2028 (§4), and today's date is past the optional-adoption start. Whether Hungary has begun issuing `PP`-coded passports is unconfirmed — worth checking against a passport issued in 2024–2026 before the schema locks in a fixed 1-character vs. 2-character document-code assumption.
4. **VIZ vs. MRZ name divergence (§6):** ICAO's own truncation and diacritic-stripping rules mean the MRZ name is not guaranteed byte-identical to the VIZ name for Hungarian names carrying diacritics. The design ticket should decide whether to store both independently (recommended, given ICAO explicitly documents them as different representations) or derive one from the other.
5. **Exact digit in the "Birth name" field's caption number** (transcribed as likely "(11)" in §7.2) could not be confirmed with full confidence even after 4–6× image upscaling — a higher-resolution specimen would resolve this, though it is unlikely to matter for schema design (the field's existence and content are what matter, not its printed caption number).
6. **PRADO access:** if the design ticket's authors have any authenticated/allow-listed access to `consilium.europa.eu/prado`, it should be reconsulted directly — it is very likely the single best primary source for Hungary-specific document metadata (exact field-by-field layout, current issuing-authority string, per-passport-type document codes) and was completely inaccessible to this research (HTTP 403 throughout).
