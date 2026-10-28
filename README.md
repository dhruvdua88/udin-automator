# ICAI UDIN Automation — Research & Build Roadmap

> Verified research on generating a **UDIN (Unique Document Identification Number)** on the ICAI portal
> (`udin.icai.org`, migrated to the **ICAI DigiCA** platform in December 2025), plus a phased plan for a
> document-aware, **assisted** UDIN generator app for Chartered Accountant firms.

**Status:** research + build phase — research is current as of **27 October 2026**; a working desktop
login slice now lives in [`app/`](app/) (real Chrome over CDP, in-app CAPTCHA panel, OTP panel, DPAPI vault,
HAR-style logging). Nothing is automated beyond those two human gates.

---

## Why this repository exists

The original brief: *"An app where the CA drops a PDF or Word document and a UDIN is generated, asking the
user for OTP, working for all types of documents."*

The research found that the ICAI portal **cannot be fully automated** — and that this is by design:

- login requires the member's **SSP credentials + a text CAPTCHA + an OTP** to the registered mobile **and** email;
- **another OTP is mandatory at generation time**, typed within a **90-second** window (5 resends max);
- payloads are encrypted client-side and there is **no member-facing API**;
- the portal **never receives the document** — it takes structured fields only.

So the honest, buildable product is an **assisted UDIN workbench**:
drop PDF/Word → extract and validate the exact portal particulars → the CA confirms → a visible browser
pre-fills the official portal and pauses for the CA's CAPTCHA/OTP → capture the 18-digit UDIN + QR → stamp
the document **before** DSC signing → keep a firm-grade UDIN register.

**Feasibility:** human-in-the-loop automation **7/10**, native bulk path **6/10**, fully unattended without ICAI sanction **1/10**. The autonomy roadmap targets **L4** (lights-out operations, one OTP gesture per batch) and pursues **L5** (literal zero-human) only through an ICAI-sanctioned API/delegation.

---

## Read in this order

1. **[Executive summary](research/00-executive-summary.md)** — bottom line, corrections to the brief, evidence.
2. **[ROADMAP.md](ROADMAP.md)** — architecture, 6 phases with exit criteria, workflows, risks, decisions.
3. **[Autonomy roadmap (L0→L5)](ROADMAP-AUTONOMY.md)** — batch autopilot, lights-out operations, and the ICAI-sanctioned zero-human path.
4. **[Pipeline spec](docs/PIPELINE.md)** — DeepSeek extraction (native text + OCR + vision), strict UDIN JSON, per-document and per-batch confirmation, portal fill, OTP, capture, stamp, register.
5. **[Official requirements](research/01-udin-official-requirements.md)** — mandate, document types, fields, rules.
6. **[Portal technical recon](research/02-udin-portal-technical-recon.md)** — SPA architecture, auth, endpoints, feasibility.
7. **[Document workflow & tools](research/03-document-workflow-and-tools.md)** — extraction, stamping, signature order, market.
8. **[Precedents, OTP UX, security](research/04-automation-precedents-security.md)** — risk register, credentials, DPDP.
9. **[Guidelines 2026 digest](research/05-udin-guidelines-2026-digest.md)** — statutory Guidelines, s.44AB validation, 60-audit ceiling.
10. **[Desktop app architecture](docs/APP-ARCHITECTURE.md)** — real Chrome over CDP, JS/DOM fills, HAR as observability (never replay), DPAPI vault, state machine, build slices.

---

## Key findings at a glance

