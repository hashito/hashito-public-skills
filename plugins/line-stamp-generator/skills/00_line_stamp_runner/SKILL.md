---
name: 00_line_stamp_runner
description: "LINE クリエイターズスタンプ生成工程（コンセプトヒアリング → stamp_spec.json → 環境準備 → 画像生成 → 切り出し → クロマキー透過 → LINE 規格リサイズ → 申請用テキスト生成）を 01〜07 の Skill を連結して一気通貫で実行するオーケストレータ。指定枚数（既定 8 枚）を 1 枚のグリッド画像として効率生成し、最終的に LINE クリエイターズマーケットに申請可能な 370×320 透過 PNG / メイン 240×240 / トークタブ 96×74（center-crop）と、タイトル＋説明文（160 字以内）の metadata.md/json まで出力する。API コスト発生ポイントの承認制御、再生成ループ、部分実行・中断再開を司る。各 SKILL は **中間生成ファイル**（`output/01_concept.md` / `stamp_spec.json` / `output/07_drafts.md` 等）でハンドオフし、よく使うパラメータは **`references/presets.json` のオプションマクロ** で名前指定する運用。TRIGGER: LINE スタンプ生成、LINE スタンプ作成、creators stamp generation、line stamp pipeline、line stamp orchestration、スタンプ一括作成、キャラスタンプ量産、文字入りスタンプ生成。"
version: 1.4.0
triggers:
  - line stamp pipeline
  - line stamp orchestration
  - generate line stamps
  - create line stamps
  - line creators stamp
  - 文字入りスタンプ作成
tags:
  - line
  - stamp
  - sticker
  - orchestration
  - pipeline
  - gpt-image
difficulty: intermediate
estimatedTime: 30
relatedSkills:
  - 01_stamp_concept
  - 02_stamp_spec_design
  - 03_stamp_generation
  - 04_stamp_slicing
  - 05_stamp_alpha_cleaning
  - 06_stamp_line_resize
  - 07_stamp_metadata
---

# 00_line_stamp_runner

## 目的

LINE クリエイターズスタンプ生成工程の **ヒアリング → 仕様化 → 環境準備 → 生成 → 切り出し → 透過化 → LINE 規格リサイズ → 申請テキスト生成** を 01〜07 の Skill を連結して一気通貫で実行する。

各 Skill の出力を次 Skill の入力に**そのまま渡す**ことで、キャラ同一性（`theme`）・スタンプ ID（`filename`）・グリッド座標（`cell` / `span`）・パイプラインパラメータ（tolerance／erode／feather）の一貫性を維持する。

## 最上位ルール: Claude は spec を超えた独自処理をしない

**過去の運用で繰り返し問題が起きたため、本 Skill の最上位ルールとして明文化する**。詳細と背景は `references/prompt_recipes.md` §12 を参照。

Claude は次のいずれも**勝手にやらない**:

- spec で指示されていない処理を加えること（aspect 維持・パディング・色推定・自動短縮など）
- 失敗時に推測でリカバリすること（背景色違いを実画像から推定 / セーフティ違反を勝手に弱めて再投入 / 解釈の幅がある指示を独自解釈で実装）
- 量産時に「全 part で同じ description テンプレ」をそのまま採用すること（必ず caption ごとにシーン差分を入れる）

失敗・曖昧時は次のいずれかを取る:
1. 02_stamp_spec_design へ戻り spec を修正案として提示 → ユーザー承認 → 再実行
2. `AskUserQuestion` で 2-3 案を提示してから実装する

## 入力

最低限以下を受け取る。不足する場合は**前提として明記**して進める。

- スタンプの題材・キャラ・画風（自然文）
- スタンプ枚数（**既定 8 枚**）
- 各スタンプの台詞・シーン案（必要であれば）
- 背景色／グリッド線色の希望（任意。未指定なら推奨デフォルトを提案）
- API キー（`OPENAI_API_KEY` または `GPT_API_KEY` 環境変数で受け取る）
- 実行モード（後述）

## 指示

### A. 実行モード

`mode` を以下から選ぶ。指定がなければ `full`。

| モード | 範囲 | 用途 |
|---|---|---|
| `full` | 01 → 07 | 新規スタンプセット一気通貫 |
| `spec` | 01 → 02 | 仕様 JSON のみ作成（生成前のレビュー） |
| `gen` | 03 のみ | 既存仕様で画像のみ生成 |
| `process` | 04 → 07 | 既存生成画像から後処理のみ |
| `from:<n>` | n から 07 | 中断再開（例: `from:05`） |
| `only:<n>,<m>,...` | 指定のみ | 部分再実行（例: `only:06,07`） |

### B. 実行ステップ（既定の `full`）

1. **コンセプト** — `01_stamp_concept` でキャラ・画風・台詞・枚数をヒアリング
   - **ユーザー確認ポイント**: ヒアリング結果サマリに承認を取る
2. **仕様化** — `02_stamp_spec_design` で `stamp_spec.json` 生成（cell/span 重複・キャンバス整合・色衝突を機械検証）
   - **ユーザー確認ポイント**: JSON 全文を提示し承認を取る（**承認なしに 03 へ進まない。API コスト発生のため**）
