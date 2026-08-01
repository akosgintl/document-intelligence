# Other Hungarian Personal-Identity / Address Documents for the Wayfinder Map

**Scope.** This document resolves GitHub issue #39 ("Research other Hungarian personal/ID documents commonly processed alongside ID/passport/driving licence"), part of the map in issue #33 ("Design Hungarian ID/passport/driving licence + NAV-compatible invoice schemas"). Issue #33 calls for schemas under `schemas/` (see `schemas/invoice/v1.json` for the existing format) for the Hungarian ID card, passport, driving licence, a NAV-compatible invoice, and "at least one additional Hungarian personal/ID document commonly processed alongside these four." This research investigates candidates for that fifth document and makes a recommendation. It does not produce schema JSON — that is the remaining design ticket's job.

Every claim below is either (a) a direct quote or close paraphrase from a page fetched during this research, with the URL given, or (b) explicitly marked as **not confirmed by a fetched primary source** where a page could not be fetched (blocked, 403, or otherwise unreadable) and the claim rests on a search-engine summary or general knowledge instead. Hungarian legal citations are given by their official designation (e.g. "Nytv." for the 1992. évi LXVI. törvény) alongside the URL fetched.

---

## Summary of findings

| Candidate document | Primary-source confirmation it's used alongside ID/passport/licence | Fits this effort's scope (personal-identity/address, not business/financial)? |
|---|---|---|
| Address card (lakcímkártya / lakcímigazolvány) | **Confirmed** — Hungarian AML law (Pmt.) requires it as a mandatory companion document to the identity document during customer due diligence for Hungarian residents. | Yes — it is a personal-identity/address document by statutory definition, structurally simple (small, fixed field set), and has no existing schema in this repo. |
| Residence permit / residence card for non-Hungarian nationals | Plausible by general immigration-onboarding logic, but no fetched source shows it being submitted *alongside* an ID/passport/licence in the same workflow (it typically substitutes for, rather than accompanies, a Hungarian ID card, since holders are by definition not Hungarian citizens). | Yes in principle (personal-identity/residence), but there are multiple non-interchangeable residence-permit card types issued by OIF (national residence card, EEA-family-member residence card, permanent residence card, etc.), making "the" residence permit a much less well-defined single Document Type than the address card. |
| Birth certificate (születési anyakönyvi kivonat) | Not confirmed as a document routinely bundled with ID/passport/licence in identity-verification workflows; found only as a civil-status record obtained for specific legal purposes (name change, first-time ID application, international use). | Weak fit — no photo, no address, not card-formatted, and its content is a birth-registry extract rather than a live identity/address credential. |

**Recommendation:** target the **Hungarian address card (lakcímkártya / lakcímigazolvány)** as the fifth Document Type. Details and citations below.

---

## 1. The Hungarian address card (lakcímkártya / lakcímigazolvány)

### 1a. What it is and who receives it

The Hungarian government portal describes the card's purpose directly: *"A lakcímigazolvány célja a polgár tájékoztatása személyi azonosítójáról és bejelentett lakcíméről"* ("The address card's purpose is to inform the citizen of their personal identification number and registered address"). [kormany.hu — Lakcímigazolvány kiadása](https://kormany.hu/nyilvantartasok/ugyleirasok/lakcimigazolvany-kiadasa)

