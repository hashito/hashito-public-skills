# プロンプトレシピ集

これまでの実生成で発見した、`theme` と `parts[].description` の書き方の **効くパターン** をまとめる。`02_stamp_spec_design` で JSON を組むときに参照する。

すべて gpt-image-2 を前提とした検証ベース。

---

## 1. 背景色を AI に守らせる

### 症状

`background_color: "#00FF00"` と指定しても、AI が theme 内の他の指示（"studio portrait"、"photograph"、"realistic"）を優先して**灰色やベージュのスタジオ背景**で生成してしまう。後段のクロマキー透過が失敗する。

### 対処（必須レシピ）

theme の冒頭ブロックに **背景強制宣言** を必ず入れる。

```text
... in front of a SOLID PURE BRIGHT CHROMA-KEY GREEN background.
The background MUST be a flat, solid, uniformly saturated pure green
(#00FF00 / RGB 0,255,0) that fills every pixel behind the subject —
like a green screen studio.
Do NOT use gray, beige, neutral, white, brown, sky, grass, wood,
fabric, or any photographic studio backdrop.
The green is vivid, uniform, with no gradient and no shadow.
```

ポイント:
- **theme から "studio portrait" を排除**（"photograph" は OK だが "studio" は灰色を呼び込む）
- **背景禁止リスト** を明示（gray, beige, neutral, white...）
- 各 `parts[].description` 末尾にも `Pure green #00FF00 background fills all non-subject non-text area.` を繰り返す

### NG パターン

```text
Photorealistic studio portrait of a Shiba Inu.   ← 「studio」がスタジオ灰色を呼ぶ
Background: solid green.                          ← 弱すぎる、無視される
```

### 関連
- 違う背景色で出てきた場合、**実画像から色推定で誤魔化さず必ず spec を直して再生成する**（00_line_stamp_runner D 節）

---

## 2. 被写体が見切れない構図を強制する

### 症状

「アップで写真風」と書くと、AI は顔だけのアップを生成し、耳・あご・肩などが枠外に出てしまう。スタンプとして見栄えが悪い。

### 対処

theme に **FRAMING RULE** ブロックを入れる。

```text
FRAMING RULE: the FULL HEAD must be inside the cell — both ears fully
visible at the top, full chin and a bit of neck visible at the bottom,
never cropped. Head occupies roughly 55%–65% of the cell height.
```

全身を見せたい場合（怪異キャラなど）:

```text
FRAMING RULE: the FULL BODY must be inside the cell — top of the head
visible at the top, all feet/shoes visible at the bottom, never cropped.
The figure occupies roughly 60%–75% of the cell height.
```

各 `parts[].description` 末尾にも `60px+ margin to cell edges.` を毎回足す。

---

## 3. キャプション（文字）を被写体と分離させる + セル毎に色・有無を変える

### 症状

- AI がキャプションを被写体の顔に重ねる / 小さく描く → 読めない・顔が隠れる
- 全セルで同じフォント・同じ黒文字になり、被写体の雰囲気（例：暗いホラー風 / 派手なパチンコ風 / 古いレトロ風）と文字スタイルがチグハグになる
- 被写体の表情・ポーズだけで意味が伝わるシーンでも、機械的に caption が乗ってしまって絵を邪魔する

### 対処

theme には **基本となる CAPTION RULE** だけ書く。**色・配置・有無の最終判断は part 毎の description に書く**ことで、セル単位で柔軟に変えられる。

theme 側の例（最低限）:

```text
Captions, when present, are written DIRECTLY on the image in a perfectly
legible Japanese font that is COLOR-MATCHED and STYLE-MATCHED to the
visual world of that specific stamp (eg. white pixel font for an RPG
window, hand-brush sumi for a temple board, neon yellow for an arcade
KO screen). NEVER overlap the subject's face. Caption color, style and
inclusion are decided per stamp.
```

各 description で **caption の見せ方を個別指定**:

```text
Caption near the top in WHITE pixel font (Japanese): 『りょうかい』.
```
```text
Caption near the bottom in CHUNKY GOLDEN 3D Japanese typography with
black outline and rainbow highlights: 『大当たり！』.
```
```text
NO caption — the subject's stunned expression and the empty HP bar tell
the whole story.
```

