# FacebookページJSONエクスポートからアーカイブサイトを作る手順

このMarkdownは、空の新規リポジトリに「Facebook Pages のJSON形式エクスポートZIP」と一緒に置き、エージェントへ渡すための実行仕様書です。既存のCode for SAITAMAリポジトリやスクリプトは不要です。エージェントはこの文書を読み、必要なAstroプロジェクト、生成スクリプト、コンテンツ、画像資産、検証手順を新規作成してください。

## エージェントへの最初の命令

新しいリポジトリでは、ユーザーは次のように依頼するだけでよい。

```text
このリポジトリに置いたFacebook Pages JSONエクスポートZIPから、静的な公式アーカイブサイトを作ってください。

必ず docs/facebook-pages-json-export-site-build-guide.md を読んで、その手順に従ってください。

ZIPを解析し、Astroサイト、生成スクリプト、Markdownコンテンツ、画像マニフェスト、READMEを新規作成してください。最後に npm run build まで通し、変更点、確認結果、追加で人間が確認すべき点をまとめてください。
```

## 作るサイト

Facebookページの公開活動記録を、次の静的サイトとして再構成する。

- トップページ: 代表写真、概要、活動件数、主要イベント。
- 年表ページ: Facebookイベントと補足メモを時系列表示。
- テーマ別ページ: イベントをキーワード分類で整理。
- イベント詳細ページ: 日時、場所、説明、関連写真、Facebookイベントリンク。
- 公式情報ページ: ページ名、説明、URL、外部リンク、プロフィール情報。
- 関連資料ページ: エクスポート由来の調査Markdown、補足資料へのリンク。
- 画像一覧: 元画像、WebP画像、由来、説明、サイズを一覧化。

公開面には、ページが公開していたプロフィール、イベント、投稿、アルバム、写真、リンクだけを使う。メッセージ、端末情報、管理履歴、フォロワー個人名などは公開ページに出さない。

## 入力ファイル

新規リポジトリ直下、または `data/input/` に次を置く想定。

- `*.zip`: Facebook Pages のJSON形式エクスポート。
- `docs/facebook-pages-json-export-site-build-guide.md`: この手順書。

ZIPはFacebookの「情報をダウンロード」で、形式をJSONにして取得したものを想定する。HTML形式エクスポートの場合は、この手順ではなくJSONパーサを作り直す。

## 必要な環境

- Node.js と npm。
- Python 3。
- 画像変換用の `cwebp`。ない場合は、まず元画像コピーだけで進め、WebP変換失敗をマニフェストに記録する。
- macOSなら画像サイズ取得に `sips` を使える。環境にない場合は、Python標準だけでサイズ不明のまま進めるか、Pillowを導入できるなら使う。

ネットワークが使える場合は `npm install` でAstroを導入する。ネットワーク不可の場合は、依存関係を入れられないことをユーザーに報告し、ファイル生成まで進める。

## 最終的なディレクトリ構成

エージェントは、最低限次の構成を作る。

```text
.
├── README.md
├── package.json
├── package-lock.json
├── astro.config.mjs
├── tsconfig.json
├── data/
│   └── facebook-export/
├── docs/
│   ├── facebook-pages-json-export-site-build-guide.md
│   ├── facebook-page-archive.md
│   ├── facebook-page-analysis.md
│   └── non-event/
├── public/
│   ├── assets/
│   │   ├── images/
│   │   │   ├── original/
│   │   │   ├── webp/
│   │   │   ├── images-manifest.csv
│   │   │   ├── images-manifest.json
│   │   │   └── images-manifest.md
│   │   └── site.js
│   └── docs/
├── scripts/
│   ├── inspect_facebook_export.py
│   ├── build_image_assets.py
│   ├── build_markdown_archive.py
│   └── export_astro_content.py
└── src/
    ├── components/
    ├── content/
    │   ├── events/
    │   ├── notes/
    │   ├── pages/
    │   └── slides/
    ├── content.config.ts
    ├── layouts/
    ├── lib/
    ├── pages/
    └── styles/
```

