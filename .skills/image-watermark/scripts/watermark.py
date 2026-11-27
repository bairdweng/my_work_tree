#!/usr/bin/env python3
"""批量平铺斜向水印。

- 不覆盖原图，成品输出到独立目录。
- 支持单张图片或整个目录（jpg / jpeg / png / webp）。
- 依赖 Pillow：pip3 install pillow
"""

import argparse
import glob
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("缺少 Pillow，请先运行：pip3 install pillow")


# 跨平台默认字体兜底；中文环境优先 CJK 字体，找不到再退西文字体
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

IMG_EXTS = ("*.jpg", "*.jpeg", "*.png", "*.webp")


def default_font_path():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def load_font(path, size):
    fp = path or default_font_path()
    if fp:
        return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def add_tile_watermark(img, text, font, color, alpha, angle, gap_x, gap_y):
    """返回叠加平铺斜向水印后的 RGBA 图。"""
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    w, h = img.size
    for y in range(0, h, gap_y):
        for x in range(0, w, gap_x):
            draw.text((x, y), text, font=font, fill=(*color, alpha))
    layer = layer.rotate(angle, expand=False, resample=Image.BICUBIC)
    return Image.alpha_composite(img, layer)


def process(src, dst, args):
    img = Image.open(src)
    font = load_font(args.font, args.font_size)
    out = add_tile_watermark(
        img, args.text, font, args.color, args.alpha,
        args.angle, args.gap_x, args.gap_y,
    )
    # PNG 保留透明通道，其余转 RGB 避免保存异常
    if not dst.lower().endswith(".png"):
        out = out.convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if dst.lower().endswith(".png"):
        out.save(dst)
    else:
        out.save(dst, quality=args.quality)


def collect_inputs(path):
    if os.path.isfile(path):
        return [path]
    files = []
    for ext in IMG_EXTS:
        files += glob.glob(os.path.join(path, ext))
    return sorted(set(files))


def parse_color(text):
    parts = [int(c) for c in text.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("颜色需为 R,G,B 三个数字，如 120,120,120")
    return tuple(parts)


def main():
    ap = argparse.ArgumentParser(description="批量平铺斜向水印（不覆盖原图）")
    ap.add_argument("-i", "--input", required=True, help="图片文件或所在目录")
    ap.add_argument("-o", "--output", help="输出目录；默认 <输入目录>/watermarked")
    ap.add_argument("--text", required=True, help="水印文字")
    ap.add_argument("--font", help="字体文件路径（可选，按平台自动兜底）")
    ap.add_argument("--font-size", type=int, default=28, help="字号，默认 28")
    ap.add_argument("--alpha", type=int, default=60, help="不透明度 0-255，默认 60")
    ap.add_argument("--angle", type=float, default=30, help="倾斜角度，默认 30")
    ap.add_argument("--gap-x", type=int, default=320, help="水平间距，默认 320")
    ap.add_argument("--gap-y", type=int, default=170, help="垂直间距，默认 170")
    ap.add_argument("--color", default="120,120,120", type=parse_color, help="R,G,B，默认 120,120,120")
    ap.add_argument("--quality", type=int, default=92, help="JPEG 质量，默认 92")
    args = ap.parse_args()

    files = collect_inputs(args.input)
    if not files:
        sys.exit("未找到可处理的图片（jpg / jpeg / png / webp）")

    outdir = args.output or os.path.join(os.path.dirname(os.path.abspath(files[0])), "watermarked")
    for src in files:
        dst = os.path.join(outdir, os.path.basename(src))
        process(src, dst, args)
        print("已输出:", dst)

    print(f"完成，共 {len(files)} 张，输出目录：{outdir}")


if __name__ == "__main__":
    main()
