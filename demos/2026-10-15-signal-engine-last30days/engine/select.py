from __future__ import annotations

import json
import sys
from datetime import datetime

from engine.config import Settings
from engine.hits import Basket, Cut, Hit, keyword_score, matches_keywords, top5, within_window
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


def _clip(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 3] + "..."


def _print_trace(cuts: tuple[Cut, ...], settings: Settings, now: datetime) -> None:
    fetched = {"github": 0, "hn": 0, "youtube": 0}
    old: list[Hit] = []
    future: list[Hit] = []
    capped = 0
    for cut in cuts:
        fetched[cut.source] += cut.fetched
        old.extend(cut.dropped_old)
        future.extend(cut.dropped_future)
        capped += cut.fetched - len(cut.dropped_old) - len(cut.dropped_future) - len(cut.hits)
    print(f"github {fetched['github']}", flush=True)
    print(f"hn {fetched['hn']}", flush=True)
    print(f"youtube {fetched['youtube']}", flush=True)
    print("", flush=True)
    keyword_drops: list[Hit] = []
    keyword_keeps: list[Hit] = []
    duplicates: list[Hit] = []
    seen: set[str] = set()
    for cut in cuts:
        for hit in cut.hits:
            if not within_window(hit.published, now, settings.lookback_hours):
                continue
            if not matches_keywords(hit, settings.keywords):
                keyword_drops.append(hit)
                continue
            if hit.canonical_id in seen:
                duplicates.append(hit)
                continue
            seen.add(hit.canonical_id)
            keyword_keeps.append(hit)
    print("cheap filters", flush=True)
    print(f"old {len(old)}  future {len(future)}", flush=True)
    print(f"duplicate {len(duplicates)}  cap {capped}", flush=True)
    shown = 0
    for hit in sorted(old, key=lambda item: item.published, reverse=True):
        if shown >= 2:
            break
        print(f"drop old  {_clip(hit.title, 28)}", flush=True)
        shown += 1
    for hit in future[:1]:
        print(f"drop future  {_clip(hit.title, 25)}", flush=True)
    for hit in duplicates[:1]:
        print(f"drop duplicate  {_clip(hit.title, 21)}", flush=True)
    print("", flush=True)
    print("keyword scorer (no Grok key)", flush=True)
    ranked = sorted(
        keyword_keeps,
        key=lambda hit: (
            -keyword_score(hit, settings.keywords),
            -hit.published.timestamp(),
            hit.canonical_id,
        ),
    )
    for hit in ranked[:3]:
        score = keyword_score(hit, settings.keywords)
        print(f"KEEP {score}  {_clip(hit.title, 29)}", flush=True)
    for hit in keyword_drops[:2]:
        print(f"DROP 0  no keyword  {_clip(hit.title, 18)}", flush=True)
    print(f"keep {len(keyword_keeps)}  drop {len(keyword_drops)}", flush=True)
    print("", flush=True)


def collect_and_select(
    settings: Settings,
    now: datetime,
    api_key: str | None,
) -> tuple[Hit, ...]:
    cuts = collect(settings, now)
    if not api_key:
        _print_trace(cuts, settings, now)
    basket = Basket.merge(cuts, settings.keywords, now, settings.lookback_hours)
    hits = basket.hits
    if api_key:
        hits = grok_keep(hits, api_key)
    return top5(hits, settings.keywords)