- **UDIN** = 18 characters: `YY` + 6-digit ICAI membership number (MRN) + 10 random alphanumerics, issued with a QR code.
- **Mandatory** since 2019 for certificates (1 Feb), GST/tax audit reports (1 Apr), all other audit/assurance (1 Jul); only full-time practising CAs, only the signing partner.
- **One UDIN per assignment × signatory × signing date**; generated at signing or within **60 days**; revoked only within **48 hours** (OTP, irreversible).
- **Three portal categories:** Certificates (**40** sub-categories), GST & Tax Audit, Audit & Assurance Functions — not "any document".
- **No document upload and no client-name field** in the portal form (Manual v1.2), although the **Guidelines 2026 §8(b)** require the client name at generation — an implementation gap flagged for Phase 0.
- **Native bulk already exists:** up to **300** certificates via Excel; **3–10** tax-audit/assurance UDINs via UI (Aug 2026). The app's value is document awareness, pre-submit validation, signature-safe stamping and the register — not "faster generation".
- **Field-level validation under s.44AB is live** (Feb 2026) and a **60-tax-audit ceiling** is enforced at the portal from **1 Apr 2026** — the app must validate these *before* the OTP window.
- **Guidelines on UDIN, 2026** (issued under s.15 of the CA Act) make the **register** and **client communication** obligations, require **verifier notification on revocation**, and allow **public disclosure** of violations.
- **Autonomy path:** batch autopilot can remove the human from all the work (~1 OTP per 300 certificates, or per 10 tax-audit UDINs) in ~20 weeks; literal zero-human (L5) requires an ICAI-sanctioned API/delegation — see [ROADMAP-AUTONOMY.md](ROADMAP-AUTONOMY.md).
- **Pipeline:** DeepSeek API extraction over **native text + OCR + page vision**, strict UDIN JSON with verbatim/enum guards, then **per-document or per-batch confirmation**, portal fill, CAPTCHA/OTP by the member, UDIN capture, stamp, register — see [docs/PIPELINE.md](docs/PIPELINE.md).
- **Desktop slice (working):** `python app/udin_app.py --ui` launches real Chrome, fills credentials, extracts the live CAPTCHA image for the member to read, and pauses for OTP. Engine self-test verified 28 Oct 2026; HAR is recorded for observability, never replayed.

---

## Repository layout

| Path | What it is |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | Architecture, phased plan, best workflows, risks, decision gates, definition of done |
| [`ROADMAP-AUTONOMY.md`](ROADMAP-AUTONOMY.md) | Ambition roadmap L0→L5: batch autopilot, lights-out ops, metrics, ICAI-sanctioned zero-human track |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | End-to-end pipeline: DeepSeek extraction (text + OCR + vision), confirmation modes, portal fill, OTP, capture, stamp, register |
| [`docs/APP-ARCHITECTURE.md`](docs/APP-ARCHITECTURE.md) | Desktop app design: Chrome/CDP engine, state machine, DPAPI vault, build slices |
| [`app/`](app/) | Working proof-of-slice: `udin_app.py` (engine + Tkinter UI), requirements, run notes |
| [`research/00-executive-summary.md`](research/00-executive-summary.md) | Synthesis with corrections and open questions |
| [`research/01-…`](research/01-udin-official-requirements.md) | Official ICAI requirements and field schema |
| [`research/02-…`](research/02-udin-portal-technical-recon.md) | Portal recon (SPA, auth, endpoints, feasibility) |
| [`research/03-…`](research/03-document-workflow-and-tools.md) | Document → UDIN → stamped-document workflow and tool survey |
| [`research/04-…`](research/04-automation-precedents-security.md) | OTP UX, credential security, DPDP/IT Act, risk register |
| [`research/05-…`](research/05-udin-guidelines-2026-digest.md) | Digest of the 2026 Guidelines + s.44AB validation/ceiling |

---

## Scope, caveats and disclaimers

- **Unofficial.** This is independent research; it is not affiliated with, endorsed by, or approved by ICAI.
- **Not legal or professional advice.** Verify every requirement against the current portal and ICAI publications before relying on it.
- **No client data, credentials or OTPs** are stored in this repository. No login, OTP, CAPTCHA or UDIN generation was performed while producing this research.
- **ICAI documents are not redistributed here** — the official PDFs are linked at their source. Quotations are short extracts used for analysis.
- **The portal changes.** The Dec-2025 DigiCA migration and the Feb/Aug-2026 validations show the design must fail closed and be re-verified at build time.
- **Deliberate non-goals:** unattended generation without the member's personal OTP (L5 requires ICAI sanction — see the autonomy roadmap), OTP interception, CAPTCHA solving, credential sharing, look-alike interfaces, cloud storage of client documents by default.

---

## Primary sources

- ICAI, *FAQs on UDIN* (4th ed., updated 2 Jul 2024) — https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf
- ICAI/TCS, *User Manual of UDIN Portal*, v1.2 (Dec 2025)
- ICAI, *Guidelines on UDIN, 2026* (Comprehensive Guidelines on UDIN), July 2026 — https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf
- ICAI UDIN Directorate, *Field-level validation under s.44AB and 60-audit ceiling* (11 Feb 2026)
- ICAI UDIN Directorate, *Migration to ICAI DigiCA Platform* (Dec 2025) and *bulk UDIN expansion* (Aug 2026)

Full source lists with access dates are in each research document.

---

## License

Repository text and analysis: **MIT** (see [`LICENSE`](LICENSE)).
ICAI publications and UDIN data remain the property of the Institute of Chartered Accountants of India.
