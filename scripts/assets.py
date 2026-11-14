#!/usr/bin/env python3
"""Local, offline image/logo loading for the carousel renderer.

Images are read from disk only (never fetched), type-checked by their bytes rather
than their extension, and embedded as data URIs so the HTML stays self-contained.
"""
import base64
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageStat

MAX_BYTES = 10 * 1024 * 1024        # per file
MAX_TOTAL_BYTES = 40 * 1024 * 1024  # per deck
SCHEME = re.compile(r'^[A-Za-z][A-Za-z0-9+.-]+:')  # http:, data:, file: … (not C:\)
SVG_FORBIDDEN = re.compile(rb'<script|<foreignObject|\bon[a-z]+\s*=|(?:href|src)\s*=\s*["\']?\s*(?:https?:|//|data:)', re.I)

IMAGE_LAYOUTS = ('background', 'top', 'side')
IMAGE_FITS = ('cover', 'contain')
IMAGE_RIGHTS = ('owned', 'licensed', 'generated', 'client-supplied')
# Box (w, h) each layout displays the image in; used for resolution warnings.
LAYOUT_BOX = {'background': (1080, 1350), 'top': (910, 430), 'side': (400, 990), 'logo': (220, 56)}


def check_reference(src, field):
    """Validate a path string without touching the filesystem."""
    if not isinstance(src, str) or not src.strip() or len(src) > 500:
        raise ValueError(f'{field} must be a local file path')
    s = src.strip()
    if SCHEME.match(s) or s.startswith('//'):
        raise ValueError(f'{field} must be a local file path, not a URL: {s[:60]}')


def resolve(src, base_dir):
    p = Path(src).expanduser()
    if not p.is_absolute():
        p = Path(base_dir or '.') / p
    p = p.resolve()
    if not p.is_file():
        raise FileNotFoundError(f'Image not found: {src} (resolved to {p})')
    return p


def _sniff(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    head = data[:1024].lstrip().lower()
    if head.startswith(b'<svg') or (head.startswith(b'<?xml') and b'<svg' in data[:4096].lower()):
        return 'image/svg+xml'
    return None


@lru_cache(maxsize=64)
def _load(path_str, mtime):
    path = Path(path_str)
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError(f'{path.name} is larger than {MAX_BYTES // (1024 * 1024)} MB')
    mime = _sniff(data)
    if mime is None:
        raise ValueError(f'{path.name}: unsupported image type (use PNG, JPEG, WebP or SVG)')
    width = height = None
    mean_rgb = bright_rgb = None
    if mime == 'image/svg+xml':
        if SVG_FORBIDDEN.search(data):
            raise ValueError(f'{path.name}: SVG with scripts, event handlers or external references is not allowed')
    else:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            width, height = im.size
            rgb = im.convert('RGBA')
            bg = Image.new('RGBA', rgb.size, (0, 0, 0, 0))
            rgb = Image.alpha_composite(bg, rgb).convert('RGB')
            rgb.thumbnail((256, 256))
            mean_rgb = tuple(round(c) for c in ImageStat.Stat(rgb).mean)
            # A bright-region sample (90th percentile by luminance): text contrast is
            # limited by the light details under it, not by the image's average colour.
            raw = rgb.tobytes()
            pixels = sorted((tuple(raw[k:k + 3]) for k in range(0, len(raw), 3)), key=lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
            bright_rgb = pixels[int(len(pixels) * 0.9)]
    uri = f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')
    return {'path': str(path), 'mime': mime, 'bytes': len(data), 'uri': uri,
            'width': width, 'height': height, 'mean_rgb': mean_rgb, 'bright_rgb': bright_rgb}


def load_image(src, base_dir):
    path = resolve(src, base_dir)
    return _load(str(path), path.stat().st_mtime)


def deck_assets(deck, base_dir):
    """Return {'logo': info|None, 'slides': [info|None, ...]} for every referenced image."""
    total = 0
    logo = None
    if deck['brand'].get('logo'):
        logo = load_image(deck['brand']['logo'], base_dir)
        total += logo['bytes']
    slides = []
    for s in deck['slides']:
        img = s.get('image')
        info = load_image(img['src'], base_dir) if img else None
        if info:
            total += info['bytes']
        slides.append(info)
    font = str(resolve(deck['brand']['font_file'], base_dir)) if deck['brand'].get('font_file') else None
    if total > MAX_TOTAL_BYTES:
        raise ValueError(f'Images total {total // (1024 * 1024)} MB; limit is {MAX_TOTAL_BYTES // (1024 * 1024)} MB')
    return {'logo': logo, 'slides': slides, 'font': font}