`dist/` はビルド成果物なので、通常は直接編集しない。

## 実装の基本方針

- AstroのContent Collectionsを使い、イベント、補足メモ、スライド、固定ページをMarkdownで管理する。
- Facebookエクスポートを直接サイトから読むのではなく、PythonスクリプトでMarkdownと画像資産へ変換する。
- 生成スクリプトは何度も実行できるようにする。ただし `src/content/events/` などを上書きする場合はREADMEに明記する。
- URL slugは英数字とハイフンだけにする。
- 日本語本文は原文を尊重しつつ、余分な改行やスケジュール行だけMarkdownとして読みやすく整える。
- デザインは、活動アーカイブとして落ち着いた実用的なものにする。トップには代表写真を使い、単なる説明ページにしない。

## セットアップファイルを作る

`package.json` は最低限次の内容にする。

```json
{
  "name": "facebook-page-archive",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev --host 127.0.0.1",
    "build": "astro build",
    "preview": "astro preview --host 127.0.0.1",
    "inspect:export": "python3 scripts/inspect_facebook_export.py",
    "build:images": "python3 scripts/build_image_assets.py",
    "build:archive": "python3 scripts/build_markdown_archive.py",
    "export:content": "python3 scripts/export_astro_content.py",
    "generate": "npm run inspect:export && npm run build:images && npm run build:archive && npm run export:content"
  },
  "devDependencies": {
    "astro": "^5.0.0"
  }
}
```

`astro.config.mjs` は静的サイトの標準設定でよい。

```js
import { defineConfig } from "astro/config";

export default defineConfig({
  output: "static"
});
```

`tsconfig.json` はAstro標準のstrict設定を使う。

```json
{
  "extends": "astro/tsconfigs/strict"
}
```

## ZIPを展開する

リポジトリ内のZIPを探し、`data/facebook-export/` に展開する。

```sh
find . -maxdepth 3 -name '*.zip' -type f
mkdir -p /tmp/fb-page-export
unzip <zip-file> -d /tmp/fb-page-export
```

ZIP内にトップディレクトリが1つだけある場合と、直接 `profile_information/` などがある場合がある。最終的に次の構造へ正規化する。

```text
data/facebook-export/
├── profile_information/
├── this_profile's_activity_across_facebook/
└── connections/
```

既存の `data/facebook-export/` がある場合は、削除せず `data/facebook-export.previous/` などに退避する。

## Facebook JSONの読み取り仕様

Facebookエクスポートは文字化け風の文字列を含むことがある。Pythonでは全JSON読み込み後、次の方針で文字列補正をかける。

```py
def fix_text(value):
    if isinstance(value, str):
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    if isinstance(value, list):
        return [fix_text(item) for item in value]
    if isinstance(value, dict):
        return {fix_text(k): fix_text(v) for k, v in value.items()}
    return value
```

日時はUnix timestampとして扱い、サイト表示では日本語ページなら `YYYY.MM.DD` と `YYYY.MM.DD HH:MM` を使う。タイムゾーンは実行環境に依存しすぎないよう、必要なら `datetime.fromtimestamp()` の結果を確認する。

## `inspect_facebook_export.py` の仕様

目的: ZIP展開後のJSON構造を棚卸しし、ページ基本情報と公開可否の判断材料を `docs/non-event/` に出す。

入力:

- `data/facebook-export/**/*.json`

出力:

- `docs/non-event/00-index-and-inventory.md`
- `docs/non-event/01-profile-and-identity.md`
- `docs/non-event/02-posts-links-and-shares.md`
- `docs/non-event/03-photos-and-albums.md`
- `docs/non-event/04-comments-and-reactions.md`
- `docs/non-event/05-pages-connections-and-network.md`
- `docs/non-event/06-admin-settings-and-system-records.md`
- `docs/non-event/07-messages-and-private-records.md`
- `docs/non-event/99-overall-summary.md`

必須処理:

