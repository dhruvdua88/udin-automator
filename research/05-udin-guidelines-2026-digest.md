# 05 — ICAI "Guidelines on UDIN, 2026": Digest and Implications for the App

**Source:** ICAI, *Comprehensive Guidelines on UDIN* — the legal instrument titled **"Guidelines on Unique Document Identification Number (UDIN), 2026"**, UDIN Directorate, published July 2026 (ISBN 978-93-47892-91-2), 23 pages. Official PDF: https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf (downloaded and text-extracted 27 Oct 2026; local copy `research/_sources/UDIN-Guidelines.pdf` / `.txt`).
**Status note:** clause 2 says the Guidelines "come into effect on such date as may be officially notified by the Council … in the Official Gazette or announced on the Institute's official website." A commencement notification was **not found** in public search on 27 Oct 2026 → `OPEN QUESTION`; until notified, the FAQ/Council-decision regime continues and Chapter X preserves UDINs generated earlier.

**Why this document matters:** it is issued under **Section 15(1) read with Section 15(2)(fa) of the Chartered Accountants Act, 1949** — statutory rule-making power, not guidance notes. It converts several "good practices" (register, communication, revocation courtesy) into **obligations**, and adds a **public-disclosure consequence** for non-compliance. It also reveals a **client-name obligation** that the current portal UI (per Manual v1.2) does not visibly implement.

---

## 1. Structure and key provisions (clause-by-clause)

| Ch. | Clause | What it says (paraphrase with key phrases) |
|---|---|---|
| I | 1–4 | Title **"Guidelines on UDIN, 2026"**; commencement on notified date; **applies to all members holding a full-time CoP** engaged in attestation, assurance, certification or any professional service requiring issuance/authentication of a report, certificate or statement. Defines UDIN as an 18-digit system-generated number; **"UDIN Qualified Assignment"** = an **"Assurance Engagement"** as defined in the Framework for Assurance Engagements and included in **clause 2(2) of the Peer Review Guidelines, 2022**. |
| II | 5–6 | Objectives: stakeholder verification, deterrence against impersonation/forgery, traceability, public interest, regulatory support. Legal authority: **s.15(1) r/w s.15(2)(fa), CA Act 1949**. |
| III | 7 | **Mandatory:** a practising member "shall generate UDIN for all kinds of **assurance engagements** signed by him" — **contemporaneously with signing or within 60 calendar days**; **the UDIN shall also be communicated to the client/appointing authority within that period if it is not written on the document**. |
| IV | 8 | Generation via **secure login** on the UDIN Portal; enter details "such as **date of signing, document type, name of the client, and financial figures** and other required details as amended time to time"; **separate UDIN for each distinct engagement even for the same client**; 18-digit alphanumeric, unique. |
| IV | 9 | UDIN to be **mentioned on the report/certificate in a visible manner, preferably near or below the signature section** ("as per Point 6(b)" — the cross-reference appears erroneous in the published text). |
| IV | 10 | **Record-keeping obligation:** maintain a proper record of **all UDINs generated with corresponding assignment details, for a minimum period as prescribed under the Institute's record-keeping requirements**; UDIN accessible to authorised verifiers; **group/joint audits — each signing partner generates a separate UDIN** for their report. |
| IV | 11 | UDIN "**normally cannot be revoked**"; in **exceptional circumstances within 48 hours** with **reason**; **a member must inform any person who verified a UDIN that it has been revoked/cancelled**; any substitute document requires a **new UDIN** per the Guidelines. |
| V | 12 | Verification via portal on specified key parameters; disclosure limited to information necessary for authentication (member authorises it). |
| V | 13 | **Integration:** the Directorate may integrate with government/regulator portals and the Institute may enter **MoUs or API-based arrangements with such agencies** — i.e. **no member/third-party API** (confirms earlier finding). |
| VI | 14–18 | Directorate of **6–12 members**, ≥50% from Council; powers include **restricting UDIN generation where the Council has stipulated a ceiling on the number of reports**, **prescribing formats for records**, and **prescribing a register to be maintained by practising members for UDINs generated during the year**. |
| VII | 19–20 | UDIN Secretariat (under Directorate/Council) runs the portal, security, monitoring, awareness. |
| VIII | 21–22 | All UDINs **archived in the portal** in a secure retrievable format; ambiguities referred to Council, whose decision is final. |
| IX | 23–24 | Non-compliance reported to Council **quarterly**; in appropriate cases the Directorate **may publish the member's name, nature of violation and penalty in ICAI periodicals** — public reputational consequence. |
| X | 25–26 | Transitional: prior UDINs remain valid under the provisions in force when generated. |

