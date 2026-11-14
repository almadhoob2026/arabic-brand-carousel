#!/usr/bin/env python3
"""Technical preflight; does not replace visual/editorial approval.

Audits the output folder and any format subfolders (square/, story/) found in it.
"""
import argparse
import json
import re
from pathlib import Path
from PIL import Image
from render import load_deck
from layouts import slide_text
from formats import FORMATS


def audit_folder(dest, deck):
    errors, warnings = [], []
    geo_file = dest/'geometry.json'
    geo = json.loads(geo_file.read_text(encoding='utf-8')) if geo_file.exists() else None
    fmt = (geo or {}).get('format', 'portrait')
    size = tuple((geo or {}).get('size') or FORMATS['portrait']['size'])
    paths = sorted(dest.glob('slide-*.png'))
    if len(paths) != len(deck['slides']):
        errors.append('PNG slide count differs from deck')
    for i, slide in enumerate(deck['slides'], 1):
        file = dest/f'slide-{i:02d}.png'
        if not file.exists():
            errors.append(f'Missing {file.name}')
            continue
        with Image.open(file) as im:
            if im.size != size:
                errors.append(f'{file.name}: incorrect size {im.size}, expected {size}')
        if fmt == 'portrait':  # copy checks are format independent; report them once
            words = len(slide_text(slide).split())
            if words > 40:
                warnings.append(f'Slide {i}: {words} words; editorial target is <=40')
            if len(slide['headline']) > 78:
                warnings.append(f'Slide {i}: long headline; inspect mobile readability')
    if geo:
        for g in geo['slides']:
            for issue in g['issues']:
                errors.append(f"Slide {g['slide']}: {issue['code']} ({issue['group']})")
            if g['headline_lines'] > geo['max_headline_lines']:
                warnings.append(f"Slide {g['slide']}: headline wraps to {g['headline_lines']} lines; rewrite shorter")
            if g['min_font_px'] < geo['min_font_px']:
                warnings.append(f"Slide {g['slide']}: text rendered at {g['min_font_px']}px ('{g['min_font_text']}')")
            if g['shrink_percent'] > 15:
                warnings.append(f"Slide {g['slide']}: display text shrunk {g['shrink_percent']}% to fit; consider shorter copy")
    else:
        warnings.append('geometry.json missing: re-render with the current render.py for layout checks')
    for required in ('carousel.html', 'deck.json', 'contact-sheet.png', 'carousel.zip'):
        if not (dest/required).exists():
            errors.append('Missing ' + required)
    pub = dest/'publish.json'
    if pub.exists():
        warnings += json.loads(pub.read_text(encoding='utf-8')).get('warnings', [])
    if (dest/'carousel.pdf').exists():
        pages = len(re.findall(rb'/Type\s*/Page(?![a-zA-Z])', (dest/'carousel.pdf').read_bytes()))
        if pages and pages != len(deck['slides']):
            errors.append(f'carousel.pdf has {pages} pages, expected {len(deck["slides"])}')
    return fmt, {'passed': not errors, 'format': fmt, 'size': list(size), 'errors': errors, 'warnings': warnings}


def audit(folder, deck_path):
    root = Path(folder)
    deck = load_deck(deck_path)
    folders = [root] + [root/f['folder'] for f in FORMATS.values()
                        if f['folder'] and (root/f['folder']/'geometry.json').exists()]
    results = {}
    for dest in folders:
        fmt, report = audit_folder(dest, deck)
        report['requires_manual_review'] = [
            'Inspect each PNG for clipped elements or overlap',
            'Proofread Arabic glyphs, punctuation and bidi text',
            'Verify claims and sources against source ledger',
            'Apply human 100-point rubric and approve only if >=90 with no blocking issue']
        (dest/'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        results[fmt] = report
    summary = results['portrait'] if len(results) == 1 and 'portrait' in results else {
        'passed': all(r['passed'] for r in results.values()), 'formats': results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(r['passed'] for r in results.values()) else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output')
    p.add_argument('--deck', required=True)
    a = p.parse_args()
    raise SystemExit(audit(a.output, a.deck))
