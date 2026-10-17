from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from engine.config import load_settings
from engine.deepdive import command_for
from engine.hits import Basket, Cut, Hit, keyword_score, top5
from engine.page import DigestPage, parse, render
from engine.select import parse_keep_drop


def _hit(source: str, canonical_id: str, title: str, published: datetime, snippet: str = "") -> Hit:
    return Hit(source, canonical_id, title, "https://example.com/x", published, snippet, "origin")


class EngineTest(unittest.TestCase):
    def test_merge_drops_old_miss_and_duplicate(self) -> None:
        now = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
        fresh = datetime(2026, 10, 15, 11, 0, tzinfo=timezone.utc)
        old = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)
        future = datetime(2026, 10, 15, 13, 0, tzinfo=timezone.utc)
        first = _hit("github", "github:vercel/ai@v1", "Claude release", fresh)
        future_hit = _hit("github", "github:vercel/ai@v2", "Claude future", future)
        duplicate = _hit("hn", "github:vercel/ai@v1", "Claude other", fresh)
        miss = _hit("hn", "hn:9", "weather report", fresh)
        stale = _hit("youtube", "yt:9", "Claude release", old)
        basket = Basket.merge(
            (
                Cut("github", (first, future_hit)),
                Cut("hn", (duplicate, miss)),
                Cut("youtube", (stale,)),
            ),
            ("claude",),
            now,
            24,
        )
        self.assertEqual(
            tuple(hit.canonical_id for hit in basket.hits),
            ("github:vercel/ai@v1",),
        )
        self.assertEqual(basket.hits[0].title, "Claude release")

    def test_keyword_score(self) -> None:
        hit = Hit(
            "hn",
            "hn:1",
            "Claude agent",
            "https://example.com/x",
            datetime(2026, 10, 15, tzinfo=timezone.utc),
            "",
            "hn",
        )
        self.assertEqual(keyword_score(hit, ("claude", "agent", "gpt")), 2)

    def test_top5_highest_score_first(self) -> None:
        start = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
        hits = (
            _hit("hn", "hn:low", "note", start - timedelta(hours=1)),
            _hit("hn", "hn:mid", "gpt", start - timedelta(hours=2)),
            _hit("hn", "hn:best", "claude agent gpt", start - timedelta(hours=3)),
            _hit("hn", "hn:a", "agent", start - timedelta(hours=4)),
            _hit("hn", "hn:b", "note", start - timedelta(hours=5)),
            _hit("hn", "hn:c", "note", start - timedelta(hours=6)),
        )
        picked = top5(hits, ("claude", "agent", "gpt"))
        self.assertEqual(
            tuple(hit.canonical_id for hit in picked),
            ("hn:best", "hn:mid", "hn:a", "hn:low", "hn:b"),
        )

    def test_render_parse_round_trip(self) -> None:
        hit = Hit(
            "hn",
            "hn:1",
            "Claude ] agent",
            "https://news.ycombinator.com/item?id=1",
            datetime(2026, 10, 15, 1, 2, 3, tzinfo=timezone.utc),
            "body",
            "hn",
        )
        page = DigestPage(datetime(2026, 10, 15, tzinfo=timezone.utc).date(), (hit,))
        parsed = parse(render(page))
        self.assertEqual(parsed.items[0].title, "Claude ] agent")
        self.assertEqual(parsed.items[0].url, "https://news.ycombinator.com/item?id=1")
        self.assertEqual(parsed.items[0].canonical_id, "hn:1")
        self.assertEqual(parsed.items[0].source, "hn")

    def test_parse_keep_drop(self) -> None:
        now = datetime(2026, 10, 15, tzinfo=timezone.utc)
        first = _hit("hn", "hn:1", "one", now)
        second = _hit("hn", "hn:2", "two", now)
        kept = parse_keep_drop("1 KEEP\n2 DROP", (first, second))
        self.assertEqual(tuple(hit.canonical_id for hit in kept), ("hn:1",))

    def test_load_settings_missing_keywords(self) -> None:
        payload = {
            "lookback_hours": 24,
            "per_source_cap": 20,
            "github_repos": ["vercel/ai"],
            "youtube_channels": [
                {"id": "UCMwVTLZIRRUyyVrkjDpn4pA", "label": "Cole Medin"},
                {"id": "UC_x36zCEGilGpB1m-V4gmjg", "label": "IndyDevDan"},
                {"id": "UCLKPca3kwwd-B59HNr-_lvA", "label": "AI Engineer"},
                {"id": "UCswG6FSbgZjbWtdf_hMLaow", "label": "Matt Pocock"},
            ],
            "last30days_checkout": "",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_settings(path)

    def test_command_for_without_checkout(self) -> None:
        text = command_for("Claude agent", None)
        self.assertIn("env -u LAST30DAYS_HOST", text)
        self.assertIn("--search reddit,hackernews,polymarket,github", text)
        self.assertEqual(
            text,
            "env -u LAST30DAYS_HOST python3 skills/last30days/scripts/last30days.py "
            "'Claude agent' --search reddit,hackernews,polymarket,github",
        )


if __name__ == "__main__":
    unittest.main()
