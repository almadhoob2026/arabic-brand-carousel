#!/usr/bin/env python3
"""Regenerate the sample images in this folder.

They are original, procedurally generated artwork (no photos, fonts or third-party
material), so the demo deck can declare rights: "generated".
Run: python examples/assets/make_samples.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent


def gradient(size, top, bottom):
    w, h = size
    img = Image.new('RGB', size)
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        row = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        for x in range(w):
            px[x, y] = row
    return img


def desk_scene(path, size=(1620, 2025), seed=7):
    """Warm abstract 'study desk' composition: soft light, paper sheets, lamp glow."""
    rnd = random.Random(seed)
    w, h = size
    img = gradient(size, (58, 46, 38), (22, 24, 30))
    glow = Image.new('L', size, 0)
    ImageDraw.Draw(glow).ellipse((w * .45, -h * .1, w * 1.25, h * .55), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    img = Image.composite(Image.new('RGB', size, (243, 201, 105)), img, glow.point(lambda v: v * .55))
    layer = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(7):  # paper sheets
        cx, cy = rnd.uniform(.15, .85) * w, rnd.uniform(.45, .9) * h
        sw, sh = rnd.uniform(.25, .4) * w, rnd.uniform(.3, .42) * h
        ang = math.radians(rnd.uniform(-18, 18))
        pts = [(-sw / 2, -sh / 2), (sw / 2, -sh / 2), (sw / 2, sh / 2), (-sw / 2, sh / 2)]
        pts = [(cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)) for x, y in pts]
        shade = rnd.randint(215, 245)
        d.polygon(pts, fill=(shade, shade - 6, shade - 18, 235))
        for k in range(1, 9):  # ruled lines
            f = k / 10
            a = (pts[0][0] + (pts[3][0] - pts[0][0]) * f, pts[0][1] + (pts[3][1] - pts[0][1]) * f)
            b = (pts[1][0] + (pts[2][0] - pts[1][0]) * f, pts[1][1] + (pts[2][1] - pts[1][1]) * f)
            d.line([a, b], fill=(150, 160, 175, 120), width=3)
    d.ellipse((w * .62, h * .08, w * .9, h * .3), fill=(255, 236, 180, 200))  # lamp
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img.convert('RGBA'), layer).convert('RGB')
    img.save(path, 'JPEG', quality=84, optimize=True, progressive=True)


def bars_chart(path, size=(1000, 1000)):
    """Simple illustrative chart graphic (no data claims)."""
    img = gradient(size, (35, 42, 51), (24, 28, 34))
    d = ImageDraw.Draw(img)
    w, h = size
    for i, v in enumerate((.35, .55, .48, .72, .9)):
        x0 = 110 + i * 165
        d.rounded_rectangle((x0, h - 120 - v * 650, x0 + 110, h - 120), 22,
                            fill=(243, 201, 105) if i == 4 else (90, 104, 122))
    d.line((80, h - 118, w - 80, h - 118), fill=(181, 189, 200), width=4)
    img.save(path, 'PNG', optimize=True)


LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <rect x="6" y="6" width="108" height="108" rx="28" fill="#F3C969"/>
  <path d="M34 78 L60 34 L86 78 Z" fill="none" stroke="#111418" stroke-width="10" stroke-linejoin="round"/>
  <circle cx="60" cy="64" r="8" fill="#111418"/>
</svg>
"""

if __name__ == '__main__':
    desk_scene(HERE / 'desk.jpg')
    bars_chart(HERE / 'chart.png')
    (HERE / 'logo.svg').write_text(LOGO, encoding='utf-8')
    print('Wrote desk.jpg, chart.png, logo.svg')
