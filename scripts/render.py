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
    taste_profile(obj)
    return obj


def t(v):
    return html.escape(str(v or ''), quote=True)


def make_slide(slide, idx, n, brand):
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
    return f'''<section class="slide {klass}" data-slide="{idx}" lang="ar" dir="rtl">
      <div class="decoration {deco}" aria-hidden="true"></div>
      <header class="topbar"><span class="category">{category}</span><span class="counter" dir="ltr">{idx} / {n}</span></header>
      <main class="content"><div class="eyebrow">{eyebrow}</div><h1 class="headline">{title}</h1>{body}{bullets_html}{cta}</main>
      {source}
      <footer class="footer"><span class="brandmark"><bdi>{brand_mark}</bdi></span>{cue}</footer>
    </section>'''


def make_html(deck):
    b = deck['brand']
    colors = {k:b.get(k, v) for k,v in PALETTE.items()}
    # Font family is a list of local CSS font family names only; disallow CSS injection.
    font = b.get('font_family', 'Cairo, Noto Sans Arabic, DejaVu Sans, sans-serif')
    if not isinstance(font, str) or len(font)>160 or not re.fullmatch(r'[\w\s,\-"\']+', font, re.UNICODE):
        raise ValueError('Invalid local font_family')
    taste = taste_profile(deck)
    # css_tokens() keys already start with '--'; palette keys do not. Normalize to one prefix.
    stylevars = ';'.join(f'--{k.lstrip("-")}:{v}' for k,v in {**colors, **css_tokens(taste)}.items())
    slides = '\n'.join(make_slide(s, i, len(deck['slides']), b) for i,s in enumerate(deck['slides'],1))
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
    .brandmark{font-weight:800;max-width:630px;overflow-wrap:anywhere}
    .swipe{color:var(--accent);font-weight:800}
    .decoration{position:absolute;z-index:0;pointer-events:none;opacity:var(--decoration-opacity)}
    .orb{width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,var(--accent) 0,transparent 70%);top:300px;left:-240px;filter:blur(70px)}
    .rings{width:600px;height:600px;border:8px solid var(--accent);border-radius:50%;left:-270px;top:410px;box-shadow:0 0 0 60px var(--background),0 0 0 70px var(--accent);opacity:.12}
    .dots{left:28px;top:400px;width:300px;height:480px;background-image:radial-gradient(var(--accent) 4px,transparent 5px);background-size:34px 34px;opacity:.18}
    @media print{.slide{page-break-after:always;margin:0}body{background:white}}
    </style></head><body>'''+slides+'''</body></html>'''


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
    dest=Path(outdir)
    dest.mkdir(parents=True,exist_ok=True)
    markup=make_html(deck)
    (dest/'carousel.html').write_text(markup,encoding='utf-8')
    (dest/'deck.json').write_text(json.dumps(deck,ensure_ascii=False,indent=2),encoding='utf-8')
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
    print(f'Rendered {len(pngs)} slides to {dest}')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('deck',help='UTF-8 deck JSON')
    ap.add_argument('--out',default='output/carousel')
    args=ap.parse_args()
    render(args.deck,args.out)
