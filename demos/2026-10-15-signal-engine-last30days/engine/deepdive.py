from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from engine.config import Settings
from engine.page import DigestPage

_SEARCH = "reddit,hackernews,polymarket,github"
_RELATIVE_SCRIPT = "skills/last30days/scripts/last30days.py"


def command_for(topic: str, checkout: Path | None) -> str:
    if checkout is not None and checkout.is_dir():
        script = f"{checkout}/{_RELATIVE_SCRIPT}"
    else:
        script = _RELATIVE_SCRIPT
    return (
        "env -u LAST30DAYS_HOST python3 "
        + shlex.quote(script)
        + " "
        + shlex.quote(topic)
        + " --search "
        + _SEARCH
    )


def run_or_print(settings: Settings, page: DigestPage, demo: Path) -> int:
    if not page.items:
        print("no item 1", flush=True)
        return 0
    topic = page.items[0].title
    checkout = settings.last30days_checkout
    print(command_for(topic, checkout), flush=True)
    if checkout is not None and checkout.is_dir():
        script = checkout / "skills" / "last30days" / "scripts" / "last30days.py"
        cwd = checkout
    else:
        script = demo / "skills" / "last30days" / "scripts" / "last30days.py"
        cwd = demo
    if not script.is_file():
        return 0
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ}
    try:
        completed = subprocess.run(
            [sys.executable, str(script), topic, "--search", _SEARCH],
            cwd=cwd,
            env=env,
            check=False,
        )
    except OSError:
        return 0
    return completed.returncode