- 全JSONのパス、型、主要配列件数、読み込みエラーを一覧化する。
- `profile_information/profile_information/profile_information.json` からページ名、URL、ユーザー名、説明、カテゴリ、Webサイトを抽出する。
- `posts/profile_posts_*.json` が複数ある場合はすべて読む。
- `posts/album/*.json` と `posts/media/**` を一覧化する。
- メッセージ、端末、管理、同期、広告、フォロワー個人名などは「公開非推奨」と明記する。

このスクリプトは調査用であり、公開ページへ直接個人情報を書き込まない。

## `build_image_assets.py` の仕様

目的: Facebookエクスポート内の画像を公開用ディレクトリにコピーし、WebP化し、由来マニフェストを作る。

入力候補:

- `data/facebook-export/this_profile's_activity_across_facebook/posts/media/**/*`
- アルバムJSON内の `uri`
- 投稿attachment内の `media.uri`
- プロフィール更新履歴内の `media.uri`

出力:

- `public/assets/images/original/archive-image-0001.jpg`
- `public/assets/images/webp/archive-image-0001.webp`
- `public/assets/images/images-manifest.json`
- `public/assets/images/images-manifest.csv`
- `public/assets/images/images-manifest.md`

マニフェスト1件の推奨フィールド:

- `asset_id`: `archive-image-0001`
- `original_backup_path`: 元のFacebookエクスポート内パス
- `original_asset_path`: `assets/images/original/...`
- `webp_asset_path`: `assets/images/webp/...`
- `webp_status`: `ok` または失敗理由
- `width`
- `height`
- `source_type`: `album_photo`、`album_cover`、`post_attachment`、`profile_update`、`unreferenced_media_file` など
- `source_title`
- `source_date`
- `description`
- `reference_count`
- `all_references`

WebP変換に失敗しても処理は止めない。`webp_asset_path` が空の場合、サイト側は元画像を使えるようにする。

## `build_markdown_archive.py` の仕様

目的: Facebookイベント、投稿、リンク、画像参照を、人間がレビューできるMarkdown資料にする。

入力:

- `events/events.json`
- `events/events_you_hosted.json`
- `posts/profile_posts_*.json`
- `profile_information/profile_information/profile_information.json`

出力:

- `docs/facebook-page-archive.md`

必須セクション:

- 基本情報
- 抽出サマリー
- 年別イベント件数
- テーマ別イベント件数
- イベント年表
- イベント詳細
- 関連投稿
- 共有リンク
- 投稿に紐づく画像
- 公開前の注意点

イベントIDは `events_you_hosted.json` と `events.json` をタイトルで突合する。タイトル重複がある場合は日時も使い、曖昧なら注記する。

## `export_astro_content.py` の仕様

目的: JSONと画像マニフェストからAstro Content Collections用Markdownを生成する。

入力:

- `data/facebook-export/...`
- `public/assets/images/images-manifest.json`
- `docs/non-event/01-profile-and-identity.md`

出力:

- `src/content/events/*.md`
- `src/content/notes/*.md`
- `src/content/slides/*.md`
- `src/content/pages/about.md`
- `src/content/pages/research.md`
- `src/lib/site-data.json`

### イベントMarkdown frontmatter

```yaml
---
title: "イベント名"
eventId: "event-001"
date: "2020.01.01"
start: "2020.01.01 13:00"
end: "2020.01.01 17:00"
sort: 1577860800
place: "会場名 / 住所"
themes: ["テーマ名"]
themeKeys: ["theme-key"]
page: "event-2020-01-01-example.html"
image: "assets/images/webp/archive-image-0001.webp"
images: ["assets/images/webp/archive-image-0001.webp"]
fbid: "1234567890"
hasDetail: true
---
```

本文にはイベント説明文をMarkdownとして整形して入れる。説明文が短い、または空の場合は `hasDetail: false` とし、年表には出すが詳細リンクは必須にしない。

### 固定ページMarkdown

`about.md` にはプロフィール情報、外部リンク、ページ説明を入れる。`research.md` には生成した資料、画像一覧、注意点へのリンクを入れる。

### `site-data.json`

サイト全体の固定情報をJSONで出す。Astro側はここを読む。

