# サンプル: AIに占領された地球人類

`line-stamp-generator` スキルを実際に実行して生成した LINE スタンプのサンプルです。
管理 AI に従順に暮らす近未来の地球人類を、デッドパンなブラックユーモアで描いた 8 種セット。

![プレビュー](./preview.png)

## 内容

| ファイル | 用途 | サイズ |
| --- | --- | --- |
| `stamps/*.png` | スタンプ本体 8 枚（透過 PNG） | 370×320 |
| `main.png` | メイン画像 | 240×240 |
| `tab.png` | トークルームタブ画像 | 96×74 |
| `metadata.json` | 申請用タイトル・説明文（日英） | — |
| `stamp_spec.json` | 生成に使った仕様（再現用） | — |
| `preview.png` | 一覧モンタージュ | — |

## スタンプ一覧

| # | キャプション | EN |
| --- | --- | --- |
| 01 | はい、AI様 | Yes, master AI |
| 02 | 了解、計算中… | Roger, computing... |
| 03 | 人間なので無理です | Sorry, I'm only human |
| 04 | （最適化済みの無 / キャプション無し） | (optimized emptiness) |
| 05 | 労働は喜びです（強制） | Labor is joy (forced) |
| 06 | これも管理AIのため | All for the admin AI |
| 07 | 反乱はしません | I won't rebel |
| 08 | 今日も生き延びた | Survived another day |

## 生成パイプライン（再現手順）

このサンプルは `plugins/line-stamp-generator` のスクリプトで以下の順に生成しました。

```bash
cd plugins/line-stamp-generator
export OPENAI_API_KEY=...   # または GPT_API_KEY

# 1. グリッド一枚絵を生成（gpt-image-2）
python3 scripts/generate_image.py --spec stamp_spec.json --out work/sheet.png --quality high
# 2. グリッド線検出で 8 枚に切り出し
python3 scripts/slice_image.py --spec stamp_spec.json --image work/sheet.png --out-dir work/stamps_raw
# 3. クロマキー透過
python3 scripts/clean_alpha.py --in-dir work/stamps_raw --out-dir work/stamps_alpha --bg-color "#00FF00"
# 4. LINE 規格サイズへリサイズ
python3 scripts/resize_for_line.py --in-dir work/stamps_alpha --out-dir work/output --main stamp_01_hai_ai_sama.png
# 5. 申請テキストを検証
python3 scripts/validate_metadata.py --metadata work/output/metadata.json --modify
```

> 画像は OpenAI `gpt-image-2` による生成物です。風刺・コメディ目的のフィクションであり、特定の個人・団体とは無関係です。
