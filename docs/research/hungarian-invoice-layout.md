# The layout of a Hungarian invoice: what statute compels, and what issuers actually draw

Researched 2026-08-06 from Hungarian statute and from invoice specimens published by issuers and software vendors, resolving [#67](https://github.com/akosgintl/document-intelligence/issues/67) under the map [#65](https://github.com/akosgintl/document-intelligence/issues/65).

## Why this file exists

`fixtures/catalogue.py` draws the invoice as a flat sequence of `Row("label:", "value")` on a `sheet` geometry. No real invoice looks like that, and #65 recorded it as the largest fidelity gap of the five fixtures. This file is the spec a widened renderer can be written from: which blocks appear, in what order, what captions they print, what is optional.

It is deliberately built the way [#48](https://github.com/akosgintl/document-intelligence/issues/48) built `hungarian-document-labels-from-statute.md`. Every claim below sits in exactly one of three buckets — **sourced**, **inferred**, **unsourced** — because the third bucket is the honest one: it is what the renderer must decide about explicitly rather than silently.

**Scope: page structure, block order and caption wording.** Nothing here supersedes `nav-online-szamla-invoicedata-requirements.md` ([#38](https://github.com/akosgintl/document-intelligence/issues/38)), which settled the *data* an invoice carries and which of it is reportable-but-not-printed. That file answers "what is on an invoice"; this one answers "where".

## Method, and its ceiling

| Source | How reached | Version read |
|---|---|---|
| Nemzeti Jogszabálytár (`njt.jog.gov.hu`) | direct HTTP, full consolidated HTML, converted to text and read | Áfa tv., 23/2014 NGM r., 2013. évi CLXXXVIII. tv., as consolidated 2026-08-06 |
| Kulcs-Soft `Számla (Minta)` | direct PDF, read with `pdftotext -layout` so column geometry survives | undated, invoice data 2008 |
| MEKH/MVM `Villamos energia részszámla` specimen | direct PDF, `pdftotext -layout` | invoice data 2023 |
| Mü-Gu Kft. `MINTA SZÁMLA` supplier template | direct PDF, `pdftotext -layout` | undated |

**The ceiling, stated plainly:**

- **Four specimens is a small sample, and none of the four is from Hungary's two dominant invoicing platforms.** szamlazz.hu and billingo.hu between them issue a large share of Hungarian invoices. Neither publishes a rendered full-page sample this research could fetch — szamlazz.hu's user manual is prose and screenshots of the *entry form*, not of the output; billingo.hu's template pages returned 404/410. So the caption frequencies below are directional, not a survey.
- **One of the four specimens is a legally distinct sub-format.** The MVM specimen is a public-utility invoice, whose layout is prescribed by its own statute (§1.8). It is excellent evidence that a Hungarian invoice *can* look like a real document, and terrible evidence for what a general commercial invoice looks like. It is quoted below for structure and captions, never as a model to copy.
- **One of the four is not an issued invoice at all.** Mü-Gu's `MINTA SZÁMLA` is a "how to invoice us" instruction sheet sent to suppliers, with fill-in ellipses and parenthetical instructions in place of values. Its *block structure* is real evidence of what a buyer expects to receive; its typography is not.
- **The Accounting Act's §167 could not be fetched as primary text.** njt's consolidated page for 2000. évi C. tv. truncated before it in every fetch attempted. §1.7 rests on a near-verbatim secondary reproduction and is bucketed accordingly.

---

## 1. What statute compels about layout

This is the ticket's central question, and it has a sharper answer than #48's equivalent did for identity documents.

### 1.1 The ÁFA Act prescribes data items and never their position

**2007. évi CXXVII. törvény 169. §** ([njt](https://njt.jog.gov.hu/jogszabaly/2007-127-00-00)) opens:

> "**A számla kötelező adattartalma a következő:**
> a) a számla kibocsátásának kelte;
> b) a számla sorszáma, amely a számlát kétséget kizáróan azonosítja;
> c) a termék értékesítőjének, szolgáltatás nyújtójának adószáma, amely alatt a termék értékesítését, szolgáltatás nyújtását teljesítette;
> d) a termék beszerzőjének, szolgáltatás igénybevevőjének … dc) adószámának … első nyolc számjegye …;
> e) a termék értékesítőjének, szolgáltatás nyújtójának, **valamint** a termék beszerzőjének, szolgáltatás igénybevevőjének neve és címe;
> f) az értékesített termék megnevezése, annak jelölésére … vtsz., továbbá mennyisége vagy a nyújtott szolgáltatás megnevezése, annak jelölésére … TESZOR'15, továbbá mennyisége, feltéve, hogy az természetes mértékegységben kifejezhető;
> g) a 163. § (1) bekezdés a) és b) pontjában említett időpont, **ha az eltér a számla kibocsátásának keltétől**;
> h) a „pénzforgalmi elszámolás" kifejezés …;
> i) az adó alapja, továbbá az értékesített termék adó nélküli egységára …, valamint az alkalmazott árengedmény …;
> j) az alkalmazott adó mértéke;
> k) az áthárított adó, kivéve, ha annak feltüntetését e törvény kizárja;
> l) az „önszámlázás" kifejezés …;
> m) adómentesség esetében jogszabályi vagy a Héa-irányelv vonatkozó rendelkezéseire történő hivatkozás vagy bármely más, de egyértelmű utalás …;
> n) a „fordított adózás" kifejezés, ha adófizetésre a termék beszerzője, szolgáltatás igénybevevője kötelezett;
> o) új közlekedési eszköz … esetében … adatok;
> p) a „különbözet szerinti szabályozás – utazási irodák" kifejezés …;
> q) a „különbözet szerinti szabályozás – használt cikkek" … kifejezések közül a megfelelő …;
> r) pénzügyi képviselő alkalmazása esetében a pénzügyi képviselő neve, címe és adószáma."

