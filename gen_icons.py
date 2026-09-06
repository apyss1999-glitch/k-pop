#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_icons.py
------------
產生 K-Pop 女團推薦指南 PWA 所需的所有 App Icon（原創設計，非任何團體/唱片公司素材）。

設計說明：
- 背景採用與網站標題相同的品牌漸層色（粉紅 #ec4899 -> 紫色 #8b5cf6，45 度角）。
- 中央置放白色「K」字母標誌（Poppins Bold），代表 K-Pop。
- 一般圖示 (any) 會加上圓角，貼近 iOS/Android 圖示的觀感。
- Maskable 圖示 (192 / 512) 採滿版方形設計，並將字母縮小置中，
  確保被系統裁切成圓形或圓角方形時，主要圖形不會被切掉（safe zone）。

使用方式：
    python3 gen_icons.py
執行後會在 ./icons 資料夾產生所有尺寸的 PNG 圖示。
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---- 基本設定 ----
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# 標準 PWA 圖示尺寸
STANDARD_SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]
# 需要另外產生 maskable（滿版安全區）版本的尺寸
MASKABLE_SIZES = [192, 512]

COLOR_FROM = (236, 72, 153)   # #ec4899 粉紅
COLOR_TO = (139, 92, 246)     # #8b5cf6 紫色

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def find_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_gradient_background(size, supersample=4):
    """建立 45 度角的粉紫漸層方形背景（使用 numpy 向量運算 + 超取樣讓漸層更平滑）。"""
    hi = size * supersample
    ys, xs = np.mgrid[0:hi, 0:hi]
    max_sum = (hi - 1) * 2
    t = (xs + ys).astype(np.float64) / max_sum  # 0.0 ~ 1.0 的對角線漸層比例

    from_arr = np.array(COLOR_FROM, dtype=np.float64)
    to_arr = np.array(COLOR_TO, dtype=np.float64)

    rgb = from_arr[None, None, :] + (to_arr - from_arr)[None, None, :] * t[:, :, None]
    rgb = rgb.astype(np.uint8)

    base = Image.fromarray(rgb, mode="RGB")
    base = base.resize((size, size), Image.LANCZOS)
    return base


def round_corners(img, radius_ratio=0.22):
    """將方形圖片裁切成圓角方形（透明背景）。"""
    size = img.size[0]
    radius = int(size * radius_ratio)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def draw_logo_letter(img, scale=0.58):
    """在圖片中央繪製白色『K』字母標誌。"""
    size = img.size[0]
    draw = ImageDraw.Draw(img)
    font_size = int(size * scale)
    font = find_font(font_size)
    text = "K"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2 - bbox[0]
    y = (size - text_h) / 2 - bbox[1]
    # 加一層淡淡陰影，增加立體感
    shadow_offset = max(1, size // 64)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 90))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    return img


def build_icon(size, maskable=False):
    bg = make_gradient_background(size).convert("RGBA")
    if maskable:
        # Maskable：滿版方形、字母縮小，確保安全區內不被裁切
        icon = draw_logo_letter(bg, scale=0.42)
    else:
        icon = round_corners(bg, radius_ratio=0.22)
        icon = draw_logo_letter(icon, scale=0.58)
    return icon


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for size in STANDARD_SIZES:
        icon = build_icon(size, maskable=False)
        filename = os.path.join(OUTPUT_DIR, f"icon-{size}.png")
        icon.save(filename, format="PNG")
        print(f"已產生 {filename}")

    for size in MASKABLE_SIZES:
        icon = build_icon(size, maskable=True)
        filename = os.path.join(OUTPUT_DIR, f"icon-maskable-{size}.png")
        icon.save(filename, format="PNG")
        print(f"已產生 {filename}")

    # 額外輸出一個多尺寸的 favicon.ico，方便瀏覽器分頁使用
    favicon_sizes = [16, 32]
    favicon_images = [build_icon(s, maskable=False) for s in favicon_sizes]
    favicon_path = os.path.join(OUTPUT_DIR, "favicon.ico")
    favicon_images[0].save(
        favicon_path,
        format="ICO",
        sizes=[(s, s) for s in favicon_sizes],
    )
    print(f"已產生 {favicon_path}")

    print("\n全部圖示已產生完成！")


if __name__ == "__main__":
    main()
