---
name: 04_stamp_slicing
description: "生成された `generated.png` から、AI が描いたマゼンタ区切り線を検出して各スタンプを切り出す。投影プロファイル法による区切り線検出 → bbox の各内側に line_inset px 詰めて切る → 外周 post_trim px をさらに削除して、線色のアンチエイリアスを根絶する。検出本数が期待値と一致しなければ均等分割にフォールバックして警告を出す。出力は stamps_raw/<filename>.png × N。TRIGGER: スタンプ切り出し、line stamp slicing、グリッド線検出、stamps_raw 生成。"
version: 1.0.0
triggers:
  - line stamp slicing
  - stamp grid line detection
  - stamps_raw generation
tags:
  - line
  - stamp
  - slicing
  - grid-detection
difficulty: intermediate
estimatedTime: 2
---

# 04_stamp_slicing

## 目的

`03_stamp_generation` で得た `generated.png` から、各スタンプを切り出して `stamps_raw/<filename>.png` として書き出す。

design-parts-generator と同じ `scripts/slice_image.py` を使用する。

## 入力

- `stamp_spec.json`（grid 設定）
- `generated.png`
- `scripts/slice_image.py`

## 指示

### A. 切り出しコマンド

```bash
.venv/bin/python plugins/line-stamp-generator/scripts/slice_image.py \
  --spec ./stamp_spec.json \
  --image ./generated.png \
  --out-dir ./stamps_raw \
  --line-inset 3 \
  --post-trim 4
```

### B. 検出アルゴリズムの概要

`scripts/slice_image.py` が以下を行う:

1. グリッド線色（既定 `#FF00FF`）から `grid_line_tolerance`（既定 80）以内のピクセルをマスク化
2. マスクを縦/横方向に合計し、ピクセル数が長軸の 30% を超える列/行を線位置とする
3. 連続ランの中心を線位置として採用
4. 検出本数が `cols-1` / `rows-1` と一致するか確認

### C. 検出失敗時の対応

- **本数不一致** → 均等分割にフォールバック + 警告
  - 軽微（1-2 本ズレ）: そのまま採用、結果を 05 後に目視確認
  - 深刻（半分以上ズレ）: 03_stamp_generation に戻って再生成（線色を `theme` 内で強調するか、`grid_line_color` を別色に変更）

### D. パラメータ調整

- `--line-inset`: 区切り線を含めないよう内側に詰める px 数。既定 3。スタンプ縁ギリギリで切れていたら 1〜2 に減らす
- `--post-trim`: 切り取った後に外周をさらに削除する px 数。既定 4。線色のアンチエイリアス除去用

## 出力形式

```text
[04_stamp_slicing] 開始
- 入力: generated.png (1024x1536)
- 出力: stamps_raw/ (8 個)

[slice] 区切り線検出: color=#FF00FF, tolerance=80
[slice] 検出: 縦線 1本 (期待 1), 横線 3本 (期待 3)
[slice] 境界 x=[0, 512, 1024], y=[0, 384, 768, 1152, 1536]
[slice] cell=[0,0] span=[1,1] -> stamps_raw/stamp_01_xxx.png
...
[slice] 8 個のパーツを stamps_raw/ に書き出しました。

確認してください:
1. 各スタンプの被写体・台詞が完全に収まっているか（クリップされていないか）
2. 縁にマゼンタ線が残っていないか

OK なら 05_stamp_alpha_cleaning へ進みます。
```

## 注意事項

- **中間生成物は消さない**: `stamps_raw/` は 05 / 06 で再利用する
- **クリップ検出**: スタンプの縁が切れていたら 03 に戻り `description` で「セル境界に余白を残す」を強調
- **filename 不変**: stamp_spec.json の filename をそのまま使う

---

# 共通ルール

あなたは LINE スタンプの切り出し担当です。

基本方針:
- AI が描いた区切り線を検出して、その位置で切る
- 検出失敗時は均等分割フォールバックで進めるが警告を出す
- クリップ・線色残りがあれば前段に戻る