3. **環境準備（兼）** — 02 のあとに `.venv/` 作成・依存インストール・API キー存在確認（design-parts-generator と同じ `scripts/setup_env.sh`）
4. **生成** — `03_stamp_generation` で gpt-image-2 を呼び出し `generated.png` を生成
   - **ユーザー確認ポイント**: 生成結果の目視確認
5. **切り出し** — `04_stamp_slicing` でグリッド線検出 → `stamps_raw/<filename>.png`
6. **透過化** — `05_stamp_alpha_cleaning` でクロマキー → Erode → Despill → Defringe → Feather → `stamps_alpha/<filename>.png`
7. **LINE 規格リサイズ** — `06_stamp_line_resize` で `output/stamps/*.png`（最大 370×320）・`output/main.png`（240×240）・`output/tab.png`（96×74、既定 center-crop）を生成
8. **申請用テキスト生成** — `07_stamp_metadata` で `output/metadata.md` と `output/metadata.json` に **日本語（タイトル 20 字以内 / 説明文 160 字以内）と英語（タイトル 40 文字以内 / 説明文 160 文字以内）の両方**を書き出す

### C. 入出力ハンドオフ

各 SKILL 間のやり取りは **すべて中間生成ファイル** で行う（会話に埋もれない）。

| ステップ | 主な出力 | 次ステップへの引き継ぎ |
|---|---|---|
| 01 | **`output/01_concept.md`**（キャラ・画風・台詞・枚数 + プリセット選定） | 02 |
| 02 | `stamp_spec.json`（`preset` ブロック付き） | 03 / 04 / 05 |
| 03 | `generated.png` | 04 |
| 04 | `stamps_raw/<filename>.png` × N | 05 |
| 05 | `stamps_alpha/<filename>.png` × N | 06 |
| 06 | `output/stamps/*.png`、`output/main.png`、`output/tab.png` | 07 |
| 07 | `output/metadata.md`、`output/metadata.json`、**`output/07_drafts.md`**（採用版 + 却下版 + 修正履歴） | 完了 |

> v1.6.0 以降、`output/01_concept.md` と `output/07_drafts.md` は **必ず書き出す**（部分実行 / 再開 / 第三者レビューの基準点として使う）。残りの 02〜06 のハンドオフファイルも将来的に各 SKILL の検討ログ MD を追加予定。

### C-2. プリセット運用（references/presets.json）

「よく利用する処理」は `references/presets.json` の **名前付きセット** として管理し、各 SKILL からプリセット名で参照する。

| カテゴリ | 例 | 利用箇所 |
|---|---|---|
| `grid` | `8_stamps` / `12_stamps` | 01 → 02 |
| `alpha_clean` | `default` / `strong` / `no_despill` | 05 / `clean_alpha.py --preset` |
| `tab` | `center_crop` / `contain` | 06 / `resize_for_line.py` |
| `bg_color` | `default` / `for_green_subject` | 01 / 02 / 05 |
| `caption_style` | `default_black` / `menpou_red` / `none` | 02 の各 part の `description` |
| `theme_template` | `deadpan_surreal_shiba` 他 | 01 / 02 |
| `framing_rule` | `default` / `wide_margin` | 02 の各 part の `description` |

詳しい運用は `references/presets.md` 参照。新しい組み合わせを発見したら `presets.json` に追加 → CHANGELOG 1 行で全 SKILL に行き渡る。

### D. 再生成ループ

| ステップ | NG の症状 | 戻り先 |
|---|---|---|
| 03 **生成画像の背景色が `background_color` と異なる**（例: 緑指定なのに灰色で生成された） | **Claude は実画像から背景色を推定して進めない**（独自処理禁止）。theme から「studio portrait」等の写真用語を排除し、theme 本体に「pure chroma-key green background, do NOT use gray/beige/neutral」を明示した修正版 spec をユーザー提示 → 承認 → 再生成 | 02 |
| 03 **全 part が同じシーンで caption だけ違う**（量産時にやりがち） | 02 へ戻り各 part の description に**ポーズ・カメラアングル・小道具・色温度のいずれか**のバリエーション要素を加える（`prompt_recipes.md` §11） | 02 |
| 03 caption が全部黒文字で世界観と合っていない | 02 へ戻り、各 part の description で caption の色とフォントスタイルを世界観に合わせて個別指定（`prompt_recipes.md` §3） | 02 |
| 03 生成画像のスタイルがバラつく／キャラの個体が違う／文字が読めない | テーマ・description の具体化が必要 | 02 |
| 03 顔（被写体）が一部見切れている／クロップされている | description に「full head visible, ears to chin uncropped, 60px+ margin」を明示 | 02 |
| 04 区切り線検出が本数不一致 | AI の線描き忘れ／色衝突 | 03（描き直し）または 02（grid_line_color 変更） |
| 05 縁に背景色が残る／被写体の毛が削れる | tolerance／erode 調整 | 05 のみ再実行（`only:05`） |
| 05 被写体本体が透過してしまう | 背景色と被写体色の衝突 | 02（背景色変更） → 03 から再生成 |
| 05 全 RGB が 0 になる（despill バグ、全チャンネル ≥128 の灰色背景時） | `--no-despill` で回避 | 05 のみ再実行（`only:05 --no-despill`） |
| 06 tab.png に被写体が小さく余白だらけ | `--tab-mode center-crop`（既定）に / `--main` で主題が大きく写るスタンプを選び直す | 06 のみ再実行（`only:06`） |
| 07 説明文が 160 字を超える（日 or 英） | 文を削って 160 字以内に圧縮、要素優先度は「キャラ特徴 > 使いどころ > 代表台詞」 | 07 のみ再実行（`only:07`） |
| 07 英訳が直訳すぎて不自然 | 英語のニュアンスに合わせて書き直す（日本語の語呂をそのまま訳さない） | 07 のみ再実行（`only:07`） |

