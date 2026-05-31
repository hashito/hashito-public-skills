# presets.md — オプションマクロ運用ガイド

`references/presets.json` に定義された **名前付きセット** を、SKILL.md（プロンプト）と `scripts/*.py`（実行）から参照するためのガイド。

「よく使うパラメータの組」を毎回手打ちせず、**プリセット名で呼び出す**ことで:
- 各 SKILL の出力が安定する（誤指定が減る）
- 再生成時のパラメータ差分が「プリセット名の違い」だけになり追跡しやすい
- 新しい運用パターンが見つかったらプリセット追加 1 件で全 SKILL に行き渡る

## プリセットのカテゴリ

| カテゴリ | 用途 | 主な利用箇所 |
|---|---|---|
| `grid` | 枚数別キャンバス・セルサイズ | 01 / 02 |
| `alpha_clean` | クロマキー透過パラメータ | 05 / `clean_alpha.py` |
| `tab` | tab.png 生成モード | 06 / `resize_for_line.py` |
| `bg_color` | クロマキー背景色 | 01 / 02 / 05 |
| `grid_line_color` | グリッド線色 | 02 / 04 / 05 |
| `caption_style` | caption の色・フォント指示テンプレ | 02 の各 part の `description` |
| `theme_template` | 真顔シュール系の theme 雛形 | 01 / 02 |
| `framing_rule` | 構図ガード文 | 02 の各 part の `description` |

## ハンドオフでの参照規約

### `stamp_spec.json` の `preset` フィールド（v1.6.0 以降）

`02_stamp_spec_design` は spec の冒頭に `preset` ブロックを置く:

```json
{
  "name": "deadpan_shiba_set",
  "theme": "...",
  "preset": {
    "grid": "8_stamps",
    "alpha_clean": "default",
    "tab": "center_crop",
    "bg_color": "default",
    "grid_line_color": "default",
    "framing_rule": "default"
  },
  "background_color": "#00FF00",
  "grid_line_color": "#FF00FF",
  "grid": { "cols": 2, "rows": 4, "cell_size": [512, 384] },
  "parts": [ ... ]
}
```

- `preset.<category>` が指定されていれば、対応する展開後の値が **`stamp_spec.json` の他フィールドと一致する** よう 02 が書き出す（重複可、ただし不整合は機械検証で NG）
- `preset` を省略した場合は従来通り個別フィールドで指定する（後方互換）

### スクリプト側の `--preset` オプション（実装はオプション）

各スクリプトは `--preset <name>` を受け取ったら `presets.json` の該当値を読み込んで既定値を上書きする。直接の `--tolerance` 等の指定があればそちらを優先する（CLI > preset > script default）。

```bash
# clean_alpha.py
.venv/bin/python plugins/line-stamp-generator/scripts/clean_alpha.py \
  --in-dir stamps_raw --out-dir stamps_alpha \
  --bg-color $(jq -r .bg_color.default plugins/line-stamp-generator/references/presets.json) \
  --preset default       # → tolerance=50 erode=2 despill=true defringe=true feather=1.0

# 強めに掃除
.venv/bin/python plugins/line-stamp-generator/scripts/clean_alpha.py \
  --in-dir stamps_raw --out-dir stamps_alpha --bg-color "#00FF00" \
  --preset strong        # → tolerance=60 erode=3 feather=1.5

# despill バグ回避
.venv/bin/python plugins/line-stamp-generator/scripts/clean_alpha.py \
  --in-dir stamps_raw --out-dir stamps_alpha --bg-color "#999999" \
  --preset no_despill    # → despill=false
```

## プリセット追加・更新の手順

1. `references/presets.json` の該当カテゴリにエントリを追加
2. `$comment` で**何のための値か**を 1 行で書く（運用判断の根拠）
3. 既存プリセット名を変更したい場合は **新名を追加 + 旧名を別名として残す** のが安全（破壊的変更は major bump）
4. `plugins/line-stamp-generator/CHANGELOG.md` の `### Added`／`### Changed` に 1 行記載
5. 影響を受ける SKILL.md（02/05/06 など）の `preset:` 参照を更新

## 何をプリセット化しない方が良いか

- **キャラの個体・台詞**: 各セットで毎回違うので雛形化しない（`theme_template` は雛形までで、個体記述は 01 で具体化）
- **caption の本文**: 各 part 固有なのでプリセットにしない（`caption_style` は **スタイル指示テンプレ** であって本文ではない）
- **API キー・出力パス**: 環境依存。プリセット対象外

## 関連ファイル

- `references/presets.json` — プリセット実体
- `references/stamp_spec_format.md` — `preset` フィールドの位置づけ
- `references/prompt_recipes.md` — 各プリセットの背景にある運用知見（FRAMING / CAPTION RULE 等）
- `skills/02_stamp_spec_design/SKILL.md` — `preset` ブロックの書き出し責務
- `skills/05_stamp_alpha_cleaning/SKILL.md` — `--preset` フラグでの呼び出し方