*(The mandatory data content of an invoice is the following: a) date of issue; b) sequential number uniquely identifying it; c) the seller's tax number; d) the buyer's tax number, or its first eight digits; e) the name and address of the seller and of the buyer; f) the name and quantity of the goods or service; g) the completion date, **if it differs from the date of issue**; h) the phrase "cash accounting" where applicable; i) the tax base, the net unit price and any discount; j) the applied tax rate; k) the passed-on tax; l) the phrase "self-billing"; m) on exemption, a statutory or Directive reference, or any other unambiguous indication; n) the phrase "reverse charge"; o) new-transport-means data; p) the phrase "margin scheme — travel agents"; q) the appropriate margin-scheme phrase; r) fiscal representative details.)*

**Read the grammar, not the list.** Every item is a noun phrase governed by `adattartalma` — content. Not one of the eighteen says *where*. The section never uses a positional verb. There is no "at the top", no "adjacent to", no "in a table", no "grouped", no "in the following order". §169 e) is the tell: it requires the seller's *and* the buyer's name and address in a single lettered item, and says nothing whatsoever about whether they sit side by side, stacked, or scattered.

Two items are worth pulling out for the renderer:

- **§169 g)** requires the completion date **only if it differs from the issue date.** This is the statutory source of `deliveryDate` being nullable, and it means a fixture that omits the row is not incomplete — it is one where the two dates coincide.
- **§169 dc)** now requires the buyer's tax number (first eight digits) on every domestic B2B invoice, with **no monetary threshold.** Older secondary write-ups still quote a 2,000,000 Ft trigger; the consolidated text carries no such clause. The buyer's tax number is not optional decoration on a B2B page.

### 1.2 The one grouping rule in the whole Act — and it is not the ÁFA összesítő

**Áfa tv. 171. §** is the single provision in the Act that constrains how invoice content is *arranged* rather than merely present:

> "A gyűjtőszámlában az összes számlakibocsátásra jogalapot teremtő ügyletet **tételesen, egymástól elkülönítve** úgy kell feltüntetni, hogy az egyes ügyletek adóalapjai – a 169. § j) és m) pontja szerinti **csoportosításban – összesítetten szerepeljenek**."

*(In an aggregate invoice, every transaction giving rise to the invoicing obligation must be shown itemised and separated from one another, such that the tax bases of the individual transactions appear aggregated, grouped according to §169 j) and m).)*

This is a genuine structural requirement: itemised, mutually separated lines, plus an aggregation grouped by applied tax rate (j) and by exemption reference (m). It describes, near enough, a line-item table with an ÁFA összesítő under it.

**But it governs the `gyűjtőszámla` only** — the aggregate invoice covering several transactions in one document. It is not a general rule. A single-transaction invoice is subject to no equivalent, and there is no provision anywhere in the Act requiring a VAT breakdown table on an ordinary invoice. **The ÁFA összesítő is convention, not law**, on every invoice except an aggregate one.

### 1.3 The two remaining near-misses

**Áfa tv. 172. §** — a currency rule that forces two figures onto the page together:

> "A 2. § a) pontja szerinti termékértékesítésről, szolgáltatásnyújtásról kibocsátott számlán az áthárított adót [169. § k) pontja] – a 80. § szerint meghatározott árfolyam alkalmazásával – **forintban kifejezve abban az esetben is fel kell tüntetni, ha az egyéb adatok külföldi pénznemben kifejezettek**."

*(On an invoice for a domestic supply, the passed-on tax must be shown expressed in forint — using the exchange rate under §80 — even where the other data are expressed in a foreign currency.)*

The nearest the Act comes to demanding two representations of one value in proximity. It still does not say where the forint figure goes. Note the asymmetry with `nav-online-szamla-invoicedata-requirements.md` §5.1: the *exchange rate* need not be printed, but the *forint VAT amount* must be.

**Áfa tv. 168/A. § (1)** — a legibility rule, not a layout rule:

> "A számla kibocsátásának időpontjától a számla megőrzésére vonatkozó időszak végéig biztosítani kell a számla eredetének hitelességét, adattartalma sértetlenségét és **olvashatóságát**."

*(From issue until the end of the retention period, the authenticity of origin, integrity of content and legibility of the invoice must be ensured.)*

Legibility is a property of the rendered page, so it constrains a renderer in the loosest possible sense — 4-point type would breach it. It prescribes nothing positional.

### 1.4 Statute forbids one block outright: the signature

**Áfa tv. 177. §:**

