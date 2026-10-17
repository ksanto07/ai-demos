"""One live command: digest, the HTML page, then last30days on item 1.

This does not rewrite program output. It runs the three steps and leaves
their stdout and stderr on the terminal.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from render_html import main as render_main
from run_deepdive import main as deepdive_main
from run_digest import main as digest_main

_TRACE_HOLD = 2.5
_PAGE_HOLD = 3.0
_RESULT_HOLD = 3.0


def _mark(name: str) -> None:
    path = os.environ.get("SIGNAL_MARKS", "").strip()
    if path == "":
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{time.time():.3f} {name}\n")


def _chrome(html: Path) -> subprocess.Popen[bytes]:
    profile = tempfile.mkdtemp(prefix="signal-chrome-")
    return subprocess.Popen(
        [
            "google-chrome",
            "--kiosk",
            "--app=file://" + str(html),
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--hide-scrollbars",
            "--disable-extensions",
            "--disable-translate",
            "--disable-features=TranslateUI,InfiniteSessionRestore",
            "--window-position=0,0",
            "--window-size=1920,1080",
            "--force-device-scale-factor=1",
            "--disable-session-crashed-bubble",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _page_visible(day: str) -> bool:
    found = subprocess.run(
        ["xdotool", "search", "--name", f"Signal {day}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return found.stdout.strip() != ""


def _stop(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except OSError:
        return
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass


def main() -> int:
    demo = Path(__file__).resolve().parent
    day = datetime.now(timezone.utc).date().isoformat()
    args = ["--date", day]
    code = digest_main(args)
    if code != 0:
        return code
    code = render_main(args)
    if code != 0:
        return code
    _mark("trace")
    time.sleep(_TRACE_HOLD)
    _mark("page-open")
    chrome = _chrome(demo / "digests" / f"{day}.html")
    deadline = time.time() + 8
    while time.time() < deadline and not _page_visible(day):
        time.sleep(0.05)
    _mark("page")
    time.sleep(_PAGE_HOLD)
    _stop(chrome)
    _mark("page-close")
    code = deepdive_main(args)
    _mark("result")
    time.sleep(_RESULT_HOLD)
    _mark("done")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
