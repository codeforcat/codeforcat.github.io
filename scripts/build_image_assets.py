from __future__ import annotations

import csv
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from fb_archive_common import EXPORT_DIR, IMAGE_DIR, format_date, load_posts, read_json, write_json


def media_timestamp(media: dict) -> int:
    meta = media.get("media_metadata", {}).get("photo_metadata", {}).get("exif_data", [])
    if meta and isinstance(meta[0], dict) and meta[0].get("taken_timestamp"):
        return meta[0]["taken_timestamp"]
    return media.get("creation_timestamp") or 0


def collect_references() -> dict[str, list[dict]]:
    refs: dict[str, list[dict]] = defaultdict(list)
    album_dir = EXPORT_DIR / "this_profile's_activity_across_facebook" / "posts" / "album"
    for path in sorted(album_dir.glob("*.json")):
        data = read_json(path)
        album_name = data.get("name", path.stem)
        cover = data.get("cover_photo")
        if cover and cover.get("uri"):
            refs[cover["uri"]].append({
                "source_type": "album_cover",
                "source_title": album_name,
                "source_date": format_date(media_timestamp(cover)),
                "description": cover.get("description") or cover.get("title") or album_name,
            })
        for photo in data.get("photos", []):
            if photo.get("uri"):
                refs[photo["uri"]].append({
                    "source_type": "album_photo",
                    "source_title": album_name,
                    "source_date": format_date(media_timestamp(photo)),
                    "description": photo.get("description") or photo.get("title") or album_name,
                })

    for post in load_posts():
        for attachment in post.get("attachments", []):
            for item in attachment.get("data", []):
                media = item.get("media", {}) if isinstance(item, dict) else {}
                if media.get("uri"):
                    refs[media["uri"]].append({
                        "source_type": "post_attachment",
                        "source_title": post.get("title") or post.get("body", "")[:80],
                        "source_date": post.get("date", ""),
                        "description": media.get("description") or media.get("title") or "",
                    })

    update_path = EXPORT_DIR / "profile_information" / "profile_information" / "profile_update_history.json"
    if update_path.exists():
        data = read_json(update_path)
        for item in data if isinstance(data, list) else data.get("profile_updates_v2", []):
            media = item.get("media", {}) if isinstance(item, dict) else {}
            if media.get("uri"):
                refs[media["uri"]].append({
                    "source_type": "profile_update",
                    "source_title": item.get("title", "プロフィール更新"),
                    "source_date": format_date(media_timestamp(media)),
                    "description": media.get("description") or media.get("title") or "",
                })
    return refs


def image_size(path: Path) -> tuple[str, str]:
    try:
        result = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], check=True, capture_output=True, text=True)
        width = height = ""
        for line in result.stdout.splitlines():
            if "pixelWidth:" in line:
                width = line.split(":", 1)[1].strip()
            if "pixelHeight:" in line:
                height = line.split(":", 1)[1].strip()
        return width, height
    except Exception:
        return "", ""


def main() -> None:
    original_dir = IMAGE_DIR / "original"
    webp_dir = IMAGE_DIR / "webp"
    original_dir.mkdir(parents=True, exist_ok=True)
    webp_dir.mkdir(parents=True, exist_ok=True)

    refs = collect_references()
    media_root = EXPORT_DIR / "this_profile's_activity_across_facebook" / "posts" / "media"
    media_files = sorted([path for path in media_root.glob("**/*") if path.is_file()])
    rows = []
    for index, source in enumerate(media_files, 1):
        asset_id = f"archive-image-{index:04d}"
        suffix = source.suffix.lower() if source.suffix.lower() in [".jpg", ".jpeg", ".png"] else source.suffix
        original_name = f"{asset_id}{suffix}"
        webp_name = f"{asset_id}.webp"
        original_path = original_dir / original_name
        webp_path = webp_dir / webp_name
        shutil.copy2(source, original_path)
        webp_status = "ok"
        try:
            subprocess.run(["cwebp", "-quiet", "-q", "82", str(original_path), "-o", str(webp_path)], check=True, capture_output=True, text=True)
            webp_asset_path = f"assets/images/webp/{webp_name}"
        except Exception as exc:
            webp_status = f"failed: {exc}"
            webp_asset_path = ""
        width, height = image_size(original_path)
        rel = str(source.relative_to(EXPORT_DIR))
        references = refs.get(rel, [])
        if not references:
            references = [{
                "source_type": "unreferenced_media_file",
                "source_title": source.parent.name,
                "source_date": "",
                "description": "",
            }]
        first = references[0]
        rows.append({
            "asset_id": asset_id,
            "original_backup_path": rel,
            "original_asset_path": f"assets/images/original/{original_name}",
            "webp_asset_path": webp_asset_path,
            "webp_status": webp_status,
            "width": width,
            "height": height,
            "source_type": first.get("source_type", ""),
            "source_title": first.get("source_title", ""),
            "source_date": first.get("source_date", ""),
            "description": first.get("description", ""),
            "reference_count": len(references),
            "all_references": references,
        })

    write_json(IMAGE_DIR / "images-manifest.json", rows)
    fields = ["asset_id", "original_backup_path", "original_asset_path", "webp_asset_path", "webp_status", "width", "height", "source_type", "source_title", "source_date", "description", "reference_count"]
    with (IMAGE_DIR / "images-manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    lines = ["# 画像マニフェスト", "", f"画像件数: {len(rows)}件", "", "| ID | 日付 | 種別 | 由来 | 画像 | 説明 |", "| --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        image = row["webp_asset_path"] or row["original_asset_path"]
        lines.append(f"| {row['asset_id']} | {row['source_date']} | {row['source_type']} | {row['source_title']} | `{image}` | {row['description']} |")
    (IMAGE_DIR / "images-manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Built {len(rows)} image assets.")


if __name__ == "__main__":
    main()