```json
{
  "siteName": "Example Page 公式サイト",
  "shortName": "Example Page",
  "siteOrigin": "https://example.com",
  "siteDescription": "ページの説明文",
  "logoPath": "/assets/images/webp/archive-image-0001.webp",
  "defaultOgImage": "/assets/images/webp/archive-image-0001.webp",
  "facebookUrl": "https://www.facebook.com/example",
  "profileCategory": "Community"
}
```

公開URLが不明な場合は `siteOrigin` を `https://example.com` に仮置きし、READMEと最終報告に「要確認」と書く。

## テーマ分類の作り方

初期分類はキーワードベースでよい。対象ページの内容に合わせ、イベント名と説明文からテーマを推定する。

推奨初期ルール:

- `mapping`: OpenStreetMap、OSM、マッピング、地図、GIS
- `open-data`: オープンデータ、UDC、COG、データ、可視化
- `workshop`: ワークショップ、勉強会、講座、もくもく
- `hackathon`: アイデアソン、ハッカソン、開発
- `community`: Meetup、交流、定例、ミートアップ
- `disaster`: 防災、災害、ハザード、復興、支援
- `culture`: まち歩き、観光、歴史、文化、地域
- `other`: その他

分類ラベルはサイトの対象に合わせて日本語で調整する。テーマが複数当たる場合は複数付けてよい。

## 画像とイベントの対応

完全自動対応は難しいため、次の順で候補を選ぶ。

1. アルバム名または投稿タイトルがイベント名と一致、または相互に含まれる。
2. 画像の `source_date` がイベント日と同日または近い。
3. 画像説明文にイベント名、会場名、主要キーワードが含まれる。
4. 候補がない場合はイベント画像なしにする。

トップスライドは `images-manifest.md` から5〜15枚程度を選ぶ。年代、活動テーマ、写真の見栄えが偏らないようにする。人物が大きく写る写真は、公開ページで使う妥当性を慎重に判断する。

## Astro実装仕様

### Content Collections

`src/content.config.ts` に `events`、`notes`、`pages`、`slides` を定義する。

### 共通ライブラリ

`src/lib/archive.ts` で次を提供する。

- `siteData`: `src/lib/site-data.json` の読み込み。
- `siteImage(path)`: 空ならロゴ、相対パスなら `/` 付きへ正規化。
- `absoluteUrl(path)`: `siteOrigin` 付きURLにする。
- `excerpt(text, limit)`
- `schemaDateTime(text)`
- `getEvents()`
- `getNotes()`
- `getSlides()`
- `getPage(slug)`
- `groupByYear(items)`
- `themeText(themes)`

### ページ

最低限作るページ:

- `src/pages/index.astro`
- `src/pages/timeline.astro`
- `src/pages/themes.astro`
- `src/pages/about.astro`
- `src/pages/research.astro`
- `src/pages/[slug].astro`
- `src/pages/sitemap.xml.ts`
- `src/pages/robots.txt.ts`
- `src/pages/llms.txt.ts`

`[slug].astro` は `src/content/events/*.md` の `page` と一致するHTMLを生成する。`hasDetail: false` のイベントは詳細ページを作らなくてもよい。

### デザイン

`src/styles/global.css` を作る。方向性:

- 落ち着いた公式アーカイブ。
- トップのファーストビューは代表画像スライダーまたは大きな写真。
- カード角丸は控えめにする。
- 年表とテーマ別は情報を読みやすく、密度を保つ。
- スマートフォン幅でもヘッダー、カード、年表が崩れない。
- 写真がないイベントはロゴまたはプレーンなプレースホルダーを表示する。

`public/assets/site.js` には、トップスライダーの最小限のJSだけを書く。JSがなくても最初のスライドが表示されるようにする。

## 個人情報・非公開情報の扱い

公開に使いやすいもの:

- ページの公開プロフィール
- 公開イベント情報
- ページ投稿本文
- 公開アルバムと写真
- 公開リンク

原則として公開しないもの:

