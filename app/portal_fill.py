"""Payload → official UDIN portal form, over CDP.

Best-effort filler: category, FRN, type/form, act, signing date, PAN, description,
remarks and the corporate key figures. Opinion/preceding/denomination/FY blocks are
reported as "skipped" for the member to complete in the visible browser.

Used by udin_app.py when launched with --payload.
"""

from __future__ import annotations

import asyncio
import json

GENERATE_URL = "https://udin.icai.org/ICAI/generateUDIN"


async def eval_js(cdp, expression: str):
    res = await cdp.send(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    if "exceptionDetails" in res:
        raise RuntimeError(str(res["exceptionDetails"])[:300])
    return res.get("result", {}).get("value")


async def click_at(cdp, x: float, y: float) -> None:
    await cdp.send("Input.dispatchMouseEvent",
                   {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1})
    await cdp.send("Input.dispatchMouseEvent",
                   {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1})


async def _center(cdp, selector: str):
    js = """(() => {
      const el = document.querySelector(%s);
      if (!el) return null;
      el.scrollIntoView({ block: 'center' });
      const b = el.getBoundingClientRect();
      return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
    })()""" % json.dumps(selector)
    return await eval_js(cdp, js)


async def set_value(cdp, selector: str, value: str) -> bool:
    js = """(() => {
      const el = document.querySelector(%s);
      if (!el) return false;
      const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, %s);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    })()""" % (json.dumps(selector), json.dumps(value))
    return bool(await eval_js(cdp, js))


async def ng_select(cdp, input_id: str, text: str) -> bool:
    """Open an ng-select, type the option text, pick the matching option."""
    pos = await eval_js(cdp, """(() => {
      const el = document.getElementById(%s);
      if (!el) return null;
      el.scrollIntoView({ block: 'center' });
      const c = (el.closest('ng-select') || el.parentElement).querySelector('.ng-select-container')
        || el.closest('ng-select') || el;
      const b = c.getBoundingClientRect();
      return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
    })()""" % json.dumps(input_id))
    if not pos:
        return False
    await click_at(cdp, pos["x"], pos["y"])
    await asyncio.sleep(0.5)
    await cdp.send("Input.insertText", {"text": text})
    await asyncio.sleep(0.8)
    match = await eval_js(cdp, """(() => {
      const opts = [...document.querySelectorAll('.ng-option')];
      const hit = opts.find(o => (o.innerText || '').toLowerCase().includes(%s.toLowerCase()));
      if (!hit) return null;
      const b = hit.getBoundingClientRect();
      return { x: b.x + b.width / 2, y: b.y + b.height / 2, text: hit.innerText.trim() };
    })()""" % json.dumps(text))
    if match:
        await click_at(cdp, match["x"], match["y"])
    else:
        await cdp.send("Input.dispatchKeyEvent",
                       {"type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
        await cdp.send("Input.dispatchKeyEvent",
                       {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13})
    await asyncio.sleep(0.8)
    return True


async def fill_generation(cdp, payload: dict) -> dict:
    """Fill the Generate UDIN form from a validated payload. Never submits."""
    filled: list[str] = []
    skipped: list[str] = []

    category = payload.get("category") or "Audit and Assurance Functions"
    clicked = await eval_js(cdp, """(() => {
      const cat = %s;
      const label = [...document.querySelectorAll('label')]
        .find(l => (l.innerText || '').trim().toLowerCase().startsWith(cat.toLowerCase()));
      if (!label) return false;
      label.click();
      return true;
    })()""" % json.dumps(category))
    if clicked:
        filled.append("category")
    await asyncio.sleep(1.4)

    if payload.get("frn"):
        if await ng_select(cdp, "FRN", payload["frn"]):
            filled.append("FRN")
        else:
            skipped.append("FRN")
    if payload.get("sub_category"):
        if await ng_select(cdp, "certficateType", payload["sub_category"]):
            filled.append("type")
        else:
            skipped.append("type")
        await asyncio.sleep(1.0)
    if payload.get("act_or_law"):
        if await ng_select(cdp, "certificateSubType", payload["act_or_law"]):
            filled.append("act")
        else:
            skipped.append("act")
        await asyncio.sleep(0.8)

    if payload.get("signing_date") and await set_value(cdp, "#mat-input-1", payload["signing_date"]):
        filled.append("signing date")
    else:
        skipped.append("signing date")

    pan_ok = await eval_js(cdp, """(() => {
      const el = [...document.querySelectorAll('input')]
        .find(i => (i.getAttribute('placeholder') || '').toLowerCase().includes('pan of the assessee'));
      if (!el) return false;
      const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      set.call(el, %s);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    })()""" % json.dumps(payload.get("pan", "")))
    (filled if pan_ok else skipped).append("PAN of auditee")

    if payload.get("description"):
        if await set_value(cdp, "#mat-input-2", payload["description"]):
            filled.append("description")
        else:
            skipped.append("description")
    if payload.get("remarks"):
        if await set_value(cdp, "#mat-input-3", payload["remarks"]):
            filled.append("remarks")

    # Corporate audit key figures: three "Figures in INR" inputs after the FY/PAN rows.
    if category == "Audit and Assurance Functions":
        values = []
        for row in payload.get("key_fields", []):
            label = (row.get("particulars") or "").lower()
            val = str(row.get("value") or "").strip()
            if not val:
                continue
            idx = None
            if "turnover" in label or "revenue" in label or "receipt" in label:
                idx = 0
            elif "shareholder" in label or "net worth" in label or "equity" in label or "fund" in label:
                idx = 1
            elif "net block" in label or "fixed asset" in label or "ppe" in label:
                idx = 2
            if idx is not None and idx not in [v[0] for v in values]:
                values.append((idx, val))
        for idx, val in values:
            ok = await eval_js(cdp, """(() => {
              const inputs = [...document.querySelectorAll('input[placeholder="Figures in INR"]')]
                .filter(i => i.getBoundingClientRect().width > 0);
              const el = inputs[%d];
              if (!el) return false;
              Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, %s);
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              el.dispatchEvent(new Event('blur', { bubbles: true }));
              return true;
            })()""" % (idx, json.dumps(val)))
            if ok:
                filled.append(f"figure {idx + 1}")
            else:
                skipped.append(f"figure {idx + 1}")

    skipped += [
        "auditor's opinion block",
        "preceding-year block",
        "denomination selects",
        "financial-year dates (if shown)",
        "remaining mandatory rows — review in the browser",
    ]
    return {"filled": filled, "skipped": skipped, "url": await eval_js(cdp, "location.href")}
