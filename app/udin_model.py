"""Canonical UDIN payload, validation rules and batch-file readers.

This is the contract every input mode (document, manual form, Excel/CSV) must
produce before the portal is touched. It encodes what the live portal enforces,
plus the local rules from the 2026 Guidelines (client name, 60-day window, etc.).

No dependencies: stdlib only (xlsx is read directly from the zip/XML).
"""

from __future__ import annotations

import csv
import re
import zipfile
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

CATEGORIES = ["Certificates and Other Reports", "Tax Audit", "Audit and Assurance Functions"]
OPINION_TYPES = ["Unmodified", "Qualified", "Adverse", "Disclaimer"]
ENTITY_TYPES = ["Listed", "Non-Listed"]
YES_NO = ["Yes", "No"]
PRECEDING_OPTIONS = ["Yes", "No", "First Year of Audit"]
FEES_OPTIONS = ["Yes", "No", "Not Known"]

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
DESC_RE = re.compile(r"^[A-Za-z0-9 .,_\-–]+$")
DATE_FMT = "%d-%m-%Y"

TEMPLATE_HEADERS = [
    "category", "sub_category", "form_or_section", "act_or_law", "frn",
    "signing_date", "client_name", "pan", "opinion_applicable", "opinion_type",
    "entity_type", "preceding_applicable", "audited_last_year", "prev_auditor",
    "communication", "communication_date", "outstanding_fees",
    "particulars_1", "value_1", "particulars_2", "value_2", "particulars_3", "value_3",
    "description", "remarks",
]


def blank_payload() -> dict:
    return {
        "category": "",
        "sub_category": "",
        "form_or_section": "",
        "act_or_law": "",
        "frn": "",
        "signing_date": "",
        "client_name": "",
        "pan": "",
        "opinion_applicable": "No",
        "opinion_type": "",
        "entity_type": "",
        "preceding_applicable": "No",
        "audited_last_year": "",
        "prev_auditor": "",
        "communication": "",
        "communication_date": "",
        "outstanding_fees": "",
        "key_fields": [
            {"particulars": "", "value": ""},
            {"particulars": "", "value": ""},
            {"particulars": "", "value": ""},
        ],
        "description": "",
        "remarks": "",
        "preliminary_44ab": {
            "cash_le_5pct": "",
            "turnover": "",
            "gross_receipts": "",
            "sec_44ad_4": "",
            "deemed_profit_lower": "",
            "total_income_gt_bel": "",
        },
    }


