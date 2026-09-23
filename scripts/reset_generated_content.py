from __future__ import annotations

import shutil
from pathlib import Path

from fb_archive_common import DOCS_DIR, IMAGE_DIR, ROOT


CONTENT_DIRS = [
    ROOT / "src" / "content" / "events",
    ROOT / "src" / "content" / "external",
    ROOT / "src" / "content" / "notes",
    ROOT / "src" / "content" / "pages",
    ROOT / "src" / "content" / "reports",
    ROOT / "src" / "content" / "slides",
]

GENERATED_DOCS = [
    DOCS_DIR / "facebook-page-archive.md",
    DOCS_DIR / "facebook-page-analysis.md",
    DOCS_DIR / "code-for-cat-civic-tech-animal-welfare-analysis.md",
    DOCS_DIR / "code-for-cat-public-web-timeline-factcheck.md",
    DOCS_DIR / "source-ledger.md",
    DOCS_DIR / "factcheck-ledger.md",
    DOCS_DIR / "source-index.json",
]

GENERATED_DIRS = [
    ROOT / ".astro",
    DOCS_DIR / "non-event",
    ROOT / "public" / "docs",
    ROOT / "public" / "assets" / "external-media",
    IMAGE_DIR / "original",
    IMAGE_DIR / "webp",
]

GENERATED_FILES = [
    IMAGE_DIR / "images-manifest.csv",
    IMAGE_DIR / "images-manifest.json",
    IMAGE_DIR / "images-manifest.md",
    ROOT / "src" / "lib" / "site-data.json",
]


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    for path in CONTENT_DIRS:
        reset_dir(path)
    for path in GENERATED_DIRS:
        if path.exists():
            shutil.rmtree(path)
    for path in GENERATED_DOCS + GENERATED_FILES:
        if path.exists():
            path.unlink()
    print("Reset generated content. Sources and application code were left intact.")


if __name__ == "__main__":
    main()
