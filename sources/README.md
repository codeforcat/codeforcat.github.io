# Source Workspace

このディレクトリは、Code for CATアーカイブサイトの「入力情報源」を置く場所です。`docs/` や `src/content/` は公開・生成物として扱い、ここに置いた情報源をもとにファクトチェック、作業記録、コンテンツ更新を行います。

## ディレクトリ

| ディレクトリ | 役割 | 公開扱い |
| --- | --- | --- |
| `facebook-export/` | Facebook Pages JSONエクスポートの所在、抽出結果、公開可否メモ | 原則非公開 |
| `ai-deepresearch/` | Deepresearchなど他AIが作成した調査レポート | 要ファクトチェック |
| `codex-research/` | CodexがWeb調査・ファクトチェックしたレポート | 要出典確認 |
| `internal/` | 今後追加する内部情報、関係者メモ、未公開資料 | 非公開前提 |
| `web/` | 追加でWebから補ったページメモ、URL、引用不可の要約 | 出典次第 |
| `media/` | 使用候補写真、取得元、ライセンス、許諾メモ | 要権利確認 |

## 運用ルール

- 新しい情報源は、該当ディレクトリにMarkdownまたはJSONで追加する。
- Markdownには、できるだけ先頭にYAMLフロントマターを付ける。
- AI生成レポートは「根拠」ではなく「仮説・調査メモ」として扱う。
- Codexや人間がWebで補った情報は、URL、確認日、確認者、確認度を残す。
- 内部情報は公開しない前提で置き、公開可能な形に要約してから使う。
- 写真は取得元、ライセンス、使用可否、加工有無を必ず記録する。
- 生成済みコンテンツを作り直す場合は `npm run reset:content` の後に `npm run generate` を実行する。
- 外部補完年表は `sources/codex-research/*timeline-facts.json` の `timeline` 配列に追加する。

詳しい運用手順は `docs/source-system.md` を参照してください。

## 推奨フロントマター

```yaml
---
title: "資料タイトル"
source_type: "ai_deepresearch | codex_research | facebook_export | internal | web | media"
created_at: "2026-06-23"
checked_at: ""
author: ""
visibility: "public | private | review"
confidence: "unverified | partial | verified"
source_urls:
  - "https://example.com/"
notes: ""
---
```
