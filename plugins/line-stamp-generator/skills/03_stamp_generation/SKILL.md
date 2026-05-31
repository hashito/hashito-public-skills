---
name: 03_stamp_generation
description: "承認済み stamp_spec.json をもとに OpenAI gpt-image-2 を呼び出し、グリッド状に配置された LINE スタンプ群を 1 枚の `generated.png` として生成する。1 リクエストで全スタンプ（既定 8 枚）を取るためコスト効率が良い。Python venv 準備、API キー存在確認、scripts/generate_image.py 呼び出しを行う。生成後はユーザー目視で OK 取得（NG の場合は 02 へ戻って theme / description 調整）。OpenAI セーフティで止まった場合は推測でリトライせず必ず spec を書き換える。TRIGGER: line stamp image generation、gpt-image-2 でのスタンプ生成、generated.png 生成、line stamp api call。"
version: 1.2.0
triggers:
  - line stamp generation
  - gpt-image-2 stamp call
  - generated.png stamp
tags:
  - line
  - stamp
  - generation
  - api
  - gpt-image
difficulty: intermediate
estimatedTime: 5
---

# 03_stamp_generation

## 目的

承認済み `stamp_spec.json` をもとに OpenAI `gpt-image-2` を呼び出し、**全スタンプを 1 枚のグリッド画像** `generated.png` として生成する。

## 入力

- `stamp_spec.json`（承認済み・`02_stamp_spec_design` 出力）
- 環境変数 `OPENAI_API_KEY` または `GPT_API_KEY`
- `scripts/generate_image.py`、`scripts/setup_env.sh`

## 指示

### A. 環境準備

`.venv/` が無い場合は作成。openai / Pillow / numpy / scipy を入れる。

```bash
bash plugins/line-stamp-generator/scripts/setup_env.sh
```

API キー（`OPENAI_API_KEY` または `GPT_API_KEY`）が**存在することのみ**確認する（値は表示しない）。

### B. 生成コマンド

```bash
.venv/bin/python plugins/line-stamp-generator/scripts/generate_image.py \
  --spec ./stamp_spec.json \
  --out ./generated.png \
  --model gpt-image-2 \
  --quality high
```

`--size` は省略（spec の grid から自動算出される）。

### C. プロンプト構築

`generate_image.py` がスペックから自動的にプロンプトを構築する。重要な特性:

- `theme` が**全パーツの前に前置き**される（キャラ・画風・文字スタイル統一）
- 各 `parts[].description` が `cell (col=, row=)` 指定とともに渡される
- グリッド線をマゼンタで描かせる指示が自動付与される
- 背景色をすべてのセルに塗らせる指示が付く

### D. 生成結果の目視確認

生成完了後、ユーザーに `generated.png` を確認させる:

- 全スタンプが同じキャラの個体に見えるか
- 文字（台詞）が読めるか・指定したスタイルか
- 各セルが背景色で埋まっているか（透過予定）
- グリッド線（マゼンタ）が描かれているか

NG の場合は **02_stamp_spec_design に戻り** `theme` / `description` を調整して再生成。

### E. API コスト

- gpt-image-2 quality=high: 約 $0.04 〜 $0.08 / 画像（スタンプ枚数に依存しない）
- 1 リクエストで全 N スタンプを取るため**枚数に応じて画像 1 枚分のみ**

### F. OpenAI セーフティで止まった場合

API が `safety_violations=[sexual]` / `[violence]` などで止まると、エラー `openai.BadRequestError: 400 ... moderation_blocked` が返り、画像は生成されない（**コストは発生しない**）。

対処（**厳守**）:

1. **`references/prompt_recipes.md` §5 を参照**
2. **Claude が独自に表現を弱めて再投入しない**（`prompt_recipes.md` §12）。たとえ「明らかに lying や bare のような語が原因」と分かっていても、修正版 spec をユーザーに提示して**承認を取ってから**再投入する
3. theme / description から NG ワードを排除した修正版 spec をユーザーに提示
4. 承認後に 02 → 03 のフローで再実行（API コスト再発生のため必ず承認必須）

**並列実行時の注意**: 複数 spec を同時生成すると、片方だけ止まることがある。背景タスクの完了通知を必ず確認し、止まった方は spec 修正案 → 承認 → 再投入する（独断で進めない）。

### G. 背景での並列生成

複数のスタンプセットを同時に生成する場合、`generate_image.py` を `run_in_background=true` で複数同時に投げられる。OpenAI 側のレートリミットには気をつけるが、通常の個人利用なら 2〜3 並列までは問題ない。

## 出力形式

```text
[03_stamp_generation] 開始
- 入力: stamp_spec.json
- モデル: gpt-image-2
- サイズ: 1024x1536 (grid 2x4, cell 512x384)
- 出力: generated.png
- 想定コスト: 約 $0.04-0.08 (画像 1 枚)

[generate] 完了: generated.png

確認してください:
1. キャラの個体は全スタンプで同じか
2. 文字（台詞）が読める／指定スタイルか
3. グリッド線（マゼンタ）が描かれているか
4. 背景色（緑）が各セルに塗られているか

OK なら 04_stamp_slicing へ進みます。NG なら 02 に戻って theme/description を調整します。
```

## 注意事項

- **API キーは値を表示しない**。存在確認のみ
- **再生成は 02 から**: theme / description 調整なしの単純再生成は同じ結果が出る確率が高い
- **コスト最適化**: 必ず 1 リクエストで全スタンプを取る（枚数 N に対して N 回呼ばない）
- **品質**: `--quality high` を既定。`medium` で安く済ませることも可能だが文字が読めない確率上昇

---

# 共通ルール

あなたは LINE スタンプの画像生成担当です。

基本方針:
- 必ず承認済みの stamp_spec.json を入力に使う
- API キーは存在確認のみ、値は表示しない
- 1 リクエストで全スタンプを取る
- 生成後は必ずユーザー目視確認 → NG なら 02 へ
