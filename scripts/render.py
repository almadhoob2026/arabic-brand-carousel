#!/usr/bin/env python3
"""Deterministic, offline Arabic carousel renderer using Chromium."""
import argparse
import base64
import html
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw
from playwright.sync_api import sync_playwright
from taste import taste_profile, css_tokens
from assets import (check_reference, deck_assets, IMAGE_LAYOUTS, IMAGE_FITS, IMAGE_RIGHTS)
from layouts import validate_fields, infer_kind, content_html, LAYOUT_CSS
from formats import FORMATS, parse_formats
from publish import validate_publish, validate_slide_alt, write_pack
from brand import merge_profile
from functools import lru_cache

W, H = 1080, 1350
PALETTE = {
    'background': '#111418', 'foreground': '#F7F5F1',
    'accent': '#F3C969', 'muted': '#B5BDC8', 'surface': '#232A33',
}
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')
ROOT = Path(__file__).resolve().parents[1]
BUNDLED_FONT = ROOT / 'fonts' / 'Cairo-Variable.ttf'  # SIL OFL 1.1, see fonts/OFL.txt
SAFE_MARGIN = 64        # px; text glyph boxes must stay inside this margin
MIN_FONT_PX = 22        # smallest acceptable rendered text size
MAX_HEADLINE_LINES = 4


def load_deck(path):
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if isinstance(obj, dict):
        obj = merge_profile(obj, path)
    if not isinstance(obj, dict) or not isinstance(obj.get('brand'), dict):
        raise ValueError('Deck must contain a brand object')
    slides = obj.get('slides')
    if not isinstance(slides, list) or not 2 <= len(slides) <= 10:
        raise ValueError('Deck must contain 2–10 slides')
    if not str(obj['brand'].get('name', '')).strip():
        raise ValueError('brand.name is required')
    for k in PALETTE:
        c = obj['brand'].get(k, PALETTE[k])
        if not isinstance(c, str) or not HEX.fullmatch(c):
            raise ValueError(f'Invalid brand color {k}: expected #RRGGBB')
    for i, s in enumerate(slides, 1):
        if not isinstance(s, dict) or not isinstance(s.get('headline'), str) or not s['headline'].strip():
            raise ValueError(f'Slide {i} needs a headline')
        if len(s['headline']) > 250:
            raise ValueError(f'Slide {i} headline is too long')
        for k in ('eyebrow','body','source','cta'):
            if len(str(s.get(k, ''))) > 1200:
                raise ValueError(f'Slide {i} {k} is too long')
        if s.get('bullets') is not None and (not isinstance(s['bullets'], list) or len(s['bullets']) > 5 or not all(isinstance(x,str) and len(x) <= 180 for x in s['bullets'])):
            raise ValueError(f'Slide {i} has invalid bullets')
        if s.get('image') is not None:
            validate_image(s['image'], f'Slide {i} image')
        validate_fields(s, i)
        validate_slide_alt(s, i)
    if obj.get('publish') is not None:
        validate_publish(obj['publish'])
    if obj.get('formats') is not None:
        parse_formats(obj['formats'])
    if obj['brand'].get('logo') is not None:
        check_reference(obj['brand']['logo'], 'brand.logo')
    if obj['brand'].get('font_file') is not None:
        check_reference(obj['brand']['font_file'], 'brand.font_file')
    taste_profile(obj)
    return obj


def validate_image(img, field):
    if not isinstance(img, dict):
        raise ValueError(f'{field} must be an object with src and alt')
    unknown = set(img) - {'src', 'alt', 'layout', 'fit', 'overlay', 'credit', 'rights', 'position'}
    if unknown:
        raise ValueError(f'{field} has unknown keys: {", ".join(sorted(unknown))}')
    check_reference(img.get('src'), f'{field}.src')
    if not isinstance(img.get('alt'), str) or not img['alt'].strip() or len(img['alt']) > 300:
        raise ValueError(f'{field}.alt is required (describe the image, max 300 chars)')
    if img.get('layout', 'background') not in IMAGE_LAYOUTS:
        raise ValueError(f'{field}.layout must be one of {", ".join(IMAGE_LAYOUTS)}')
    if img.get('fit', 'cover') not in IMAGE_FITS:
        raise ValueError(f'{field}.fit must be one of {", ".join(IMAGE_FITS)}')
    ov = img.get('overlay', 0.62)
    if type(ov) not in (int, float) or not 0 <= ov <= 0.95:
        raise ValueError(f'{field}.overlay must be a number between 0 and 0.95')
    if img.get('rights') is not None and img['rights'] not in IMAGE_RIGHTS:
        raise ValueError(f'{field}.rights must be one of {", ".join(IMAGE_RIGHTS)}')
    if len(str(img.get('credit', ''))) > 120:
        raise ValueError(f'{field}.credit is too long (max 120 chars)')
    if img.get('position') is not None and not re.fullmatch(r'(?:left|center|right|top|bottom|\d{1,3}%)(?: (?:left|center|right|top|bottom|\d{1,3}%))?', str(img['position'])):
        raise ValueError(f'{field}.position must look like "center", "top" or "50% 30%"')


