from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Source = Literal["github", "hn", "youtube"]


@dataclass(frozen=True)
class Hit:
    source: Source
    canonical_id: str
    title: str
    url: str
    published: datetime
    snippet: str
    origin: str


@dataclass(frozen=True)
class Cut:
    source: Source
    hits: tuple[Hit, ...]
    dropped_old: tuple[Hit, ...] = ()
    dropped_future: tuple[Hit, ...] = ()
    fetched: int = 0


def within_window(published: datetime, now: datetime, lookback_hours: int) -> bool:
    if published > now:
        return False
    return now - published <= timedelta(hours=lookback_hours)


def _text(hit: Hit) -> str:
    return f"{hit.title} {hit.snippet}".casefold()


def matches_keywords(hit: Hit, keywords: tuple[str, ...]) -> bool:
    text = _text(hit)
    return any(keyword.casefold() in text for keyword in keywords)


def keyword_score(hit: Hit, keywords: tuple[str, ...]) -> int:
    text = _text(hit)
    seen: set[str] = set()
    score = 0
    for keyword in keywords:
        folded = keyword.casefold()
        if folded in seen:
            continue
        seen.add(folded)
        if folded in text:
            score += 1
    return score


def top5(hits: tuple[Hit, ...], keywords: tuple[str, ...]) -> tuple[Hit, ...]:
    ranked = sorted(
        hits,
        key=lambda hit: (
            -keyword_score(hit, keywords),
            -hit.published.timestamp(),
            hit.canonical_id,
        ),
    )
    return tuple(ranked[:5])


@dataclass(frozen=True)
class Basket:
    hits: tuple[Hit, ...]

    @staticmethod
    def merge(
        cuts: tuple[Cut, ...],
        keywords: tuple[str, ...],
        now: datetime,
        lookback_hours: int,
    ) -> Basket:
        seen: set[str] = set()
        kept: list[Hit] = []
        for cut in cuts:
            for hit in cut.hits:
                if not within_window(hit.published, now, lookback_hours):
                    continue
                if not matches_keywords(hit, keywords):
                    continue
                if hit.canonical_id in seen:
                    continue
                seen.add(hit.canonical_id)
                kept.append(hit)
        return Basket(tuple(kept))
