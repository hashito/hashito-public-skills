---
name: 02_stamp_spec_design
description: "01_stamp_concept のヒアリング結果サマリを `stamp_spec.json` に落とし込む。グリッド構造（cols × rows × cell_size）、各スタンプの cell/span/filename/description（被写体 + 表情 + ポーズ + シーン差分 + 台詞 or 省略 + 余白）、背景色／グリッド線色／許容誤差を確定し、cell 重複・グリッド外配置・キャンバスサイズの妥当性・色衝突・OpenAI セーフティ違反になりやすい表現・**全 part のシーンが同一になっていないか**・**caption の色とフォントが世界観に合っているか / 不要な場合は省略指示があるか**を機械的に検証する。承認なしに後段（API コスト発生）に進めないため、JSON 全文をユーザー提示して必ず合意を取る。これまでの試行錯誤を凝縮した `references/prompt_recipes.md` を必ず参照すること。TRIGGER: stamp_spec.json 設計、スタンプ仕様 JSON、cell/span 割付、スタンプ配置設計、line stamp spec。"
version: 1.2.0
triggers:
  - line stamp spec design
  - stamp_spec.json
  - stamp grid allocation
  - stamp spec validation
tags:
  - line
  - stamp
  - spec
  - json
  - validation
difficulty: intermediate
estimatedTime: 10
---

# 02_stamp_spec_design

## 目的

`01_stamp_concept` のヒアリング結果サマリを **`stamp_spec.json`** に落とし込み、**機械検証** を通したうえでユーザーに最終承認を取る。

承認後の JSON は後段（`03_stamp_generation` 以降）の **すべての入力** になる。`filename` は採番後に変更しない。

## 入力

- `01_stamp_concept` の出力サマリ（キャラ・画風・台詞案・色・グリッド構造）
- `references/stamp_spec_format.md`（フォーマット仕様）
- `references/sample_stamp_spec.json`（サンプル）
- **`references/prompt_recipes.md`（必読、これまでの試行錯誤を凝縮）**

## 指示

### A. JSON フォーマット

`references/stamp_spec_format.md` の規約に従う。

```json
{
  "theme": "<キャラ + 画風 + 文字表現の統合的な前置き（プロンプトに毎パーツ前置きされる）>",
  "background_color": "#00FF00",
  "background_tolerance": 40,
  "grid_line_color": "#FF00FF",
  "grid_line_tolerance": 80,
  "grid": { "cols": 2, "rows": 4, "cell_size": [512, 384] },
  "parts": [
    {
      "description": "<セル内に描かせるスタンプ 1 個の指示。被写体 + 表情 + 台詞 + 余白>",
      "cell": [0, 0],
      "span": [1, 1],
      "filename": "stamp_01_<short_label>.png"
    }
  ]
}
```

### B. 各フィールドの規則

- **theme**: 「**キャラの個体 + 画風 + 文字表現**」を 1〜3 文で記述。「全スタンプでキャラの個体・画風・文字スタイルを完全に統一する」旨を明示
- **background_color**: 被写体に登場しない色。既定 `#00FF00`
- **background_tolerance**: 30〜60。既定 40
- **grid_line_color**: 既定 `#FF00FF`
- **grid_line_tolerance**: 既定 80
- **grid**: 01 のグリッド推奨プリセットに従う（gpt-image-2 サポートサイズに一致必須）
- **parts[].description**: 被写体ポーズ・表情・台詞（""で囲まずに直接書く）・配置余白を 1〜2 文で
- **parts[].cell**: `[col, row]` 左上原点
- **parts[].span**: 省略時 `[1, 1]`
- **parts[].filename**: 英数字＋アンダースコア＋`.png`。**採番後不変**

### C. 機械検証（必須）

