"""Vendor Chrome for Testing into %LOCALAPPDATA%\\UDINApp\\browser.

One-time download so the app does not depend on a machine-installed Chrome.
Run:  python app/get_chromium.py

After it finishes, udin_app.py picks the bundled browser automatically (it is
first in CHROME_CANDIDATES), and the app becomes self-sufficient on a clean PC.
"""

from __future__ import annotations

import json
import os
import urllib.request
import zipfile
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "UDINApp"
DEST = APP_DIR / "browser"
INDEX = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"


def main() -> int:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    data = json.load(urllib.request.urlopen(INDEX, timeout=60))
    stable = data["channels"]["Stable"]
    version = stable["version"]
    downloads = [d for d in stable["downloads"]["chrome"] if d["platform"] == "win64"]
    if not downloads:
        raise SystemExit("no win64 Chrome-for-Testing download found")
    url = downloads[0]["url"]
    archive = APP_DIR / f"chrome-win64-{version}.zip"
    print(f"Chrome for Testing {version}")
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, archive)
    print(f"downloaded {archive} ({archive.stat().st_size / 1e6:.1f} MB)")
    DEST.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(DEST)
    exe = DEST / "chrome-win64" / "chrome.exe"
    print(f"ready: {exe}" if exe.exists() else "extracted, but chrome.exe not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
