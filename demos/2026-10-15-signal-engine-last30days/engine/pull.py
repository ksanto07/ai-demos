from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from engine.config import Settings, YoutubeChannel
from engine.hits import Cut, Hit, Source, within_window

USER_AGENT = "signal-engine-last30days/0.1"
TIMEOUT_SECONDS = 20

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def http_get(url: str, headers: dict[str, str] | None = None) -> bytes:
    merged = {"User-Agent": USER_AGENT}
    if headers:
        merged.update(headers)
    request = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def http_post(url: str, payload: object, headers: dict[str, str]) -> bytes:
    merged = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    merged.update(headers)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=merged, method="POST")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def _parse_time(value: object) -> datetime | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _one_line(value: str) -> str:
    return " ".join(value.split())


def _bounded(
    hits: list[Hit],
    now: datetime,
    lookback_hours: int,
    cap: int,
    source: Source,
) -> Cut:
    fresh: list[Hit] = []
    old: list[Hit] = []
    future: list[Hit] = []
    for hit in hits:
        if hit.published > now:
            future.append(hit)
        elif within_window(hit.published, now, lookback_hours):
            fresh.append(hit)
        else:
            old.append(hit)
    fresh.sort(key=lambda hit: hit.published, reverse=True)
    return Cut(source, tuple(fresh[:cap]), tuple(old), tuple(future), len(hits))


def _empty(source: Source, label: str, exc: BaseException) -> Cut:
    detail = " ".join(str(exc).split())
    if label:
        print(f"{source} {label} {detail}", file=sys.stderr)
    else:
        print(f"{source} {detail}", file=sys.stderr)
    return Cut(source, ())


def parse_github_releases(
    payload: bytes,
    owner: str,
    repo: str,
    now: datetime,
    lookback_hours: int,
    cap: int,
) -> Cut:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("github releases payload is not a list")
    origin = f"{owner}/{repo}"
    hits: list[Hit] = []
    for item in data:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        tag = item.get("tag_name")
        if not isinstance(tag, str) or tag == "":
            continue
        published = _parse_time(item.get("published_at"))
        if published is None:
            continue
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            title = _one_line(name)
        else:
            title = _one_line(tag)
        if title == "":
            continue
        url = item.get("html_url")
        if not isinstance(url, str) or url.strip() == "":
            continue
        body = item.get("body")
        snippet = body if isinstance(body, str) else ""
        hits.append(
            Hit("github", f"github:{owner}/{repo}@{tag}", title, url, published, snippet, origin)
        )
    return _bounded(hits, now, lookback_hours, cap, "github")


def parse_hn_hits(payload: bytes, now: datetime, lookback_hours: int, cap: int) -> Cut:
    data = json.loads(payload)
    rows = data.get("hits") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError("hn payload missing hits")
    hits: list[Hit] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        object_id = row.get("objectID")
        if object_id is None or isinstance(object_id, bool):
            continue
        canonical = str(object_id)
        if canonical == "":
            continue
        title_raw = row.get("title")
        if not isinstance(title_raw, str):
            continue
        title = _one_line(title_raw)
        if title == "":
            continue
        published = _parse_time(row.get("created_at_i"))
        if published is None:
            published = _parse_time(row.get("created_at"))
        if published is None:
            continue
        url = row.get("url")
        if not isinstance(url, str) or url.strip() == "":
            url = f"https://news.ycombinator.com/item?id={canonical}"
        story = row.get("story_text")
        snippet = story if isinstance(story, str) else ""
        hits.append(Hit("hn", f"hn:{canonical}", title, url, published, snippet, "hn"))
    return _bounded(hits, now, lookback_hours, cap, "hn")


def parse_youtube_feed(
    payload: bytes,
    channel: YoutubeChannel,
    now: datetime,
    lookback_hours: int,
    cap: int,
) -> Cut:
    root = ET.fromstring(payload)
    hits: list[Hit] = []
    for entry in root.findall("atom:entry", NS):
        video_id = (entry.findtext("yt:videoId", default="", namespaces=NS) or "").strip()
        if video_id == "":
            continue
        title = _one_line(entry.findtext("atom:title", default="", namespaces=NS) or "")
        if title == "":
            title = video_id
        published = _parse_time(entry.findtext("atom:published", default="", namespaces=NS))
        if published is None:
            continue
        href = ""
        for link in entry.findall("atom:link", NS):
            if link.attrib.get("rel") == "alternate":
                href = link.attrib.get("href") or ""
                break
        if href == "":
            href = f"https://www.youtube.com/watch?v={video_id}"
        description = entry.findtext("media:group/media:description", namespaces=NS)
        if description is None:
            description = entry.findtext("media:description", namespaces=NS)
        snippet = description if isinstance(description, str) else ""
        hits.append(
            Hit("youtube", f"yt:{video_id}", title, href, published, snippet, channel.label)
        )
    return _bounded(hits, now, lookback_hours, cap, "youtube")


def collect(settings: Settings, now: datetime) -> tuple[Cut, ...]:
    cuts: list[Cut] = []
    for repo in settings.github_repos:
        owner, name = repo.split("/", 1)
        url = (
            "https://api.github.com/repos/"
            + urllib.parse.quote(owner)
            + "/"
            + urllib.parse.quote(name)
            + "/releases"
        )
        try:
            payload = http_get(url, {"Accept": "application/vnd.github+json"})
            cuts.append(
                parse_github_releases(
                    payload,
                    owner,
                    name,
                    now,
                    settings.lookback_hours,
                    settings.per_source_cap,
                )
            )
        except Exception as exc:
            cuts.append(_empty("github", repo, exc))
    window_start = int((now - timedelta(hours=settings.lookback_hours)).timestamp())
    query = urllib.parse.urlencode(
        {
            "tags": "story",
            "hitsPerPage": str(settings.per_source_cap),
            "numericFilters": f"created_at_i>{window_start}",
        }
    )
    try:
        payload = http_get("https://hn.algolia.com/api/v1/search_by_date?" + query)
        cuts.append(
            parse_hn_hits(payload, now, settings.lookback_hours, settings.per_source_cap)
        )
    except Exception as exc:
        cuts.append(_empty("hn", "", exc))
    for channel in settings.youtube_channels:
        feed = "https://www.youtube.com/feeds/videos.xml?" + urllib.parse.urlencode(
            {"channel_id": channel.channel_id}
        )
        try:
            payload = http_get(feed)
            cuts.append(
                parse_youtube_feed(
                    payload,
                    channel,
                    now,
                    settings.lookback_hours,
                    settings.per_source_cap,
                )
            )
        except Exception as exc:
            cuts.append(_empty("youtube", channel.label, exc))
    return tuple(cuts)
