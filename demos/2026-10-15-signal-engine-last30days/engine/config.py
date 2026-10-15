from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

REQUIRED_YOUTUBE_IDS = (
    "UCMwVTLZIRRUyyVrkjDpn4pA",
    "UC_x36zCEGilGpB1m-V4gmjg",
    "UCLKPca3kwwd-B59HNr-_lvA",
    "UCswG6FSbgZjbWtdf_hMLaow",
)


@dataclass(frozen=True)
class YoutubeChannel:
    channel_id: str
    label: str


@dataclass(frozen=True)
class Settings:
    lookback_hours: int
    per_source_cap: int
    keywords: tuple[str, ...]
    github_repos: tuple[str, ...]
    youtube_channels: tuple[YoutubeChannel, ...]
    last30days_checkout: Path | None


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip())


def _as_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def load_settings(path: Path) -> Settings:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config must be an object")

    if "lookback_hours" in raw:
        lookback_hours = _as_int(raw["lookback_hours"], "lookback_hours")
    else:
        lookback_hours = 24
    if lookback_hours < 1:
        raise ValueError("lookback_hours must be at least 1")

    per_source_cap = _as_int(raw.get("per_source_cap"), "per_source_cap")
    if per_source_cap < 1:
        raise ValueError("per_source_cap must be at least 1")

    keywords_raw = raw.get("keywords")
    if not isinstance(keywords_raw, list) or len(keywords_raw) == 0:
        raise ValueError("keywords must be a non-empty list")
    keywords: list[str] = []
    for keyword in keywords_raw:
        if not isinstance(keyword, str) or keyword.strip() == "":
            raise ValueError("keywords must be non-empty strings")
        keywords.append(keyword)

    repos_raw = raw.get("github_repos", [])
    if not isinstance(repos_raw, list):
        raise ValueError("github_repos must be a list")
    repos: list[str] = []
    for repo in repos_raw:
        if not isinstance(repo, str) or repo.count("/") != 1:
            raise ValueError("github repo must contain exactly one slash")
        owner, name = repo.split("/", 1)
        if owner == "" or name == "":
            raise ValueError("github repo must contain exactly one slash")
        repos.append(repo)

    channels_raw = raw.get("youtube_channels")
    if not isinstance(channels_raw, list):
        raise ValueError("youtube_channels must be a list")
    channels: list[YoutubeChannel] = []
    seen: set[str] = set()
    for row in channels_raw:
        if not isinstance(row, dict):
            raise ValueError("youtube channel must be an object")
        channel_id = row.get("id")
        label = row.get("label")
        if not isinstance(channel_id, str) or channel_id == "":
            raise ValueError("youtube channel id is missing")
        if not isinstance(label, str) or label == "":
            raise ValueError("youtube channel label is missing")
        channels.append(YoutubeChannel(channel_id, label))
        seen.add(channel_id)
    for channel_id in REQUIRED_YOUTUBE_IDS:
        if channel_id not in seen:
            raise ValueError("youtube channel id is missing")

    checkout_raw = raw.get("last30days_checkout", "")
    if checkout_raw is None or (isinstance(checkout_raw, str) and checkout_raw.strip() == ""):
        checkout = None
    elif isinstance(checkout_raw, str):
        checkout = Path(checkout_raw)
    else:
        raise ValueError("last30days_checkout must be a string")

    return Settings(
        lookback_hours,
        per_source_cap,
        tuple(keywords),
        tuple(repos),
        tuple(channels),
        checkout,
    )