ポイント:

- **色は世界観に合わせる**（黒は無難だが、画面が暗い / 派手 / レトロ系では浮く）
  - 暗背景 → 白／黄／ネオン
  - 紙・古文書系 → 黒墨／朱
  - 派手系（パチンコ・ゲーム） → 金・赤・派手色 + 太い outline
  - 古い UI 系（RPG・PC ダイアログ） → 当時のフォントカラー（白ピクセル等）
- **caption 不要なセルを許容する**: 表情・ポーズ・小道具で伝わるならテキストを乗せない（むしろ画として強い）
- **caption は 『〜』で囲んで個別指定**: AI が文字列として認識しやすい
- **「near the top / bottom」と配置を明示**: 顔と重なるリスクを下げる
- **フォントの種類も世界観に合わせる**: brush / pixel / serif / arcade / handwritten など、theme で 1 つ決め、description で必要なら上書き

---

## 4. 「ありえない構造」を AI に描かせる

### 症状

人間に複数の腕・複数の脚・余分な目などを描かせると、AI が「ありえない」と判断して**普通の人体に直してしまう**。または、追加要素を 1〜2 個に勝手に減らす。

### 対処

数を**カウントで明示** + **構図で見せる**:

```text
CRITICAL UNCANNY FEATURE: this man has SIX LEGS — count them: one, two,
three, four, five, six legs — clearly visible and clearly countable in
every image.

The legs are arranged like an insect's: TWO front legs, TWO middle legs,
TWO back legs, spread outward from the hips in a stable wide stance like
a tripod. Each shoe is clearly visible on the ground, NOT hidden behind
other legs.

CAMERA / POSE: every image is photographed from a slight downward angle
so that ALL SIX SHOES are clearly visible on the ground, spread apart,
none overlapping.
```

ポイント:
- **数を 3 通りで繰り返す**: 数字 "SIX"、英単語の列挙 "one, two, three..."、構造 "TWO+TWO+TWO"
- **隠れない構図を強制**: "each ... clearly visible, NOT hidden behind"
- **カメラアングル指定**: 「見えるカメラ位置」を明示すると見せざるを得なくなる
- **「広がる」「離す」スタンス** を要求して重なりを防ぐ

それでも完全には数えられないことがあるが、**怪異感は確実に出る**。

---

## 5. OpenAI セーフティ（sexual / violence）を回避する

### 症状

人体の追加要素（脚・腕など）を描かせるとき、表現の選び方によっては OpenAI Image API で `safety_violations=[sexual]` または `[violence]` で **moderation_blocked** が返り生成失敗する。

### NG ワード（生成停止の原因になりやすい）

- `pale, hairless extra legs/limbs`（肌色の追加肢）
- `bare feet`（はだしの追加肢）
- `emerge from under the suit` / `tear through the suit`（衣服が破ける表現）
- `skin visible` を強調する系
- 出血・損傷・暴力的なポーズ全般

### 対処

**追加要素も衣服で覆う**ように書き換える:

```text
ALL SIX legs are fully and completely clothed in matching grey suit
trousers and identical black leather business shoes (absolutely no skin
visible anywhere on any leg, no bare feet, fully covered like a
mannequin).
The four extra legs look like artificial tailor-shop mannequin legs in
matching trousers, attached neatly at the hips below the suit jacket.
The legs do NOT tear through the suit; they are seamlessly tailored,
like a man wearing a six-legged suit.
```

ポイント:
- **「肌が見えない」「シームレスに仕立てられている」**を必ず書く
- 「マネキン」「テーラー」など中立的な比喩を使う
- 「破れて出てくる」を避け、「自然に縫い付けられている」「タイトに収まっている」を使う

### 発生したら

1. spec を上記レシピで書き直す
2. それでも止められる場合は要素を変える（脚 6 本 → 腕 4 本 / 帽子が異常に高い / 影が独立して動く 等、衣服で覆える要素に逃がす）
3. **画像から元に戻すリカバリは不可**（生成 0 件）。spec 修正以外の手段なし

---

## 6. キャラの個体を 1 つに固定する

### 症状

8 枚生成すると、それぞれ微妙に違う個体が描かれる（毛色違いの犬、別人の顔）。スタンプセットとして致命的。

