# UDIN Desktop App (proof-of-slice)

A local Python desktop app that drives the official UDIN portal in a real Chrome
instance over the DevTools Protocol. It fills credentials and the login form for
you, extracts and displays the **CAPTCHA image**, and pauses for **OTP**. No
HTTP replay, no CAPTCHA solving, no hidden automation.

```text
app/
  udin_app.py        login engine + Tkinter UI (CAPTCHA/OTP panels)
  form_ui.py         validated manual form (all UDIN fields, load Excel, save JSON)
  udin_model.py      canonical payload + validation + XLSX/CSV batch reader (stdlib)
  make_template.py   generates the Excel batch template (needs openpyxl)
  templates/         udin_batch_template.xlsx
  test_model.py      validation self-test
  requirements.txt   websockets, Pillow, pywin32 (already installed on this machine)
```

## Run

```powershell
# prove Chrome + CDP + CAPTCHA extraction work (headless; saves CAPTCHA + screenshot)
python app\udin_app.py --selftest

# same, with a visible browser
python app\udin_app.py --selftest --headed

# desktop UI (real Chrome window + in-app CAPTCHA/OTP panels)
python app\udin_app.py --ui

# validated manual form (all required fields, validation, load Excel/CSV, save JSON)
python app\form_ui.py
python app\form_ui.py --file app\templates\udin_batch_template.xlsx

# validation engine self-test
python app\test_model.py

# assistant with a prepared payload (what "Prepare in portal" launches)
python app\udin_app.py --ui --payload "%LOCALAPPDATA%\UDINApp\pending_payload.json"
```

Outputs (never inside the repo):

```text
%LOCALAPPDATA%\UDINApp\
  chrome-profile\        persistent browser profile (session reuse)
  vault.json             DPAPI-encrypted username/password
  logs\*.jsonl           HAR-like request/response record (observability only)
  out\captcha-*.png      extracted CAPTCHA images
  out\login-selftest.png login page screenshot
```

## What works today

- launches Chrome/Edge with a dedicated profile and remote debugging;
- connects over WebSocket CDP, enables `Page`/`Network`, records HAR-like JSONL;
- opens `https://udin.icai.org/ICAI/login`;
- fills `#username` / `#password` from the app (DPAPI vault for "remember");
- extracts the live CAPTCHA `<img alt="CAPTCHA">` and shows it in the Tkinter panel;
- submits the CAPTCHA + LOGIN, detects dashboard / OTP / error state;
- OTP panel and submit path;
- self-test verified 28 Oct 2026: login page loaded, CAPTCHA PNG extracted (≈3 KB), form IDs confirmed;
- canonical UDIN payload + validator (`udin_model.py`): PAN, dates/60-day, description charset, opinion and preceding-year blocks, key-field minimums, s.44AB warnings;
- Excel batch template + stdlib XLSX/CSV reader: rows → payloads → same validator;
- validated manual form (`form_ui.py`): four-step workbench, adaptive fields, live inline validation, Excel/CSV batch table, JSON export — starts cleanly;
- **Prepare in portal**: saves the validated payload and launches the assistant with `--payload`; after login the assistant fills the Generate UDIN form (category, FRN, type, act, signing date, PAN, description, remarks, corporate figures) and reports the blocks left for manual completion.

## Not built yet (next slices)

- complete the remaining portal blocks automatically: auditor's-opinion subfields, preceding-year block, denomination selects, FY dates;
- Save Draft → Preview → Send OTP → capture UDIN/QR, then stamp and register;
- document → UDIN JSON extraction (local parse + OCR/vision + DeepSeek) that prefills the form;
- batch submission through the portal's bulk path (3–300 certificates; 3–10 tax/audit);
- stamping before DSC, register, deadlines, e-filing validation;
- packaging (PyInstaller) and signed installer.

## Security

- Credentials: Windows DPAPI, per Windows user, never in argv/logs/repo.
- OTP: memory only; never persisted or logged.
- Dedicated Chrome profile holds session cookies — BitLocker on the machine is a prerequisite.
- CAPTCHA is read by the human and typed in; the app never OCRs or auto-solves it.
- The portal's OTP goes to the member's registered mobile + email; the app only accepts it.

## Requirements

Python 3.11+ with `websockets>=14`, `Pillow`, `pywin32`; Chrome or Edge installed.
No Playwright/Selenium and no `pip install` needed on this machine — but
`requirements.txt` is provided for clean installs.

See [`../docs/APP-ARCHITECTURE.md`](../docs/APP-ARCHITECTURE.md) for the design,
state machine, build slices and the reason HAR is recorded but never replayed, and
[`../docs/INPUT-MODES.md`](../docs/INPUT-MODES.md) for the document / form / Excel
input modes and the validation matrix.