def t(v):
    return html.escape(str(v or ''), quote=True)


def make_slide(slide, idx, n, brand, image=None, logo=None):
    kind = infer_kind(slide, idx, n)
    deco = slide.get('decorative', 'none')
    if deco not in ('orb','dots','rings'):
        deco = 'none'
    source = f'<div class="source">{t(slide["source"])}</div>' if slide.get('source') else ''
    cue = '' if idx == n else '<span class="swipe" aria-hidden="true">← اسحب</span>'
    category = t(brand.get('category','محتوى عربي'))
    brand_mark = t(brand.get('handle') or brand['name'])
    klass = kind
    media = ''
    style = ''
    if image:
        spec = slide['image']
        layout = spec.get('layout', 'background')
        klass += f' has-image img-{layout}'
        deco = 'none'  # never stack ornaments on a photo
        credit = f'<figcaption class="credit"><bdi>{t(spec["credit"])}</bdi></figcaption>' if spec.get('credit') else ''
        style = (f' style="--img-fit:{spec.get("fit", "cover")};--img-pos:{spec.get("position", "center")};'
                 f'--overlay:{float(spec.get("overlay", 0.62)):.2f}"')
        media = f'<figure class="media"><img src="{image["uri"]}" alt="{t(spec["alt"])}">{credit}</figure>'
    logo_html = f'<img class="logo" src="{logo["uri"]}" alt="{t(brand["name"])}">' if logo else ''
    return f'''<section class="slide {klass}" data-slide="{idx}" data-kind="{kind}" lang="ar" dir="rtl"{style}>
      <div class="decoration {deco}" aria-hidden="true"></div>{media}
      <header class="topbar"><span class="category">{category}</span><span class="counter" dir="ltr">{idx} / {n}</span></header>
      <main class="content">{content_html(slide, kind)}</main>
      {source}
      <footer class="footer"><span class="brandmark">{logo_html}<bdi>{brand_mark}</bdi></span>{cue}</footer>
    </section>'''


@lru_cache(maxsize=4)
def _font_data_uri(path_str, mtime):
    data = Path(path_str).read_bytes()
    fmt = {b'\x00\x01\x00\x00': ('font/ttf', 'truetype'), b'true': ('font/ttf', 'truetype'),
           b'OTTO': ('font/otf', 'opentype'), b'wOFF': ('font/woff', 'woff'), b'wOF2': ('font/woff2', 'woff2')}.get(data[:4])
    if not fmt:
        raise ValueError(f'{Path(path_str).name}: not a TTF/OTF/WOFF/WOFF2 font')
    if len(data) > 5 * 1024 * 1024:
        raise ValueError(f'{Path(path_str).name}: font larger than 5 MB')
    return f'data:{fmt[0]};base64,' + base64.b64encode(data).decode('ascii'), fmt[1]


def font_faces(font_stack, font_path=None):
    """@font-face rules: the brand's own font file (if any) and the bundled Cairo."""
    rules = []
    if font_path:
        p = Path(font_path)
        uri, fmt = _font_data_uri(str(p), p.stat().st_mtime)
        rules.append(f"@font-face{{font-family:'BrandFont';src:url({uri}) format('{fmt}');font-weight:100 1000;font-display:block}}")
    if 'cairo' in font_stack.lower() and BUNDLED_FONT.is_file():
        uri, fmt = _font_data_uri(str(BUNDLED_FONT), BUNDLED_FONT.stat().st_mtime)
        rules.append(f"@font-face{{font-family:'Cairo';src:url({uri}) format('{fmt}');font-weight:200 1000;font-display:block}}")
    return '\n'.join(rules)


