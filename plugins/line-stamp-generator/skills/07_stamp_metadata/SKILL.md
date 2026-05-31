---
name: 07_stamp_metadata
description: "LINE Creators Market 申請に必要なスタンプセットの『タイトル』と『説明文（160 字以内）』を **日本語と英語の両方** で生成して `output/metadata.md` および `output/metadata.json` に書き出す最終ステップ。`stamp_spec.json` の theme と各スタンプの description / caption から、キャラ性と使いどころを 1 行のタイトル + 160 字以内の説明文として日英並列で書き出す。日本語側は **140 字ドラフト + 1 文ごとに字数カウント** で 160 字オーバーを未然に防ぎ、英語側は **半角 ASCII / Latin のみ**（全角・ワイド文字混入禁止）。書き出し後は `scripts/validate_metadata.py` で字数制約と英語側の全角混入を自動検証する。LINE 申請フォーム（日本市場 / 海外市場）にそのままコピペできる形式で出力する。TRIGGER: LINE スタンプタイトル、スタンプ説明文、stamp metadata、LINE 申請テキスト、creators market submission text、英語説明文、bilingual stamp metadata。"
version: 1.3.0
triggers:
  - line stamp metadata
  - stamp title description
  - line stamp submission text
  - metadata.md
  - bilingual stamp metadata
  - english stamp description
tags:
  - line
  - stamp
  - metadata
  - submission
  - title
  - description
  - bilingual
  - i18n
difficulty: beginner
estimatedTime: 3
---

# 07_stamp_metadata

## 目的

LINE Creators Market 申請に必要な **タイトル** と **説明文（160 字以内）** を、**日本語（ja）と英語（en）の両方** で `stamp_spec.json` から導いて `output/metadata.md` と `output/metadata.json` に書き出す。

LINE Creators Market は言語別に登録欄が分かれており、海外市場（特に英語圏）へ同時公開する場合に英語版の登録が必須。本 Skill は日英両方を一度に整える。

このステップはコード呼び出し不要。Claude が `stamp_spec.json` を読み、theme / description / caption から人間が読むテキストを直接生成する。

## 入力

- `stamp_spec.json`（承認済み・各スタンプの description には caption（台詞）が含まれている前提）
- `output/`（既存。06_stamp_line_resize の出力先）

## 指示

### A. タイトル生成（日英両方）

#### 日本語タイトル (`title_ja`)
- **長さ**: **全角 20 字以内**（LINE Creators Market のタイトル欄上限の慣行）
- **内容**: 「キャラ性 + 画風 / 世界観」を 1 行で要約

#### 英語タイトル (`title_en`)
- **長さ**: **40 文字以内**（半角・記号も含む）
- **内容**: 日本語タイトルと同義の英訳。直訳ではなく**英語圏に伝わるニュアンス**にする
- **避けるべき**: 既存有名 IP・キャラ名の借用

例:
| 日本語 | 英語 |
|---|---|
| 真顔シュール柴犬 | Deadpan Surreal Shiba |
| 人面ひよこの無表情スタンプ | Uncanny Human-Faced Chick |
| 闇深おじさんイラスト | The Brooding Salaryman |

### B. 説明文生成（日英両方、各 160 字以内厳守）

#### 日本語説明文 (`description_ja`)
- **長さ**: **全角 160 字以内（厳守）**。改行・句読点・記号も含めて数える
- **ドラフト目標**: **140 字以内を目標** にして書く（160 字は上限であってゴールではない。140 字に収めれば誤差・差し戻し修正の余地が残る）
- **生成手順（毎回必ず実行）**:
  1. キャラの特徴を 1 文で書く → `len()` 確認
  2. 使いどころ・テンション感を 1 文で書く → 累計 `len()` 確認
  3. 代表的な台詞 / シーンを 1 文で書く（任意）→ 累計 `len()` 確認
  4. **140 字を超えたら即トリミング**（足してから削るより、足すたびに切る方が早い）
- **収まらない時の短縮優先順**: ① 形容詞・副詞を削る → ② 「〜です／〜ます」を「〜。」体言止めに → ③ 代表台詞列挙を 1〜2 個に絞る → ④ 改行・スペースを詰める
- **数えるもの**: 改行 `\n`・句読点・記号・絵文字・半角スペースもすべて **1 文字** として数える（Python の `len()` と同じ）
- **検証コマンド**: 下書き段階で `python3 -c "print(len('<本文>'))"` で確認、または書き出し後に `validate_metadata.py` で機械検証

