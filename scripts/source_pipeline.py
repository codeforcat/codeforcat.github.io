from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fb_archive_common import DOCS_DIR, ROOT, write_json

SOURCES_DIR = ROOT / "sources"
WORKLOG_DIR = ROOT / "worklog"
SOURCE_LEDGER = DOCS_DIR / "source-ledger.md"
FACTCHECK_LEDGER = DOCS_DIR / "factcheck-ledger.md"
WORKLOG_PATH = WORKLOG_DIR / "content-pipeline-log.md"
SOURCE_INDEX_JSON = DOCS_DIR / "source-index.json"
SYNTHESIS_REPORT = DOCS_DIR / "code-for-cat-civic-tech-animal-welfare-analysis.md"
TIMELINE_FACTCHECK_REPORT = DOCS_DIR / "code-for-cat-public-web-timeline-factcheck.md"

SOURCE_TYPES = {
    "facebook-export": "facebook_export",
    "ai-deepresearch": "ai_deepresearch",
    "codex-research": "codex_research",
    "internal": "internal",
    "web": "web",
    "media": "media",
}


@dataclass
class SourceDoc:
    path: Path
    relpath: str
    source_group: str
    source_type: str
    title: str
    visibility: str
    confidence: str
    checked_at: str
    source_urls: list[str]
    body: str


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, Any] = {}
    current_list: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if current_list and line.strip().startswith("- "):
            data.setdefault(current_list, []).append(line.strip()[2:].strip().strip('"'))
            continue
        current_list = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list = key
        else:
            data[key] = value.strip('"')
    return data, body.strip()


def urls_from_text(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>）]+", text)
    cleaned = []
    for url in urls:
        url = url.rstrip(".,、。")
        if url not in cleaned:
            cleaned.append(url)
    return cleaned