> "Törvény a számla adattartalmára további rendelkezéseket is megállapíthat, de a 175. § (2) bekezdésének a) pontjában említett eset kivételével **a számla aláírását nem teheti kötelezővé**."

*(An act may lay down further provisions on invoice content, but — except in the qualified-electronic-signature case of §175(2)(a) — may not make signing the invoice mandatory.)*

This is a rare thing in this research: a **sourced negative**. No Hungarian invoice needs a `Kelt: …… / aláírás` block, and no statute may impose one. A signature or stamp line on a fixture is decorative carry-over from paper practice, and would be an active fidelity error on a software-issued invoice. None of the four specimens examined prints one.

### 1.5 The section literally titled "Megjelenési forma" is about the medium

The Act has a heading — `Megjelenési forma`, "form of appearance" — that promises exactly what this ticket is asking for. **Áfa tv. 174. § (1)** delivers:

> "A számla és a nyugta lehet elektronikus vagy papíralapú."

*(An invoice and a receipt may be electronic or paper-based.)*

That is the whole of it as regards the invoice. The one place the Act uses the word "appearance" is about paper-versus-electronic and nothing else. **Áfa tv. 178. § (2)** adds the language rule, which is worth knowing for a fixture: "Számla magyar nyelven vagy élő idegen nyelven egyaránt kiállítható" — an invoice may be issued in Hungarian or in any living foreign language. Hungarian captions are not compelled either.

### 1.6 23/2014 (VI. 30.) NGM rendelet governs numbering and software, not the page

The ticket named this decree as a candidate source of layout rules. **It contains none.** Fetched in full from [njt](https://njt.jog.gov.hu/jogszabaly/2014-23-20-2X) and searched for every positional term, the decree governs four things and no others:

| Provision | What it governs |
|---|---|
| **3–5. §** | Pre-printed invoice pads (`nyomtatvány`) must be produced by a printing house within a **sorszámtartomány** (serial-number range) pre-assigned to the printer by the tax authority, used "kihagyás és ismétlés nélkül" (without gaps or repeats). |
| **6–7. §** | The seller of a pad must record and invoice it by serial range; the buyer must handle it as `szigorú számadású nyomtatvány` (strict-accounting stationery) with a prescribed register. |
| **8–13/C. §** | Invoicing *software* requirements: continuous gapless numbering, a built-in `"adóhatósági ellenőrzési adatszolgáltatás"` data-export function, and real-time XML transmission to NAV. |
| **14–19. §, annexes** | EDI contract template, and the data structures for handing archived invoices to an audit. |

The word `nyomtatvány` in this decree means the *blank pad as stationery*, controlled by its serial numbers — not a prescribed printed form. **§4 (1)** is the whole of what it says about how a pad is produced:

> "A nyomtatványt az adóhatóság által a nyomtatvány előállítója részére **előre kijelölt sorszámtartományban** folyamatosan, az adott sorszámtartományba illeszkedő sorszám kihagyás és ismétlés nélküli felhasználásával kell előállítani."

*(The pad must be produced continuously within a serial-number range pre-assigned by the tax authority to its producer, using numbers from that range without gaps or repeats.)*

Nothing about columns, boxes, captions or arrangement. **The fixed layout of the invoice pads sold in Hungarian stationers is the printers' own product design, not a regulated form.**

### 1.7 The Accounting Act is why the page says "SZÁMLA" at all

Nothing in the ÁFA Act requires an invoice to be *titled*. §169 b) requires a sequential number; no item requires the word `SZÁMLA` on the page. The requirement comes from the Accounting Act, because an invoice is also a `számviteli bizonylat`.

**2000. évi C. törvény 167. § (1)** lists the general formal and content elements of a voucher directly supporting a bookkeeping entry, beginning:

> "a bizonylat **megnevezése** és sorszáma vagy egyéb más azonosítója"

*(the name of the voucher and its serial number or other identifier)*