- メッセージ本文
- 管理者、端末、ログイン、同期、広告、内部設定に関する情報
- 個人のメールアドレス、電話番号、住所
- フォロワーやリアクションした個人の一覧
- 公開意図が確認できないスクリーンショット

判断に迷う情報は `docs/non-event/` の調査資料に留め、トップ、イベント詳細、OGP、画像スライドには使わない。

## READMEに書くこと

生成後、`README.md` に次をまとめる。

- サイトの概要。
- 入力データの場所。
- 生成スクリプトの役割。
- `npm install`、`npm run generate`、`npm run dev`、`npm run build` の使い方。
- `src/content/` と `public/assets/images/` の説明。
- 再生成時に上書きされるディレクトリ。
- 公開前の個人情報確認。
- 公開URLやCNAMEが未確定なら、その旨。

## 作業順チェックリスト

1. `git status --short --branch` で状態を確認する。
2. リポジトリ内のZIPを探す。
3. ZIPを `data/facebook-export/` に展開、正規化する。
4. `package.json`、Astro設定、基本ディレクトリを作る。
5. `npm install` を実行する。失敗したら理由を記録して、可能な範囲でファイル生成を進める。
6. `scripts/inspect_facebook_export.py` を作って実行する。
7. `docs/non-event/` を読み、対象ページ名、説明、URL、公開注意点を把握する。
8. `scripts/build_image_assets.py` を作って実行する。
9. `public/assets/images/images-manifest.md` を読み、ロゴ、代表画像、スライド候補を決める。
10. `scripts/build_markdown_archive.py` を作って実行する。
11. `scripts/export_astro_content.py` を作って実行する。
12. Astroの `src/` 一式、CSS、JS、固定ページを作る。
13. `README.md` を作る。
14. `npm run generate` を実行し、再生成できることを確認する。
15. `npm run build` を実行する。
16. 可能なら `npm run dev` を起動し、トップ、年表、テーマ別、公式情報、関連資料、代表イベント詳細を確認する。
17. `rg` で仮文字列、サンプル文字列、元テンプレート名が残っていないか確認する。
18. 公開非推奨情報が公開ページや画像スライドに出ていないか確認する。
19. 最終報告に、変更点、生成件数、ビルド結果、人間による追加確認事項を書く。

## ビルド確認

必ず実行する。

```sh
npm run build
```

できれば実行する。

```sh
npm run dev
```

確認ページ:

- `/`
- `/timeline.html`
- `/themes.html`
- `/about.html`
- `/research.html`
- 代表的なイベント詳細ページ3〜5件
- 写真がないイベントの表示
- スマートフォン幅でのトップ、年表、詳細ページ

確認項目:

- ビルドエラーがない。
- 画像が404になっていない。
- 日本語が文字化けしていない。
- ページ名、説明、OGP、構造化データが対象ページ用になっている。
- イベント詳細へのリンクが壊れていない。
- `sitemap.xml`、`robots.txt`、`llms.txt` が公開URLに合っている。

## 最終報告に含めること

- 作成したサイトの概要。
- 展開したFacebookエクスポートの場所。
- 抽出したイベント件数、投稿件数、画像件数。
- 生成した主要ファイル。
- `npm run build` の結果。
- 目視確認できたページ。
- 未確認または人間確認が必要な点。
- 公開前に見直すべき個人情報、画像、公開URL、CNAME。

## つまずきやすい点

- FacebookエクスポートのJSON構造は一定ではない。ファイルが見つからない場合は、`find data/facebook-export -name '*.json'` で実構造を見て、スクリプト側を柔軟にする。
- `profile_posts_1.json` だけとは限らない。`profile_posts_*.json` をすべて読む。
- `events_you_hosted.json` と `events.json` はタイトルだけでは誤対応する場合がある。日時も見る。
- 画像とイベントの対応は完全自動化しない。マニフェストを読んで代表画像を選ぶ工程を入れる。
- WebP変換に失敗してもサイト生成は止めない。
- 公開サイトに出す情報と、調査資料に留める情報を必ず分ける。
- 公開URLが不明な場合は仮URLのままにせず、最終報告で明確に「要確認」とする。