Eligible recipients, per the same page: Hungarian citizens; persons with long-term residence authorization; recognized refugees; recognized beneficiaries of subsidiary protection; persons with EEA freedom-of-movement/residence rights; and Hungarian citizens resident abroad. The card has **no expiration date**, unlike the ID card, passport, or driving licence. [kormany.hu — Lakcímigazolvány kiadása](https://kormany.hu/nyilvantartasok/ugyleirasok/lakcimigazolvany-kiadasa)

### 1b. Why it exists as a document separate from the ID card

This is a deliberate, statutory privacy design, not an accident of card real estate. The governing law — Nytv., the 1992. évi LXVI. törvény on the registration of citizens' personal data and address — states in **13. § (4)**: *"A személyi azonosítót igazoló hatósági igazolványt úgy kell kiállítani, hogy abból az érintett polgár személyi azonosítója és lakcím adata egyidejűleg ne váljon megismerhetővé"* ("The official document certifying the personal identifier must be issued such that the citizen's personal identifier and address data cannot become simultaneously knowable from it"). [njt.jog.gov.hu — 1992. évi LXVI. törvény](https://njt.jog.gov.hu/jogszabaly/1992-66-00-00.44) This is the statutory basis for the Hungarian ID card carrying no address field at all — address lives exclusively on the separate address card.

### 1c. Statutory field content

Two primary legal sources converge on the same field list:

- **Nytv. 13. § (2)**: *"A személyi azonosítót és lakcímet igazoló hatósági igazolvány tartalmazza a polgár természetes személyazonosító adatait, lakcímét, személyi azonosítóját, az okmány azonosítóját"* — the card contains the citizen's natural-person identification data (name, birth data, mother's name — the term used elsewhere in Hungarian personal-data law), address, personal identifier ("személyi azonosító"), and the document's own identifier. For minors under 14, at the legal representative's request, the card may also carry the legal representative's name and a phone number as of issuance. [njt.jog.gov.hu — 1992. évi LXVI. törvény](https://njt.jog.gov.hu/jogszabaly/1992-66-00-00.44)
- **146/1993. (X. 26.) Korm. rendelet, 16. § (2)–(3)** (the law's implementing decree): confirms the card additionally carries the issuance date, the issuing authority's name, and — per (3) — the personal identifier "gépi olvasásra alkalmas vonalkód formájában is" (also in machine-readable barcode form). [net.jogtar.hu — 146/1993. (X. 26.) Korm. rendelet](https://net.jogtar.hu/jogszabaly?docid=99300146.kor)

So the confirmed field set is: name / natural-person identification data, address, personal identification number ("személyi azonosító", format `x-xxxxxx-xxxx` per a secondary source below), document ID number, issuing authority, issue date, a barcode encoding of the personal identifier, and (optionally, minors only) a legal representative's name and phone number.

A secondary (non-government) source adds unverified layout detail consistent with 13. § (4)'s privacy requirement — that the personal ID number is printed on the reverse side specifically to keep it and the address from being visible at the same time, and gives the number's format as `x-xxxxxx-xxxx` (gender, birth date, sequence digits). This is **not confirmed by a fetched primary government source** and is reported here only as plausible elaboration of the statutory requirement in §1b. [hungarynewsinenglish.com — What is the Hungarian address card?](https://hungarynewsinenglish.com/p/what-is-the-hungarian-address-card-lakcimkartya)

A 2018 research response from Canada's Immigration and Refugee Board, citing KEKKH (the predecessor of today's nyilvantarto.hu registry authority) and the Hungarian Embassy in Ottawa, corroborates that the card format "has not changed" since 2015 and that ID cards issued to immigrants/refugees/subsidiary-protection holders are visually distinct from citizen ID cards — relevant background for the residence-permit comparison in §2a below. [ecoi.net — IRB, Hungary: Identity cards and address cards (HUN106146.E)](https://www.ecoi.net/en/document/1442244.html)

The EU's PRADO document register reportedly lists the address card as an 86mm × 54mm card, first issued 01/03/2012, with indefinite validity — this detail came back only via a search-engine summary; direct fetches of `consilium.europa.eu/prado` pages were blocked with HTTP 403 during this research and the claim is therefore **not confirmed by a fetched primary source**.

### 1d. Confirmed role in identity-verification/onboarding workflows

This is the strongest evidence for the recommendation. Hungary's AML/CFT law — Pmt., the 2017. évi LIII. törvény — defines in **3. §** the accepted identity documents: *"személyazonosság igazolására alkalmas hatósági igazolvány: személyazonosító igazolvány, útlevél, valamint kártya formátumú vezetői engedély"* (ID card, passport, and card-format driving licence — exactly the three document types already in scope for issue #33). Separately, **7. § (3)** requires that a Hungarian-resident customer also present *"lakcímet igazoló hatósági igazolványát"* — the address-certifying official document, i.e. the lakcímkártya — during customer due diligence. [net.jogtar.hu — 2017. évi LIII. törvény (Pmt.)](https://net.jogtar.hu/jogszabaly?docid=a1700053.tv) In other words, Hungarian law itself structures identity verification as "one of {ID card, passport, driving licence} *plus* the address card" — precisely the "submitted alongside" relationship the research question asked about.

A useful contrast/caveat: a document list published by hiteles.gov.hu (NISZ, the National Infocommunication Services company) for a specific downstream trust/e-signature service enumerates only the same three identity documents (ID card, passport, card-format driving licence) as accepted identification, with no mention of the address card. [hiteles.gov.hu — A Szolgáltató által elfogadott személyazonosításra alkalmas okmányok listája (PDF)](https://hiteles.gov.hu/letoltes/511/Szolg%C3%A1ltat%C3%B3%20%C3%A1ltal%20elfogadott%20okm%C3%A1nyok%20list%C3%A1ja.pdf) This is consistent with, not contradictory to, the Pmt. finding above: the address card is not itself an *identity* document (it doesn't independently prove who someone is) — it is the separate, mandatory *address-proof* document required in addition to one of the three identity documents. That two-document pairing is exactly why it's a realistic companion Document Type for this system, distinct in kind from ID/passport/licence rather than a fourth interchangeable option among them.

A generic KYC-vendor page (kyc-chain.com) lists only ID card, passport, and driving licence as "acceptable identity documents" for Hungary and does not mention the address card, residence permit, or birth certificate — but this page uses templated language that appears copied across country pages (it labels the Hungarian ID card "CNIC," a term specific to Pakistani identity documents), so it is treated here as low-reliability, non-primary evidence and given no weight against the Pmt. finding above. [kyc-chain.com — Hungary](https://kyc-chain.com/coverage/hungary/)

---

## 2. Other candidates considered and set aside

### 2a. Residence permit / residence card for non-Hungarian nationals

Hungary's immigration office (OIF, Országos Idegenrendészeti Főigazgatóság) publishes factsheets for several distinct residence-document types, e.g.:

- **National Residence Card**: for third-country nationals who have resided in Hungary "legally and without interruption for at least 3 years" (or qualify via other routes — family reunification, marriage ≥2 years to a Hungarian citizen, former Hungarian citizenship, or as a minor child of a long-term resident). Valid "for an indefinite period of time," with the physical document itself valid "up to 10 years" and renewable. The factsheet does not enumerate the card's printed fields. [oif.gov.hu — National Residence Card](https://oif.gov.hu/factsheets/national-residence-card)
- **Residence Card for Third-Country National Family Member of EEA National**: issued to spouses, dependent children under 21, dependent ascending relatives, or registered partners of an EEA national exercising free-movement rights in Hungary, valid "for a maximum period of five years." Field content not enumerated in the fetched factsheet. [oif.gov.hu — Residence Card for Third-Country National Family Member of EEA National](https://oif.gov.hu/factsheets/residence-card-for-third-country-national-family-member-of-eea-national)

Both require biometric capture (facial photograph and fingerprints) at application. [oif.gov.hu factsheets, general application-process text, cited above]

**Why this is a weaker candidate than the address card for the *next* ticket**, despite being a real personal-identity document:
1. **No single "the" residence permit.** OIF issues multiple non-interchangeable card types (national residence card, EEA-family-member card, permanent residence card, plus others found in the same factsheet index but not fetched in depth here) with different eligibility, validity, and — per the factsheets — likely different printed fields. Picking one Document Type to schema would be an arbitrary choice among several, unlike the address card, which is a single, uniform document.
2. **It doesn't accompany a Hungarian ID card/passport/licence for the same person** — a holder is, by definition, a non-Hungarian-citizen third-country or EEA-family-member national, so in practice it functions as an *alternative* identity credential for onboarding a foreign national, not as a document bundled alongside a Hungarian ID/passport/licence for the same identity-verification case the way the address card is (per the Pmt. 3 §/7 § (3) pairing in §1d). No fetched source shows it submitted in the same package as a Hungarian citizen's ID card, passport, or driving licence.
3. **Scope note (not a blocker on its own):** it is squarely personal-identity in nature, so it isn't excluded by the business/financial-document boundary the way an invoice-adjacent document would be — it's excluded on the "well-defined single document type" and "commonly submitted *alongside*" grounds above, not on subject-matter grounds.

### 2b. Birth certificate (születési anyakönyvi kivonat)

A Hungarian government portal describes the request process for a birth certificate extract, noting it can be requested electronically and that a multilingual version can be requested in up to two foreign languages. [magyarorszag.hu — Születési anyakönyvi kivonat kiállítása iránti kérelem](https://magyarorszag.hu/szuf_ugyleiras?id=92dace7c-71a0-4734-81d3-65d4d1045381) The fetched page did not itself enumerate the certificate's field content, format, or whether it carries a photograph — those specifics are **not confirmed by a fetched primary source** in this research.

**Why this doesn't fit as well, even taking the above at face value:**
- It is a civil-registry extract issued on request for specific legal purposes (e.g. first ID-card application, name changes, international use), not a document routinely carried and re-submitted alongside a live ID card, passport, or driving licence in ordinary identity-verification/onboarding flows — no fetched source shows it bundled with those three the way the Pmt. bundles the address card with them.
- Structurally it is a civil-status record (birth event data — parents, date/place of birth, registration details) rather than a *current* identity/address credential: no photo, no address, and (per general knowledge of anyakönyvi kivonat formats, not independently confirmed here) typically issued as a printed form/certificate rather than a wallet card, which is a much weaker match to this system's existing `invoice`-style schema shape (a small set of scannable, camelCase fields matching a compact physical layout) than the address card's fixed small field set is.

---

## Recommendation

**Target the Hungarian address card (lakcímkártya / lakcímigazolvány) as the fifth Document Type for the remaining design ticket.**

Justification, weighing the findings above:

1. **It is the only candidate with a direct primary-source statement that it is submitted *alongside* one of the ID card/passport/driving licence in a real identity-verification workflow** — Hungary's own AML law structures customer due diligence as exactly that pairing (§1d, Pmt. 3 §/7 § (3)).
2. **It is a single, well-defined document**, unlike the residence-permit family, which splits into several non-interchangeable OIF card types with unconfirmed, likely differing field sets (§2a).
3. **Its field content is fully confirmed by two converging primary legal sources** (Nytv. 13 § and the 146/1993 Korm. rendelet, §1c) and is small and fixed — name/natural-person data, address, personal identifier, document ID, issuing authority, issue date, barcode, and an optional minors-only legal-representative note — a good shape match for this repo's existing compact `schemas/invoice/v1.json`-style camelCase field list.
4. **It stays inside this effort's stated scope**: a personal-identity/address document, not a business/financial one, and complements rather than duplicates the ID card/passport/driving licence schemas already planned in issue #33.

The birth certificate is set aside for weak evidence of being routinely bundled with the other three, and an unconfirmed, less structured field/format profile (§2b). The residence permit is set aside primarily for lacking a single canonical card type and for functioning as an alternative rather than a companion to a Hungarian ID/passport/licence (§2a) — it remains a reasonable follow-up candidate for a *future* map focused on foreign-national onboarding specifically, should one arise.
