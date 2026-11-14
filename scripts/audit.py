#!/usr/bin/env python3
"""Technical preflight; does not replace visual/editorial approval."""
import argparse
import json
import re
from pathlib import Path
from PIL import Image
from render import load_deck


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
        text=' '.join(str(slide.get(k,'')) for k in ('headline','body','cta'))
        text+=' '+' '.join(slide.get('bullets',[]))
        words=len(text.split())
        if words>40:warnings.append(f'Slide {i}: {words} words; editorial target is <=40')
        if len(slide['headline'])>78:warnings.append(f'Slide {i}: long headline; inspect mobile readability')
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