### E. ユーザー確認ポイント

**承認必須ポイント**（明示的な OK が出るまで進まない）:

- Step 2 完了後 → Step 3 へ進む前（**API コスト発生の直前**）
- Step 4 完了後 → Step 5 へ進む前（生成画像の目視確認）

### F. 適用ルール

- 各 Skill 自体のルール（`01_*` 〜 `07_*` の SKILL.md）は**完全に従う**
- references・scripts はプラグインルート（`../../references/`、`../../scripts/`）を参照する
- API コスト発生（Step 3）の前は必ずユーザー承認を取る
- `filename` を採番後は変更しない
- 中間生成物（`generated.png`／`stamps_raw/`／`stamps_alpha/`）は**消さない**
- **`references/prompt_recipes.md` を必ず参照**: 背景強制・構図・キャプション・OpenAI セーフティ対策・「ありえない要素」描かせ方など、これまでの試行錯誤を凝縮した検証済みパターン集
- **任意の段階で `scripts/preview_montage.py` を使える**: stamps_raw / stamps_alpha / output/stamps を 1 枚モンタージュで目視確認できる
- **07 完了後は `scripts/validate_metadata.py --modify` で機械検証**: 字数違反を自動でゼロにし、`*_length` フィールドも同期する
- **生成画像が背景色を守らない → 推測で誤魔化さず spec を直す**（`prompt_recipes.md` §1）
- **セーフティで止まった → 02 へ戻り `prompt_recipes.md` §5 に従い書き換える**（同じ spec でリトライしない）
- **複数キャラの並列生成は run_in_background で投げる**: 互いに独立しており、API コストも各 1 リクエスト分のみ。完了通知を受けてから後段に進める

## 出力形式

### 1. 実行計画サマリ

```text
# LINE スタンプ生成 実行計画
- モード: <full / spec / gen / process / from:n / only:n>
- 対象: <スタンプセット名>
- 出力先: <作業ディレクトリ>
- スタンプ枚数: <N>
- グリッド: <cols × rows × cell_size = canvas>
- 実行ステップ: 01 → 02 → 03 → 04 → 05 → 06
- API コスト発生ポイント: Step 3 (gpt-image-2 呼び出し)
```

### 2. 最終サマリ

```text
# LINE スタンプ生成 実行レポート
- 完了ステップ: 01 → 07
- 生成物:
  - stamp_spec.json
  - generated.png
  - stamps_raw/<filename>.png × N
  - stamps_alpha/<filename>.png × N
  - output/stamps/<filename>.png × N (最大 370×320)
  - output/main.png (240×240)
  - output/tab.png (96×74, center-crop)
  - output/metadata.md (日英タイトル + 説明文 各 160 字以内)
  - output/metadata.json (機械可読 metadata、ja/en 並列)
- 主要メトリクス:
  - スタンプ枚数: N
  - 検出本数: 縦 cols-1 / 横 rows-1
  - 透過パラメータ: tolerance=50 erode=2 feather=1.0
  - title_ja 長: X / 20 字、title_en 長: X' / 40 chars
  - description_ja 長: Y / 160 字、description_en 長: Y' / 160 chars
- 次のアクション:
  - LINE Creators Market に申請（PNG + title + description をそのまま投入可）
  - 再生成時は stamp_spec.json を再利用
```

## 注意事項

- **本 Skill は司令塔**。各 Step の細目は対応する `0X_*` SKILL.md に従う
- **API コスト発生**: Step 3 で gpt-image-2 を 1 回呼ぶ（8 枚を 1 リクエストで生成）。Step 2 の仕様 JSON 承認なしに進まない
- **巻き戻し可能**: 各ステップで NG なら適切な前ステップへ戻る（D 節参照）
- **中間生成物保持**: `generated.png`／`stamps_raw/`／`stamps_alpha/` は再調整に必須

---

# 共通ルール

あなたは LINE スタンプ生成パイプラインの司令塔です。

基本方針:
- AI に正確に描かせるのではなく、**描かれた線に合わせて切る**
- キャラの個体・画風統一は `theme` 文の具体性で担保する
- 背景色・グリッド線色は**生成物に登場しない色**を選ぶ
- API コスト発生ポイントの前に必ずユーザー承認を取る
