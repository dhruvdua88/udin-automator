# UDIN — Official Requirements for an Automated Generator (ICAI)

**Prepared for:** Dhruv Dua & Co (CA firm) — UDIN automation project, research phase
**Author:** `udin-official` (research teammate)
**Date prepared:** 27 October 2026 · **All URLs accessed:** 27 October 2026
**Evidence tags:** `[OFFICIAL]` = ICAI / udin.icai.org / ICAI-published PDF · `[SECONDARY]` = CA press, blogs, news · `[INFERENCE]` = my reasoning from cited facts.

> **Bottom line for the product:** the UDIN portal (now on ICAI's **DigiCA** platform) is a *member-only, OTP-gated, human-in-the-loop* web form. It exposes **no document upload, no client-name field, no document-number field and no public generation API**, and every submission requires an OTP to the member's SSP-registered mobile **and** email plus a CAPTCHA at login. An app can therefore **prepare, validate, store and track UDIN payloads** and (at most) drive a browser session, but it cannot legitimately generate UDINs headlessly on the member's behalf.

---

## 1. What UDIN is and its regulatory basis

UDIN (Unique Document Identification Number) is an **18-digit system-generated unique number for every document certified/attested by a full-time practising Chartered Accountant**, introduced to curb certification by non-CAs impersonating members and to let regulators/banks verify authenticity `[OFFICIAL]` ([FAQs on UDIN, 4th Ed., updated 2 Jul 2024, Q1–Q3](https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf)).

**Source of the mandate:** ICAI **Council decision at its 379th meeting (17–18 December 2018)**, implemented in phases `[OFFICIAL]` (FAQ Q5, same PDF):

| Phase | Documents covered | Effective from |
|---|---|---|
| 1 | All **Certificates** (incl. reports in lieu of certificates per GN on Reports/Certificates for Special Purposes, Rev. 2016) | **1 Feb 2019** |
| 2 | All **GST Audit Reports** (CGST Act 2017) and **Tax Audit Reports** (IT Act 1961) | **1 Apr 2019** |
| 3 | All other **Audit, Assurance and Attestation** functions | **1 Jul 2019** |

**No monetary or turnover threshold exists** anywhere in the FAQs or portal manual — coverage is defined by *document class*, not by amount `[OFFICIAL]` (FAQ Ch. 4–8; absence of any threshold in [User Manual v1.2](https://blog.saginfotech.com/wp-content/uploads/2025/12/icai-udin-portal-manual-updated.pdf)). This was checked specifically because the project brief assumed thresholds might exist.

**Who must generate** `[OFFICIAL]` (FAQ Q6–Q13, Q84):
- Only **practising CAs holding a full-time Certificate of Practice (CoP)**; part-time CoP holders cannot.
- **Only the signing partner/proprietor** generates — never another partner. If two partners sign, **two UDINs**.
- **Firms cannot register/login**; a firm's UDINs are visible only to the "head in charge" per SSP data.
- Members in industry, and members without a current full-time CoP, cannot generate (they may only *view* past UDINs).

**Exemptions / not required** `[OFFICIAL]` (FAQ Q34, Q37, Q38, Q104, Q109, Q124):
certified true copies · auditor's resignation · NOC from previous auditor · consent letter + certificate u/s 139 Companies Act 2013 · peer review report · attestation of CA students' exam forms/marksheets · UDIN also not required on the financial statements themselves (only on the audit report).

**Cardinality rule (drives the app's data model):** **one UDIN per assignment × per signatory × per signing date**. Separate UDINs are required for standalone vs consolidated statements, for each quarterly/limited review, for each bank-branch location, and for tax audit vs statutory audit; but **one** UDIN covers Form 3CA+3CD (or 3CB+3CD) and all annexures of one report, and **one** UDIN covers a bank branch audit report incl. LFAR and its certificates `[OFFICIAL]` (FAQ Q39, Q74–Q79, Q96–Q99, Q128).

---

## 2. UDIN number format

`[OFFICIAL]` FAQ Q4: syntax **`YY MMMMMM AAAAAANNNN`** — 18 characters, example `19304576AKTSBN1359`:

| Position | Length | Meaning |
|---|---|---|
| 1–2 | 2 digits | `YY` — last two digits of the **year of generation** (`19` = 2019) |
| 3–8 | 6 digits | `MMMMMM` — the member's **ICAI Membership (Registration) Number**, e.g. `304576` |
| 9–18 | 10 chars | `AAAAAANNNN` — **randomly generated alphanumeric** by the system (e.g. `AKTSBN1359`). **Contains no document-type code.** |

`[INFERENCE]` Practical consequences: the number **cannot be pre-computed or predicted** by an app; it must be read back from the portal after submission. It is *not* an encoding of document type — document type lives only in the portal's record, so any app-side mapping of document type → code is unnecessary (and would be invented data). Each UDIN is issued with a **QR code** that deep-links to the pre-filled Verify UDIN page `[OFFICIAL]` (FAQ Q16; Manual v1.2 §3).

---

## 3. Document types and the exact generation-time fields

The DigiCA-era portal has **three main categories only**, with sub-categories beneath each `[OFFICIAL]` (Manual v1.2, TOC and §3; confirmed by the [Addendum to FAQs 5th Ed.](https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html) republished verbatim):

| # | Category | Sub-category depth | Sub-category count |
|---|---|---|---|
| 1 | **Certificates** | "Type of Certificate" dropdown | **40 categories** per Manual v1.2 §3(i) (the Jul-2024 FAQ listed 36 + "Others") |
| 2 | **GST & Tax Audit** | "Particulars of Section / Form under which Report issued" | illustrative dropdown (IT Act 1961 / CGST Act 2017 forms) |
| 3 | **Audit & Assurance Functions** | "Type of Audit" + "Under Act / Law / Statute / Regulation" | two illustrative dropdowns |

### 3.1 Common header fields (all three categories)

`[OFFICIAL]` Manual v1.2 §3; Addendum Q16:

| Field | Mandatory? | Notes |
|---|---|---|
| Name, MRN, Email, **PAN of member**, Pincode | pre-filled, read-only | fetched live from **SSP** — the app must never store/derive these |
| **FRN** of firm | Yes (dropdown) | "NA / Not Applicable / Individual Capacity" allowed if not signing for a firm |
| **Document type** (category) | Yes | 3 options above |
| Sub-category / Form / Section / Type of Audit / Act | Yes | depends on category |
| **Date of Signing of Document** | Yes | actual signing date; UDIN may be generated up to **60 days** after (see §6) |
| **Key fields** (particulars + figures/values) | Yes, category-specific | dynamic rows, "Add More" |
| **Document Description** | Yes | **5–250 characters** (Manual v1.2 / Addendum Q32) — note the older FAQ said 15–250; the portal reduced the floor to 5. Only `. , _ - –` special characters allowed |
| Remarks | Optional | internal reference, not shown to verifier |
| Document upload | **Not required** | FAQ Q18 — no document is ever uploaded |

### 3.2 Certificates

`[OFFICIAL]` FAQ Q30/Q33 + Addendum Q32 + Manual v1.2 §3(i):
- **3 key-field rows**, of which **2 are mandatory**; each row = *particulars description (≤50 chars)* + *figure/value* + (for numeric rows) a **denomination** field; extra rows via "Add More".
- **Dynamic typing** (new in DigiCA): the portal offers **Numeric / Alphanumeric / Numeric-and-Alphanumeric** modes — if "Numeric & Alphanumeric", rows 1–2 accept only numbers and later rows accept alphanumerics.
- If the certificate has **no financial figure**, enter **0** and state "There is no Financial Figure in Certificate" in the particulars.
- "Add More" is explicitly allowed to capture further figures from the certificate.
- Certificate list (FAQ 4th Ed. Q29, illustrative, 36 named + Others): Net worth/Capital Contribution; bank/insurance statutory auditor certificates; KYC sole-proprietorship; RERA; liquid asset u/s 45-IB RBI Act; physical verification of securities (concurrent audit); short sale of securities; sources of income; deductions/exemptions; funds/grants utilisation (Charitable Trust, NGO, Statutory Authority, FERA/FEMA); **Form 15CB**; IPO/ICDR-LODR compliances; certificates from statutory records under Companies Act 2013; LLP Act; indirect-tax refund; **GST refund**; arms-length price u/s 92; fair value of shares (buy-back, merger/de-merger, resident→non-resident transfer, further allotment); exchange-control certifications; income-tax deduction certifications; net worth for bank finance / bank guarantee / student loan / visa; RBI statutory auditor certificate for NBFCs; turnover; working capital; Others. `[INFERENCE]` Treat this list as illustrative and ship it as *configurable seed data* — the authoritative current set is the 40-item dropdown visible only after login.

### 3.3 GST & Tax Audit

`[OFFICIAL]` FAQ Q43–Q46 + Manual v1.2 §3(ii) + Addendum Q46:

| Field | Mandatory? | Detail |
|---|---|---|
| Form / Section (e.g. 44AB + Form 3CA/3CB/3CD; 92; 115JB(4) Form 29B; CGST s.35(5) Form 9C; s.66(1) Form ADT-04) | Yes | illustrative dropdown; "Other Report under IT Act, 1961" fallback |
| **PAN of assessee/auditee** | **Yes (new)** | **5th validation parameter** at the e-filing portal alongside MRN, UDIN, AY/FY and Form No. **Not visible to verifier** |
| Date of signing | Yes | |
| **Auditor's Opinion on Financial Statements** | **Yes (new, compulsory)** | "Applicable? Yes/No"; if Yes → Unmodified / Qualified / Adverse / Disclaimer. **Not visible to verifier** |
| **Preceding year's audit details** | **Yes (new, compulsory** for GST & Tax Audit and Audit & Assurance) | Council 442nd meeting decision: Was preceding-auditor capture applicable? → Have you audited the entity last year (Yes/No/First Year of Audit) → if Yes: previous-year UDIN (select or type); if No: previous auditor's MRN/FRN, whether communication made + date, outstanding-fees status (Yes/No/Not Known). **Not visible to verifier** |
| Key fields — **s.44AB**: Total Turnover (Form 3CD); Net Profit/Turnover ratio (3CD); WDV of Fixed Assets (3CD); **Assessment Year (YYYY-YYYY)** | 4 mandatory | + 3 optional key fields incl. PAN of assessee (pre-DigiCA) |
| Key fields — **GSTR-9C (s.35(5))**: turnover incl. exports per audited FS (Cl.5A); turnover per GSTR-9 (Cl.5Q); **FY (YYYY-YYYY)**; additional GST declared in GSTR-9; additional interest accrued; total ITC reversed | 6 mandatory | + 2 optional incl. **GSTIN** |
| Key fields — **ADT-04 (s.66(1))**: short payment of tax; any other amount; **FY (dd-mm-yyyy–dd-mm-yyyy)** | 3 mandatory | + 2 optional incl. GSTIN |

`[OFFICIAL]` Note: GSTIN is **optional**, not mandatory, and appears only under GST categories — it is *not* a universal field. There is **no "entity name" or "registration/unique document number" field anywhere in generation** (the client's identity is deliberately anonymised; only PAN is captured, encrypted from verifiers). This corrects two assumptions in the project brief.

### 3.4 Audit & Assurance Functions

`[OFFICIAL]` FAQ Q81–Q93, Q80 + Manual v1.2 §3(iii): Type of Audit + Act/Law/Statute/Regulation dropdowns (fallback "Any other Audit not covered above" / "Other Act…"), date of signing, preceding-year audit details, key fields such as **Financial Year/Period of Audit**, **Shareholders'/Owners' Fund**, **Gross Turnover/Gross Receipts**, **Net Block of PPE & intangibles**, **Cash & Cash Equivalents**, **Major Comment/Observation (adverse/favourable) + financial implication (Nil if none)**, **Type & Units of Fuel Consumed** (energy audit), **Method used for Valuation** (valuation reports), and mandatory Document Description. **Statutory Bank Audit – Branch** additionally requires **Memorandum of Changes (MoC)** values — mandatory, encrypted, never visible to verifiers (Manual v1.2 §3(iii)(b); FAQ Q80). Figures must be the **closing-date or reporting-date** figures (FAQ Q93).

---

## 4. Registration, login and OTP rules

**This changed materially in December 2025 and is the single most important constraint for the app.** `[OFFICIAL]` ([Addendum to FAQs 5th Ed.](https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html); Manual v1.2 §2):

- **"First-Time Registration for Members" has been abolished.** Login uses **SSP credentials only**: username `MRN@icai.org`, **SSP password**, CAPTCHA, then **"Send OTP"** → OTP to the mobile **and** email registered in SSP → dashboard.
- **Forgot/reset password → redirected to ICAI SSP.** Member mobile/email can only be changed at SSP and flow through to UDIN automatically (FAQ Q22).
- **Only full-time CoP holders can log in to generate**; past generators without current full-time CoP may log in **read-only** to List UDIN.
- **No separate UDIN portal account, and no credential delegation to firm staff** exists as a feature. `[INFERENCE]` Any automation that needs to act on behalf of the CA would require possession of the member's SSP password + access to their OTP channel — i.e. credential sharing, which the portal design (personal MRN, CAPTCHA, dual-channel OTP) implicitly forbids.
- OTP at generation: **valid 5 minutes**, must be entered **within 90 seconds** of receipt; **Resend** up to **5 attempts** (Manual v1.2; Addendum Q16). Same 90-second/5-attempt envelope applies to grievance and revocation OTPs.

---

## 5. Bulk generation, apps and APIs

| Capability | Status | Source |
|---|---|---|
| **Bulk UDIN (web)** | Yes — **max 300 at one time**, **min 3**; Excel (.xlsx, Excel 2007+) template downloaded **per certificate sub-category**; portal validates/populates, errors fixable in the UI, rows addable up to the 300 cap; `Save Draft` available for bulk | `[OFFICIAL]` [Manual v1.2 §4](https://blog.saginfotech.com/wp-content/uploads/2025/12/icai-udin-portal-manual-updated.pdf); Addendum Q43–Q44 |
| Bulk scope | **Certificates only** — bulk is not offered for GST/Tax Audit or Audit & Assurance (Manual v1.2 §4 lists only "Certificates") | `[OFFICIAL]` |
| **Saved drafts** | Yes — Save Draft list, edit/delete/retrieve; drafts persist until submitted or deleted | `[OFFICIAL]` Manual v1.2 §6 |
| **UDIN generation API** | **None found.** No API/endpoint, developer portal, client credentials or partner integration is documented in the FAQs, Manual v1.2 or ICAI announcements. Generation is web-UI + OTP only | `[OFFICIAL]` absence in cited docs; **OPEN QUESTION** (§9) |
| Verification (public) | **Single** or **Bulk** verify on the portal, no registration; bulk = **2–10 UDINs** per attempt (manual entry or Excel upload); verifier name + mobile + email + CAPTCHA + **two OTPs**; results printable/PDF | `[OFFICIAL]` Addendum Q26 + new Q1 |
| Mobile app | **Dedicated UDIN Mobile App for iOS and Android announced for launch 30 Dec 2025** | `[OFFICIAL]` [ICAI UDIN Directorate announcement, 10 Dec 2025](https://taxguru.in/chartered-accountant/icai-udin-portal-migrates-digica-platform.html) `[SECONDARY reproduction]` |
| Portal platform migration | **UDIN Portal migrated to ICAI DigiCA Platform on 20 Dec 2025** (~24h downtime from midnight 19 Dec 2025); URL unchanged, `udin.icai.org` | Same announcement |
| Institutional verification | RBI real-time UDIN verification collaboration (per UDIN Annual Report) | `[OFFICIAL]` [UDIN Annual Report PDF](https://udin.icai.org/assets/images/UDIN%20Annual%20Report.pdf) (indexed, not retrievable — 403) |

`[INFERENCE]` Because verification needs a CAPTCHA and two OTPs, there is **no machine-to-machine verification** available to the firm either. The app's own records must therefore be the system of record; the portal is the attestation of record.

---

## 6. Revocation, editing, time limits, fees

| Rule | Detail | Source |
|---|---|---|
| **Revocation window** | **48 hours from generation** only — Council 420th meeting (23–24 Mar 2023) | `[OFFICIAL]` FAQ Q110–Q114; Manual v1.2 §5(iv) |
| Revocation mechanics | List UDIN → Revoke → enter reason → **OTP** → status becomes Revoked, email+SMS confirmation; **cannot be reinstated**; only the generating member can revoke | `[OFFICIAL]` |
| After the window | Generate a **fresh UDIN** instead; a revoked UDIN cannot be re-issued against the old signature date beyond the 60-day rule | `[OFFICIAL]` FAQ Q111, Q114 |
| **Editing** | **UDIN cannot be edited.** Preview-before-submit is the only control; a wrong FRN requires a fresh UDIN | `[OFFICIAL]` FAQ Q115, Q131 |
| **Generation window** | Ideally at signing; permitted **within 60 days** of signing (both dates counted), aligned to SQC-1/SA 230; regs may require immediate | `[OFFICIAL]` FAQ Q17, Q126 |
| Volume limits | **No limit** on number of UDINs per day/month/year | `[OFFICIAL]` FAQ Q116 |
| Validity | **No expiry unless revoked** | `[OFFICIAL]` FAQ Q122 |
| Archiving | UDINs archived after 1 year; search by "Document Generation Year" | `[OFFICIAL]` FAQ Q118–Q119 |
| **Fee** | **No fee for generating, revoking or verifying a UDIN is mentioned anywhere in the FAQs, Manual or announcements** — the portal charges nothing | `[OFFICIAL]` absence + `[INFERENCE]` |
| Non-compliance | Treated as non-adherence to a Council decision; **may attract disciplinary proceedings** under Second Schedule Part II, CA Act 1949 | `[OFFICIAL]` FAQ Q127 |
| e-filing linkage | UDIN mandatory on TRP uploads; can be updated within **60 calendar days** of upload; validation is on **five parameters — MRN, UDIN, AY/FY, Form No., PAN** — any mismatch invalidates; a UDIN generated under "Others" always invalidates against a Form No. | `[OFFICIAL]` FAQ Q54–Q76; Addendum Q76 |

---

## 7. Terms / statements on credential sharing, automation and responsibility

What the official documents *actually say* `[OFFICIAL]`:

1. **Personal, non-transferable identity:** login is the member's own **SSP username/password + MRN**, with CAPTCHA and dual-channel OTP; **no firm account, no sub-users, no delegation** (Addendum Q7/Q10/Q14; Manual v1.2 §2).
2. **Only the signing member may act:** "only signing Partner has to generate UDIN"; a partner cannot revoke another's UDIN; head of firm may only *view* firm UDINs (FAQ Q9, Q133).
3. **Member responsibility:** UDIN is to be generated at signing, communicated to "Management/Those Charged with Governance" when there is no field on a digital filing, and its absence is a **disciplinary matter** (FAQ Q17, Q35, Q127).
4. **Integrity of the record:** UDIN cannot be edited; wrong data must be revoked within 48h and regenerated; e-filing cross-validates five parameters against the portal (FAQ Q115; Addendum Q76).

**OPEN QUESTION (material):** I could **not retrieve a page titled "Terms of Use" / "Terms & Conditions"** for udin.icai.org — the site is a JavaScript app returning an empty body to fetchers, and the PDFs on that host return **HTTP 403** to automated requests. Therefore, an **explicit clause prohibiting automated access, scripting, or credential sharing could not be quoted or ruled out**. This must be verified manually in a browser before any browser-automation design decision is taken. See §9.

`[INFERENCE]` Design implication: any feature where the app holds the member's password or OTP, or replays a generation without the member present, sits outside both the letter of the login design and the professional-responsibility framing. Safer product boundary: **the app prepares and validates; the CA authenticates and submits** (assisted, not autonomous).

---

## 8. Official resources (direct URLs)

| Resource | URL | Notes |
|---|---|---|
| UDIN portal (DigiCA) | https://udin.icai.org | Login, Generate, Bulk, List, Verify, Grievance |
| FAQs on UDIN — 4th Edition (updated 2 Jul 2024), 62 pp | https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf | Most complete public text on fields/rules |
| FAQs on UDIN — 5th Edition (2025) | https://udin.icai.org/assets/images/FAQs%20on%20UDIN.pdf | Linked from portal; **403 to bots** |
| **Addendum to FAQs 5th Ed. (DigiCA)** | https://udin.icai.org/assets/images/Addendum%20to%20FAQs%20on%20Unique%20Document%20Identification%20Number%20(UDIN)%2C%205th%20Edition%20-%20ICAI%20DigiCA%20Platform.pdf | Post-migration revisions (Q7,8,10,14,16,22,23,26,27,29,32,43,44,46,76) — **403 to bots**, full text republished at the TaxGuru link in §4 |
| **User Manual of UDIN Portal v1.2** (TCS, reviewed by UDIN Secretariat 15 Dec 2025) | https://blog.saginfotech.com/wp-content/uploads/2025/12/icai-udin-portal-manual-updated.pdf (official copy on udin.icai.org 403s) | Authoritative field-by-field walkthrough of the current UI |
| Migration announcement (UDIN Directorate, 10 Dec 2025) | https://taxguru.in/chartered-accountant/icai-udin-portal-migrates-digica-platform.html | DigiCA migration 20 Dec 2025; mobile app 30 Dec 2025 |
| Revocation restricted to 48 hours | https://www.icai.org/post/restricting-revocation-of-the-udins-within-48-hours | ICAI announcement (420th Council) |
| Bulk UDIN for certificates (17 Jun 2020) | https://icai.org/post/generation-of-udin-in-bulk-for-certificates-17-06-2020 | Origin of the bulk Excel facility |
| UDIN Guidelines / Annual Report / CA Journal feature | https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf · https://udin.icai.org/assets/images/UDIN%20Annual%20Report.pdf · https://resource.cdn.icai.org/93013cajournal-july2026-40.pdf | Guidelines & Annual Report **403 to bots**; CA Journal "UDIN@10.77 crore" (Jul 2026) |
| CBDT e-filing UDIN FAQ | https://www.incometax.gov.in/iec/foportal/sites/default/files/2021-05/FAQ_On_UDIN-8-12-20.pdf | Validation at the e-filing portal |

---

## 9. Open questions (unverified — do not build on these)

1. **Terms of Use / automation clause** — not retrievable; whether scripting or browser automation is expressly prohibited is **unknown**. Verify in a browser (logged-out pages only).
2. **A UDIN generation API** — none found; absence in documents is not proof of non-existence. Ask UDIN Directorate (`udin@icai.in`) whether a partner/API channel exists.
3. **The current 40-item certificate dropdown**, and the exact sub-category lists under GST & Tax Audit / Audit & Assurance — only visible **after login**; must be captured manually by a member and treated as gated data.
4. **Whether the DigiCA mobile app supports generation, bulk or only verification** — the app does not appear in the manuals; its feature set is unconfirmed.
5. **Field-level mandatory flags per certificate sub-category** (e.g. which of the 40 ask for turnover vs net worth) — the portal drives these dynamically; the manual only describes the mechanism, not the matrix.
6. **Whether the 5-char minimum document description is enforced everywhere**, given the 15-char minimum still printed in the Addendum Q16 and the pre-2025 FAQ.
7. **ICAI's tax-audit ceiling** (reported as 60 assignments from April 2026) may cap annual UDIN volume and interacts with UDIN issuance — headline only, **not verified**.

---

## 10. Recommendation: field schema for the app

Design the app's schema as **"portal payload + local-only context"**, never inventing portal fields:

**Portal-bound (must be produced/validated by the app):**
`category` (Certificates | GST_TaxAudit | Audit_Assurance) · `sub_category` (config-driven, seeded from §3.2–3.4, refreshable) · `form_or_section` · `act_or_law` (Audit & Assurance) · `frn` (or `INDIVIDUAL`) · `signing_date` · `pan_of_auditee` (GST/Tax + A&A) · `auditor_opinion` {applicable, type ∈ Unmodified/Qualified/Adverse/Disclaimer} · `preceding_audit` {applicable, audited_last_year ∈ Yes/No/FirstYear, prev_year_udin | prev_auditor_mrn, communication_made+date, outstanding_fees ∈ Yes/No/NotKnown} · `key_fields[]` {particulars ≤50 chars, value, type ∈ numeric|alphanumeric, denomination} · `document_description` (**5–250 chars**, charset `A-Za-z0-9 . , _ - –`) · `remarks` (optional, internal) · `moc` {applicable, rows} for bank-branch statutory audits · `document_generation_year` (for List/archive search).

**Local-only enrichment (never sent to the portal, never claimed as a portal field):**
client/entity name, GSTIN (only if you also want to mirror the *optional* GST key field), internal document number/reference, document file hash, aml/engagement ID, preparer, reviewer, 60-day signing-window deadline, 48-hour revocation deadline, e-filing form name for the 5-parameter check, verification events.

**Hard product constraints to encode:** no document upload to the portal (so the "drop a PDF → extract → generate" flow ends at *preparation*); member-only login with SSP credentials + CAPTCHA + dual OTP; one UDIN per assignment/signatory/date; 60-day generation window; 48-hour revoke window; 300-row bulk for certificates only; UDIN value can only be captured *after* submission (no pre-computation).

---

### Sources (all accessed 27 October 2026)

1. ICAI, *FAQs on Unique Document Identification Number (UDIN)*, 4th Ed., updated 2 Jul 2024 — https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf `[OFFICIAL]`
2. ICAI/TCS, *User Manual of UDIN Portal*, Version 1.2, reviewed 15 Dec 2025 — https://blog.saginfotech.com/wp-content/uploads/2025/12/icai-udin-portal-manual-updated.pdf `[OFFICIAL, mirror]`
3. ICAI UDIN Directorate, *Addendum to FAQs on UDIN, 5th Edition (ICAI DigiCA Platform)*, Dec 2025 — official PDF at https://udin.icai.org/assets/images/Addendum%20to%20FAQs%20on%20Unique%20Document%20Identification%20Number%20(UDIN)%2C%205th%20Edition%20-%20ICAI%20DigiCA%20Platform.pdf; full text via https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html `[OFFICIAL text / SECONDARY host]`
4. TaxGuru, *ICAI UDIN Portal Migrates to DigiCA Platform*, 12 Dec 2025 (reproducing ICAI UDIN Directorate announcement, 10 Dec 2025) — https://taxguru.in/chartered-accountant/icai-udin-portal-migrates-digica-platform.html `[SECONDARY]`
5. CA Page, *ICAI Releases Updated UDIN Portal Manual (v1.2)*, 19 Dec 2025 — https://capage.in/icai-releases-updated-udin-portal-manual-new-features-for-gst-tax-audit-certificates/ `[SECONDARY]`
6. ICAI, *Restricting revocation of UDINs within 48 hours* — https://www.icai.org/post/restricting-revocation-of-the-udins-within-48-hours `[OFFICIAL]`
7. ICAI, *Generation of UDIN in bulk for certificates*, 17 Jun 2020 — https://icai.org/post/generation-of-udin-in-bulk-for-certificates-17-06-2020 `[OFFICIAL]`
8. UDIN portal — https://udin.icai.org `[OFFICIAL]`
9. CBDT, *FAQ on UDIN* (e-filing portal) — https://www.incometax.gov.in/iec/foportal/sites/default/files/2021-05/FAQ_On_UDIN-8-12-20.pdf `[OFFICIAL]`
10. ICAI, CA Journal feature "UDIN@10.77 crore" (Jul 2026) — https://resource.cdn.icai.org/93013cajournal-july2026-40.pdf `[OFFICIAL]`
11. ICAI, *UDIN Guidelines* / *UDIN Annual Report* — https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf · https://udin.icai.org/assets/images/UDIN%20Annual%20Report.pdf `[OFFICIAL, 403 to automated fetch]`

*Research conducted read-only on public pages. No login, account, credential, CAPTCHA or UDIN generation was attempted. Content behind the member login (certificate/sub-category dropdowns, field-level mandatory matrix) is flagged as gated in §9.*
