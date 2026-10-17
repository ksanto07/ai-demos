from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from engine.config import load_settings
from engine.deepdive import run_or_print
from engine.page import parse


def _day(argv: list[str] | None) -> date:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args(argv)
    if args.date is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(args.date)


def main(argv: list[str] | None = None) -> int:
    demo = Path(__file__).resolve().parent
    try:
        settings = load_settings(demo / "config.json")
        day = _day(argv)
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    path = demo / "digests" / f"{day.isoformat()}.md"
    try:
        page = parse(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(exc, flush=True)
        print("run python3 run_digest.py first", flush=True)
        return 0
    return run_or_print(settings, page, demo)


if __name__ == "__main__":
    raise SystemExit(main())
