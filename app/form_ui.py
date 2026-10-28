"""Validated UDIN form — the manual input mode.

Run:  python app/form_ui.py [--file app/templates/udin_batch_template.xlsx]

Every field the portal needs is on one screen. Validate before touching the
portal; load one row from the Excel/CSV batch template; save the payload JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from tkinter import Tk, filedialog, messagebox, ttk
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parent))

from udin_model import (  # noqa: E402
    CATEGORIES, ENTITY_TYPES, FEES_OPTIONS, OPINION_TYPES, PRECEDING_OPTIONS,
    YES_NO, blank_payload, load_batch, validate,
)


def run(initial_file: str | None = None) -> int:
    root = Tk()
    root.title("UDIN Automator — validated form")
    root.geometry("1000x820")

    vars: dict[str, tk.StringVar] = {}
    key_vars: list[tuple[tk.StringVar, tk.StringVar]] = []

    def add_row(parent, row: int, label: str, widget):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=3)
        widget.grid(row=row, column=1, sticky="w", padx=6, pady=3, columnspan=3)
        return widget

    def entry(parent, row: int, label: str, key: str, width: int = 60):
        var = tk.StringVar()
        vars[key] = var
        add_row(parent, row, label, ttk.Entry(parent, textvariable=var, width=width))
        return var

    def combo(parent, row: int, label: str, key: str, values: list[str], width: int = 40):
        var = tk.StringVar()
        vars[key] = var
        add_row(parent, row, label, ttk.Combobox(parent, textvariable=var, values=values, width=width))
        return var

    main = ttk.Frame(root)
    main.pack(fill="both", expand=True, padx=10, pady=8)

    # Input mode banner
    mode = ttk.LabelFrame(main, text="Input mode")
    mode.pack(fill="x", pady=(0, 6))
    ttk.Label(mode, text="Fill the form  ·  Load Excel/CSV  ·  (Document extraction is the next slice)",
              foreground="#555").pack(anchor="w", padx=8, pady=4)

    body = ttk.Frame(main)
    body.pack(fill="both", expand=True)

    left = ttk.LabelFrame(body, text="Assignment")
    left.pack(side="left", fill="both", expand=True, padx=(0, 6))
    right = ttk.LabelFrame(body, text="Attestation")
    right.pack(side="left", fill="both", expand=True, padx=(6, 0))

    combo(left, 0, "Category", "category", CATEGORIES)
    entry(left, 1, "Sub-category / type", "sub_category")
    entry(left, 2, "Form / section", "form_or_section")
    entry(left, 3, "Act / law / statute", "act_or_law")
    entry(left, 4, "FRN (or Individual)", "frn")
    entry(left, 5, "Signing date (DD-MM-YYYY)", "signing_date")
    entry(left, 6, "Client name", "client_name")
    entry(left, 7, "PAN of auditee", "pan")
    entry(left, 8, "Document description (5-250)", "description")
    entry(left, 9, "Remarks (optional)", "remarks")

    combo(right, 0, "Auditor's opinion applicable", "opinion_applicable", YES_NO)
    combo(right, 1, "Opinion type", "opinion_type", OPINION_TYPES)
    combo(right, 2, "Entity type", "entity_type", ENTITY_TYPES)
    combo(right, 3, "Preceding-year applicable", "preceding_applicable", YES_NO)
    combo(right, 4, "Audited last year", "audited_last_year", PRECEDING_OPTIONS)
    entry(right, 5, "Previous auditor MRN/FRN", "prev_auditor")
    combo(right, 6, "Communication with previous auditor", "communication", YES_NO)
    entry(right, 7, "Communication date", "communication_date")
    combo(right, 8, "Outstanding fees", "outstanding_fees", FEES_OPTIONS)

    figures = ttk.LabelFrame(main, text="Key fields (2 minimum for certificates; 1 for audit/assurance)")
    figures.pack(fill="x", pady=6)
    ttk.Label(figures, text="Particulars (≤50 chars)").grid(row=0, column=0, padx=6, sticky="w")
    ttk.Label(figures, text="Figure / value").grid(row=0, column=1, padx=6, sticky="w")
    for i in range(3):
        pv, vv = tk.StringVar(), tk.StringVar()
        key_vars.append((pv, vv))
        ttk.Entry(figures, textvariable=pv, width=55).grid(row=i + 1, column=0, padx=6, pady=3)
        ttk.Entry(figures, textvariable=vv, width=25).grid(row=i + 1, column=1, padx=6, pady=3)

    actions = ttk.Frame(main)
    actions.pack(fill="x", pady=4)

    out = tk.Text(main, height=9, wrap="word")
    out.pack(fill="both", expand=False, pady=(4, 0))

    def payload() -> dict:
        p = blank_payload()
        for key in ("category", "sub_category", "form_or_section", "act_or_law", "frn",
                    "signing_date", "client_name", "pan", "opinion_applicable", "opinion_type",
                    "entity_type", "preceding_applicable", "audited_last_year", "prev_auditor",
                    "communication", "communication_date", "outstanding_fees", "description", "remarks"):
            p[key] = vars[key].get().strip()
        p["key_fields"] = [
            {"particulars": pv.get().strip(), "value": vv.get().strip()}
            for pv, vv in key_vars
            if pv.get().strip() or vv.get().strip()
        ] or blank_payload()["key_fields"]
        return p

    def fill(p: dict) -> None:
        for key, var in vars.items():
            if key in p and p[key] is not None:
                var.set(str(p[key]))
        for i, (pv, vv) in enumerate(key_vars):
            field = p.get("key_fields", [])
            pv.set(field[i]["particulars"] if i < len(field) else "")
            vv.set(field[i]["value"] if i < len(field) else "")

    def do_validate() -> dict:
        result = validate(payload())
        out.delete("1.0", "end")
        out.insert("end", ("VALID\n" if result["ok"] else "INVALID\n"))
        for e in result["errors"]:
            out.insert("end", f"ERROR  {e}\n")
        for w in result["warnings"]:
            out.insert("end", f"WARN   {w}\n")
        color = "#0a7" if result["ok"] else "#b00"
        out.tag_add("status", "1.0", "1.end")
        out.tag_configure("status", foreground=color)
        return result

    def do_load() -> None:
        path = filedialog.askopenfilename(
            title="Load UDIN batch",
            filetypes=[("Excel/CSV", "*.xlsx *.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            rows = load_batch(path)
            if not rows:
                messagebox.showwarning("Empty", "No data rows found in the file")
                return
            fill(rows[0])
            out.delete("1.0", "end")
            out.insert("end", f"Loaded {len(rows)} row(s); showing row 1 of {len(rows)}.\n")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Load failed", str(exc))

    def do_save() -> None:
        result = do_validate()
        if not result["ok"]:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        Path(path).write_text(json.dumps(payload(), indent=2), encoding="utf-8")
        out.insert("end", f"\nSaved payload: {path}\n")

    def do_clear() -> None:
        fill(blank_payload())
        vars["signing_date"].set(datetime.now().strftime("%d-%m-%Y"))
        out.delete("1.0", "end")

    ttk.Button(actions, text="Validate", command=do_validate).pack(side="left", padx=4)
    ttk.Button(actions, text="Load Excel / CSV", command=do_load).pack(side="left", padx=4)
    ttk.Button(actions, text="Save payload JSON", command=do_save).pack(side="left", padx=4)
    ttk.Button(actions, text="Clear", command=do_clear).pack(side="left", padx=4)

    do_clear()
    vars["frn"].set("028145N - DHRUV DUA & CO")
    if initial_file:
        try:
            rows = load_batch(initial_file)
            if rows:
                fill(rows[0])
                out.insert("end", f"Loaded {len(rows)} row(s) from {initial_file}\n")
        except Exception as exc:  # noqa: BLE001
            out.insert("end", f"Could not load {initial_file}: {exc}\n")

    root.mainloop()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None)
    args = ap.parse_args()
    raise SystemExit(run(args.file))
