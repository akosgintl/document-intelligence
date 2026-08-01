# NAV Online Számla `invoiceData` schema requirements, for extraction-schema design

**Scope.** This document researches what Hungary's NAV Online Számla real-time e-invoice reporting system requires in its `invoiceData` XML schema (currently namespace version 3.0), to the extent it should shape what a scanned/PDF-invoice extraction Schema (`schemas/invoice/v2.json`, redesigning `schemas/invoice/v1.json` per ADR-0007's append-only versioning rule) needs to capture. It covers mandatory header-level fields, line-item fields, VAT summary/aggregation fields, and — the specific question this ticket asks — which of NAV's required fields would actually be visible on a rendered invoice document versus which exist only for the electronic submission itself. This is GitHub issue #38, a research ticket under the Wayfinder map for issue #33 ("Design Hungarian ID/passport/driving licence + NAV-compatible invoice schemas").

**Sources used, and which are primary vs. secondary:**

- **Primary — NAV's own published XSD schema files**, fetched directly from `nav-gov-hu/Online-Invoice` on GitHub, which the repository's own README identifies as "Public repository of the Online Invoice System" and links as the source for schema definitions, example XMLs, and descriptions of the invoice-reporting M2M interface (the same schemas published under `onlineszamla.nav.gov.hu`). Files fetched by raw content and inspected directly (not summarized by an intermediary model) via `curl`, then grepped/read line-by-line for exact element names, `minOccurs` cardinality, and bilingual (`hu`/`en`) `xs:documentation` annotations:
  - [`invoiceData.xsd`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd) — the invoice content schema itself (target namespace `http://schemas.nav.gov.hu/OSA/3.0/data`).
  - [`invoiceBase.xsd`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceBase.xsd) — shared base types (`TaxNumberType`, `InvoiceDateType`, `PaymentMethodType`, `InvoiceCategoryType`, `InvoiceAppearanceType`).
  - [`invoiceApi.xsd`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceApi.xsd) — the submission/reporting wrapper (distinct from the invoice content itself).
  - [`CHANGELOG_3.0.md`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/CHANGELOG_3.0.md) — version-3.0 change history.
- **Primary — NAV's own published interface specification PDF**, hosted on NAV's own domain: `Online_Szamla_interfesz specifikáció_HU_v3.0.pdf`, fetched from `onlineszamla-test.nav.gov.hu` (NAV's official test-system domain) and converted to text locally for exact-quote searching (the file is genuinely NAV's document — the same PDF the `nav-gov-hu/Online-Invoice` GitHub README itself links as "Aktuális API dokumentáció" / "current API documentation"). This is a large (27,000+ line) Hungarian-language technical document; only the sections relevant to this ticket's questions were located and quoted, not read cover to cover.
- **Secondary, explicitly flagged as such, not fetched in full**: search-result snippets suggesting the accompanying interface-specification *document* (as opposed to the XSD schema itself) carries its own, more granular revision counter separate from the XSD's namespace version, observed in 2026 search snippets as high as "3.44.3," and a separate mention of a "NAV XML schema 4.0" tied to a 2026 mandatory e-invoicing article. Neither of these was confirmed against a fetched primary source — see §6.

Every claim below is either a direct quote/close paraphrase of fetched primary-source content with a citation, or is explicitly marked as **not confirmed by a fetched primary source**.

---

## Summary of findings

