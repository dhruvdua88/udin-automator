"""UDIN Automator — desktop workbench (validated form).

A four-step desktop UI for preparing a UDIN payload:
  1 Assignment   2 Attestation   3 Figures & Description   4 Import / Batch

Everything is validated locally before the portal is touched; the user only
authenticates (CAPTCHA + OTP) when the payload is ready.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))

from udin_model import (  # noqa: E402
    CATEGORIES, ENTITY_TYPES, FEES_OPTIONS, OPINION_TYPES, PRECEDING_OPTIONS,
    TEMPLATE_HEADERS, YES_NO, blank_payload, load_batch, validate,
)

FONT = "Segoe UI"
C = {
    "navy": "#0f172a", "navy2": "#1e293b", "navy3": "#334155",
    "bg": "#f1f5f9", "card": "#ffffff", "text": "#0f172a",
    "muted": "#64748b", "border": "#e2e8f0",
    "accent": "#2563eb", "accent_dark": "#1d4ed8",
    "danger": "#dc2626", "ok": "#059669", "warn": "#b45309",
}

LABEL_TO_KEY = {
    "Category": "category",
    "Sub-category": "sub_category",
    "Form / Section": "form_or_section",
    "Act / Law": "act_or_law",
    "FRN": "frn",
    "Client name": "client_name",
    "PAN": "pan",
    "Signing date": "signing_date",
    "Document Description": "description",
    "Remarks": "remarks",
    "Auditor's Opinion": "opinion_type",
    "opinion": "opinion_applicable",
    "Preceding": "audited_last_year",
    "Key field": None,
}


def error_key(message: str) -> str | None:
    for prefix, key in LABEL_TO_KEY.items():
        if message.lower().startswith(prefix.lower()):
            return key
    return None


class App:
    def __init__(self, root: tk.Tk, initial_file: str | None = None):
        self.root = root
        self.vars: dict[str, tk.StringVar] = {}
        self.widgets: dict[str, tk.Widget] = {}
        self.err_labels: dict[str, tk.Label] = {}
        self.key_rows: list[dict] = []
        self.batch: list[dict] = []
        self.valid = {"ok": False, "errors": [], "warnings": []}
        self._pending = None
        self.doc_path: Path | None = None

        self._style()
        self._chrome()
        self._pages()
        self._bind_keys()
        self.new()
        self.show_step(1)
        if initial_file:
            self.load_batch(initial_file)

    # ---------------------------------------------------------------- style
    def _style(self):
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("TFrame", background=C["bg"])
        st.configure("Card.TFrame", background=C["card"])
        st.configure("TLabel", background=C["card"], foreground=C["text"], font=(FONT, 9))
        st.configure("Muted.TLabel", background=C["card"], foreground=C["muted"], font=(FONT, 9))
        st.configure("H1.TLabel", background=C["navy"], foreground="#ffffff", font=(FONT, 17, "bold"))
        st.configure("H1Sub.TLabel", background=C["navy"], foreground="#94a3b8", font=(FONT, 9))
        st.configure("PageTitle.TLabel", background=C["bg"], foreground=C["text"], font=(FONT, 15, "bold"))
        st.configure("PageSub.TLabel", background=C["bg"], foreground=C["muted"], font=(FONT, 9))
        st.configure("Section.TLabel", background=C["card"], foreground=C["text"], font=(FONT, 10, "bold"))
        st.configure("Err.TLabel", background=C["card"], foreground=C["danger"], font=(FONT, 8))
        st.configure("Pill.TLabel", background=C["navy2"], foreground="#e2e8f0",
                     font=(FONT, 9, "bold"), padding=(10, 4))
        st.configure("TEntry", fieldbackground="#ffffff", bordercolor=C["border"],
                     lightcolor=C["border"], darkcolor=C["border"], padding=4)
        st.configure("TCombobox", fieldbackground="#ffffff", padding=3)
        st.configure("TButton", padding=(10, 5), font=(FONT, 9))
        st.configure("Primary.TButton", background=C["accent"], foreground="#ffffff",
                     borderwidth=0, padding=(14, 7), font=(FONT, 9, "bold"))
        st.map("Primary.TButton",
               background=[("active", C["accent_dark"]), ("disabled", "#94a3b8")],
               foreground=[("disabled", "#e2e8f0")])
        st.configure("Step.TButton", background=C["navy"], foreground="#cbd5e1",
                     borderwidth=0, anchor="w", padding=(18, 11), font=(FONT, 10))
        st.map("Step.TButton", background=[("active", C["navy2"])])
        st.configure("Active.TButton", background=C["navy2"], foreground="#ffffff",
                     borderwidth=0, anchor="w", padding=(18, 11), font=(FONT, 10, "bold"))
        st.configure("Treeview", rowheight=26, font=(FONT, 9), background="#ffffff",
                     fieldbackground="#ffffff")
        st.configure("Treeview.Heading", font=(FONT, 9, "bold"))

    # ---------------------------------------------------------------- chrome
    def _chrome(self):
        self.root.configure(bg=C["bg"])
        self.root.title("UDIN Automator — desktop workbench")
        self.root.geometry("1240x820+40+30")
        self.root.minsize(1100, 720)

        header = tk.Frame(self.root, bg=C["navy"], height=78)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="UDIN", bg=C["navy"], fg="#60a5fa",
                 font=(FONT, 18, "bold")).pack(side="left", padx=(22, 6))
        tk.Label(header, text="Automator", bg=C["navy"], fg="#ffffff",
                 font=(FONT, 18)).pack(side="left")
        tk.Label(header, text="Assisted UDIN preparation  ·  you confirm, you authenticate",
                 bg=C["navy"], fg="#94a3b8", font=(FONT, 9)).pack(side="left", padx=18)
        self.pill = tk.Label(header, text="NOT READY", bg=C["navy2"], fg="#fca5a5",
                             font=(FONT, 9, "bold"), padx=12, pady=5)
        self.pill.pack(side="right", padx=22)

        footer = tk.Frame(self.root, bg="#ffffff", highlightbackground=C["border"], highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        self.footer_status = tk.Label(footer, text="", bg="#ffffff", fg=C["muted"], font=(FONT, 9))
        self.footer_status.pack(side="right", padx=16)
        ttk.Button(footer, text="Validate", style="Primary.TButton",
                   command=self.validate_now).pack(side="left", padx=(14, 6), pady=9)
        ttk.Button(footer, text="Save payload JSON", command=self.save_json).pack(side="left", padx=4, pady=9)
        ttk.Button(footer, text="Copy JSON", command=self.copy_json).pack(side="left", padx=4, pady=9)
        ttk.Button(footer, text="Clear", command=self.new).pack(side="left", padx=4, pady=9)
        self.prepare_btn = ttk.Button(footer, text="Prepare in portal", style="Primary.TButton",
                                      command=self.prepare, state="disabled")
        self.prepare_btn.pack(side="right", padx=14, pady=9)

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg=C["navy"], width=238)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="WORKFLOW", bg=C["navy"], fg="#64748b",
                 font=(FONT, 8, "bold")).pack(anchor="w", padx=22, pady=(22, 8))
        self.step_buttons = {}
        for n, label in [(1, "1   Assignment"), (2, "2   Attestation"),
                         (3, "3   Figures & description"), (4, "4   Import / batch")]:
            b = ttk.Button(side, text=label, style="Step.TButton", command=lambda i=n: self.show_step(i))
            b.pack(fill="x", padx=12, pady=2)
            self.step_buttons[n] = b
        tk.Frame(side, bg=C["navy"], height=20).pack(fill="x")
        tk.Label(side, text="VALIDATION", bg=C["navy"], fg="#64748b",
                 font=(FONT, 8, "bold")).pack(anchor="w", padx=22, pady=(10, 4))
        self.side_errors = tk.Label(side, text="No checks yet", bg=C["navy"], fg="#94a3b8",
                                    justify="left", anchor="nw", wraplength=190, font=(FONT, 8))
        self.side_errors.pack(anchor="w", padx=22)
        tk.Label(side, text="v0.2  ·  local-first", bg=C["navy"], fg="#475569",
                 font=(FONT, 8)).pack(side="bottom", anchor="w", padx=22, pady=16)

        self.content = tk.Frame(body, bg=C["bg"])
        self.content.pack(side="left", fill="both", expand=True, padx=22, pady=16)
        self.page_title = ttk.Label(self.content, text="", style="PageTitle.TLabel")
        self.page_title.pack(anchor="w")
        self.page_sub = ttk.Label(self.content, text="", style="PageSub.TLabel")
        self.page_sub.pack(anchor="w", pady=(2, 12))
        self.page_host = tk.Frame(self.content, bg=C["bg"])
        self.page_host.pack(fill="both", expand=True)

    # ---------------------------------------------------------------- pages
    def _pages(self):
        self.pages = {}
        self.pages[1] = self._page_assignment()
        self.pages[2] = self._page_attestation()
        self.pages[3] = self._page_figures()
        self.pages[4] = self._page_import()

    def card(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        outer.pack(fill="x", pady=(0, 12))
        tk.Label(outer, text=title, bg=C["card"], fg=C["text"],
                 font=(FONT, 10, "bold")).pack(anchor="w", padx=16, pady=(12, 6))
        inner = tk.Frame(outer, bg=C["card"])
        inner.pack(fill="x", padx=16, pady=(0, 14))
        return inner

    def field(self, parent, row: int, label: str, key: str, kind: str = "entry",
              values: list[str] | None = None, width: int = 42) -> tk.StringVar:
        tk.Label(parent, text=label, bg=C["card"], fg=C["muted"],
                 font=(FONT, 8), anchor="w").grid(row=row, column=0, sticky="w", padx=(0, 14), pady=(6, 0))
        var = tk.StringVar()
        self.vars[key] = var
        if kind == "combo":
            w = ttk.Combobox(parent, textvariable=var, values=values or [], width=width - 2)
        else:
            w = ttk.Entry(parent, textvariable=var, width=width)
        w.grid(row=row, column=1, sticky="w", pady=(6, 0))
        err = tk.Label(parent, text="", bg=C["card"], fg=C["danger"], font=(FONT, 8), anchor="w")
        err.grid(row=row, column=2, sticky="w", padx=(10, 0), pady=(6, 0))
        self.widgets[key] = w
        self.err_labels[key] = err
        var.trace_add("write", lambda *_: self.schedule_validate())
        return var

    def _page_assignment(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=C["bg"])
        c1 = self.card(page, "Assignment")
        self.field(c1, 0, "Category", "category", "combo", CATEGORIES)
        self.field(c1, 1, "Sub-category / type of audit", "sub_category")
        self.field(c1, 2, "Form / section (tax audit)", "form_or_section")
        self.field(c1, 3, "Act / law / statute", "act_or_law")
        c2 = self.card(page, "Signing & client")
        self.field(c2, 0, "FRN (or Individual capacity)", "frn")
        self.field(c2, 1, "Signing date (DD-MM-YYYY)", "signing_date")
        self.field(c2, 2, "Client name (Guidelines s.8(b))", "client_name")
        self.field(c2, 3, "PAN of auditee", "pan")
        self.assignment_hint = tk.Label(page, text="Choose a category to see which fields apply.",
                                        bg=C["bg"], fg=C["muted"], font=(FONT, 9))
        self.assignment_hint.pack(anchor="w")
        self.vars["category"].trace_add("write", lambda *_: self._category_hint())
        return page

    def _page_attestation(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=C["bg"])
        c1 = self.card(page, "Auditor's opinion on financial statements")
        self.field(c1, 0, "Opinion applicable?", "opinion_applicable", "combo", YES_NO)
        self.field(c1, 1, "Opinion type", "opinion_type", "combo", OPINION_TYPES)
        self.field(c1, 2, "Entity type", "entity_type", "combo", ENTITY_TYPES)
        c2 = self.card(page, "Preceding year's audit (compulsory for tax audit & assurance)")
        self.field(c2, 0, "Preceding-year details applicable?", "preceding_applicable", "combo", YES_NO)
        self.field(c2, 1, "Audited last year?", "audited_last_year", "combo", PRECEDING_OPTIONS)
        self.field(c2, 2, "Previous auditor MRN / FRN", "prev_auditor")
        self.field(c2, 3, "Communicated with previous auditor?", "communication", "combo", YES_NO)
        self.field(c2, 4, "Communication date", "communication_date")
        self.field(c2, 5, "Outstanding audit fees", "outstanding_fees", "combo", FEES_OPTIONS)
        self.attest_hint = tk.Label(page, text="These details are hidden from the verifier on the portal.",
                                    bg=C["bg"], fg=C["muted"], font=(FONT, 9))
        self.attest_hint.pack(anchor="w")
        return page

    def _page_figures(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=C["bg"])
        outer = tk.Frame(page, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        outer.pack(fill="x", pady=(0, 12))
        tk.Label(outer, text="Key fields (do not disclose client details)",
                 bg=C["card"], fg=C["text"], font=(FONT, 10, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Label(outer, text="Certificates need 2+ rows; audit / assurance need 1+.",
                 bg=C["card"], fg=C["muted"], font=(FONT, 8)).pack(anchor="w", padx=16)
        self.kf_host = tk.Frame(outer, bg=C["card"])
        self.kf_host.pack(fill="x", padx=16, pady=8)
        head = tk.Frame(self.kf_host, bg=C["card"])
        head.grid(row=0, column=0, sticky="w")
        tk.Label(head, text="Particulars (≤50 chars)", bg=C["card"], fg=C["muted"],
                 font=(FONT, 8)).pack(side="left", padx=(0, 130))
        tk.Label(head, text="Figure / value", bg=C["card"], fg=C["muted"], font=(FONT, 8)).pack(side="left")
        ttk.Button(outer, text="+ Add row", command=lambda: self.add_key_row()).pack(anchor="w", padx=16, pady=(0, 12))

        c2 = self.card(page, "Document description")
        self.desc = tk.Text(c2, height=3, width=82, wrap="word", font=(FONT, 9),
                            relief="solid", bd=1, highlightthickness=0)
        self.desc.pack(anchor="w", pady=(0, 4))
        self.desc.bind("<KeyRelease>", lambda *_: self._count_desc())
        self.desc_count = tk.Label(c2, text="0 / 250", bg=C["card"], fg=C["muted"], font=(FONT, 8))
        self.desc_count.pack(anchor="w")
        rem = tk.Frame(c2, bg=C["card"])
        rem.pack(fill="x", pady=(8, 0))
        tk.Label(rem, text="Remarks (optional, hidden)", bg=C["card"], fg=C["muted"],
                 font=(FONT, 8)).pack(side="left")
        remarks_var = tk.StringVar()
        self.vars["remarks"] = remarks_var
        rem_entry = ttk.Entry(rem, textvariable=remarks_var, width=52)
        rem_entry.pack(side="left", padx=(10, 8))
        rem_err = tk.Label(rem, text="", bg=C["card"], fg=C["danger"], font=(FONT, 8))
        rem_err.pack(side="left")
        self.widgets["remarks"] = rem_entry
        self.err_labels["remarks"] = rem_err
        remarks_var.trace_add("write", lambda *_: self.schedule_validate())
        self.issues = tk.Label(page, text="", bg=C["bg"], fg=C["danger"], justify="left",
                               anchor="nw", wraplength=900, font=(FONT, 9))
        self.issues.pack(anchor="w", pady=(4, 0))
        return page

    def _page_import(self) -> tk.Frame:
        page = tk.Frame(self.page_host, bg=C["bg"])
        row = tk.Frame(page, bg=C["bg"])
        row.pack(fill="x", pady=(0, 12))

        doc = tk.Frame(row, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        doc.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(doc, text="Document", bg=C["card"], fg=C["text"],
                 font=(FONT, 11, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(doc, text="PDF / Word / Excel → extraction prefills the form (next slice).",
                 bg=C["card"], fg=C["muted"], font=(FONT, 8), wraplength=300, justify="left").pack(anchor="w", padx=16)
        self.doc_label = tk.Label(doc, text="No file selected", bg=C["card"], fg=C["muted"], font=(FONT, 9))
        self.doc_label.pack(anchor="w", padx=16, pady=(8, 4))
        ttk.Button(doc, text="Choose document…", command=self.choose_document).pack(anchor="w", padx=16, pady=(0, 14))

        batch = tk.Frame(row, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        batch.pack(side="left", fill="x", expand=True, padx=(8, 0))
        tk.Label(batch, text="Excel / CSV batch", bg=C["card"], fg=C["text"],
                 font=(FONT, 11, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(batch, text="Template rows → validate → bulk portal path (one OTP per batch).",
                 bg=C["card"], fg=C["muted"], font=(FONT, 8), wraplength=300, justify="left").pack(anchor="w", padx=16)
        self.batch_label = tk.Label(batch, text="No batch loaded", bg=C["card"], fg=C["muted"], font=(FONT, 9))
        self.batch_label.pack(anchor="w", padx=16, pady=(8, 4))
        btns = tk.Frame(batch, bg=C["card"])
        btns.pack(anchor="w", padx=16, pady=(0, 14))
        ttk.Button(btns, text="Load Excel / CSV", command=self.choose_batch).pack(side="left")
        ttk.Button(btns, text="Download CSV template", command=self.save_template).pack(side="left", padx=6)

        table_card = tk.Frame(page, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        table_card.pack(fill="both", expand=True)
        tk.Label(table_card, text="Batch preview", bg=C["card"], fg=C["text"],
                 font=(FONT, 10, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        cols = ("category", "sub_category", "client_name", "pan", "status")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", height=10)
        for col, text, width in [("category", "Category", 210), ("sub_category", "Sub-category", 230),
                                 ("client_name", "Client", 220), ("pan", "PAN", 120), ("status", "Status", 110)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", lambda *_: self.select_batch_row())
        self.tree.tag_configure("bad", foreground=C["danger"])
        self.tree.tag_configure("good", foreground=C["ok"])
        return page

    # ---------------------------------------------------------------- data
    def payload(self) -> dict:
        p = blank_payload()
        for key in ("category", "sub_category", "form_or_section", "act_or_law", "frn",
                    "signing_date", "client_name", "pan", "opinion_applicable", "opinion_type",
                    "entity_type", "preceding_applicable", "audited_last_year", "prev_auditor",
                    "communication", "communication_date", "outstanding_fees", "remarks"):
            if key in self.vars:
                p[key] = self.vars[key].get().strip()
        p["description"] = self.desc.get("1.0", "end").strip()
        fields = []
        for row in self.key_rows:
            pv, vv = row["particulars"].get().strip(), row["value"].get().strip()
            if pv or vv:
                fields.append({"particulars": pv, "value": vv})
        p["key_fields"] = fields or blank_payload()["key_fields"]
        return p

    def fill(self, p: dict) -> None:
        for key, var in self.vars.items():
            if key in p and p[key] is not None:
                var.set(str(p[key]))
        self.desc.delete("1.0", "end")
        self.desc.insert("1.0", p.get("description", "") or "")
        self._count_desc()
        rows = p.get("key_fields") or []
        while len(self.key_rows) < max(3, len(rows)):
            self.add_key_row()
        for i, row in enumerate(self.key_rows):
            row["particulars"].set(rows[i]["particulars"] if i < len(rows) else "")
            row["value"].set(rows[i]["value"] if i < len(rows) else "")
        self.schedule_validate()

    def new(self) -> None:
        for var in self.vars.values():
            var.set("")
        self.desc.delete("1.0", "end")
        self.vars["signing_date"].set(datetime.now().strftime("%d-%m-%Y"))
        self.vars["frn"].set("028145N - DHRUV DUA & CO")
        self.vars["category"].set(CATEGORIES[2])
        for row in self.key_rows:
            row["frame"].destroy()
        self.key_rows.clear()
        for _ in range(3):
            self.add_key_row()
        self._count_desc()
        self.schedule_validate()

    # ---------------------------------------------------------------- key rows
    def add_key_row(self) -> None:
        idx = len(self.key_rows)
        frame = tk.Frame(self.kf_host, bg=C["card"])
        frame.grid(row=idx + 1, column=0, sticky="w", pady=2)
        pv, vv = tk.StringVar(), tk.StringVar()
        tk.Entry(frame, textvariable=pv, width=62, font=(FONT, 9), relief="solid", bd=1).pack(side="left", padx=(0, 8))
        tk.Entry(frame, textvariable=vv, width=24, font=(FONT, 9), relief="solid", bd=1).pack(side="left")
        ttk.Button(frame, text="✕", width=3,
                   command=lambda f=frame: self.remove_key_row(f)).pack(side="left", padx=6)
        self.key_rows.append({"frame": frame, "particulars": pv, "value": vv})
        pv.trace_add("write", lambda *_: self.schedule_validate())
        vv.trace_add("write", lambda *_: self.schedule_validate())
        if len(self.key_rows) > 1:
            pass

    def remove_key_row(self, frame: tk.Frame) -> None:
        if len(self.key_rows) <= 1:
            return
        for row in list(self.key_rows):
            if row["frame"] is frame:
                row["frame"].destroy()
                self.key_rows.remove(row)
        self._regrid_keys()
        self.schedule_validate()

    def _regrid_keys(self) -> None:
        for i, row in enumerate(self.key_rows):
            row["frame"].grid_configure(row=i + 1)

    # ---------------------------------------------------------------- validation
    def schedule_validate(self, *_) -> None:
        if self._pending:
            try:
                self.root.after_cancel(self._pending)
            except Exception:
                pass
        self._pending = self.root.after(300, self.validate_now)

    def validate_now(self) -> dict:
        self._pending = None
        self.valid = validate(self.payload())
        for label in self.err_labels.values():
            label.configure(text="")
        for msg in self.valid["errors"]:
            key = error_key(msg)
            if key and key in self.err_labels:
                self.err_labels[key].configure(text=msg)
        ok = self.valid["ok"]
        self.pill.configure(text="READY" if ok else "NOT READY",
                            bg="#065f46" if ok else C["navy2"],
                            fg="#a7f3d0" if ok else "#fca5a5")
        self.prepare_btn.configure(state="normal" if ok else "disabled")
        n_e, n_w = len(self.valid["errors"]), len(self.valid["warnings"])
        self.footer_status.configure(
            text=("All checks passed" if ok else f"{n_e} error(s) · {n_w} warning(s)")
            + (f"  ·  {self.vars['client_name'].get() or 'no client'}")
        )
        side = []
        if ok:
            side.append("✓ ready to prepare")
        side += [f"• {m}" for m in self.valid["errors"][:4]]
        side += [f"! {m}" for m in self.valid["warnings"][:3]]
        self.side_errors.configure(text="\n".join(side) if side else "No checks yet",
                                   fg="#fca5a5" if not ok else "#a7f3d0")
        self.issues.configure(text=("\n".join(self.valid["errors"]) if self.valid["errors"] else ""))
        return self.valid

    # ---------------------------------------------------------------- actions
    def _category_hint(self) -> None:
        c = self.vars["category"].get()
        if c == "Tax Audit":
            self.assignment_hint.configure(text="Tax Audit: Form/Section is required; s.44AB answers are validated.")
        elif c == "Audit and Assurance Functions":
            self.assignment_hint.configure(text="Audit & Assurance: Act/Law is required; opinion and preceding-year blocks apply.")
        elif c == "Certificates and Other Reports":
            self.assignment_hint.configure(text="Certificates: 2+ key fields; form/act optional.")
        else:
            self.assignment_hint.configure(text="Choose a category to see which fields apply.")

    def _count_desc(self) -> None:
        n = len(self.desc.get("1.0", "end").strip())
        self.desc_count.configure(text=f"{n} / 250", fg=C["danger"] if n and n < 5 else C["muted"])
        self.schedule_validate()

    def show_step(self, n: int) -> None:
        for i, page in self.pages.items():
            page.pack_forget()
        self.pages[n].pack(fill="both", expand=True)
        titles = {
            1: ("Assignment", "Category, type, FRN, signing date and client identity."),
            2: ("Attestation", "Opinion and preceding-year details — hidden from verifiers."),
            3: ("Figures & description", "Key figures from the document and the portal description."),
            4: ("Import / batch", "Start from a document or an Excel/CSV batch, or fill manually."),
        }
        self.page_title.configure(text=titles[n][0])
        self.page_sub.configure(text=titles[n][1])
        for i, btn in self.step_buttons.items():
            btn.configure(style="Active.TButton" if i == n else "Step.TButton")

    def save_template(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        sample = {
            "category": "Certificates and Other Reports",
            "sub_category": "Net worth Certificates for Bank finances",
            "frn": "028145N - DHRUV DUA & CO",
            "signing_date": datetime.now().strftime("%d-%m-%Y"),
            "client_name": "Example Private Limited",
            "pan": "AAAAA0000A",
            "description": "Net worth certificate as at 31 March 2026 for bank finance.",
            "particulars_1": "Net worth",
            "value_1": "12500000",
            "particulars_2": "Turnover",
            "value_2": "40000000",
        }
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(TEMPLATE_HEADERS)
            writer.writerow([sample.get(h, "") for h in TEMPLATE_HEADERS])
        self.footer_status.configure(text=f"Template saved: {Path(path).name}")

    def save_json(self) -> None:
        if not self.validate_now()["ok"]:
            messagebox.showwarning("Validation", "Fix the errors before saving.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        Path(path).write_text(json.dumps(self.payload(), indent=2), encoding="utf-8")
        self.footer_status.configure(text=f"Saved {Path(path).name}")

    def copy_json(self) -> None:
        payload = self.payload()
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(payload, indent=2))
        self.footer_status.configure(text="Payload copied to clipboard")

    def prepare(self) -> None:
        result = self.validate_now()
        if not result["ok"]:
            messagebox.showwarning("Validation", "Fix the errors before preparing.")
            return
        import os
        import subprocess

        app_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "UDINApp"
        app_dir.mkdir(parents=True, exist_ok=True)
        pending = app_dir / "pending_payload.json"
        pending.write_text(json.dumps(self.payload(), indent=2), encoding="utf-8")
        assistant = Path(__file__).with_name("udin_app.py")
        subprocess.Popen(
            [sys.executable, str(assistant), "--ui", "--payload", str(pending)],
            cwd=str(Path(__file__).parent),
        )
        self.footer_status.configure(text="UDIN Assistant opened — log in, then review the prefilled form")
        messagebox.showinfo(
            "Preparing in portal",
            "The UDIN Assistant is opening.\n\n"
            "1. Log in with your CAPTCHA and OTP.\n"
            "2. The Generate UDIN form is prefilled from this payload.\n"
            "3. Review it in the browser; complete the fields the assistant reports as skipped.\n"
            "4. Send OTP only when you are satisfied.",
        )

    def choose_document(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose document",
            filetypes=[("Documents", "*.pdf *.docx *.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        self.doc_path = Path(path)
        self.doc_label.configure(text=self.doc_path.name, fg=C["text"])
        if self.doc_path.suffix.lower() in (".xlsx", ".xls"):
            try:
                rows = load_batch(str(self.doc_path))
                if rows:
                    self.batch = rows
                    self._render_batch()
            except Exception:
                pass
        self.footer_status.configure(text="Document selected — extraction arrives in the next slice")

    def choose_batch(self) -> None:
        path = filedialog.askopenfilename(
            title="Load UDIN batch",
            filetypes=[("Excel/CSV", "*.xlsx *.csv"), ("All files", "*.*")],
        )
        if path:
            self.load_batch(path)

    def load_batch(self, path: str) -> None:
        try:
            rows = load_batch(path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Load failed", str(exc))
            return
        if not rows:
            messagebox.showwarning("Empty", "No data rows found.")
            return
        self.batch = rows
        self.batch_label.configure(text=f"{Path(path).name} — {len(rows)} row(s)", fg=C["text"])
        self._render_batch()
        self.show_step(4)
        self.fill(rows[0])
        self.show_step(2)
        self.footer_status.configure(text=f"Loaded {len(rows)} row(s); edit and validate")

    def _render_batch(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.batch):
            res = validate(row)
            status = "Valid" if res["ok"] else f"{len(res['errors'])} error(s)"
            self.tree.insert("", "end", iid=str(i), values=(
                row.get("category", ""), row.get("sub_category", ""),
                row.get("client_name", ""), row.get("pan", ""), status),
                tags=("good" if res["ok"] else "bad",))

    def select_batch_row(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self.fill(self.batch[int(sel[0])])
        self.show_step(2)
        self.footer_status.configure(text=f"Row {int(sel[0]) + 1} loaded — edit and validate")

    # ---------------------------------------------------------------- shortcuts
    def _bind_keys(self) -> None:
        self.root.bind("<Control-Return>", lambda *_: self.validate_now())
        self.root.bind("<Control-s>", lambda *_: self.save_json())
        self.root.bind("<Control-Key-1>", lambda *_: self.show_step(1))
        self.root.bind("<Control-Key-2>", lambda *_: self.show_step(2))
        self.root.bind("<Control-Key-3>", lambda *_: self.show_step(3))
        self.root.bind("<Control-Key-4>", lambda *_: self.show_step(4))


def run(initial_file: str | None = None) -> int:
    root = tk.Tk()
    App(root, initial_file)
    root.mainloop()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None)
    args = ap.parse_args()
    raise SystemExit(run(args.file))
