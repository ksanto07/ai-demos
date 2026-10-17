from __future__ import annotations

import argparse
import html
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from engine.page import parse

_SOURCE = {"github": "GitHub", "hn": "Hacker News", "youtube": "YouTube"}


def _day(argv: list[str] | None) -> date:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    args = parser.parse_args(argv)
    if args.date is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(args.date)


def _meta(source: str, origin: str, published: datetime) -> str:
    label = _SOURCE[source]
    when = published.astimezone(timezone.utc).strftime("%H:%M UTC")
    if origin == source or origin == label or origin == "hn":
        return f"{label} · {when}"
    return f"{label} · {origin} · {when}"


def render_html(day: date, items: list[tuple[str, str, str]]) -> str:
    rows: list[str] = []
    for number, title, meta in items:
        rows.append(
            "<li>"
            f'<span class="n">{number}</span>'
            f'<p class="title">{html.escape(title)}</p>'
            f'<p class="meta">{html.escape(meta)}</p>'
            "</li>"
        )
    body = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Signal {day.isoformat()}</title>
<style>
  html, body {{
    margin: 0;
    height: 100%;
    background: #101114;
    color: #f4f1ea;
  }}
  body {{
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Inter, "Noto Sans", sans-serif;
  }}
  main {{
    width: 520px;
  }}
  h1 {{
    margin: 0;
    font-family: "Noto Serif", serif;
    font-size: 44px;
    font-weight: 560;
    letter-spacing: -0.03em;
  }}
  .day {{
    margin: 8px 0 0;
    font-size: 28px;
    color: #a8b0bb;
  }}
  ol {{
    list-style: none;
    padding: 0;
    margin: 36px 0 0;
  }}
  li {{
    display: grid;
    grid-template-columns: 36px 1fr;
    column-gap: 14px;
    margin: 0 0 22px;
  }}
  .n {{
    font-size: 28px;
    line-height: 1.25;
    color: #d6f25a;
  }}
  .title {{
    margin: 0;
    font-family: "Noto Serif", serif;
    font-size: 32px;
    line-height: 1.25;
    font-weight: 560;
  }}
  .meta {{
    grid-column: 2;
    margin: 4px 0 0;
    font-size: 28px;
    line-height: 1.3;
    color: #a8b0bb;
  }}
</style>
</head>
<body>
<main>
  <h1>Signal</h1>
  <p class="day">{day.isoformat()}</p>
  <ol>
{body}
  </ol>
</main>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    demo = Path(__file__).resolve().parent
    try:
        day = _day(argv)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    path = demo / "digests" / f"{day.isoformat()}.md"
    try:
        page = parse(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    items = [
        (str(number), hit.title, _meta(hit.source, hit.origin, hit.published))
        for number, hit in enumerate(page.items, start=1)
    ]
    out = path.with_suffix(".html")
    out.write_text(render_html(day, items), encoding="utf-8")
    print(out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
