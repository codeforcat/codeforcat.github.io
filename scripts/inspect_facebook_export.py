from __future__ import annotations

from collections import Counter
from pathlib import Path

from fb_archive_common import EXPORT_DIR, NON_EVENT_DIR, fix_text, load_posts, profile, read_json


def summarize_json(path: Path) -> tuple[str, str]:
    try:
        data = read_json(path)
    except Exception as exc:
        return "error", str(exc)
    if isinstance(data, list):
        return "list", f"{len(data)} items"
    if isinstance(data, dict):
        keys = ", ".join(list(data.keys())[:8])
        counts = []
        for key, value in data.items():
            if isinstance(value, list):
                counts.append(f"{key}: {len(value)}")
        return "dict", f"keys: {keys}; " + "; ".join(counts[:6])
    return type(data).__name__, ""


def write(name: str, title: str, body: str) -> None:
    NON_EVENT_DIR.mkdir(parents=True, exist_ok=True)
    (NON_EVENT_DIR / name).write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def main() -> None:
    json_paths = sorted(EXPORT_DIR.glob("**/*.json"))
    rows = []
    type_counts = Counter()
    for path in json_paths:
        kind, summary = summarize_json(path)
        type_counts[kind] += 1
        rows.append(f"| `{path.relative_to(EXPORT_DIR)}` | {kind} | {summary} |")

    prof = profile()
    posts = load_posts()
    media_files = sorted((EXPORT_DIR / "this_profile's_activity_across_facebook" / "posts" / "media").glob("**/*"))
    media_files = [path for path in media_files if path.is_file()]
    albums = sorted((EXPORT_DIR / "this_profile's_activity_across_facebook" / "posts" / "album").glob("*.json"))

    inventory = [
        f"- JSONファイル: {len(json_paths)}件",
        f"- 投稿: {len(posts)}件",
        f"- アルバムJSON: {len(albums)}件",
        f"- メディアファイル: {len(media_files)}件",
        "",
        "| パス | 型 | 概要 |",
        "| --- | --- | --- |",
        *rows,
    ]
    write("00-index-and-inventory.md", "JSON棚卸し", "\n".join(inventory))

    identity = [
        f"- ページ名: {prof['name']}",
        f"- ユーザー名: {prof['username']}",
        f"- Facebook URL: {prof['url']}",
        f"- カテゴリ: {prof['category']}",
        f"- 説明: {prof['description']}",
        f"- Webサイト: {', '.join(prof['websites']) or 'なし'}",
        f"- 登録日時: {prof['registered']}",
        "",
        "公開ページへ利用しやすい情報です。ただし電話番号、メールアドレス、端末情報は公開対象に含めません。",
    ]
    write("01-profile-and-identity.md", "プロフィールと公式情報", "\n".join(identity))

    post_lines = [f"- 投稿件数: {len(posts)}件", "", "## 直近投稿サンプル"]
    for item in posts[:10]:
        post_lines.append(f"- {item['date']} {item['title'] or item['body'][:60]}")
    write("02-posts-links-and-shares.md", "投稿・リンク・シェア", "\n".join(post_lines))

    photo_lines = [f"- アルバムJSON: {len(albums)}件", f"- メディアファイル: {len(media_files)}件", "", "## アルバム"]
    for path in albums:
        data = read_json(path)
        photo_lines.append(f"- {data.get('name', path.stem)}: {len(data.get('photos', []))}枚")
    write("03-photos-and-albums.md", "写真とアルバム", "\n".join(photo_lines))

    write("04-comments-and-reactions.md", "コメントとリアクション", "リアクションした個人名やコメント投稿者情報は公開非推奨です。必要な統計確認に留めます。")
    write("05-pages-connections-and-network.md", "ページ接続とネットワーク", "フォロワー一覧や接続情報は公開非推奨です。公開サイトには掲載しません。")
    write("06-admin-settings-and-system-records.md", "管理・端末・システム記録", "管理者、端末、同期、ナビゲーション履歴、広告、内部設定は公開非推奨です。")
    write("07-messages-and-private-records.md", "メッセージと私的記録", "メッセージ本文、添付ファイル、相手名は公開非推奨です。公開サイトには掲載しません。")
    write("99-overall-summary.md", "全体サマリー", "\n".join([
        f"{prof['name']} のFacebook Pages JSONエクスポートを棚卸ししました。",
        "公開サイトではプロフィール、イベント、投稿、アルバム、写真、外部リンクのみを利用します。",
        "メッセージ、管理記録、端末情報、フォロワー個人名、リアクション個人名は公開対象外です。",
    ]))

    print(f"Inspected {len(json_paths)} JSON files.")


if __name__ == "__main__":
    main()
