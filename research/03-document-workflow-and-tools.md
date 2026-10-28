# 03 — Document → UDIN → Stamped Document: Workflow, Parsing Stack and Tool Survey

**Author:** udin-docflow (research teammate) · **Date:** 2026-10-27 · **All sources accessed 2026-10-27**
**Scope:** document handling inside an automated UDIN generator for Dhruv Dua & Co (Windows app): how a UDIN is shown on a document, what must be extracted per document type, which libraries to use, how to stamp without breaking digital signatures, what to record, what already exists in the market, and the resulting UX.
**Method:** public, read-only desk research. No logins, no accounts, no real UDIN generated. Tags: `[OFFICIAL]` = ICAI/ICAI-support official; `[SECONDARY]` = press, vendor or practitioner source; `[INFERENCE]` = my reasoned recommendation not stated by a source; `OPEN QUESTION` = unverified.

---

## 0. Bottom line

1. **UDIN is an 18-character alphanumeric string** — `YY` + 6-digit ICAI membership (MRN) + 10 random alphanumerics, e.g. `22314875RKTSAN1639`. The portal also issues a **QR code** alongside the number, and ICAI states the UDIN "can be used for mentioning on the Document" `[OFFICIAL]`.
2. **Extraction is a 6–10 field problem, not a document-understanding problem.** All plausible attestation documents converge on: document category + sub-type, date of signing, client name, PAN, registration/unique document number, FRN, and 2+ numeric "descriptions with values". Everything else (opinion, MoC, prior-year auditor) is portal-version-specific.
3. **The hard constraint is digital signatures, not OCR.** Stamping a UDIN into an already-signed PDF destroys the signature. The only defensible order is *extract → confirm → generate UDIN → stamp → DSC-sign → deliver*.
4. **There is no legitimate public UDIN-generation API.** ICAI explicitly warns members against look-alike interfaces that "provide a replica interface to generate UDIN" `[SECONDARY, quoting ICAI advisory]`. Our product should be an **assistant around the official portal** (prefill, OTP hand-off, capture), never a reimplementation.
5. **No surveyed tool reads the document to prefill portal fields, or manages stamp→sign ordering, or keeps a hash-chained UDIN register.** That is the competitive gap and the product wedge.

---

## 1. How a UDIN is shown on a document (ICAI convention)

### 1.1 Format