| Question | Finding |
|---|---|
| Is v3.0 still the current `invoiceData` XSD? | **Confirmed** — the fetched XSD's target namespace is `http://schemas.nav.gov.hu/OSA/3.0/data`, unchanged since the CHANGELOG's Nov 2020 introduction; no successor major schema version was found in any fetched primary source. A separate, unconfirmed revision counter for the *specification document* (not the schema) was seen in secondary search snippets — see §6. |
| Are NAV's mandatory reporting fields generally the same as the invoice's own legally mandatory content? | **Confirmed, with named exceptions.** The spec states data reporting is mandatory chiefly for what the VAT Act already requires to appear on the invoice — but explicitly carves out exceptions, the clearest being the exchange rate (§5). |
| Hungarian tax number (adószám) format | **Confirmed, with exact regex.** Structured as `taxpayerId` (`[0-9]{8}`) + `vatCode` (`[1-5]{1}`) + `countyCode` (`[0-9]{2}`) — i.e. the familiar `12345678-1-42` hyphenated form, all three components sourced from the fetched XSD and the fetched PDF's field-facet table. |
| Is exchange rate printed on the invoice? | **Confirmed not required to be.** The spec states verbatim that the exchange rate "is not mandatory content of the invoice" but "is a mandatory element of the data exchange" as of Jan 4, 2021 (§5). |
| Is `completenessIndicator` visible on an invoice? | **Confirmed no** — it is a submission-only boolean describing the *data exchange itself* ("does this XML equal the invoice"), not invoice content (§5). |
| Line items: are quantity/unit/unit price always present? | **Confirmed optional at the schema level** (`minOccurs="0"` in the fetched XSD) — NAV's schema tolerates lump-sum service lines without a stated quantity or unit price, while net amount and VAT rate remain mandatory per line (§3). |
| VAT summary structure | **Confirmed**: per-VAT-rate net/VAT/gross subtotals (`SummaryByVatRateType`), plus invoice-wide net/VAT/gross totals, both in invoice currency and in HUF when the invoice currency isn't HUF (§4). |

---

## 1. Header-level mandatory fields

### 1.1 Invoice number and issue date

Both are direct children of the top-level `InvoiceDataType`, not nested under `invoiceHead`, and both are mandatory (no `minOccurs="0"`):

```xml
<xs:element name="invoiceNumber" type="common:SimpleText50NotBlankType">
  <!-- en: "Sequential number of the original invoice or modification document -
       section 169 (b) or section 170 (1) b) of the VAT law" -->
<xs:element name="invoiceIssueDate" type="base:InvoiceDateType">
  <!-- en: "Date of issue of the invoice or the modification document -
       section 169 (a) of the VAT law, section 170 (1) a) of the VAT law" -->
```
[`invoiceData.xsd`, `InvoiceDataType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

`InvoiceDateType` (in `invoiceBase.xsd`) is a restriction of `xs:date`, pattern `\d{4}-\d{2}-\d{2}` (ISO `YYYY-MM-DD`), with a documented minimum value of `2010-01-01`.

Both correspond directly to what the VAT Act requires printed on the invoice itself (§169(a), §169(b)) — these are unambiguously extractable from a rendered document.

### 1.2 Delivery/completion date (teljesítés dátuma)

Mandatory, inside `InvoiceHeadType/invoiceDetail` (`InvoiceDetailType`):

```xml
<xs:element name="invoiceDeliveryDate" type="base:InvoiceDateType">
  <!-- en: "Delivery date (if this field does not exist on the invoice, the date of
       the invoice should be considered as such) - section 169 (g) of the VAT law" -->
```
[`invoiceData.xsd`, `InvoiceDetailType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

The annotation itself tells us this field is often *absent* from the printed invoice — NAV's own schema defaults it to the issue date when not separately stated. Two further optional fields, `invoiceDeliveryPeriodStart`/`invoiceDeliveryPeriodEnd`, exist for period-billed invoices (e.g. subscriptions/utilities) and `invoiceAccountingDeliveryDate` for a distinct accounting-performance date, both `minOccurs="0"`.

### 1.3 Payment due date and payment method

Both optional at schema level (`minOccurs="0"`), inside `InvoiceDetailType`:

```xml
<xs:element name="paymentMethod" type="base:PaymentMethodType" minOccurs="0">
  <!-- en: "Method of payment" -->
<xs:element name="paymentDate" type="base:InvoiceDateType" minOccurs="0">
  <!-- en: "Deadline for payment" -->
```
[`invoiceData.xsd`, `InvoiceDetailType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

`PaymentMethodType` enumeration (`invoiceBase.xsd`, confirmed identically in the fetched interface-spec PDF §2.3.9, "PaymentMethodType (Fizetés módja típus)"):

| Value | Hungarian label | English label |
|---|---|---|
| `TRANSFER` | Átutalás | Bank transfer |
| `CASH` | Készpénz | Cash |
| `CARD` | Bankkártya, hitelkártya, egyéb készpénz helyettesítő eszköz | Debit/credit card, other cash-substitute instrument |
| `VOUCHER` | Utalvány, váltó, egyéb pénzhelyettesítő eszköz | Voucher, bill of exchange, other non-cash instrument |
| `OTHER` | Egyéb | Other |

Both fields are optional in the schema because they are only invoice content when the underlying fact is stated on the invoice — consistent with the spec's general rule (§5 below) that some legally-mandatory-when-applicable fields are conditionally required.

### 1.4 Currency and exchange rate

```xml
<xs:element name="currencyCode" type="common:CurrencyType">
  <!-- en: "ISO 4217 currency code on the invoice" -->
<xs:element name="exchangeRate" type="ExchangeRateType">
  <!-- en: "In case any currency is used other than HUF, the applied exchange rate
       should be mentioned: 1 unit of the foreign currency expressed in HUF" -->
```
Both are **mandatory in the XML** (`currencyCode` and `exchangeRate` have no `minOccurs="0"` in `InvoiceDetailType`) — `exchangeRate` must be reported as `1` for HUF-denominated invoices. `ExchangeRateType` is documented as 14 total digits with 6 decimal places. [`invoiceData.xsd`, `InvoiceDetailType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

Critically, **the exchange rate is not required invoice content** — see §5 for the exact quote from the interface spec establishing this is a data-exchange-only mandatory field, not an invoice-printing requirement.

### 1.5 Seller (supplier) identification, including adószám format

`SupplierInfoType` (`invoiceData.xsd`) — mandatory fields: `supplierTaxNumber` (`base:TaxNumberType`), `supplierName` (`common:SimpleText512NotBlankType`), `supplierAddress` (`base:AddressType`). Optional: `groupMemberTaxNumber`, `communityVatNumber`, `supplierBankAccountNumber`, `individualExemption` (VAT-exempt sole trader flag), `exciseLicenceNum`.

**`TaxNumberType` structure**, confirmed identically in both the fetched XSD (`invoiceBase.xsd`) and the fetched interface-spec PDF (§2.1.4, "Adószámok a sémában" / "Tax numbers in the schema," including its field-facet table):

| Element | Mandatory | Pattern | Content |
|---|---|---|---|
| `taxpayerId` | Yes | `[0-9]{8}` | "Core tax number of the taxable person. In case of group taxation arrangement, the group identification number." |
| `vatCode` | No | `[1-5]{1}` | "VAT code to indicate taxation type of the taxpayer. One digit." |
| `countyCode` | No | `[0-9]{2}` | "County code, two digits." |

This is the familiar Hungarian adószám printed form `12345678-1-42` (8 digits – 1 digit – 2 digits), confirmed directly from NAV's own schema and specification text, not inferred. The PDF spec (§2.1.4) further states the VAT-code digit is normally `5` when the seller reports under a group VAT number and `4` for the reporting group member's own number — a detail an extraction schema does not need, but useful for validating that a captured tax number's second segment is a plausible 1–5 digit.

### 1.6 Buyer (customer) identification, including VAT status

`CustomerInfoType` (`invoiceData.xsd`) — only `customerVatStatus` is mandatory; everything else (`customerVatData`, `customerName`, `customerAddress`, `customerBankAccountNumber`) is `minOccurs="0"`, reflecting that Hungarian B2C retail invoices legitimately omit buyer details.

`CustomerVatStatusType` enumeration:

| Value | Meaning |
|---|---|
| `DOMESTIC` | Domestic VAT subject |
| `OTHER` | Other (domestic non-VAT-subject entity, non-natural person, etc.) |
| `PRIVATE_PERSON` | Non-VAT-subject (domestic or foreign) natural person |

When `customerVatData` is present, it is a *choice* of `customerTaxNumber` (domestic, same `TaxNumberType` shape as the seller's), `communityVatNumber` (EU VAT number), or `thirdStateTaxId` (non-EU). [`invoiceData.xsd`, `CustomerInfoType`/`CustomerVatDataType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

The interface-spec PDF (§2.1.4.1, "Vevői adószám") states the legal basis (VAT Act §169(d)): domestic B2B sales must show at least the first eight digits of the buyer's tax number on the invoice and in the report — i.e. the buyer's tax number, when it applies, genuinely is expected to be printed on the invoice face, unlike the exchange rate.

---

## 2. Fields covering invoice type/appearance (useful context, lower extraction priority)

- `invoiceCategory` (mandatory): `NORMAL` | `SIMPLIFIED` | `AGGREGATE` — whether it's a normal, simplified (typically receipt-like, gross-only), or aggregate (batch/collective) invoice. This materially changes which summary/line-amount shape applies (§3, §4).
- `invoiceAppearance` (mandatory): `PAPER` | `ELECTRONIC` (non-EDI) | `EDI` | `UNKNOWN`.

Both enumerations were confirmed via the fetched `invoiceBase.xsd`. These describe the invoice's *nature*, not data a scanned-document extraction pipeline would read off the page — they're closer to classification metadata than extractable fields, and are noted here mainly because `invoiceCategory` determines whether the line/summary shape below is "normal" (net+VAT+gross per line and per rate) or "simplified" (gross-only, VAT-content-only).

---

## 3. Line-item-level fields

`LineType` (`invoiceData.xsd`) — mandatory fields: `lineNumber`, `lineExpressionIndicator` (boolean: "is the quantity expressible in a natural unit"). Everything describing the actual product/service is `minOccurs="0"` at the schema level:

```xml
<xs:element name="lineDescription" type="common:SimpleText512NotBlankType" minOccurs="0">
  <!-- en: "Name / description of the product or service" -->
<xs:element name="quantity" type="QuantityType" minOccurs="0">
  <!-- en: "Quantity" -->
<xs:element name="unitOfMeasure" type="UnitOfMeasureType" minOccurs="0">
  <!-- en: "Canonical representation of the unit of measure of the invoice,
       according to the interface specification" -->
<xs:element name="unitOfMeasureOwn" type="common:SimpleText50NotBlankType" minOccurs="0">
  <!-- en: "Literal unit of measure of the invoice" -->
<xs:element name="unitPrice" type="QuantityType" minOccurs="0">
  <!-- en: "Unit price expressed in the currency of the invoice. In the event of
       simplified invoices gross unit price, in other cases net unit price" -->
```
[`invoiceData.xsd`, `LineType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

`unitOfMeasure` is a closed enumeration: `PIECE, KILOGRAM, TON, KWH, DAY, HOUR, MINUTE, MONTH, LITER, KILOMETER, CUBIC_METER, METER, LINEAR_METER, CARTON, PACK, OWN` (with `unitOfMeasureOwn` as free text when `OWN` is chosen) — confirmed in `invoiceData.xsd`.

**Line value data is a choice between two mutually exclusive shapes**, selected by `invoiceCategory`:

- `LineAmountsNormalType` (normal/aggregate invoices) — `lineNetAmountData` (mandatory: `lineNetAmount` + `lineNetAmountHUF`), `lineVatRate` (mandatory, see §3.1), `lineVatData` (optional: `lineVatAmount` + `lineVatAmountHUF` — VAT amount is omitted, e.g., for exempt/reverse-charge lines), `lineGrossAmountData` (optional: `lineGrossAmountNormal` + `lineGrossAmountNormalHUF`).
- `LineAmountsSimplifiedType` (simplified invoices) — `lineVatRate` (mandatory) plus a single gross figure (`lineGrossAmountSimplified` + HUF equivalent) only; no separate net/VAT breakdown per line, since simplified invoices are gross-only by nature.

[`invoiceData.xsd`, `LineAmountsNormalType` / `LineAmountsSimplifiedType` / `LineNetAmountDataType` / `LineVatDataType` / `LineGrossAmountDataType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

### 3.1 Per-line VAT rate/exemption (`VatRateType`)

This is a `choice`, not a single numeric field — the schema forces a report to say *which kind* of VAT treatment applies, not just a percentage:

| Element | Type | Meaning |
|---|---|---|
| `vatPercentage` | `RateType` | "Applied tax rate - section 169 (j) of the VAT law" |
| `vatContent` | `RateType` | "VAT content in case of simplified invoice" |
| `vatExemption` | `DetailedReasonType` (code + reason text) | "Marking tax exemption - section 169 (m) of the VAT law" |
| `vatOutOfScope` | `DetailedReasonType` | "Out of scope of the VAT law" |
| `vatDomesticReverseCharge` | `xs:boolean`, fixed `true` | "Marking the national reverse charge taxation - section 142 of the VAT law" |
| `marginSchemeIndicator` | `MarginSchemeType` (`TRAVEL_AGENCY`\|`SECOND_HAND`\|`ARTWORK`\|`ANTIQUES`) | Margin-scheme taxation marker per §169(p)(q) |
| `vatAmountMismatch` | `VatAmountMismatchType` | Cases where the tax base and levied tax diverge from the plain rate calculation |
| `noVatCharge` | `xs:boolean`, fixed `true` | "No VAT charged under Section 17" |

[`invoiceData.xsd`, `VatRateType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd) — the CHANGELOG_3.0.md confirms this choice expanded from 6 to 8 options in the 3.0 revision specifically to disambiguate exemption/out-of-scope cases.

Every one of these is expected to be represented on the invoice face in some form (a percentage figure, or an exemption clause/legal citation text near the line or in the invoice footer) — VAT rate/exemption marking is itself VAT Act §169(j)/(m) mandatory invoice content, not reporting-only metadata.

---

## 4. VAT summary/aggregation fields (`SummaryType`)

`SummaryType` is a choice between `summaryNormal` (one, for normal/aggregate invoices) and `summarySimplified` (repeatable, for simplified invoices), plus an optional invoice-wide gross total:

**`SummaryNormalType`** — one or more `summaryByVatRate` rows (`maxOccurs="unbounded"`), each containing:
- `vatRate` (the same `VatRateType` choice as §3.1)
- `vatRateNetData`: `vatRateNetAmount` + `vatRateNetAmountHUF` — net subtotal for that rate
- `vatRateVatData`: `vatRateVatAmount` + `vatRateVatAmountHUF` — VAT subtotal for that rate
- `vatRateGrossData` (optional): `vatRateGrossAmount` + `vatRateGrossAmountHUF` — gross subtotal for that rate

...followed by invoice-wide totals: `invoiceNetAmount`/`invoiceNetAmountHUF` and `invoiceVatAmount`/`invoiceVatAmountHUF` (both mandatory).

**`SummarySimplifiedType`** (one row per VAT rate present, `summarySimplified` itself `maxOccurs="unbounded"`) — `vatRate`, `vatContentGrossAmount` + `vatContentGrossAmountHUF` only (gross-only, consistent with §3's simplified-invoice line shape).

**`SummaryGrossDataType`** (optional at the `SummaryType` level): `invoiceGrossAmount` + `invoiceGrossAmountHUF` — the invoice's single bottom-line total.

[`invoiceData.xsd`, `SummaryType` / `SummaryNormalType` / `SummarySimplifiedType` / `SummaryByVatRateType` / `SummaryGrossDataType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

Every one of these — per-rate net/VAT/gross subtotals and the invoice-wide net/VAT/gross totals — corresponds to the "VAT breakdown table" that's a standard, expected block on a real Hungarian invoice (usually printed as one row per VAT rate near the bottom, then a grand total row), so this is realistically extractable from a rendered document, **provided** the invoice actually prints such a table (many do; not all — see §5's general caveat that reporting mandatoriness tracks invoice-content mandatoriness only "as a general rule," with named exceptions).

The `HUF`-suffixed duplicate of every monetary figure (`vatRateNetAmountHUF`, `invoiceGrossAmountHUF`, etc.) exists because NAV requires all monetary reporting fields expressed in HUF regardless of invoice currency — for a HUF-denominated invoice the two values are identical; for a foreign-currency invoice, the HUF figure is a computed value (using the exchange rate from §1.4) that will **not** independently appear as separate printed text on the invoice in most cases — an extraction schema capturing the invoice-currency figures and letting downstream logic compute/convert is more realistic than expecting a document to print both currencies per line.

---

## 5. Fields NAV requires that would not appear on the face of an invoice

This directly answers the ticket's flag-for-non-extractable-fields ask. Two categories:

### 5.1 Fields the interface spec itself calls out as reporting-only, not invoice-printing-mandatory

The interface spec's own framing section (§2.1.2, "Adatok kötelezősége" / "Mandatory nature of data") states the general rule and its own caveat:

> (Hungarian, ¶1) "Az online adatszolgáltatásról szóló jogszabály (23/2014. (VI.30.) NGM rendelet) a számlákon általában megjelenő adatoknak csak egy részéről, meghatározóan az Áfa tv. által megkövetelt adattartalomról teszi kötelezővé az adatszolgáltatást. […] Az adatszolgáltatásban főszabály szerint azokat az adatokat kötelező szerepeltetni, amelyeket az Áfa tv. a számla/módosító okirat kötelező adattartalmaként határoz meg."
>
> (English paraphrase) The data-reporting regulation makes reporting mandatory chiefly for the data content the VAT Act already requires to appear on the invoice. As a general rule, the report must include exactly the data the VAT Act defines as mandatory invoice/modification-document content.

— i.e., NAV's own framing is that reporting-mandatory *should* generally coincide with invoice-mandatory. But the spec then gives at least one explicit, concrete exception with its exact legal basis — the exchange rate:

> (§2.1.3, discussing `currencyCode`/`exchangeRate`) "Az árfolyam, nem a számla kötelező adattartalma, azonban az Áfa tv. 10. melléklete 2021. január 4-étől hatályos 2. és 4. pontja alapján az adatszolgáltatás kötelező eleme."
>
> (English paraphrase) "The exchange rate is not mandatory content of the invoice, but — per points 2 and 4 of Annex 10 of the VAT Act, effective from January 4, 2021 — it is a mandatory element of the data report."

This means **`exchangeRate` must be flagged as not reliably extractable from a rendered document.** A foreign-currency invoice may or may not print its applied HUF exchange rate; NAV's own spec confirms it is not required to. Any extraction schema field for exchange rate should be treated as optional/best-effort, not required, and downstream logic that needs it for HUF conversion should not assume it will be present on the source document.

### 5.2 Fields that only exist to describe the electronic submission itself, not the invoice's content

These live in `invoiceApi.xsd` (the submission/reporting wrapper) or are metadata-about-the-report fields inside `invoiceData.xsd`'s top level, not fields describing what's printed on the invoice:

| Field | Schema | Purpose (from fetched annotation) |
|---|---|---|
| `completenessIndicator` | `invoiceData.xsd`, `InvoiceDataType` (mandatory, top level) | "Indicates whether the data exchange is identical with the invoice (the invoice does not contain any more data)" — a flag about the *report*, describing whether the XML is itself a complete substitute for the invoice (relevant to e-invoicing use cases since Jan 4, 2021). Never printed on an invoice. |
| `transactionId` | `invoiceApi.xsd` | "Transaction ID of the invoice if it was exchanged via M2M interface" — a submission-tracking identifier. |
| `index` | `invoiceApi.xsd` | "Sequence number of the invoice within the request" — batch-submission bookkeeping. |
| `batchIndex` | `invoiceApi.xsd` / `InvoiceReferenceType` | "Sequence number of the modification document within the batch." |
| `invoiceOperation` | `invoiceApi.xsd` (`ManageInvoiceOperationType`: `CREATE`\|`MODIFY`\|`STORNO`) | "Invoice operation type" — describes the submission's intent (new / amend / void), not a fact about the invoice's own printed content. |
| `electronicInvoiceHash` | `invoiceApi.xsd` (`common:CryptoType`) | "Electronic invoice or modification document file hash value" — an integrity checksum of the submitted file, computed post-hoc, never printed. |
| `exchangeToken` | `invoiceApi.xsd` | Authentication/authorization token for the API call — pure transport-layer plumbing. |

[`invoiceApi.xsd`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceApi.xsd), [`invoiceData.xsd`, `InvoiceDataType`](https://github.com/nav-gov-hu/Online-Invoice/blob/master/src/schemas/nav/gov/hu/OSA/invoiceData.xsd)

None of these belong in a document-extraction schema — they are properties of the *reporting act*, not the invoice document, and a scanned/PDF invoice has no way to carry them.

### 5.3 A softer, third category: present in the schema, but rarely printed on a standard invoice

Not confirmed by the spec as reporting-only, but worth flagging from the schema's own structure and annotations as low-yield for OCR/extraction even though they are legitimate invoice-content fields when applicable:

- `conventionalInvoiceInfo` (`ConventionalInvoiceInfoType`) — order numbers, delivery notes, shipping dates, contract numbers, GLN numbers, material/item numbers, EKAER IDs, cost centers, project numbers, general-ledger account numbers. The schema's own annotation calls these "other conventionally named data to assist in invoice processing" — i.e. logistics/ERP metadata that appears on *some* B2B invoices (especially EDI-originated ones) but is inconsistent in presence and placement, unlike the VAT-Act-mandated fields above.
- `additionalInvoiceData` / `additionalLineData` (`AdditionalDataType`, both `minOccurs="0" maxOccurs="unbounded"`) — explicitly an open-ended free-form extension point, not a defined field at all.
- Product-fee / excise / diesel-oil / new-transport-means / vessel / vehicle sub-blocks under `LineType` — real VAT-Act-driven fields for narrow product categories (environmental product fee, excise goods, new vehicles), unlikely to be relevant to a general-purpose invoice extraction schema; worth excluding unless a specific Document Type for those categories is later needed.

---

## 6. Version note: is "v3.0" still accurate, and what "3.0" actually versions

**Confirmed from primary sources**: the fetched `invoiceData.xsd`'s target namespace is `http://schemas.nav.gov.hu/OSA/3.0/data`, and the `nav-gov-hu/Online-Invoice` README (fetched) identifies the accompanying `Online_Szamla_interfesz specifikáció_HU_v3.0.pdf` as the current ("Aktuális") API documentation. The `CHANGELOG_3.0.md` (fetched) documents 3.0's introduction (targeted for test-environment availability by end of September 2020) and its major changes from 2.0 (electronic-invoice support via `completenessIndicator`/`electronicInvoiceHash`, the `customerVatStatus` redesign replacing a vaguer `privatePersonIndicator`, `mergedItemIndicator` for large submissions, the `VatRateType` expansion from 6 to 8 options, and the `advanceData` restructuring for advance-payment invoices) — no fetched source describes a schema version beyond 3.0.

**Not confirmed by a fetched primary source**: search-result snippets (not independently fetched and verified in full) suggest the *interface specification document* — as distinct from the XSD schema's namespace version — carries its own more granular revision number that has continued incrementing well past 3.0 (observed in snippets as "3.44" / "3.44.3" in 2026-dated pages), representing clarifications and amendments layered onto the same underlying 3.0 XSD rather than a schema-breaking change. A separate snippet referenced a "NAV XML schema 4.0" in the context of a 2026 mandatory-e-invoicing article; this research could not confirm whether that refers to a genuinely new Online Számla reporting schema, a different mandatory-e-invoice-format initiative entirely distinct from the real-time reporting obligation this document covers, or a misreading of the specification-document revision counter. **This should be treated as an open question, not a settled fact, and re-checked against a freshly fetched primary source (`onlineszamla.nav.gov.hu/dokumentaciok` or the current interface-spec PDF) before this research's "v3.0 is current" conclusion is relied on for anything beyond this schema-design ticket.**

---

## Implications for `schemas/invoice/v2.json`

(Facts only — no schema JSON drafted here, per this ticket's brief; this is a bridge to the redesign, not the redesign itself.)

1. **Solidly extractable, invoice-face-printed, and NAV-mandatory**: invoice number, issue date, delivery/completion date (with the caveat it may be genuinely absent and default to issue date), seller name/address/tax-number, buyer name/tax-number when present, currency code, per-line description/quantity/unit/unit-price/net-amount/VAT-rate/VAT-amount/gross-amount, and the VAT-summary table (per-rate net/VAT/gross subtotals plus invoice grand totals).
2. **Extractable but schema-optional on both sides (NAV and the physical document)**: payment method, payment due date, buyer tax number (legitimately absent on many receipts/simplified invoices), quantity/unit/unit-price at line level (legitimately absent for lump-sum service lines per the fetched XSD's own `minOccurs="0"`).
3. **Should NOT be modeled as required, and probably not worth modeling at all**: exchange rate (§5.1 — NAV's own spec confirms it's not invoice-mandatory despite being report-mandatory), and the entire submission-metadata family in §5.2 (`completenessIndicator`, `transactionId`, `index`, `batchIndex`, `invoiceOperation`, `electronicInvoiceHash`, `exchangeToken`) — these describe the act of reporting to NAV, not the document, and have no printed representation to extract.
4. **Lower priority / defer**: the §5.3 logistics-metadata bag (order/delivery/contract numbers, GLN, EKAER, cost centers) and the narrow product-category sub-schemas (excise, product fee, vehicles) — real NAV fields, but inconsistent-to-absent on a general invoice and better scoped to a future, narrower Document Type if a concrete need arises.
