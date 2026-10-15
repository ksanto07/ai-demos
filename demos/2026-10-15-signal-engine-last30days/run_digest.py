from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from engine.config import load_dotenv, load_settings
from engine.page import DigestPage, render, write_atomic
from engine.select import collect_and_select


def _day(argv: list[str] | None) -> date:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args(argv)
    if args.date is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(args.date)


def main(argv: list[str] | None = None) -> int:
    demo = Path(__file__).resolve().parent
    load_dotenv(demo / ".env")
    try:
        settings = load_settings(demo / "config.json")
        day = _day(argv)
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc)
    key = os.environ.get("XAI_API_KEY", "").strip() or None
    selected = collect_and_select(settings, now, key)
    path = demo / "digests" / f"{day.isoformat()}.md"
    write_atomic(path, render(DigestPage(day, selected)))
    print(path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