| Component | Length | Meaning | Source |
|---|---|---|---|
| `YY` | 2 | Last two digits of year of generation (e.g. `26` for 2026) | `[SECONDARY]` [CCI/UDIN article](https://www.caclubindia.com/articles/all-about-udin--38666.asp); example in [SAG Infotech](https://blog.saginfotech.com/generate-udin-tax-audit-gen-bal-software) |
| MRN | 6 | CA's ICAI membership registration number | same |
| Random | 10 | Portal-generated alphanumeric | same |
| **Total** | **18** | Printed as `UDIN: 26xxxxxxxxxxxxxxxx` | `[INFERENCE]` on the printed label |

Caution: the same CCI article also contains a contradictory "15-digit / MRN+DDMMYY+serial" paragraph. That section is wrong or stale — the 18-character structure is corroborated by two independent sources and by the example `22314875RKTSAN1639`. Treat any 15-digit claim as an error `[SECONDARY, contradictory]`.

### 1.2 What ICAI actually says about printing it

- ICAI's support FAQ states that after generation, "18 Digit UDIN will be generated **having a QR Code**, that UDIN can be used for **mentioning on the Document** for which it [was generated]" `[OFFICIAL]` — [ICAI UDIN FAQ](https://icai-call-sahayata.icai.org/assets/pdf/UDIN%20FAQ.pdf).
- Practitioner guidance describes the UDIN being placed "by mentioning it **using a pen or as a watermark** on the document" `[SECONDARY]` — [CCI](https://www.caclubindia.com/articles/all-about-udin--38666.asp). The pen/watermark phrasing itself is evidence that ICAI prescribes no fixed layout, font or placement.
- Generation for attestation documents is mandatory; the **60-day** generation window from date of signing (reduced from 15 days) was decided by the Council at its 405th meeting on 17 Sep 2021 `[SECONDARY]` — [CCI article, §Introduction](https://www.caclubindia.com/articles/all-about-udin--38666.asp).

**Status of "mandated layout":** ICAI mandates *generation* and expects the number to appear on the document; no official guideline reviewed prescribes a font, size, coordinate or exact string. What follows is therefore convention, not regulation:

**Recommended house format** `[INFERENCE]`:

```
UDIN: 26XXXXXXXXXXXXXXXX            <- 18 chars, monospaced, same size as body text
[ QR code, 18–22 mm ]               <- optional, placed in the margin beside the block
```

Placement rules recommended for the app:

| Rule | Rationale | Tag |
|---|---|---|
| Bottom of the **signature page**, immediately below the CA's name / MRN / FRN / place / date block | This is where a verifier looks; matches how ICAI's own portal print-outs lay out UDIN | `[INFERENCE]` |
| Repeat in the **footer of every page** of multi-page reports as `UDIN: …` at 7–8 pt grey | Page-level proof when pages are extracted and emailed separately (very common with 3CD annexures) | `[INFERENCE]` |
| Never place it over the signature, seal, or DSC appearance block | Overlap makes verification/reproduction look tampered; also collides with e-sign visual marks | `[INFERENCE]` |
| Only add after the UDIN exists — never pre-print a placeholder | A placeholder leaks the expectation of a UDIN and invites editing | `[INFERENCE]` |

`OPEN QUESTION`: whether ICAI treats *non-mention* on the document (generation done, never printed) as a disciplinary defect. No guideline text found either way in this pass; firm policy should assume it must be printed.

---

## 2. Per-document-type extraction needs

Portal taxonomy per the **UDIN Portal Manual v1.2 (reviewed 15 Dec 2025)**: categories include **Certificates**, **GST & Tax Audit**, **Audit & Assurance Functions**, **Statutory Bank Branch Audit**; certificates now require a mandatory **Document Description (5–250 chars)** with restricted special characters; GST/Tax Audit and Audit & Assurance now **mandate the assessee PAN** (validated against the Income-tax e-filing portal, hidden from verifiers) and a **mandatory Auditor's Opinion** with optional prior-year auditor details; **Statutory Bank Branch Audits** now mandate **Memorandum of Changes (MoC)** values, encrypted and hidden from verifiers. Bulk generation uses category-specific Excel templates, **min 3 / max 300** per upload; revocation only within **48 hours**, OTP-authenticated, irreversible `[SECONDARY]` — [CCI news](https://www.caclubindia.com/news/icai-releases-updated-udin-portal-manual-new-features-for-gst-tax-audit-certificates-25941.asp), corroborated by [CA Page](https://capage.in/icai-releases-updated-udin-portal-manual-new-features-for-gst-tax-audit-certificates/).

| Document type | Portal category / sub-type | Portal fields required | Extraction source inside the document | Auto-infer confidence | Validation rules |
|---|---|---|---|---|---|
| **Tax audit — Form 3CA + 3CD** (books audited under other law) | GST & Tax Audit → Tax Audit | Date of signing; PAN; assessee name; auditor's opinion; FY/AY; 2+ description+value pairs (turnover, total tax, depreciation, etc.) | Cover page of 3CA ("Report of even date"), the "Date"/"Place" block above signature, PAN + name in the 3CA header, "Annexure" 3CD clause 1/11/44 figures | **High** — signed-form templates are stable | Form chosen must be 3CA (not 3CB) because the "audited under any other law" clause is present; PAN regex; AY = FY+1; signing date within 60 days of generation |
| **Tax audit — Form 3CB + 3CD** (no other-law audit) | GST & Tax Audit → Tax Audit | as above | 3CB header + signature block | **High** | Mutually exclusive with 3CA — reject if both markers found |
| **Tax audit — Form 3CEB** (transfer pricing) | GST & Tax Audit → other report | Date of signing; PAN; international/specified-domestic transaction total | Form header, "Total of transactions" table | Medium | Amount must equal sum of Table rows (recompute) |
| **Company statutory audit report** (+ CARO annexure) | Audit & Assurance Functions → Company Audit | Date of report; CIN/PAN; company name; FY; opinion type (unmodified/qualified/adverse/disclaimer); signing partner MRN/FRN | "Independent Auditor's Report" title, "For <Firm>", "Firm Registration No.", "Membership No.", "Place/Date" | **High** for identity/date; **Medium** for opinion (phrase-matching per SA 700/705/706 wording) | Opinion must be one of 4 enumerations; if "qualified" the basis-of-qualification paragraph must be located; date ≥ balance-sheet date |
| **GST audit / GSTR-9C** (certification) | GST & Tax Audit → GST | GSTIN; FY; date of certification; turnover/reconciliation figures; auditor's opinion | GSTR-9C cover declaration, Pt. I basics (GSTIN, FY, trade name), Pt. V reconciliation totals | Medium | **GSTIN check-digit (mod-36) is verifiable offline** — strongest single validation available; note GST audit (9C) applicability has been narrowed/omitted in recent years — `OPEN QUESTION` for FY 2025-26 and later, confirm before building the template |
| **Net worth / turnover / turnover-for-tender certificates** | Certificates | Document type; document description (5–250 chars); date; PAN; entity name; **2+ description+value pairs** (e.g. Net Worth ₹X as at 31-03-2026) | Certificate body: "we certify that the Net Worth … is Rs. …", the as-on date, entity name/PAN in the addressee block | **High** for amounts; **Low** for which 2 descriptions to choose | Amounts in words vs figures must match; choose descriptions that also appear in the body text (portal text is evidence-bound); as-on date ≤ today |
| **Bank / branch statutory audit** | Statutory Bank Branch Audit | Branch name + code; bank name; FY; date of signing; **MoC values**; opinion | Audit report cover, "Branch Code", "MoC" annexure | Medium | Branch code numeric; MoC fields encrypted per portal update — do not put MoC values in plain-text logs |
| **Misc. certificates under FEMA/FERA/other laws, funds utilisation** | Certificates → other | Document description; date; PAN; 1–2 values | Certificate body | Low–Medium — free-form prose | Require human confirm of the 2 description/value pairs; conflict if certifying entity PAN ≠ client PAN |
| **Any document already carrying a UDIN** (resubmission) | — | — | `UDIN:` pattern in footer/signature block | High (regex) | If found: treat as *reference/reuse* case, prompt "generate new or link existing?" — two UDINs on one document is a red flag, not an error to auto-fix |

**Cross-document rules worth encoding** `[INFERENCE]`: (a) one signing date per document — if two different dates appear in two signature blocks, this is typically **two UDINs**; (b) FRN + MRN must belong to the firm/member actually signing; (c) AY/FY must be internally consistent across forms in the same bundle; (d) **a single PDF bundle frequently needs 2+ UDINs** (e.g. 3CA/3CD and a separate net-worth certificate stapled into one file) — the data model must be `document bundle → N UDINs`, not `document → 1 UDIN`.

---

## 3. Recommended parsing stack (Windows app)

| Layer | Recommended library | What it gives | Limitations to design around | Tag |
|---|---|---|---|---|
| PDF text + geometry | **PyMuPDF (fitz)** | Fast text with bounding boxes, page render for OCR fallback, incremental-update saves, annotation/overlay drawing | AGPL/commercial licence for closed-source distribution — decide early; licence review required | `[INFERENCE]` |
| PDF tables / word-level layout | **pdfplumber** | Character/rect-level tables — good for 3CD clauses, GSTR-9C Pt. V tables | Slower; layout heuristics fail on malformed ruled tables | `[INFERENCE]` |
| PDF metadata / security state | **pypdf** (`PdfReader`) | Detects existing signature fields, `/AcroForm`, encryption | Does not validate signatures cryptographically (use `pyhanko` if validation is needed) | `[INFERENCE]` |
| Word | **python-docx** | Paragraphs, tables, headers/footers, core properties; footer is where a UDIN line belongs | No rendering engine — pagination and "last page" are unknown; `.doc` must be converted first (Word COM automation or LibreOffice `--convert-to docx`) | `[INFERENCE]` |
| OCR — general | **Tesseract** via pytesseract, `--psm 6`, 300 dpi render | Cheap, offline, no model download, adequate for typed tax-audit reports | Poor on skew, stamps, Devanagari, faint carbon-copy bank reports | `[INFERENCE]` |
| OCR — tables/handwriting-ish | **PaddleOCR** | Noticeably better on dense tables and Indian document layouts | Heavier install (Paddle runtime), slower cold start, packaging friction in a Windows installer | `[INFERENCE]` |
| Classification | Rules + filename + first-page text signatures (e.g. presence of "Form 3CA", "Independent Auditor's Report", "GSTR-9C") before any model | Deterministic, explainable, cheap | Breaks on scanned bundles — fall back to OCR then user selection | `[INFERENCE]` |
| Optional LLM extraction | Local or API LLM with a strict JSON schema over *first 2 + last 2 pages* text only | Handles free-form certificates and opinion wording | Hallucination, cost, client-confidentiality/DPDP concerns, non-determinism | `[INFERENCE]` |
| Stamping/signing | **PyMuPDF** overlay + **qrcode** + **pyhanko** (DSC signing / timestamping) | One Python stack for both stamp and sign | DSC token/PFX handling, driver dependencies | `[INFERENCE]` |

**Anti-hallucination rule if an LLM is used** `[INFERENCE]`: every extracted string must be verifiable as a normalised substring of the source text (or a regex-normalised date/amount); anything failing the check is downgraded to "needs confirmation". Never let the model produce a *value* that isn't in the document — only choose among candidates.

**Confidence model** `[INFERENCE]` (three states, shown as chips in the UI):

| State | Trigger | UX |
|---|---|---|
| Verified | Regex/structure check passed **and** value found in an expected region (signature block, header, totals row) | pre-filled, green, still editable |
| Inferred | Found once, no corroboration | pre-filled, amber, must be acknowledged before OTP step |
| Unknown | not found / OCR confidence < threshold / two conflicting candidates | blank, red, blocks submit until filled |

**Why this matters commercially:** the portal is unforgiving — once submitted, "the data cannot be deleted or modified" and the only correction path is revocation within 48 hours `[SECONDARY]` — [CCI](https://www.caclubindia.com/articles/all-about-udin--38666.asp). A wrong auto-fill therefore costs a revocation, not an edit.

---

## 4. Stamping: options, and the digital-signature trap

### 4.1 The constraint

A PDF digital signature is a cryptographic digest over a declared byte range. Any subsequent save that alters the file outside the permitted incremental-update region **invalidates the signature**; Adobe's documentation frames the operational rule as making final changes before certifying/signing `[SECONDARY]` — [Adobe digital-signature overview](https://helpx.adobe.com/acrobat/desktop/e-sign-documents/learn-about-signatures/digital-sign-overview.html) (note: this pass captured the help navigation only; the "sign last" principle is standard PDF/ISO 32000 signed-byte-range behaviour, so treat the exact wording as unquoted here).

Consequences for our app:

- **Stamping after the CA's DSC is applied = broken signature.** Banks and portals that verify the signature will reject the document, and the UDIN itself becomes evidence of a tampered file. This is the single biggest footgun in the whole product.
- If the incoming document is **already signed** by the client or another CA (common: client-signed 3CD, or a report signed by a partner before the UDIN was generated), we must **not** silently stamp it. Options: (i) request an unsigned copy; (ii) stamp and have the signing CA re-sign (their own DSC, own key — acceptable, but the *previous* signature is gone); (iii) issue the UDIN on a separate signed **covering letter/annexure** that references the document. Option (iii) is the safest default `[INFERENCE]`.
- Never flatten/rasterise a text PDF to "make stamping easy" — it destroys the text layer that makes the document searchable/verifiable and bloats size.

### 4.2 Stamping options

| Option | How | Pros | Cons | Tag |
|---|---|---|---|---|
| **Signature-block line (default)** | `insert_textbox` below the CA name/MRN/FRN/date block on the signature page | Conventional, unobtrusive, high trust | Verifier must open the right page | `[INFERENCE]` |
| **Footer on every page** | 7–8 pt grey `UDIN: …` in a fixed footer band, applied to all pages | Survives page extraction/forwarding | Slight visual noise on annexures | `[INFERENCE]` |
| **Watermark** | Diagonal/light-grey text or a semi-transparent UDIN in the margin | Explicitly contemplated ("as a watermark") `[SECONDARY]` | Can clash with stamps/seals; ugly on dense 3CD tables | `[SECONDARY]` CCI |
| **QR code** | QR beside the UDIN block; encode at minimum the 18-char UDIN (and ideally the official verification URL) | Portal itself issues a QR with the UDIN `[OFFICIAL]`; fastest verification by a bank clerk | Exact official verify-URL query format **not confirmed** — `OPEN QUESTION`; encode only the UDIN until confirmed | `[OFFICIAL]` for QR existence |
| **Annexure page** | Append a one-page "UDIN Memorandum" (doc identity, UDIN, QR, signing date) | Works when the body must stay byte-identical to something already signed elsewhere | Still changes the file if appended to the signed PDF — must be a *separate* file | `[INFERENCE]` |
| **DOCX insertion** | Insert a paragraph at the end of the body and a field in the footer via python-docx, then export to PDF and sign the PDF | Native, editable, easy review | "Last page" is unknowable without a renderer; a Word digital signature has the same invalidation rule; DOCX→PDF conversion must happen **before** signing | `[INFERENCE]` |

### 4.3 Recommended order of operations

| # | Step | Why this order | Tag |
|---|---|---|---|
| 1 | Extract + classify | read-only; no bytes changed | `[INFERENCE]` |
| 2 | Human confirms/edits fields | portal data is immutable once submitted | `[SECONDARY]` |
| 3 | Pre-flight validation (PAN, GSTIN checksum, dates, duplicates) | cheapest place to catch a 48-hour revocation | `[INFERENCE]` |
| 4 | Generate UDIN on **udin.icai.org** (OTP) | must exist before it can be printed | `[SECONDARY]` |
| 5 | **Stamp** the UDIN into the still-unsigned PDF/DOCX→PDF | stamping must precede signing | `[INFERENCE]` |
| 6 | CA applies **DSC** (pyhanko / Acrobat / eSign) and timestamps | signature covers the stamped bytes | `[INFERENCE]` |
| 7 | Store stamped+signed file, SHA-256, register row; deliver | tamper-evident record | `[INFERENCE]` |

Second-order caveat `[INFERENCE]`: for **income-tax e-filing**, the audit report is uploaded through the e-filing utility and the UDIN is *also* entered into the form/JSON field — so the app's output must be usable twice: (a) a stamped PDF for the client/records, and (b) a copy-paste/exports-ready field for the e-filing utility. `OPEN QUESTION` whether the department cross-validates the PDF's printed UDIN against the JSON field (likely yes for audit reports) — worth confirming with one real filing.

---

## 5. Record-keeping

**UDIN register (one row per UDIN, never one row per document):**

| Field group | Fields | Purpose |
|---|---|---|
| Identity | UDIN, category, sub-type/document type, document description | reproduce & match portal |
| People | signing member name + MRN, firm name + FRN, client name, client PAN, GSTIN (if any) | attribution; multi-partner firms |
| Dates | date of signing, UDIN generated at (timestamp), 60-day deadline flag | compliance window |
| Content | the 2+ description/value pairs exactly as submitted; auditor's opinion; prior-year auditor; MoC (encrypted) | portal parity, dispute defence |
| Document | source file path + SHA-256 of **unsigned** source, stamped+signed file path + SHA-256, page count, manifest of which pages carry the stamp | tamper evidence |
| Lifecycle | status (generated / stamped / delivered / revoked), revocation reason & timestamp, regenerated-from UDIN | 48-hour revoke workflow `[SECONDARY]` |
| Audit | user, workstation, action, timestamp, before/after values; append-only | audit trail |

**Retention:** ICAI's own 60-day generation window and the immutability of submitted data mean the register must outlive any single engagement file. No specific UDIN-retention period was found in the guidance reviewed — `OPEN QUESTION`. Recommended posture `[INFERENCE]`: retain **≥8 years** (matching the long tail of audit-file expectations and assessment/reassessment horizons), store the *stamped+signed* PDF and its hash, and keep the register exportable and immutable (append-only log or hash-chained table) so a partner can demonstrate what was certified on what date.

**Multi-firm / multi-client:** a single CA can sign under a firm FRN; partners in the same firm sign under their own MRN — and the UDIN must be generated from the **signing member's own login** `[INFERENCE]` from the portal architecture (login is per-member MRN; "SSP credentials are the sole login method" `[SECONDARY]` CCI). Design implication: **one portal identity per signing partner**, with the app holding many identities and attributing each UDIN to the right person; never batch-generate another partner's UDIN under one login.

---

## 6. Existing tools and services

| Offering | Claim | Public pricing | Strengths | Gaps / risks | Tag |
|---|---|---|---|---|---|
| **ICAI UDIN portal** (udin.icai.org) | Generation, verification, bulk Excel (min 3 / max 300), CSV/PDF download, 48-h revocation | Free to members | Authoritative; QR issued with UDIN; verification used by banks/regulators | Manual re-keying of every document field; no document awareness; no register/stamping | `[SECONDARY]` [CCI](https://www.caclubindia.com/news/icai-releases-updated-udin-portal-manual-new-features-for-gst-tax-audit-certificates-25941.asp) |
| **SAG Infotech Genius / Gen Bal** | Launch UDIN generation from inside the Form 3CA/3CD, 3CB/3CD workflow; redirects to the portal screen, user solves captcha | Not published for the UDIN module — `OPEN QUESTION` | Shows the winning pattern: generate *from the document context*, don't re-key | Still portal-bound (captcha + OTP); no stamping; no cross-document register | `[SECONDARY]` [SAG blog](https://blog.saginfotech.com/generate-udin-tax-audit-gen-bal-software) |
| **QwikCA** (CA practice suite) | "UDIN generation & tracking" alongside tasks, DSC register, GST fetch, client portal, mobile apps | ₹1,000/yr solo; ₹7,500/yr 10 users; ₹12,500/20; ₹17,000/40; ₹27,000/60 (vendor page) | Cheap, cloud, multi-feature, UDIN register concept exists | No document→field extraction found; vendor comparison page is self-interested — verify | `[SECONDARY]` [QwikCA](https://www.qwikca.in/compare/qwikca-vs-turia/) |
| **Turia** | DSC register + expiry alerts, WhatsApp automation, practice management | ₹100/user/month (as stated by a competitor) | Strong DSC custody/expiry angle | UDIN generation not documented on its site (per competitor) — `OPEN QUESTION` | `[SECONDARY]` [QwikCA comparison](https://www.qwikca.in/compare/qwikca-vs-turia/) |
| **Finexo PMS** | Practice management, GST/ITR/TDS task generation, credential vault | ₹5,999/yr 10 users → ₹24,999/60 (excl. 18% GST) | Multi-firm dashboards, established base | "UDIN generation … Not currently offered" (competitor's page) — verify | `[SECONDARY]` [Finexo comparison](https://finexo.in/compare/finexo-vs-qwikca) |
| **Winman CA-ERP, Computax, Taxmann and similar suites** | Full CA-office suites (accounts, audits, e-filing) | Tiered, not comparable in this pass | Distribution + trust | In-app UDIN generation/stamping **not verified** in this pass — `OPEN QUESTION`; do not assume | `OPEN QUESTION` |
| **Browser extensions / "UDIN API" providers** | Third-party helpers promising automated UDIN generation | — | — | ICAI advisory warns that "certain Online Portals / Software may provide a replica interface to generate UDIN giving a false presentation… members [are advised] to generate through the official site… only and stay away from UDIN look alike interface(s)" `[SECONDARY, quoting ICAI]` [CCI](https://www.caclubindia.com/articles/all-about-udin--38666.asp). No legitimate public generation API found → any such service is a compliance and credential risk | `[SECONDARY]` / `OPEN QUESTION` |
| **Verification-side integration** | ICAI–RBI MoU for real-time UDIN verification by banks | n/a | Third parties increasingly verify UDINs automatically → wrong/inconsistent UDINs will surface faster | Not a generation channel | `[OFFICIAL]` [ICAI](https://cms.icai.org/post/prc-rbi-mou-udin), [coverage](https://indiatechnologynews.in/icai-rbi-mou-ushers-in-real-time-udin-verification-boosting-transparency-and-regulatory-confidence/) |

Scale signal: ICAI's Journal (July 2026) headlines UDIN volumes at ~10.77 crore `[OFFICIAL-ish, from title only]` — [ICAI Journal](https://resource.cdn.icai.org/93013cajournal-july2026-40.pdf). Not load-bearing for our design; indicates the ecosystem is large and verification-normalised.

**Where the market is thin (our wedge):** nobody found in this pass (a) reads the PDF/DOCX to prefill the portal, (b) manages stamp-then-sign ordering or signature-preservation, (c) keeps a firm-grade UDIN register keyed to document hashes with revocation history, or (d) handles one-bundle-many-UDINs. Suites compete on task/billing breadth, not on the document.

---

## 7. Proposed UX

### 7.1 Happy path

1. **Drop** — drag-and-drop + picker (later: watched folder / email-in). PDF, DOCX, converted DOC, scanned PDF; batch with per-file cards. Encrypted/unsupported → clear message, no retry loop.
2. **Classify + extract** — "We think this is **Form 3CA + 3CD**, AY 2026-27" plus per-field confidence chips; one click shows the page region each value came from. Low confidence → user picks the type from the portal's own enumerations.
3. **Confirm** — a form that **mirrors the portal exactly** (same categories/sub-types, order, labels), with the 2 description/value pairs defaulted from document totals. A missing mandatory field blocks "Generate".
4. **Pre-flight** — PAN format + entity-type character; GSTIN mod-36 checksum; signing date not in the future and within the 60-day window; duplicate detection by SHA-256 or same client+type+date. Duplicate → "link existing / revoke and regenerate / continue".
5. **OTP + portal** — open a controlled window on **udin.icai.org** with fields pre-copied; the user completes login, CAPTCHA and OTP; the app captures the 18-char UDIN back into the form. The app never impersonates the portal. OTP timeout resumes without losing the draft.
6. **Stamp** — preview of the stamped signature page and footer (QR toggle), saved as `client_doc_UDIN_<udin>.pdf`. Detected pre-existing signature → block, offer annexure/quarantine options.
7. **Sign + deliver** — hand-off to DSC/Acrobat/pyhanko *after* stamping; verify the signature post-sign; on failure keep the unsigned stamped copy and flag it.
8. **Register** — row appended with PDF + hash archived; searchable by client/PAN/date/status; exportable; 48-hour revoke countdown always visible.

### 7.2 Edge cases the design must own

| Edge case | Behaviour |
|---|---|
| **Scanned document / no text layer** | Detect per-page text length; OCR at 300 dpi; if OCR confidence low on *any* mandatory field, never auto-submit — force manual entry with the page image side-by-side |
| **Multi-page report, multiple signatures** | Identify every signature block; if >1 signing date or >1 signer, propose N UDINs and let the user confirm the split |
| **One PDF, multiple documents** | Bundle-splitting UI: assign each UDIN to specific page ranges; stamp each range separately |
| **Already contains a UDIN** | Regex-detect `UDIN:\s*[0-9A-Z]{18}`; never silently overwrite — offer link/regenerate |
| **Revoke & regenerate (48 h)** | One-click revoke with mandatory reason; issue replacement UDIN, keep both rows linked (`regenerated_from`), stamp the new one, archive the old stamped file (never delete) |
| **Revised document after stamping** | New UDIN; old one revoked; version chain retained |
| **Wrong PAN / wrong FY discovered late** | >48 h means revocation is impossible → escalate to a firm-level exception workflow with documented reason (this is why pre-flight validation matters) |
| **Partner signs, junior operates the app** | Role split: preparer drafts + prefills, signing partner authenticates the portal session; log both identities |
| **Client confidentiality** | Local-first processing by default; if an LLM is used, explicit per-client opt-in and no retention; MoC/PAN values excluded from logs |

### 7.3 The five UX requirements that decide adoption

1. **Nothing is generated without an explicit human confirmation** of every portal field — the submitted record cannot be edited.
2. **Show provenance**: for each extracted field, one click reveals the page region it came from.
3. **Never break a digital signature** — block, warn and offer alternatives rather than silently modifying a signed file.
4. **Assist, don't imitate**: the OTP/CAPTCHA step happens on the official ICAI portal; the app pre-fills and captures the result. (ICAI's own advisory against look-alike interfaces makes this non-negotiable.)
5. **The register is the product**: one searchable, exportable, tamper-evident UDIN register per firm with stamped copies attached — that is what a CA firm will pay for after the first bank query.

---

## 8. Open questions (to resolve with one real engagement or a colleague)

1. Exact official **verification URL/QR payload** for a UDIN (safe to encode only the UDIN until confirmed).
2. Whether the portal/income-tax e-filing cross-validates **printed UDIN vs JSON field**.
3. Whether ICAI treats **not printing** the UDIN on the document as a defect (vs only generation being mandatory).
4. Whether GSTR-9C **certification (and hence UDIN)** still applies for FY 2025-26 onwards.
5. Current **pricing/module availability** of UDIN features in Winman / Computax / Taxmann (not verified here).
6. **Retention period** expected by ICAI for UDIN records (no explicit figure found).
7. Whether any **legitimate** automation-friendly interface exists (portal API/partner programme) — assume none and design the assisted flow.

---

## Sources (all accessed 2026-10-27)

**Official / ICAI**
- ICAI UDIN FAQ (QR + "mentioning on the Document") — https://icai-call-sahayata.icai.org/assets/pdf/UDIN%20FAQ.pdf
- ICAI Comprehensive Guidelines on UDIN — https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf
- ICAI FAQs on UDIN, 4th edition (Feb 2024) — https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf
- ICAI–RBI MoU on real-time UDIN verification — https://cms.icai.org/post/prc-rbi-mou-udin
- ICAI Journal, July 2026 (UDIN volume headline) — https://resource.cdn.icai.org/93013cajournal-july2026-40.pdf

**Secondary (press / practitioner / vendor)**
- UDIN Portal Manual v1.2 summary — https://www.caclubindia.com/news/icai-releases-updated-udin-portal-manual-new-features-for-gst-tax-audit-certificates-25941.asp ; mirror https://capage.in/icai-releases-updated-udin-portal-manual-new-features-for-gst-tax-audit-certificates/
- "All about UDIN" (format, 60-day window, pen/watermark, ICAI anti-lookalike advisory, revocation) — https://www.caclubindia.com/articles/all-about-udin--38666.asp
- SAG Infotech — generating UDIN from Gen Bal / Genius — https://blog.saginfotech.com/generate-udin-tax-audit-gen-bal-software
- QwikCA vs Turia (UDIN feature + pricing) — https://www.qwikca.in/compare/qwikca-vs-turia/
- Finexo vs QwikCA (pricing; "UDIN not currently offered") — https://finexo.in/compare/finexo-vs-qwikca
- ICAI–RBI MoU coverage — https://indiatechnologynews.in/icai-rbi-mou-ushers-in-real-time-udin-verification-boosting-transparency-and-regulatory-confidence/

**Technical**
- Adobe Acrobat Help — digital signatures overview — https://helpx.adobe.com/acrobat/desktop/e-sign-documents/learn-about-signatures/digital-sign-overview.html (standard signed-byte-range semantics; library docs for PyMuPDF / pdfplumber / python-docx / pyhanko / qrcode to be pinned at build time).
