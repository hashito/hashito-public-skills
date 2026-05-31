# stamp_spec.json フォーマット

LINE スタンプ生成パイプラインの**入力 JSON 仕様**。

`02_stamp_spec_design` で生成し、`03_stamp_generation` 以降の全ステップが**この同じ JSON を入力に取る**。`design-parts-generator/parts_spec.json` と互換のあるグリッドベース構造を採用しているため、共通スクリプト（generate_image.py / slice_image.py / clean_alpha.py）はそのまま再利用できる。

## 構造

```json
{
  "theme": "<キャラクター・画風・文字表現の指示。プロンプト前置きされる>",
  "background_color": "#00FF00",
  "background_tolerance": 40,
  "grid_line_color": "#FF00FF",
  "grid_line_tolerance": 80,
  "grid": {
    "cols": 2,
    "rows": 4,
    "cell_size": [512, 384]
  },
  "parts": [
    {
      "description": "<セル内に描かせるスタンプ 1 個の指示。被写体 + 表情 + 台詞 + 余白>",
      "cell": [0, 0],
      "span": [1, 1],
      "filename": "stamp_01.png"
    }
  ]
}
```

## フィールド

| キー | 役割 | 推奨値 |
|---|---|---|
| `theme` | キャラ・画風・文字スタイル統一の核となる前置き。全パーツ生成プロンプトに前置きされる | 1〜3 文の具体的記述 |
| `background_color` | クロマキー抜き対象の色。被写体に登場しない色 | `#00FF00`（緑系被写体があれば `#FF00FF`） |
| `background_tolerance` | クロマキー時の RGB 距離許容 | 30〜60（既定 40） |
| `grid_line_color` | AI に描かせる区切り線色 | `#FF00FF`（背景・被写体に出てこない色） |
| `grid_line_tolerance` | 区切り線検出時の RGB 距離許容 | 既定 80 |
| `grid.cols` × `grid.rows` × `grid.cell_size` | キャンバス＝ `cols × cell_w` × `rows × cell_h`。gpt-image-2 サポートサイズに一致必須 | 後述 |
| `parts[].description` | AI が読むスタンプ 1 個の描画指示 | 被写体・表情・台詞・配置・余白・**caption の色とフォントスタイル**・**caption 省略時はその旨**を文で書く |
| `parts[].cell` | 配置セル `[col, row]`（0 起点） | グリッド内 |
| `parts[].span` | 占有セル数 `[span_col, span_row]` | 既定 `[1, 1]` |
| `parts[].filename` | 出力ファイル名（英数字＋アンダースコア＋`.png`） | 採番後不変 |

## グリッド構成プリセット

LINE スタンプは **横長（370×320 ≒ 1.156:1）** が標準だが、縦長スタンプも許容される。生成枚数とキャンバスサイズで以下プリセットを使う。

| 枚数 | グリッド | キャンバス | セル比率 | 用途 |
|---|---|---|---|---|
| 4 | 2 × 2 × [512, 512] | 1024 × 1024 | 1:1 正方 | 少数の核スタンプ |
| 6 | 2 × 3 × [512, 512] | 1024 × 1536 | 1:1 正方 | バランス型 |
| **8（既定）** | **2 × 4 × [512, 384]** | **1024 × 1536** | **1.33:1 横長** | **LINE 規格に近い** |
| 12 | 3 × 4 × [341, 384] | 1023 × 1536 | 0.89:1 縦長 | 大量量産（解像度は落ちる） |

gpt-image-2 のサポートサイズ: `1024×1024`、`1024×1536`、`1536×1024`。**ぴったり一致するよう cell_size を選ぶ**。

## description の書き方

各スタンプは「**被写体 + 表情・ポーズ + シーン差分 + 台詞（色・フォント・配置 / または『無し』）+ セル内配置・余白**」を 1〜3 文で書く。

例（caption あり・色指定あり）:
```text
中央やや左に座った柴犬が少し首をかしげる。完全な真顔。
セル上部に手書き風の太い黒文字で日本語の台詞『とりあえず…』を白フチで添える。
セル境界に 30px の余白を残す。
```

例（世界観に合わせて色変更）:
```text
夜の街角に立つ被写体、ネオン看板の青いグロー。
セル下部にネオンピンク色の太めゴシック日本語『見えてます？』、黒のソフトドロップシャドウ。
60px+ margin to cell edges.
```

例（caption を **省略**）:
```text
被写体が深くうなだれて完全に沈み込んだポーズ。表情と空気感だけで意味が伝わるため、
THIS STAMP HAS NO CAPTION — leave the cell text-free.
セル境界に 60px の余白。
```

ポイント:

- **被写体は theme で 1 種類に固定**（毎回違うキャラが出るとスタンプにならない）
- **台詞は description ごとに変える**（スタンプの個性）
- **シーン差分（ポーズ・小道具・カメラアングル）も description で必ず変える** — 全 8 セルが「同じシーン + 文字違い」にならないよう `prompt_recipes.md` §11 を参照
- **caption の色・フォントは世界観に合わせて part 毎に上書き可能**（theme には基本ルールだけ書く）。`prompt_recipes.md` §3 を参照
- **caption を **省略** したい場合は description に明示**: `THIS STAMP HAS NO CAPTION — leave the cell text-free.` のような明確な指示を入れる（曖昧にしない）
- **余白指示を必ず含める**（境界侵食を防ぐ）

## 機械検証

`02_stamp_spec_design` 出力前に必ず以下を満たすこと。

1. `cols × cell_w == 1024 or 1536` かつ `rows × cell_h == 1024 or 1536`
2. 全 `parts` の `cell + span` がグリッド内
3. 全 `parts` の占有セルが他と重複しない
4. `background_color != grid_line_color`、かつ被写体色と衝突しない
5. `filename` が全て一意かつ英数字＋アンダースコア＋`.png`
6. `description` がスタンプ 1 個分の描画指示として成立している（被写体・表情・台詞・余白）
7. **シーン差分**: 全 parts を見比べたとき「同じシーンで caption だけ違う」状態になっていない（ポーズ・カメラアングル・小道具・色温度などのバリエーション要素がある）
8. **caption の扱い**: 各 part が以下のいずれかを明示している
   - caption あり + 色とフォントスタイルを description に書いている
   - **`THIS STAMP HAS NO CAPTION — leave the cell text-free.`** のように caption 省略を明示している
9. theme と各 part が `prompt_recipes.md` §1（背景強制）／§2（FRAMING RULE）／§3（caption 個別指定）／§11（シーン差分）／§6（同一性）に従っている
