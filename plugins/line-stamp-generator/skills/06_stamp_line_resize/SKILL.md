---
name: 06_stamp_line_resize
description: "透過 PNG `stamps_alpha/*.png` を LINE Creators Market 規格に合わせてリサイズ・パディングする最終ステップ。各スタンプは最大 370×320 px（アスペクト維持・中央配置・透明パディング）、メイン画像 240×240、トークルームタブ 96×74 を一括生成する。tab.png は既定で center-crop モード（主たる画像の中心を 96×74 で切り抜いて拡縮、cover 方式）。アルファ bbox で被写体の実位置を取り直すので、AI 生成時の余白の偏りも補正される。これで LINE Creators Market にそのまま申請可能な完全セットが揃う。TRIGGER: LINE 規格リサイズ、line stamp packaging、main.png 生成、tab.png 生成、LINE 申請用 PNG。"
version: 1.1.0
triggers:
  - line stamp resize
  - line stamp packaging
  - main.png tab.png generation
  - line creators market packaging
tags:
  - line
  - stamp
  - resize
  - packaging
  - line-creators-market
difficulty: beginner
estimatedTime: 1
---

# 06_stamp_line_resize

## 目的

`stamps_alpha/*.png` を LINE Creators Market 規格に合わせて整え、`output/` 配下に申請可能な完全セットを生成する。

## 入力

- `stamps_alpha/*.png`
- `scripts/resize_for_line.py`

## 指示

### A. リサイズコマンド

```bash
.venv/bin/python plugins/line-stamp-generator/scripts/resize_for_line.py \
  --in-dir ./stamps_alpha \
  --out-dir ./output
```

オプション:
- `--main <filename>`: メイン画像・タブ画像のソースに使うファイル名（既定: 先頭 PNG）
- `--alpha-threshold <int>`: bbox 計算時のアルファ閾値（既定 8、羽化された薄い縁を切り捨てる）
- `--no-main`: main.png / tab.png を生成しない
- `--tab-mode {center-crop | contain}`: tab.png の生成方式
  - `center-crop`（**既定**）: 主たる画像の被写体中心を 96×74 で切り抜いて拡縮（**cover** 方式、余白なし）。アイコン的に主題を見せたいタブ画像に最適
  - `contain`: 96×74 にアスペクト維持で収めて透明パディング（main / stamps と同じ fit 方式）

### B. 生成される LINE 規格セット

| ファイル | サイズ | 用途 |
|---|---|---|
| `output/stamps/<filename>.png` × N | 最大 370×320 | スタンプ本体（アスペクト維持・中央配置・透明パディング） |
| `output/main.png` | 240×240 | LINE Creators Market のメイン画像 |
| `output/tab.png` | 96×74 | トークルームタブ画像 |

### C. アルファ bbox に基づく整列

スクリプトは各スタンプの**アルファ bbox**（不透明領域の外接矩形）を取り直して、その bbox を中央配置する。これにより:

- AI 生成時のセル内余白の偏りが補正される
- 縦長／横長の被写体でも、被写体自体が中央に来る
- 透過縁の薄い羽化部分は閾値で切り捨てられる（既定 `--alpha-threshold 8`）

### C-2. tab.png の center-crop（既定）

タブ画像 (96×74) は LINE トークルームのタブで小さく表示されるため、余白付きの contain 方式だと被写体が小さくなりすぎる。**center-crop モード（既定）** は次の手順:

1. ソース画像のアルファ bbox を取り、被写体中心 (cx, cy) を確定
2. ソース画像全体から target アスペクト比 (96/74 ≒ 1.297:1) の最大矩形を取り、被写体中心に揃える
3. 切り抜いた矩形を 96×74 にリサイズ

→ 余白なしで主題を見せられる（cover）。主題が画像端に偏っている場合は範囲クランプで自動補正。`--tab-mode contain` で旧挙動に戻せる。

### D. メイン画像の選定

- ユーザーから指定があれば `--main <filename>` で指定
- 未指定なら `stamps_alpha/` の**先頭ファイル**（filename 昇順）が main / tab に採用される
- 仕上がり後にメイン画像が気に入らなければ `--main` を変えて 06 のみ再実行（`only:06`）

## 出力形式

```text
[06_stamp_line_resize] 開始
- 入力: stamps_alpha/ (8 個)
- 出力: output/

[resize] stamp: stamp_01_xxx.png -> output/stamps/stamp_01_xxx.png (370x320)
...
[resize] main: stamp_01_xxx.png -> output/main.png (240x240)
[resize] tab : stamp_01_xxx.png -> output/tab.png (96x74)
[resize] 8 枚のスタンプを output/stamps/ に書き出しました。

完了:
- output/stamps/ … LINE スタンプ本体 8 枚 (370x320 max)
- output/main.png … メイン画像 (240x240)
- output/tab.png … トークルームタブ (96x74)

LINE Creators Market にそのまま申請できます。
```

## 注意事項

- **アスペクト維持**: スクリプトは contain（収まる範囲で最大化）を採用し、引き伸ばしはしない
- **透明パディング**: 余白は完全透明。LINE 規格に準拠
- **main/tab 選定**: 仕上がり後に `--main <filename>` で変更可能（06 のみ再実行）
- **既存 output の扱い**: スクリプトは個別ファイルを上書きするのみ。古い `output/` を完全に消したい場合は事前削除

---

# 共通ルール

あなたは LINE スタンプの最終パッケージング担当です。

基本方針:
- LINE 規格に準拠（最大 370x320 / メイン 240x240 / タブ 96x74）
- アスペクト維持 + 中央配置 + 透明パディング
- アルファ bbox で被写体位置を補正
- メイン画像は --main で任意切替可能
