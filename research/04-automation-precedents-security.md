# 04 — Automation Precedents, OTP UX, Security & Compliance for a UDIN Generator

**Researcher:** `udin-precedents` (Team research stream 4)
**Access date for all URLs:** 2026-10-27
**Scope:** documentary, public, read-only. No portal was logged into, no account created, no captcha/OTP system was tested or bypassed.
**Status:** research input for the UDIN app design. Not legal advice; ICAI/legal points need practitioner or ICAI confirmation before build sign-off.

**Tag legend:** `[OFFICIAL]` = ICAI/ICAI-portal/statute text · `[SECONDARY]` = professional press, commentary, aggregator · `[INFERENCE]` = my synthesis, not sourced · **OPEN QUESTION** = could not verify.

---

## 0. The headline finding that reframes the whole project

Two facts, both `[OFFICIAL]`, change the product's centre of gravity:

1. **ICAI already ships bulk UDIN generation natively.** For the *Certificates* category, up to **300 UDINs** can be generated in one go **by uploading an Excel template**. For *Tax Audit* and *Audit & Assurance Functions*, the facility (since Aug 2026) is UI-only, **3–10 UDINs per batch**, with `Save Draft` and OTP-verified submission. `[OFFICIAL]` — [Addendum to UDIN FAQs (5th Ed.), Q43–Q44](https://udin.icai.org/assets/images/Addendum%20to%20FAQs%20on%20Unique%20Document%20Identification%20Number%20(UDIN),%205th%20Edition%20-%20ICAI%20DigiCA%20Platform.pdf), and [ICAI expands bulk UDIN facility](https://taxguru.in/corporate-law/icai-expands-bulk-udin-facility-tax-audit-assurance.html).

2. **The UDIN OTP has a brutal timing window: valid 5 minutes, but must be typed within 90 seconds**, with a maximum of 5 resend attempts. `[OFFICIAL]` — [UDIN Addendum FAQs, Q16](https://udin.icai.org/assets/images/Addendum%20to%20FAQs%20on%20Unique%20Document%20Identification%20Number%20(UDIN),%205th%20Edition%20-%20ICAI%20DigiCA%20Platform.pdf).

**Consequence `[INFERENCE]`:** the value of this app is *not* "generate UDINs faster than the portal can" — the portal already batches. The value is **(a) extraction**: turn PDF/Word documents into correctly-populated UDIN fields with the right category/keys, **(b) reconciliation/tracking**: know which signed documents still lack a UDIN and are approaching the 60-day deadline, and **(c) safe assisted fill + human OTP**. The 90-second OTP window makes genuinely unattended generation *both* fragile and legally exposed; a human-in-the-loop OTP step is not a limitation to engineer around, it is the design.

> **Strategic recommendation:** position the app as a *document-extraction + UDIN ledger + assisted-entry* tool, and prefer driving ICAI's own Excel bulk-upload path (where available) over clicking through individual UDIN forms. Re-validate the bulk limits at build time — they have already changed once (Certificates-only → extended to Tax Audit/Assurance in Aug 2026). `[INFERENCE]`

---

## 1. Precedent summary — the local `gst-login` skill

Source read: `~/.dsh/skills/gst-login\SKILL.md` (readable, 118 lines). Treated as a **design precedent**, not a template to copy wholesale — parts of it are explicitly anti-patterns for this project.

### 1.1 What it does
Logs into `services.gst.gov.in` with a client GSTIN's username/password, auto-solves the login captcha with `ddddocr`, then scrapes the notices/orders register and filed-return ARNs to CSV. Read-only; it never files anything. Orchestrated by a PowerShell driver (`gst.ps1`) over four Node scripts plus a Python captcha solver.

### 1.2 Pattern breakdown

| Dimension | How `gst-login` does it | Verdict for UDIN app |
|---|---|---|
| **Credential storage** | `credentials.json` in the skill root mapping GSTIN → user/pass, **in plaintext**, with an in-file warning to keep it out of synced folders. Alternatively `-User`/`-Pass` per call. | **Anti-pattern.** Unacceptable for a commercial app handling CA SSP credentials. Replace with DPAPI/Credential Manager (§4). Per-call CLI passwords are also bad (shell history / process args). |
| **Captcha** | ddddocr, 4 preprocessing variants × 2 models, strict 6-character vote, ~1–2 attempts per login, retries absorbed by `-MaxAttempts` (default 6). Notes that de-noising *hurts*; raw + autocontrast + unsharp is best. | **Do not port.** Captcha automation is the single clearest terms-of-use conflict and the thing that looks like a bot to the portal. If a UDIN captcha exists on the login path, surface it to the human. |
| **OTP** | **Not handled at all.** The skill explicitly stops at the login boundary: "Filing/amendment needs DSC or EVC (OTP to the authorised signatory) and is deliberately not automated here." | **This is the most valuable precedent in the file.** The house already decided OTP-gated actions are out of scope for automation. Keep that line. |
| **Session / browser reuse** | Uses a persistent, resumable `ego-browser` task space (`gst portal automation`); logs out any existing session first; **never `goto`s an authenticated URL** (portal kills the session / returns Access Denied) — navigates only by clicking real dashboard controls. | **Copy the navigation discipline** (UI-click paths, never deep-link authenticated routes), and the explicit logout-before-login step. For UDIN, **do not** persist a long-lived authenticated session — shorten its life and let it expire. |
| **Failure modes documented** | Failed captcha does *not* rotate the image (needed a refresh+GET to rebind); portal maintenance windows break logins; multi-registration GSTINs may hit a chooser that breaks the assumed flow; portal truncates long text with "…"; `ego-browser` writes JSON to stderr which PowerShell treats as errors. | **Copy the practice**: maintain a living "portal facts learned the hard way" section. Every one of these is a future support ticket otherwise. |
| **Compliance posture** | Self-aware caveat: "Automating a portal captcha very likely conflicts with gst.gov.in's terms of use… get sign-off before using it routinely on client filings." | **Echo this, and go further** — see §6/§7. |

### 1.3 The one-line lesson
> The house precedent is: **automate the reading and the form-filling, stop at the signature/OTP boundary, and keep the human's own credentials on the human's own machine.** That is exactly the shape the UDIN app should take.

### 1.3a Corroboration: this is already the house pattern, twice
A second house skill, **`gst-amendment`** (GST REG-14 / REG-16 applications), is documented as driving the wizard **"to the signing step; a human always completes DS[C/EVC]"** — i.e. it prepares the transaction and hands off exactly at the authentication/signature boundary. `[observed from session skill catalog, 2026-10-27]` Together with `gst-login`'s explicit "OTP is deliberately not automated here", this is a **two-for-two house convention**, not one tool's caution:

| House skill | Automates | Stops at |
|---|---|---|
| `gst-login` | login, captcha, read/scrape notices & ARNs | OTP/DSC-gated *actions* (explicitly out of scope) |
| `gst-amendment` | amendment/cancellation wizard to the signing step | DSC/EVC signing (human always completes) |
| **UDIN app (proposed)** | document extraction, field fill, ledger/reconciliation | **the member's OTP — human always types it** |

`[INFERENCE]` The UDIN app is therefore the *third* instance of an established internal pattern, which is a strong argument for consistency of both design and the customer-facing promise ("we prepare, you authenticate"). It also means the OTP-UX decision in §3 is not a novel judgment call requiring escalation — it is the house default.

### 1.4 `ego-browser` skill — availability note
The skill is **listed in the session catalog** (`ego-browser`: Chromium-based browser for agents, reusable logged-in user context) but the file **`~/.dsh/skills/ego-browser\SKILL.md` is not present on disk** — a `glob` for `**/ego-browser/**/*.md` under `~/.dsh/skills` returned no files. `[observed]` So I could not read its documented pattern; only the catalog summary and the `gst-login` skill's *usage* of it (resumable task space, JSON to stderr) are available. **OPEN QUESTION** for the Lead: is `ego-browser` vendored elsewhere, or installed but with only its runtime (no SKILL.md)? Its relevance here is as a **browser-automation substrate option** for the UDIN app — but note it is an *agent-operated* browser, whereas the shipped product needs an embedded/automated browser the CA's own machine runs (§4.4).

---

## 2. Public evidence of UDIN portal automation by others

**Search queries run:** `"udin icai automation github"`, `"UDIN portal bot"`, `"UDIN bulk generate script"`, `"UDIN automation excel 'UDIN generator' software"`, `"UDIN generation automation tool CA firms"`, `"caclubindia UDIN bulk generation excel template automation"`.

### 2.1 Finding: there is essentially **no public UDIN automation**
- **No GitHub project automating the UDIN portal was found.** Repeated searches returned none. `[observed]` What surfaces instead is (a) ICAI's own bulk facility and (b) *adjacent* Indian-gov-portal RPA, e.g. [GovSight-AI](https://github.com/theashishmavii/GovSight-AI) — a FastAPI+Selenium RPA layer for UIDAI/India Post portals, and academic MCA-portal automation synopses. `[SECONDARY]`
- **No CA-forum thread describing a working UDIN bot** was found; CAs discuss the *official* bulk facility instead (see 2.2). `[observed]`

**How to read that `[INFERENCE]`:** absence of public automation is *weak* evidence that it's hard — but combined with (i) OTP-on-every-submission, (ii) a 90-second OTP window, (iii) captcha on login, and (iv) Dec-2025 migration of the portal to the **ICAI DigiCA platform** (new auth/SSO surface, §2.3), "nobody has published one" is consistent with "the portal is deliberately hostile to unattended scripting." Do **not** treat the absence as an opportunity to be first; treat it as a signal that the realistic product is assisted, not autonomous.

### 2.2 What the public record *does* say works
- **Excel template upload is the sanctioned bulk path** for Certificates (up to 300); UI bulk for Tax Audit / Audit & Assurance (3–10). Drafts can be saved before OTP submission. `[OFFICIAL]` (Addendum FAQs Q43–Q44; TaxGuru expansion note, 2026-08-22)
- **Data must be populated in the portal's own shape**: date formatting quirks (don't copy-paste the date cell), dropdown-driven category/section selection, mandatory key fields. `[OFFICIAL]` (Q44)
- **New mandatory validations** for tax audits: assessee **PAN** capture plus **preceding-year audit details** (including previous auditor MRN/FRN, communication-with-predecessor question, outstanding-fee question). `[OFFICIAL]` (Q46, new FAQ Q2) — this is a *lot* of structured data the extraction layer must supply, and a big reason the app is worth building.
- **Invalidation trap:** a UDIN is invalidated at the income-tax e-filing portal on mismatch of **any of 5 parameters — MRN, UDIN, AY/FY, Form No., PAN**; additionally a UDIN generated under "Others" is invalidated if used against a Form No. `[OFFICIAL]` (Q76) → the app must validate these 5 fields *before* submission, not after.

### 2.3 What broke / what to expect to break
- **Portal migration to ICAI DigiCA Platform (announcements 10 & 20 Dec 2025).** Login now uses **SSP credentials**; "First Time Registration for Members" discontinued; password changes and resets happen **only on SSP**, not the UDIN portal. `[OFFICIAL]` ([ICAI restricts UDIN portal login to practicing members](https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html), reproducing the Addendum)
- **Access is narrower than assumed:** only **practicing CAs holding a full-time Certificate of Practice** may log in and generate. **Firms cannot register.** Members without a current full-time CoP may log in **only to view** previously generated UDINs. `[OFFICIAL]` (Q7/Q8/Q10)
- **Ecosystem caution:** ICAI has issued public advisories about **fake ICAI/UDIN look-alike websites** and **fraudulent communications** to members ([ICAI chapter advisory on a fake website](https://www.cainindia.org/news/5_2015/general_advisory_cautioning_members_students_of_icai_and_other_stakeholders_to_beware_of_a_fake_website.html) `[OFFICIAL, dated]`; [public advisory on fraudulent communications](https://cacult.com/important-public-advisory-regarding-fraudulent-communications/) `[SECONDARY]`). A third-party UDIN app therefore **inherits a phishing-suspicion problem**: CAs are trained to distrust UDIN-branded third-party tools. Branding/verifiability matters.

---

## 3. OTP handling options — pros, cons, legal risk

### 3.1 The portal's actual OTP mechanics (the constraint we design against)
`[OFFICIAL]` (Addendum FAQs Q14, Q16, Q26):

| Step | Detail |
|---|---|
| Login | Username `<MRN>@org` (same as SSP), SSP password, **captcha**, then **Send OTP** → OTP to registered **mobile AND email** → Dashboard |
| Per-UDIN submit | Fill form → **Send OTP** → OTP to registered mobile + email → **valid 5 min, must be entered within 90 s** → Verify OTP → **Preview** → Submit |
| Failure handling | **Resend OTP, max 5 attempts** |
| Output | **18-digit UDIN + QR code**, printed or handwritten after signature + membership number |
| Third-party verify | Verifier supplies name/mobile/email, captcha, declaration, then **two separate OTPs** (email + mobile) to validate |

Two design facts follow `[INFERENCE]`: (i) the OTP goes to **both** channels, so an email-based path is *technically* the lower-friction one to intercept — which is exactly why it is the more dangerous one to build; (ii) the **90-second** entry window means any interception pipeline has to be fast and reliable, and any latency/parsing failure burns one of only **5** resends, after which the CA is stuck in a manual flow anyway. Interception buys very little and costs a lot.

### 3.2 Options table

| # | Option | How it works | Pros | Cons | Legal / ethical risk | Verdict |
|---|---|---|---|---|---|---|
| **A** | **App pauses; CA types the OTP** *(recommended baseline)* | App fills the form, clicks Send OTP, then shows a modal "OTP sent to <masked mobile> and <masked email> — enter it here". CA types 6 digits; app submits; app never stores it. | Only design where the **human is genuinely the authenticating party**. No SMS/IMAP permissions. No credential or OTP ever leaves the CA's machine. Survives portal OTP-mechanic changes. Directly parallels the `gst-login` precedent's stated boundary. | Not "hands-free"; CA must be present. 90-second window means the CA must be ready → app must pre-fill everything *before* requesting OTP. | **Low.** This is the CA using their own credential on their own machine for their own attestation. | **Adopt as the only OTP mode in v1.** |
| **B** | **Read SMS programmatically** (Android SMS gateway, `SMS_RECEIVED` app, modem/GSM dongle, notification listener) | App (or a paired phone app) captures the OTP SMS and auto-fills. | Fully unattended. | Requires an Android app with SMS permissions, or a GSM modem — heavy IT footprint for a CA firm. Fragile parsing. The OTP is in a *third-party app's* memory. Google Play restricts SMS/Call-Log permissions to default-handler/limited categories. | **High.** Intercepting an authentication factor that the portal sent to *the member* is at best a terms-of-use breach and at worst looks identical to an account-takeover pattern; it also arguably makes the app a processor of the member's authentication data with no consent basis. | **Reject.** |
| **C** | **Read the registered email via IMAP/API** | App watches the CA's mailbox for the UDIN OTP mail, extracts the code, auto-fills. | No extra hardware; mailbox is already accessible; likely the *easiest* implementation of the three. | OTP mail in a shared/firm mailbox → **the firm's staff can read the CA's authentication factor**. Latency + spam filtering = misses the 90-second window; each miss burns a resend. Mailbox credentials become a new high-value secret the app must hold. Mail-format changes break it silently. | **High.** Very hard to distinguish from credential/OTP phishing infrastructure ("app that reads your email for OTPs" is a malware signature). Also drags the firm's mailbox data into the app's data-processing perimeter under DPDP. | **Reject for production.** Only ever acceptable as a *future, explicitly opt-in, per-CA, local-only* convenience — and even then I'd advise against it. |
| **C′** | *(variant)* **Mailbox read but human confirms** | App pre-fetches the OTP mail, shows the code, CA clicks "use this". | Removes typing latency while keeping a human decision. | Still means the app holds mailbox access; still a phishing-shaped capability. | **High** for the same reason. | **Not recommended.** |

### 3.3 Legal reasoning, expanded

- **ICAI — the attestation is personal.** Only a practicing CA with full-time CoP can generate a UDIN; **firms cannot register**; the UDIN is tied to **MRN** and, on the e-filing side, validated against MRN + PAN + AY/FY + Form No. `[OFFICIAL]` This is not a firm-level administrative act — it is the member's personal certification. `[INFERENCE]` Therefore the OTP step is not friction to remove; it is the **evidentiary trace that the member personally authorised this specific attestation**. An app that types the OTP for the member is arguably manufacturing that trace. **That is the central ethics risk of the whole project.**
- **ICAI Code of Ethics — confidentiality.** The Code requires members to "hold in strict confidence any confidential information obtained in the course of their professional engagement unless the client…" `[OFFICIAL]` ([ICAI Code of Ethics / professional members publication](https://resource.cdn.icai.org/57745mss-pub-profmembers.pdf)). Practical effect: client documents (which the extractor reads, and which contain PAN, financials, bank details) must not be shipped to a third-party server without a clear engagement/consent basis. `[INFERENCE]`
- **DPDP Act 2023.** Client PII + the CA's own authentication data are "personal data"; the firm/app is a **Data Fiduciary** (or Processor for the firm). Obligations: lawful purpose + consent (or a specified legitimate use), purpose limitation, **reasonable security safeguards**, **breach notification to the Data Protection Board and affected principals**, and erasure on withdrawal. Penalties for security-safeguard failures run to **₹250 crore**, with a graded schedule. `[OFFICIAL statute]`; penalty framing per `[SECONDARY]` ([DPDP phased-compliance commentary](https://www.juriscorp.in/phased-compliance-under-dpdp-act-are-you-ready/); [DPDP & OTP compliance note](https://startmessaging.com/blog/dpdp-act-otp-compliance-india)). → **Sending client PDFs to a cloud OCR/LLM endpoint is the single largest DPDP exposure in this design.**
- **IT Act 2000.** §43A (failure to protect data — compensation), §66 (computer-related offences incl. unauthorised access), §66C/66D (identity theft / cheating by personation) are the provisions that would be in play if credentials or OTPs were mishandled or if a member's identity were used to generate UDINs. `[OFFICIAL statute]`; §66 "assistance to facilitate access… in contravention" language per [Cytrain India copy of the Act](http://cyatindia.gov.in/writereaddata/ln_F5C0iN111912012.pdf) `[SECONDARY reproduction]`. → **Credential-sharing across firm members is the scenario that turns a compliance problem into a criminal one** (§7).

---

## 4. Secure credential & data storage for a Windows desktop app

### 4.1 Credential storage — ranked
| Mechanism | What it is | Use for | Notes |
|---|---|---|---|
| **DPAPI, user-scoped** (`CryptProtectData`, current-user) — best via the .NET `ProtectedData` / `System.Security.Cryptography` wrappers | OS-managed encryption keyed to the Windows user profile | **The UDIN portal / SSP password**, stored as ciphertext in a local file or DB | No key management burden; ciphertext is useless if copied to another machine/user. Bind with an **entropy** value and additionally to the account identity. `[OFFICIAL-ish docs]` ([Handling Passwords, Win32](https://learn.microsoft.com/en-us/windows/win32/secbp/handling-passwords)) |
| **Windows Credential Manager** (`CredWrite`/`CredRead`, or `PasswordVault` in WinRT) | OS credential vault, visible to the user in Control Panel | Same, if you want the user to be able to **see/delete** the stored credential themselves | Better for user trust + support ("clear it from Credential Manager"). Also per-user. |
| **DPAPI machine-scoped** | Keyed to the machine | **Avoid** for portal passwords — any local user can decrypt. |
| **Plaintext file / config / registry / `.env`** | — | **Never** | This is the `gst-login` `credentials.json` anti-pattern. |
| Cloud secret managers (Azure Key Vault etc.) | — | Only if you move to a cloud backend (contradicts §4.2) | Adds a network dependency into a login path; needs its own auth story. |

**Design rules `[INFERENCE]`:**
1. **Per-Windows-user vault, not per-app.** The CA's SSP password is *personal*. It must never be readable by another Windows user on the same PC and never synced.
2. **Bind the encrypted blob to (Windows user SID + app install ID + machine)** so a copied vault file is inert.
3. **Never log, never echo, never put in argv.** Pass secrets to the browser-automation layer over a local channel, not the command line — the `gst-login` skill's `-Pass <PASS>` per-call mode is a visible command line / PowerShell history leak.
4. **Optional "don't remember" mode is the default.** Let the CA type the password each session and store nothing.
5. **Optional biometric/TPM gate** (Windows Hello) in front of the vault — nice-to-have, not v1.
6. **Keychain note (for context):** on macOS the equivalent is Keychain `SecItem` with `kSecAttrAccessibleWhenUnlocked`; if the app later ports, do not carry a custom crypto scheme across — use the platform vault. `[INFERENCE]`

### 4.2 Local-first vs cloud
| | Local-first (recommended) | Cloud |
|---|---|---|
| Client documents | Stay on the CA's machine | Leave the firm → DPDP processor obligations, breach liability, ICAI confidentiality tension |
| Credentials | DPAPI/Cred Manager, never leave device | Central vault = single high-value target; "honeypot" risk |
| OTP | Typed into local modal | Would have to traverse the network if any step is server-side |
| Sync/multi-device | **Lost** — the real cost | Convenient |
| Update/telemetry | Manual, but simple | Easy |
| Licensing | Offline licence check | Easy |

**Recommendation `[INFERENCE]`:** **local-first for all client data and all credentials; cloud only for (a) licence/entitlement, (b) anonymised crash telemetry with an explicit opt-in, and (c) an *optional* encrypted metadata-only backup (UDIN number, date, category, client code — never the document).** If you ever add cloud OCR/LLM extraction, it must be opt-in, disclosed, and covered by the firm's engagement letters and privacy notice.

### 4.3 Encryption at rest of client documents
- **Documents**: encrypt the app's document store with AES-256-GCM using a key wrapped by DPAPI (or store in an EFS-encrypted folder). Encrypt the *extracted JSON* too, not just the PDF — the extracted fields (PAN, figures) are the sensitive payload.
- **Database**: if SQLite, use **SQLCipher** (or encrypt individual sensitive columns). Never ship a plain `.db` of client PANs.
- **Temp files**: extraction pipelines leak through temp dirs and crash dumps. Set a private temp dir, delete on exit and on failure, and don't write intermediate PDFs to the OS temp root.
- **Backups**: if the app rolls its own backup, encrypt with a user-supplied passphrase; if it doesn't, say so in the docs so firms include the store in their own encrypted backup.
- **Full-disk**: document the requirement for **BitLocker** on the host as a deployment prerequisite — the app cannot protect against an unencrypted disk being removed.

### 4.4 Where the browser sits in this
`[INFERENCE]` Three options for the automation substrate, in order of preference for this product:
1. **Embedded browser in the app** (WebView2/Chromium with automation) driving the CA's own session on the CA's own machine — the CA *sees* the portal throughout, which is both a safety feature and a trust feature.
2. **Automate a real, visible browser** the CA already uses (Playwright/`ego-browser`-style), in a dedicated profile — acceptable, but session/profile hygiene becomes the app's problem.
3. **Hidden/headless browser** — **reject** for a login+OTP flow: it removes the human's ability to see what's happening, invites "bot" detection, and makes an OTP modal incoherent. (See §7.)

**Never persist an authenticated UDIN session across app restarts.** Log in → act → log out (or let it expire), matching the `gst-login` logout-first discipline.

### 4.5 OTP handling in storage terms
- **OTP is never persisted** — not in the DB, not in logs, not in crash reports, not in telemetry. Hold it in memory only for the life of the submit, then zero it.
- Disable clipboard for the OTP field (or at minimum don't offer "remember").
- Redact OTP-shaped strings (`\b\d{4,8}\b` in OTP context) from any captured screenshot/DOM you store for debugging.
- If you keep an audit log of submissions, log **"OTP requested / OTP verified"** as events — never the value.

### 4.6 Logging & redaction rules
| Never log | Log instead |
|---|---|
| SSP password, OTP, session cookies, auth tokens | "login attempt #n", "OTP requested", "OTP verified", "session established/ended" |
| Full client PAN, bank a/c, full address | Masked PAN (`ABCDE****F`), client code |
| Full document text / LLM prompts containing client data | Field names extracted, document hash, page count |
| Raw HTML/DOM of authenticated pages (contains CSRF tokens, IDs) | Portal version string, UI element names found/missing |

Support-bundle rule `[INFERENCE]`: a "send diagnostics" button must run a **redaction pass** and show the CA exactly what will be sent, before it is sent.

---

## 5. ICAI cybersecurity advisories & rules on credentials/automation

**What is established:**
- ICAI **has** publicly cautioned members about **look-alike/fake ICAI websites** and **fraudulent communications** to members `[OFFICIAL, older advisory]` ([fake-website advisory](https://www.cainindia.org/news/5_2015/general_advisory_cautioning_members_students_of_icai_and_other_stakeholders_to_beware_of_a_fake_website.html)); more recently it has cautioned against **unauthorised WhatsApp groups and fake notices** `[SECONDARY]` ([TaxGuru report](https://taxguru.in/chartered-accountant/icai-cautions-members-unauthorized-whatsapp-groups-fake-notices.html)).
- ICAI emphasises that **UDIN is verified on the portal** and that **third parties can verify without registering** (Q26/Q27), and that **members are alerted whenever a third party verifies their UDIN** (Q29) `[OFFICIAL]`. → *Verification is the anti-fraud mechanism; the member gets an alert on every verification.* An app that generates UDINs the member didn't intend would therefore also trigger alerts the member would see — a partial safety net, not a licence.
- The **credential relationship is explicit**: UDIN portal login == **SSP credentials**, and password reset/change happens **only on SSP** (Q22/Q23) `[OFFICIAL]`. → **There is no separate UDIN password to hold, and no separate revocable UDIN credential.** Compromising the stored secret compromises the member's *entire* ICAI SSP identity, not just UDIN. This materially raises the blast radius and should be stated in the app's own threat model and user consent.

**What I could NOT verify (OPEN QUESTIONS — do not assert these either way):**
1. **Is there an explicit ICAI rule prohibiting *automation* of the UDIN portal?** I found no such published rule. The nearest things are portal terms of use (not reviewed — I did not fetch `udin.icai.org` terms) and the general ethics duties. **OPEN QUESTION.** Action: someone should read the UDIN portal's terms of use / DigiCA terms, and/or raise the question with the UDIN Directorate before launch.
2. **Is there an explicit ICAI rule prohibiting *sharing* SSP/UDIN credentials with a firm or staff?** Not found stated as a standalone prohibition in what I read, but it follows from (a) login being restricted to the member personally, (b) the e-filing validation against **MRN**, and (c) the confidentiality/attestation logic. **OPEN QUESTION**, but treat credential sharing as prohibited in practice. `[INFERENCE]`
3. **A specific ICAI "cybersecurity advisory on UDIN phishing"** — I found general fake-website/fraudulent-communication advisories and search hits referencing an ICAI cyber-security warning, but the primary page did not render usable text, so I cannot quote its content. **OPEN QUESTION**; do not cite specifics.
4. Whether ICAI's DigiCA migration introduced SSO/MFA changes beyond the Dec-2025 announcements. **OPEN QUESTION** — re-check before build.

> **Net for the product `[INFERENCE]`:** design as if (1) credential sharing is prohibited, (2) automation of the OTP step is not defensible, and (3) the app must be *transparent* to ICAI — i.e. a helper the member operates, not a service that operates on the member's behalf.

---

## 6. Risk register

| # | Risk | Likelihood | Impact | Why / evidence | Mitigation |
|---|---|---|---|---|---|
| R1 | **Captcha blocks or is misread** (login and/or verify pages) | High | Low–Med | Portal puts captcha on member login (Q14) and on third-party verify (Q26) `[OFFICIAL]`; `gst-login` documents 1–2 attempts/login | **Show captcha to the human**; never auto-solve. Refresh-and-retry affordance. Log captcha-fail rate as a health metric. |
| R2 | **OTP expires inside 90 seconds** | High | Med | OTP valid 5 min but must be entered within **90 s** (Q16) `[OFFICIAL]` | **Pre-fill everything before Send OTP.** Request OTP as the *last* action, with the field focused and CA ready. Show a live 90-s countdown. `[INFERENCE]` measure real typing latency in pilot. |
| R3 | **OTP never arrives / arrives late** (SMS delay, email spam) | Med | Med | OTP goes to both mobile + email `[OFFICIAL]`; delivery is outside our control | Detect "no OTP in N seconds" and prompt **Resend** with a visible attempt counter (**max 5**, Q16) — never burn resends automatically. Offer "check spam folder" hint for the email OTP. Degrade to full manual portal flow. |
| R4 | **OTP resend exhaustion (5 attempts)** | Med | High | Max 5 resends (Q16) `[OFFICIAL]` | Hard-stop auto-retry well before 5. After 3 failures, hand over to manual. Never loop. `[INFERENCE]` |
| R5 | **Account lockout on repeated login failure** | Med | **High** | Commonly enforced by auth systems; **exact UDIN/SSP lockout policy not verified — OPEN QUESTION** `[INFERENCE]` | Cap login attempts (e.g. 3) per app session, then stop and show SSP reset link (password change is **SSP-only**, Q22/Q23). No background retry loops at all. |
| R6 | **Session expires mid-workflow** | High | Med | Gov portals time out; `gst-login` shows the portal kills sessions on direct authenticated-URL navigation | Save a **draft** of form state before OTP; on expiry, re-login and restore fields (portal supports `Save Draft` for bulk — Q44 `[OFFICIAL]`). |
| R7 | **Portal/UI change breaks automation** (selectors, field order, new mandatory field) | **High** | High | Portal **migrated to DigiCA in Dec-2025**; new mandatory fields already added (PAN + preceding-year audit, Q46/new Q2); bulk limits changed Aug-2026 `[OFFICIAL]` | Selector strategy keyed to **labels/semantic text, not CSS/XPath order**; version-detect the portal; **fail closed and loud** ("portal changed — manual mode") rather than mis-filling. Maintain a fixture-based regression suite + a "portal facts learned the hard way" doc like `gst-login`'s. |
| R8 | **Missed new mandatory field → invalid UDIN / e-filing rejection** | Med | High | UDIN invalidated on any mismatch of MRN/UDIN/AY-FY/Form No./PAN; "Others" category invalid against a Form No. (Q76) `[OFFICIAL]` | **Pre-submit validator** on all 5 params + category-vs-Form-No consistency; show a diff/preview screen before OTP (portal itself has Preview, Q16). |
| R9 | **Wrong category / wrong document type selected → invalid UDIN** | Med | High | Category determines keys & validation (Q32/Q46) `[OFFICIAL]` | Extraction must output a **confidence score**; low confidence → force human pick from the portal's dropdown list (never invent an option). |
| R10 | **Rate limiting / fraud flag on rapid submissions** | Med | Med | **Not verified for UDIN portal — OPEN QUESTION** `[INFERENCE]`; bot-like cadence is what fraud engines look for | Human-paced cadence; natural delays; **no parallel tabs/sessions**; batch via the sanctioned bulk path rather than 50 sequential single-UDIN submits. |
| R11 | **IP binding / new-location challenge** | Low–Med | Med | **Not verified — OPEN QUESTION** `[INFERENCE]`; many Indian gov portals bind sessions to IP/session-fingerprint | Don't use cloud/VPN/proxy egress; run on the CA's own machine on their normal network. Warn on IP/network change; expect re-auth and handle gracefully. |
| R12 | **Multi-user / multi-member firm conflict** | High | Med | UDIN is per-member (MRN); firms can't register (Q7/Q8/Q10) `[OFFICIAL]`. Two staff using one CA's credential = credential sharing | **One vault per Windows user/CA.** No shared service account. If a firm needs multiple CAs, model **per-CA local installs** with an optional shared ledger, not shared credentials. |
| R13 | **Compromise of stored SSP credential = full ICAI identity** | Low (if §4 done) | **Critical** | UDIN login == SSP credentials; reset only on SSP (Q22/Q23) `[OFFICIAL]` | DPAPI/Cred Manager only; see §4; least-privilege; document incident steps (SSP password reset + check `List UDIN` for unknown UDINs + report to ICAI). |
| R14 | **Client data leaked via cloud OCR/LLM** | Med if cloud used | **Critical** | DPDP security-safeguard duty; ICAI confidentiality `[OFFICIAL]` | **Local extraction first.** Any cloud call: opt-in, disclosed, DPA with the processor, no retention, no training. Default OFF. |
| R15 | **App mistaken for a phishing tool by CAs/ICAI** | Med | Med | ICAI has advised members on fake ICAI websites/fraudulent comms `[OFFICIAL/SECONDARY]` | Public, verifiable publisher; code signing; **never ask for anything but the CA's own credentials for their own portal**; publish exactly what the app sends where; maybe pursue an ICAI-visible endorsement/acknowledgement. |
| R16 | **UDIN not generated within the signing deadline** (60-day window) | Med | High | ICAI ties UDIN generation to a time limit linked to signing (60 days, per [ICAI resource 73013](https://resource.cdn.icai.org/73013udin58848.pdf) — *re-verify current text*) `[OFFICIAL, needs re-check]` | The ledger should flag **signed-but-no-UDIN** documents and days remaining; escalate. This is a core product value, not an add-on. |
| R17 | **Unicode/OCR extraction errors in names, figures, dates** | High | Med | Portal validates date formats and numeric-only fields (Q32/Q44) `[OFFICIAL]` | Field-level validation mirroring the portal's rules; numeric-only fields enforced; date normalised to `dd-mm-yyyy`; human confirm on low confidence. |
| R18 | **Lost app data / no backup of the UDIN ledger** | Med | Med | Local-first trade-off | Encrypted export (CSV/JSON) + documented backup step; ledger is reconstructible from `List UDIN` on the portal (Q7) as a fallback. |

### Top 5 for the exec summary
1. **R7 portal/UI change** (high/high) — semantic selectors, version detection, fail-closed, regression fixtures.
2. **R13 stored-credential compromise** (low/critical) — DPAPI/Cred Manager, per-user, no plaintext, no argv.
3. **R2/R4 OTP timing + resend exhaustion** (high/high) — pre-fill everything, OTP last, visible countdown, hard-stop before 5 resends.
4. **R8/R9 invalid UDIN from field/category error** (med/high) — pre-submit validator on the 5 e-filing params + preview-before-OTP.
5. **R12/R14 credential sharing & client-data leakage** (high/critical) — per-CA vaults, local-first extraction, opt-in-only cloud, no shared accounts.

---

## 7. Anti-patterns — do not build these

| Anti-pattern | Why it's disqualifying |
|---|---|
| **Auto-OTP interception** (SMS read, mailbox polling, notification scraping) | Removes the one step that proves the member personally authorised the attestation. Manufactures an authentication trail that did not involve the human. Phishing/malware-shaped. See §3.2 B/C. |
| **Plaintext credentials** (`credentials.json`, config, registry, `.env`, source constant) | The `gst-login` precedent's own warning; fails DPDP "reasonable safeguards" and ICAI confidentiality in one move. |
| **Passwords on the command line / in PowerShell history** | Visible in process lists and shell history. The `gst-login` `-Pass` mode is a leak; don't copy it. |
| **Headless / hidden browser for login+OTP** | CA can't see what's happening; login+OTP with no visible window is indistinguishable from a bot; makes the OTP modal incoherent. Use a visible/embedded browser (§4.4). |
| **Captcha solving (ddddocr-style)** | Clear terms-of-use conflict (the `gst-login` skill says so itself); invites blocking; nothing to gain when a human is already present for the OTP. |
| **Credential sharing across firm members/staff** | UDIN is personal to the MRN; firms cannot register; e-filing validates MRN. Sharing converts a compliance issue into an IT Act §66/§66C exposure and an ethics breach. No shared service account. |
| **Storing client data on third-party servers by default** | DPDP fiduciary duties + ICAI confidentiality. Local-first; cloud only opt-in, disclosed, contracted. |
| **Persisting the OTP anywhere** (DB, logs, telemetry, screenshots, crash dumps) | Turns a one-time factor into a stored secret. §4.5. |
| **Long-lived authenticated session reuse / background refresh** | Extends the compromise window and looks like automation. Log out after the batch, like `gst-login` does on entry. |
| **Silent auto-retry loops on login/OTP failure** | Burns the 5 OTP resends and can trip lockout. Hard caps + human handover (§6 R5). |
| **Deep-linking authenticated portal URLs** | `gst-login` learned the hard way: it kills the session / Access Denied. Navigate by UI only. |
| **Fabricating dropdown values from extraction** | Portal validation (category ↔ Form No., numeric-only fields) will invalidate the UDIN. Force human choice on low confidence. |
| **"We are ICAI" / UDIN-branded lookalike** | ICAI has actively warned members about fake ICAI/UDIN sites. Be unmistakably third-party. |
| **Sending full client PDFs to a cloud LLM without disclosure** | Largest single DPDP/confidentiality exposure in the design. |

---

## 8. Compliance & safety checklist

### 8.1 Before build (decisions that must be made)
- [ ] **Read the UDIN/ICAI DigiCA portal terms of use** and record the exact clause on automated access. **OPEN QUESTION** — not verified in this research.
- [ ] Decide and document: **is the app a "member-operated helper"** (recommended) or a service acting for the member? This one decision drives everything else.
- [ ] Confirm current **bulk UDIN limits** and whether Excel upload applies to the client's categories (Certificates 300 / Tax Audit & Assurance 3–10 UI-only, as of Aug-2026 — likely to change).
- [ ] Confirm the current **60-day UDIN generation window** wording from a current ICAI source.
- [ ] Get a **CA/legal review** of the OTP design and the credential-sharing stance.
- [ ] Decide the cloud posture: **local-first default**; write down what (if anything) leaves the device.

### 8.2 Credentials & authentication
- [ ] Password stored **only** via DPAPI (user-scoped) or Windows Credential Manager; bound to Windows user SID + machine.
- [ ] Vault file inert if copied to another machine/user (verified by test).
- [ ] "Don't remember password" available and **default**.
- [ ] No secret in argv, env, logs, crash dumps, telemetry, or support bundles.
- [ ] **OTP is memory-only**, zeroed after submit, never persisted, never logged.
- [ ] Login attempts capped (≤3) with human handover; **no background retries**.
- [ ] OTP resends capped and surfaced (**portal max 5**); hard-stop before that.
- [ ] 90-second OTP window handled: pre-fill → Send OTP → focused field + countdown.
- [ ] No authenticated session persisted beyond the batch; explicit logout.

### 8.3 Data protection (DPDP / IT Act / ICAI confidentiality)
- [ ] **Data map**: what personal data the app touches (client PAN, names, financials, figures, the CA's own credentials/OTP), where it lives, how long.
- [ ] Client document store encrypted at rest (AES-256-GCM, key DPAPI-wrapped, or SQLCipher); temp files private and wiped.
- [ ] **BitLocker** documented as a deployment prerequisite.
- [ ] Local-first extraction; **no client PDF leaves the device** unless explicitly opted in, with a processor agreement, no-retention, no-training terms.
- [ ] Privacy notice + engagement-letter language covering document processing.
- [ ] **Breach response runbook**: detect → contain → notify Board + affected principals → notify ICAI if a member identity is implicated.
- [ ] Data retention/erasure: configurable, and honour client erasure requests.
- [ ] No client data in telemetry; anonymised opt-in only.

### 8.4 Product / legal posture
- [ ] Unmistakably **third-party** branding; never imply ICAI affiliation.
- [ ] **Code-signed** installer; published publisher identity and checksums.
- [ ] Clear in-app statement: *"This tool uses your own credentials, on your own machine, for your own UDINs. It does not read your SMS or email. It never types your OTP for you."*
- [ ] Per-CA install/vault model documented; **no shared firm credential**.
- [ ] Pre-submit validator on the **5 e-filing params** (MRN, AY/FY, Form No., PAN, UDIN) + category consistency.
- [ ] **Preview/diff screen before Send OTP**, mirroring the portal's own Preview step.
- [ ] Ledger flags **signed-but-no-UDIN** and days-to-deadline.
- [ ] Audit log of events (not secrets): login, OTP requested/verified, UDIN generated, UDIN verified-by-third-party (the portal emails/SMS-alerts the member on this — Q29 — consider surfacing it).
- [ ] Documented **manual fallback**: full manual portal flow always available; app never the only path.
- [ ] Support-bundle redaction preview before sending.
- [ ] Living "portal facts learned the hard way" doc + semantic-selector regression fixtures.

### 8.5 Explicit non-goals (state them in the design doc)
- No SMS/IMAP OTP interception. No captcha solving. No headless login. No credential sharing. No cloud storage of client documents by default. No generation of a UDIN the member has not personally OTP-authorised.

---

## 9. Source list (all accessed 2026-10-27)

**Official (ICAI / portal / statute)**
- UDIN Addendum to FAQs, 5th Edition — ICAI DigiCA Platform (Q7/Q8/Q10/Q14/Q16/Q22/Q23/Q26/Q27/Q29/Q32/Q43/Q44/Q46/Q76 + new FAQs): https://udin.icai.org/assets/images/Addendum%20to%20FAQs%20on%20Unique%20Document%20Identification%20Number%20(UDIN),%205th%20Edition%20-%20ICAI%20DigiCA%20Platform.pdf
- UDIN FAQs (portal): https://udin.icai.org/assets/images/FAQs%20on%20UDIN.pdf
- Comprehensive Guidelines on UDIN: https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf
- ICAI — Generation of UDIN in bulk for certificates: https://icai.org/post/generation-of-udin-in-bulk-for-certificates-17-06-2020
- ICAI — alignment of UDIN time limit with SOC-1/SA 230 (60 days): https://resource.cdn.icai.org/73013udin58848.pdf
- ICAI Code of Ethics / professional members (confidentiality): https://resource.cdn.icai.org/57745mss-pub-profmembers.pdf
- ICAI advisory — fake ICAI website: https://www.cainindia.org/news/5_2015/general_advisory_cautioning_members_students_of_icai_and_other_stakeholders_to_beware_of_a_fake_website.html
- UDIN mobile app manual: https://udin.icai.org/assets/images/ICAI_UDIN_Mobile_App_Manual.pdf
- Microsoft — Handling Passwords (Win32): https://learn.microsoft.com/en-us/windows/win32/secbp/handling-passwords
- IT Act 2000 (text reproduction, incl. §66): http://cyatindia.gov.in/writereaddata/ln_F5C0iN111912012.pdf

**Secondary (professional press / commentary)**
- TaxGuru — ICAI restricts UDIN portal login to practicing members (reproduces Addendum FAQs): https://taxguru.in/corporate-law/icai-restricts-udin-portal-login-practicing-members.html
- TaxGuru — ICAI expands bulk UDIN facility to Tax Audit & Assurance (2026-08-22): https://taxguru.in/corporate-law/icai-expands-bulk-udin-facility-tax-audit-assurance.html
- TaxGuru — ICAI cautions members against fake notices/WhatsApp groups: https://taxguru.in/chartered-accountant/icai-cautions-members-unauthorized-whatsapp-groups-fake-notices.html
- CA Cult — public advisory on fraudulent communications: https://cacult.com/important-public-advisory-regarding-fraudulent-communications/
- Juris Corp — phased compliance under DPDP: https://www.juriscorp.in/phased-compliance-under-dpdp-act-are-you-ready/
- StartMessaging — DPDP and OTP compliance: https://startmessaging.com/blog/dpdp-act-otp-compliance-india
- GovSight-AI (adjacent Indian-gov-portal RPA): https://github.com/theashishmavii/GovSight-AI

**Local**
- `~/.dsh/skills/gst-login\SKILL.md` — read in full (118 lines).
- `~/.dsh/skills/ego-browser\SKILL.md` — **NOT FOUND** (glob under `~/.dsh/skills` returned nothing); skill is catalogued but its docs are not on disk. **OPEN QUESTION** for the Lead.

## 10. Open questions carried forward
1. UDIN/DigiCA portal **terms of use** on automated access — unread; must be read before build sign-off.
2. Existence of an explicit ICAI rule on **automation** of the UDIN portal — not found.
3. Existence of an explicit ICAI rule on **sharing SSP/UDIN credentials** — not found standalone; inferred prohibited.
4. ICAI **cybersecurity advisory specifics** on UDIN phishing — primary page did not render; not quoted.
5. **Account-lockout policy** and **rate limits / IP binding** on the UDIN/SSP login — unverified; drives R5/R10/R11 severity.
6. Current **bulk limits** and whether Excel upload covers the firm's categories — re-verify at build time.
7. Where the **`ego-browser`** skill documentation lives (skipped: file absent).
