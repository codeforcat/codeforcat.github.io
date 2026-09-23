from __future__ import annotations

from collections import Counter

from fb_archive_common import DOCS_DIR, classify, extract_urls, load_events, load_posts, profile


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    prof = profile()
    events = load_events()
    posts = load_posts()
    year_counts = Counter((event["date"][:4] or "不明") for event in events)
    theme_counts = Counter()
    event_lines = []
    detail_lines = []
    for event in events:
        keys, labels = classify(event["title"], event["description"])
        for label in labels:
            theme_counts[label] += 1
        event_lines.append(f"- {event['date']} | {event['title']} | {', '.join(labels)} | {event['place']}")
        detail_lines.append("\n".join([
            f"### {event['title']}",
            "",
            f"- 日時: {event['start']}" + (f" - {event['end']}" if event["end"] else ""),
            f"- 場所: {event['place'] or '未記録'}",
            f"- テーマ: {', '.join(labels)}",
            "",
            event["description"] or "説明文はありません。",
        ]))

    links = []
    for post in posts:
        for url in extract_urls(post["body"]):
            links.append(f"- {post['date']} {url}")

    body = [
        "# Facebookページ公開アーカイブ",
        "",
        "## 基本情報",
        f"- ページ名: {prof['name']}",
        f"- Facebook URL: {prof['url']}",
        f"- 説明: {prof['description']}",
        f"- カテゴリ: {prof['category']}",
        f"- Webサイト: {', '.join(prof['websites']) or 'なし'}",
        "",
        "## 抽出サマリー",
        f"- イベント: {len(events)}件",
        f"- 投稿: {len(posts)}件",
        "",
        "## 年別イベント件数",
        *[f"- {year}: {count}件" for year, count in sorted(year_counts.items(), reverse=True)],
        "",
        "## テーマ別イベント件数",
        *[f"- {theme}: {count}件" for theme, count in theme_counts.most_common()],
        "",
        "## イベント年表",
        *event_lines,
        "",
        "## イベント詳細",
        "\n\n".join(detail_lines),
        "",
        "## 関連投稿",
        *[f"- {post['date']} {post['title'] or post['body'][:80]}" for post in posts[:30]],
        "",
        "## 共有リンク",
        *(links[:80] or ["- 共有リンクは抽出されませんでした。"]),
        "",
        "## 投稿に紐づく画像",
        "画像一覧は `public/assets/images/images-manifest.md` を参照してください。",
        "",
        "## 公開前の注意点",
        "- メッセージ、端末、管理履歴、フォロワー個人名、リアクション個人名は公開対象外です。",
        "- 人物が大きく写る写真、非公開意図が不明な画像、公開URLは人間が最終確認してください。",
    ]
    (DOCS_DIR / "facebook-page-archive.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    (DOCS_DIR / "facebook-page-analysis.md").write_text("\n".join([
        "# Facebookページ分析メモ",
        "",
        f"{prof['name']} は、地域猫・TNR、シビックテック、災害時のペット支援などを中心に活動記録を公開していました。",
        "イベント数は少数ですが、投稿と写真には活動説明、資料リンク、啓発コンテンツが含まれます。",
        "公開サイトではイベント中心に構成し、投稿や調査資料は関連資料ページへ集約します。",
    ]) + "\n", encoding="utf-8")
    print(f"Built archive markdown for {len(events)} events and {len(posts)} posts.")


if __name__ == "__main__":
    main()
