# Hungarian invoicing providers: which one can hand us a genuine, synthetic-data invoice PDF that does not report to NAV

Researched 2026-08-06, resolving [#66](https://github.com/akosgintl/document-intelligence/issues/66), part of the fidelity map [#65](https://github.com/akosgintl/document-intelligence/issues/65).

## Why this file exists

[#65](https://github.com/akosgintl/document-intelligence/issues/65)'s premise for the invoice half of the fidelity map is that this document type does not need redrawing at all: a real Hungarian invoicing provider will hand us a real invoice if we ask it to, and a genuinely provider-issued PDF is closer to production input than anything `fixtures/catalogue.py` can draw. This ticket exists to test that premise before the map spends a follow-on ticket ([#68](https://github.com/akosgintl/document-intelligence/issues/68)) walking a signup flow.

The premise has a trap built into it, and the ticket names it explicitly: **issuing a Hungarian invoice through a live account is a regulated act.** Hungary's NAV Online Számla system requires real-time (or near-real-time) reporting of invoice data to the tax authority, and — this is the finding that reorders the rest of this document — **that reporting obligation has no exemption for "this one's just a test."** The question this file answers first, before it is worth asking anything about any specific provider's pricing or API, is: **does a path exist anywhere in this ecosystem that produces a real, provider-rendered PDF without also creating a real NAV record?**

**Scope.** Per the ticket: Számlázz.hu (KBOSS.hu), Billingo, Novitax, szamlazo.hu, and NAV's own free Online Számlázó, plus anything else with meaningful market share encountered along the way. Per-provider axes: published sample PDFs, free tier/trial requirements, API test/demo mode, the NAV-reporting question above all, and layout distinctiveness.

## Method, and its ceiling

This research was run as three parallel passes, each fetching and quoting primary sources directly rather than summarizing secondary write-ups: (1) NAV's own legal framework and its free Online Számlázó tool; (2) Számlázz.hu and szamlazo.hu; (3) Billingo and Novitax. Sources, all primary except where flagged:

| Source | What it covers |
|---|---|
| `nav.gov.hu` — NAV's own rule explainers and the current (dated 2026.03.02) information booklet on invoice/receipt issuance | The reporting-threshold rule and the statutory basis for who may issue an invoice at all |
| `onlineszamla.nav.gov.hu` — NAV's own published user manuals (PDF) for the Online Számla system and the free Online Számlázó app | Registration mechanics, the test environment, storno behaviour |
| Each provider's own site: pricing pages, registration forms, help-center/`tudastar` articles, API documentation, terms of service (ÁSZF) | Free tier terms, test/demo modes, NAV-integration statements, API shape |
| Direct DNS/HTTP inspection of `szamlazo.hu` | Whether the domain is a live service at all |

**The ceiling, stated plainly, matching this repo's convention for honesty about what wasn't checked:**

- **No signup flow was actually walked.** Every finding below about registration requirements — what a form asks for, whether a tax-number field is validated against NAV's real taxpayer registry or merely format-checked — is read off documentation and help-center text, not observed by creating an account. This is exactly the residue [#68](https://github.com/akosgintl/document-intelligence/issues/68) exists to close, and it is flagged per-provider below rather than glossed over.
- **`web.archive.org` was unreachable from the research environment**, so `szamlazo.hu`'s history (as opposed to its current state) could not be checked.
- **Some pages are JavaScript-rendered** (notably Novitax's demo signup pages) and returned only generic titles to a plain fetch; their exact signup fields are unconfirmed for the same reason.
- **Billingo's ÁSZF quotes below come from an AI-assisted extraction of the terms-of-service page**, not a manual clause-by-clause read — treat section numbers as indicative, not certified.
- The research did not attempt other Hungarian invoicing brands beyond the ticket's list except where they surfaced incidentally (`mostszamlazz.hu`, `szamla.hu`, `onlineszamlazo.hu` appeared in search results as other market participants but were not investigated — noted for completeness, not ruled in or out).

---

## The central fact, established before any provider is worth comparing

### NAV Online Számla reporting has no threshold left

**Sourced.** The old 100,000 HUF transferred-VAT threshold was abolished effective 1 July 2020. NAV's own explainer states it directly:

> "A 100 000 forint áthárított adóban meghatározott értékhatár megszűnése miatt ugyanakkor 2020. július 1-jétől minden olyan áthárított adót tartalmazó számláról adatot kell szolgáltatni... függetlenül az áthárított adó összegének (és az abból levont adó összegének) nagyságától."
>
> ("Because the 100,000 HUF transferred-VAT threshold ceased to exist, from 1 July 2020 data must be reported on every invoice containing transferred VAT... regardless of the size of the transferred VAT amount.")

— [NAV, "A számlaadat-szolgáltatás 2020. július 1-jétől alkalmazandó szabályai"](https://nav.gov.hu/ado/afa/A_szamlaadat_szolgalt20200701)

A second reform, effective 4 January 2021, widened scope further to cover invoices to non-VAT-registered persons and foreign parties, and left only a **deadline** distinction (1 calendar day if the invoice's VAT is ≥500,000 HUF; 4 calendar days otherwise, including invoices with zero VAT) — [NAV, "A számlakibocsátók számlaadat-szolgáltatásának 2021. január 4-től hatályos szabályai"](https://nav.gov.hu/ado/afa/A_szamlakibocsatok_sz20201231). NAV's current (2026.03.02-dated) booklet on invoice/receipt issuance still footnotes the January 2021 rules as the live reference and mentions no threshold — [`nav.gov.hu` booklet PDF](https://nav.gov.hu/pfile/file?path=%2Fugyfeliranytu%2Fnezzen-utana%2Finf_fuz%2Frejtett%2FInformacios-fuzetek---Aktualis%2F18.-informacios-fuzet---A-szamla-nyugta-kibocsatasanak-alapveto-szabalyai).

**Verdict: essentially every invoice a Hungarian VAT-registered entity issues must be reported.** There is no small-value, no-VAT, or "informal" carve-out at the statutory level.

### Issuing "a számla" at all presupposes a live, registered adószám

**Sourced.** Áfa tv. (2007. évi CXXVII. törvény) §159(1), quoted in NAV's current booklet:

> "Az áfaalany – az Áfa tv. számlaadási kötelezettségre vonatkozó általános szabálya értelmében – köteles számlát kibocsátani a belföldön és ellenérték fejében teljesített termékértékesítéséről, szolgáltatásnyújtásáról a termék beszerzője, a szolgáltatás igénybevevője számára..."
>
> ("The VAT-taxable person — under the VAT Act's general invoicing rule — is required to issue an invoice for domestic, consideration-based supplies of goods/services to the buyer/recipient...")

Áfa tv. §169's mandatory-content list, quoted in the same booklet, makes the seller's own tax number unconditional (unlike the buyer's, which is conditional): "az adószáma, amely alatt a termék értékesítését, a szolgáltatás nyújtását teljesítette" ("its tax number under which it performed the supply"). **There is no lighter-weight legal category — no "specimen invoice," no "demo invoice" — recognized in the VAT Act.** An "invoice" is, by statutory definition, something only a registered taxable person issues.

This matters for every provider below: a provider's live account is inescapably gated on a real adószám because the *law*, not the provider's product design, requires it. The only place synthetic data can enter without also being illegal is a **test/demo environment that is not connected to a real NAV taxpayer at all** — which is exactly the axis to check per provider.

---

## 1. NAV's own free Online Számlázó — ruled out

The ticket flagged this as worth special attention because it is the tax authority's own renderer and therefore as canonical as a Hungarian invoice layout gets. That is true, and it is also the reason it is the *worst* candidate: NAV's tool has no separation whatsoever between "issue" and "report."

| Axis | Finding | Bucket |
|---|---|---|
| What it is | Free web/mobile invoicing app inside the Online Számla ecosystem | sourced |
| Registration | Requires **KAÜ** (Központi Azonosítási Ügynök — Hungary's real government identity federation: Ügyfélkapu / e-személyi / phone-based ID), then selection of a real registered "adóalany" from companies the authenticated person represents | sourced |
| Issue = report, same act | *"Az Online Számlázóban: az új, kiállított számlákról valós idejű adatok érkeznek a NAV-hoz..."* ("...real-time data on newly issued invoices arrives at NAV...") | sourced |
| Demo/oktatási/bemutató mode | **None found.** Extensive search for "oktatási rendszer", "bemutató", "demo" tied to the Online Számlázó specifically turned up nothing | unsourced (absence, not proven impossible, but nothing found after a real search) |
| The "teszt" environment (`onlineszamla-test.nav.gov.hu`) | Exists, and is NOT an isolated synthetic sandbox — it mirrors production requirements | sourced, see below |
| Storno erases the original | **No.** The original stays visible marked ⊘ "Érvénytelenített"; the cancelling invoice is itself a new, separately-reported invoice | sourced |
| PDF watermark on test-environment output | Manual screenshots show what looks like a repeating "TESZT" watermark, but no prose in the manual asserts this as a guaranteed system behaviour | inferred, not fully confirmed |

**Sources:** NAV Online Számlázó Felhasználói kézikönyv v1.19 (2019-12-03), [PDF](https://onlineszamla.nav.gov.hu/api/files/container/download/OSZ%20-%20Felhaszn%C3%A1l%C3%B3i%20k%C3%A9zik%C3%B6nyv%20v1.19.pdf), pp. 4, 7, 14, 83–86. NAV Online Számla Rendszer Felhasználói kézikönyv v1.6 (2019-03-19), [PDF](https://onlineszamla.nav.gov.hu/api/files/container/download/Online_Sz%C3%A1mla_Rendszer_felhaszn%C3%A1l%C3%B3i_k%C3%A9zik%C3%B6nyv_v1.6.pdf), pp. 24, 27, 30–31. [NAV, "Az Online Számla rendszer használata"](https://nav.gov.hu/Elethelyzetek-adozasa/vallalkozas/Regisztracio-az-Online-Szamla-rendszerben).

### Why the "teszt" environment does not solve this

`onlineszamla-test.nav.gov.hu` is real, and NAV's own page says it serves two audiences: ordinary taxpayers trying out data entry, and software vendors testing system-to-system XML submission. But registration into it mirrors production, not a sandbox:

> "A regisztrációhoz aktív ügyfélkapus fiók megléte szükséges." ("An active Ügyfélkapu account is required for registration") — stated identically for both production and test.

> "Gazdálkodó szervezet regisztrációjakor meg kell adni az adószám első 8 számjegyét, azaz a törzsszámot. Formailag megfelelő adószám esetén a felületen aktívvá válik az 'Adózói adatok ellenőrzése' funkciógomb." ("...you must enter the tax number's first 8 digits... a 'Verify taxpayer data' button activates.")

> "'Érvénytelen adózó, a folyamat nem folytatható!' hibaüzenet abban az esetben jelenik meg, ha az adatbázisban nem szerepel az érték..." ("'Invalid taxpayer, cannot continue' appears if the value is not found in the [NAV] database...")

That last quote is decisive: **the test-registration flow validates the tax number against NAV's real taxpayer database.** There is no documented way to register a fictitious taxpayer there. What is unconfirmed — genuinely, no primary source found either way — is whether the test environment's *invoice records* ultimately live in a database partition fully separate from production once a real registered taxpayer is using it; the evidence available (shared real-taxpayer validation, no separate synthetic registry mentioned anywhere) points toward "not meaningfully isolated," but this is inference, not a quoted NAV statement.

**Verdict for NAV's own tool: no non-reporting path exists via any avenue this research found.** If a synthetic-but-realistic Hungarian invoice PDF is needed, going through NAV's actual production systems is not the way to get it — a conclusion that directly overturns the ticket's working assumption that NAV's canonical layout was worth chasing first.

---

## 2. Számlázz.hu (KBOSS.hu Kft.) — the strongest candidate found

| Axis | Finding | Bucket |
|---|---|---|
| Free tier | `#free`, 0 Ft, unlimited paper-based invoicing, described as itself **"NAV-kompatibilis"** — i.e. fully live/reportable, not a workaround | sourced |
| Initial signup | Name, email, password only (or Google/Facebook OAuth) — no adószám at this step | sourced |
| **Demófiók (demo account)** | **No registration at all**, public homepage link, free, unlimited use | sourced |
| **Tesztfiók (test account)** | Requires "an actual business tax number" per docs (validation strictness unconfirmed); **explicitly and structurally cannot connect to NAV**; free/unlimited | sourced (the NAV-block claim); unsourced (validation strictness) |
| **Díjbekérő (proforma)** | Real, live, paid-subscription document; legally not a "számla," so outside NAV's reporting scope by definition, not by provider workaround | sourced |
| API (Számla Agent) | XML/HTTPS, live since 2010, one key/endpoint for both test and live — the account-level Tesztüzem toggle decides which | sourced |
| Layout | 6 selectable stock templates plus fully custom PDF/JPG/PNG upload (up to 10 MB) | sourced |

### 2.1 Demófiók — no account needed at all

> "egy nyilvánosan, a Számlázz.hu főoldaláról, regisztráció nélkül elérhető felület mindenki számára"
>
> ("a publicly accessible interface from the Számlázz.hu homepage, available to everyone without registration")

— [tudastar.szamlazz.hu, "Mire használhatom a demófiókot?"](https://tudastar.szamlazz.hu/gyik/mire-hasznalhatom-a-demofiokot)

Documents produced there carry a **"MINTA" (SAMPLE) watermark**:

> "kipróbálhatod ... a(z) különböző bizonylatítipusokat (MINTA felirattal ellátva)"

This is the cleanest possible non-reporting guarantee available anywhere in this research, precisely *because* no account and no tax number exist at all — there is structurally nothing to connect to NAV. Its weaknesses are practical, not legal: it is a **shared, public sandbox** ("a demófiók közös próbakörnyezet, ezért az ott kiállított bizonylatokat más felhasználók is láthatják" — "the demo account is a shared trial environment, so documents issued there can be seen by other users") with daily auto-deletion, and there is no API access to it — it is web-UI-only. [Számlázz.hu blog, "Demo vs. tesztfiók"](https://www.szamlazz.hu/blog/2020/05/demo-vs-tesztfiok-a-szamlazz-hu-ban-kisbolt-10-perc-alatt-vagy-plazazas-a-vegtelensegig/).

### 2.2 Tesztfiók — the API-capable option

> "A kibocsátott számlák teszt számlák, nem minősülnek számviteli bizonylatnak."
>
> ("Issued invoices are test invoices and do not constitute accounting documents.")

> "Nem tudod összekapcsolni a NAV Online számla rendszerével."
>
> ("You cannot connect it to the NAV Online Számla system.")

— [tudastar.szamlazz.hu, "A tesztfiók működése"](https://tudastar.szamlazz.hu/gyik/teszt-fiok-mukodese)

This is the **most explicit, most directly quoted non-reporting guarantee of any option surveyed**: it isn't inferred from architecture, it's stated as a structural incapability. The tesztfiók gives full `#profi`-tier feature access and full Számla Agent API testing, free and indefinitely — flipping "Tesztüzem bekapcsolása" (Enable Test Mode) on the dashboard applies to the whole account; the same API key and endpoint work in both modes.

**The one real unknown, and exactly what #68 must resolve first:** the help-center text (as fetched, not confirmed by an actual signup) describes tesztfiók activation as "requires registration with an actual business tax number," which is a stronger claim than the demófiók's "no registration." Whether that field is checked against NAV's real taxpayer registry (as `onlineszamla-test.nav.gov.hu`'s is, per §1) or merely format-validated is **not established by any document fetched** — it needs to be walked live. If it's format-only, this is the best option in the whole survey: private, unlimited, free, full API, and the strongest quoted non-reporting guarantee found. If it turns out to require a real registered adószám, the demófiók (§2.1) is the immediate, zero-risk fallback, at the cost of losing API access and privacy.

### 2.3 Díjbekérő — real but not legally an invoice

> "van lehetőség díjbekérő készítésére is a Számla Agent használatával, ehhez azonban előfizetéssel kell rendelkezned"
>
> ("there is a possibility to create a díjbekérő using Számla Agent [API], but you must have a paid subscription")

— [tudastar.szamlazz.hu, "Díjbekérő automatikusan"](https://tudastar.szamlazz.hu/gyik/dijbekero-automatikusan)

A díjbekérő (payment request / proforma) is a genuine, live, non-test, non-watermarked PDF, generated through the real production account and API. It is outside NAV's reporting scope because Hungarian VAT law does not classify it as a "számla" at all — no VAT event, nothing to report. Its weakness for this project: it is conventionally titled `DÍJBEKÉRŐ`, not `SZÁMLA`, so whether it satisfies "a genuine invoice" depends on how strictly the eval needs the document to *be* one — this was not verified against an actual generated PDF and is flagged for #68.

### 2.4 General NAV obligation, confirmed as universal (no invoice-type carve-out)

> "A papír alapú számlatömb használata nem mentesít a NAV Online Számla rendszer felé történő adatszolgáltatás alól." / "A kézzel kiállított számlák adatait ugyanúgy el kell juttatni a NAV rendszerébe, mint a számlázóprogrammal készített számlák adatait."
>
> ("Using a paper invoice pad does not exempt you from NAV Online Számla data reporting." / "Manually issued invoices' data must reach NAV the same way as software-generated invoices' data.")

— [tudastar.szamlazz.hu, "Számlatömbbel is kell adatot szolgáltatni a NAV-nak?"](https://tudastar.szamlazz.hu/gyik/szamlatombbel-is-kell-adatot-szolgaltatni-a-nav-nak)

This confirms every *real* "számla" issued live through Számlázz.hu — regardless of how it was produced — is reportable; there is no exemption by invoice type or issuance method for a genuine invoice. Only the tesztfiók (structurally disconnected) and the demófiók (no account) sit outside that.

**Sources not otherwise cited above:** [pricing](https://www.szamlazz.hu/csomagok-es-arak), [registration](https://www.szamlazz.hu/szamla/regisztracio), [test-API access FAQ](https://tudastar.szamlazz.hu/gyik/teszt-api-hozzaferes), [try-without-subscription FAQ](https://tudastar.szamlazz.hu/gyik/szamlazz-hu-kipobalasa-elofizetes-nelkul), [NAV integration page](https://www.szamlazz.hu/nav-online-szamlazas), [API docs root](https://docs.szamlazz.hu/), [API auth docs](https://docs.szamlazz.hu/agent/basics/authentication), [brand assets](https://www.szamlazz.hu/arculat/), [template selection FAQ](https://tudastar.szamlazz.hu/gyik/milyen-szamlakepek-kozul-valaszthatok), [custom template FAQ](https://tudastar.szamlazz.hu/gyik/szamlakep-kezeles).

---

## 3. Billingo — a viable second option, weaker sourcing on the reporting guarantee

| Axis | Finding | Bucket |
|---|---|---|
| Free tier | 0 Ft + ÁFA/hó, unlimited invoicing, 1 template, "NAV szinkron" included | sourced |
| Account shell signup | Name/email/password only, no adószám | sourced |
| Any "vállalkozás" profile, test or live | Requires the **same fields**: vállalkozási forma, adószám, cégjegyzékszám, full address | sourced |
| **Teszt profil** | Separate signup entry (`app.billingo.hu/demo`), **permanent** (cannot convert to live), free/unlimited API testing | sourced |
| PDF watermark on test output | Visible **"TESZT"** watermark, and explicit language that the documents "cannot be used in any official format" | sourced |
| Non-reporting guarantee | **Inferred, not directly quoted** — no sentence found stating "test-profile invoices are never sent to NAV" | inferred |
| Díjbekérő/proforma exemption | Exists, same shape as Számlázz.hu's | sourced |
| API sandbox | v3 API has **no separate sandbox base URL** — Billingo's own recommendation is to use a test profile instead | sourced |
| Foreign/non-Hungarian applicants | Explicitly excluded — "A Billingo rendszere jelenleg csak magyar vállalkozások regisztrációját teszi lehetővé" | sourced |
| Layout | 26 selectable templates + 1 bilingual + thermal; default layout carries Billingo's name/logo unless customized | sourced |

Key quotes:

> "Az itt kiállított dokumentumok semmilyen hivatalos formátumban nem használhatók fel." / "A rendszerből kiállított bizonylatokon egyértelműen TESZT feliratokkal jelezzük, hogy nem éles rendszerből került kiállításra az adott dokumentum."
>
> ("Documents issued here cannot be used in any official format." / "Documents issued from the system are clearly marked with 'TESZT' labels indicating the document was not issued from the live system.")

— [support.billingo.hu, "A Billingo tesztelése"](https://support.billingo.hu/content/96338065) / [support.billingo.hu, content 2092630095](https://support.billingo.hu/content/2092630095)

> "A díjbekérő tartalmában hasonlít a számlára, de nem kell könyvelni, nincs adóvonzata... és nem vonatkozik rá a kötelező NAV adatszolgáltatás teljesítése sem." / "A proforma adatait nem – csak a későbbi számlát - kell feltölteni az Online számla rendszerébe."
>
> ("A payment request resembles an invoice in content, but need not be booked, has no tax consequence... and the mandatory NAV data-reporting obligation does not apply to it either." / "Proforma data need not be uploaded to Online Számla — only the later actual invoice.")

— Billingo tudástár, "Díjbekérő, proforma, előlegszámla" (search-indexed content)

**Why Billingo ranks below Számlázz.hu here despite a comparable feature set:** the test-profile non-reporting claim is architecturally very plausible (separate database, no real NAV technical-user credentials possible on a synthetic profile, documents explicitly marked non-official) but is not backed by a quotable sentence the way Számlázz.hu's "Nem tudod összekapcsolni a NAV Online számla rendszerével" is. It is also unconfirmed whether Billingo's "vállalkozás" creation form validates the adószám against a real registry — Billingo does offer an optional "Céginfó" lookup/autofill tool, which reads as a convenience rather than a forced picker, but that too is unconfirmed without a live signup.

**Sources:** [pricing](https://www.billingo.hu/arak), [registration](https://www.billingo.hu/regisztracio), [new-profile creation](https://support.billingo.hu/content/930512910), [company registration](https://support.billingo.hu/content/96239625), [foreign businesses](https://support.billingo.hu/content/3041853520), [Céginfó](https://support.billingo.hu/content/1804435475), [v2 sandbox deprecation](https://support.billingo.hu/content/951124290), [NAV sync feature page](https://www.billingo.hu/funkciok/nav-online-szamla-szinkron), [NAV connection support article](https://support.billingo.hu/content/930611592), [ÁSZF](https://www.billingo.hu/felhasznalasi-feltetelek), [template blog post](https://www.billingo.hu/blog/olvas/szamlasablon), [templates feature page](https://www.billingo.hu/funkciok/szamlasablonok).

---

## 4. Novitax — deprioritized

| Axis | Finding | Bucket |
|---|---|---|
| Core product line (WINTAX/NTAX/TAXA/BÉR) | Accountant-office software; **purchase required before registration** — "A regisztráció első feltétele a program megrendelése" | sourced |
| WebTax (lighter cloud product) | Has a genuinely self-service free demo | sourced |
| WebTax demo | Free, usable 2 months, at `szamlazodemo.novitax.hu` / `webtaxdemo.novitax.hu`; "a Demoban rögzített adatok nem mennek át az éles rendszerbe" (demo data does not transfer to the live system) | sourced |
| Exact demo signup fields | Unconfirmed — pages are JS-rendered and did not fetch cleanly | unsourced |
| Live-system NAV gating | Stronger than the other providers: **"NAV online adatbeküldéshez szükséges adatok megadása nélkül számla kiállítására nincs lehetősége!"** (Without NAV-submission data configured, there is no possibility of issuing an invoice at all) | sourced |
| Demo non-reporting guarantee | Not found explicitly; inferred from data-isolation statement only | inferred |
| Public invoicing API | **Not found.** Only a bank-transaction-feed API ("WebTax B-API") was located, not an invoice-creation API | unsourced (absence) |
| Cost | WebTax Számlázó from 500 Ft/hó (150 docs/yr tier) to 3,500 Ft/hó (unlimited); annual billing only | sourced |

Novitax is deprioritized for three compounding reasons: it splits into an accountant-gated core product that isn't reachable by an outside party at all, and a lighter WebTax product whose demo signup mechanics couldn't be confirmed from documentation; its live system's NAV-connection requirement is described as an outright block on issuing *any* invoice (stronger friction than the other providers, and it's unconfirmed whether the demo shares that block or not); and no public invoice-creation API was found to build a repeatable pipeline against. **Sources:** [new-user registration](https://novitax.hu/uj-felhasznaloknak/), [WebTax product page](https://novitax.hu/webtax/), [WebTax registration knowledge-base article](https://tudastar.novitax.hu/webtax-regisztracio-aktivalas-csomag-kivalasztas-bejelentkezes/), [NAV reporting article](https://tudastar.novitax.hu/nav-online-szamla-adatszolgaltatas/), [WebTax price list](https://novitax.hu/megrendeles-kepzes/webtax-arlista/).

---

## 5. szamlazo.hu — appears to be a dead domain, not a functioning provider

Direct DNS/HTTP inspection (not a document source, but the primary evidence available):

- `szamlazo.hu` resolves to `185.51.65.38`; nameservers `ns1.autoweb.hu` / `ns-slave.m.glbns.com`; MX `mail.autoweb.hu`; reverse DNS `cpanel.autoweb.hu`. **autoweb.hu is a generic Hungarian shared-hosting/reseller provider** unrelated to KBOSS.hu (Számlázz.hu) or Billingo Technologies Zrt.
- A plain HTTPS request (with certificate validation bypassed) returns **HTTP 403 Forbidden**, with the custom `ErrorDocument` itself also failing — a double-403, the signature of an unconfigured/parked hosting slot.
- With certificate validation enforced, the connection fails outright ("Hostname/IP does not match certificate's altnames") — the TLS certificate actually served covers unrelated domains, confirming shared/parked hosting rather than an active site.
- Web search for `"szamlazo.hu"` surfaces no results describing it as an active or historically active independent invoicing brand; Hungarian e-invoicing search results instead point to Számlázz.hu, Billingo, `szamla.hu`, `mostszamlazz.hu`, and `onlineszamlazo.hu`.
- `web.archive.org` was unreachable from the research environment, so its history could not be checked — **unsourced**, and flagged rather than guessed at.

**Verdict: `szamlazo.hu` is not a usable provider today.** Recommend a plain-browser re-check (not an automated fetch) before #68 spends any time on it, in case this was a transient hosting issue, but do not plan around it.

---

## Per-provider comparison table

| Provider | Free/no-cost non-reporting path | Registration friction | API access to that path | Non-reporting guarantee, sourcing strength | Layout distinctiveness |
|---|---|---|---|---|---|
| **NAV Online Számlázó** | None found | KAÜ + real, DB-verified adószám, in both prod and "teszt" | N/A — issue = report, same act | N/A — no such path exists | Highest (it's the tax authority's own layout) — moot, unreachable without reporting |
| **Számlázz.hu — demófiók** | Yes | **None** — no signup at all | No (web UI only) | Strong by construction (no account exists to connect to NAV) | Stock templates, MINTA-watermarked |
| **Számlázz.hu — tesztfiók** | Yes (pending #68 confirming the adószám field's validation strictness) | "Actual business tax number" claimed by docs — unconfirmed if DB-checked | **Yes** — full Számla Agent API | Strongest explicit quote found ("cannot connect to NAV") | 6 stock templates or custom upload |
| **Számlázz.hu — díjbekérő** | Yes, but it's legally a proforma, not an invoice | Requires paid subscription + live account | Yes, via API | Sourced (not a "számla" under VAT law at all) | Same rendering engine as real invoices, titled DÍJBEKÉRŐ |
| **Billingo — teszt profil** | Yes | Same adószám/company fields as a live profile, validation strictness unconfirmed | Yes — v3 API works against a test profile | Plausible but inferred, not directly quoted | 26+ templates, default carries Billingo branding |
| **Billingo — díjbekérő** | Yes, same caveat as Számlázz.hu's | Requires live account | Yes | Sourced | — |
| **Novitax — WebTax demo** | Likely, but unconfirmed | Signup fields unconfirmed (JS-rendered pages) | No invoicing API found | Inferred only, from a data-isolation statement | Unconfirmed |
| **szamlazo.hu** | N/A | N/A | N/A | N/A | Domain appears dead |

---

## Recommendation, and the path #68 should walk

**Recommendation: Számlázz.hu's tesztfiók (test account), reached through the Számla Agent API, is the target for #68 to attempt first.** It has the single strongest, most directly quoted non-reporting guarantee found anywhere in this survey — "Nem tudod összekapcsolni a NAV Online számla rendszerével" is a structural incapability, not an inference from architecture — and unlike every other viable option, it comes with full, unlimited, free API access using the exact same key/endpoint mechanics as production. That combination (private, repeatable, programmatic, and the strongest sourced non-reporting claim) is what a fixture-generation pipeline needs, and no other option scores as well on all four.

**The specific path #68 should walk, in order:**

1. Register a personal account at [szamlazz.hu/szamla/regisztracio](https://www.szamlazz.hu/szamla/regisztracio) (name, email, password — no adószám needed at this step).
2. Attempt to activate **Tesztüzem** ("Tesztüzem bekapcsolása" on the dashboard). The load-bearing unknown to resolve immediately: **does the tax-number field this requires get validated against NAV's real taxpayer registry, or only format-checked?** If format-only, a synthetic-but-valid-format Hungarian adószám (matching the pattern already documented in `docs/research/nav-online-szamla-invoicedata-requirements.md` — `taxpayerId` `[0-9]{8}` + `vatCode` `[1-5]{1}` + `countyCode` `[0-9]{2}`) unlocks the whole path. If it turns out to require a real, registered adószám, stop and fall back to step 4.
3. If Tesztüzem activates: generate a Számla Agent key from the account dashboard ("Számla Agent kulcsok"), and confirm via the API docs at [docs.szamlazz.hu](https://docs.szamlazz.hu/) that an invoice issued while Tesztüzem is on (a) renders as a real Számlázz.hu PDF template, (b) is confirmed via the account UI as *not* connected to NAV, and (c) carries whatever visual marking (if any) distinguishes it as non-live — this last point was not confirmed by documentation and needs a generated sample to check.
4. **Fallback, usable immediately and with zero registration risk:** the demófiók at the Számlázz.hu homepage. No signup, no adószám, "MINTA"-watermarked, free. Weaker for automation (web-UI only, shared/public, daily-deleted) but proves the concept and gets a first sample fast while step 2 is being resolved.
5. **Secondary alternative if Számlázz.hu's tesztfiók turns out to require a real adószám:** Billingo's teszt profil, reached the same way (`app.billingo.hu/demo`), with the same open question about adószám validation strictness, and a weaker (inferred, not quoted) non-reporting guarantee — but a comparably capable v3 REST API if Számlázz.hu's path is closed off.

**Do not pursue NAV's own Online Számlázó, and do not pursue szamlazo.hu.** The former has no non-reporting path at any layer this research could find; the latter is not currently a live service.

---

## What could not be sourced — the honest residue for #68

1. **Whether Számlázz.hu's or Billingo's test-account/test-profile tax-number field is validated against NAV's real taxpayer registry or only format-checked.** This is the single fact that decides whether the recommended path is frictionless or requires a real Hungarian company. Only a live signup resolves it.
2. **Whether a tesztfiók/teszt-profil-issued PDF carries any visible non-live marking** (a "TESZT" or "PRÓBA" watermark analogous to the demófiók's "MINTA"). Confirmed present for Billingo's teszt profil; not confirmed either way for Számlázz.hu's tesztfiók.
3. **Whether a díjbekérő/proforma PDF is close enough in layout to a real `SZÁMLA` for the project's needs**, or whether the `DÍJBEKÉRŐ` title and any accompanying legal-notice text make it unsuitable as an invoice-extraction fixture. Not verified against a generated sample.
4. **`szamlazo.hu`'s history** (as opposed to its dead current state) — `web.archive.org` was unreachable during this research.
5. **Novitax WebTax's exact demo signup fields**, and whether its demo environment shares the live system's hard block on issuing any invoice without NAV-submission data configured.
6. **Whether entering a synthetic third-party customer's adószám on an invoice (even in a provider's test mode) triggers a live NAV partner-validation lookup** — relevant if the fixture needs a synthetic buyer as well as a synthetic seller, and unconfirmed for any provider.
7. Other Hungarian invoicing brands spotted incidentally (`mostszamlazz.hu`, `szamla.hu`, `onlineszamlazo.hu`) were not investigated at all — noted for completeness, ruled neither in nor out.

## Relationship to existing research

This file is an axis on top of, not a duplicate of, `docs/research/nav-online-szamla-invoicedata-requirements.md` (#38), which established the `invoiceData` XSD schema's mandatory-field structure assuming an invoice is already being reported. This file establishes the prior question — whether reporting can be avoided at all for a synthetic fixture — and finds that at the legal/statutory level it generally cannot, except through the specific provider-side test/demo mechanisms catalogued above.
