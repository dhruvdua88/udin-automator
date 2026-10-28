"""Self-test for the canonical payload + validation engine (stdlib only)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from udin_model import blank_payload, validate  # noqa: E402

p = blank_payload()
p.update({
    "category": "Audit and Assurance Functions",
    "sub_category": "Statutory Audit - Corporate",
    "act_or_law": "Companies Act, 2013",
    "frn": "028145N - DHRUV DUA & CO",
    "signing_date": "28-10-2026",
    "client_name": "Sinteractive Technologies Private Limited",
    "pan": "ABQCS4906B",
    "opinion_applicable": "Yes",
    "opinion_type": "Unmodified",
    "entity_type": "Non-Listed",
    "preceding_applicable": "Yes",
    "audited_last_year": "First Year of Audit",
    "key_fields": [
        {"particulars": "Revenue from operations", "value": "1017.39"},
        {"particulars": "Loss before tax", "value": "278.64"},
        {"particulars": "Shareholders funds", "value": "221.36"},
    ],
    "description": "Financial statements for the period 12 June 2025 to 31 March 2026, FY 2025-26. Dry-run mapping, not submitted.",
    "remarks": "Prepared from Sinteractive_FS_March2026_Final.xlsx",
})
result = validate(p)
print(json.dumps(result, indent=1))
assert result["ok"], result

bad = blank_payload()
bad["category"] = "Certificates and Other Reports"
bad["sub_category"] = "Turnover Certificate"
bad["frn"] = "Not Applicable/Individual Capacity"
bad["signing_date"] = "01-01-2020"
bad["pan"] = "BADPAN"
bad["description"] = "x"
bad["key_fields"] = [{"particulars": "", "value": ""}]
result2 = validate(bad)
print(json.dumps(result2, indent=1))
assert not result2["ok"]
print("MODEL OK")