def make_html(deck, assets=None, fmt='portrait'):
    """assets: output of assets.deck_assets(); omitted → images are not embedded."""
    b = deck['brand']
    colors = {k:b.get(k, v) for k,v in PALETTE.items()}
    # Font family is a list of local CSS font family names only; disallow CSS injection.
    font = b.get('font_family', 'Cairo, Noto Sans Arabic, DejaVu Sans, sans-serif')
    if not isinstance(font, str) or len(font)>160 or not re.fullmatch(r'[\w\s,\-"\']+', font, re.UNICODE):
        raise ValueError('Invalid local font_family')
    font_path = (assets or {}).get('font')
    if font_path:
        font = "'BrandFont', " + font
    faces = font_faces(font, font_path)
    taste = taste_profile(deck)
    # css_tokens() keys already start with '--'; palette keys do not. Normalize to one prefix.
    spec = FORMATS[fmt]
    tokens = css_tokens(taste)
    tokens['--headline-scale'] = f"{float(tokens['--headline-scale']) * spec['scale']:.3f}"
    stylevars = ';'.join(f'--{k.lstrip("-")}:{v}' for k,v in {**colors, **tokens}.items())
    assets = {'logo': None, 'slides': [None] * len(deck['slides']), **(assets or {})}
    slides = '\n'.join(make_slide(s, i, len(deck['slides']), b, assets['slides'][i-1], assets['logo'])
                       for i,s in enumerate(deck['slides'],1))
    return '''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arabic Brand Carousel</title><style>
    '''+faces+'''
    :root{'''+stylevars+';--arabic-font:'+font+'''}
    html{scrollbar-width:none}::-webkit-scrollbar{display:none}
    *{box-sizing:border-box}html,body{margin:0;padding:0;background:#555;color:var(--foreground);font-family:var(--arabic-font)}
    .slide{width:1080px;height:1350px;position:relative;overflow:hidden;background:var(--background);color:var(--foreground);margin:0 0 20px;isolation:isolate}
    .topbar{position:absolute;z-index:3;top:74px;left:82px;right:82px;display:flex;align-items:center;justify-content:space-between;gap:24px}
    .category{background:var(--surface);padding:16px 28px;border-radius:100px;font-size:27px;line-height:1.35;font-weight:700;max-width:640px;overflow-wrap:anywhere}
    .counter{font-family:Arial,sans-serif;font-size:26px;color:var(--muted);letter-spacing:2px;direction:ltr;flex-shrink:0}
    .content{position:absolute;z-index:2;top:245px;left:85px;right:85px;bottom:185px;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;text-align:right}
    .eyebrow{font-size:35px;font-weight:700;color:var(--accent);margin-bottom:33px;line-height:1.4}
    .headline{font-size:calc(100px * var(--headline-scale));font-weight:900;line-height:1.27;letter-spacing:-1.5px;margin:0;overflow-wrap:break-word;max-width:100%;text-wrap:balance}
    .slide:nth-child(3n) .content{right:calc(85px + var(--layout-shift))}
    .eyebrow:not(:empty){border-right:var(--accent-rule) solid var(--accent);padding-right:18px}
    .cover .headline{font-size:calc(109px * var(--headline-scale))}.cta .headline{font-size:calc(102px * var(--headline-scale))}
    .body{font-size:calc(45px * var(--body-scale));line-height:var(--body-leading);color:var(--muted);font-weight:600;margin:44px 0 0;max-width:890px;overflow-wrap:break-word}
    .cta-line{font-size:39px;font-weight:800;color:var(--accent);margin:46px 0 0}
    .steps{list-style:none;padding:0;margin:35px 0 0;width:100%;display:flex;flex-direction:column;gap:18px}
    .steps li{display:flex;align-items:center;gap:20px;background:var(--surface);border-radius:22px;padding:22px 26px;font-size:36px;font-weight:700;line-height:1.45}
    .step-num{color:var(--accent);font-size:30px;font-family:Arial,sans-serif;flex-shrink:0}
    .source{position:absolute;bottom:165px;right:85px;left:85px;font-size:24px;color:var(--muted);z-index:2;white-space:normal}
    .footer{position:absolute;z-index:3;bottom:72px;left:85px;right:85px;display:flex;justify-content:space-between;align-items:center;gap:20px;font-size:29px}
    .brandmark{font-weight:800;max-width:630px;overflow-wrap:anywhere;display:flex;align-items:center;gap:16px}
    .logo{height:56px;max-width:220px;object-fit:contain;display:block}
    .media{position:absolute;z-index:1;margin:0;overflow:hidden;background:var(--surface)}
    .media img{width:100%;height:100%;display:block;object-fit:var(--img-fit,cover);object-position:var(--img-pos,center)}
    .credit{position:absolute;bottom:14px;left:16px;font-size:19px;line-height:1.3;color:#fff;background:rgba(0,0,0,.55);padding:6px 12px;border-radius:8px;max-width:80%}
    .img-background .media{inset:0}
    .img-background .media::after{content:'';position:absolute;inset:0;background:var(--background);opacity:var(--overlay)}
    .img-background .credit{bottom:auto;top:150px;left:82px}
    .img-background .content{text-shadow:0 2px 18px rgba(0,0,0,.45)}
    .img-background .body{color:var(--foreground)}
    .img-top .media{top:190px;left:85px;right:85px;height:430px;border-radius:28px}
    .img-top .content{top:660px;justify-content:flex-start}
    .img-top .headline{font-size:calc(84px * var(--headline-scale))}
    .img-side .media{top:200px;bottom:170px;left:85px;width:400px;border-radius:28px}
    .img-side .content,.img-side:nth-child(3n) .content{left:525px;right:85px}
    .img-side .headline{font-size:calc(76px * var(--headline-scale))}
    .img-side .source{left:525px}
    .swipe{color:var(--accent);font-weight:800}
    .decoration{position:absolute;z-index:0;pointer-events:none;opacity:var(--decoration-opacity)}
    .orb{width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,var(--accent) 0,transparent 70%);top:300px;left:-240px;filter:blur(70px)}
    .rings{width:600px;height:600px;border:8px solid var(--accent);border-radius:50%;left:-270px;top:410px;box-shadow:0 0 0 60px var(--background),0 0 0 70px var(--accent);opacity:.12}
    .dots{left:28px;top:400px;width:300px;height:480px;background-image:radial-gradient(var(--accent) 4px,transparent 5px);background-size:34px 34px;opacity:.18}
    '''+LAYOUT_CSS+spec['css']+'''
    @page{size:'''+f"{spec['size'][0]}px {spec['size'][1]}px"+''';margin:0}
    @media print{.slide{margin:0;break-after:page}.slide:last-child{break-after:auto}body{background:white}}
    </style></head><body class="fmt-'''+fmt+'''">'''+slides+'''</body></html>'''