**Bucketed carefully: this is a near-verbatim secondary reproduction, not a primary fetch.** njt's consolidated page for the Accounting Act truncated before §167 on every attempt; the wording above is quoted from the Hungarian Academy of Sciences Library's published [`Bizonylati rend és album`](https://www.konyvtar.mta.hu/download/dokumentumok/uvegzseb/bizonylati_rend_es_album.pdf) (§"A bizonylat alaki és tartalmi kellékei"), which reproduces the list under an explicit "A Számviteli törvény 167. §-a értelmében" attribution, and is corroborated by a second independent restatement on Sulinet Tudásbázis. It should be re-checked against a primary text before anything load-bearing rests on the exact words.

The same source records a drafting *principle* rather than a rule: "A bizonylat szerkesztésekor a **világosság elvét** szem előtt kell tartani" — the principle of clarity is to be kept in mind when composing a voucher. That is as close as Hungarian accounting law comes to a layout norm, and it is a principle, not a prescription.

### 1.8 The exception that proves the rule: the public-utility invoice

Hungarian law *is* perfectly capable of prescribing an invoice layout, in exhaustive detail. It does so exactly once, for exactly one class of invoice.

**2013. évi CLXXXVIII. törvény az egységes közszolgáltatói számlaképről** ([njt](https://njt.jog.gov.hu/jogszabaly/2013-188-00-00)) — "on the uniform public-utility invoice appearance". Its preamble states the purpose:

> "…a közüzemi szolgáltatási területeken való egységes, érthető és átlátható számlakép megteremtése érdekében … az … egyetemes szolgáltató, a … elosztó, a távhőszolgáltató, a víziközmű-szolgáltató, a hulladékgazdálkodási és a kéményseprő-ipari közszolgáltató által kibocsátott számlák számlaképének **formai és tartalmi** meghatározására az alábbi törvényt alkotja"

*(…in order to create a uniform, comprehensible and transparent invoice appearance in the public-utility service areas … Parliament enacts the following law for the determination of the **formal and content** requirements of the invoice appearance of invoices issued by the universal electricity and gas supplier, the network operators, the district-heating supplier, the water utility, and the waste-management and chimney-sweeping public service providers.)*

Twelve annexes each carry, for one utility and one invoice type, **an embedded image of the prescribed page** ("2. A részszámla első oldala: …", "3. A részszámla harmadik oldala: …") followed by a numbered `Magyarázat` explaining each element. And **8. § (1)** goes further than any layout spec this research expected to find anywhere:

> "Az 1–12. mellékletekben meghatározott adatokat a szolgáltató az ott meghatározott **elrendezésben, Times New Roman betűtípussal, a címzést Arial betűtípussal** köteles feltüntetni. A számlák első oldalán, színes mezőben szereplő adatokat **11 pontos betűmérettel** kell feltüntetni. A számlában szereplő további adatokat a szolgáltató jól olvashatóan … **minimum 8 pontos betűmérettel** köteles szerepeltetni. A betűméret megválasztása és az adatok kitöltése nem járhat **a számlakép elrendezésének sérelmével**."

*(The provider must show the data specified in Annexes 1–12 **in the arrangement specified there, in Times New Roman, with the addressing in Arial**. Data in the coloured field on the first page must be set in **11 point**. Further data must be legible, at **minimum 8 point**. The choice of font size and the filling-in of data must not prejudice **the arrangement of the invoice image**.)*

**8. § (5)** then fixes the page-one panel colour per utility by hex and Pantone: electricity `#FF7F50` (coral), gas `#FF8C00`, district heating `#DDA0DD`, water `#00FFFF`, waste `#32CD32`. **8. § (4)** permits deviation from the annex's row heights and column widths only "a számlakép elrendezésének sérelme nélkül".

So: **typeface, point size, hex colour, and a picture of the page.** This matters to #67 in two ways. It settles beyond argument that the silence of the ÁFA Act is deliberate rather than an accident of drafting — when the legislature wants a layout, it writes one. And it rules the MVM specimen out as a model: its structure is a statutory artefact of a sub-format that a general commercial invoice fixture must not imitate.

### 1.9 Layout resolution record

| Item | Bucket | Basis |
|---|---|---|
| The invoice's data-item set | **sourced** | Áfa tv. 169. §, eighteen lettered items. |
| Delivery date required only when it differs from the issue date | **sourced** | Áfa tv. 169. § g). |
| Buyer tax number on domestic B2B, no monetary threshold | **sourced** | Áfa tv. 169. § d) dc), consolidated text. |
| **Position of any block on the page** | **sourced as absent** | Áfa tv. 169. § is exhaustively a content list; no positional verb appears in it, and 174. § "Megjelenési forma" addresses only paper-vs-electronic. |
| Itemised, mutually separated lines + aggregation grouped by rate | **sourced, but only for the `gyűjtőszámla`** | Áfa tv. 171. §. No equivalent exists for an ordinary invoice. |
| A VAT summary table on an ordinary invoice | **unsourced** | No provision requires one. Convention only. |
| Seller and buyer boxes side by side | **unsourced** | Áfa tv. 169. § e) names both parties in one item and says nothing about arrangement. |
| Forint VAT figure alongside foreign-currency amounts | **sourced** | Áfa tv. 172. §. |
| Legibility of the rendered page | **sourced** | Áfa tv. 168/A. § (1). |
| **A signature or stamp block** | **sourced as forbidden-to-mandate** | Áfa tv. 177. §. Absent from all four specimens. |
| Hungarian-language captions | **sourced as optional** | Áfa tv. 178. § (2): any living language is permitted. |
| Numbering ranges, strict-accounting stationery, software data export | **sourced** | 23/2014 NGM r. 3–13/C. § — and this is the decree's *entire* subject matter. |
| **Any layout rule in 23/2014 NGM r.** | **sourced as absent** | Full text fetched and searched; the decree never addresses the printed page's appearance. |
| The printed title `SZÁMLA` | **sourced via secondary reproduction** | Szvt. 167. § (1) "a bizonylat megnevezése és sorszáma". Primary fetch failed; see §1.7. |
| Layout prescribed by statute for **public-utility** invoices | **sourced** | 2013. évi CLXXXVIII. tv. 8. § and Annexes 1–12: arrangement, typeface, point size, hex colour. **Out of scope for this fixture.** |
| Caption *wording* for any block | **unsourced** | No instrument prescribes any invoice caption. Exactly as #48 found for identity documents. |

