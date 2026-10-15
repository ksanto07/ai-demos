from __future__ import annotations

import json
import sys
from datetime import datetime

from engine.config import Settings
from engine.hits import Basket, Hit, top5
from engine.pull import collect, http_post

GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-4"

_SYSTEM = (
    "Reply with one line per item and nothing else. "
    "Each line is the item number, a space, then KEEP or DROP."
)


def parse_keep_drop(text: str, hits: tuple[Hit, ...]) -> tuple[Hit, ...]:
    decision = {index: False for index in range(1, len(hits) + 1)}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        index = int(parts[0])
        if index not in decision:
            continue
        word = parts[1].upper()
        if word == "KEEP" or word == "DROP":
            decision[index] = word == "KEEP"
    return tuple(hit for index, hit in enumerate(hits, start=1) if decision[index])


def _prompt(hits: tuple[Hit, ...]) -> str:
    blocks: list[str] = []
    for number, hit in enumerate(hits, start=1):
        title = " ".join(hit.title.split())
        snippet = " ".join(hit.snippet.split())
        blocks.append(f"{number} {hit.source} {title}\n{hit.url}\n{snippet}")
    return "\n\n".join(blocks)


def grok_keep(hits: tuple[Hit, ...], api_key: str) -> tuple[Hit, ...]:
    if not hits:
        return hits
    payload: dict[str, object] = {
        "model": GROK_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _prompt(hits)},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        body = http_post(GROK_URL, payload, headers)
        parsed = json.loads(body)
        text = parsed["choices"][0]["message"]["content"]
        if not isinstance(text, str):
            raise ValueError("grok content is not text")
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print(f"grok {' '.join(str(exc).split())}", file=sys.stderr)
        return hits
    return parse_keep_drop(text, hits)


def collect_and_select(
    settings: Settings,
    now: datetime,
    api_key: str | None,
) -> tuple[Hit, ...]:
    cuts = collect(settings, now)
    basket = Basket.merge(cuts, settings.keywords, now, settings.lookback_hours)
    hits = basket.hits
    if api_key:
        hits = grok_keep(hits, api_key)
    return top5(hits, settings.keywords)
