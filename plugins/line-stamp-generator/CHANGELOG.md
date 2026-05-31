# Changelog

All notable changes to this plugin are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.6.0] - 2026-05-16

### Added
- `references/presets.json` を新設（**オプションマクロ管理**）。`grid` / `alpha_clean` / `tab` / `bg_color` / `grid_line_color` / `caption_style` / `theme_template` / `framing_rule` の 8 カテゴリの名前付きセットを定義。`stamp_spec.json` の `preset` ブロックや `scripts/*.py --preset <name>` から参照する運用に統一
- `references/presets.md` を新設。プリセット運用ガイド（カテゴリ一覧・ハンドオフでの参照規約・スクリプト側 `--preset` の使い方・追加更新手順・プリセット化しない方が良い項目）
- `01_stamp_concept` v1.1.0: ヒアリング結果を **`output/01_concept.md`** に書き出すよう拡張。プリセット選定セクション（grid / bg_color / grid_line_color / caption_style / framing_rule / theme_template）を必須化し、02 へ正の入力として渡す
- `07_stamp_metadata` v1.3.0: 採用版だけでなく **却下案・修正履歴** を `output/07_drafts.md` に書き出すよう拡張。`only:07` 再実行時の参照点・第三者レビューの基準点になる
- `00_line_stamp_runner` v1.4.0: ハンドオフ表を中間生成ファイル中心の構造に更新（01 → `output/01_concept.md`、07 → `output/07_drafts.md` を追加）。プリセット運用セクション C-2 を新設し、`references/presets.json` のカテゴリ一覧と参照箇所を明示

### Changed
- スキル間の情報伝達を **会話依存から中間生成ファイル依存に移行**。01・07 を最初のターゲットとし、02〜06 の検討ログ MD は次バージョン以降で順次追加予定

## [1.5.0] - 2026-05-16

### Added
- `scripts/validate_metadata.py` に **英語フィールド全角混入チェック** を追加。`title_en` / `description_en` に East Asian Width が `F`（Fullwidth）または `W`（Wide）の文字（全角句読点・ひらがな・カタカナ・漢字・全角英数・全角スペース等）が含まれていた場合はエラーで exit 1。検出された文字を最大 10 件サンプル表示する
- `07_stamp_metadata` v1.3.0: `description_ja` 160 字オーバー対策として **140 字ドラフト目標 + 1 文ごとの累計字数カウント + 短縮優先順（形容詞削除 → 体言止め → 台詞列挙削減 → 改行詰め）** を生成手順に明文化。`description_en` には **半角 ASCII / Latin のみ** の使用可能文字リストと、全角句読点・ひらがな・カタカナ・漢字・全角英数の使用禁止を明示。NG 時の半角置換マップ（`、`→`,` / `。`→`.` / `…`→`...` / `「」`→`""` / `（）`→`()` 等）を追加

### Changed
- `validate_metadata.py` のレポート表示で `title_en` / `description_en` の行に検出された全角文字サンプルを併記

## [1.4.0] - 2026-05-16

### Added
- `references/prompt_recipes.md` に **§11 セル毎のシーン・ポーズ・小道具のバリエーション** と **§12 Claude 自身は spec を超えた独自処理をしない** を新設。量産時に「同じシーン + caption だけ違う」状態を防ぐ実用パターンと、過去に発生した Claude の独自処理（色推定リカバリ・独断リトライ・独自解釈）を禁止する運用ルールを明文化
- `references/prompt_recipes.md` §3 を全面改訂: theme には基本ルールだけ書き、**caption の色・フォント・有無を part 毎に description で個別指定** する方式に変更。世界観に合わせた色（白ピクセル / 朱墨 / ネオン / 金 など）と「THIS STAMP HAS NO CAPTION」省略指示の例を追加
- `references/stamp_spec_format.md` に caption 個別指定とシーン差分のガイド、機械検証項目（差分・caption 指定）を追加
- `references/sample_stamp_spec.json` を 3 part 構成のサンプルに更新し、色指定あり / 世界観連動色 / caption 省略の 3 パターンを実例として掲載
- `00_line_stamp_runner` v1.3.0: **最上位ルール「Claude は spec を超えた独自処理をしない」** を SKILL 冒頭に明記。再生成ループ表に「全 part が同じシーン」「caption が全黒で世界観と合わない」のトリガーを追加
- `02_stamp_spec_design` v1.2.0: 機械検証を 11 → 13 項目（シーン差分・caption 個別指定）に拡張、注意事項に独自処理禁止を明記
- `03_stamp_generation` v1.2.0: セーフティ違反時の Claude 独断リトライを明示禁止、必ず修正版 spec をユーザー承認 → 再投入
- `05_stamp_alpha_cleaning` v1.2.0: 背景色を実画像から推定して `--bg-color` に渡す独自処理を明示禁止、必ず 02 へ戻る

### Changed
- 量産パイプラインの設計思想を更新: theme で世界観の核を統一し、part 毎の description で**ポーズ・小道具・camera・caption スタイルのバリエーション**を入れる前提に変更（従来は theme でフォント・色まで固定していた）

## [1.3.0] - 2026-05-16

### Added
- `references/prompt_recipes.md` を新設（**最重要**）。これまでの実生成で蓄積した検証済みパターンを凝縮:
  - §1 背景色を AI に守らせる（"studio portrait" を排除、背景禁止リスト明示）
  - §2 被写体が見切れない構図を強制する（FRAMING RULE ブロック）
  - §3 キャプションを被写体と分離させる（CAPTION RULE ブロック）
  - §4 「ありえない構造」を AI に描かせる（数のカウント明示・カメラアングル指定・重なり禁止）
  - §5 OpenAI セーフティ（sexual / violence）を回避する（NG ワード集と書き換え例）
  - §6 キャラの個体を 1 つに固定する（SAME INDIVIDUAL）
  - §7 写真風の AI 特有の崩れを減らす
  - §8 グリッド線を確実に描かせる
  - §9 セル数別 cell_size 選び（文字読みやすさ評価付き）
  - §10 「真顔シュール系」の鉄板パターン（柴犬／人面ひよこ／六本足おじで実証済み）