---

## 2. What is genuinely new or sharper than the FAQ regime

1. **Statutory footing.** The mandate now rests on Guidelines under s.15 of the Act, not merely Council resolutions. Non-compliance is framed as a Guidelines breach with disciplinary consequences (Ch. IX).
2. **"Assurance engagement" as the operative scope**, tied to the Framework for Assurance Engagements and Peer Review Guidelines 2022 cl. 2(2) (the "UDIN Qualified Assignment" definition). The FAQ regime described "certificates + GST/tax audit + audit/assurance/attestation"; the Guidelines phrase it as assurance engagements. `OPEN QUESTION`: whether every "certificate" the portal offers is an assurance engagement for this purpose — the portal taxonomy remains the practical authority.
3. **Client name is an express generation detail** (§8(b)) — yet Manual v1.2 describes no client-name field in the DigiCa form. Either the portal has since added it, the Guidelines are describing a requirement the form satisfies indirectly, or there is an implementation gap. **Phase 0 must check this.**
4. **Communication duty** (§7(c)): if the UDIN is not written on the document, the member must communicate it to the client/appointing authority **within the 60-day window**. The app should generate and log that communication.
5. **Record and register duty** (§10(a), §18(vi)): a register is now explicitly contemplated, and the Directorate may **prescribe its format**. The app's register should be format-adaptable and export in the prescribed layout once published.
6. **Revocation courtesy duty** (§11(c)): inform every verifier. The portal already alerts members when a UDIN is verified (FAQ Q27) — the app should capture those alerts/events and produce a revocation notice list.
7. **Ceiling enforcement** (§18(iii)): the Directorate may restrict generation where the Council caps report numbers — this is the legal hook for the **60 tax-audit ceiling** now enforced at the portal.

---

## 3. Related operational change: s.44AB field-level validation and the 60-audit ceiling

