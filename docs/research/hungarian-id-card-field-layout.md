# Hungarian ID Card (Személyi Igazolvány) Field Layout

**Scope.** This document researches, from Hungarian government/legal primary sources where fetchable, EU legal primary sources, and secondary sources explicitly flagged as such, what fields the Hungarian national identity card (`személyi igazolvány` / formally `személyazonosító igazolvány`) prints — across the pre-2016 laminated plastic card (issued 2000–2016) and the current chip-based eID card (issued since 1 January 2016, and since 2 August 2021 mandatorily with a storage element per EU Regulation 2019/1157) — and whether/how the back of the current card carries a machine-readable zone (MRZ). This is issue #35 of the Wayfinder planning map for issue #33 (Hungarian ID/passport/driving-licence + NAV invoice schemas). Per that ticket, this document is **research only** — it captures facts with citations and does not propose or write any JSON Schema.

Every claim below is either (a) a direct quote or close paraphrase from a page or legal text fetched during this research, with the URL given, or (b) explicitly marked **not confirmed by a fetched primary source** where only secondary sources were findable, or the primary source could not be fetched (e.g. blocked, 404, parked domain). Nothing is asserted from training-data memory alone.

---

## Summary of findings

| Question | Answer | Confidence |
|---|---|---|
| Does the current (2016+) eID card carry an MRZ on the back? | **Yes.** Confirmed by the current issuance decree, which requires the machine-readable data row to be built to ICAO 9303 spec, and by EU Regulation 2019/1157 (directly applicable in Hungary), which mandates an ICAO-9303 MRZ on all EU national ID cards issued from 2 August 2021. | Primary source (Hungarian decree text + EU regulation text) |
| Did the pre-2016 (2000–2016) laminated plastic card also carry an MRZ? | **Yes.** The 2000–2016 card's own issuance decree (in force from 1 January 2000) states the card contains the same data "also in machine-readable form" (`gépi olvasásra alkalmas adatsor formájában`). This contradicts some secondary/forum sources that suggested the MRZ only arrived in 2016. | Primary source (Hungarian decree text, 1999) |
| Is the citizen's personal ID number (`személyi azonosító`, 11 digits) printed anywhere on the card face? | **No — not on current cards.** It is stored electronically in the chip (`tároló elem`) only; the government's own procedural page lists it separately from "visually perceptible data" (`vizuálisan is érzékelhető adatok`). | Primary source (kormany.hu) |
| What is printed on the card face instead, as its own unique number? | A separate **document number** (`okmányazonosító`), format 6 digits + 2 letters (e.g. `123456AA`), distinct from the personal ID number. | Primary source (kormany.hu) for the distinction; secondary forum source for the exact character-format example |
| Do pre-2016 and 2016+ cards differ in printed (visible) fields? | Only modestly — the core visible field set (name, birth data, mother's name, nationality, sex omitted/optional, photo, signature, document number, dates, issuing authority) is stable across both. The major difference is the addition of a chip (`tároló elem`) in 2016+ cards, storing biometrics and other identifiers that are *not* printed on either card's face. | Primary source (both decrees) + secondary (Wikipedia, IRB Canada) |
| Standard external references describing the layout? | Hungary's own government decrees (168/1999 and 414/2015, both Korm. rendelet) are the operative primary sources; both explicitly defer the MRZ's technical structure to **ICAO Document 9303**. The current card's overall EU-mandated format (ID‑1, MRZ, storage medium, biometrics) is set by **EU Regulation (EU) 2019/1157**, fetched and quoted below. The EU Council's **PRADO** register (which normally documents exact Hungarian card imagery/layout) could not be fetched — it returned HTTP 403 to this research's automated requests. | Primary sources fetched for the legal requirements; PRADO inaccessible |

---

## 1. Front-of-card fields — current eID card (2016+)

The Hungarian government's own procedural page for the "Állandó személyazonosító igazolvány" (permanent ID card), fetched in full, distinguishes "visually perceptible data" (`vizuálisan is érzékelhető adatok`) from chip-only data. Quoting directly:

> "A vizuálisan is érzékelhető adatok közül változik az okmányazonosító, a kiállítás ideje, a gépi olvasásra alkalmas adatsor (MRZ), a kódszám (CAN) és az adattároló kód (QR)."

("Among the visually perceptible data, the document identifier, the date of issue, the machine-readable data row (MRZ), the code number (CAN), and the data-storage code (QR) change [when the card is replaced].") — [kormany.hu, Állandó személyazonosító igazolvány](https://kormany.hu/nyilvantartasok/ugyleirasok/szemelyazonosito-igazolvany)

The same page and the current issuance decree, **414/2015. (XII. 23.) Korm. rendelet** ("a személyazonosító igazolvány kiadása és az egységes arcképmás- és aláírás-felvételezés szabályairól"), together establish the following as visible/printed card content (fetched via [net.jogtar.hu](https://net.jogtar.hu/jogszabaly?docid=a1500414.kor)):

- Full name (family name + given name(s))
- Birth name, if different from current name
- Place of birth
- Date of birth
- Mother's name
- Nationality — printed as a **three-letter country code** per § 33(4) of the decree (the same three-letter-code convention as the earlier 1999 decree's § 7(2), see §4 below)
- Photograph
- Signature (holders aged 12+)
- Document number (`okmányazonosító`)
- Date of issue
- Date of expiry / validity period
- Name of the issuing authority
- Hungary's ISO 3166-1/3166-2-derived state code
- **CAN (Card Access Number)** — a 6-digit code
- **QR code** (referred to as the "adattároló kód" / data-storage code)
- The machine-readable zone (MRZ) — see §5 below for whether this is front or back

A secondary source (a Hungarian consumer/finance site, not a government page) gives a specific physical placement for the CAN code that this research could not independently confirm from a primary source:

> "A CAN szám az eSzemélyi fényképes oldalának, előlapjának jobb alsó részén található, 6 jegyű szám... amelyek függőlegesen vannak kinyomtatva." ("The CAN number is a 6-digit number located on the bottom-right of the photo side / front of the eSzemélyi, printed vertically.") — **not confirmed by a fetched primary source**; [Pénzcentrum.hu, "Ezt kell tudni az új e-személyi kapcsán"](https://www.penzcentrum.hu/karrier/20210717/ezt-kell-tudni-az-uj-e-szemelyi-kapcsan-mi-az-az-e-szemelyi-igazolvany-az-e-szemelyi-regisztracios-kod-hol-van-1116160)

A secondary but detailed tertiary source, the Canadian Immigration and Refugee Board's (IRB) research response on Hungarian identity documents, lists the same field set independently and states its own primary sourcing (KEKKH's website, the Hungarian Embassy in Ottawa, the Hungarian Civil Liberties Union, and PRADO):

> Front/visible information: "Name, place and date of birth, nationality, mother's name, sex, facial portrait, signature (if 12+), card expiry date, document number/identifier, issuance date, issuing authority name, CAN number, and data storage code." — [ecoi.net, IRB Canada, HUN106146.E](https://www.ecoi.net/en/document/1442244.html) (secondary/tertiary; cites named primary contacts this research could not independently re-verify)

**Sex/gender as a printed field is not confirmed** from a Hungarian primary source fetched during this research. EU Regulation 2019/1157 (see §9) makes gender/sex designation **optional** on EU ID cards generally ("the designation of a person's gender shall be optional" — Art. 3(2)); whether Hungary in practice includes it on the printed card face was not independently confirmed from a Hungarian primary source in this research (the IRB secondary source above lists "sex" as printed, but this is not corroborated by the fetched Hungarian government/legal primary sources).

---

## 2. Back-of-card fields and MRZ — current eID card (2016+)

The current issuance decree is explicit that the MRZ exists and states its technical basis:

> **§ 33(5):** "A magyar állampolgár részére kiállított személyazonosító igazolvány az Nytv. 29. § (3) bekezdése szerinti gépi olvasásra alkalmas adatsora az ICAO 9303 számú dokumentum előírásai alapján épül fel." ("The machine-readable data row of the ID card issued to a Hungarian citizen, per § 29(3) of the Nytv. [the personal-data-and-address-registration Act], is built according to the specifications of ICAO Document 9303.") — **414/2015. (XII. 23.) Korm. rendelet**, § 33(5), fetched via [njt.jog.gov.hu](https://njt.jog.gov.hu/jogszabaly/2015-414-20-22.42)

This document could not fetch an explicit Hungarian-government statement of which physical side (front vs. back) the MRZ sits on. General ICAO 9303/TD1 practice — and the consistent pattern across all EU 2019/1157-compliant national ID cards — places the MRZ on the back, with the photo/personal-data panel on the front; this is stated by multiple secondary sources but **not independently confirmed by a fetched Hungarian primary source** for the Hungarian card specifically:

> "The MRZ is generally located on the back of the identity card, in the lower part of the document." — secondary summary of ICAO 9303/TD1 practice, not Hungary-specific — surfaced via web search of generic MRZ explainer content (didit.me, TrustDocHub; not fetched as primary ICAO text)

A Hungarian community Q&A thread (low-trust, crowd-sourced, explicitly flagged as such) describes the MRZ's field content in a way consistent with ICAO 9303 TD1 structure:

> Components identified: a document-type indicator ("I" for identity), Hungary's country code ("HUN"), the document number, date of birth (YYMMDD), sex, expiry date (YYMMDD), name field, and multiple check digits. — **not confirmed by a fetched primary source**; [gyakorikerdesek.hu thread](https://www.gyakorikerdesek.hu/egyeb-kerdesek__egyeb-kerdesek__10755884-a-szemelyigazolvanyon-levo-mrz-kod-milyen-adatokbol-epul-fel)

This is consistent with the standard ICAO 9303 **TD1** format (three lines of 30 characters each, used for ID-1-sized cards), which this research did not fetch directly from ICAO's own document but which is described consistently across secondary technical sources:

> "The TD1 format... consists of three lines of thirty characters and is suited to smaller documents, such as card-sized identity cards... encodes the document type and issuing country, the holder's name, the document number and nationality, the date of birth, sex, and expiry date, plus a series of check digits computed using a 7-3-1 weight cycle." — **not confirmed by a fetched primary ICAO source in this research**; paraphrased from web-search summaries of ICAO 9303 (tiny-idp.com, TrustDocHub, Signzy)

Whether the current Hungarian card uses the TD1 3×30 layout specifically (as opposed to another ICAO-9303-compliant MRZ layout) is **not independently confirmed by a fetched primary source** — the Hungarian decree (§33(5) above) only says the MRZ is "based on the specifications of ICAO Document 9303" without this research being able to fetch the Annex/technical-specification text that would pin down the exact line count.

The IRB Canada secondary source adds one MRZ-scope caveat not found elsewhere:

> "Permanent personal ID cards issued to foreign citizens or stateless persons do not have an MRZ code; instead, there is an indication that the card holder is not entitled to travel abroad." — [ecoi.net, IRB Canada, HUN106146.E](https://www.ecoi.net/en/document/1442244.html) (secondary; describes cards issued to non-citizens, not the Hungarian-citizen card that is this ticket's focus)

---

## 3. Chip ("tároló elem") contents — current eID card (2016+)

The chip is legally mandatory for all cards requested from 2 August 2021 onward, per the government's own procedural text:

> "2021. augusztus 2. napját követően kizárólag tároló elemet tartalmazó okmány adható ki. A tároló elem tartalmazza birtokosának arcképét és 2 ujjnyomatát..." ("From 2 August 2021 only a document containing a storage element may be issued. The storage element contains the holder's facial image and 2 fingerprints...") — [kormany.hu](https://kormany.hu/nyilvantartasok/ugyleirasok/szemelyazonosito-igazolvany)

The same page, describing what a replacement card's chip will hold, gives a fuller list:

> "...az tartalmazni fogja az igénylő TAJ számát, adóazonosító jelét, személyi azonosítóját és lakcímadatát." ("...it will contain the applicant's social security number [TAJ], tax ID number, personal ID number, and address data.") — [kormany.hu](https://kormany.hu/nyilvantartasok/ugyleirasok/szemelyazonosito-igazolvany)

So the chip (not the printed face) holds:

- Facial image and 2 fingerprints (mandatory for holders 6+, per EU Regulation 2019/1157 Art. 3(5)/(7), see §9)
- Personal ID number (`személyi azonosító`) — **not printed on the face**
- Address data (`lakcímadat`)
- Social security number (TAJ)
- Tax ID number (`adóazonosító jel`)
- An electronic unique identifier for the card itself
- Optionally, emergency contact phone number(s) and e-signature credentials (on some issuances; the same source notes a *replacement* card specifically will *not* carry the emergency-contact number or e-signature service: "a tároló elem nem fogja tartalmazni a vészhelyzet esetén értesítendő telefonszámo(ka)t, valamint az e-aláírás szolgáltatást")

---

## 4. Pre-2016 laminated plastic card (issued 2000–2016)

The card-format ID (replacing the earlier paper booklet) was introduced by **168/1999. (XI. 24.) Korm. rendelet**, in force from 1 January 2000 (§ 49(1)). This research fetched the consolidated (May-2012-in-force) Hungarian-language text of this decree, hosted as a PDF by the EUI Global Citizenship Observatory (an academic mirror of the primary legal text, not the Hungarian government's own hosting, but the decree text itself is quoted directly, not summarized by a third party): [data.globalcit.eu, HUN Decree No. 168](https://data.globalcit.eu/NationalDB/docs/HUN%20Decree%20No%20168_consolidated%20version_ORIGINAL%20LANGUAGE.pdf).

Key provisions on card content:

> **§ 7(1):** "Az állandó személyazonosító igazolvány az Nytv. 29. §-ának (3) bekezdésében meghatározott személy- és okmányazonosító adatokon kívül tartalmazza a személyazonosító igazolvány kiállításának keltét, a kiadó magyar állam kódját és a kiállító hatóság nevét." ("The permanent ID card, beyond the person- and document-identifying data defined in Nytv. § 29(3), also contains the date of issue of the ID card, the code of the issuing Hungarian state, and the name of the issuing authority.")

> **§ 7(2):** "A magyar állampolgár... állampolgársági adatát a személyazonosító igazolványban - az országnevek kódjaira vonatkozó nemzeti szabvány alkalmazásával - háromjegyű betűkód formájában kell feltüntetni." ("The citizenship data of a Hungarian citizen... must be shown on the ID card as a three-letter country code, per the national standard for country-name codes.")

> **§ 7(3): "Az állandó személyazonosító igazolvány az (1)-(2) bekezdésben meghatározott adatokat gépi olvasásra alkalmas adatsor formájában is tartalmazza."** ("The permanent ID card also contains the data defined in subsections (1)-(2) in machine-readable form.") — **this is the primary-source basis for this document's finding that the 2000–2016 card already had an MRZ**, not only the 2016+ eID card.

> **§ 8:** base card color is blue for Hungarian citizens' permanent ID cards, yellow for cards issued to immigrant/settled/refugee/protected-status persons (§ 8(1)–(2)).

> **§ 30:** detailed rules on which name variant is entered (birth-register name; both languages for a national-minority citizen; a married woman's name with the "-né" suffix; doctoral-title entry rules; illiterate/`írásképtelen` applicants get no signature field entry).

Because § 7(1) explicitly frames the card's content as "the person- and document-identifying data defined in Nytv. § 29(3)" **plus** issue date, state code, and issuing-authority name, the base personal/document data set (name, birth name if applicable, birthplace, birth date, mother's name, document number) is defined one level up, in the **Nytv.** itself (1992. évi LXVI. törvény, "a polgárok személyi adatainak és lakcímének nyilvántartásáról" — the personal-data-and-address-registration Act). This research located the Act at [net.jogtar.hu](https://net.jogtar.hu/jogszabaly?docid=99200066.tv) but the fetched excerpt was truncated before § 29 — **the exact enumerated field list inside Nytv. § 29(3) itself is not independently confirmed by a fetched primary source in this research**; the 168/1999 decree's own text (quoted above) is used instead as the operative primary-source description of card content.

Secondary sources (Hungarian Wikipedia, fetched and explicitly flagged as secondary) corroborate a matching front-field list for the 2000–2016 card and add packaging/branding details not found in the decree text itself:

> Visible data: "a polgár nevét, születési helyét, születési idejét, állampolgárságát, anyja nevét, arcképét, saját kezű aláírását, a személyazonosító igazolvány sorszámát és érvényességi idejét" (name, birthplace, birth date, citizenship, mother's name, photograph, signature, card serial number, validity period), plus issuance date, issuing authority name, and an ISO-3166-2-derived country code; base color blue for citizens. — **secondary source**, [hu.wikipedia.org, Személyi igazolvány](https://hu.wikipedia.org/wiki/Szem%C3%A9lyi_igazolv%C3%A1ny)

> Card format/dimensions: ID-1 (85.6 × 53.98 mm) per ISO/IEC 7810. — **secondary source**, same Wikipedia article, via WebSearch synthesis

The 2000–2016 card did **not** have a chip; the earlier (pre-2000) format was a soft-cover 16-page booklet, not a card at all, and predates the "laminated card" the ticket asks about — noted here only for context and **not** analyzed further since it is outside the ticket's explicit pre-2016-laminated vs. current-eID comparison scope.

---

## 5. Differences between the pre-2016 card and the current eID card

| Aspect | 2000–2016 laminated card | 2016+ eID card |
|---|---|---|
| Physical medium | Plastic card, ID-1 size, no chip | Plastic (polycarbonate) card, ID-1 size, **with contactless chip** |
| Front/visible field set | Name, birthplace, birth date, nationality (3-letter code), mother's name, photo, signature, document number, validity period, issue date, issuing authority | Same core set, **plus** CAN code and QR code (not present pre-2016, since these relate to chip access) |
| MRZ | Present — per § 7(3) of 168/1999. (XI. 24.) Korm. rendelet ("also in machine-readable form") | Present — per § 33(5) of 414/2015. (XII. 23.) Korm. rendelet, explicitly built to ICAO 9303 |
| Chip / electronic storage | None | Facial image + 2 fingerprints (mandatory since 2 Aug 2021), personal ID number, address, TAJ (social security) number, tax ID number, electronic unique identifier, optionally emergency contact number(s) and e-signature credentials |
| Personal ID number on the card | Not confirmed either printed or electronic (the card had no chip to hold it electronically, and this research found no primary-source statement that it was printed on the 2000–2016 card face either) | Confirmed **not printed** on the face; held only in the chip |
| Legal basis | 168/1999. (XI. 24.) Korm. rendelet | 414/2015. (XII. 23.) Korm. rendelet, tightened by EU Regulation 2019/1157 from 2 Aug 2021 |

Sources: as cited in §§1–4 above.

---

## 6. Personal identification number vs. document number — resolving the two-numbers confusion

This research specifically tracked which of Hungary's two easily-confused numbers is printed on the card:

1. **`személyi azonosító`** (a.k.a. "személyi szám" colloquially) — the citizen's own **personal identification number**, an 11-digit number. Per the Hungarian government's own procedural page, on current (2016+) cards this is **stored only in the chip**, listed separately from "visually perceptible data": "Amennyiben a pótlási eljárásban kiállított személyazonosító igazolvány tároló elemmel rendelkezik, az tartalmazni fogja az igénylő ... személyi azonosítóját ..." — [kormany.hu](https://kormany.hu/nyilvantartasok/ugyleirasok/szemelyazonosito-igazolvany). Historically, this number type has a fraught legal history in Hungary: a secondary source (Hungarian Wikipedia) states a predecessor "10-digit" universal personal number was **struck down by the Hungarian Constitutional Court in 1991** (decision 15/1991. (IV.13.)) as an unconstitutional universal identifier, which is why Hungary does not print it plainly on identity documents today — **not independently confirmed by this research against the Constitutional Court decision itself**, only against the secondary Wikipedia summary citing it.
2. **`okmányazonosító`** — the ID **card's own document number**, a serial number **printed on the card face**, in the format **6 digits + 2 letters** (e.g. `123456AA`), per a secondary Hungarian-language source cross-checked against the government's listing of it among visually perceptible data: "Az igazolvány okmányazonosítója... tartalmaz sorszámot (hatjegyű szám) és a sorozat jelölést (két betű). Példaként: 123456AA... Az igazolványon egy okmányazonosító található, amely a személyi igazolvány azonosítására alkalmas [és] eltér a személyi azonosítótól." ("The card's document identifier... contains a serial number (six digits) and a series designator (two letters). Example: 123456AA... The card carries one document identifier, suitable for identifying the ID card itself [and] distinct from the personal ID number.") — **secondary source**, surfaced via WebSearch of a Hungarian forum ([hup.hu](https://hup.hu/node/184270)), not independently verified against a government-hosted specimen image in this research.

**Conclusion on this sub-question:** only the document number (`okmányazonosító`) is printed on the card face; the personal ID number (`személyi azonosító`) is not printed and, on the current card, lives only in the chip. This is confirmed by the primary kormany.hu source; the exact document-number character format (6 digits + 2 letters) rests on a secondary source only.

---

## 7. External standards / references describing the layout

- **ICAO Document 9303** ("Machine Readable Travel Documents") — both Hungarian decrees fetched during this research (168/1999 § 7(3) implicitly via "gépi olvasásra alkalmas adatsor," and 414/2015 § 33(5) explicitly) tie the MRZ's technical construction to this standard. This research did **not** fetch ICAO 9303 itself (e.g. from icao.int); the TD1 3-line/30-character layout described in §2 above is sourced from secondary technical explainer sites, not ICAO's own document, and is flagged accordingly.
- **EU Regulation (EU) 2019/1157** of 20 June 2019 "on strengthening the security of identity cards of Union citizens..." — fetched in full as a PDF from EUR-Lex ([eur-lex.europa.eu, CELEX:32019R1157](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32019R1157)). This is directly applicable EU law (a Regulation, not a Directive) and has applied since **2 August 2021** (Art. 16). Key provisions:
  - **Art. 3(1):** "Identity cards issued by Member States shall be produced in ID-1 format and shall contain a machine-readable zone (MRZ). Such identity cards shall be based on the specifications and minimum security standards set out in ICAO Document 9303..."
  - **Art. 3(2):** "The data elements included on identity cards shall comply with the specifications set out in part 5 of ICAO document 9303. By way of derogation from the first subparagraph, the document number may be inserted in zone I and the designation of a person's gender shall be optional."
  - **Art. 3(3):** the card must bear the title "Identity card" (or an established national designation) in the issuing Member State's official language, plus the words "Identity card" in at least one other official EU language.
  - **Art. 3(4):** front side must show the two-letter Member State country code "printed in negative in a blue rectangle and encircled by 12 yellow stars."
  - **Art. 3(5)–(7):** the card must include a highly secure storage medium containing a facial image and two fingerprints in interoperable digital format, with exemptions for children under 6 (and optionally under 12) and persons physically unable to give fingerprints.
  - **Art. 4:** minimum validity 5 years, maximum 10 years, with derogations (minors, special/limited circumstances, persons 70+).
  - **Art. 5:** phase-out schedule — cards lacking the Art. 3 security standards cease to be valid by their expiry or **3 August 2031** at the latest; cards lacking even ICAO 9303 part-2 minimum security standards or a functional MRZ are phased out by **3 August 2026**.
  - This Regulation contains **no separate Annex** detailing an exact field-by-field visual layout (this research fetched the full regulation text through Art. 16 and confirmed no Annex I of that kind exists in it, contrary to what this research initially expected going in) — the data-element specification is delegated entirely to ICAO 9303 part 5 by reference (Art. 3(2)), not spelled out in the Regulation itself.
- **PRADO** (Council of the EU's Public Register of Authentic Identity and Travel Documents Online) — the standard EU cross-reference for exact national document imagery/layout (`consilium.europa.eu/prado`). This research attempted to fetch several Hungarian PRADO entries (e.g. `HUN-HO-11002`, `HUN-HO-09003`) and PRADO's Hungary document-listing pages; **all requests returned HTTP 403 Forbidden**, including retries with a browser-like User-Agent header. PRADO could not be used as a source in this research despite being the most likely primary source for an exact front/back image-annotated layout.
- **Hungarian government primary legal/procedural sources used:** `kormany.hu` (government portal, current procedural description); `414/2015. (XII. 23.) Korm. rendelet` (current eID issuance decree, fetched via `net.jogtar.hu` and `njt.jog.gov.hu`); `168/1999. (XI. 24.) Korm. rendelet` (2000–2016 card issuance decree, fetched as a consolidated PDF via `data.globalcit.eu`). Two other expected Hungarian primary sources could **not** be fetched during this research: `nyilvantarto.hu/hu/szig` returned HTTP 404, and `eszemelyi.hu` resolved to a parked-domain placeholder page rather than the expected official eSzemélyi FAQ site.

---

## 8. Sources attempted but inaccessible during this research

For completeness/reproducibility, the following URLs were attempted and could not be used as sources:

- `https://www.nyilvantarto.hu/hu/szig` — HTTP 404
- `https://www.nyilvantarto.hu/hu/fogalmak_szig` — HTTP 404
- `https://eszemelyi.hu/gyakran-ismetlodo-kerdesek/` and `https://eszemelyi.hu/gyik/gyik_altalanos_info` — domain-parking placeholder page, no real content served
- `https://www.consilium.europa.eu/prado/en/HUN-HO-11002/index.html`, `HUN-HO-09003`, and the PRADO Hungary document-listing pages — HTTP 403 Forbidden (both via the WebFetch tool and via direct `curl` with a browser User-Agent)
- `https://london.mfa.gov.hu/en/szemelyi-igazolvany` and `https://edinburgh.mfa.gov.hu/en/eid-card` (Hungarian consulate pages) — fetched but returned only page headers/navigation, no substantive body content in the fetched excerpt
- `https://www.gyomro.hu/dox/okmanyiroda/szemelyi_igazolvany.pdf` — fetched but the tool could not extract readable text from the PDF's internal encoding
- `https://net.jogtar.hu/jogszabaly?docid=99200066.tv` (the underlying Nytv. Act, § 29) — fetched but the returned excerpt was truncated before reaching § 29, so the Act's own enumerated field list could not be independently confirmed (the 168/1999 decree text was used instead, as noted in §4)
