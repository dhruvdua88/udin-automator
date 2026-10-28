#!/usr/bin/env python3
"""
UDIN Desktop Assistant — proof-of-slice.

Design: a local desktop app that owns a real Chrome instance over the DevTools
Protocol (CDP). It fills the official portal with JavaScript/DOM events, records
network traffic as a HAR-like JSONL for observability (never replays it), and
surfaces exactly two human gates: the CAPTCHA image and the OTP.

Commands:
  python udin_app.py --selftest [--headed]   launch Chrome, open the login page,
                                             dump fields, save the CAPTCHA + screenshot
  python udin_app.py --ui                    Tkinter desktop UI

Requirements (already present on this machine): websockets>=14, Pillow, pywin32.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "UDINApp"
PROFILE_DIR = APP_DIR / "chrome-profile"
LOG_DIR = APP_DIR / "logs"
OUT_DIR = APP_DIR / "out"

LOGIN_URL = "https://udin.icai.org/ICAI/login"
DEFAULT_PORT = 9333

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

VAULT_PATH = APP_DIR / "vault.json"


def ensure_dirs() -> None:
    for d in (APP_DIR, PROFILE_DIR, LOG_DIR, OUT_DIR):
        d.mkdir(parents=True, exist_ok=True)


def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise RuntimeError("Chrome/Edge not found")


# --------------------------------------------------------------------------- #
# Credential vault (Windows DPAPI, per-user)
# --------------------------------------------------------------------------- #
def vault_save(key: str, value: str) -> None:
    import win32crypt

    blob = win32crypt.CryptProtectData(value.encode("utf-8"), key, None, None, None, 0)
    data = {}
    if VAULT_PATH.exists():
        try:
            data = json.loads(VAULT_PATH.read_text())
        except Exception:
            data = {}
    data[key] = base64.b64encode(blob).decode("ascii")
    VAULT_PATH.write_text(json.dumps(data))


def vault_load(key: str) -> str | None:
    import win32crypt

    if not VAULT_PATH.exists():
        return None
    try:
        data = json.loads(VAULT_PATH.read_text())
        blob = base64.b64decode(data[key])
        return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode("utf-8")
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Chrome + CDP
# --------------------------------------------------------------------------- #
class ChromeSession:
    def __init__(self, port: int = DEFAULT_PORT, headless: bool = True):
        self.port = port
        self.headless = headless
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        ensure_dirs()
        args = [
            find_browser(),
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={PROFILE_DIR}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-sync",
            "--window-size=1366,900",
            "about:blank",
        ]
        if self.headless:
            args.insert(1, "--headless=new")
        self.proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.time() + 25
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=1)
                return
            except Exception:
                time.sleep(0.4)
        raise RuntimeError("Chrome DevTools endpoint did not come up")

    def page_ws(self) -> str:
        targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=5).read())
        pages = [t for t in targets if t.get("type") == "page"]
        if not pages:
            raise RuntimeError("no page target")
        return pages[0]["webSocketDebuggerUrl"]

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass


class CDP:
    """Minimal CDP client. Sends commands, routes events to a JSONL recorder."""

    def __init__(self, ws_url: str, har_path: Path | None = None):
        self.ws_url = ws_url
        self.har_path = har_path
        self._id = 0
        self._ws = None
        self._har = None

    async def __aenter__(self) -> "CDP":
        from websockets.asyncio.client import connect

        self._ws = await connect(self.ws_url, max_size=64 * 1024 * 1024, ping_interval=None)
        if self.har_path:
            self._har = open(self.har_path, "a", encoding="utf-8")
        return self

    async def __aexit__(self, *exc) -> None:
        if self._har:
            self._har.close()
        if self._ws:
            await self._ws.close()

    async def send(self, method: str, params: dict | None = None, timeout: float = 45.0):
        assert self._ws is not None
        self._id += 1
        mid = self._id
        await self._ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            raw = await asyncio.wait_for(self._ws.recv(), timeout)
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
            self._event(msg)

    def _event(self, msg: dict) -> None:
        if not self._har:
            return
        method = msg.get("method", "")
        if not method.startswith("Network."):
            return
        p = msg.get("params", {})
        rec = {"ts": round(time.time(), 3), "event": method}
        if method == "Network.requestWillBeSent":
            req = p.get("request", {})
            rec.update({"url": req.get("url"), "method": req.get("method")})
        elif method == "Network.responseReceived":
            resp = p.get("response", {})
            rec.update({"url": resp.get("url"), "status": resp.get("status"), "mime": resp.get("mimeType")})
        else:
            return
        self._har.write(json.dumps(rec) + "\n")
        self._har.flush()


# --------------------------------------------------------------------------- #
# Portal operations (all via in-page JavaScript; no HTTP replay)
# --------------------------------------------------------------------------- #
async def evaluate(cdp: CDP, expression: str):
    res = await cdp.send(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    if "exceptionDetails" in res:
        raise RuntimeError(str(res["exceptionDetails"])[:400])
    return res.get("result", {}).get("value")


async def navigate(cdp: CDP, url: str, settle: float = 2.5) -> None:
    await cdp.send("Page.navigate", {"url": url})
    deadline = time.time() + 25
    while time.time() < deadline:
        try:
            state = await evaluate(cdp, "document.readyState")
            if state == "complete":
                break
        except Exception:
            pass
        await asyncio.sleep(0.3)
    await asyncio.sleep(settle)  # let the Angular view render


async def body_text(cdp: CDP) -> str:
    return (await evaluate(cdp, "document.body ? document.body.innerText : ''")) or ""


async def dump_fields(cdp: CDP):
    return await evaluate(
        cdp,
        """[...document.querySelectorAll('input,textarea,select,button')].map((el) => ({
             tag: el.tagName, type: el.type || '', id: el.id || '',
             placeholder: el.placeholder || '', name: el.name || '',
             text: (el.innerText || '').trim().slice(0, 40)
           }))""",
    )


async def fill_login(cdp: CDP, username: str, password: str) -> dict:
    js = """(() => {
      const set = (el, v) => {
        const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      const u = document.querySelector('input[placeholder="<MRN>@icai.org"]');
      const p = document.querySelector('input[placeholder="Please Enter Password"]');
      if (!u || !p) return { ok: false, reason: 'login fields not found' };
      set(u, %s); set(p, %s);
      return { ok: true };
    })()""" % (json.dumps(username), json.dumps(password))
    return await evaluate(cdp, js)


async def captcha_png(cdp: CDP) -> bytes | None:
    src = await evaluate(cdp, """document.querySelector('img[alt="CAPTCHA"]')?.src || null""")
    if not src or not src.startswith("data:image/png;base64,"):
        return None
    return base64.b64decode(src.split(",", 1)[1])


async def fill_captcha_and_login(cdp: CDP, captcha: str) -> dict:
    js = """(() => {
      const set = (el, v) => {
        const proto = HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      const inputs = [...document.querySelectorAll('input')];
      const captchaInput = inputs.find((i) => (i.placeholder || '').toUpperCase().includes('CAPTCHA'))
        || inputs.find((i) => (i.id || '').toLowerCase().includes('captcha'));
      if (!captchaInput) return { ok: false, reason: 'captcha input not found' };
      set(captchaInput, %s);
      const btn = [...document.querySelectorAll('button')].find((b) => /^\\s*LOGIN\\s*$/i.test(b.innerText));
      if (!btn) return { ok: false, reason: 'LOGIN button not found' };
      btn.click();
      return { ok: true };
    })()""" % json.dumps(captcha)
    return await evaluate(cdp, js)


async def fill_otp_and_submit(cdp: CDP, otp: str) -> dict:
    js = """(() => {
      const set = (el, v) => {
        const proto = HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      const inputs = [...document.querySelectorAll('input')];
      const otpInput = inputs.find((i) => (i.placeholder || '').toLowerCase().includes('otp'))
        || inputs.find((i) => (i.id || '').toLowerCase().includes('otp'));
      if (!otpInput) return { ok: false, reason: 'OTP input not found' };
      set(otpInput, %s);
      const btn = [...document.querySelectorAll('button')].find((b) => /verify|submit|continue/i.test(b.innerText));
      if (btn) btn.click();
      return { ok: true };
    })()""" % json.dumps(otp)
    return await evaluate(cdp, js)


async def detect_state(cdp: CDP) -> str:
    text = (await body_text(cdp)).lower()
    if "membership registration number" in text and "generate udin" in text:
        return "dashboard"
    if "otp" in text and ("verify" in text or "enter" in text or "resend" in text):
        return "otp"
    if any(w in text for w in ("invalid captcha", "incorrect", "wrong", "captcha is not valid")):
        return "error"
    return "unknown"


# --------------------------------------------------------------------------- #
# Self-test: prove Chrome + CDP + CAPTCHA extraction work
# --------------------------------------------------------------------------- #
async def selftest(headless: bool = True) -> int:
    ensure_dirs()
    session = ChromeSession(headless=headless)
    har = LOG_DIR / f"selftest-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    summary: dict = {}
    try:
        session.start()
        ws = session.page_ws()
        async with CDP(ws, har) as cdp:
            await cdp.send("Page.enable")
            await cdp.send("Network.enable")
            await navigate(cdp, LOGIN_URL)
            summary["url"] = await evaluate(cdp, "location.href")
            summary["title"] = await evaluate(cdp, "document.title")
            summary["captchaPng"] = None
            png = None
            for _ in range(30):
                png = await captcha_png(cdp)
                if png:
                    break
                await asyncio.sleep(0.5)
            summary["fields"] = await dump_fields(cdp)
            if png:
                path = OUT_DIR / "captcha-selftest.png"
                path.write_bytes(png)
                summary["captchaPng"] = {"path": str(path), "bytes": len(png)}
            shot = await cdp.send("Page.captureScreenshot", {"format": "png"})
            shot_path = OUT_DIR / "login-selftest.png"
            shot_path.write_bytes(base64.b64decode(shot["data"]))
            summary["screenshot"] = str(shot_path)
            summary["bodyHead"] = (await body_text(cdp))[:400]
    finally:
        session.stop()
    print(json.dumps(summary, indent=1))
    return 0 if summary.get("captchaPng") else 1


# --------------------------------------------------------------------------- #
# Tkinter desktop UI
# --------------------------------------------------------------------------- #
def run_ui() -> int:
    import tkinter as tk
    from tkinter import messagebox, ttk

    from PIL import Image, ImageTk

    ensure_dirs()
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    session = ChromeSession(headless=False)
    cdp_holder: dict = {}
    running: dict = {"chrome": False}

    def submit(coro):
        return asyncio.run_coroutine_threadsafe(coro, loop)

    root = tk.Tk()
    root.title("UDIN Assistant")
    root.geometry("760x640")

    status = tk.StringVar(value="Starting Chrome…")
    ttk.Label(root, textvariable=status, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

    frm = ttk.Frame(root)
    frm.pack(fill="x", padx=12)
    ttk.Label(frm, text="Username").grid(row=0, column=0, sticky="w")
    user_var = tk.StringVar(value=vault_load("username") or "")
    ttk.Entry(frm, textvariable=user_var, width=34).grid(row=0, column=1, sticky="w", padx=6)
    ttk.Label(frm, text="Password").grid(row=1, column=0, sticky="w")
    pass_var = tk.StringVar(value=vault_load("password") or "")
    ttk.Entry(frm, textvariable=pass_var, show="*", width=34).grid(row=1, column=1, sticky="w", padx=6)
    remember = tk.BooleanVar(value=True)
    ttk.Checkbutton(frm, text="Remember (DPAPI)", variable=remember).grid(row=1, column=2, sticky="w")

    captcha_frame = ttk.LabelFrame(root, text="CAPTCHA (type what you see)")
    captcha_frame.pack(fill="x", padx=12, pady=8)
    captcha_img_label = ttk.Label(captcha_frame)
    captcha_img_label.pack(side="left", padx=8, pady=6)
    cap_var = tk.StringVar()
    ttk.Entry(captcha_frame, textvariable=cap_var, width=18).pack(side="left", padx=6)
    captcha_btn = ttk.Button(captcha_frame, text="Submit CAPTCHA", state="disabled")
    captcha_btn.pack(side="left", padx=6)

    otp_frame = ttk.LabelFrame(root, text="OTP (sent to your mobile + email)")
    otp_frame.pack(fill="x", padx=12, pady=8)
    otp_var = tk.StringVar()
    ttk.Entry(otp_frame, textvariable=otp_var, width=18).pack(side="left", padx=8, pady=6)
    otp_btn = ttk.Button(otp_frame, text="Submit OTP")
    otp_btn.pack(side="left", padx=6)
    otp_frame.pack_forget()

    log = tk.Text(root, height=16, wrap="word")
    log.pack(fill="both", expand=True, padx=12, pady=8)

    def say(msg: str):
        log.insert("end", time.strftime("%H:%M:%S ") + msg + "\n")
        log.see("end")

    def set_status(msg: str):
        status.set(msg)

    def ensure_chrome():
        if running["chrome"]:
            return cdp_holder.get("cdp")
        session.start()
        running["chrome"] = True
        return session.page_ws()

    async def open_login():
        ws = ensure_chrome()
        cdp = await CDP(ws, LOG_DIR / f"ui-{time.strftime('%Y%m%d')}.jsonl").__aenter__()
        cdp_holder["cdp"] = cdp
        await cdp.send("Page.enable")
        await cdp.send("Network.enable")
        await navigate(cdp, LOGIN_URL)
        say("Login page loaded")
        return cdp

    def do_start():
        async def run():
            try:
                cdp = await open_login()
                user = user_var.get().strip()
                pw = pass_var.get()
                if user and pw:
                    await fill_login(cdp, user, pw)
                    if remember.get():
                        vault_save("username", user)
                        vault_save("password", pw)
                    say("Credentials filled from the app")
                png = await captcha_png(cdp)
                if not png:
                    set_status("CAPTCHA not found — is the login page loaded?")
                    return
                path = OUT_DIR / "captcha-ui.png"
                path.write_bytes(png)
                img = Image.open(path)
                root.after(0, lambda: show_captcha(img))
                set_status("CAPTCHA ready — type it and submit")
            except Exception as e:
                say(f"start failed: {e}")
                set_status("Error — see log")

        submit(run())

    def show_captcha(img):
        photo = ImageTk.PhotoImage(img)
        captcha_img_label.configure(image=photo)
        captcha_img_label.image = photo
        captcha_btn.configure(state="normal")

    def do_captcha():
        captcha = cap_var.get().strip()
        if not captcha:
            return
        captcha_btn.configure(state="disabled")
        set_status("Submitting CAPTCHA…")

        async def run():
            cdp = cdp_holder.get("cdp")
            if not cdp:
                say("not connected")
                return
            res = await fill_captcha_and_login(cdp, captcha)
            if not res.get("ok"):
                say(f"captcha submit failed: {res}")
                return
            await asyncio.sleep(3.5)
            state = await detect_state(cdp)
            say(f"state after login: {state}")
            if state == "dashboard":
                set_status("Logged in — backend session is live")
            elif state == "otp":
                root.after(0, lambda: otp_frame.pack(fill="x", padx=12, pady=8))
                set_status("OTP required — enter the OTP")
            elif state == "error":
                txt = (await body_text(cdp))[:300]
                say("error text: " + txt)
                set_status("Login error — see log")
            else:
                set_status("Unknown state — see log")

        submit(run())

    def do_otp():
        otp = otp_var.get().strip()
        if not otp:
            return
        set_status("Submitting OTP…")

        async def run():
            cdp = cdp_holder.get("cdp")
            if not cdp:
                return
            await fill_otp_and_submit(cdp, otp)
            await asyncio.sleep(3)
            state = await detect_state(cdp)
            say(f"state after OTP: {state}")
            set_status("Logged in" if state == "dashboard" else "Check the browser window")

        submit(run())

    captcha_btn.configure(command=do_captcha)
    otp_btn.configure(command=do_otp)

    btns = ttk.Frame(root)
    btns.pack(fill="x", padx=12)
    ttk.Button(btns, text="Start / Login", command=do_start).pack(side="left")
    ttk.Button(btns, text="Quit", command=lambda: (session.stop(), root.destroy())).pack(side="left", padx=8)

    root.after(300, do_start)
    root.mainloop()
    try:
        loop.call_soon_threadsafe(loop.stop)
    except Exception:
        pass
    session.stop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="UDIN desktop assistant (proof-of-slice)")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--headed", action="store_true", help="show Chrome in selftest")
    parser.add_argument("--ui", action="store_true", help="open the desktop UI")
    args = parser.parse_args()
    if args.selftest:
        return asyncio.run(selftest(headless=not args.headed))
    if args.ui:
        return run_ui()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
