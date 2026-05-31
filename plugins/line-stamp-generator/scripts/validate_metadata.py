#!/usr/bin/env python3
"""LINE Creators Market 申請用 metadata.json の制約を検証する。

検査項目:
  - title_ja : 1〜20 文字（全角）
  - title_en : 1〜40 文字（半角ベース）／全角・東アジア幅文字を含まないこと
  - description_ja : 1〜160 文字（全角、改行含む）
  - description_en : 1〜160 文字（半角ベース、改行含む）／全角・東アジア幅文字を含まないこと
  - stamps[] が空でない、各エントリに filename / caption_ja が存在
  - languages 配列に "ja" / "en" が含まれる
  - title_*_length / description_*_length フィールドが実際の長さと一致

NG が 1 件でもあれば exit code 1、すべて OK なら 0 を返す。
metadata.json を上書きする modify モードでは、*_length フィールドを実際の値に再計算して書き戻す。
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path


LIMITS = {
    "title_ja": 20,
    "title_en": 40,
    "description_ja": 160,
    "description_en": 160,
}

# 英語フィールドで禁止する東アジア幅区分（LINE 申請フォームは全角を受け付けない）
#   F: Fullwidth（全角英数・全角記号）
#   W: Wide（CJK・ひらがな・カタカナ・全角句読点・全角省略記号など）
FORBIDDEN_EAW_IN_EN = {"F", "W"}


def _fullwidth_chars(text: str) -> list[str]:
    """en フィールドに混入してはいけない全角/ワイド文字を列挙して返す（重複除去・出現順保持）。"""
    seen: dict[str, None] = {}
    for ch in text:
        if unicodedata.east_asian_width(ch) in FORBIDDEN_EAW_IN_EN:
            seen.setdefault(ch, None)
    return list(seen.keys())


def check(meta: dict) -> tuple[list[str], list[str]]:
    """戻り値: (errors, warnings)"""
    errors: list[str] = []
    warnings: list[str] = []

    # 必須キー
    for key in ("title_ja", "title_en", "description_ja", "description_en", "stamps", "languages"):
        if key not in meta:
            errors.append(f"missing key: {key}")

    # 長さ
    for key, limit in LIMITS.items():
        if key not in meta:
            continue
        value = meta[key]
        if not isinstance(value, str) or not value:
            errors.append(f"{key} must be a non-empty string")
            continue
        if len(value) > limit:
            errors.append(f"{key} too long: {len(value)} / {limit} chars")
        length_key = f"{key}_length"
        if length_key in meta and meta[length_key] != len(value):
            warnings.append(
                f"{length_key} stale: declared {meta[length_key]} but actual {len(value)}"
            )

    # 英語フィールドに全角文字が混入していないか（LINE 申請フォームは全角を受け付けない）
    for key in ("title_en", "description_en"):
        value = meta.get(key)
        if not isinstance(value, str) or not value:
            continue
        bad = _fullwidth_chars(value)
        if bad:
            sample = "".join(bad[:10])
            errors.append(
                f"{key} contains full-width / wide chars (LINE rejects them): '{sample}'"
            )

    # languages
    if isinstance(meta.get("languages"), list):
        if "ja" not in meta["languages"]:
            errors.append("languages must include 'ja'")
        if "en" not in meta["languages"]:
            warnings.append("languages doesn't include 'en' (bilingual recommended)")
    else:
        errors.append("languages must be a list")

    # stamps
    stamps = meta.get("stamps", [])
    if not isinstance(stamps, list) or not stamps:
        errors.append("stamps must be a non-empty list")
    else:
        for i, s in enumerate(stamps):
            if "filename" not in s:
                errors.append(f"stamps[{i}] missing filename")
            if "caption_ja" not in s:
                errors.append(f"stamps[{i}] missing caption_ja")
            if "caption_en" not in s:
                warnings.append(f"stamps[{i}] missing caption_en (recommended)")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LINE stamp metadata.json.")
    parser.add_argument("--metadata", required=True, help="Path to metadata.json")
    parser.add_argument(
        "--modify",
        action="store_true",
        help="*_length フィールドを実際の長さに再計算して metadata.json を上書き保存",
    )
    args = parser.parse_args()

    path = Path(args.metadata)
    if not path.exists():
        print(f"[validate] file not found: {path}", file=sys.stderr)
        return 2
    meta = json.loads(path.read_text(encoding="utf-8"))

    errors, warnings = check(meta)

    print(f"[validate] {path}")
    for key, limit in LIMITS.items():
        value = meta.get(key, "")
        if isinstance(value, str):
            length_ok = len(value) <= limit
            extra = ""
            if key.endswith("_en"):
                bad = _fullwidth_chars(value)
                if bad:
                    extra = f"  full-width: {''.join(bad[:5])}"
                    length_ok = False
            status = "OK" if length_ok else "NG"
            print(f"  {key:>16} ({len(value):>4} / {limit:>3}): {status}{extra}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    if args.modify:
        # *_length を実際の長さで上書き
        for key in LIMITS:
            if key in meta:
                meta[f"{key}_length"] = len(meta[key])
        path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n[validate] *_length を再計算して上書き保存しました: {path}")

    print("\n[validate] all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