def validate(p: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    def req(field: str, label: str):
        if not str(p.get(field, "")).strip():
            errors.append(f"{label} is required")

    if p.get("category") not in CATEGORIES:
        errors.append("Category must be one of: " + "; ".join(CATEGORIES))
    req("sub_category", "Sub-category / Type of Audit / Type of Certificate")
    if p.get("category") == "Tax Audit":
        req("form_or_section", "Form / Section")
    if p.get("category") == "Audit and Assurance Functions":
        req("act_or_law", "Act / Law / Statute")
    req("frn", "FRN (or 'Not Applicable/Individual Capacity')")
    req("client_name", "Client name (Guidelines 2026 s.8(b))")

    if not PAN_RE.match(str(p.get("pan", "")).strip().upper()):
        errors.append("PAN of auditee must match AAAAA9999A")

    date_text = str(p.get("signing_date", "")).strip()
    try:
        signing = datetime.strptime(date_text, DATE_FMT)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if signing > today:
            errors.append("Signing date cannot be in the future")
        if (today - signing).days > 60:
            errors.append("Signing date is older than the 60-day generation window")
    except ValueError:
        errors.append("Signing date must be DD-MM-YYYY")

    desc = str(p.get("description", "")).strip()
    if not (5 <= len(desc) <= 250):
        errors.append("Document Description must be 5-250 characters")
    elif not DESC_RE.match(desc):
        errors.append("Document Description contains characters the portal rejects")
    if len(str(p.get("remarks", ""))) > 250:
        errors.append("Remarks must be 250 characters or fewer")

    if p.get("category") in ("Tax Audit", "Audit and Assurance Functions"):
        if p.get("opinion_applicable") not in YES_NO:
            errors.append("Auditor's Opinion applicability must be Yes/No")
        elif p.get("opinion_applicable") == "Yes":
            if p.get("opinion_type") not in OPINION_TYPES:
                errors.append("Choose an opinion type")
            if p.get("entity_type") not in ENTITY_TYPES:
                errors.append("Choose Listed/Non-Listed entity type")
        if p.get("preceding_applicable") not in YES_NO:
            errors.append("Preceding-year audit applicability must be Yes/No")
        elif p.get("preceding_applicable") == "Yes":
            if p.get("audited_last_year") not in PRECEDING_OPTIONS:
                errors.append("Choose preceding-year audit status")
            elif p.get("audited_last_year") == "No":
                req("prev_auditor", "Previous auditor MRN/FRN")
                if p.get("communication") not in YES_NO:
                    errors.append("Communication with previous auditor must be Yes/No")
                if p.get("communication") == "Yes" and not p.get("communication_date"):
                    errors.append("Communication date is required")
                if p.get("outstanding_fees") not in FEES_OPTIONS:
                    errors.append("Outstanding-fee status is required")

    rows = [r for r in p.get("key_fields", []) if str(r.get("particulars", "")).strip() or str(r.get("value", "")).strip()]
    minimum = 2 if p.get("category") == "Certificates and Other Reports" else 1
    if len(rows) < minimum:
        errors.append(f"At least {minimum} key field(s) with particulars + figure are required")
    for i, row in enumerate(rows, 1):
        if not str(row.get("particulars", "")).strip():
            errors.append(f"Key field {i}: particulars are required")
        if str(row.get("value", "")).strip() == "":
            errors.append(f"Key field {i}: figure/value is required")
        if len(str(row.get("particulars", ""))) > 50:
            errors.append(f"Key field {i}: particulars must be 50 characters or fewer")

    if p.get("category") == "Tax Audit":
        if not str(p["preliminary_44ab"].get("turnover", "")).strip():
            warnings.append("s.44AB: turnover is missing; the portal may reject at generation")
        if p.get("sub_category", "").startswith("Statutory Audit") and p.get("opinion_applicable") == "Yes":
            if p.get("entity_type") == "":
                warnings.append("Entity type is missing for the auditor's opinion block")

    if str(p.get("frn", "")).strip() in ("", "Not Applicable/Individual Capacity"):
        warnings.append("Individual-capacity UDIN: put the firm details in Document Description per ICAI guidance")

    if p.get("client_name") and p.get("client_name", "").lower() in desc.lower():
        warnings.append("Document Description contains the client name; key fields are meant to avoid client details")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "").group(0)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def read_xlsx(path: str) -> list[dict]:
    rows: list[list[str]] = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
            for si in root.findall(f"{ns}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{ns}t")))
        sheet_name = next((n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")), None)
        if not sheet_name:
            raise ValueError("no worksheet found in xlsx")
        root = ET.fromstring(z.read(sheet_name))
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        for row in root.iter(f"{ns}row"):
            cells: dict[int, str] = {}
            for c in row.findall(f"{ns}c"):
                ref = c.get("r", "")
                idx = _col_index(ref) if ref else len(cells)
                t = c.get("t")
                v = c.find(f"{ns}v")
                inline = c.find(f"{ns}is")
                if t == "inlineStr" and inline is not None:
                    val = "".join(x.text or "" for x in inline.iter(f"{ns}t"))
                elif v is None:
                    val = ""
                elif t == "s":
                    val = shared[int(v.text)]
                elif t == "b":
                    val = "Yes" if v.text == "1" else "No"
                else:
                    val = v.text or ""
                cells[idx] = val
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
    return rows


def read_csv(path: str) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [row for row in csv.reader(fh)]


def load_batch(path: str) -> list[dict]:
    """Read an XLSX/CSV batch template into validated payload dicts."""
    ext = path.lower().rsplit(".", 1)[-1]
    raw = read_xlsx(path) if ext == "xlsx" else read_csv(path)
    if not raw:
        return []
    headers = [str(h).strip().lower() for h in raw[0]]
    payloads = []
    for line in raw[1:]:
        if not any(str(c).strip() for c in line):
            continue
        row = {headers[i]: (line[i] if i < len(line) else "") for i in range(len(headers))}
        p = blank_payload()
        for key in ("category", "sub_category", "form_or_section", "act_or_law", "frn",
                    "signing_date", "client_name", "pan", "opinion_applicable", "opinion_type",
                    "entity_type", "preceding_applicable", "audited_last_year", "prev_auditor",
                    "communication", "communication_date", "outstanding_fees", "description", "remarks"):
            if key in row:
                p[key] = str(row[key]).strip()
        fields = []
        for i in (1, 2, 3):
            particulars = str(row.get(f"particulars_{i}", "")).strip()
            value = str(row.get(f"value_{i}", "")).strip()
            if particulars or value:
                fields.append({"particulars": particulars, "value": value})
        p["key_fields"] = fields or blank_payload()["key_fields"]
        payloads.append(p)
    return payloads
