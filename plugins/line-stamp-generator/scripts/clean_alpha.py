#!/usr/bin/env python3
"""AI 生成画像の背景クロマキー透過処理パイプライン。

「宝石本体だけを綺麗に抜く」用途を想定して、

    クロマキー → マスク収縮(erode) → Despill → Defringe → 羽化(feather)

の順で処理する。AI 画像のエッジには「背景色＋パーツ色」が混ざった半透明帯
（フリンジ）が必ず生じるため、単純なクロマキーだけでは縁に背景色が残る。
本パイプラインは外周の発光・粒子も一緒に削るが、その代わり輪郭が綺麗になる。

各ステップの役割:

  1. クロマキー
     指定背景色 ± tolerance のピクセルを透明候補にする。AI 画像の背景はまだら
     なので、tolerance は緩めに（30-60）。

  2. マスク収縮 (Erode)
     アルファマスクを N px 内側に縮める。これにより、背景とパーツ色が混じった
     エッジ帯（半透明フリンジ）と、外側の発光・粒子のような薄い領域がまとめて
     透明側に倒れる。デフォルト 2px。

  3. Despill (背景色のスピル除去)
     パーツ内部に残る「背景色の漏れ込み」を抑える。背景色の主成分（緑なら G、
     マゼンタなら R）が、他成分の最大値を超えている分だけ削る。
     これは Nuke / Fusion 等の VFX で使われる定番の despill アルゴリズムを
     簡略化したもの。

  4. Defringe (輪郭の RGB 補正)
     透明領域 (alpha=0) の RGB を、最近傍の不透明ピクセルの色で塗り直す。
     こうしておくと、後段の Gaussian feather で半透明化された境界帯にも
     パーツ本体の色が出てきて、緑などの背景色が滲まない。
     scipy.ndimage.distance_transform_edt の最近傍インデックス機能を使う。

  5. 羽化 (Feather)
     最終的にアルファチャンネルを軽く Gaussian でぼかし、UI に貼った時の
     ジャギを和らげる。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import distance_transform_edt


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    h = hex_code.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def chroma_key(arr: np.ndarray, bg_rgb: tuple[int, int, int], tolerance: float) -> np.ndarray:
    """RGB 距離で背景マスクを作る。戻り値は alpha (uint8, 0 or 255)。"""
    rgb = arr[..., :3].astype(np.int32)
    dist = np.sqrt(((rgb - np.array(bg_rgb, dtype=np.int32)) ** 2).sum(axis=-1))
    bg_mask = dist <= tolerance
    return np.where(bg_mask, 0, 255).astype(np.uint8)


def erode_alpha(alpha: np.ndarray, px: int) -> np.ndarray:
    """アルファマスクを px ピクセル内側に収縮する。Pillow MinFilter(3) を px 回。"""
    if px <= 0:
        return alpha
    img = Image.fromarray(alpha, mode="L")
    for _ in range(px):
        img = img.filter(ImageFilter.MinFilter(3))
    return np.array(img)


def despill(arr: np.ndarray, bg_rgb: tuple[int, int, int]) -> None:
    """背景色の主成分が他より突出している分を削る（in-place）。

    緑背景なら G を、赤背景なら R を、マゼンタ背景なら R と B を抑える。
    """
    bg = np.array(bg_rgb, dtype=np.int32)
    # 各チャンネルの「背景に対する寄与」を考える。背景の各成分が高い順に主成分とみなし、
    # それらが他成分の最大より突出している分を削る。
    # 単純化: bg の各チャンネルが 128 以上のものを「主成分」とする。
    main_channels = [i for i in range(3) if bg[i] >= 128]
    if not main_channels:
        return
    other_max = np.max(
        np.stack([arr[..., i].astype(np.int32) for i in range(3) if i not in main_channels], axis=-1)
        if len([i for i in range(3) if i not in main_channels]) > 0
        else np.zeros((*arr.shape[:2], 1), dtype=np.int32),
        axis=-1,
    )
    for ch in main_channels:
        v = arr[..., ch].astype(np.int32)
        spill = np.maximum(v - other_max, 0)
        arr[..., ch] = (v - spill).clip(0, 255).astype(np.uint8)


def defringe(arr: np.ndarray, alpha: np.ndarray) -> None:
    """透明ピクセルの RGB を最近傍の不透明ピクセルの色で埋める（in-place）。

    こうすると、後段で Gaussian blur をかけた際に縁の半透明部分に背景色が
    出ず、パーツ色が自然に減衰する。
    """
    inside = alpha >= 128
    if not inside.any() or inside.all():
        return
    # 距離変換: ~inside（透明領域）の各点について、最近傍 inside 点の座標を返す
    _, indices = distance_transform_edt(~inside, return_indices=True)
    # indices: shape (2, H, W), [y_index, x_index]
    src_y = indices[0]
    src_x = indices[1]
    outside = ~inside
    arr[outside, 0] = arr[src_y[outside], src_x[outside], 0]
    arr[outside, 1] = arr[src_y[outside], src_x[outside], 1]
    arr[outside, 2] = arr[src_y[outside], src_x[outside], 2]


def feather_alpha(alpha: np.ndarray, radius: float) -> np.ndarray:
    if radius <= 0:
        return alpha
    img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=radius))
    return np.array(img)


def remove_color_fringe(
    arr: np.ndarray,
    alpha: np.ndarray,
    fringe_rgb: tuple[int, int, int],
    fringe_tolerance: float,
) -> None:
    """グリッド線色（マゼンタ等）が切り出し後に縁に残る現象を除去する（in-place）。

    クロマキー (bg-color) とは別に、もう 1 色だけ「縁に残る可能性のある色」を
    アルファ 0 に倒す。`slice_image.py` でグリッド線を完全に除去しきれなかった
    場合に、本パスで追加除去できる。
    """
    rgb = arr[..., :3].astype(np.int32)
    diff = rgb - np.array(fringe_rgb, dtype=np.int32)
    dist = np.sqrt((diff ** 2).sum(axis=-1))
    fringe_mask = dist <= fringe_tolerance
    alpha[fringe_mask] = 0


def clean_one(
    src: Image.Image,
    bg_rgb: tuple[int, int, int],
    tolerance: float,
    erode: int,
    do_despill: bool,
    do_defringe: bool,
    feather: float,
    grid_line_rgb: tuple[int, int, int] | None = None,
    grid_line_tolerance: float = 80.0,
) -> Image.Image:
    arr = np.array(src.convert("RGBA"))

    alpha = chroma_key(arr, bg_rgb, tolerance)
    if grid_line_rgb is not None:
        remove_color_fringe(arr, alpha, grid_line_rgb, grid_line_tolerance)
    alpha = erode_alpha(alpha, erode)
    if do_despill:
        despill(arr, bg_rgb)
    if do_defringe:
        defringe(arr, alpha)
    alpha = feather_alpha(alpha, feather)

    arr[..., 3] = alpha
    return Image.fromarray(arr, mode="RGBA")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean AI-generated background to clean alpha.")
    parser.add_argument("--in-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--bg-color", required=True, help="Background hex like #00FF00")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=50.0,
        help="クロマキーのRGB距離閾値（30-60が良い）。省略時 50。",
    )
    parser.add_argument(
        "--erode",
        type=int,
        default=2,
        help="アルファマスクを内側に収縮するピクセル数（フリンジ・外周発光除去）。省略時 2。",
    )
    parser.add_argument("--no-despill", action="store_false", dest="despill", default=True,
                        help="Despill (背景色のスピル除去) を無効化")
    parser.add_argument("--no-defringe", action="store_false", dest="defringe", default=True,
                        help="Defringe (輪郭RGB補正) を無効化")
    parser.add_argument(
        "--feather",
        type=float,
        default=1.0,
        help="アルファエッジの羽化半径 (px)。0 で完全二値。省略時 1.0。",
    )
    parser.add_argument(
        "--grid-line-color",
        default=None,
        help="グリッド線色（例: #FF00FF）を指定すると、その色近傍ピクセルもアルファ 0 に倒す。"
        "slice_image.py で除去しきれなかったマゼンタ縁などを掃除する。"
        " 指定しなければグリッド線除去はスキップ。",
    )
    parser.add_argument(
        "--grid-line-tolerance",
        type=float,
        default=80.0,
        help="--grid-line-color の許容 RGB 距離。既定 80。",
    )
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bg_rgb = hex_to_rgb(args.bg_color)
    grid_line_rgb = hex_to_rgb(args.grid_line_color) if args.grid_line_color else None
    pngs = sorted(in_dir.glob("*.png"))
    if not pngs:
        print(f"[clean] {in_dir} に PNG がありません。", file=sys.stderr)
        return 2

    for p in pngs:
        src = Image.open(p)
        cleaned = clean_one(
            src,
            bg_rgb,
            args.tolerance,
            args.erode,
            args.despill,
            args.defringe,
            args.feather,
            grid_line_rgb=grid_line_rgb,
            grid_line_tolerance=args.grid_line_tolerance,
        )
        out_path = out_dir / p.name
        cleaned.save(out_path, format="PNG")
        grid_msg = (
            f" grid_line={args.grid_line_color}/{args.grid_line_tolerance}"
            if grid_line_rgb is not None
            else ""
        )
        print(
            f"[clean] {p.name} -> {out_path} "
            f"(tol={args.tolerance}, erode={args.erode}, "
            f"despill={args.despill}, defringe={args.defringe}, feather={args.feather}{grid_msg})"
        )

    print(f"[clean] {len(pngs)} 個を処理しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