def infer_title(path: Path, body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ")


def load_sources() -> list[SourceDoc]:
    docs: list[SourceDoc] = []
    for group, source_type in SOURCE_TYPES.items():
        base = SOURCES_DIR / group
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.name.startswith("."):
                continue
            if path.name == "README.md":
                continue
            if path.suffix.lower() not in {".md", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = {}
                if parsed == []:
                    continue
                meta = parsed if isinstance(parsed, dict) else {}
                title = meta.get("title") or path.stem.replace("-", " ")
                body = json.dumps(parsed, ensure_ascii=False, indent=2)
            else:
                meta, body = parse_frontmatter(text)
                title = meta.get("title") or infer_title(path, body)
            source_urls = meta.get("source_urls") if isinstance(meta.get("source_urls"), list) else []
            source_urls = list(dict.fromkeys([*source_urls, *urls_from_text(body)]))
            docs.append(
                SourceDoc(
                    path=path,
                    relpath=str(path.relative_to(ROOT)),
                    source_group=group,
                    source_type=str(meta.get("source_type") or source_type),
                    title=str(title),
                    visibility=str(meta.get("visibility") or "review"),
                    confidence=str(meta.get("confidence") or "unverified"),
                    checked_at=str(meta.get("checked_at") or ""),
                    source_urls=source_urls,
                    body=body,
                )
            )
    return docs


def confidence_score(confidence: str) -> int:
    order = {
        "verified": 3,
        "partial": 2,
        "unverified": 1,
        "": 0,
    }
    return order.get(confidence, 1)


def write_source_ledger(docs: list[SourceDoc]) -> None:
    lines = [
        "# 情報源台帳",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 情報源 | 種別 | 公開扱い | 確認度 | 確認日 | URL数 | ファイル |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for doc in docs:
        lines.append(
            f"| {doc.title} | {doc.source_type} | {doc.visibility} | {doc.confidence} | {doc.checked_at or '-'} | {len(doc.source_urls)} | `{doc.relpath}` |"
        )
    SOURCE_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(
        SOURCE_INDEX_JSON,
        [
            {
                "title": doc.title,
                "path": doc.relpath,
                "source_group": doc.source_group,
                "source_type": doc.source_type,
                "visibility": doc.visibility,
                "confidence": doc.confidence,
                "checked_at": doc.checked_at,
                "source_urls": doc.source_urls,
            }
            for doc in docs
        ],
    )


def write_factcheck_ledger(docs: list[SourceDoc]) -> None:
    claims: dict[str, list[SourceDoc]] = {}
    patterns = {
        "2015年発足": r"2015|発足|CIVIC TECH FORUM|Code for Japan Summit",
        "CatBot": r"CatBot|ChatBot|チャットボット",
        "ライタソン": r"ライタソン|Writeathon|Q&A|QnA",
        "Catdon": r"Catdon|Mastodon|マストドン",
        "NECOLO": r"NECOLO|ネコロ",
        "石巻ハッカソン": r"石巻|田代島|キャットソン|地域猫カードゲーム",
        "2021-2024空白期": r"2021|2022|2023|2024|空白|更新",
        "2025年近況": r"2025|生成AI|猫エージェント|Podcast|ポッドキャスト",
    }
    for claim, pattern in patterns.items():
        regex = re.compile(pattern, re.I)
        claims[claim] = [doc for doc in docs if regex.search(doc.body) or regex.search(doc.title)]

    lines = [
        "# ファクトチェック台帳",
        "",
        "この台帳は `sources/` 配下の入力情報源だけを読み、主要トピックごとの根拠数と確認状態を機械的に整理したものです。内容の正誤判断は、人間または追加調査で更新してください。",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| トピック | 根拠数 | 最高確認度 | 主な情報源 | 判定メモ |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for claim, items in claims.items():
        if not items:
            lines.append(f"| {claim} | 0 | - | - | 要調査 |")
            continue
        best = max(items, key=lambda doc: confidence_score(doc.confidence)).confidence
        source_names = "<br>".join([f"`{doc.relpath}`" for doc in items[:4]])
        note = "複数ソースで確認候補" if len(items) >= 2 else "単一ソース。追加確認推奨"
        if any(doc.source_type == "internal" for doc in items):
            note += "。内部情報を含むため公開表現に注意"
        lines.append(f"| {claim} | {len(items)} | {best} | {source_names} | {note} |")
    FACTCHECK_LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_timeline_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(SOURCES_DIR.rglob("*.json")):
        if path.name == "media-manifest.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for item in data.get("timeline", []):
            if isinstance(item, dict):
                items.append(item)
    return sorted(items, key=lambda item: int(item.get("sort") or 0))


def write_synthesis_reports(docs: list[SourceDoc]) -> None:
    source_rows = [
        f"- `{doc.relpath}`: {doc.title}（{doc.source_type}, {doc.confidence}）"
        for doc in docs
    ]
    confirmed = []
    cautions = []
    for doc in docs:
        if doc.source_group == "codex-research":
            confirmed.append(f"- {doc.title}: Codex調査により一部確認済み。URL数 {len(doc.source_urls)}。")
        elif doc.source_group == "facebook-export":
            confirmed.append(f"- {doc.title}: 非公開原本から公開イベント・投稿・画像候補を抽出する一次入力。")
        elif doc.source_group == "ai-deepresearch":
            cautions.append(f"- {doc.title}: 分析仮説として扱い、公開断定には追加確認が必要。")
        elif doc.source_group == "internal":
            cautions.append(f"- {doc.title}: 内部情報を含む可能性があるため、公開前に人間の確認が必要。")

    timeline_items = load_timeline_items()
    timeline_rows = [
        f"| {item.get('displayDate') or item.get('date')} | {item.get('title')} | {item.get('confidence', '-')} | {item.get('sourceLabel', '-')} |"
        for item in timeline_items
    ]

    SYNTHESIS_REPORT.write_text("\n".join([
        "# シビックテックと動物福祉の融合",
        "",
        "この資料は `sources/` 配下の情報源だけを入力として再構成した公開向け分析メモです。AI調査は仮説、Codex調査は確認済み範囲、Facebookエクスポートは非公開原本からの抽出結果として扱います。",
        "",
        "## 入力情報源",
        *(source_rows or ["- 入力情報源はまだありません。"]),
        "",
        "## 確認できる中核",
        *(confirmed or ["- 追加確認が必要です。"]),
        "",
        "## 分析上の読み取り",
        "- Code for CATは、地理的範囲ではなく「猫と人の共生」というテーマを軸にしたシビックテック活動として整理できます。",
        "- CatBot、ライタソン、Catdon、NECOLOなどは、猫への関心を入口に知識共有、参加型データ整備、安心できるコミュニティづくりへ広げる実践として読めます。",
        "- 地域猫をめぐる課題は、猫だけの問題ではなく、住民合意、行政、保護活動、専門知、オンラインコミュニティが交差する社会課題として扱う必要があります。",
        "",
        "## 注意が必要な情報",
        *(cautions or ["- 現時点で特記する注意情報はありません。"]),
        "",
        "## 公開表現の方針",
        "- `verified` または複数根拠があるものは「確認できる」「記録されている」と表現する。",
        "- `partial` は「公開情報から確認できる範囲では」「公開記事では」と表現する。",
        "- `unverified` は「とされる」「追加確認が必要」と表現する。",
    ]) + "\n", encoding="utf-8")

    TIMELINE_FACTCHECK_REPORT.write_text("\n".join([
        "# 公開Web調査による活動年表とファクトチェック",
        "",
        "この資料は `sources/` の構造化年表ファクトと情報源台帳をもとに生成しています。Facebookエクスポートだけでは薄い初期・空白期の活動を、公開Web調査で補うための確認用資料です。",
        "",
        "## 年表ファクト候補",
        "| 時期 | 内容 | 確認度 | 主な情報源 |",
        "| --- | --- | --- | --- |",
        *(timeline_rows or ["| - | 構造化された年表ファクトはまだありません。 | - | - |"]),
        "",
        "## 情報源別の扱い",
        "- Facebookエクスポート: 非公開原本。公開イベント、投稿、画像候補の抽出元として使う。",
        "- AI Deepresearch: 分析仮説。単独では事実断定に使わない。",
        "- Codex調査: 公開Webで確認した範囲の調査メモ。URLと確認日を併記する。",
        "- 内部情報: 今後追加予定。公開可否と個人情報を確認してから反映する。",
        "",
        "## 追加確認が必要な点",
        "- 2015年の正確な開催日と正式発足日の一次情報。",
        "- 2017年Catdon立ち上げ日、ネコ市ネコ座ライタソン、NECOLOの一次情報または関係者確認。",
        "- 2021〜2024年の活動状況。公開記録が少ないだけで、活動停止とは断定しない。",
        "- 2025年Podcastの音声内容確認と、現在の活動状況の内部確認。",
    ]) + "\n", encoding="utf-8")


def append_worklog(docs: list[SourceDoc]) -> None:
    WORKLOG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "- `sources/` をスキャン",
        f"- 情報源ファイル: {len(docs)}件",
        f"- 公開扱いpublic: {sum(1 for doc in docs if doc.visibility == 'public')}件",
        f"- review: {sum(1 for doc in docs if doc.visibility == 'review')}件",
        f"- private: {sum(1 for doc in docs if doc.visibility == 'private')}件",
        "- `docs/source-ledger.md` を更新",
        "- `docs/factcheck-ledger.md` を更新",
        "",
    ]
    previous = WORKLOG_PATH.read_text(encoding="utf-8") if WORKLOG_PATH.exists() else "# コンテンツパイプライン作業記録\n\n"
    WORKLOG_PATH.write_text(previous.rstrip() + "\n\n" + "\n".join(lines), encoding="utf-8")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_sources()
    write_source_ledger(docs)
    write_factcheck_ledger(docs)
    write_synthesis_reports(docs)
    append_worklog(docs)
    print(f"Indexed {len(docs)} source files.")


if __name__ == "__main__":
    main()
