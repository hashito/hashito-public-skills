#!/usr/bin/env python3
"""グリッド仕様 JSON に従って一枚絵を切り出す。

「AI が描いた区切り線を実画像から検出して、その位置で切る」方式を採る。

理由:
    gpt-image-2 はキャンバスサイズや内部のセル位置を完璧には守らない。
    あらかじめ決めた数値で切ると微妙なズレで切り口が汚くなる。
    そこで生成プロンプトでマゼンタ色（背景・パーツに被らない色）の区切り線を
    明示的に描かせ、それを検出して実画像上の真のセル境界を確定する。

検出アルゴリズム:
    1. 各ピクセルが「区切り線色からの色距離 <= tolerance」のマスクを作る
    2. マスクを縦方向に合計 → 列ごとのスコアの 1D プロファイル（縦線検出用）
       マスクを横方向に合計 → 行ごとのスコアの 1D プロファイル（横線検出用）
    3. しきい値以上の連続ランをクラスタ化し、各クラスタの中心を線位置とする
    4. 期待本数（cols-1 / rows-1）に一致したらその位置を採用、しなければ既定の
       grid 位置にフォールバックして警告を出す

切り取り時に区切り線そのものを含めないため、bbox の各内側に line_inset px
（デフォルト 3）詰めて切る。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    h = hex_code.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def canvas_size_from_grid(spec: dict) -> tuple[int, int]:
    grid = spec["grid"]
    cw, ch = grid["cell_size"]
    return cw * grid["cols"], ch * grid["rows"]


def detect_lines(
    arr: np.ndarray,
    line_rgb: tuple[int, int, int],
    tolerance: float,
    axis: int,
    expected_count: int,
    min_run_ratio: float,
) -> list[int]:
    """画像から区切り線位置を検出する。

    axis=0: 縦線を検出 → 戻り値は x 座標のリスト
    axis=1: 横線を検出 → 戻り値は y 座標のリスト

    min_run_ratio: 連続ランがこの比率（対象軸の長さに対する割合）以上ならピーク
        として採用。0.3 程度。
    """
    rgb = arr[..., :3].astype(np.int32)
    diff = rgb - np.array(line_rgb, dtype=np.int32)
    dist = np.sqrt((diff ** 2).sum(axis=-1))
    mask = dist <= tolerance  # H x W

    if axis == 0:
        # 縦線 → 各列で「マスクピクセルが縦に何個並んでいるか」スコア
        scores = mask.sum(axis=0)  # shape (W,)
        long_axis_len = mask.shape[0]
    else:
        scores = mask.sum(axis=1)  # shape (H,)
        long_axis_len = mask.shape[1]

    min_run = int(long_axis_len * min_run_ratio)
    above = scores >= min_run

    # 連続ラン → 中心位置
    positions: list[int] = []
    in_run = False
    start = 0
    for i, v in enumerate(above):
        if v and not in_run:
            in_run = True
            start = i
        elif not v and in_run:
            in_run = False
            positions.append((start + i - 1) // 2)
    if in_run:
        positions.append((start + len(above) - 1) // 2)

    # 期待本数に達するまで最も強いピークから順に拾う、というロジックも考えられるが
    # 今回はシンプルに「全クラスタを返す → 期待本数と一致するか」で判定する。
    return positions


def compute_boundaries(
    detected: list[int],
    expected_internal: int,
    canvas_len: int,
) -> tuple[list[int], bool]:
    """検出された内部区切り線位置から、全境界（端含む）リストを作る。

    戻り値: (境界リスト [0, ..., canvas_len], 検出成功フラグ)

    expected_internal と検出本数が一致すれば検出位置を採用、しなければ
    均等分割でフォールバック。
    """
    if len(detected) == expected_internal:
        return [0, *detected, canvas_len], True
    # フォールバック: 均等分割
    step = canvas_len / (expected_internal + 1)
    fallback = [round(step * (i + 1)) for i in range(expected_internal)]
    return [0, *fallback, canvas_len], False


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice a grid-based parts sheet via detected grid lines.")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--image", required=True, help="Generated sheet PNG")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--line-inset", type=int, default=3, help="Crop inside the detected line by this many pixels")
    parser.add_argument(
        "--post-trim",
        type=int,
        default=4,
        help="切り取った後に外周をこのピクセル数だけ追加で削除する。"
        "区切り線のアンチエイリアスやはみ出しの残骸を確実に除去するため。",
    )
    parser.add_argument("--no-resize", action="store_true", help="Skip resize-to-canvas safety step")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    if "grid" not in spec:
        print("ERROR: 仕様 JSON に grid フィールドがありません。", file=sys.stderr)
        return 2

    sheet = Image.open(args.image).convert("RGBA")
    expected_w, expected_h = canvas_size_from_grid(spec)

    if sheet.size != (expected_w, expected_h):
        if args.no_resize:
            print(
                f"[slice] WARN: 画像サイズ {sheet.size} が期待値 "
                f"{(expected_w, expected_h)} と異なりますが --no-resize 指定のためそのまま使います。"
            )
        else:
            print(f"[slice] 画像サイズ {sheet.size} を {(expected_w, expected_h)} へリサイズします。")
            sheet = sheet.resize((expected_w, expected_h), Image.LANCZOS)

    arr = np.array(sheet)
    grid = spec["grid"]
    cols, rows = grid["cols"], grid["rows"]
    canvas_w, canvas_h = expected_w, expected_h

    line_color = spec.get("grid_line_color", "#FF00FF")
    line_tol = float(spec.get("grid_line_tolerance", 80))
    line_rgb = hex_to_rgb(line_color)

    print(f"[slice] 区切り線検出: color={line_color}, tolerance={line_tol}")

    detected_x = detect_lines(arr, line_rgb, line_tol, axis=0, expected_count=cols - 1, min_run_ratio=0.3)
    detected_y = detect_lines(arr, line_rgb, line_tol, axis=1, expected_count=rows - 1, min_run_ratio=0.3)
    print(f"[slice] 検出: 縦線 {len(detected_x)}本（期待 {cols - 1}）, 横線 {len(detected_y)}本（期待 {rows - 1}）")

    x_boundaries, x_ok = compute_boundaries(detected_x, cols - 1, canvas_w)
    y_boundaries, y_ok = compute_boundaries(detected_y, rows - 1, canvas_h)
    if not x_ok:
        print(f"[slice] WARN: 縦線検出が期待本数と不一致。均等分割にフォールバックします: {x_boundaries}")
    if not y_ok:
        print(f"[slice] WARN: 横線検出が期待本数と不一致。均等分割にフォールバックします: {y_boundaries}")
    if x_ok and y_ok:
        print(f"[slice] 境界 x={x_boundaries}, y={y_boundaries}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    inset = args.line_inset
    post_trim = max(0, args.post_trim)

    written: list[Path] = []
    for i, part in enumerate(spec["parts"]):
        col, row = part["cell"]
        sc, sr = part.get("span", [1, 1])
        if not (0 <= col and 0 <= row and col + sc <= cols and row + sr <= rows):
            print(f"[slice] ERROR: part #{i} cell={[col, row]} span={[sc, sr]} がグリッド外", file=sys.stderr)
            return 2

        x1 = x_boundaries[col] + (inset if col > 0 else 0)
        y1 = y_boundaries[row] + (inset if row > 0 else 0)
        x2 = x_boundaries[col + sc] - (inset if col + sc < cols else 0)
        y2 = y_boundaries[row + sr] - (inset if row + sr < rows else 0)

        cropped = sheet.crop((x1, y1, x2, y2))

        # 切り取り後に外周を一律トリム。区切り線のアンチエイリアスや、AI が描いた
        # 線の太さの揺らぎで残った色を確実に除去するための保険。
        if post_trim > 0:
            cw, ch = cropped.size
            if cw > post_trim * 2 and ch > post_trim * 2:
                cropped = cropped.crop((post_trim, post_trim, cw - post_trim, ch - post_trim))

        filename = part.get("filename") or f"part_{i:02d}.png"
        if not filename.lower().endswith(".png"):
            filename += ".png"
        out_path = out_dir / filename
        cropped.save(out_path, format="PNG")
        written.append(out_path)
        print(
            f"[slice] cell=[{col},{row}] span=[{sc},{sr}] bbox=[{x1},{y1},{x2},{y2}] "
            f"post_trim={post_trim} final={cropped.size} -> {out_path}"
        )

    print(f"[slice] {len(written)} 個のパーツを {out_dir} に書き出しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