**The verdict the ticket asked for: for a general commercial invoice, Hungarian statute constrains layout not at all.** It fixes the data items, one grouping rule for aggregate invoices, a currency-pairing rule, a legibility duty, a required document name, and a prohibition on compelling a signature. Everything else on the page — the header block, the side-by-side party boxes, the column order, the VAT summary table, the totals block, the footer — is issuer convention with no legal basis whatsoever.

---

## 2. The observed skeleton

Reading order, top to bottom. Every block is marked with how well the four specimens corroborate it. **Nothing in this section is sourced** in the #48 sense — no statute prescribes any of it — so the column records evidential weight instead.

| # | Block | Corroboration |
|---|---|---|
| 1 | **Title + issuer identity band.** The word `SZÁMLA` set large, plus the issuer's logo or name. | 3 of 3 commercial specimens print a title. Title/logo *placement* varies: Kulcs-Soft sets the title top-left with the trading name in the seller box; MVM leads with the invoice type and puts the logo top-right; Mü-Gu centres `SZÁMLA` alone. |
| 2 | **Invoice number**, near the title and usually flush right. | Kulcs-Soft prints `Sorszám 6/2008` right-aligned on the title line. MVM prints `Számla sorszáma:` inside the top-right identity stack. Mü-Gu prints it as the first row of a metadata list. **Position varies; proximity to the title does not.** |
| 3 | **Seller box and buyer box, side by side.** Two columns of the same band, seller left, buyer right. | 2 of 2 specimens that draw party boxes at all (Kulcs-Soft `Szállító`/`Vevő`; Mü-Gu `eladó:`/`vevő:`) put them side by side, seller left. This is the single best-corroborated structural claim in this file and the sharpest departure from the current fixture. |
| 4 | **Metadata band** — payment method, the dates, currency. | Present in all three commercial specimens, but **its position relative to the party boxes flips**: Kulcs-Soft puts it *below* the boxes as a four-column strip; Mü-Gu puts it *above* them as a stacked list. Treat the ordering of blocks 3 and 4 as a free choice. |
| 5 | **Line-item table.** One row per item, description first, amounts right-aligned. | 3 of 3. A description column, a quantity, a unit price and a net amount appear in every one. |
| 5a | *Free-text sub-description under an item row*, in smaller type. | Kulcs-Soft (twice), MVM (as asterisked footnotes). Optional, but it is what makes an item table look real rather than generated. |
| 6 | **Per-block subtotal rows inside the item table**, before the summary. | MVM (`Energiadíj összesen`, `Rendszerhasználati díjak összesen`, `Nettó számlaérték összesen`). A utility-invoice trait; do not generalise. |
| 7 | **VAT summary table (`ÁFA összesítő`), visually separate from the item table.** One row per rate, plus a total row. | 2 of 2 specimens that carry amounts at all. Both set it as a distinct bordered table, right-aligned on the page, narrower than the item table. **Only MVM captions it**; Kulcs-Soft's is a bare table with column headers and no heading. |
| 8 | **Totals block** — the single bold payable figure. | 3 of 3. Kulcs-Soft and MVM both make it the last figure before the footer. |
| 8a | *The amount spelled out in words*, immediately under the total. | Kulcs-Soft: `azaz Kilencvenhatezer-háromszázhatvan Forint.` A carry-over from cheque-era paper practice with no legal basis; still printed. Optional. |
| 9 | **Footer** — software attribution, legal citation, courtesy line, payment-terms note. | Kulcs-Soft prints all four. Mü-Gu's footer is procedural instruction (it is a supplier brief, not an issued invoice). Content is entirely issuer-chosen. |

Two structural facts worth stating explicitly for the renderer:

- **The item table and the VAT summary are different widths.** In both specimens that draw them, the item table spans the full text block and the summary is a narrower table pushed to the right margin, beneath it. Drawing them as two equal-width tables — as the current fixture effectively does — is the specific thing that makes the page read as generated.
- **The reverse-charge / exemption phrase is a free-standing block, not a column value.** Mü-Gu prints `FORDÍTOTT ADÓZÁS, AZ ÁFA MEGFIZETÉSÉRE A VEVŐ KÖTELEZETT` centred and emphasised between the item table and the totals. The current fixture puts `fordított adózás` in a `vatRate` cell — legitimate, and defended in `catalogue.py`, but not the only way real invoices carry the §169 n) phrase.

---

## 3. Caption wording, by source

Nothing here is sourced to statute; every wording is one issuer's choice, and the columns disagree often enough to make that plain.

### 3.1 Metadata band

| Concept | Kulcs-Soft | MVM (utility) | Mü-Gu |
|---|---|---|---|
| Invoice number | `Sorszám` | `Számla sorszáma:` | `Számla száma:` |
| Issue date | `Számla kelte` | `Számla kelte` | `Számla kelte` |
| Completion date | `Teljesítés időpontja` | `Teljesítés kelte` | `Teljesítés dátuma` |
| Payment due date | `Esedékesség` | `Fizetési határidő:` | `Fizetési határidő:` |
| Payment method | `Fizetési mód` | — | `Fizetési mód:` |
| Bank account | *(in seller box)* | `Bankszámla száma:` | `Bankszámla-szám:` |

