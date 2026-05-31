#!/usr/bin/env python3
"""LINE クリエイターズスタンプ規格に合わせて透過 PNG を整える。

LINE 公式仕様:
  - スタンプ画像 (stamps)        : 最大 370 x 320 px、透過 PNG
  - メイン画像 (main)            : 240 x 240 px、透過 PNG
  - トークルームタブ画像 (tab)   : 96 x 74 px、透過 PNG

各入力 PNG を「アスペクト比を保ったまま」最大枠に contain → 中央配置で
透明パディング、として書き出す。スタンプ本体の縁にあるアルファを基準に
バウンディングボックスを取り直すので、AI が生成した余白の偏りも補正される。

入力:
  --in-dir <透過 PNG 群>
  --out-dir <出力先ルート>
出力:
  <out-dir>/stamps/*.png         (370x320 max)
  <out-dir>/main.png             (240x240、1 枚目をメインに採用、--main で指定可能)
  <out-dir>/tab.png              (96x74、--main と同じソースを採用)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image


LINE_STAMP_MAX = (370, 320)
LINE_MAIN_SIZE = (240, 240)
LINE_TAB_SIZE = (96, 74)


def alpha_bbox(img: Image.Image, alpha_threshold: int = 8) -> tuple[int, int, int, int] | None:
    """アルファチャンネルの bbox を返す。中身が無ければ None。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[-1]
    # alpha が threshold 以下を背景扱い
    mask = alpha.point(lambda v: 255 if v > alpha_threshold else 0)
    return mask.getbbox()


