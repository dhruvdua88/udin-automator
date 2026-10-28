# UDIN Automation — Executive Research Summary

**Prepared:** 27 October 2026 · **For:** Dhruv Dua & Co (CA firm) · **Status:** research complete, decision needed before build
**Method:** four parallel research streams (official rules, portal technical recon, document workflow, automation precedents/security), each with sourced findings, synthesised here with the Lead's own verification of the official PDFs. Evidence tags: `[OFFICIAL]`, `[SECONDARY]`, `[INFERENCE]`, `OPEN QUESTION`.

**Companion documents:**
- [ROADMAP.md](../ROADMAP.md) — phased build plan, architecture, decisions, risks
- [01 — Official requirements](01-udin-official-requirements.md) · [02 — Technical recon](02-udin-portal-technical-recon.md) · [03 — Document workflow & tools](03-document-workflow-and-tools.md) · [04 — Precedents, OTP UX, security](04-automation-precedents-security.md)

---

## 0. Bottom line

1. **The portal cannot be fully automated, and that is by design.** UDIN generation on `udin.icai.org` requires a **member's SSP login + text CAPTCHA + OTP to their registered mobile and email**, and **another OTP at generation time**. No document is uploaded, no member API exists, and the UDIN value is random and only known after submission `[OFFICIAL]` ([FAQ 4th ed.](https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf); [DigiCA addendum](https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html)).
2. **The honest product is an "assisted UDIN workbench":** drop PDF/Word → extract and validate the exact portal particulars → CA confirms → a visible browser pre-fills the official portal and **pauses for the CA's CAPTCHA and OTP** → the app captures the 18-digit UDIN + QR → stamps the document locally → records it in a firm-grade register.
3. **Feasibility:** human-in-the-loop browser automation **7/10**; native bulk path **6/10**; fully unattended **1/10** — do not promise it (portal recon, [02](02-udin-portal-technical-recon.md) §1).
4. **The real value is not "faster generation"** — ICAI already gives members bulk generation (300 certificates via Excel; 3–10 tax-audit/assurance via UI) `[OFFICIAL]` ([bulk certificates 2020](https://icai.org/post/generation-of-udin-in-bulk-for-certificates-17-06-2020); [Aug-2026 expansion](https://taxguru.in/corporate-law/icai-expands-bulk-udin-facility-tax-audit-assurance.html)). The gap is **reading the document, validating before an immutable submission, protecting the digital-signature order, and keeping the register.**
5. **Nothing in the market does document-aware UDIN generation.** The closest are ICAI's free portal and CA suites that merely link to it (e.g. SAG's Genius/Gen Bal launches UDIN from the 3CA/3CD flow; QwikCA sells "UDIN generation & tracking"). None reads the PDF/Word to prefill, manages stamp→sign ordering, or keeps a hash-linked register `[SECONDARY]` ([03](03-document-workflow-and-tools.md) §6).

---

## 1. What UDIN is, and who must generate it

A UDIN is an **18-character system-generated ID** for a document certified/attested by a **full-time practising CA**. Structure: `YY` (year) + `6-digit MRN` + `10 random alphanumerics`, e.g. `19304576AKTSBN1359` `[OFFICIAL]` (FAQ 4th ed., Q4). It is issued with a **QR code**, printed or handwritten **after the signature and membership number** (FAQ Q117).

| Rule | Detail |
|---|---|
| Mandate basis | ICAI Council, **379th meeting (17–18 Dec 2018)**; phased: certificates **1 Feb 2019**, GST & tax audit reports **1 Apr 2019**, all other audit/assurance/attestation **1 Jul 2019** `[OFFICIAL]` |
| Who can generate | Only **full-time practising CAs (CoP)**; only the **signing partner/proprietor**; **firms cannot register**; members without current full-time CoP can log in only to view `[OFFICIAL]` |
| Cardinality | **One UDIN per assignment × signatory × signing date** — separate UDINs for standalone vs consolidated, per bank branch, per quarter; one UDIN covers Form 3CA/3CB + 3CD + annexures `[OFFICIAL]` |
| Generation window | At signing; permitted up to **60 days** after signing `[OFFICIAL]` |
| Revocation | Within **48 hours only**, with reason + OTP; **irreversible**; revoked UDIN cannot be reinstated `[OFFICIAL]` |
| Editability | **None.** Preview-before-submit is the only control. Wrong FRN/period ⇒ revoke + regenerate `[OFFICIAL]` |
| Fee | None mentioned in any ICAI document; the portal is free `[OFFICIAL]`/`[INFERENCE]` |
| Non-compliance | Treated as non-adherence to a Council decision / Guidelines breach; may attract **disciplinary proceedings** (Second Schedule Part II, CA Act 1949), and the 2026 Guidelines Ch. IX allow **publication of the member's name, violation and penalty** in ICAI periodicals `[OFFICIAL]` |

---

## 2. The generation act: three categories, one payload shape

Current portal (DigiCA, migrated **20 Dec 2025**; mobile app announced **30 Dec 2025**) exposes **three categories**:

| Category | Sub-category depth | Key constraints |
|---|---|---|
| **Certificates** | **40** sub-categories (36 named + Others in the 2024 FAQ) | 3 key-field rows, **2 mandatory**; dynamic **Numeric / Alphanumeric / Both** typing with denomination; **Document Description 5–250 chars** (manual v1.2; older FAQ says 15); special chars limited to `. , _ - –` |
| **GST & Tax Audit** | Form/section dropdown (44AB + 3CA/3CB/3CD, 92, 115JB(4)/29B, CGST s.35(5)/9C, s.66(1)/ADT-04, etc.) | **PAN of assessee mandatory** (5th e-filing validation parameter, hidden from verifier); **Auditor's Opinion compulsory** (Yes/No → Unmodified/Qualified/Adverse/Disclaimer, plus KAM/EOM/Other Matter/going-concern flags, listed/non-listed entity); **preceding-year audit details compulsory**; key fields such as turnover, net-profit ratio, WDV, AY |
| **Audit & Assurance Functions** | "Type of Audit" + "Under Act/Law/Statute/Regulation" dropdowns | Same opinion + preceding-year blocks; key fields (shareholders' fund, gross turnover, net block, cash equivalents, major comment, fuel/energy, valuation method, etc.); **MoC mandatory** for statutory bank-branch audits (encrypted, hidden from verifier) |

**What the portal asks for — and does not ask for** `[OFFICIAL]` (FAQ Q15/Q18; Manual v1.2 §3):
- **No document upload**, ever; no registration/unique document number. GSTIN is **optional** and only under GST categories. The portal form (Manual v1.2) also shows **no client-name field** — but the 2026 Guidelines §8(b) expressly list "name of the client" as a generation detail, so treat client name as mandatory app-side data and verify the current DigiCa form in Phase 0 ([05](05-udin-guidelines-2026-digest.md) §2).
- Pre-filled from SSP: member name, MRN, email, **PAN of member**, pincode. FRN is selected from a dropdown (or NA/Individual Capacity).
- The submission is **immutable** — hence the app's pre-flight validator matters more than its OCR accuracy.

**Session/auth mechanics** `[OFFICIAL]` + portal recon:
- Login = `MRN@icai.org` + SSP password + **text CAPTCHA** (server-validated; `captchaType:"text"`, `GET /security/captcha`) + **OTP on registered mobile and email**.
- At generation: **Send OTP → OTP valid 5 minutes but must be entered within 90 seconds → max 5 resends → Verify → Preview → Submit**.
- Third-party verification is separate and public (`/ICAI/verifyUDIN`), also CAPTCHA + **two OTPs** (email + mobile), bulk 2–10.
- Password reset/change happens **only on SSP**; compromising the stored secret compromises the member's **entire ICAI identity**.

**Bulk generation (use it — don't fight it)** `[OFFICIAL]`:
- Certificates: **3–300 UDINs** per Excel template (per-sub-category template), errors fixable in UI, drafts saved.
- Tax Audit / Audit & Assurance: **3–10 UDINs** via UI (no Excel), added **Aug 2026**.
- Bulk verification: 2–10 UDINs.

**UDIN number is random** — no document-type code, cannot be pre-computed; it must be read back from the portal after submission `[OFFICIAL]`.

### 2A. The 2026 Guidelines raise the legal baseline

ICAI has issued the **"Guidelines on UDIN, 2026"** under **s.15(1) r/w s.15(2)(fa) of the Chartered Accountants Act, 1949** (published July 2026; commencement on a notified date) — no longer merely FAQ/Council guidance `[OFFICIAL]` ([Guidelines PDF](https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf); digest in [05](05-udin-guidelines-2026-digest.md)). Consequences for the app:

- **Register is an obligation**, not a nice-to-have: §10(a) requires a record of every UDIN + assignment details for the Institute's prescribed minimum period; §18(vi) lets the Directorate prescribe a **register format**.
- **Client communication duty:** if the UDIN is not written on the document, it must be communicated to the client/appointing authority **within 60 days** (§7(c)).
- **Revocation courtesy duty:** if a UDIN that was already verified is revoked, the member must **inform the verifier** (§11(c)) — the app must track verification events and produce revocation notices.
- **Ceiling enforcement:** §18(iii) empowers the Directorate to restrict generation where the Council caps report numbers — the legal hook for the **60 tax-audit ceiling** enforced at the portal from **1 Apr 2026**.
- **Field-level validation under s.44AB is already live** (Feb 2026): the portal asks preliminary questions (cash-transaction %, turnover/gross-receipt thresholds, s.44AD(4), deemed profits, basic-exemption limit) and refuses generation if the logic fails — so the app must capture and validate these **before** the OTP window, not let the portal reject at the end.
- **Public disclosure:** Chapter IX allows ICAI to publish the member's name, violation and penalty — a wrong pre-filled submission is not just a rework cost.

### 2B. The 60-audit ceiling and s.44AB validation (from Feb 2026)

From **1 April 2026** the UDIN portal enforces a **60 tax-audit ceiling** per member for **Form 3CA (3rd proviso), Form 3CB under 44AB(a), 3CB under 44AB(b) and 3CB (Combined)**; field-level validation applies to **all 44AB clauses (a)–(e)** at generation `[OFFICIAL]` ([UDIN Directorate, 11 Feb 2026](https://taxguru.in/chartered-accountant/icai-introduces-field-level-validation-udin-section-44ab.html)):

| Clause | Validation (portal refuses if not met) |
|---|---|
| 44AB(a) | cash transactions ≤5% → turnover > ₹10 cr; otherwise turnover > ₹1 cr |
| 44AB(b) | gross receipts > ₹50 lakh |
| 44AB(c) | income claimed lower than deemed profits u/s 44AE/44BB/44BBB |
| 44AB(d) | (gross receipts ≤ ₹50 lakh) or (>₹50 lakh ≤₹75 lakh and cash ≤5%), **and** income lower than 44ADA deemed profits, **and** total income > basic exemption limit |
| 44AB(e) | s.44AD(4) applicable **and** total income > basic exemption limit |

The app therefore needs a **tax-audit eligibility module** (derive/confirm those answers from Form 3CD/3CB) and a **ceiling counter** reconciled with the portal quota — both are pre-submission blockers, not reporting extras.

---

## 3. What the technical recon proves about automation

The portal is **not** legacy ASP.NET — it is an **Angular SPA on TCS's DigiGov platform** (`main.*.js` ≈ 9.85 MB, lazy-loaded numeric chunks) `[observed in shipped bundle, 02 §2]`. Consequences:

| Path | Verdict | Why |
|---|---|---|
| Fully unattended / headless | **1/10 — blocked** | CAPTCHA + OTP on every session, OTP again before generation, no member API |
| Human-in-the-loop browser automation | **7/10 — recommended** | Deterministic Angular UI; human does CAPTCHA + OTP; app fills and captures |
| Bulk via native Excel path | **6/10 — good for volume** | Portal feature; same auth friction |
| Raw HTTP replay (`requests`) | **1/10 — do not attempt** | Payloads encrypted client-side (`encryptPassword`, `encryptFileUploadInput`) + 4 proprietary session headers (`ksad/otyb/kbxa/qqmm`) + hash churn |
| Verification lookup | **9/10 — easy** | Public `/ICAI/verifyUDIN` route |

Generation endpoints observed in the bundle include `POST /udin/udinGeneration/save`, `POST /udin/udinGeneration/bulk-save`, `/udin-common/send-otp`, `/udin-common/verify-loggedIn-user-otp`, `/udin/revokeUdin`, `/udin/getQRCodeData`. These are **client-side strings**, not independently exercised; exact DOM field names live in lazy chunks and must be captured with one real session (`02` §11).

**No member API exists.** ICAI's guidelines mention API/MoU arrangements **only with government/regulator agencies** — not with CAs or third-party apps `[OFFICIAL]` (Guidelines; `02` §8).

---

## 4. Your brief vs. the researched reality

| Brief assumption | Reality | Consequence |
|---|---|---|
| "Works on **all types of docs**" | Portal has **3 categories / 40 certificate sub-types** with dynamic mandatory fields | The app maps documents to those enumerations; novel types fall back to "Others" + human choice. Do not invent categories. |
| "User enters **PDF or Word** and UDIN is generated" | Portal **never receives the document**; it takes structured fields | The PDF/Word is input to **our extraction**, not to ICAI. "Generation" = form fill + OTP, not upload. |
| "Asks for **user OTP**" | Correct — but there is also a **login CAPTCHA + login OTP**, and the generation OTP has a **90-second entry window** | UX must be built around two human gates, not one; pre-fill everything before requesting OTP. |
| "**Automation** generates UDIN" | No API; anti-automation design; ICAI warns against **replica interfaces** | Position as **assisted** (official portal stays the authority). A hidden headless bot is both brittle and indefensible. |
| "All docs, any volume" | Native bulk already exists: 300 certs (Excel), 3–10 tax/assurance (UI) | Compete on **document awareness + validation + register**, and use ICAI bulk where it fits. |

---

## 5. Document workflow: where the product actually earns its keep

**Recommended pipeline** (from [03](03-document-workflow-and-tools.md)):
**ingest** (PDF/DOCX/scanned) → **classify** (Form 3CA/3CB/3CD, GSTR-9C, company audit, certificates, bank branch) → **extract** (category, sub-type, signing date, PAN, FRN, opinion, preceding-year details, key-field description/value pairs, document description) → **human confirms every field with page-region provenance** → **pre-flight validation** (PAN format, GSTIN mod-36 checksum, date ≤ today and ≤ 60 days old, duplicate hash, category↔form consistency) → **assisted portal submission** → **capture UDIN + QR** → **stamp** → **CA applies DSC** → **archive hash + register row**.

Stack: **PyMuPDF** (text/geometry/stamping), **pdfplumber** (tables), **python-docx** (Word + footer), **Tesseract** at 300 dpi for scans (PaddleOCR only for table-heavy), optional LLM restricted to **choosing among document-verbatim candidates**, **pyhanko** for signing, **qrcode**.

**The signature trap (single biggest footgun):** stamping a UDIN into an already digitally signed PDF **destroys the signature**. The only defensible order is **extract → confirm → generate → stamp → DSC-sign → deliver**. If the incoming file is already signed, block and offer: unsigned copy, re-sign, or a separate signed UDIN covering letter. Never rasterise a PDF to make stamping easier.

**Record-keeping:** one register row **per UDIN** (not per document): UDIN, category/sub-type, member MRN + firm FRN, client + PAN, signing date, 60-day deadline, submitted description/value pairs, opinion/prior-year/MoC, source-file SHA-256, stamped+signed-file SHA-256, status, revocation reason/timestamp, append-only audit trail. A single PDF bundle can need **N UDINs** — model `bundle → N UDINs`.

---

## 6. Security, legal and ethical constraints (non-negotiable)

- **OTP is typed by the CA, never intercepted.** No SMS reading, no mailbox polling, no OCR of notifications. The OTP is the evidentiary trace that the member personally authorised this attestation; an app that types it manufactures that trace.
- **No CAPTCHA solving.** Show the CAPTCHA to the human; refresh/retry affordance only.
- **No credential sharing.** UDIN is personal to the MRN; firms cannot register. One vault per Windows user/CA, never a shared service account. Stored SSP password = full ICAI identity ⇒ **DPAPI user-scoped or Windows Credential Manager**, per-CA, never in argv/logs/plaintext.
- **Local-first.** Client documents and extracted PAN/financial data stay on the CA's machine; any cloud OCR/LLM must be opt-in, disclosed and contracted (DPDP Act 2023 security/breach obligations; ICAI confidentiality) `[SECONDARY]` ([04](04-automation-precedents-security.md) §4).
- **Be unmistakably third-party** and never imply ICAI affiliation — ICAI has warned members about fake UDIN/ICAI look-alike sites.
- **Never touch `preprodudin.icai.org`** (seen in the bundle) or any internal host.
- **ToS status:** ICAI's general website T&C has **no explicit anti-automation clause**; the UDIN portal's own terms were not retrievable. Absence is not permission — the product should be a **member-operated helper**, and the position should be documented and reviewed before launch `OPEN QUESTION`.

---

## 7. Open questions that must be closed before/at start of build

1. **UDIN/DigiCA terms of use** on automated access — read in a browser and record the exact clause (not yet verified).
2. **One real member session** to capture: DOM field names/IDs, full 40-item certificate dropdown, GST/Tax and Audit dropdowns, exact OTP behaviour (per-session vs per-UDIN), idle timeout, lockout policy, quota semantics.
3. Whether login OTP occurs **every session** or only first/risky sessions; whether "remember device" exists.
4. Exact **bulk Excel column schema** and error format; per-day caps.
5. Whether the income-tax e-filing portal cross-checks the **printed** UDIN vs the JSON field; the 5-parameter rule (MRN, UDIN, AY/FY, Form No., PAN) is already confirmed.
6. Whether GSTR-9C certification (hence UDIN) still applies for FY 2025-26+.
7. Retention period ICAI expects for UDIN records (recommend ≥8 years as firm policy).
8. Legitimate partner/API channel — assume none unless the UDIN Directorate confirms otherwise (`udin@icai.in`).
9. **Guidelines commencement:** published July 2026 but effective on a notified date — confirm whether the 2026 Guidelines are operative.
10. **Prescribed register format** under Guidelines §18(vi) — not yet published.
11. **Client-name field** in the DigiCa generation form (Guidelines §8(b) vs Manual v1.2), and the **60-audit counting rules/exclusions**.

---

## 8. Sources

**Official / primary**
- ICAI, *FAQs on UDIN*, 4th ed., updated 2 Jul 2024 — https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf
- ICAI/TCS, *User Manual of UDIN Portal*, v1.2 (reviewed 15 Dec 2025) — mirror: https://www.caclubindia.com/news/files_download.asp?news_item_id=25941
- ICAI, *Addendum to FAQs 5th ed. (DigiCA)* — official PDF on udin.icai.org; full text reproduced at https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html
- ICAI UDIN Directorate, *Migration to DigiCA* (10 Dec 2025) — https://taxguru.in/chartered-accountant/icai-udin-portal-migrates-digica-platform.html
- ICAI, *Bulk UDIN for Certificates* (17 Jun 2020) — https://icai.org/post/generation-of-udin-in-bulk-for-certificates-17-06-2020
- ICAI, *Bulk UDIN extended to Tax Audit & Assurance* (22 Aug 2026) — https://taxguru.in/corporate-law/icai-expands-bulk-udin-facility-tax-audit-assurance.html
- ICAI, *Revocation restricted to 48 hours* — https://www.icai.org/post/restricting-revocation-of-the-udins-within-48-hours
- ICAI, *Guidelines on UDIN, 2026* (the "Comprehensive Guidelines on UDIN"), July 2026 — https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf · digest: [05](05-udin-guidelines-2026-digest.md)
- ICAI UDIN Directorate, *Field-level validation under s.44AB + 60-audit ceiling* (11 Feb 2026) — https://taxguru.in/chartered-accountant/icai-introduces-field-level-validation-udin-section-44ab.html
- ICAI website Terms & Conditions — https://www.icai.org/post/16566

**Technical / vendor / commentary**
- Portal recon evidence (SPA shell, bundles, endpoints, captcha/OTP strings): [02](02-udin-portal-technical-recon.md) §2–§7
- SAG Infotech — UDIN from 3CA/3CD flow: https://blog.saginfotech.com/generate-udin-tax-audit-gen-bal-software
- QwikCA/Turia and Finexo public comparison pages (pricing/feature claims, self-interested): https://www.qwikca.in/compare/qwikca-vs-turia/ · https://finexo.in/compare/finexo-vs-qwikca
- DPDP phase-compliance commentary: https://www.juriscorp.in/phased-compliance-under-dpdp-act-are-you-ready/
- House precedent: `~/.dsh/skills/gst-login/SKILL.md` (OTP/DSC deliberately not automated) — summarised in [04](04-automation-precedents-security.md) §1

*All URLs accessed 27 October 2026. Content behind login (dropdowns, DOM, OTP timings) is flagged as unverified above.*
