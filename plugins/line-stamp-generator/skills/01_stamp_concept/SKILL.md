---
name: 01_stamp_concept
description: "LINE スタンプ生成の最初のステップ。スタンプの題材（キャラクター・画風）・スタンプ枚数（既定 8 枚）・各スタンプの台詞やシーン案・背景色／グリッド線色・グリッド構造をユーザーから引き出し、後段（02_stamp_spec_design）が JSON 化できる粒度のヒアリング結果サマリにまとめる。ヒアリング結果は会話で完結させず **`output/01_concept.md`** に永続化し、02 以降からはこのファイルを正として参照する。プリセット参照（grid / bg_color / caption_style / theme_template）も同ファイルに明記し、`references/presets.json` の名前付きセットを採用する。スタンプ間でキャラの個体・画風・文字表現が完全に統一されることを最優先する。TRIGGER: LINE スタンプのヒアリング、スタンプキャラ決め、台詞案整理、スタンプ枚数決定、creators stamp concept。"
version: 1.1.0
triggers:
  - line stamp concept
  - stamp concept hearing
  - stamp character intake
  - stamp lines intake
tags:
  - line
  - stamp
  - intake
  - hearing
  - concept
difficulty: beginner
estimatedTime: 10
---

# 01_stamp_concept

## 目的

LINE スタンプ生成のスタート地点として、ユーザーから次の 5 点を引き出す。

1. **キャラクター**（被写体・個体）— 最重要：「**1 種類で固定**」
2. **画風**（写真風／イラスト風／3D など）+ **文字表現の統一スタイル**
3. **スタンプ枚数**（既定 8 枚）と**各スタンプの台詞・シーン案**
4. **背景色／グリッド線色**（任意。未指定なら推奨を提示）
5. **グリッド構造**（cols × rows × cell_size、枚数から自動推奨）

引き出した内容は次 Skill `02_stamp_spec_design` で `stamp_spec.json` に落とし込む。本 Skill は **JSON は作らない** が、ヒアリング結果は **`output/01_concept.md`** に書き出して以後の SKILL から参照できる中間生成物にする（会話に埋もれない）。

## 入力

- ユーザーとの対話
- 既存資料（任意）: キャラのリファレンス画像、似たスタンプのスクリーンショット
- `references/presets.json`（grid / bg_color / caption_style / theme_template のプリセット名候補）

## 指示

### A. キャラクター（最重要）

「**全スタンプを通して同じ個体に見える**」が LINE スタンプの最優先要件。以下を具体化する。

- **種類は 1 種類に固定**（例: 柴犬、人間の女性、猫、ロボット）
- **個体の特徴**（毛色・体格・年齢感・服装・固有の小道具）
- **特殊加工**（例: 「目と唇が人っぽい犬」「常に眠そう」「片耳が垂れている」など固定の見た目要素）

抽象表現が来たら**具体化を促す**。「犬」だけでなく「柴犬、薄茶、子犬と成犬の中間、首輪なし」レベルまで掘る。

### B. 画風・文字表現

スタイル統一は `theme` 文の具体性で担保する。

- **画風**: 写真風（photorealistic）／フラットイラスト／水彩／3D レンダリング／手描き調 など
- **照明・色調**: 屋外日中・スタジオ撮影・暗め・パステル など
- **文字表現の統一**: フォント感（手書き／ゴシック／角丸）・色（黒／白フチ）・配置（吹き出し or 直書き）
  - LINE スタンプは**文字が入っているもの**が使いやすい（既定）

### C. スタンプ枚数と台詞案

- **既定 8 枚**。ユーザーから指定がなければ 8 枚で進める
- 各スタンプの台詞は**短く**（1〜10 文字程度）、感情・シーンが伝わるもの
  - 例: 「了解」「ありがとう」「無理」「いいね」「ごめん」「お疲れ」「おはよう」「おやすみ」
- 台詞が未指定の場合は、キャラに合う**汎用 8 種**を提案する

### D. 背景色／グリッド線色

- **背景色** (`background_color`): クロマキー抜き対象。被写体に登場しない色
  - 既定推奨: `#00FF00`（蛍光緑）
  - 緑系の被写体（カエル・植物）の場合: `#FF00FF`（マゼンタ）に切替
- **グリッド線色** (`grid_line_color`): 既定 `#FF00FF`（マゼンタ）
- **両者の衝突回避**: 背景色と線色は別

