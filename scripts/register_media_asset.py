from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from fb_archive_common import ROOT

MANIFEST = ROOT / "sources" / "media" / "media-manifest.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a candidate media asset and its rights metadata.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--local-path", default="")
    parser.add_argument("--creator", default="")
    parser.add_argument("--license", default="unknown")
    parser.add_argument("--permission", default="unknown", choices=["unknown", "granted", "denied", "public-domain", "open-license"])
    parser.add_argument("--visibility", default="review", choices=["review", "public", "private"])
    parser.add_argument("--alt", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    else:
        data = []
    item = {
        "title": args.title,
        "source_url": args.source_url,
        "local_path": args.local_path,
        "creator": args.creator,
        "license": args.license,
        "permission": args.permission,
        "visibility": args.visibility,
        "alt": args.alt,
        "notes": args.notes,
        "registered_at": date.today().isoformat(),
    }
    data.append(item)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"registered: {args.title}")


if __name__ == "__main__":
    main()