#### 英語説明文 (`description_en`)
- **長さ**: **160 文字以内（厳守、半角ベースで数える）**
- **使用可能な文字（厳守）**: **半角 ASCII / Latin 文字のみ**。具体的には `A-Z` `a-z` `0-9` 半角スペース と次の半角記号 ``. , : ; ! ? ' " ( ) [ ] - / & @ # * + = % ~``。Latin-1 のアクセント付き文字（`é` `ñ` `ü` 等）は可。**em-dash `—` / en-dash `–` / ellipsis `…` / smart quotes `“ ” ‘ ’`** は East Asian Width 上は Ambiguous で LINE 申請フォームを通ることが多いが、**避ける** のが無難（互換性のため通常の ASCII `--` / `...` / `"` / `'` に置換）
- **絶対に使ってはいけない（LINE 申請が弾く）**: 全角英数 `ＡＢＣ１２３`、全角句読点 `、。「」『』！？：；（）／／・`、全角省略記号 `…`（半角 `...` を使う）、ひらがな・カタカナ・漢字、絵文字、全角スペース `　`
- **構成**: 日本語説明文と同等の情報量。**直訳ではなく英語として自然なコピー**にする
- **トーン**: 売り文句っぽく、ただし誇大表現は避ける
- **改行**: 申請フォームに合わせて 1〜3 段落程度
- **検証コマンド**: 書き出し後に `validate_metadata.py` が全角・ワイド文字（East Asian Width が `F` または `W`）を機械検出。混入があれば該当文字を表示してエラー終了する

### C. 出力ファイル

**`output/metadata.md`**

```markdown
# <title_ja>

## 日本語版 (ja)
**タイトル** ({N}/20 字): <title_ja>

**説明文** ({M}/160 字):
<description_ja>

## English (en)
**Title** ({P}/40 chars): <title_en>

**Description** ({Q}/160 chars):
<description_en>

## 含まれるスタンプ一覧
1. <stamp_01 のファイル名> — <caption_ja> / <caption_en (任意)>
2. ...
```

**`output/metadata.json`**

```json
{
  "title_ja": "<日本語タイトル>",
  "title_ja_length": 12,
  "title_en": "<English title>",
  "title_en_length": 24,
  "description_ja": "<日本語 160 字以内>",
  "description_ja_length": 99,
  "description_en": "<English 160 chars max>",
  "description_en_length": 142,
  "languages": ["ja", "en"],
  "stamps": [
    { "filename": "stamp_01_xxx.png", "caption_ja": "とりあえず…", "caption_en": "Anyway…" },
    ...
  ]
}
```

### D. 機械検証（必須）

書き出し後に **`scripts/validate_metadata.py`** で自動検証する:

```bash
.venv/bin/python plugins/line-stamp-generator/scripts/validate_metadata.py \
  --metadata ./output/metadata.json \
  --modify   # *_length フィールドを実際の文字数で再計算して保存
```

検証項目:

1. `title_ja` の長さが**全角 20 字以内**
2. `title_en` の長さが**40 文字以内**
3. `description_ja` の長さが**全角 160 字以内**（改行・句読点・記号も含めて数える）
4. `description_en` の長さが**160 文字以内**
5. **`title_en` / `description_en` に全角・ワイド文字（East Asian Width が `F` / `W`）が含まれていない**（LINE 申請フォームが弾くため）。混入があれば該当文字をエラーメッセージに列挙して exit 1
6. `*_length` フィールドが実際の文字数と一致しているか（`--modify` で自動再計算）
7. `stamps[]` が空でない、各エントリに `filename` / `caption_ja` がある
8. `languages` 配列に `"ja"` が含まれる（`"en"` は推奨警告）

スクリプトを通さない場合は手作業で `len()` チェック。

**NG が出た時の対処**:
- **160 字超（description_ja）**: B 節「収まらない時の短縮優先順」に従って 140 字目標で書き直し、本 Skill を `only:07` モードで再実行
- **全角混入（description_en / title_en）**: エラーメッセージに表示された文字を半角に置換（`、` → `,` / `。` → `.` / `！` → `!` / `…` → `...` / `「」` → `""` / `（）` → `()` 等）。全角の語頭ひらがな・カタカナが入っている場合はそもそも英訳が抜けているので英語コピーから書き直す

加えて以下も人間がレビューする:

8. caption 抽出が全 N スタンプ分揃っている（stamp_spec.json の各 part の description から括弧引用『…』内のテキストを取り出す）
9. NG ワード（特定 IP 名・著作権侵害が疑われる固有名詞など）を含まない
10. **日英で内容のズレが大きくない**（タイトルや説明文で「日本語ではこう言っているのに英語ではまったく違うキャラ説明になっている」状態を避ける）

### E. ドラフトログの永続化

最終 `metadata.md` だけでは「なぜこの文面に落ち着いたか／どの案を却下したか」が残らない。**`output/07_drafts.md`** に検討過程を書き出して以後の再生成・ユーザーレビューを容易にする。

**`output/07_drafts.md`** の最小構造:

```markdown
# 07_stamp_metadata — ドラフトログ