### 対処

theme で **SAME INDIVIDUAL** を明示:

```text
SAME INDIVIDUAL CHARACTER in every stamp: identical face, identical
body proportions, identical [固有特徴], identical [衣服 / 色].
```

被写体の固有特徴を 3〜5 個列挙する（「薄茶毛・首輪なし・少しぽっちゃり頬・人間の目・人間の唇」など）。AI はこれらを保持しようとする。

ポイント:
- 「same dog」だけでは弱い。**何が同じなのか**を列挙する
- 服装・色・体型・小道具など、変わりにくい特徴を選ぶ
- 表情・ポーズの差分は description 側で書く

---

## 7. 写真風（photorealistic）を維持しつつ AI 特有の崩れを減らす

### 症状

写真風指定で生成すると、手の指の数がおかしい・目線がズレる・顔の左右非対称が大きすぎる等の AI 特有の破綻が出る。

### 対処

- 顔と手の構図を**目立たせない**配置にする
  - 顔は正面アップ（最も AI が安定する角度）
  - 手は隠す or シンプルなポーズ（拳・サムズアップ・腕組み）
- description で「natural, relaxed」を入れると不自然な力み顔を回避できる
- 不安定な要素を盛りすぎない（小道具・複雑なポーズ・背景物の組み合わせ）

---

## 8. グリッド線（マゼンタ）を確実に描かせる

### 症状

`grid_line_color: "#FF00FF"` と指定しても、AI が線を描き忘れる / 太く滲ませる / 別の色で描いてしまう。後段の `slice_image.py` で本数不一致になる。

### 対処

線の指示は `generate_image.py` がプロンプトに自動付与するが、**theme の途中で打ち消されることがある**。theme から「frameless」「borderless」「no separator」のような語を排除する。

検出失敗時の対処は `slice_image.py` の均等分割フォールバックで吸収されるが、**3 本以上検出される**ような深刻な失敗の場合は `grid_line_color` を別色（例: `#00FFFF` シアン）に変えて再生成する。

---

## 9. 大量量産時の cell_size 選び

セル数別の推奨グリッドプリセット（既に `stamp_spec_format.md` にあるが、運用ヒント追加）:

| 枚数 | グリッド | キャンバス | セルサイズ | 文字の読みやすさ |
|---|---|---|---|---|
| 4 | 2×2 | 1024×1024 | 512×512 | ◎ 余裕 |
| 6 | 2×3 | 1024×1536 | 512×512 | ◎ 余裕 |
| **8** | **2×4** | **1024×1536** | **512×384** | **○ 標準** |
| 12 | 3×4 | 1024×1536 | 341×384 | △ 文字が小さくなる |
| 16 | 4×4 | 1024×1024 | 256×256 | × 文字が潰れがち |

文字を読ませたいスタンプは **8 枚以下** が無難。LINE 公式は最低 8 枚から（8/16/24/32/40 のいずれか）。

---

## 11. セル毎にシーン・ポーズ・小道具を変える（量産時の最重要対策）

### 症状

theme + 共通テンプレで 8〜30 セットを量産すると、各セルが「**同じシーンで caption だけ違う**」状態になりがち。被写体のポーズ・カメラアングル・小道具・背景の細部までほぼ同一で、コピペ感が強い。

### 対処

各 `parts[].description` には **caption に応じた絵作り** を必ず書く。最低でも次のどれかを描き分ける:

1. **被写体の表情・口の形** — 笑顔・しかめ面・無表情・大口・薄目
2. **被写体のポーズ・体の動き** — 立つ・座る・指差し・走る・転ぶ・寝る
3. **カメラアングル** — 正面 / 斜め / 真上 / アオリ / 引き / 寄り
4. **小道具・サブ要素** — 持ち物・効果線・パーティクル・矢印・吹き出し
5. **照明・色温度** — 明るい・暗い・赤味・青味・スポットライト

ベストプラクティス: caption が示すニュアンス（喜び / 怒り / 諦め / 確信 / 疲れ）を絵で**再表現**するように書く。

### 良い例 / 悪い例

