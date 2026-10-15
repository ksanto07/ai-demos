from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from engine.hits import Hit, Source

_DOT = " \u00b7 "


@dataclass(frozen=True)
class DigestPage:
    day: date
    items: tuple[Hit, ...]


def _escape_title(title: str) -> str:
    return title.replace("\\", "\\\\").replace("]", "\\]")


def _split_link(line: str, number: int) -> tuple[str, str]:
    prefix = f"{number}. ["
    if not line.startswith(prefix):
        raise ValueError("bad digest item")
    rest = line[len(prefix) :]
    chars: list[str] = []
    index = 0
    while index < len(rest):
        if rest[index] == "\\" and index + 1 < len(rest):
            chars.append(rest[index + 1])
            index += 2
            continue
        if rest.startswith("](", index):
            url = rest[index + 2 :]
            if not url.endswith(")"):
                raise ValueError("bad digest link")
            return "".join(chars), url[:-1]
        chars.append(rest[index])
        index += 1
    raise ValueError("bad digest link")


def _split_meta(line: str) -> tuple[Source, str, datetime]:
    if not line.startswith("   "):
        raise ValueError("bad digest meta")
    parts = line[3:].split(_DOT)
    if len(parts) != 3:
        raise ValueError("bad digest meta")
    source, origin, stamp = parts
    if source == "github" or source == "hn" or source == "youtube":
        kind: Source = source
    else:
        raise ValueError("bad digest source")
    try:
        published = datetime.fromisoformat(stamp)
    except ValueError as exc:
        raise ValueError("bad digest time") from exc
    if published.utcoffset() != timedelta(0):
        raise ValueError("bad digest time")
    return kind, origin, published.astimezone(timezone.utc)


def _split_id(line: str) -> str:
    if not line.startswith("   ") or line[3:] == "":
        raise ValueError("bad digest id")
    return line[3:]


def render(page: DigestPage) -> str:
    lines = [f"# Signal {page.day.isoformat()}", ""]
    for number, hit in enumerate(page.items, start=1):
        when = hit.published.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        lines.append(f"{number}. [{_escape_title(hit.title)}]({hit.url})")
        lines.append(f"   {hit.source}{_DOT}{hit.origin}{_DOT}{when}")
        lines.append(f"   {hit.canonical_id}")
    return "\n".join(lines) + "\n"


def parse(text: str) -> DigestPage:
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# Signal "):
        raise ValueError("bad digest header")
    try:
        day = date.fromisoformat(lines[0][len("# Signal ") :])
    except ValueError as exc:
        raise ValueError("bad digest date") from exc
    items: list[Hit] = []
    cursor = 1
    while cursor < len(lines):
        if lines[cursor] == "":
            cursor += 1
            continue
        if cursor + 2 >= len(lines):
            raise ValueError("bad digest item")
        number = len(items) + 1
        title, url = _split_link(lines[cursor], number)
        source, origin, published = _split_meta(lines[cursor + 1])
        canonical_id = _split_id(lines[cursor + 2])
        items.append(Hit(source, canonical_id, title, url, published, "", origin))
        cursor += 3
    return DigestPage(day, tuple(items))


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)
