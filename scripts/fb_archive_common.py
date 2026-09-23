from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "data" / "facebook-export"
DOCS_DIR = ROOT / "docs"
NON_EVENT_DIR = DOCS_DIR / "non-event"
IMAGE_DIR = ROOT / "public" / "assets" / "images"


def fix_text(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    if isinstance(value, list):
        return [fix_text(item) for item in value]
    if isinstance(value, dict):
        return {fix_text(k): fix_text(v) for k, v in value.items()}
    return value


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return fix_text(json.load(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ts_to_dt(timestamp: int | float | None) -> datetime | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp)


def format_date(timestamp: int | float | None) -> str:
    dt = ts_to_dt(timestamp)
    return dt.strftime("%Y.%m.%d") if dt else ""


def format_datetime(timestamp: int | float | None) -> str:
    dt = ts_to_dt(timestamp)
    return dt.strftime("%Y.%m.%d %H:%M") if dt else ""


def slugify(text: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return slug or fallback


def yaml_string(value: str) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def yaml_list(values: list[str]) -> str:
    return json.dumps(values or [], ensure_ascii=False)


def clean_markdown(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    compact: list[str] = []
    blank = 0
    for line in lines:
        if line.strip():
            blank = 0
            compact.append(line)
        else:
            blank += 1
            if blank <= 1:
                compact.append("")
    return "\n".join(compact).strip()


def profile() -> dict[str, Any]:
    path = EXPORT_DIR / "profile_information" / "profile_information" / "profile_information.json"
    data = read_json(path).get("profile_v2", {}) if path.exists() else {}
    name_data = data.get("name", {})
    websites = [item.get("address", "") for item in data.get("websites", []) if item.get("address")]
    return {
        "name": name_data.get("full_name") or data.get("username") or "Facebook Page Archive",
        "username": data.get("username", ""),
        "url": data.get("profile_uri", ""),
        "description": data.get("intro_bio", {}).get("name", ""),
        "category": data.get("profile_category", ""),
        "websites": websites,
        "registered": format_datetime(data.get("registration_timestamp")),
    }


def event_place(event: dict[str, Any]) -> str:
    place = event.get("place") or {}
    bits = [place.get("name", ""), place.get("address", "")]
    return " / ".join([bit for bit in bits if bit])


def load_events() -> list[dict[str, Any]]:
    events_path = EXPORT_DIR / "this_profile's_activity_across_facebook" / "events" / "events.json"
    if not events_path.exists():
        return []
    data = read_json(events_path)
    events = data.get("your_events_v2", data if isinstance(data, list) else [])
    normalized = []
    for index, event in enumerate(events, 1):
        title = event.get("name", f"Event {index}")
        start = event.get("start_timestamp") or event.get("create_timestamp") or 0
        normalized.append({
            "id": f"event-{index:03d}",
            "title": title,
            "start_timestamp": start,
            "end_timestamp": event.get("end_timestamp"),
            "date": format_date(start),
            "start": format_datetime(start),
            "end": format_datetime(event.get("end_timestamp")),
            "place": event_place(event),
            "description": clean_markdown(event.get("description", "")),
            "fbid": str(event.get("event_id", "")),
            "raw": event,
        })
    return sorted(normalized, key=lambda item: item["start_timestamp"] or 0, reverse=True)


def load_posts() -> list[dict[str, Any]]:
    posts = []
    base = EXPORT_DIR / "this_profile's_activity_across_facebook" / "posts"
    for path in sorted(base.glob("profile_posts_*.json")):
        data = read_json(path)
        if isinstance(data, list):
            for item in data:
                body = "\n\n".join([part.get("post", "") for part in item.get("data", []) if isinstance(part, dict) and part.get("post")])
                posts.append({
                    "timestamp": item.get("timestamp") or 0,
                    "date": format_date(item.get("timestamp")),
                    "title": item.get("title", ""),
                    "body": clean_markdown(body),
                    "attachments": item.get("attachments", []),
                    "source": str(path.relative_to(EXPORT_DIR)),
                })
    return sorted(posts, key=lambda item: item["timestamp"], reverse=True)


THEME_RULES = [
    ("cat-care", "地域猫・TNR", ["地域猫", "TNR", "保護猫", "譲渡", "殺処分", "猫"]),
    ("civic-tech", "シビックテック", ["Code for", "CivicTech", "IT", "アプリ", "システム"]),
    ("workshop", "ワークショップ", ["ワークショップ", "勉強会", "講座", "もくもく"]),
    ("hackathon", "ハッカソン", ["アイデアソン", "ハッカソン", "開発"]),
    ("disaster", "災害支援", ["防災", "災害", "被災", "避難", "支援"]),
    ("community", "交流・コミュニティ", ["交流", "Meetup", "ミートアップ", "定例", "サミット"]),
    ("open-data", "オープンデータ", ["オープンデータ", "データ", "可視化", "UDC"]),
]


def classify(title: str, description: str) -> tuple[list[str], list[str]]:
    haystack = f"{title}\n{description}"
    keys: list[str] = []
    labels: list[str] = []
    for key, label, needles in THEME_RULES:
        if any(needle.lower() in haystack.lower() for needle in needles):
            keys.append(key)
            labels.append(label)
    if not keys:
        return ["other"], ["その他"]
    return keys, labels


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)）]+", text or "")

