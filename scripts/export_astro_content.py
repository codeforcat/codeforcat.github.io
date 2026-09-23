from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from fb_archive_common import DOCS_DIR, IMAGE_DIR, ROOT, classify, clean_markdown, load_events, load_posts, profile, slugify, write_json, yaml_list, yaml_string


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def choose_images(event: dict, manifest: list[dict]) -> list[str]:
    title = event["title"].lower()
    event_date = event["date"]
    scored = []
    for row in manifest:
        score = 0
        text = f"{row.get('source_title','')} {row.get('description','')}".lower()
        if title and (title in text or any(part and part in text for part in re.split(r"\s+", title) if len(part) > 3)):
            score += 5
        if event_date and row.get("source_date") == event_date:
            score += 4
        if event_date[:4] and row.get("source_date", "").startswith(event_date[:4]):
            score += 1
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], item[1].get("asset_id", "")))
    return [(row.get("webp_asset_path") or row.get("original_asset_path")) for _, row in scored[:6]]


def post_image(post: dict, manifest_by_source: dict[str, dict]) -> str:
    for attachment in post.get("attachments", []):
        for item in attachment.get("data", []):
            media = item.get("media", {}) if isinstance(item, dict) else {}
            row = manifest_by_source.get(media.get("uri", ""))
            if row:
                return row.get("webp_asset_path") or row.get("original_asset_path") or ""
    return ""


def post_title(post: dict, index: int) -> str:
    body = clean_markdown(post.get("body", ""))
    source_title = post.get("title", "")
    candidates: list[str] = []
    for line in body.splitlines():
        line = re.sub(r"https?://\S+", "", line).strip(" \t-・●○■□★☆=─—")
        if not line:
            continue
        if not candidates and "ステッカー" in line:
            return "ステッカー配布のお知らせ"
        bracket = re.match(r"^[【\[]([^】\]]{3,40})[】\]]", line)
        if bracket:
            candidates.append(bracket.group(1))
        candidates.append(line)
        if len(candidates) >= 4:
            break
    if source_title:
        cleaned_source = source_title.replace("CODE for CATさんが", "").replace("CODE for CATが", "")
        cleaned_source = cleaned_source.replace("を投稿しました。", "").replace("投稿しました。", "")
        cleaned_source = cleaned_source.replace("写真を追加しました", "写真を追加")
        candidates.append(cleaned_source)
    for candidate in candidates:
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if 4 <= len(candidate) <= 52:
            return candidate
        if len(candidate) > 52:
            return candidate[:49] + "..."
    return f"投稿記録 {index:02d}"


def write_markdown(path: Path, frontmatter: list[str], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + "\n".join(frontmatter) + "\n---\n\n" + body.strip() + "\n", encoding="utf-8")


def write_report(content_root: Path, slug: str, title: str, description: str, source: Path) -> None:
    body = source.read_text(encoding="utf-8") if source.exists() else "資料を生成できませんでした。"
    body = re.sub(r"^---\n.*?\n---\n", "", body, flags=re.S).strip()
    body = body.replace(
        "画像一覧は `public/assets/images/images-manifest.md` を参照してください。",
        "画像一覧は [画像マニフェスト](/reports/images-manifest.html) を参照してください。",
    )
    write_markdown(content_root / "reports" / f"{slug}.md", [
        f"title: {yaml_string(title)}",
        f"description: {yaml_string(description)}",
        f"sourcePath: {yaml_string(str(source.relative_to(ROOT)) if source.exists() else '')}",
    ], body)


def load_external_timeline() -> list[dict]:
    items: list[dict] = []
    for path in sorted((ROOT / "sources").rglob("*.json")):
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


def write_external_timeline(content_root: Path) -> None:
    for item in load_external_timeline():
        write_markdown(content_root / "external" / f"{item['slug']}.md", [
            f"title: {yaml_string(item['title'])}",
            f"date: {yaml_string(item['date'])}",
            f"displayDate: {yaml_string(item['displayDate'])}",
            f"sort: {item['sort']}",
            f"category: {yaml_string(item['category'])}",
            f"confidence: {yaml_string(item['confidence'])}",
            f"sourceLabel: {yaml_string(item['sourceLabel'])}",
            f"sourceUrl: {yaml_string(item['sourceUrl'])}",
            f"sourceUrls: {yaml_list([item['sourceUrl']] if item['sourceUrl'] else [])}",
        ], item["body"])