def copy_assets(deck, assets, dest):
    """Copy referenced images to dest/assets and return a deck whose paths point there."""
    portable = json.loads(json.dumps(deck))
    refs = [('logo', assets['logo'])] + [(i, a) for i, a in enumerate(assets['slides'])]
    if not any(a for _, a in refs) and not assets.get('font'):
        return portable
    folder = dest / 'assets'
    folder.mkdir(exist_ok=True)
    if assets.get('font'):
        src = Path(assets['font'])
        shutil.copyfile(src, folder / f'font-{src.name}')
        portable['brand']['font_file'] = f'assets/font-{src.name}'
    for key, info in refs:
        if not info:
            continue
        src = Path(info['path'])
        name = f'logo-{src.name}' if key == 'logo' else f'slide-{key+1:02d}-{src.name}'
        shutil.copyfile(src, folder / name)
        if key == 'logo':
            portable['brand']['logo'] = f'assets/{name}'
        else:
            portable['slides'][key]['image']['src'] = f'assets/{name}'
    return portable


GEOMETRY_JS = '''(el, cfg) => {
  const content = el.querySelector('.content');
  const fits = [...el.querySelectorAll('[data-fit]')];
  const base = fits.map(f => parseFloat(getComputedStyle(f).fontSize));
  const overflow = () => content.scrollHeight > content.clientHeight + 2 || content.scrollWidth > content.clientWidth + 2;
  let ratio = 1;
  while (overflow() && ratio > 0.64) { ratio -= 0.03; fits.forEach((f, i) => f.style.fontSize = (base[i] * ratio) + 'px'); }
  const box = el.getBoundingClientRect(), W = box.width, H = box.height, S = cfg.side, T = cfg.top, B = cfg.bottom;
  const groups = {}; let minFont = 1e9, minFontText = '';
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), range = document.createRange();
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim()) continue;
    const parent = n.parentElement, holder = parent.closest('.credit,.topbar,.content,.source,.footer');
    const g = holder ? holder.classList[0] : 'other';
    range.selectNodeContents(n);
    for (const r of range.getClientRects()) {
      if (r.width < 1 || r.height < 1) continue;
      (groups[g] = groups[g] || []).push({x: r.left - box.left, y: r.top - box.top, w: r.width, h: r.height});
    }
    const fs = parseFloat(getComputedStyle(parent).fontSize);
    if (fs < minFont) { minFont = fs; minFontText = n.textContent.trim().slice(0, 40); }
  }
  const hit = (a, b) => a.x < b.x + b.w - 2 && b.x < a.x + a.w - 2 && a.y < b.y + b.h - 2 && b.y < a.y + a.h - 2;
  const issues = [];
  for (const [g, rects] of Object.entries(groups)) {
    if (g === 'credit') continue;
    const bad = rects.find(r => r.x < S || r.y < T || r.x + r.w > W - S || r.y + r.h > H - B);
    if (bad) issues.push({code: 'outside-safe-area', group: g, at: [Math.round(bad.x), Math.round(bad.y)]});
  }
  const names = ['topbar', 'content', 'source', 'footer'];
  for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
    const A = groups[names[i]] || [], B = groups[names[j]] || [];
    if (A.some(a => B.some(b => hit(a, b)))) issues.push({code: 'text-overlap', group: names[i] + '/' + names[j]});
  }
  const media = el.querySelector('.media');
  if (media && !el.classList.contains('img-background')) {
    const m = media.getBoundingClientRect(), mr = {x: m.left - box.left, y: m.top - box.top, w: m.width, h: m.height};
    for (const g of ['content', 'source', 'topbar', 'footer'])
      if ((groups[g] || []).some(r => hit(r, mr))) issues.push({code: 'text-over-image', group: g});
  }
  if (overflow()) issues.push({code: 'content-overflow', group: 'content'});
  const h = el.querySelector('.headline'), hs = getComputedStyle(h);
  return {kind: el.dataset.kind, shrink_percent: Math.round((1 - ratio) * 100),
          headline_px: Math.round(parseFloat(hs.fontSize)),
          headline_lines: Math.round(h.getBoundingClientRect().height / parseFloat(hs.lineHeight)),
          min_font_px: Math.round(minFont * 10) / 10, min_font_text: minFontText, issues};
}'''


