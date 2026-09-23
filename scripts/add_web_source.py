from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from fb_archive_common import ROOT, yaml_list, yaml_string


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80] or "web-source"


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a structured web source note under sources/web.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--confidence", default="partial", choices=["unverified", "partial", "verified"])
    parser.add_argument("--visibility", default="review", choices=["public", "private", "review"])
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    host = urlparse(args.url).netloc.replace("www.", "")
    slug = slugify(f"{args.date}-{host}-{args.title}")
    path = ROOT / "sources" / "web" / f"{slug}.md"
    body = [
        "---",
        f"title: {yaml_string(args.title)}",
        'source_type: "web"',
        f"created_at: {yaml_string(args.date)}",
        f"checked_at: {yaml_string(args.date)}",
        'author: "Codex or human researcher"',
        f"visibility: {yaml_string(args.visibility)}",
        f"confidence: {yaml_string(args.confidence)}",
        f"source_urls: {yaml_list([args.url])}",
        'notes: ""',
        "---",
        "",
        f"# {args.title}",
        "",
        f"- URL: {args.url}",
        f"- 確認日: {args.date}",
        f"- 確認度: {args.confidence}",
        "",
        "## 確認できたこと",
        "",
        args.summary or "- TODO: 確認できた事実を短く記録する。",
        "",
        "## 未確認・注意点",
        "",
        "- TODO: 公開前に確認が必要な点を記録する。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
