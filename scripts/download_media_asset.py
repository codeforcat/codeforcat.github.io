from __future__ import annotations

import argparse
import json
import mimetypes
import re
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fb_archive_common import ROOT

MANIFEST = ROOT / "sources" / "media" / "media-manifest.json"
DOWNLOAD_DIR = ROOT / "sources" / "media" / "downloads"
MAX_BYTES = 20 * 1024 * 1024


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:72] or "media"


def load_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def save_manifest(data: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extension_from(content_type: str, url: str) -> str:
    path_ext = Path(urlparse(url).path).suffix.lower()
    if path_ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return path_ext
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
    return guessed or ".bin"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a candidate media asset into sources/media/downloads and register rights metadata.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--creator", default="")
    parser.add_argument("--license", default="unknown")
    parser.add_argument("--permission", default="unknown", choices=["unknown", "granted", "denied", "public-domain", "open-license"])
    parser.add_argument("--visibility", default="review", choices=["review", "public", "private"])
    parser.add_argument("--alt", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    request = Request(args.source_url, headers={"User-Agent": "code-for-cat-archive-media-fetcher/1.0"})
    try:
      with urlopen(request, timeout=args.timeout) as response:
          content_type = response.headers.get("content-type", "")
          if not content_type.startswith("image/"):
              raise ValueError(f"Not an image content type: {content_type}")
          raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise SystemExit(f"download failed: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise SystemExit(f"download failed: image exceeds {MAX_BYTES} bytes")

    ext = extension_from(content_type, args.source_url)
    filename = f"{date.today().isoformat()}-{slugify(args.title)}{ext}"
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DOWNLOAD_DIR / filename
    local_path.write_bytes(raw)

    manifest = load_manifest()
    manifest.append({
        "title": args.title,
        "source_url": args.source_url,
        "local_path": str(local_path.relative_to(ROOT)),
        "creator": args.creator,
        "license": args.license,
        "permission": args.permission,
        "visibility": args.visibility,
        "alt": args.alt,
        "notes": args.notes,
        "content_type": content_type,
        "registered_at": date.today().isoformat(),
    })
    save_manifest(manifest)
    print(local_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
