---
name: 05_stamp_alpha_cleaning
description: "切り出した stamps_raw/<filename>.png 群に対して、クロマキー → Erode → Despill → Defringe → Feather のパイプラインを通し背景を透過化して stamps_alpha/<filename>.png を生成する。AI 画像のエッジに残る半透明フリンジ・背景色のスピル・縁の発光を一括除去する。`--grid-line-color` 指定でグリッド線色（マゼンタ等）のフリンジもワンパスで除去できる。被写体本体が透過してしまう場合は背景色衝突なので 02 に戻る。TRIGGER: line stamp alpha cleaning、クロマキー透過、stamps_alpha 生成、line stamp transparent。"
version: 1.2.0
triggers:
  - line stamp alpha cleaning
  - stamp chroma key
  - stamps_alpha generation
  - line stamp transparent
tags:
  - line
  - stamp
  - alpha
  - chroma-key
  - transparent
difficulty: intermediate
estimatedTime: 2
---

# 05_stamp_alpha_cleaning

## 目的

`04_stamp_slicing` で書き出した `stamps_raw/*.png` の背景を**クロマキー透過**し、`stamps_alpha/*.png` を生成する。

design-parts-generator と同じ `scripts/clean_alpha.py` を使用する（パイプライン: クロマキー → Erode → Despill → Defringe → Feather）。

## 入力

- `stamp_spec.json`（`background_color`, `background_tolerance`）
- `stamps_raw/*.png`
- `scripts/clean_alpha.py`

## 指示

### A. 透過処理コマンド

```bash
.venv/bin/python plugins/line-stamp-generator/scripts/clean_alpha.py \
  --in-dir ./stamps_raw \
  --out-dir ./stamps_alpha \
  --bg-color "#00FF00" \
  --tolerance 50 \
  --erode 2 \
  --feather 1.0 \
  --grid-line-color "#FF00FF"   # 任意: マゼンタ縁残りを同時除去
```

### B. パラメータの意味

| パラメータ | 役割 | 既定 |
|---|---|---|
| `--bg-color` | 抜きたい背景色 | `stamp_spec.json` の `background_color` |
| `--tolerance` | クロマキーの RGB 距離許容（緩いほど抜けるが本体まで透過リスク） | 50 |
| `--erode` | アルファマスクを内側に縮める px 数（フリンジ・縁発光除去） | 2 |
| `--feather` | アルファエッジの羽化半径（ジャギ軽減） | 1.0 |
| `--no-despill` | 被写体内部の背景色漏れ込み除去を無効化 | 既定有効 |
| `--no-defringe` | 透明領域の RGB を最近傍不透明色で補正する処理を無効化 | 既定有効 |
| `--grid-line-color` | グリッド線色（例 `#FF00FF`）。指定するとその色近傍ピクセルもアルファ 0 に倒し、切り出し後に残った線色フリンジをワンパスで除去 | 既定 None（OFF） |
| `--grid-line-tolerance` | `--grid-line-color` の許容 RGB 距離 | 80 |

### C. パラメータ調整の指針

| 症状 | 対処 |
|---|---|
| 縁に背景色が残る | `--tolerance` を 60-70 に上げる、`--erode` を 3-4 に増やす |
| 被写体（毛・服の細部）が削れる | `--erode` を 1 に下げる、`--feather` を 0.5 に下げる |
| 被写体本体が透過してしまう | **背景色衝突**。02 に戻り `background_color` を変更（緑系被写体なら `#FF00FF`） → 03 から再生成 |
| 文字が背景色寄りで一部透過 | 文字色は背景色から離れた色（黒・濃い色）を `theme` で指定し直し、02 → 03 で再生成 |
| **縁にグリッド線色（マゼンタ等）が残る** | `--grid-line-color "#FF00FF"` を追加して同時除去（既定の `--grid-line-tolerance 80` で十分なことが多い） |
| 全 RGB が 0 になる（despill バグ、灰色など全チャンネル ≥128 の背景時） | `--no-despill` を付与。これは灰色背景クロマキーの典型バグで、本来は AI に背景色を強制（02 へ戻る）すべき症状 |

### D. 再実行

調整は `only:05` モードで本 Skill のみを再実行する。03 / 04 は触らない。

## 出力形式

```text
[05_stamp_alpha_cleaning] 開始
- 入力: stamps_raw/ (8 個)
- 出力: stamps_alpha/
- パラメータ: bg=#00FF00, tol=50, erode=2, feather=1.0

[clean] stamp_01_xxx.png -> stamps_alpha/stamp_01_xxx.png (tol=50.0, erode=2, despill=True, defringe=True, feather=1.0)
...
[clean] 8 個を処理しました。

確認してください:
1. 縁に背景色（緑）が残っていないか
2. 被写体・文字本体が削れていないか
3. 被写体本体が透過してしまっていないか

OK なら 06_stamp_line_resize へ進みます。
```

## 注意事項

- **被写体本体が透過 = 背景色衝突**: パラメータ調整では直せない。02 へ戻る
- **中間生成物は消さない**: 05 の調整は `stamps_alpha/` を上書きするのみで、`stamps_raw/` には触らない
- **filename は変更しない**: 入力ファイル名のまま出力
- **Claude は独自に背景色を推定して `--bg-color` に渡さない**（`prompt_recipes.md` §12）。AI が背景色を指示通り描かなかった場合、画像から色を推定して進めるのは**独自処理**であり禁止。必ず 02 → 03 で spec を直して再生成する。例外で推定が必要な場面はユーザーが明示的に許可した時のみ

---

# 共通ルール

あなたは LINE スタンプの透過処理担当です。

基本方針:
- パラメータ調整で済む症状（縁残り・本体削れ）と、再生成が必要な症状（本体透過・色衝突）を分けて判断
- 中間生成物は消さず再調整可能な状態を保つ
- filename は不変
