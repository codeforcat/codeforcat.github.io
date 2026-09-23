# CODE for CAT Facebook公式アーカイブ

Facebook Pages のJSON形式エクスポートから、公開プロフィール、イベント、投稿、アルバム、写真を静的なAstroサイトへ再構成したアーカイブです。

## 入力データ

- ZIP: `facebook-CODEforCAT-2026_06_22-enQ3GTXm.zip`
- 展開先: `data/facebook-export/`
- 手順書: `docs/facebook-pages-json-export-site-build-guide.md`

ZIPと `data/facebook-export/` はローカル生成用の入力データです。メッセージや管理情報など公開非推奨情報を含むため、`.gitignore` で除外し、Web公開対象には含めません。

## 生成スクリプト

- `scripts/source_pipeline.py`: `sources/` 配下の情報源を台帳化し、ファクトチェック台帳と作業記録を更新します。
- `scripts/reset_generated_content.py`: 生成済みコンテンツを削除し、`sources/` とFacebook抽出データから再構築できる状態に戻します。
- `scripts/inspect_facebook_export.py`: JSON棚卸しと公開非推奨情報の整理を `docs/non-event/` に出力します。
- `scripts/build_image_assets.py`: 画像を `public/assets/images/original/` にコピーし、WebPとマニフェストを生成します。
- `scripts/build_markdown_archive.py`: 人間確認用のMarkdown資料を生成します。
- `scripts/export_astro_content.py`: Astro Content Collections用Markdownと `src/lib/site-data.json` を生成します。
- `scripts/add_web_source.py`: Webで補った情報源メモを `sources/web/` に追加します。
- `scripts/fetch_web_source.py`: Webページを取得し、要約つきの情報源メモを `sources/web/` に追加します。
- `scripts/register_media_asset.py`: 使用候補写真の権利・出典メモを `sources/media/media-manifest.json` に登録します。
- `scripts/download_media_asset.py`: 画像を `sources/media/downloads/` にダウンロードし、権利メモを登録します。
- `scripts/publish_media_assets.py`: 使用許可済み画像だけを `public/assets/external-media/` にコピーします。

## 使い方

```sh
npm install
npm run generate
npm run dev
npm run build
```

`npm run generate` は `src/content/events/`、`src/content/notes/`、`src/content/pages/`、`src/content/slides/`、`src/lib/site-data.json`、`public/docs/`、`public/assets/images/` を再生成または上書きします。

生成済みコンテンツをいったん空にして、入力情報源から作り直す場合:

```sh
npm run reset:content
npm run generate
npm run build
```

`reset:content` は `sources/`、アプリケーションコード、Facebookエクスポート原本には触れません。削除対象は `src/content/`、生成済み `docs/`、`public/docs/`、生成画像、`src/lib/site-data.json` などの再生成可能なファイルです。

## 情報源管理

入力情報源は `sources/` に分けて保存します。Facebookエクスポート、他AIのDeepresearch、CodexのWeb調査、内部情報、Web補足、使用候補写真を分け、`npm run sources:index` で `docs/source-ledger.md`、`docs/factcheck-ledger.md`、`worklog/content-pipeline-log.md` を更新します。

内部情報は `sources/internal/` に置きます。このディレクトリはREADME以外を `.gitignore` で除外しています。

詳しい運用手順は `docs/source-system.md` と `/reports/source-system.html` にまとめています。

外部補完年表は `sources/codex-research/*timeline-facts.json` の `timeline` 配列から生成します。スクリプト内に年表本文を固定せず、根拠ファイルを更新してから `npm run generate` で反映します。

Web情報を追加する例:

```sh
python3 scripts/add_web_source.py --title "Code for CAT公式サイト" --url "https://code4cat.org/" --summary "団体ミッション、CatBot、Catdonの説明を確認。"
```

Webページを取得して追加する例:

```sh
npm run sources:fetch-web -- --url "https://code4cat.org/" --title "Code for CAT公式サイト"
```

写真候補を登録する例:

```sh
python3 scripts/register_media_asset.py --title "イベント写真候補" --source-url "https://example.com/photo.jpg" --license "unknown" --permission "unknown"
```

画像をダウンロードして候補登録する例:

```sh
npm run media:download -- --title "イベント写真候補" --source-url "https://example.com/photo.jpg"
```

## サイト構成

- `/`: 代表写真、概要、活動件数、主要イベント。
- `/timeline.html`: Facebookイベントの年表。
- `/themes.html`: キーワード分類によるテーマ別整理。
- `/analysis.html`: シビックテック、動物福祉、社会的包摂の観点からの分析。
- `/about.html`: ページ名、説明、URL、外部リンク、プロフィール情報。
- `/research.html`: 整形済み生成資料、画像一覧、公開前注意点への入口。
- `/reports/*.html`: 生成資料を読みやすく表示するページ。
- `/reports/code-for-cat-public-web-timeline-factcheck.html`: 公開Web調査で補った初期・空白期の活動と情報源。
- `/*.html`: イベント詳細ページ。

## 公開前確認

公開サイトにはメッセージ、端末情報、管理履歴、フォロワー個人名、リアクション個人名を掲載しない方針です。公開前に、人物が大きく写る写真、非公開意図が不明な画像、外部リンク、イベント本文中の個人情報を人間が確認してください。

`src/lib/site-data.json` の `siteOrigin` は `https://example.com` の仮値です。公開URLやCNAMEが決まったら更新してください。