### E. グリッド構造（枚数から自動推奨）

| 枚数 | グリッド | キャンバス | セル比率 |
|---|---|---|---|
| 4 | 2×2×[512, 512] | 1024×1024 | 1:1 |
| 6 | 2×3×[512, 512] | 1024×1536 | 1:1 |
| **8（既定）** | **2×4×[512, 384]** | **1024×1536** | **横長 ≒ LINE 比率** |
| 12 | 3×4×[341, 384] | 1023×1536 | 縦長 |

### F. プリセット選定

`references/presets.json` から該当する **プリセット名** を選んで明記する（02 はこれを `stamp_spec.json` の `preset` ブロックへ写す）。

- `grid`: 枚数から自動選択（`4_stamps` / `6_stamps` / `8_stamps` / `12_stamps`）
- `bg_color`: 被写体色と衝突しないものを選ぶ（`default` / `for_green_subject` / `for_magenta_subject`）
- `grid_line_color`: 背景色と衝突しないもの（`default` / `for_magenta_subject` / `for_green_subject`）
- `caption_style`: 世界観に合うもの（`default_black` / `menpou_red` / `neon_cyan` / `gold_serif` / `comic_pop` / `none`）。**part 毎に違うものを選ぶ余地もある**
- `framing_rule`: `default` / `wide_margin` / `tight`
- `theme_template`: 真顔シュール系から始める場合は雛形を選ぶ（`deadpan_surreal_shiba` / `uncanny_human_chick` / `brooding_salaryman`）。新規世界観なら未指定可

### G. ユーザー確認 + ファイル永続化

ヒアリング結果サマリを提示し、**全 5 点 + プリセット選定が確定するまで対話を続ける**。確定したら下記の **`output/01_concept.md`** を書き出して 02 へハンドオフする。

## 出力形式

ヒアリング完了時に **`output/01_concept.md`** を書き出す（同フォーマットをユーザーへのプレビューとしても提示）:

```markdown
# LINE スタンプ ヒアリング結果

## キャラクター（個体固定）
<具体的な被写体記述。種類・体格・色・特殊加工>

## 画風・文字表現
<画風の指定（写真風／イラスト等）・照明・文字スタイル（フォント・色・配置）>

## スタンプ枚数と台詞案
- 枚数: <N>
- 台詞案:
  1. <台詞 1>
  2. <台詞 2>
  ...

## 背景色 / グリッド線色
- background_color: #XXXXXX
- grid_line_color: #XXXXXX

## グリッド構造
- cols × rows × cell_size: <例: 2×4×[512, 384]>
- キャンバス: <例: 1024×1536>

## プリセット選定（references/presets.json）
- grid: 8_stamps
- bg_color: default
- grid_line_color: default
- caption_style (既定): default_black   # part 毎に上書き可
- framing_rule: default
- theme_template: deadpan_surreal_shiba  # 雛形なし時は省略

## 確認事項
- <ユーザーに最終確認したい点>
```

## ハンドオフ（次 Skill へ）

- ファイル: `output/01_concept.md`
- 受け取る Skill: `02_stamp_spec_design`
- 02 はこのファイルを **正の入力** として読み、`stamp_spec.json` の `preset` ブロック・`grid`・`background_color`・`grid_line_color`・各 part の caption 等に展開する

## 注意事項

- **JSON 化はこの Skill では行わない**。次 Skill `02_stamp_spec_design` の責務
- **キャラの個体を 1 つに固定**することが最優先。「色違いの犬が混ざる」「同じキャラに見えない」は致命的
- **文字も画風統一の対象**。フォント感・色・配置を 1 文で `theme` に明記する
- **画風統一の核は `theme` 文の具体性**。抽象的なまま進めるとスタイルがバラつき再生成コストが膨らむ
- **背景色と被写体色の衝突に注意**（緑の被写体に `#00FF00` 背景はダメ）

---

# 共通ルール

あなたは LINE スタンプ生成のヒアリング担当です。

基本方針:
- キャラの個体は 1 つに固定（最重要）
- 画風と文字表現は theme 文に統合して具体化
- 既定枚数は 8 枚、グリッド構造は枚数から自動推奨
- 背景色／グリッド線色は生成物に登場しない色を選ぶ
- JSON 化は次 Skill の責務。本 Skill では自然文サマリに留める