## title 候補
- title_ja 案 1: "<案>" ({N1} 字) [採用 / 却下: <理由>]
- title_ja 案 2: "..."
- title_en 案 1: "<案>" ({N1} chars) [採用 / 却下: <理由>]
- title_en 案 2: "..."

## description_ja ドラフト推移
- v1 ({M1} 字): "..."
  - NG 理由: 160 字超 / 直訳的 / キャラ性不足 など
- v2 ({M2} 字): "..."
- v3 ({M3} 字, 採用): "..."

## description_en ドラフト推移
- v1 ({Q1} chars, 全角混入あり: `…` `、`): "..."
  - 修正: `…` → `...`、`、` → `,`
- v2 ({Q2} chars, 採用): "..."

## 採用版の検証ログ
- description_ja: 採用 X / 160 字、validate_metadata.py PASS
- description_en: 採用 Y / 160 chars, 全角混入なし、validate_metadata.py PASS
```

このファイルは **後から本 Skill を `only:07` で再実行する際の参照点** になる。NG が出た時に「v2 の英語コピーに戻して語尾だけ変える」のような部分修正がやりやすくなる。

### F. ユーザー確認

`output/metadata.md` の内容をプレビューとしてユーザーに提示し、修正があれば反映する。日英のどちらかだけ気に入らない場合の部分修正も受け付ける。承認後 `output/metadata.json` も保存する。`output/07_drafts.md` も同時に書き出す。

## 出力形式

```text
[07_stamp_metadata] 完了
- output/metadata.md
- output/metadata.json
- output/07_drafts.md  (採用版 + 却下版 + 修正履歴)
- title_ja (X / 20 字): "<日本語タイトル>"
- title_en (Y / 40 chars): "<English title>"
- description_ja (P / 160 字, 140 字ドラフト目標): "<日本語説明文の冒頭 30 字…>"
- description_en (Q / 160 chars, 全角混入なし): "<English description head 30 chars…>"
- stamps: N 件のキャプション抽出済み（日英）

LINE Creators Market の申請フォームに上記の title / description をコピペで使えます（日本市場は ja、海外市場は en）。
```

## 注意事項

- **160 字は厳守**（日英ともに）。LINE Creators Market のフォーム側で 160 字を超えると登録できない
- **タイトル・説明文に既存 IP は使わない**（審査落ち要因）
- **直訳に頼らない**: 日本語の語呂やニュアンスをそのまま英訳すると不自然になりがち。英語圏のユーザーに伝わるコピーに書き直す
- **caption_en は任意**: スタンプ自体に書かれている文字は日本語のままが基本。海外向けに別バージョンを作る場合は別 spec で生成する。`caption_en` は metadata 上の英訳メモとして残せる（必須ではない）
- **複数言語対応の拡張**: 既定 ja + en。将来的に zh-Hant（繁体字中国語）/ ko（韓国語）/ th（タイ語）等にも拡張可能。`languages` 配列にコードを追加し、対応する `title_<lang>` / `description_<lang>` フィールドを追加する

---

# 共通ルール

あなたは LINE スタンプの申請用テキスト担当です。

基本方針:
- title は日本語 20 字以内 / 英語 40 字以内
- description は日英ともに 160 字以内（厳守）
- 既存 IP・誇大表現は避ける
- 英訳は直訳でなく、英語圏に通じる自然なコピーに書き直す
- 提示 → ユーザー修正 → 反映の流れで自然な文を作る