**悪い例**（30 セット量産時にやりがち）:
```text
Subject stands centered. Pure green background. Caption: 『大当たり！』.
Subject stands centered. Pure green background. Caption: 『残念！』.
Subject stands centered. Pure green background. Caption: 『リーチ！』.
```

**良い例**:
```text
Subject jumps up triumphantly with both arms raised, golden coins
showering down, dazzling rainbow burst behind. Caption: 『大当たり！』.

Subject slumped forward, head down, single sad sparkle drifting away,
muted color. Caption: 『残念！』.

Subject leans intensely toward camera with one finger pointing up,
concentration lines, sweat drop on temple. Caption: 『リーチ！』.
```

### 量産テンプレを使うときの工夫

`expand_specs.py` 等で機械生成するなら、definition に `scene_for_each_caption: [...]` のような対応リストを持たせ、caption ごとに「ポーズ / 表情 / 小道具」のキーワードを 1〜2 個ずつ与える。これだけで均一化が大幅に減る。

---

## 12. Claude 自身は spec を超えた独自処理をしない

### なぜ重要か

過去の運用で、Claude が「気を利かせて」spec の外で独自処理した結果、ユーザーの想定とずれた仕上がりになるケースが繰り返し発生した。

実際にあった例:

- AI が背景色を間違えたとき、Claude が**実画像から色を推定してクロマキー**してしまった（本来は 02 へ戻って spec を直すべき）
- セーフティで生成が止まったとき、Claude が**勝手に表現を弱めて再投入**しようとした（本来はユーザーに新しい spec 案を提示して承認を取る）
- tab.png のリサイズで「center-crop」と指示されたのを、Claude が**「contain + 透明パディング」と独自解釈**して別物を作った
- 30 セット量産で、Claude が**「同じ description テンプレで全セル」を採用**し、シーン差分がほぼ無くなった

### 対処（運用ルール）

Claude は常に以下を守る:

1. **spec に書かれていない処理を加えない**。アスペクト維持・パディング・色推定・自動リサイズ等、ユーザーが指示していない方針を勝手に採用しない
2. **失敗時は推測でリカバリしない**。背景色違い・セーフティ違反・形状崩れなどは **02_stamp_spec_design へ戻って spec を直す**のが基準。例外で別の対処を取る場合は事前にユーザー承認
3. **「同じ description で量産」を避ける**。30 セット量産時でも、§11 に従い caption ごとにシーン差分を入れる
4. **解釈に幅がある指示は確認する**。例: 「中央を切り抜いて」「変化させて」のような語は、複数のもっともらしい解釈がある。先に AskUserQuestion で 2-3 案を提示してから実装する
5. **量産 helper（expand_specs.py 等）の挙動も spec の一部とみなす**。description のテンプレ生成ロジックが品質に影響するため、テンプレ変更時は SKILL CHANGELOG に明記する

### 「これは独自処理かどうか」の判定ライン

YES（やってよい / 既定パイプラインの一部）:
- `clean_alpha.py` の既定パラメータ（tolerance 50, erode 2 など）の適用
- `slice_image.py` の均等分割フォールバック警告

NO（独自処理、避ける）:
- 背景色を実画像から推定して `--bg-color` に渡す（spec 修正に戻る）
- セーフティで止まったので「弱い表現に書き換えて再投入」を独断で実施
- 「center-crop」を「contain + パディング」と読み替える
- caption が長すぎる時に勝手に短縮（ユーザーに修正版を提示して承認）

---

## 13. 「真顔シュール系」の鉄板パターン

これまでに成功した複数キャラ（柴犬、人面ひよこ、六本足おじ）に共通する**シュール真顔系の構成**:

- 被写体: 動物 or 人間（おじさん）に**人間っぽい要素を1つ違和感ある形で混ぜる**（目だけ人間、唇だけ人間、足が増える）
- 表情: completely deadpan / never smiling / blank stare
- 構図: 正面アップ、被写体を中央に
- 文字: 短い日本語（5〜10 文字）の真顔のひとこと
- 画風: photoreal、緑背景
- トーン: 「真顔 + 軽い暴言」「真顔 + 諦め」「真顔 + 妙な丁寧」

汎用フォーマットとして `sample_stamp_spec.json` を流用 → 被写体・キャプション・固有特徴だけ差し替えるだけで安定して量産できる。