- `scripts/preview_montage.py` を新設。8 枚 PNG を 1 枚モンタージュ画像に整列。枚数から自動グリッド推定、`--bg transparent` で透明背景も対応
- `scripts/validate_metadata.py` を新設。`metadata.json` の字数制約（title 20/40・description 160/160）と必須キーを機械検証。`--modify` で `*_length` フィールド再計算
- `scripts/clean_alpha.py` に `--grid-line-color` / `--grid-line-tolerance` オプション追加。クロマキー透過時にマゼンタなどのグリッド線フリンジをワンパスで除去（従来は別 Python ワンライナーで後処理していた）

### Changed
- `02_stamp_spec_design` v1.1.0: 機械検証項目を 7 件 → 11 件に拡張（背景強制宣言・FRAMING RULE・CAPTION RULE・セーフティ違反ワード検出を追加）。`prompt_recipes.md` 参照を必須化
- `03_stamp_generation` v1.1.0: OpenAI セーフティで止まった場合の対処を明文化（同じ spec でリトライしない、`prompt_recipes.md` §5 参照）、複数キャラ並列生成のガイダンスを追加
- `05_stamp_alpha_cleaning` v1.1.0: グリッド線フリンジ除去オプションをコマンド例とパラメータ表に反映、despill バグの記載も明示
- `07_stamp_metadata` v1.2.0: `validate_metadata.py` を機械検証手段として明記
- `00_line_stamp_runner` v1.2.0: 適用ルールに `prompt_recipes.md` 参照必須・`preview_montage.py`／`validate_metadata.py` の活用方法・並列生成運用を追加

## [1.2.0] - 2026-05-15

### Added
- `07_stamp_metadata` v1.1.0: **日本語と英語の両方**でタイトル・説明文を出力するよう拡張。`title_ja` (20 字以内) / `title_en` (40 chars 以内) / `description_ja` (160 字以内) / `description_en` (160 chars 以内) を `metadata.md` と `metadata.json` に並列出力。LINE Creators Market の日本市場 / 海外市場（特に英語圏）への同時申請に対応
- `metadata.json` の構造拡張: `languages: ["ja","en"]`、`stamps[].caption_ja` / `stamps[].caption_en` を許容
- `00_line_stamp_runner` v1.1.0: 再生成ループ表に「英訳が直訳すぎて不自然」の対処を追加。最終サマリの metric を日英両方の文字数表示に更新

### Changed
- 既存の `description` / `title` フィールドは廃止し、`description_ja` / `title_ja` などの言語別フィールドに移行（破壊的変更）。既存 metadata.json を再利用する場合はフィールド名を変換する必要あり

## [1.1.0] - 2026-05-15

### Added
- `07_stamp_metadata` Skill を新設（v1.0.0）。`stamp_spec.json` の theme と各 description から LINE Creators Market 申請用の **タイトル（20 字以内）** と **説明文（160 字以内厳守）** を生成し `output/metadata.md` / `output/metadata.json` に書き出す
- `06_stamp_line_resize` v1.1.0: tab.png に **center-crop モード**を追加（既定）。主たる画像の被写体中心を 96×74 で切り抜いて拡縮（cover 方式）し、トークタブで主題が小さくなる問題を解消。`--tab-mode {center-crop | contain}` で切替可能
- `scripts/resize_for_line.py` に `center_crop_into()` 関数と `--tab-mode` オプションを追加
- `00_line_stamp_runner` v1.1.0: 実行範囲を 01 → 06 から 01 → 07 に拡張。再生成ループ表に「**背景色が指示と異なる場合は推定せず spec を直して再生成**」「顔が見切れた場合の対処」「despill バグ（灰色背景時）」「tab 余白問題」「説明文 160 字超」の項目を追加

### Changed
- プラグイン全体を 7 Skill → **8 Skill** 構成に拡張
- 既定 tab.png 挙動が contain → center-crop に変更（破壊的ではないが見た目が変わる）

## [1.0.0] - 2026-05-15

### Added
- `line-stamp-generator` プラグイン初版（v1.0.0）。7 Skill 構成で LINE クリエイターズスタンプを一括生成する:
  - `00_line_stamp_runner` オーケストレータ
  - `01_stamp_concept`（キャラ・画風・台詞案ヒアリング）
  - `02_stamp_spec_design`（stamp_spec.json 化、機械検証）
  - `03_stamp_generation`（gpt-image-2 で 1 リクエスト・グリッド一枚絵生成）
  - `04_stamp_slicing`（マゼンタ区切り線検出による切り出し）
  - `05_stamp_alpha_cleaning`（クロマキー → Erode → Despill → Defringe → Feather）
  - `06_stamp_line_resize`（LINE 規格リサイズ: 最大 370×320 / メイン 240×240 / タブ 96×74）
- 共通スクリプトは `design-parts-generator` から流用（`generate_image.py` / `slice_image.py` / `clean_alpha.py` / `setup_env.sh`）
- 新規スクリプト `scripts/resize_for_line.py`（アルファ bbox 中央配置 + LINE 規格パディング）
- `references/stamp_spec_format.md` と `references/sample_stamp_spec.json`
- 既定 8 枚（2×4 グリッド、キャンバス 1024×1536、各セル 512×384 横長 ≒ LINE 比率）
