#!/usr/bin/env python3
"""Deterministic, offline Arabic carousel renderer using Chromium."""
import argparse
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

W, H = 1080, 1350
PALETTE = {
    'background': '#111418', 'foreground': '#F7F5F1',
    'accent': '#F3C969', 'muted': '#B5BDC8', 'surface': '#232A33',
}
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def load_deck(path):
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
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
    if obj['brand'].get('logo') is not None:
        check_reference(obj['brand']['logo'], 'brand.logo')
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
    kind = str(slide.get('kind','statement')).lower()
    deco = slide.get('decorative', 'none')
    if deco not in ('orb','dots','rings'):
        deco = 'none'
    title = t(slide['headline'])
    body = f'<p class="body">{t(slide["body"])}</p>' if slide.get('body') else ''
    bullets = slide.get('bullets', [])
    bullets_html = '<ul class="steps">' + ''.join(f'<li><span class="step-num">{j:02}</span><span>{t(b)}</span></li>' for j,b in enumerate(bullets, 1)) + '</ul>' if bullets else ''
    cta = f'<p class="cta-line">{t(slide["cta"])}</p>' if slide.get('cta') else ''
    source = f'<div class="source">{t(slide["source"])}</div>' if slide.get('source') else ''
    cue = '' if idx == n else '<span class="swipe" aria-hidden="true">← اسحب</span>'
    eyebrow = t(slide.get('eyebrow', ''))
    category = t(brand.get('category','محتوى عربي'))
    brand_mark = t(brand.get('handle') or brand['name'])
    klass = kind if kind in ('cover','statement','steps','list','cta') else 'statement'
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
    return f'''<section class="slide {klass}" data-slide="{idx}" lang="ar" dir="rtl"{style}>
      <div class="decoration {deco}" aria-hidden="true"></div>{media}
      <header class="topbar"><span class="category">{category}</span><span class="counter" dir="ltr">{idx} / {n}</span></header>
      <main class="content"><div class="eyebrow">{eyebrow}</div><h1 class="headline">{title}</h1>{body}{bullets_html}{cta}</main>
      {source}
      <footer class="footer"><span class="brandmark">{logo_html}<bdi>{brand_mark}</bdi></span>{cue}</footer>
    </section>'''


def make_html(deck, assets=None):
    """assets: output of assets.deck_assets(); omitted → images are not embedded."""
    b = deck['brand']
    colors = {k:b.get(k, v) for k,v in PALETTE.items()}
    # Font family is a list of local CSS font family names only; disallow CSS injection.
    font = b.get('font_family', 'Cairo, Noto Sans Arabic, DejaVu Sans, sans-serif')
    if not isinstance(font, str) or len(font)>160 or not re.fullmatch(r'[\w\s,\-"\']+', font, re.UNICODE):
        raise ValueError('Invalid local font_family')
    taste = taste_profile(deck)
    # css_tokens() keys already start with '--'; palette keys do not. Normalize to one prefix.
    stylevars = ';'.join(f'--{k.lstrip("-")}:{v}' for k,v in {**colors, **css_tokens(taste)}.items())
    assets = assets or {'logo': None, 'slides': [None] * len(deck['slides'])}
    slides = '\n'.join(make_slide(s, i, len(deck['slides']), b, assets['slides'][i-1], assets['logo'])
                       for i,s in enumerate(deck['slides'],1))
    return '''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arabic Brand Carousel</title><style>
    :root{'''+stylevars+';--arabic-font:'+font+'''}
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
    .source{position:absolute;bottom:165px;right:85px;left:85px;font-size:23px;color:var(--muted);z-index:2;white-space:normal}
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
    @media print{.slide{page-break-after:always;margin:0}body{background:white}}
    </style></head><body>'''+slides+'''</body></html>'''


def copy_assets(deck, assets, dest):
    """Copy referenced images to dest/assets and return a deck whose paths point there."""
    portable = json.loads(json.dumps(deck))
    refs = [('logo', assets['logo'])] + [(i, a) for i, a in enumerate(assets['slides'])]
    if not any(a for _, a in refs):
        return portable
    folder = dest / 'assets'
    folder.mkdir(exist_ok=True)
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


def render(deck_path, outdir):
    deck=load_deck(deck_path)
    assets=deck_assets(deck, Path(deck_path).parent)
    dest=Path(outdir)
    dest.mkdir(parents=True,exist_ok=True)
    markup=make_html(deck, assets)
    (dest/'carousel.html').write_text(markup,encoding='utf-8')
    portable=copy_assets(deck, assets, dest)
    (dest/'deck.json').write_text(json.dumps(portable,ensure_ascii=False,indent=2),encoding='utf-8')
    pngs=[]
    with sync_playwright() as p:
        args={'headless':True}
        executable=browser_executable()
        if executable: args['executable_path']=executable
        browser=p.chromium.launch(**args)
        page=browser.new_page(viewport={'width':W,'height':H},device_scale_factor=1)
        page.set_content(markup,wait_until='load')
        page.evaluate('document.fonts.ready')
        for i in range(len(deck['slides'])):
            slide=page.locator('.slide').nth(i)
            # Shrink headlines only when actual DOM overflow requires it; never below 64px.
            status=slide.evaluate('''el => {
              const content=el.querySelector('.content'), headline=el.querySelector('.headline');
              let sz=parseFloat(getComputedStyle(headline).fontSize);
              const isOverflow=()=> content.scrollHeight > content.clientHeight + 2 || headline.scrollWidth > headline.clientWidth + 2;
              while(isOverflow() && sz > 64){sz -= 2;headline.style.fontSize=sz+'px'}
              return {fontSize:sz,overflow:isOverflow()};
            }''')
            if status['overflow']:
                print(f'WARNING: slide {i+1} content overflow; shorten text before publication')
            out=dest/f'slide-{i+1:02d}.png'
            slide.screenshot(path=str(out),animations='disabled')
            pngs.append(out)
        browser.close()
    # Montage with scaled images; native files remain untouched.
    thumb_w=270
    thumb_h=338
    cols=3
    rows=(len(pngs)+cols-1)//cols
    gap=24
    montage=Image.new('RGB',(cols*thumb_w+(cols+1)*gap,rows*thumb_h+(rows+1)*gap),'#e9ecef')
    for i, f in enumerate(pngs):
        with Image.open(f) as im:
            im=ImageOps.fit(im.convert('RGB'),(thumb_w,thumb_h))
            montage.paste(im,(gap+(i%cols)*(thumb_w+gap),gap+(i//cols)*(thumb_h+gap)))
    montage.save(dest/'contact-sheet.png')
    with zipfile.ZipFile(dest/'carousel.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for f in pngs+[dest/'carousel.html',dest/'deck.json',dest/'contact-sheet.png']:
            archive.write(f,arcname=f.name)
        for f in sorted((dest/'assets').glob('*')) if (dest/'assets').is_dir() else []:
            archive.write(f,arcname=f'assets/{f.name}')
    print(f'Rendered {len(pngs)} slides to {dest}')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('deck',help='UTF-8 deck JSON')
    ap.add_argument('--out',default='output/carousel')
    args=ap.parse_args()
    render(args.deck,args.out)
