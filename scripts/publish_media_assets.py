from __future__ import annotations

import json
import shutil
from pathlib import Path

from fb_archive_common import ROOT, write_json

SOURCE_MANIFEST = ROOT / "sources" / "media" / "media-manifest.json"
PUBLIC_DIR = ROOT / "public" / "assets" / "external-media"
PUBLIC_MANIFEST = PUBLIC_DIR / "external-media-manifest.json"
ALLOWED_PERMISSIONS = {"granted", "public-domain", "open-license"}


def main() -> None:
    if not SOURCE_MANIFEST.exists():
        write_json(PUBLIC_MANIFEST, [])
        print("Published 0 external media assets.")
        return
    data = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = []
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    published = []
    for index, item in enumerate(data, 1):
        if item.get("visibility") != "public":
            continue
        if item.get("permission") not in ALLOWED_PERMISSIONS:
            continue
        local_path = item.get("local_path") or ""
        if not local_path:
            continue
        source = ROOT / local_path
        if not source.exists() or not source.is_file():
            continue
        ext = source.suffix.lower() or ".jpg"
        target_name = f"external-media-{index:03d}{ext}"
        target = PUBLIC_DIR / target_name
        shutil.copy2(source, target)
        published.append({
            **item,
            "public_path": f"assets/external-media/{target_name}",
        })
    write_json(PUBLIC_MANIFEST, published)
    print(f"Published {len(published)} external media assets.")


if __name__ == "__main__":
    main()
