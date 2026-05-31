# hashito-public-skills

[Claude Code](https://claude.com/claude-code) 向けの公開スキル集です。
Claude Code のプラグインマーケットプレイスとして利用できます。

## 収録スキル

### line-stamp-generator — LINE スタンプ生成

LINE クリエイターズスタンプ一式と申請用テキスト（日本語・英語）を
OpenAI `gpt-image-2` で一括生成するスキル群です。

コンセプトのヒアリングから申請可能な成果物までを 8 つの Skill で一気通貫に自動化します。

1. **00_line_stamp_runner** — 全工程のオーケストレータ
2. **01_stamp_concept** — コンセプトのヒアリングと仕様化
3. **02_stamp_spec_design** — `stamp_spec.json` の設計
4. **03_stamp_generation** — グリッド画像の一括生成
5. **04_stamp_slicing** — グリッド線検出による各スタンプの切り出し
6. **05_stamp_alpha_cleaning** — クロマキー透過処理
7. **06_stamp_line_resize** — LINE 規格サイズへのリサイズ
8. **07_stamp_metadata** — 申請用タイトル・説明文（日英）の生成

**出力規格**

- スタンプ本体: 最大 370×320 透過 PNG（既定 8 枚）
- メイン画像: 240×240
- トークタブ: 96×74（center-crop）
- 申請テキスト: タイトル＋説明文（各 160 字以内 / 日英）

## サンプル

スキルを実際に実行して生成したサンプルを [`samples/`](./samples/) に **スキル毎のフォルダ** で収録しています（`samples/<スキル名>/<サンプル名>/`）。

- **line-stamp-generator** → [`samples/line-stamp-generator/ai-occupied-humans`](./samples/line-stamp-generator/ai-occupied-humans/)（テーマ「AIに占領された地球人類」/ 透過 PNG 8 枚 + メイン + タブ + 申請用 metadata）

![サンプルプレビュー](./samples/line-stamp-generator/ai-occupied-humans/preview.png)

## 使い方

### プラグインとして追加

```
/plugin marketplace add hashito/hashito-public-skills
/plugin install line-stamp-generator
```

### スキルの直接実行

Claude Code で `line stamp pipeline` や「LINE スタンプを作って」などと
依頼すると `00_line_stamp_runner` が起動します。

## 必要な環境

- Python 3（依存ライブラリは `plugins/line-stamp-generator/scripts/setup_env.sh` で準備）
- OpenAI API キー — 環境変数 `OPENAI_API_KEY`（または `GPT_API_KEY`）で渡します。
  キーはコードにハードコードせず、必ず環境変数で渡してください。

> 画像生成には OpenAI API の利用料金が発生します。実行前に承認を求める設計になっています。

## ライセンス

[MIT License](./LICENSE)
