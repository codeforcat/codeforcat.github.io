---
title: "情報源管理システム運用ガイド"
description: "情報源の追加、Web補足、写真利用、ファクトチェック、作業記録の運用手順"
sourcePath: "docs/source-system.md"
---

# 情報源管理・ファクトチェック・コンテンツ更新システム

このドキュメントは、Code for CATアーカイブサイトの情報源管理システムの運用手順です。目的は、Facebookエクスポート、AI調査、Codex調査、内部情報、Web補足、写真素材を混ぜずに管理し、根拠を追跡できる状態でコンテンツへ反映することです。

## 基本方針

- 入力情報源は `sources/` に置く。
- 公開用の読み物・生成資料は `docs/` と `src/content/` に置く。
- `sources/` の情報をそのまま公開しない。台帳、ファクトチェック、要約を通して公開する。
- AI調査は「仮説」または「調査メモ」として扱い、事実の根拠にはしない。
- Facebookエクスポートと内部情報は非公開前提で扱う。
- 写真は、権利・許諾・公開可否が確認できたものだけ公開する。

## ディレクトリ構成

| パス | 役割 |
| --- | --- |
| `sources/facebook-export/` | Facebook Pages JSONエクスポートの所在、入力メモ。原本ZIPや展開データは `.gitignore` で除外。 |
| `sources/ai-deepresearch/` | Deepresearchなど他AIが作成したレポート。要ファクトチェック。 |
| `sources/codex-research/` | CodexがWeb調査・ファクトチェックしたレポート。出典URLと確認日を残す。 |
| `sources/internal/` | 今後追加する内部情報。README以外はGit管理しない。 |
| `sources/web/` | Webから補ったページメモ。自動取得または手動追加。 |
| `sources/media/` | 写真・画像候補の出典、権利、使用可否メモ。 |
| `docs/source-ledger.md` | 情報源台帳。`sources/` から自動生成。 |
| `docs/factcheck-ledger.md` | ファクトチェック台帳。`sources/` から自動生成。 |
| `worklog/content-pipeline-log.md` | 情報源スキャンと生成処理の作業記録。 |

## 通常の更新フロー

1. 情報源を `sources/` に追加する。
2. `npm run sources:index` で情報源台帳とファクトチェック台帳を更新する。
3. 必要なら `sources/` の構造化データや公開向けテンプレートを更新する。
4. `npm run generate` でFacebook抽出、画像生成、メディア公開コピー、Astroコンテンツ生成を行う。
5. `npm run build` で静的サイトを検証する。
6. 公開前確認事項を `docs/` または `worklog/` に残す。

## コンテンツをリセットして再構築する

生成済みコンテンツをいったん空にして、入力情報源から作り直す場合:

```sh
npm run reset:content
npm run generate
npm run build
```

`reset:content` が削除するもの:

- `src/content/` 配下の生成Markdown
- `.astro` のコンテンツ同期キャッシュ
- `docs/` 配下の生成レポート、台帳、Facebook棚卸し
- `public/docs/`
- `public/assets/images/` の生成画像とマニフェスト
- `public/assets/external-media/`
- `src/lib/site-data.json`

`reset:content` が残すもの:

- `sources/` 配下の入力情報源
- `data/facebook-export/` と原本ZIP
- Astroページ、レイアウト、CSS、生成スクリプト
- `docs/facebook-pages-json-export-site-build-guide.md`

外部補完年表は `sources/codex-research/*timeline-facts.json` の `timeline` 配列を入力にする。新しい年表項目を追加する場合は、スクリプトではなく情報源JSONを更新する。

## Web情報を追加する

Webページを取得して `sources/web/` に調査メモを作る場合:

```sh
npm run sources:fetch-web -- --url "https://code4cat.org/" --title "Code for CAT公式サイト"
```

ネットワーク取得せず、URLと手動要約だけを登録する場合:

```sh
npm run sources:fetch-web -- --url "https://example.com/" --title "手動確認メモ" --summary "確認できた事実。" --no-fetch
```

より軽い手動追加には次を使う:

```sh
python3 scripts/add_web_source.py --title "Code for CAT公式サイト" --url "https://code4cat.org/" --summary "団体ミッション、CatBot、Catdonの説明を確認。"
```

## 写真・画像候補を扱う

画像をダウンロードして候補登録する場合:

```sh
npm run media:download -- --title "イベント写真候補" --source-url "https://example.com/photo.jpg"
```

ダウンロード済みまたは外部URLだけ登録する場合:

```sh
python3 scripts/register_media_asset.py --title "イベント写真候補" --source-url "https://example.com/photo.jpg" --license "unknown" --permission "unknown"
```

公開サイトへコピーされる条件:

- `visibility` が `public`
- `permission` が `granted`、`public-domain`、`open-license` のいずれか
- `local_path` が存在する

公開コピーは次で実行する:

```sh
npm run media:publish
```

`npm run generate` の中でも `media:publish` は実行される。ただし条件を満たさない画像は公開されない。

## ファクトチェックの考え方

`docs/factcheck-ledger.md` は、`sources/` の入力情報源だけを読んで主要トピックの根拠数を機械的に集計する。これは最終判定ではなく、確認作業の入口である。

確認度:

| 値 | 意味 |
| --- | --- |
| `unverified` | 未確認。AI出力、未検証メモ、出典不足。 |
| `partial` | 一部確認済み。公開Webや複数資料で手がかりがある。 |
| `verified` | 信頼できる一次情報または内部確認で確認済み。 |

公開本文では、確認度に応じて表現を変える。

- `verified`: 「確認できる」「記録されている」
- `partial`: 「公開情報から確認できる範囲では」「公開記事では」
- `unverified`: 「とされる」「未確認」「公開前確認が必要」

## 内部情報の扱い

`sources/internal/` はREADME以外Git管理しない。内部情報を公開コンテンツに反映する場合は、次を確認する。

- 公開してよい情報か
- 個人名、連絡先、未公開URL、管理情報が含まれていないか
- 要約公開で十分か
- 関係者確認が必要か
- 写真や画像の使用許諾があるか

## 公開前チェック

- `dist/` にZIPや `data/facebook-export/` が含まれていない。
- `public/docs/` に非公開棚卸し資料が混ざっていない。
- `.md` 直リンクではなく `/reports/*.html` へ誘導している。
- `docs/source-ledger.md` と `docs/factcheck-ledger.md` が最新。
- `worklog/content-pipeline-log.md` に作業記録が残っている。
- 写真は許諾・ライセンス・公開可否が確認済み。

## 今後の拡張

- URLごとの取得許可リストを作る。
- Web取得結果の差分検知を入れる。
- 内部情報を公開可能な要約へ変換するレビューキューを作る。
- 写真のサムネイル生成と出典表示をサイト上に組み込む。
- ファクトチェック項目をJSON化し、年表や記事生成に直接反映する。