Separate ICAI UDIN Directorate announcement, **11 Feb 2026** (reproduced at https://taxguru.in/chartered-accountant/icai-introduces-field-level-validation-udin-section-44ab.html):

- The Council (442nd meeting, 26–27 May 2025) capped **tax audits at 60 per member w.e.f. 1 April 2026**; at the UDIN portal the ceiling applies to **Form 3CA (3rd proviso to s.44AB), Form 3CB under 44AB(a), Form 3CB under 44AB(b), and Form 3CB (Combined) under 44AB**. From 1 Apr 2026, UDIN generation for those categories is blocked beyond the ceiling.
- **Field-level validation is live now** for **all s.44AB sub-categories (clauses a–e)** under "GST and Tax Audit". The portal asks preliminary questions and only proceeds if the validation logic passes:

| Clause | Preliminary question(s) | Validation logic |
|---|---|---|
| 44AB(a) | Cash transactions ≤ 5%? (Yes/No) | Yes → turnover > ₹10 cr; No → turnover > ₹1 cr |
| 44AB(b) | — | Gross receipts > ₹50 lakh |
| 44AB(c) | Income claimed lower than deemed profits u/s 44AE/44BB/44BBB? | Proceed only if **Yes** |
| 44AB(d) | (i) Gross receipts ≤ ₹50 lakh? (ii) > ₹50 lakh but ≤ ₹75 lakh **and** cash receipts ≤5%? (iii) income claimed lower than deemed profits u/s 44ADA? (iv) total income > basic exemption limit? | Proceed only if (i) **or** (ii) = Yes, **and** (iii) **and** (iv) = Yes |
| 44AB(e) | (i) s.44AD(4) applicable? (ii) total income > basic exemption limit? | Proceed only if both = Yes |

**Implication for us:** the app's pre-flight validator must not stop at PAN/GSTIN/date checks. For tax-audit documents it must capture these preliminary answers (from the Form 3CD/3CB data or by asking the member) and validate the thresholds **before** opening the portal; otherwise the portal will reject the submission at the last step, after the CA has already spent the OTP window.

---

## 4. What changes in our plan

| Area | Change |
|---|---|
| **Register** | Now a compliance obligation (§10(a)) and possibly a prescribed format (§18(vi)). Phase 1 must store UDIN + full assignment details; Phase 3 must ship export templates and be ready to match an ICAI-prescribed register format. Retention: at least the Institute's record-keeping minimum (no number in the Guidelines — keep the ≥8-year firm posture). |
| **Client name** | Add `client_name` as a mandatory local field regardless of the portal UI; Phase 0 confirms whether the DigiCa form now exposes it. This also removes an earlier "no client name" assumption from the plan. |
| **Communication tracking** | Add `communicated_to_client_at`, channel, evidence; app generates a UDIN communication letter/email for documents where the UDIN is not printed on the signed document. |
| **Revocation workflow** | Add verifier-notification step: capture verification alerts/events; on revoke, produce a notice to every verifier and keep proof. |
| **Ceiling tracking** | Track tax-audit UDIN counts per member and per form category (3CA 3rd proviso, 3CB(a), 3CB(b), 3CB combined); warn before the 60-audit ceiling; reconcile with portal quota (`/udin-config/get-quota`, `/udin-config/getEffectiveUdinCount`). Counting rules/exclusions for the ceiling: `OPEN QUESTION` (Phase 0). |
| **44AB validation** | Add a clause-specific validation module with the preliminary questions and thresholds above; block/flag before portal entry. |
| **Scope language** | Use "assurance engagements" per Guidelines, but keep the portal's three categories as the operational taxonomy; verify the certificate-vs-assurance nuance with the UDIN Directorate/legal review. |
| **Risk framing** | Public disclosure of violations (Ch. IX) raises the stakes of wrong submissions — strengthens the case for mandatory human confirmation and pre-flight validation. |

---

## 5. Open questions added by this document

1. **Commencement date / notification** of the Guidelines (published July 2026; clause 2 requires a notification). Check ICAI announcements before quoting it as operative.
2. Whether the **client-name field** now exists in the DigiCa generation form; if not, how ICAI expects §8(b) to be satisfied.
3. The **prescribed register format** under §18(vi) — not yet published.
4. Whether "**UDIN Qualified Assignment**" (assurance engagement) narrows the certificate scope in practice.
5. **60-audit ceiling counting rules and exclusions** (branches, bank audits, different forms, migrated assignments) — needed for a trustworthy counter.
6. The "Point 6(b)" cross-reference in §9 — likely a drafting error; confirm intended placement requirement.
7. Whether a copy of the *comprehensive* Guidelines (with annexures/forms) exists beyond the 23-page booklet.

---

## 6. Sources

- ICAI, *Comprehensive Guidelines on UDIN* (Guidelines on UDIN, 2026), UDIN Directorate, July 2026 — https://udin.icai.org/assets/images/UDIN%20Guidelines.pdf (local: `research/_sources/UDIN-Guidelines.pdf`)
- ICAI UDIN Directorate announcement, 11 Feb 2026 — field-level validation under s.44AB + 60-audit ceiling — https://taxguru.in/chartered-accountant/icai-introduces-field-level-validation-udin-section-44ab.html
- ICAI tax-audit ceiling counting rules (secondary) — https://taxguru.in/chartered-accountant/icai-tax-audit-limit-60-assignments-counting-rules-exclusions-udin.html
- Portal manual v1.2 (Dec 2025) for the current form behaviour — https://www.caclubindia.com/news/files_download.asp?news_item_id=25941
- FAQ 4th edition (2024) for the pre-Guidelines regime — https://icai-call-sahayata.icai.org/wp-content/uploads/2025/03/FAQs-on-UDIN-4th-Edition-Final-02-02-24-2-NI.pdf

*All URLs accessed 27 October 2026. Clause text paraphrased from the official PDF; local full text retained for audit. No portal login or UDIN generation was performed.*