def main() -> None:
    content_root = ROOT / "src" / "content"
    for name in ["events", "external", "notes", "pages", "reports", "slides"]:
        reset_dir(content_root / name)

    manifest_path = IMAGE_DIR / "images-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    manifest_by_source = {row.get("original_backup_path", ""): row for row in manifest}
    prof = profile()
    events = load_events()
    posts = load_posts()

    used_slugs: set[str] = set()
    exported_events = []
    for index, event in enumerate(events, 1):
        theme_keys, themes = classify(event["title"], event["description"])
        slug_base = f"{event['date'].replace('.', '-')}-{slugify(event['title'], event['id'])}"
        slug = slug_base[:72].strip("-") or event["id"]
        suffix = 2
        while slug in used_slugs:
            slug = f"{slug_base[:65]}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
        page = f"{slug}.html"
        images = choose_images(event, manifest)
        has_detail = len(event["description"]) >= 20
        frontmatter = [
            f"title: {yaml_string(event['title'])}",
            f"eventId: {yaml_string(event['id'])}",
            f"date: {yaml_string(event['date'])}",
            f"start: {yaml_string(event['start'])}",
            f"end: {yaml_string(event['end'])}",
            f"sort: {int(event['start_timestamp'] or 0)}",
            f"place: {yaml_string(event['place'])}",
            f"themes: {yaml_list(themes)}",
            f"themeKeys: {yaml_list(theme_keys)}",
            f"page: {yaml_string(page)}",
            f"image: {yaml_string(images[0] if images else '')}",
            f"images: {yaml_list(images)}",
            f"fbid: {yaml_string(event['fbid'])}",
            f"hasDetail: {'true' if has_detail else 'false'}",
        ]
        write_markdown(content_root / "events" / f"{slug}.md", frontmatter, event["description"] or "説明文はありません。")
        exported_events.append({**event, "slug": slug, "page": page, "themes": themes, "themeKeys": theme_keys, "images": images})

    for index, post in enumerate(posts, 1):
        title = post_title(post, index)
        slug = f"post-{index:02d}"
        image = post_image(post, manifest_by_source)
        write_markdown(content_root / "notes" / f"{slug}.md", [
            f"title: {yaml_string(title)}",
            f"date: {yaml_string(post['date'])}",
            f"sort: {int(post['timestamp'] or 0)}",
            'kind: "post"',
            f"image: {yaml_string(image)}",
        ], post["body"] or title)

    top_images = [row for row in manifest if row.get("webp_asset_path") or row.get("original_asset_path")]
    top_images = sorted(top_images, key=lambda row: (row.get("source_type") != "album_photo", row.get("source_date", "")))
    for index, row in enumerate(top_images[:12], 1):
        image = row.get("webp_asset_path") or row.get("original_asset_path")
        write_markdown(content_root / "slides" / f"slide-{index:02d}.md", [
            f"title: {yaml_string(row.get('source_title') or prof['name'])}",
            f"image: {yaml_string(image)}",
            f"alt: {yaml_string(row.get('description') or row.get('source_title') or prof['name'])}",
            f"sort: {index}",
        ], row.get("description") or row.get("source_title") or "")

    write_external_timeline(content_root)

    about_body = "\n".join([
        f"{prof['description']}",
        "",
        "Code for CATは、地理的な範囲ではなく「猫と人の共生」というテーマを軸に集まるシビックテック・コミュニティです。地域猫を単なる管理対象ではなく、地域の関係性を見直すための資産として捉え、テクノロジー、参加型ワークショップ、オンラインコミュニティを組み合わせて活動してきました。",
        "",
        "公開Web調査では、Code for Japanの公式サイト上でCode for CATが地域型ではなくテーマ型・地域横断型のCode forコミュニティとして紹介されていること、CatBot、Catdon、ライタソン、NECOLOなどの活動記録がMediumやイベントページに残っていることが確認できます。",
        "",
        "## 活動の視点",
        "- テーマ型ブリゲードとして、地域を越えて猫好き、エンジニア、デザイナー、行政関係者、保護活動者が参加しやすい場を作る。",
        "- CatBot、ライタソン、Catdon、NECOLO、マイニャンバー構想などを通じて、猫に関する知識共有と合意形成を支える。",
        "- 「猫が好き」「猫を助けたい」という前向きな感情を、市民参加と技術活用の入口にする。",
        "- 2018〜2020年の濃い活動記録に加え、2025年にはPodcastで生成AI・猫エージェントに関する近況も確認できる。",
        "",
        "## 主な公開プロジェクト",
        "- CatBot: 猫に関する疑問に答えるLINEベースのチャットボット。2019年にアルファ版、2020年にベータ版公開の流れが確認できます。",
        "- ライタソン: 市民の疑問や経験をQ&Aデータとして整理する参加型ワークショップ。CatBotの知識基盤づくりと結びついています。",
        "- Catdon: 猫好き向けMastodonインスタンス。小さく安心できるテーマ型コミュニティとして位置づけられます。",
        "- NECOLO: 飼い主、猫、ネコシッターをつなぐ遠隔見守り・遊びのプロトタイプとして語られています。",
        "",
        "## 公式プロフィール",
        f"- ページ名: {prof['name']}",
        f"- Facebook: {prof['url']}",
        f"- カテゴリ: {prof['category']}",
        f"- Webサイト: {', '.join(prof['websites']) or '未記録'}",
        f"- 登録日時: {prof['registered']}",
    ])
    write_markdown(content_root / "pages" / "about.md", [
        f"title: {yaml_string('公式情報')}",
        f"description: {yaml_string(prof['description'])}",
    ], about_body)

    analysis_body = "\n".join([
        "Code for CATの公開記録は、イベントや投稿の時系列だけでなく、シビックテックが動物福祉と交わった実践の記録として読むことができます。",
        "",
        "## テーマ型コミュニティとしての特徴",
        "一般的なCode for X型コミュニティは、自治体や地域を単位に活動することが多い一方、Code for CATは「猫」という関心と社会課題を中心に人が集まります。この形により、居住地に縛られず、エンジニア、デザイナー、データサイエンティスト、保護活動者、行政関係者が参加しやすくなっています。",
        "",
        "## 地域猫を資産として見る",
        "Code for CATの重要な視点は、地域猫を迷惑や管理の対象としてだけ扱わないことです。餌やり、糞尿、鳴き声をめぐる対立は、猫の問題であると同時に、住民同士の合意形成や相互理解の問題でもあります。猫に関する正しい知識を共有し、人と猫が共生する仕組みを作ることは、地域コミュニティの分断を和らげる市民的な取り組みでもあります。",
        "",
        "## CatBotとライタソン",
        "CatBotは、猫に関する疑問にLINE上で答えるチャットボットです。2019年2月22日にアルファ版、2020年2月22日にベータ版が公開された流れが確認できます。Microsoft AzureのQnA MakerやLogic Appsのようなクラウドサービスを組み合わせることで、専門的なコードだけに依存しない運用が目指されました。FAQのもとになる問いは、ライタソンによって市民から集められました。付箋と模造紙を使い、参加者が猫に関する困りごとや経験を書き出すことで、生活知がデータとして整理されていきます。",
        "",
        "## ライタソンプラットフォーム",
        "2020年末の公開記事では、CatBotのQ&Aコンテンツを維持管理し、Dialogflowなどへ書き出すためのライタソンプラットフォームが議論されています。模造紙、付箋、Googleフォーム、スプレッドシート、QnA Maker、Zoom、Miroといった道具をまたぎながら、市民参加型の知識整理をどうデジタル化するかが課題になっていました。この論点は、猫に限らず地域ガイド、観光、子育て、NPO支援にも応用できます。",
        "",
        "## 安心できる小さな場",
        "Catdonは、Mastodonを基盤とした猫好き向けの分散型SNSです。2017年4月19日に立ち上げられ、Code for CAT運営という位置づけになったことが公開記事から確認できます。大規模SNSのアルゴリズムから距離を置き、猫という共通の関心を持つ人が安心して集まれる場として設計されています。小さなテーマ型ネットワークは、シビックテックに必要な心理的安全性を支える基盤にもなります。",
        "",
        "## 活動を支える人材",
        "Code for CATは、設立発起人、Webディレクター、ファシリテーター、データサイエンティスト、エンジニア、コミュニティビルダーなど、多様な専門性を持つ人々によって支えられてきました。個人の関心と専門性が重なり合うことで、義務感だけでは続きにくい市民活動に、楽しさと持続性が生まれています。",
        "",
        "## 近年の公開情報",
        "公式Mediumは2020年12月を最後に更新が止まっているように見えます。一方で、2025年公開のポッドキャストでは、生成AIによる猫エージェント開発や猫との対話など、2025年度版の取り組みが紹介されています。公開発信の場が、ブログから音声や雑談型コンテンツへ移っている可能性があります。",
        "",
        "## アーカイブ上の課題",
        "Code for CATの記録は、公式サイト、Medium、Facebook、Qiita、CAMPFIRE、Catdon、Podcastなどに分散しています。このサイトはFacebookページの公開記録を軸に再構成していますが、団体紹介としてさらに強くするには、活動年表、主要プロジェクト、成果物、現在の活動状況、連絡先を横断的に整理することが重要です。",
        "",
        "## 詳細資料",
        "- [シビックテックと動物福祉の融合](/reports/code-for-cat-civic-tech-animal-welfare-analysis.html)",
        "- [公開Web調査による活動年表とファクトチェック](/reports/code-for-cat-public-web-timeline-factcheck.html)",
    ])
    write_markdown(content_root / "pages" / "analysis.md", [
        f"title: {yaml_string('分析レポート')}",
        f"description: {yaml_string('Code for CATをシビックテック、動物福祉、社会的包摂の視点から読み解く')}",
    ], analysis_body)

    research_body = "\n".join([
        "このページは、公開記録から生成した調査資料への入口です。各資料はMarkdownへの直リンクではなく、読みやすく整形したページとして表示します。",
        "",
        "Facebookページのエクスポートだけでは、公式サイト、Medium、Code for Japan、Qiita、CAMPFIRE、Catdon、Podcastに分散した活動の全体像までは見えません。そのため、今回の調査結果を「シビックテックと動物福祉の融合」レポートに統合し、2015年の発足経緯から2025年の公開音声発信までを補っています。",
        "",
        "`docs/non-event/` の棚卸し資料は、メッセージ、端末、管理履歴、フォロワー個人名、リアクション個人名などの公開非推奨情報を含みうるため、公開コピーから除外しています。",
    ])
    write_markdown(content_root / "pages" / "research.md", [
        f"title: {yaml_string('関連資料')}",
        f"description: {yaml_string('生成資料と公開前確認事項')}",
    ], research_body)

    logo = ""
    for row in manifest:
        if "profile" in row.get("original_backup_path", "") or "purofiru" in row.get("original_backup_path", ""):
            logo = row.get("webp_asset_path") or row.get("original_asset_path")
            break
    default_image = (top_images[0].get("webp_asset_path") or top_images[0].get("original_asset_path")) if top_images else logo
    write_json(ROOT / "src" / "lib" / "site-data.json", {
        "siteName": f"{prof['name']} 公式アーカイブ",
        "shortName": prof["name"],
        "siteOrigin": "https://code4cat.org",
        "siteDescription": prof["description"],
        "logoPath": f"/{logo}" if logo else f"/{default_image}",
        "defaultOgImage": f"/{default_image}" if default_image else "",
        "facebookUrl": prof["url"],
        "profileCategory": prof["category"],
        "eventCount": len(events),
        "postCount": len(posts),
        "imageCount": len(manifest),
        "siteOriginNeedsReview": False,
    })

    public_docs = ROOT / "public" / "docs"
    if public_docs.exists():
        shutil.rmtree(public_docs)
    public_docs.mkdir(parents=True, exist_ok=True)
    for name in [
        "facebook-page-archive.md",
        "facebook-page-analysis.md",
        "code-for-cat-civic-tech-animal-welfare-analysis.md",
        "code-for-cat-public-web-timeline-factcheck.md",
        "source-ledger.md",
        "factcheck-ledger.md",
        "source-system.md",
    ]:
        source = DOCS_DIR / name
        if source.exists():
            shutil.copy2(source, public_docs / name)
    report_specs = [
        ("facebook-page-archive", "Facebookページ公開アーカイブ", "イベント、投稿、画像を公開記録として整理した資料", DOCS_DIR / "facebook-page-archive.md"),
        ("facebook-page-analysis", "Facebookページ分析メモ", "Facebookエクスポートから読み取れる活動傾向と公開前確認事項", DOCS_DIR / "facebook-page-analysis.md"),
        ("code-for-cat-civic-tech-animal-welfare-analysis", "シビックテックと動物福祉の融合", "Code for CATをテーマ型コミュニティと社会的包摂の視点から分析した資料", DOCS_DIR / "code-for-cat-civic-tech-animal-welfare-analysis.md"),
        ("code-for-cat-public-web-timeline-factcheck", "公開Web調査による活動年表とファクトチェック", "Facebook外で確認した初期・空白期の活動と情報源を整理した資料", DOCS_DIR / "code-for-cat-public-web-timeline-factcheck.md"),
        ("source-ledger", "情報源台帳", "入力情報源の分類、公開扱い、確認度、所在を整理した台帳", DOCS_DIR / "source-ledger.md"),
        ("factcheck-ledger", "ファクトチェック台帳", "sources配下の入力情報源だけをもとに主要トピックの根拠数と確認状態を整理した台帳", DOCS_DIR / "factcheck-ledger.md"),
        ("source-system", "情報源管理システム運用ガイド", "情報源の追加、Web補足、写真利用、ファクトチェック、作業記録の運用手順", DOCS_DIR / "source-system.md"),
        ("images-manifest", "画像マニフェスト", "公開画像のファイル名、出典、説明を確認するための一覧", IMAGE_DIR / "images-manifest.md"),
    ]
    for slug, title, description, source in report_specs:
        write_report(content_root, slug, title, description, source)
    print(f"Exported {len(events)} events, {len(posts)} notes, and {min(len(top_images), 12)} slides.")


if __name__ == "__main__":
    main()