def fit_into(img: Image.Image, target: tuple[int, int], alpha_threshold: int) -> Image.Image:
    """alpha bbox でトリム → target に収まるよう contain → 中央配置で透明パディング。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    bbox = alpha_bbox(img, alpha_threshold=alpha_threshold)
    if bbox is None:
        # 完全透明: 何もできないので透明キャンバスを返す
        return Image.new("RGBA", target, (0, 0, 0, 0))

    cropped = img.crop(bbox)
    cw, ch = cropped.size
    tw, th = target

    scale = min(tw / cw, th / ch)
    new_w = max(1, int(round(cw * scale)))
    new_h = max(1, int(round(ch * scale)))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", target, (0, 0, 0, 0))
    canvas.paste(resized, ((tw - new_w) // 2, (th - new_h) // 2), resized)
    return canvas


def center_crop_into(
    img: Image.Image,
    target: tuple[int, int],
    alpha_threshold: int,
    zoom: float = 1.0,
) -> Image.Image:
    """主たる画像の被写体中心を target アスペクト比で切り抜いて拡縮する（cover 方式）。

    contain（fit_into）は余白が出るが、center_crop は余白を出さず target を満たす。
    タグ画像 (96x74 など) のようにアイコン的に主題を大きく見せたい場合に使う。

    手順:
      1. alpha bbox を取り、被写体の存在範囲を確定
      2. **bbox サイズを基準に** target_ratio の矩形を作り、bbox 中心に揃える
         （ソース画像全体を基準にすると余白を含めてしまい、結果が contain と変わらないため）
      3. zoom > 1.0 ならさらに矩形を縮小して被写体をクローズアップ（既定 1.0 = bbox いっぱい）
      4. 画像範囲にクランプして切り抜き、target サイズへリサイズ
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    bbox = alpha_bbox(img, alpha_threshold=alpha_threshold)
    if bbox is None:
        return Image.new("RGBA", target, (0, 0, 0, 0))

    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2

    iw, ih = img.size
    tw, th = target
    target_ratio = tw / th
    bbox_ratio = bw / bh

    # bbox に内接する target_ratio 矩形（被写体が必ず全て収まる最大サイズ）
    if bbox_ratio >= target_ratio:
        # bbox の方が target より横長 → bbox の縦いっぱい使って横を絞る
        crop_h = bh
        crop_w = int(round(bh * target_ratio))
    else:
        # bbox の方が target より縦長 → bbox の横いっぱい使って縦を絞る
        crop_w = bw
        crop_h = int(round(bw / target_ratio))

    # zoom > 1.0 で被写体に寄る（矩形を縮小）
    if zoom > 1.0:
        crop_w = max(1, int(round(crop_w / zoom)))
        crop_h = max(1, int(round(crop_h / zoom)))

    left = int(round(cx - crop_w / 2))
    top = int(round(cy - crop_h / 2))
    # 画像範囲にクランプ
    left = max(0, min(left, iw - crop_w))
    top = max(0, min(top, ih - crop_h))

    cropped = img.crop((left, top, left + crop_w, top + crop_h))
    return cropped.resize(target, Image.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resize transparent PNGs to LINE stamp specs.")
    parser.add_argument("--in-dir", required=True, help="Directory containing transparent PNGs")
    parser.add_argument("--out-dir", required=True, help="Output directory root")
    parser.add_argument(
        "--main",
        default=None,
        help="Filename within --in-dir to use as main.png / tab.png (default: first PNG alphabetically)",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=8,
        help="アルファ bbox 計算時の閾値（0-255）。羽化された輪郭の薄い部分を切り捨てる。",
    )
    parser.add_argument("--no-main", action="store_true", help="main.png / tab.png を生成しない")
    parser.add_argument(
        "--tab-mode",
        choices=["center-crop", "contain"],
        default="center-crop",
        help="tab.png の生成方式。center-crop（既定）= 主たる画像の被写体中心を 96x74 で切り抜いて拡縮（cover）。"
        " contain = アスペクト維持で 96x74 に収めて透明パディング（fit_into と同じ）。",
    )
    parser.add_argument(
        "--tab-zoom",
        type=float,
        default=1.0,
        help="tab center-crop 時のズーム倍率。1.0（既定）で被写体 bbox いっぱい。"
        "1.4〜1.8 で顔のクローズアップ。center-crop モード時のみ有効。",
    )
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    stamps_dir = out_dir / "stamps"
    stamps_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(in_dir.glob("*.png"))
    if not pngs:
        print(f"[resize] {in_dir} に PNG がありません。", file=sys.stderr)
        return 2

    for p in pngs:
        src = Image.open(p)
        out = fit_into(src, LINE_STAMP_MAX, args.alpha_threshold)
        out_path = stamps_dir / p.name
        out.save(out_path, format="PNG")
        print(f"[resize] stamp: {p.name} -> {out_path} ({out.size[0]}x{out.size[1]})")

    if not args.no_main:
        main_name = args.main if args.main else pngs[0].name
        main_src_path = in_dir / main_name
        if not main_src_path.exists():
            print(f"[resize] WARN: --main 指定の {main_name} が見つからないため先頭 PNG を使います。")
            main_src_path = pngs[0]
        main_src = Image.open(main_src_path)
        main_img = fit_into(main_src, LINE_MAIN_SIZE, args.alpha_threshold)
        main_img.save(out_dir / "main.png", format="PNG")
        print(f"[resize] main: {main_src_path.name} -> {out_dir / 'main.png'} ({LINE_MAIN_SIZE[0]}x{LINE_MAIN_SIZE[1]})")

        if args.tab_mode == "center-crop":
            tab_img = center_crop_into(main_src, LINE_TAB_SIZE, args.alpha_threshold, zoom=args.tab_zoom)
        else:
            tab_img = fit_into(main_src, LINE_TAB_SIZE, args.alpha_threshold)
        tab_img.save(out_dir / "tab.png", format="PNG")
        print(
            f"[resize] tab : {main_src_path.name} -> {out_dir / 'tab.png'} "
            f"({LINE_TAB_SIZE[0]}x{LINE_TAB_SIZE[1]}, mode={args.tab_mode})"
        )

    print(f"[resize] {len(pngs)} 枚のスタンプを {stamps_dir} に書き出しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
