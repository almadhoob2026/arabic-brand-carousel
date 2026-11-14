#!/usr/bin/env python3
"""Technical preflight; does not replace visual/editorial approval."""
import argparse
import json
import re
from pathlib import Path
from PIL import Image
from render import load_deck
from layouts import slide_text


def audit(folder,deck_path):
    dest=Path(folder)
    deck=load_deck(deck_path)
    errors=[]
    warnings=[]
    paths=sorted(dest.glob('slide-*.png'))
    if len(paths)!=len(deck['slides']): errors.append('PNG slide count differs from deck')
    for i,slide in enumerate(deck['slides'],1):
        file=dest/f'slide-{i:02d}.png'
        if not file.exists():
            errors.append(f'Missing {file.name}')
            continue
        with Image.open(file) as im:
            if im.size!=(1080,1350):errors.append(f'{file.name}: incorrect size {im.size}')
        words=len(slide_text(slide).split())
        if words>40:warnings.append(f'Slide {i}: {words} words; editorial target is <=40')
        if len(slide['headline'])>78:warnings.append(f'Slide {i}: long headline; inspect mobile readability')
    geo_file=dest/'geometry.json'
    if geo_file.exists():
        geo=json.loads(geo_file.read_text(encoding='utf-8'))
        for g in geo['slides']:
            for issue in g['issues']:
                errors.append(f"Slide {g['slide']}: {issue['code']} ({issue['group']})")
            if g['headline_lines']>geo['max_headline_lines']:
                warnings.append(f"Slide {g['slide']}: headline wraps to {g['headline_lines']} lines; rewrite shorter")
            if g['min_font_px']<geo['min_font_px']:
                warnings.append(f"Slide {g['slide']}: text rendered at {g['min_font_px']}px ('{g['min_font_text']}')")
            if g['shrink_percent']>15:
                warnings.append(f"Slide {g['slide']}: display text shrunk {g['shrink_percent']}% to fit; consider shorter copy")
    else:
        warnings.append('geometry.json missing: re-render with the current render.py for layout checks')
    for required in ('carousel.html','deck.json','contact-sheet.png','carousel.zip'):
        if not (dest/required).exists():errors.append('Missing '+required)
    report={'passed':not errors,'errors':errors,'warnings':warnings,'requires_manual_review':[
      'Inspect each PNG for clipped elements or overlap',
      'Proofread Arabic glyphs, punctuation and bidi text',
      'Verify claims and sources against source ledger',
      'Apply human 100-point rubric and approve only if >=90 with no blocking issue'
    ]}
    (dest/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output')
    p.add_argument('--deck',required=True)
    a=p.parse_args()
    raise SystemExit(audit(a.output,a.deck))