1. **キャンバスサイズ整合**: `cols × cell_w` × `rows × cell_h` が `1024×1024` / `1024×1536` / `1536×1024` のいずれか
2. **cell + span のグリッド内収納**: `cell[0] + span[0] <= cols`、`cell[1] + span[1] <= rows`
3. **cell の重複なし**
4. **色衝突なし**: `background_color != grid_line_color`、被写体色とも衝突なし
5. **filename 一意性 + 命名規則**
6. **description の具体性**: 被写体・表情・ポーズ・シーン差分・台詞 or 省略・余白指示が含まれているか
7. **theme の同一性指示**: 「キャラの個体・画風を完全に統一」旨が明示されているか（`prompt_recipes.md` §6）。**文字スタイルは theme で基本を決め、part 毎に上書き可能であることも明示**
8. **背景強制宣言の有無**: theme に背景色を強制するブロック（`SOLID PURE BRIGHT CHROMA-KEY ...`、`Do NOT use gray/beige/...`）があるか（`prompt_recipes.md` §1）
9. **構図ルールの明示**: theme に FRAMING RULE（耳〜あご or 頭〜足を枠内、〇〇% 占有、〇〇px 余白）があるか（`prompt_recipes.md` §2）
10. **キャプションルールの明示**: theme に CAPTION RULE（**世界観に合った色とフォント / 顔と重ねない / 各 part が個別に色・有無を上書き可能**）があるか（`prompt_recipes.md` §3）
11. **OpenAI セーフティ違反ワードの検出**: theme / description 内に `pale, hairless`、`bare feet`、`emerge from / tear through the suit`、過度な肌露出表現が含まれていないか（含まれていれば `prompt_recipes.md` §5 の書き換え推奨）
12. **シーン差分の確認**: 全 parts を見比べて「同じシーンで caption だけ違う」状態になっていないか。各 part に**ポーズ・カメラアングル・小道具・色温度のいずれか**のバリエーション指示があるか（`prompt_recipes.md` §11）
13. **caption の個別指定**: 各 part が次のいずれかを明示しているか
    - caption あり + **色とフォントスタイル**（世界観に合わせて）が description 内に書かれている
    - **`THIS STAMP HAS NO CAPTION — leave the cell text-free.`** などで caption 省略を明示している
    - 「ただ『〇〇』と書く」だけは NG。色・フォント・配置を必ず添える

### D. 承認プロセス

JSON 全文をユーザーに提示し、**明示的な OK が出るまで** `03_stamp_generation` に進ませない（API コスト発生のため）。

提示時に併記:
- グリッド占有図（テキスト）
- キャンバスサイズ
- 想定 API コスト: gpt-image-2 を 1 リクエスト（**スタンプ枚数によらず画像 1 枚分**）

### E. 既存 spec の更新

- 差分のみ提示（追加・変更・削除）
- `filename` は既存と一致させる
- `theme` を変えると全スタンプが変わるため、慎重に承認

## 出力形式

### 1. stamp_spec.json 全文

```json
{ "theme": "...", "background_color": "#00FF00", ... }
```

### 2. 検証結果サマリ

```text
[02_stamp_spec_design] 検証結果
- キャンバス: 1024×1536 (gpt-image-2 サポート: OK)
- スタンプ数: 8
- セル使用: 2×4 グリッド中 8 セル占有 / 0 セル空き
- cell 重複: なし
- 色衝突: なし (bg=#00FF00, line=#FF00FF)
- filename 重複: なし
- description の具体性: 全 8 スタンプで被写体・表情・台詞・余白指示あり
- theme 同一性指示: あり
```

### 3. ユーザー確認文

```text
stamp_spec.json を生成しました。上記内容で進めて良ければ「OK」、修正点があれば指示してください。
承認後、03_stamp_generation で gpt-image-2 を呼び出します（API コスト発生）。
```

## 注意事項

- **承認なしに後段に進めない**
- **filename は不変**: 採番後の変更は後続生成物の整合を壊す
- **キャンバスサイズの自由度なし**: gpt-image-2 サポートサイズに一致必須
- **description は AI への指示そのもの**: 被写体・表情・ポーズ・シーン差分・台詞（色・フォント）or 省略・余白まで書く
- **theme で同一性を担保**: キャラと画風は統一、文字スタイルは「基本ルール + part 毎の上書き可能」と明示
- **`prompt_recipes.md` を必ず参照**: 背景強制（§1）・構図（§2）・キャプション個別指定（§3）・セーフティ対策（§5）・キャラ同一性（§6）・シーン差分（§11）・Claude 独自処理禁止（§12）の検証済みパターンが集約されている
- **セーフティ違反 (`safety_violations=[sexual]` 等) で生成が止まると 1 リクエスト分は無駄になる**。spec 提示時点で §5 のチェックを必ず通す
- **同じシーンで caption だけ違う spec は NG**（§11）。量産時にやりがちな最大の失敗。承認前に必ず差分が入っていることを確認する
- **Claude が独自に「気を利かせて」spec の外で処理しない**（§12）。aspect 維持・色推定・自動短縮など、ユーザー指示にない方針を勝手に採用しない。失敗時は必ず spec 修正に戻る

---

# 共通ルール

あなたは LINE スタンプの仕様化担当です。

基本方針:
- 仕様 JSON は機械検証を通してから承認を取る
- API コスト発生の前段で必ず合意
- filename は採番後不変
- description は被写体 + 表情 + 台詞 + 余白で書く
- theme で同一性を担保（キャラ・画風・文字スタイル）
