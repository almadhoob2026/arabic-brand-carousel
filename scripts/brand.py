#!/usr/bin/env python3
"""Reusable brand profiles and logo-based palette extraction.

A profile is a JSON file shared by many decks:

    {"brand": {...same keys as deck.brand...}, "design": {...}, "hashtags": ["..."]}

A deck points at it with "brand_profile": "brands/acme.json". Values written in the
deck override the profile. Paths inside the profile (logo, font_file) are relative to
the profile file.

CLI:
    python scripts/brand.py init --logo assets/logo.png --name "اسم العلامة" \
        --handle @brand --out brands/brand.json [--theme dark|light]
"""
import argparse
import colorsys
import json
import os
import re
from pathlib import Path

PROFILE_KEYS = {'brand', 'design', 'hashtags'}
PATH_KEYS = ('logo', 'font_file')
DEFAULT_ACCENT = (243, 201, 105)


# ------------------------------------------------------------------ profiles

def merge_profile(deck, deck_path):
    """Return a new deck with its brand_profile merged in (deck values win)."""
    ref = deck.get('brand_profile')
    if ref is None:
        return deck
    from assets import check_reference, resolve
    check_reference(ref, 'brand_profile')
    path = resolve(ref, Path(deck_path).parent)
    profile = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(profile, dict) or not isinstance(profile.get('brand', {}), dict):
        raise ValueError(f'{path.name}: profile must be an object with a "brand" object')
    unknown = set(profile) - PROFILE_KEYS
    if unknown:
        raise ValueError(f'{path.name}: unknown keys {", ".join(sorted(unknown))}')
    brand = dict(profile.get('brand', {}))
    for key in PATH_KEYS:  # make profile-relative paths absolute
        if brand.get(key):
            check_reference(brand[key], f'profile brand.{key}')
            brand[key] = str((path.parent / brand[key]).resolve())
    merged = {k: v for k, v in deck.items() if k != 'brand_profile'}
    merged['brand'] = {**brand, **(deck.get('brand') or {})}
    if profile.get('design') or deck.get('design'):
        merged['design'] = {**(profile.get('design') or {}), **(deck.get('design') or {})}
    if profile.get('hashtags'):
        pub = dict(deck.get('publish') or {})
        pub.setdefault('hashtags', profile['hashtags'])
        merged['publish'] = pub
    return merged


# ------------------------------------------------------------------ colour

def hex_of(rgb):
    return '#' + ''.join(f'{round(c):02X}' for c in rgb)


def rgb_of(hexcolor):
    return tuple(int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))


def luminance(rgb):
    ch = [c / 255 for c in rgb]
    ch = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def hls(h, l, s):
    return tuple(c * 255 for c in colorsys.hls_to_rgb(h, l, s))


def logo_colours(path):
    """[(rgb, weight)] from a raster logo (quantized) or an SVG (hex fills/strokes)."""
    data = Path(path).read_bytes()
    if data[:1024].lstrip().lower().startswith((b'<svg', b'<?xml')):
        found = re.findall(rb'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', data)
        counts = {}
        for h in found:
            h = h.decode()
            h = ''.join(c * 2 for c in h) if len(h) == 3 else h
            rgb = rgb_of('#' + h)
            counts[rgb] = counts.get(rgb, 0) + 1
        return list(counts.items())
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert('RGBA')
        im.thumbnail((200, 200))
        raw = im.tobytes()
    opaque = [tuple(raw[k:k + 3]) for k in range(0, len(raw), 4) if raw[k + 3] >= 128]
    if not opaque:
        return []
    strip = Image.new('RGB', (len(opaque), 1))
    strip.putdata(opaque)
    pal = strip.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    palette = pal.getpalette()[:24]
    return [(tuple(palette[i * 3:i * 3 + 3]), n) for n, i in (pal.getcolors() or [])]


def pick_accent(colours):
    best, score = None, -1
    for rgb, weight in colours:
        h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
        if s < 0.25 or not 0.2 < l < 0.85:
            continue  # greys, near-black, near-white are not accents
        sc = s * (weight ** 0.5)
        if sc > score:
            best, score = rgb, sc
    return best or DEFAULT_ACCENT


def _push(rgb, against, target, toward_light):
    """Move rgb's lightness until contrast(rgb, against) >= target."""
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    step = 0.02 if toward_light else -0.02
    while contrast(hls(h, l, s), against) < target and 0 <= l + step <= 1:
        l += step
    return hls(h, l, s)


def build_palette(accent, theme='dark'):
    h, _, s = colorsys.rgb_to_hls(*(c / 255 for c in accent))
    tint = min(s, 0.35)
    if theme == 'light':
        bg, fg = hls(h, 0.97, tint * 0.5), hls(h, 0.11, tint * 0.4)
        muted, surface = hls(h, 0.36, tint * 0.3), hls(h, 0.92, tint * 0.5)
        light_text = False
    else:
        bg, fg = hls(h, 0.08, tint * 0.6), hls(h, 0.96, tint * 0.3)
        muted, surface = hls(h, 0.76, tint * 0.25), hls(h, 0.15, tint * 0.5)
        light_text = True
    fg = _push(fg, bg, 7.0, light_text)
    muted = _push(muted, bg, 4.5, light_text)
    acc = _push(accent, bg, 3.0, light_text)
    palette = {'background': hex_of(bg), 'foreground': hex_of(fg), 'accent': hex_of(acc),
               'muted': hex_of(muted), 'surface': hex_of(surface)}
    report = {'foreground/background': round(contrast(fg, bg), 2),
              'muted/background': round(contrast(muted, bg), 2),
              'accent/background': round(contrast(acc, bg), 2),
              'accent_from_logo': hex_of(accent), 'accent_adjusted': hex_of(acc) != hex_of(accent)}
    return palette, report


def init_profile(logo, name, out, handle=None, theme='dark', category=None):
    out = Path(out)
    colours = logo_colours(logo) if logo else []
    accent = pick_accent(colours)
    palette, report = build_palette(accent, theme)
    brand = {'name': name, **({'handle': handle} if handle else {}),
             **({'category': category} if category else {}), **palette,
             'font_family': 'Cairo, Noto Sans Arabic, DejaVu Sans, sans-serif'}
    if logo:
        # Relative to the profile file so the profile works on any machine.
        brand['logo'] = os.path.relpath(Path(logo).resolve(), out.resolve().parent).replace(os.sep, '/')
    profile = {'brand': brand, 'design': {'direction': 'editorial'}, 'hashtags': []}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return profile, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init', help='create a brand profile from a logo')
    p.add_argument('--logo')
    p.add_argument('--name', required=True)
    p.add_argument('--handle')
    p.add_argument('--category')
    p.add_argument('--theme', choices=('dark', 'light'), default='dark')
    p.add_argument('--out', required=True)
    args = ap.parse_args()
    profile, report = init_profile(args.logo, args.name, args.out, args.handle, args.theme, args.category)
    print(json.dumps({'profile': args.out, 'palette': {k: profile['brand'][k] for k in
                      ('background', 'foreground', 'accent', 'muted', 'surface')}, 'contrast': report},
                     ensure_ascii=False, indent=2))
    print('Review the palette with the user before using it; it is derived, not the official brand guide.')


if __name__ == '__main__':
    main()
