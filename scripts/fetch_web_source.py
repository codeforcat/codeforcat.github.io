from __future__ import annotations

import argparse
import re
from datetime import date
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fb_archive_common import ROOT, yaml_list, yaml_string


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._in_title:
            self.title = f"{self.title} {text}".strip()
        elif not self._skip_depth:
            self.parts.append(text)

    def summary(self, limit: int = 1400) -> str:
        text = re.sub(r"\s+", " ", " ".join(self.parts)).strip()
        return text[:limit].rstrip()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:84] or "web-source"


def fetch(url: str, timeout: int) -> tuple[int, str, str]:
    request = Request(url, headers={"User-Agent": "code-for-cat-archive-source-fetcher/1.0"})
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        content_type = response.headers.get("content-type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        raw = response.read(2_000_000)
    return status, content_type, raw.decode(charset, errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a web page and save a reviewed source note under sources/web.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--confidence", default="partial", choices=["unverified", "partial", "verified"])
    parser.add_argument("--visibility", default="review", choices=["public", "private", "review"])
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--no-fetch", action="store_true", help="Create a source note without making a network request.")
    args = parser.parse_args()

    fetched_title = ""
    fetched_summary = ""
    status = ""
    content_type = ""
    error = ""
    if not args.no_fetch:
        try:
            status_code, content_type, html = fetch(args.url, args.timeout)
            status = str(status_code)
            parser_html = TextExtractor()
            parser_html.feed(html)
            fetched_title = parser_html.title
            fetched_summary = parser_html.summary()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            error = f"{type(exc).__name__}: {exc}"

    title = args.title or fetched_title or urlparse(args.url).netloc or args.url
    summary = args.summary or fetched_summary or "- TODO: 確認できた事実を短く記録する。"
    host = urlparse(args.url).netloc.replace("www.", "")
    slug = slugify(f"{args.date}-{host}-{title}")
    path = ROOT / "sources" / "web" / f"{slug}.md"
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        'source_type: "web"',
        f"created_at: {yaml_string(args.date)}",
        f"checked_at: {yaml_string(args.date)}",
        'author: "Codex web fetcher"',
        f"visibility: {yaml_string(args.visibility)}",
        f"confidence: {yaml_string(args.confidence)}",
        f"source_urls: {yaml_list([args.url])}",
        f"http_status: {yaml_string(status)}",
        f"content_type: {yaml_string(content_type)}",
        f"fetch_error: {yaml_string(error)}",
        'notes: "Fetched summary only. Re-check before publishing claims."',
        "---",
        "",
        f"# {title}",
        "",
        f"- URL: {args.url}",
        f"- 確認日: {args.date}",
        f"- 確認度: {args.confidence}",
        f"- HTTP status: {status or '-'}",
        f"- Content-Type: {content_type or '-'}",
        "",
        "## 確認できたこと",
        "",
        summary,
        "",
        "## 未確認・注意点",
        "",
        "- 自動抽出した要約は、公開前に人間が本文と照合する。",
    ]
    if error:
        lines.extend(["", "## 取得エラー", "", error])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
