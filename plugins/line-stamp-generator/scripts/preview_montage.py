#!/usr/bin/env python3
"""透過 PNG 群を 1 枚のモンタージュ画像にまとめてプレビューする。

LINE スタンプ生成パイプラインの各段階（stamps_raw / stamps_alpha / output/stamps）
で、8 枚（または任意枚数）の見え方を 1 枚にまとめて目視確認するために使う。

- 透明背景の PNG を、薄いグレーの背景に貼り付けて見やすくする
- グリッドは入力枚数から自動推定（4→2x2、6→2x3、8→2x4、12→3x4、16→4x4 等）
- セルサイズはソース PNG の最大サイズに合わせる
"""

from __future__ import annotations

import argparse
import sys
from math import ceil
from pathlib import Path

from PIL import Image


def auto_grid(n: int) -> tuple[int, int]:
    """枚数から (cols, rows) を自動推定。"""
    presets = {
        1: (1, 1),
        2: (2, 1),
        3: (3, 1),
        4: (2, 2),
        5: (3, 2),
        6: (3, 2),
        7: (4, 2),
        8: (4, 2),
        9: (3, 3),
        10: (5, 2),
        11: (4, 3),
        12: (4, 3),
        16: (4, 4),
        20: (5, 4),
        24: (6, 4),
        32: (8, 4),
        40: (8, 5),
    }
    if n in presets:
        return presets[n]
    # それ以外は 4 列固定
    cols = 4
    rows = ceil(n / cols)
    return cols, rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Render PNGs into a single montage preview.")
    parser.add_argument("--in-dir", required=True, help="Directory containing PNG stamps")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument(
        "--grid",
        default=None,
        help="'colsxrows' (e.g. 4x2). Omit for auto-detect from file count.",
    )
    parser.add_argument(
        "--bg",
        default="#F5F5F5",
        help="Background color hex (default #F5F5F5 light gray). 'transparent' で透明背景。",
    )
    parser.add_argument(
        "--cell",
        default=None,
        help="セルサイズ 'WxH'。省略で各ソース PNG の最大サイズに合わせる。",
    )
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    pngs = sorted(in_dir.glob("*.png"))
    if not pngs:
        print(f"[montage] {in_dir} に PNG がありません。", file=sys.stderr)
        return 2

    # グリッドサイズ
    if args.grid:
        try:
            cols, rows = map(int, args.grid.lower().split("x"))
        except ValueError:
            print(f"[montage] --grid は 'WxH' 形式で指定してください: {args.grid!r}", file=sys.stderr)
            return 2
    else:
        cols, rows = auto_grid(len(pngs))
    if cols * rows < len(pngs):
        print(
            f"[montage] WARN: グリッド {cols}x{rows} = {cols * rows} 枠に対し PNG が "
            f"{len(pngs)} 枚あります。先頭 {cols * rows} 枚のみ使用します。"
        )
        pngs = pngs[: cols * rows]

    # セルサイズ
    if args.cell:
        try:
            cw, ch = map(int, args.cell.lower().split("x"))
        except ValueError:
            print(f"[montage] --cell は 'WxH' 形式で指定してください: {args.cell!r}", file=sys.stderr)
            return 2
    else:
        images = [Image.open(p) for p in pngs]
        cw = max(img.size[0] for img in images)
        ch = max(img.size[1] for img in images)

    # 背景
    if args.bg.lower() == "transparent":
        canvas = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    else:
        bg = args.bg.lstrip("#")
        r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
        canvas = Image.new("RGB", (cw * cols, ch * rows), (r, g, b))

    for i, p in enumerate(pngs):
        s = Image.open(p).convert("RGBA")
        col, row = i % cols, i // cols
        # セル内中央配置
        x = col * cw + (cw - s.size[0]) // 2
        y = row * ch + (ch - s.size[1]) // 2
        canvas.paste(s, (x, y), s)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG")
    print(f"[montage] {len(pngs)} 枚を {cols}x{rows} で配置 ({cw}x{ch}/cell) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