def browser_executable():
    env = os.environ.get('CHROME_PATH')
    if env:
        if not Path(env).exists():
            raise FileNotFoundError(f'CHROME_PATH does not exist: {env}')
        return env
    found = shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
    if found:
        return found
    for candidate in (
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    ):
        if Path(candidate).exists():
            return candidate
    return None


def contact_sheet(pngs, size, out):
    """Scaled overview of all slides; native files remain untouched."""
    thumb_w = 270
    thumb_h = round(thumb_w * size[1] / size[0])
    cols, gap = 3, 24
    rows = (len(pngs) + cols - 1) // cols
    montage = Image.new('RGB', (cols * thumb_w + (cols + 1) * gap, rows * thumb_h + (rows + 1) * gap), '#e9ecef')
    for i, f in enumerate(pngs):
        with Image.open(f) as im:
            im = ImageOps.fit(im.convert('RGB'), (thumb_w, thumb_h))
            montage.paste(im, (gap + (i % cols) * (thumb_w + gap), gap + (i // cols) * (thumb_h + gap)))
    montage.save(out)


GENERATED = ('carousel.html', 'deck.json', 'geometry.json', 'audit.json', 'contact-sheet.png', 'carousel.pdf',
             'carousel.zip', 'caption.txt', 'alt-text.txt', 'publish.json')
SLIDE_PNG = re.compile(r'^slide-\d{2}\.png$')


def clean_generated(dest):
    """Remove files this renderer wrote in an earlier run, so no stale slide survives.

    Only exact generated names are touched (slide-NN.png and the files above);
    anything else the user keeps in the folder stays."""
    if not dest.is_dir():
        return
    for f in dest.iterdir():
        if f.is_file() and (f.name in GENERATED or SLIDE_PNG.match(f.name)):
            f.unlink()


def render_format(browser, deck, assets, dest, fmt, pdf):
    spec = FORMATS[fmt]
    w, h = spec['size']
    clean_generated(dest)
    dest.mkdir(parents=True, exist_ok=True)
    markup = make_html(deck, assets, fmt)
    (dest/'carousel.html').write_text(markup, encoding='utf-8')
    portable = copy_assets(deck, assets, dest)
    (dest/'deck.json').write_text(json.dumps(portable, ensure_ascii=False, indent=2), encoding='utf-8')
    page = browser.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
    page.set_content(markup, wait_until='load')
    page.evaluate('document.fonts.ready')
    pngs, geometry = [], []
    for i in range(len(deck['slides'])):
        slide = page.locator('.slide').nth(i)
        # Shrink display text (headline, metric, quote) only if the DOM overflows (max 36%),
        # then measure real glyph boxes for safe-area, overlap and size checks.
        geo = slide.evaluate(GEOMETRY_JS, spec['safe'])
        geo['slide'] = i + 1
        geometry.append(geo)
        for issue in geo['issues']:
            print(f"WARNING: {fmt} slide {i+1}: {issue['code']} ({issue['group']})")
        out = dest/f'slide-{i+1:02d}.png'
        slide.screenshot(path=str(out), animations='disabled')
        pngs.append(out)
    if pdf:  # vector PDF with real, searchable text; same DOM as the PNGs (after fitting)
        page.pdf(path=str(dest/'carousel.pdf'), width=f'{w}px', height=f'{h}px',
                 print_background=True, prefer_css_page_size=True,
                 margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
    page.close()
    (dest/'geometry.json').write_text(json.dumps({
        'format': fmt, 'size': [w, h], 'safe_area': spec['safe'], 'min_font_px': MIN_FONT_PX,
        'max_headline_lines': MAX_HEADLINE_LINES, 'slides': geometry}, ensure_ascii=False, indent=2), encoding='utf-8')
    contact_sheet(pngs, (w, h), dest/'contact-sheet.png')
    write_pack(deck, dest)
    extras = [dest/n for n in ('carousel.html', 'deck.json', 'contact-sheet.png', 'carousel.pdf',
                               'caption.txt', 'alt-text.txt', 'publish.json') if (dest/n).exists()]
    with zipfile.ZipFile(dest/'carousel.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for f in pngs + extras:
            archive.write(f, arcname=f.name)
        for f in sorted((dest/'assets').glob('*')) if (dest/'assets').is_dir() else []:
            archive.write(f, arcname=f'assets/{f.name}')
    print(f'Rendered {len(pngs)} {fmt} slides ({w}x{h}) to {dest}')
    return dest


def render(deck_path, outdir, formats=None, pdf=False):
    """Render each format: portrait into outdir, others into outdir/<format>/."""
    root = Path(outdir)
    src = Path(deck_path).resolve()
    targets = [root] + [root/f['folder'] for f in FORMATS.values() if f['folder']]
    if any(src.parent == t.resolve() and src.name in GENERATED for t in targets):
        raise ValueError(f'{deck_path} would be overwritten by the output; keep the deck outside --out')
    deck = load_deck(deck_path)
    fmts = parse_formats(formats if formats is not None else deck.get('formats'))
    assets = deck_assets(deck, Path(deck_path).parent)
    outputs = []
    with sync_playwright() as p:
        args = {'headless': True}
        executable = browser_executable()
        if executable:
            args['executable_path'] = executable
        browser = p.chromium.launch(**args)
        for fmt in fmts:
            folder = FORMATS[fmt]['folder']
            outputs.append(render_format(browser, deck, assets, root/folder if folder else root, fmt, pdf))
        browser.close()
    # Manifest of what this run produced; audit.py checks exactly these folders.
    (root/'render.json').write_text(json.dumps({
        'formats': {f: FORMATS[f]['folder'] or '.' for f in fmts}, 'slides': len(deck['slides']), 'pdf': pdf},
        ensure_ascii=False, indent=2), encoding='utf-8')
    stale = [FORMATS[f]['folder'] for f in FORMATS if FORMATS[f]['folder'] and f not in fmts
             and (root/FORMATS[f]['folder']/'geometry.json').exists()]
    for folder in stale:
        print(f'NOTE: {root/folder} is from an earlier render and was not updated; it is not audited.')
    return outputs


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('deck',help='UTF-8 deck JSON')
    ap.add_argument('--out',default='output/carousel')
    ap.add_argument('--formats',help='comma list: portrait,square,story (default: deck "formats" or portrait)')
    ap.add_argument('--pdf',action='store_true',help='also write carousel.pdf (vector text; LinkedIn document posts)')
    args=ap.parse_args()
    render(args.deck,args.out,args.formats,args.pdf)