`Számla kelte` is the one caption all three agree on. `Esedékesség` versus `Fizetési határidő` for the same date, and three different words for the completion date, are real divergence — the current fixture's `Kiállítás kelte:` matches none of the three, which is a defensible choice but worth knowing is not what any of these specimens print.

### 3.2 Party boxes

| Role | Kulcs-Soft | MVM (utility) | Mü-Gu |
|---|---|---|---|
| Seller | `Szállító` | `Szolgáltató neve:` / `Címe:` / `Adószáma:` | `eladó:` |
| Buyer | `Vevő` | `Vevő (Fizető) neve:` / `címe:` / `azonosító:` | `vevő:` |

`Vevő` is unanimous for the buyer, as a bare box header or as the stem of a field caption. The seller has **three different words across three specimens** — `Szállító`, `Szolgáltató`, `eladó` — and the fixture's `Eladó:` is a fourth-in-spirit but attested variant (Mü-Gu, lowercased). A renderer must simply pick one; nothing constrains it.

### 3.3 Line-item table columns

| Kulcs-Soft (in printed order) | MVM (utility) | Mü-Gu |
|---|---|---|
| `Megnevezés` | `Tétel megnevezése` | `megnevezés és egyéb jellemzők` |
| `VTSZ/SZJ` | `Fogyasztási időszak` | *(VTSZ inside the description cell)* |
| `Súly` | `Mennyiség` | `ÁFA kulcsa` |
| `Mennyiség` | `Mérték-egység` | `menny. egység` |
| `Mee` | `Nettó egységár és mértékegysége` | `mennyiség` |
| `Egységár` | `Nettó érték (Ft)` | `egységár` |
| `Nettó` | `ÁFA (%)` | `nettó érték` |
| `Áfa %` | `Bruttó érték (Ft)` | |
| `Áfaérték` | | |
| `Bruttó` | | |

Corroborated across all three: **description first, then quantity and unit, then unit price, then net, then VAT, then gross.** That ordering is the stable skeleton. Everything else varies — the abbreviation `Mee` for `mértékegység` is Kulcs-Soft's alone, a `VTSZ/SZJ` classification column appears on one specimen and inside the description cell on another, and `Áfaérték` versus `ÁFA (Ft)` versus no VAT-amount column at all are three attested treatments.

### 3.4 VAT summary and totals

Kulcs-Soft's summary table, uncaptioned: `Áfa %` | `Nettó` | `ÁFA` | `Bruttó`, closing row `Összesen`.
MVM's, captioned `ÁFA összesítő (Ft)`: `Tétel megnevezése` | `ÁFA (%)` | `Nettó érték (Ft)` | `ÁFA (Ft)` | `Bruttó érték (Ft)`, closing row `Számla összesen:`.

For the payable total, three specimens give **three different captions** for the same figure:

| Caption | Source |
|---|---|
| `Fizetendő végösszeg:` | Kulcs-Soft |
| `Fizetendő összeg:` | MVM (printed twice — once in the page-one summary box, once as the item table's last row) |
| `BRUTTÓ ÉRTÉK:` | Mü-Gu |

The current fixture prints `Fizetendő összeg:`, which is attested. `Fizetendő végösszeg:` is equally attested. Note that neither `Áfa kulcsonkénti összesítő` nor `Áfa bontás` — plausible alternative wordings for the summary caption — was found on any specimen reached; they are **not confirmed**, which is not the same as wrong.

---

## 4. Which printed blocks map onto Fields

| Printed block | Fields of `schemas/invoice/v2.json` |
|---|---|
| Title band | *(none — see §5)* |
| Invoice number | `invoiceNumber` |
| Metadata band | `invoiceDate`, `deliveryDate`, `paymentDueDate`, `paymentMethod`, `currency` |
| Seller box | `sellerName`, `sellerTaxNumber`, `sellerAddress`, `sellerBankAccountNumber` |
| Buyer box | `buyerName`, `buyerTaxNumber`, `buyerAddress` |
| Line-item table | `lineItems[]` — all eight nested properties |
| VAT summary table | `vatSummary[]` — `vatRate`, `netAmount`, `vatAmount`, `grossAmount` |
| Totals block | `netTotal`, `vatTotal`, `grossTotal` |
| Footer | *(none — see §5)* |

The mapping is clean, and that is the point: **every Field has a home, and roughly a third of the page has no Field.** The Schema was designed against NAV's reportable data set (#38), which is a subset of what the page shows.

---

## 5. Printed blocks no Field captures

These must still be drawn, or the page does not read as an invoice. Each is listed with what compels it, if anything.

| Block | Status |
|---|---|
| **The `SZÁMLA` title itself** | Required as a *voucher name* by Szvt. 167. § (1) (§1.7), and printed by every specimen. No Field. The fixture already draws it via `Face.title`, which is the right place. |
| **`EGYSZERŰSÍTETT SZÁMLA` as the title variant** | See §6. No Field distinguishes a simplified invoice from a normal one — by design, per `catalogue.py`'s note on #43 — so the title carries a fact the extracted Document cannot represent. |
| **Issuer logo / graphic identity** | Universal in practice, compelled by nothing. |
| **The §169 h)/l)/n)/m)/p)/q) statutory phrases as a free-standing block** | `fordított adózás`, `önszámlázás`, `pénzforgalmi elszámolás`, the margin-scheme phrases, and an exemption's statutory reference. **Sourced as mandatory content** (Áfa tv. 169.), conditionally on the transaction. `vatRate` can carry them per line, but a page-level block is equally real and has no Field. |
| **The amount spelled out in words** | `azaz … Forint.` — Kulcs-Soft. No legal basis, still printed. |
| **Software attribution footer** | `Ez a számla a … rendszerével készült` — Kulcs-Soft. Compelled by nothing; near-universal on software-issued invoices, and a strong realism cue. |
| **A legal-compliance citation in the footer** | Kulcs-Soft prints `A számla a 47/2007. (XII.29.) PM rendeletnek megfelel.` — a citation to the **pre-2014 regime**: 47/2007 was an amending decree of 24/1995. (XI. 22.) PM r., which 23/2014 NGM r. repealed from 1 July 2014. The *practice* of citing a decree in the footer is real; that specific string is stale, and a fixture copying it verbatim would be drawing a document that could not be issued today. |
| **Copy/original marking** | `Az eredeti bizonylat másolata, csak tájékoztatásra!` (Kulcs-Soft), `1. sz. eredeti példány` (MVM), `MIN. 3 PÉLDÁNYOS, az 1. példány a vevőé` (Mü-Gu). Three of three. No Field. |
| **Page numbering** | `Oldalszám: 1/4` (MVM), `Oldal 1 / 2` (Mü-Gu). Needed the moment a fixture spans more than one page. |
| **Courtesy and terms boilerplate** | `Köszönjük a vásárlást!`, late-payment interest clauses — Kulcs-Soft. |
| **Exchange rate line** | Mü-Gu's template reserves `ÁRFOLYAM (csak devizás számla esetén kell feltüntetni)`. `nav-online-szamla-invoicedata-requirements.md` §5.1 established the rate is **not** required invoice content, and #38 deliberately gave it no Field. Confirmed here as a block issuers nonetheless reserve space for. |
| **The forint VAT figure on a foreign-currency invoice** | **Sourced as mandatory** (Áfa tv. 172. §) and has no Field — `vatTotal` is defined as being in the invoice's own `currency`. A EUR-denominated Hungarian invoice must print a forint VAT amount that the Schema cannot hold. Worth flagging to whoever revisits the Schema; out of scope to fix here. |
| **VTSZ / TESZOR classification codes per line** | Kulcs-Soft draws a whole column for it; §169 f) makes it the issuer's option. No nested Field. |
| **Seller's legal-status markings** | `e.v.` for a sole trader, `kisadózó` where applicable. Reported by the parallel survey from a Billingo infographic; **not observed on any specimen this research fetched directly**, so single-sourced and second-hand. |
| **Signature / stamp area** | **Sourced as not required** (Áfa tv. 177. §) and absent from all four specimens. Listed here so the renderer explicitly decides *not* to draw one. |
| **QR code** | Looked for; **not found on any specimen reached.** Do not invent one. |

---

## 6. The egyszerűsített számla

The simplified invoice differs from a normal one by a **sourced content rule**, and that rule is unusually precise — it is the one place statute tells a renderer what it may *not* print.

**Áfa tv. 176. § (1)** lists when simplified content is permitted, including — the case the committed fixture uses — **(1) d)**:

> "a számla adóval növelt végösszege nem haladja meg a **100 eurónak megfelelő pénzösszeget**, feltéve, hogy a számlakibocsátásra jogalapot teremtő ügylet a 29. § vagy a 89. § szerinti termékértékesítéstől eltérő ügylet…"

*(the invoice's VAT-inclusive total does not exceed the forint equivalent of 100 euros, provided the transaction is other than a §29 or §89 supply…)*

Note the threshold is **100 EUR in the consolidated text.** Secondary write-ups still circulating quote 25,000 Ft; that figure is stale. Paragraph (1) e) separately permits simplified content for a seller under `alanyi adómentesség` (AAM).

**Áfa tv. 176. § (2) a)** is the operative rule:

> "…a 169. §-ban felsorolt adatok közül **az i) pontban megjelölt helyett az ellenérték adót is tartalmazó összege**, valamint **a j) pontban megjelölt helyett az alkalmazott adómértéknek megfelelő, a 83. § szerint meghatározott százalékérték** feltüntetése kötelező azzal, hogy egyúttal **a k) pontban megjelölt adat nem tüntethető fel**"

*(…in place of the item under (i) [tax base and net unit price], the VAT-inclusive amount of the consideration, and in place of the item under (j) [applied tax rate], the percentage determined under §83 corresponding to the applied rate, are mandatory — and at the same time the item under (k) [the passed-on tax] **may not be shown**.)*

Three consequences, all sourced:

1. **Amounts are gross.** The net tax base and the net unit price are *replaced*, not supplemented.
2. **The rate is replaced by a VAT-content percentage.** **Áfa tv. 83. §** fixes the values: `a) … 21,26 százalékot` for the 27% rate, `b) … 4,76 százalékot` for 5%, `c) … 15,25 százalékot` for 18%, `d) … 0 százalékot` for the 0% rate. This is the statutory source of the fixture's `21,26%` and of the Schema's insistence that `vatRate` stay a verbatim string rather than an enum.
3. **The VAT amount is forbidden.** `nem tüntethető fel` — may not be shown. A simplified invoice printing a VAT amount column is not merely unconventional; it is non-compliant. This is a stronger fact than the Schema currently expresses: `lineItems[].vatAmount` and `vatSummary[].vatAmount` being null on a simplified invoice is not "the invoice happens not to print it" but "the invoice may not print it".

**Layout consequences, which are inferred rather than sourced** — no instrument prescribes them, they follow from the content rule plus the specimens:

- The item table loses its `Nettó` and `ÁFA összeg` columns and gains `ÁFA tartalom` and `Bruttó`. The committed fixture already does exactly this.
- The `ÁFA összesítő` collapses. With no net and no VAT amount, a per-rate breakdown has only a gross column left, and issuers commonly drop the table entirely — which is what the committed fixture does, and it remains the only fixture asserting `vatSummary` null as a whole.
- The buyer box is frequently absent. Legitimate at a retail counter, and the source of three null buyer Fields. *(Corroboration: reported second-hand from a Billingo infographic labelling the buyer block `esetleg a vevő neve és címe` — "possibly the buyer's name and address". Not directly observed by this research; single-sourced.)*
- The totals block reduces to one line, since a net total and a VAT total cannot exist.

**One correction to the committed fixture, offered rather than applied.** `_INVOICE_SIMPLIFIED` prints `Megjegyzés: Áfa tv. 176. § szerinti egyszerűsített adattartalmú számla` and its comment asserts a real one "cites Áfa tv. 176. §". Nothing in §176 requires that citation, and none of the four specimens prints anything comparable. The document *is* a §176(1)(d) invoice — its 8 140 Ft total is well under 100 EUR — but the printed citation is the fixture's own invention, not observed practice. It is harmless, and it gives the page a `Megjegyzés` block that real invoices do carry; it should just not be described as something real invoices do.

---

## Conflicts, presented rather than resolved

| # | Subject | One source says | Another says | Note |
|---|---|---|---|---|
| 1 | Position of the metadata band | Kulcs-Soft: below the party boxes | Mü-Gu: above them | Both real. The renderer must choose; nothing constrains it. |
| 2 | Caption for the payment due date | Kulcs-Soft: `Esedékesség` | MVM, Mü-Gu: `Fizetési határidő` | Same date, different word. |
| 3 | Caption for the seller box | `Szállító` / `Szolgáltató` / `eladó` | — | Three specimens, three words. `Vevő` by contrast is unanimous. |
| 4 | Whether the VAT summary is captioned | MVM: `ÁFA összesítő (Ft)` | Kulcs-Soft: no heading at all | The block is visually distinct either way. `catalogue.py` already captions the happy-path one and argues for it; that argument survives, as a choice rather than a requirement. |
| 5 | Simplified-invoice threshold | Áfa tv. 176. § (1) d) consolidated: **100 EUR** equivalent | secondary write-ups still in circulation: 25 000 Ft | The consolidated primary text governs. |
| 6 | Footer legal citation | Kulcs-Soft prints compliance with `47/2007. (XII.29.) PM rendelet` | That decree amended 24/1995. (XI. 22.) PM r., which 23/2014 NGM r. repealed from 2014-07-01 | The *practice* is real; the *string* is stale. Do not copy it verbatim. |

---

## What could not be sourced

The honest residue — what the renderer must decide about explicitly, because nothing constrains it:

1. **Every caption on a general commercial invoice.** Exactly as #48 found for identity documents: Hungarian statute prescribes data items and, occasionally, a rendering rule, and never caption wording. The specimens are the only source, and they disagree with one another on the seller box, the due date and the completion date.
2. **Every block's position.** Confirmed as a sourced absence for the ÁFA Act and 23/2014 NGM r. (§1.9), which is a stronger statement than "not found" — both were fetched in full and searched.
3. **Whether the seller box goes left or right.** Two specimens put the seller left; two is not a survey. Nothing legal bears on it.
4. **Date formats.** Kulcs-Soft prints `2008.06.09.`, MVM prints `2023.08.21.`, the committed fixture prints `2026.07.01` without the trailing dot. No instrument governs the format on an invoice, unlike the driving licence's verso.
5. **The two dominant issuers' actual output.** szamlazz.hu and billingo.hu could not be made to yield a rendered full-page sample. Until one is obtained, every frequency claim here rests on three commercial specimens, one of which is a supplier brief rather than an issued invoice. **This is the gap a future pass should close first**, and #65 already contemplates a provider-issued PDF as one of the two ways the invoice half can end.
6. **Typography.** No general invoice statute names a typeface or a point size. The one Hungarian instrument that does — 2013. évi CLXXXVIII. tv. 8. § — governs a sub-format this fixture must not imitate, and #65 already records the typeface question as unresolved pending the redraw prototype.
