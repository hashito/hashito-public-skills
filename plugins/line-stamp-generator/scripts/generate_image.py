#!/usr/bin/env python3
"""仕様 JSON から gpt-image-2 を呼び出してデザインパーツの一枚絵を生成する。

仕様はグリッドベース。`grid.cols × grid.rows` の格子に分けたキャンバスの上に、
各パーツを `cell` で指定したマスから `span` 個分のセルにわたって描かせる。
グリッドを明示すると AI が配置を守りやすく、後段の切り出しも単純な算術で行える。

OpenAI API キーは環境変数 OPENAI_API_KEY または GPT_API_KEY から読む。
スクリプト側では保存しない。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from openai import OpenAI


def hex_to_color_words(hex_code: str) -> str:
    h = hex_code.lstrip("#")
    if len(h) != 6:
        return hex_code
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{h.upper()} (RGB {r},{g},{b})"


def canvas_size_from_grid(spec: dict) -> tuple[int, int]:
    grid = spec["grid"]
    cw, ch = grid["cell_size"]
    return cw * grid["cols"], ch * grid["rows"]


def cell_bbox(spec: dict, cell: list[int], span: list[int]) -> tuple[int, int, int, int]:
    cw, ch = spec["grid"]["cell_size"]
    col, row = cell
    sc, sr = span
    x1, y1 = col * cw, row * ch
    x2, y2 = x1 + sc * cw, y1 + sr * ch
    return x1, y1, x2, y2


def build_prompt(spec: dict) -> str:
    theme = spec["theme"].strip()
    grid = spec["grid"]
    cols, rows = grid["cols"], grid["rows"]
    cw, ch = grid["cell_size"]
    canvas_w, canvas_h = canvas_size_from_grid(spec)
    bg = hex_to_color_words(spec["background_color"])
    line_color_hex = spec.get("grid_line_color", "#FF00FF")
    line = hex_to_color_words(line_color_hex)

    parts_lines = []
    for i, part in enumerate(spec["parts"], start=1):
        cell = part["cell"]
        span = part.get("span", [1, 1])
        x1, y1, x2, y2 = cell_bbox(spec, cell, span)
        w, h = x2 - x1, y2 - y1
        if span == [1, 1]:
            cell_desc = f"cell (col={cell[0]}, row={cell[1]}) [{w}x{h}px around x={x1},y={y1}]"
        else:
            cell_desc = (
                f"cells col={cell[0]}..{cell[0] + span[0] - 1}, row={cell[1]}..{cell[1] + span[1] - 1} "
                f"[spanning {span[0]}x{span[1]} cells = {w}x{h}px around x={x1},y={y1}]"
            )
        parts_lines.append(f"  ({i}) {cell_desc}: {part['description']}")

    n_v = cols - 1  # internal vertical lines
    n_h = rows - 1  # internal horizontal lines

    return (
        f"Create a {canvas_w}x{canvas_h} pixel image divided into a {cols}-column by "
        f"{rows}-row grid. Each cell is approximately {cw}x{ch} pixels. "
        f"Column 0 is leftmost, row 0 is topmost.\n"
        f"\n"
        f"Overall visual theme (apply consistently to ALL parts): {theme}\n"
        f"\n"
        f"Background: fill all cells with solid {bg}. "
        f"This exact background color must NOT appear inside any part; "
        f"keep parts visually distinct from the background.\n"
        f"\n"
        f"=== VERY IMPORTANT: GRID LINES ===\n"
        f"Draw {n_v} vertical and {n_h} horizontal {line} grid lines on the INTERNAL "
        f"cell boundaries. These lines must be:\n"
        f"  - solid bright {line} color (NOT used anywhere else in the image)\n"
        f"  - approximately 4-6 pixels thick\n"
        f"  - perfectly straight and continuous from one edge of the canvas to the other\n"
        f"  - placed only on internal cell boundaries (NOT on the outer edges of the canvas)\n"
        f"These grid lines are crucial — they will be used to crop each part. "
        f"The lines must be clearly visible and the {line} color must not bleed into the parts.\n"
        f"\n"
        f"Place each part inside its assigned cell(s). Leave a small margin between the "
        f"part and the surrounding grid lines so the cropping does not clip the part.\n"
        f"Empty cells (those not listed below) must remain pure background color (still "
        f"separated from other cells by the {line} grid lines).\n"
        f"\n"
        f"Parts:\n"
        + "\n".join(parts_lines)
        + "\n\nMaintain a unified visual style so all parts look like they belong to the same "
        f"project. Each part should have clean edges against the background."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a design-parts sheet via gpt-image-2.")
    parser.add_argument("--spec", required=True, help="Path to parts spec JSON")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--model", default="gpt-image-2", help="Image model id (default: gpt-image-2)")
    parser.add_argument(
        "--size",
        default=None,
        help="Override output size (e.g. 1024x1024). Defaults to grid-derived canvas size",
    )
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GPT_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY (または GPT_API_KEY) が設定されていません。", file=sys.stderr)
        return 2
    os.environ["OPENAI_API_KEY"] = api_key

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    if "grid" not in spec:
        print("ERROR: 仕様 JSON に grid フィールドがありません。", file=sys.stderr)
        return 2

    prompt = build_prompt(spec)

    if args.size:
        size = args.size
    else:
        w, h = canvas_size_from_grid(spec)
        size = f"{w}x{h}"

    print(f"[generate] model={args.model} size={size} quality={args.quality}")
    print(f"[generate] grid={spec['grid']['cols']}x{spec['grid']['rows']}, cell={spec['grid']['cell_size']}")
    print(f"[generate] prompt (head):\n{prompt[:400]}{'...' if len(prompt) > 400 else ''}")

    client = OpenAI()
    result = client.images.generate(
        model=args.model,
        prompt=prompt,
        size=size,
        quality=args.quality,
        n=1,
    )

    b64 = result.data[0].b64_json
    if b64 is None:
        print("ERROR: API レスポンスに b64_json がありません。", file=sys.stderr)
        return 3

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(b64))
    print(f"[generate] 書き出し: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
