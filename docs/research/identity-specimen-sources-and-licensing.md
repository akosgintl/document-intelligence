# Hungarian identity documents: specimen imagery beyond PRADO, and what its licensing permits

Researched 2026-08-06 from Hungarian government sources, EUR-Lex, and ICAO, resolving [#70](https://github.com/akosgintl/document-intelligence/issues/70), part of map [#65](https://github.com/akosgintl/document-intelligence/issues/65).

## Why this file exists

[#65](https://github.com/akosgintl/document-intelligence/issues/65)'s convention 5 rules that identity fixtures are **redrawn from reference, never composited from a scan** — a ruling made on the strength of PRADO specimen images being Council of the EU copyright ([#47](https://github.com/akosgintl/document-intelligence/issues/47)). That ruling is tested here against the rest of the field: does a published specimen source exist, for any of the four Hungarian identity document types, whose licensing is more permissive than PRADO's — specifically, permissive enough to permit *derivative* use rather than reference-only redrawing?

**Scope boundary, held strictly throughout:** this file is about *specimen* imagery — the MINTA-marked examples authorities publish deliberately. Blank ("bianco") document stock is not a target; it is controlled security material and out of scope regardless of what licensing it might carry. Nothing below pursues, links to, or describes a source of blank stock.

**The asymmetry the ticket set up:** the ID card and address card are purely national designs with no EU-prescribed layout, so PRADO is the only real candidate regardless of what else turns up. The passport and the driving licence are different — both formats are prescribed *with figures* in EU law, so a better-licensed EU source might exist for those two specifically. That is where this research concentrated.

## Method, and its ceiling

| Source | How reached | What happened |
|---|---|---|
| Hungarian government sites (bm.hu, nyilvantarto.hu, kormany.hu, kekkh.gov.hu, e-egeszsegugy.gov.hu, police.hu) | Direct HTTP/WebFetch, plus targeted web search | Mixed — see §2. `bm.hu` returned a TLS certificate error on every attempt (root and deep links); its press room (*sajtószoba*) was never reached, and is the single most likely place for an official passport/licence redesign announcement. `kekkh.gov.hu`'s certificate is issued for `*.nyilvantarto.hu`, not `kekkh.gov.hu`, and also went unreached. |
| EUR-Lex (`eur-lex.europa.eu`) | Direct WebFetch, including the original scanned OJ PDF endpoint (`/legal-content/EN/TXT/PDF/?uri=CELEX:<n>`) | Worked for most CELEX numbers this session, unlike the interstitial-challenge block `hungarian-document-labels-from-statute.md` hit in full; **three passport amending resolutions** (30 June 1982, 14 July 1986, 10 July 1995) began returning empty/interstitial responses partway through the session and were not independently re-verified here — treated as a residual gap, not a finding, since the earlier research file already read them via the CELLAR mirror. |
| ICAO Doc 9303 Parts 4 and 5, Eighth Edition 2021 | Direct PDF fetch from `icao.int`, read page-by-page (WebFetch does not render embedded images, so pages were read as extracted content) | Worked in full. |

**A general caution on this pass, stated plainly:** four sub-investigations ran as parallel background agents and are synthesized here rather than independently re-verified by a single continuous read. Where a finding rests on one agent's fetch, the citation says so and gives the exact URL, so it can be re-checked. One agent flagged that its tool-results cache briefly returned content it had not itself fetched (from a concurrent sibling agent) and explicitly discarded it — noted here for the same honesty this file's predecessor practiced about its own ceiling, not because it changes any finding below.

---

## 1. PRADO — the existing baseline, unchanged

Recapped from [#47](https://github.com/akosgintl/document-intelligence/issues/47) and `docs/research/hungarian-document-printed-labels.md`, not re-researched here: PRADO (Council of the EU public register of authentic identity and travel documents) specimen images are **© Council of the European Union**, not redistributable, captured only as local MHTML (`docs/prado/`, gitignored), with no image committed to the repository. Nothing found in this pass changes that. PRADO remains the **only source in this whole survey with full-resolution (~600 px / ~175 dpi), Hungary-specific, current-generation specimen imagery for all four document types.** Every alternative found below is either lower-resolution, non-Hungary-specific, generic, or itself restrictively licensed — sometimes all four.

---

## 2. Hungarian government sources

### 2.1 nyilvantarto.hu has migrated and no longer serves content

Fetching `https://nyilvantarto.hu/` returns HTTP 200 with a banner: *"Tájékoztatjuk, hogy a nyilvantarto.hu oldal tartalma átköltözött a kormany.hu oldalra."* ("We inform you that nyilvantarto.hu's content has moved to kormany.hu"), signed IdomSoft Zrt. Every sub-page tested (`/hu/torzskonyv_okmany`, `/hu/utlevel`) now 404s. The ticket's expectation that nyilvantarto.hu is a live specimen source is **out of date**; all searches were re-run against `kormany.hu`.

### 2.2 kormany.hu (current) — procedural text, no specimen images

The four current ügyleírás (procedure-description) pages for személyazonosító igazolvány, útlevél, lakcímkártya and vezetői engedély were fetched directly and their `<img>` tags extracted (not just an LLM summary of rendered content): each contains only the site header/footer logo, **no document specimen imagery at all** — just eligibility, fee and required-document text. No `felhasznalasi-feltetelek` (terms-of-use) page exists at the expected path on the current site (404); the footer links to `kozadatportal.hu`, the general Hungarian PSI/open-data portal, but no page-specific reuse statement was found.

### 2.3 e-egeszsegugy.gov.hu — a genuine MINTA-watermarked specimen, no stated terms

A `.gov.hu`-domain PDF, *"Mi az e-Személyi igazolvány?"* (published by NEAK/EESZT), at
`https://e-egeszsegugy.gov.hu/documents/26398/211405/eSzig/190ca028-b903-7e7a-c4a0-5e81c3cb73d9`,
shows the front of the eSzemélyi (chip eID) card watermarked **"MINTA"** twice — a genuine official specimen graphic in the sense the ticket is after, not a diagram. **No copyright or reuse statement was found in the extracted PDF text or metadata** — only Microsoft Word authoring metadata (author "Rönyai Júlia Anna," created 2017-09-05). Absence of a stated licence is not a licence; treated here as default copyright (all rights reserved) until shown otherwise.

### 2.4 kormany.hu archive — the one explicit government licence found, and it is restrictive

The 2015–2019 kormany.hu archive (BM's site during that period) carries an article on the first chip eID card hand-over, *"Átadták az első elektronikus személyi igazolványt"* (2016-01-11), at
`https://2015-2019.kormany.hu/hu/belugyminiszterium/rendeszeti-allamtitkarsag/hirek/atadtak-az-elso-elektronikus-szemelyi-igazolvanyt`,
with four press photographs (officials handling the card; captions reference "16 biztonsági elemmel védik az új okmányt"). Only 496×330 px thumbnails were reachable; no full-resolution path was found. Each is credited "Fotó: Árvai Károly/kormany.hu".

This is the **one Hungarian government source with an explicit, on-page reuse policy**, at `2015-2019.kormany.hu/hu/felhasznalasi-feltetelek`. Quoted verbatim:

> §3.1.2: "Felhasználó kötelezi magát arra, hogy a honlapról átvett fotókat a következő forrásmegjelöléssel közli: 'fotós neve, kormany.hu'; a fotó képaláírását csak a képpel együtt teszi közzé... a fényképfelvétel(eke)t harmadik fél számára továbbfelhasználásra nem adja tovább, a fényképfelvétel(ek)ből archívumot nem képez... a fényképfelvétel(ek) és a kísérő szöveg(ek) mondanivalóját, tartalmát... **sem retusálással, sem vágással, sem számítógépes beavatkozással... nem változtatja meg.**"

("The user commits to publishing photos taken from the site with the source credit 'photographer's name, kormany.hu'; publishes the photo's caption only together with the photo... does not pass the photograph(s) on to third parties for further use, does not build an archive from the photograph(s)... **does not alter the meaning or content of the photograph(s) and accompanying text(s) — by retouching, cropping, or computer intervention.**")

§3.2 additionally grounds general reuse in Hungary's Copyright Act (1999. évi LXXVI. törvény) "szabad felhasználás" (fair-use) provisions, conditional on attribution and non-commercial purpose, and explicitly bars news-agency-style redistribution.

**This is the opposite of a derivative-use permission — it is an explicit no-modification clause.** It also predates and does not bind the current kormany.hu, where no equivalent page was found at all (§2.2). Even setting that aside, it would not help the fixture use case: it forbids exactly the "computer intervention" a redraw or a crop would be.

### 2.5 Non-government manufacturer specimens — not a government source, restrictively licensed

Two of the consortium members that physically produce Hungarian identity documents publish their own portfolio images, found in the same sweep but **not** BM/nyilvantarto.hu/gov.hu sources and so outside the ticket's ask — noted for completeness, not as a candidate:

- **ANY Security Printing Company** (`any.hu`) — eID card, driving licence and passport-cover portfolio images (e.g. `any.hu/en/portfolio-items/hungarian-electronic-identity-card/`, `.../hungarian-driving-licence/`, `.../passport-sample/`), all low/thumbnail resolution, footer "© 2017-2022 ANY Security Printing Company PLC - All rights reserved."
- **Pénzjegynyomda** (`penzjegynyomda.hu`) — passport security-feature close-ups (microprint, UV, hologram) at higher resolution (~1024×665), no reuse statement found on the image pages themselves (a Terms and Conditions link exists but was not followed).

Both are ordinary third-party commercial copyright, "all rights reserved" or silent — neither is more permissive than PRADO, and using either would face the identical redraw-only constraint.

### 2.6 What went unreached

`bm.hu`'s press room was never loaded (TLS certificate errors on every attempt) — this is a real gap, not a negative finding; BM is the ministry that would announce a passport or licence redesign, and its news section is unverified rather than confirmed empty. A 2010 BÁH (Immigration and Citizenship Office) internal slide deck, `Okmany-mintatar_20101102.ppt`, was found via `kormanyhivatal.hu` but could not be opened with tools available (legacy binary PowerPoint format); string extraction suggests it is about foreign nationals' visas and residence permits rather than the four in-scope document types, but this is unconfirmed.

### 2.7 Hungarian-source resolution record

| Item | Bucket | Basis |
|---|---|---|
| nyilvantarto.hu hosts current specimen imagery | **sourced as false** | Site itself states it migrated; sub-pages 404. |
| kormany.hu (current) hosts specimen imagery | **sourced as false** | Four ügyleírás pages fetched and their `<img>` tags checked directly; only site chrome. |
| A MINTA-watermarked eID specimen exists on a `.gov.hu` domain | **sourced** | `e-egeszsegugy.gov.hu` PDF, watermark observed directly. |
| That specimen carries an explicit reuse licence | **sourced as absent** | No statement found in text or metadata. |
| A Hungarian government press photo carries an explicit reuse licence | **sourced** | `2015-2019.kormany.hu/hu/felhasznalasi-feltetelek`, quoted above — and it is a no-modification clause. |
| bm.hu press room specimen coverage | **unsourced — unreached** | TLS failures throughout; a real gap in this survey. |

---

## 3. EU Official Journal, passport chain — text only, no figure

The uniform-format-passport Resolutions (Resolution of 23 June 1981, OJ C 241, CELEX [41981X0919](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:41981X0919); its consolidation CELEX 01981X0919-19950710; and the amending resolutions of 1982, 1986, 1995 and 2000 already read in full by `hungarian-document-labels-from-statute.md`) were checked specifically for whether the Official Journal publication includes an actual **figure** of the passport data page, distinct from the textual ten-item list already used in that earlier file.

**It does not, anywhere in the chain, and the 1981 base text says why.** Annex I explicitly punts the visual model to ICAO rather than publishing its own: *"The presentation of the laminated page will comply with the model appearing in the draft ICAO recommendation."* Fetched and confirmed directly from the original scanned OJ PDF (`eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:41981X0919`). This is the single sentence that resolves the whole task-1 question: the EU passport Resolutions were never going to contain a competing figure, because they were drafted to defer to ICAO's.

One further instrument, not in the prior research file because it postdates Hungary's accession specifically: the **Resolution of 8 June 2004** (CELEX [42004X1002(01)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:42004X1002(01)), OJ C 245/1, 2.10.2004) extends the 1981 Annex I language list to the ten 2004 accession states, Hungary among them — text-only, one page, no figure.

**Task-1 conclusion: no Council Resolution in the passport chain publishes a layout figure.** ICAO Doc 9303 Part 4 is the only place a figure exists at all (§5 below), and PRADO is the only source with a Hungary-specific rendering of it.

---

## 4. EU Official Journal, driving licence — Directive 2006/126/EC Annex I is figure-bearing

Directive 2006/126/EC, Annex I, "PROVISIONS CONCERNING THE COMMUNITY MODEL DRIVING LICENCE" — CELEX [32006L0126](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32006L0126), fetched from the original scanned OJ PDF, OJ L 403, 30.12.2006, 43 pages. `hungarian-document-labels-from-statute.md` §2.1 already sourced the Directive's *textual* numbered-field list from this Annex; this pass checked for an accompanying image and found two, at OJ L 403/36–37:

1. **"COMMUNITY MODEL DRIVING LICENCE" (L 403/36)** — a line-art structural diagram of both card faces: page 1 shows the rounded-rectangle card outline, the EU-star emblem, "PERMIS DE CONDUIRE / ÉTAT MEMBRE" header, and numbered field placeholders (1, 2, 3, 4a, 4b, 4c, (4d), 5, 7, (8), 9) plus a blank "6 PHOTO" box — structural only, no sample data. Page 2 is a table of category codes (A1, A, B1, B, C1, C, D1, D, BE, C1E, CE, D1E, DE) each paired with a line-drawn vehicle pictogram.
2. **"SPECIMEN MODEL LICENCE — BELGIAN LICENCE (for information)" (L 403/37)** — two complete illustrative front-face cards filled with fictional sample data (names, birthdates, licence numbers, category marks), explicitly marked "(for information)" — i.e. illustrative of one member state's actual implementation, not itself the binding template.

Both are black-and-white scanned line art (visible scan artefacts — an OCR-bled "6c PHOTO" mislabel was noted) but are **layout-accurate**: correct relative field positions matching the Directive's own numbered-item text, correct card proportions. Neither carries any distinct copyright mark beyond the standard OJ page header. A footnote on L 403/36 (*"a pictogram and a line for category AM will be added"*) signals the figure was known to be provisional at publication; whether a later consolidated or amending act redrew it with the AM category is **not confirmed** — EUR-Lex began blocking further fetches before the current consolidated PDF could be checked.

**Task-2 conclusion: yes, a genuine figure exists, and it is layout-accurate for the generic EU model** — but it is Belgian (for the filled specimen) or fully generic (for the blank template), not Hungarian. It corroborates, but does not replace, `hungarian-document-labels-from-statute.md`'s finding (§2.3 there) that the *Hungarian-specific* legend wording — especially for the current `HUN-FO-04001` card, where 326/2011 Annex 5 Part D is stale against the real card — is PRADO-only.

---

## 5. ICAO Doc 9303 — schematic in the body, filled specimens in an appendix, neither Hungary-specific, all copyrighted

ICAO Doc 9303, Eighth Edition 2021, Parts 4 (`9303_p4_cons_en.pdf`, TD3/passport) and 5 (`9303_p5_cons_en.pdf`, TD1/ID card), fetched and read directly.

**Two distinct kinds of figure exist, and they answer different questions:**

- The **main-body figures** (Part 4 Figures 4–10; Part 5 Figures 3 and 5) are pure zone schematics — numbered Zones I–VII with data-element *names*, an unlabelled grey box for the portrait, and dimensional/tolerance callouts. Figure 6 is explicitly titled "Schematic of nominal layout of data elements." No sample data anywhere.
- **Appendix A of each Part** ("Examples of a personalized MRP/TD1 data page (informative)") is a genuine **filled specimen**, using ICAO's standard fictional country "Utopia" (code `UTO`): a complete data page for holder "ERIKSSON, ANNA MARIA" (Part 4) or the TD1 equivalent (Part 5), with a stock model photo, plausible dates, a document number, a signature image, and full MRZ strings.

Neither is Hungary-specific — the whole point of Doc 9303 is a generic international standard, and it explicitly allows "dimensional flexibility" per issuing state (Part 4 Figures 8–10). It confirms, rather than adds to, what the statute-research file already established: Hungary's actual layout may deviate from the ICAO generic template, and PRADO remains the only source of the Hungary-specific rendering.

**Licensing is unambiguous and unfavourable.** Both PDFs' front matter carries identical text:

> "© ICAO 2021. All rights reserved. No part of this publication may be reproduced, stored in a retrieval system or transmitted in any form or by any means, without prior permission in writing from the International Civil Aviation Organization."

ICAO's website copyright policy (`icao.int/pages/copyright.aspx`) repeats the same "all rights reserved... without permission in writing from ICAO" language with no public-domain or free-excerpt carve-out found anywhere. ICAO additionally distributes Doc 9303 PDFs with DRM. **This is the most restrictive licence found in the entire survey** — more restrictive than PRADO, which at least has no stated DRM and is silent rather than affirmatively locked.

---

## 6. The licensing question that decides everything

### 6.1 Commission Decision 2011/833/EU — the operative EU reuse policy

Commission Decision 2011/833/EU of 12 December 2011, CELEX [32011D0833](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011D0833), OJ L 330, 14.12.2011, p. 39, fetched via the Publications Office CELLAR endpoint after `eur-lex.europa.eu`'s own page returned a JS-challenge shell. Verbatim, the articles that matter:

> **Article 4 — General principle**: "All documents shall be available for reuse: (a) for commercial or non-commercial purposes under the conditions laid down in Article 6; (b) without charge, subject to the provisions laid down in Article 9; and (c) without the need to make an individual application, unless otherwise provided in Article 7."
>
> **Article 6 — Conditions for reuse**: "1. Documents shall be made available for reuse without application unless otherwise specified and without restrictions or, where appropriate, an open licence or disclaimer setting out conditions explaining the rights of reusers. 2. Those conditions, which shall not unnecessarily restrict possibilities for reuse, may include the following: (a) the obligation for the reuser to acknowledge the source of the documents; **(b) the obligation not to distort the original meaning or message of the documents**; (c) the non-liability of the Commission..."

Scope (**Article 2**) covers documents "published by the Commission or by the Publications Office on its behalf through publications, websites or dissemination tools" — which reaches the Official Journal as published via EUR-Lex — but excludes "documents covered by industrial property rights such as patents, trademarks, registered designs, logos and names" and third-party-IP content.

**The Decision's own operative text never uses "modify," "adapt," or "derivative."** The closest thing to a modification right is the negative framing of Article 6(2)(b): a condition the Commission *may* impose is that reuse not distort the original meaning — phrasing that presupposes some modification is contemplated, but stops short of affirmatively granting it.

### 6.2 The EUR-Lex legal notice — the explicit derivative-use grant, narrowly scoped

`eur-lex.europa.eu/content/legal-notice/legal-notice.html`, "Copyright notice" section, verbatim:

> "© European Union, 1998-2026. The Commission's document reuse policy is based on Decision 2011/833/EU. Unless otherwise specified, you can re-use the legal documents published in EUR-Lex for commercial or non-commercial purposes. Some documents, like the International Accounting Standards, may be subject to special conditions of use; these are mentioned in the respective Official Journal/document. **The copyright for the editorial content of this website, the summaries of EU legislation and the consolidated texts, which is owned by the EU, is licensed under the Creative Commons Attribution 4.0 International licence. This means that you can re-use the content provided you acknowledge the source and indicate any changes you have made.**"

**This is the one explicit derivative-use permission found anywhere in this survey.** CC BY 4.0 is unambiguous: it permits modification, adaptation, and derivative works, conditioned only on attribution and noting what was changed — "indicate any changes you have made" only makes sense as boilerplate if modification is licensed conduct.

**But its scope is textually narrower than "everything on EUR-Lex."** The sentence names three things: "the editorial content of this website," "the summaries of EU legislation," and "the consolidated texts." It does not say "annexes" or "figures" or "images." The preceding, broader sentence — "you can re-use the legal documents published in EUR-Lex for commercial or non-commercial purposes" — plainly does reach an annex (an annex is part of the legal document), but that sentence tracks the weaker Decision 2011/833/EU wording and carries no explicit modification grant of its own. Whether a bitmap or line-art figure embedded in an Annex counts as part of "the consolidated text" for CC BY 4.0 purposes is **not stated anywhere found**. The legal notice separately confirms only the OJ-published version is authentic — EUR-Lex is the access portal, the underlying document is the Official Journal act, and the reuse permission runs to that content, not merely to the portal's rendering of it.

### 6.3 The Open Data Directive does not apply here

Directive (EU) 2019/1024, Article 1(1): its minimum-rules regime governs "(a) existing documents held by **public sector bodies of the Member States**; (b) existing documents held by public undertakings...; (c) research data." This governs member states' own public-sector bodies (and is the framework any Hungarian PSI reuse would fall under, distinct from §2 above) — **it is not a successor to, and does not supersede, Decision 2011/833/EU for EU-institution-held documents.** No repeal or amendment of 2011/833/EU was found; the current legal-notice page still cites it as the operative basis.

### 6.4 Verdict on derivative use

**Partial and scope-limited, not a clean yes.** Two overlapping texts apply to any EUR-Lex-published figure:

- Decision 2011/833/EU's own articles: permissive on reuse generally (no individual application, free of charge, "for commercial or non-commercial purposes"), but silent on modification beyond the negative "don't distort" condition.
- The EUR-Lex legal notice's CC BY 4.0 clause: explicit modification/derivative-use grant, but textually scoped to "editorial content... summaries... consolidated texts," not expressly extended to annex figures.

A redraw that reproduces an Annex I structural layout with synthetic data does not "distort the original meaning" of a template diagram — arguably satisfying even the stricter reading — but no source found states in so many words that an annexed *figure* may be redrawn. This is a defensible basis for treating the driving-licence Annex I figure as more freely usable than PRADO, not an airtight one.

---

## Source table

| Source | Document type(s) covered | Genuine specimen imagery? | Resolution/fidelity | Stated licence | Permits derivative use? |
|---|---|---|---|---|---|
| PRADO | All four | Yes, Hungary-specific, current generation | ~600 px / ~175 dpi | © Council of the EU, no reuse terms found (#47) | **No** |
| `e-egeszsegugy.gov.hu` PDF | ID card (eID) | Yes, MINTA-watermarked, Hungary-specific | Unassessed (PDF-embedded) | None found | Unsourced — no statement either way; default copyright assumed |
| `2015-2019.kormany.hu` archive press photos | ID card (eID launch) | Event/press photos, not a clean flat scan | 496×330 px thumbnails only | Explicit: attribution required, non-commercial, **modification expressly forbidden** | **No — explicit no-modification clause** |
| `kormany.hu` (current) | — | None found | — | No page-specific statement found | N/A |
| `any.hu` (manufacturer) | ID card, licence, passport cover | Portfolio/promotional images | Thumbnail | "All rights reserved" | **No** |
| `penzjegynyomda.hu` (manufacturer) | Passport security features | Close-up detail images | ~1024×665 | None found | Unsourced — treat as default copyright |
| EU passport Resolutions (1981–2004 chain) | Passport | **None — text only**, defers to ICAO's model | N/A | Decision 2011/833/EU + legal-notice CC BY 4.0, scope-limited per §6 | N/A — no figure exists to reuse |
| Directive 2006/126/EC Annex I (OJ L 403/36–37) | Driving licence | Yes — blank structural template + Belgian filled specimen | Line-art, layout-accurate, not Hungary-specific | Decision 2011/833/EU + legal-notice CC BY 4.0, scope-limited per §6 | **Partial — defensible, not confirmed** |
| ICAO Doc 9303 Part 4 body figures | Passport (TD3) | No — schematic zone diagrams only | N/A | © ICAO 2021, all rights reserved, DRM-protected PDFs | **No** |
| ICAO Doc 9303 Part 4/5 Appendix A | Passport (TD3), ID card (TD1) | Yes — filled specimen, fictional "Utopia" | Generic, not Hungary-specific | © ICAO 2021, all rights reserved | **No** |

---

## Verdict per document type

### Identity card and address card — **PRADO, unchanged**

Both are purely national designs; nothing EU-prescribed exists for either. The one candidate government alternative — the `e-egeszsegugy.gov.hu` MINTA-watermarked eID specimen (§2.3) — has no stated licence at all, which is not better than PRADO's known-restrictive one, only differently uncertain. The one government source with an *explicit* licence (the kormany.hu archive press photos, §2.4) affirmatively forbids modification. Convention 5 stands for both types without qualification.

### Passport — **PRADO, unchanged; no viable alternative exists**

The EU's own uniform-passport instruments never contained a figure — they deferred to ICAO's from the start (§3). ICAO's figure exists (Doc 9303 Part 4 Appendix A) but is generic (fictional "Utopia," not Hungary) and is the single most restrictively licensed source in this whole survey — DRM-protected, all rights reserved, permission required in writing (§5). Nothing found beats PRADO for the passport; convention 5 stands.

### Driving licence — **PRADO for Hungarian content; the EU Annex I figure is the one genuine (if imperfect) opening**

This is the one document type where the map's premise gets tested and partially holds up. Directive 2006/126/EC Annex I publishes an actual layout-accurate figure (§4) under a licensing regime that — unlike PRADO, unlike ICAO, unlike every Hungarian government source found — includes an explicit, on-the-record derivative-use grant (CC BY 4.0, §6.2), even though that grant's reach to an embedded figure specifically is arguable rather than certain (§6.4). Practically: the card's generic structural frame (rounded-rectangle outline, EU star emblem, numbered-field placeholder positions, category pictograms) can be drawn from this figure with a materially better licensing footing than tracing PRADO. It does **not** replace PRADO for the Hungarian-specific legend wording — `hungarian-document-labels-from-statute.md` already established that content is PRADO-only and, for the current card, that the Hungarian decree itself is stale against it. So this is a **partial** reopening of convention 5: the base template's provenance can shift to a more defensibly-licensed EU source; the Hungarian overlay cannot.

---

## What could not be sourced

1. **bm.hu's press room.** TLS errors blocked every attempt; this is the single most likely place a passport or driving-licence redesign would be announced with specimen photos, and it is unverified rather than confirmed empty. A future pass should retry this directly, or via a different fetch path.
2. **Three passport amending resolutions** (30 June 1982, 14 July 1986, 10 July 1995) were not independently re-fetched this session after EUR-Lex began blocking; `hungarian-document-labels-from-statute.md` already read them via the CELLAR mirror and found them textual, and nothing here contradicts that, but this file did not re-verify the absence of a figure in each directly.
3. **Whether a later consolidated or amending version of Directive 2006/126/EC redrew the Annex I figure** with the AM-category pictogram the 2006 original's own footnote flagged as pending. If the figure now committed to reference differs from the one actually fetched, a future pass should pull the current consolidated PDF and compare.
4. **Whether Directive 2006/126/EC or any passport Resolution carries a document-specific special reuse notice** overriding the general EUR-Lex policy — the legal notice itself flags that "some documents... may be subject to special conditions of use... mentioned in the respective Official Journal/document," and this was not checked field-by-field for either instrument.
5. **Whether Hungary's own Copyright Act exemption for official texts** (1999. évi LXXVI. törvény, §1(4), which excludes legislation, official decisions, and official communications from copyright) extends to a specimen document *image* published by a government agency, such as the `e-egeszsegugy.gov.hu` MINTA specimen. Not researched in this pass; the specimen is treated as default-copyrighted for now, which is the conservative reading either way.
6. **The 2010 BÁH `Okmany-mintatar_20101102.ppt`** — legacy binary format, unopenable with the tools available this session. Its actual content (Hungarian ID document specimens vs. foreign visa/permit specimens for border-control training) is unconfirmed.
