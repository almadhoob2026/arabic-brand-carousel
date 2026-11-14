#!/usr/bin/env python3
"""Explainable, conservative carousel preflight critique; no false visual certification."""
import argparse
import json
import re
from pathlib import Path
from render import load_deck
from taste import taste_profile, suggest_layouts


def rgb(color):
    return tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))


def luminance(hexcolor):
    channels = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb(hexcolor)]
    return sum(x * y for x, y in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return round((x + .05) / (y + .05), 2)


def critique(deck):
    p = taste_profile(deck)
    brand = deck['brand']
    slides = deck['slides']
    items = []
    def add(severity, code, slide, issue, fix):
        items.append({'severity': severity, 'code': code, 'slide': slide, 'issue': issue, 'fix': fix})
    from render import PALETTE
    colors = {k: brand.get(k, v) for k, v in PALETTE.items()}
    text_ratio = contrast(colors['foreground'], colors['background'])
    muted_ratio = contrast(colors['muted'], colors['background'])
    if text_ratio < 4.5:
        add('blocker', 'contrast-primary', None, f'Primary text contrast {text_ratio}:1 below 4.5:1', 'Adjust foreground or background for readable contrast.')
    if muted_ratio < 4.5:
        add('warning', 'contrast-secondary', None, f'Muted text contrast {muted_ratio}:1 below 4.5:1', 'Increase muted text contrast or limit it to noncritical decoration.')
    headlines = {}
    prev_deco = None
    deco_streak = 0
    for i, slide in enumerate(slides, 1):
        head = re.sub(r'\s+', ' ', slide['headline']).strip()
        if head in headlines:
            add('blocker', 'repeated-headline', i, f'Headline duplicated with slide {headlines[head]}', 'Rewrite one slide to carry a distinct idea.')
        headlines[head] = i
        if len(head) > 75:
            add('warning', 'long-headline', i, f'Headline contains {len(head)} characters', 'Condense the headline before shrinking typography.')
        words = ' '.join([head, str(slide.get('body', '')), *slide.get('bullets', [])]).split()
        if len(words) > 40:
            add('warning', 'content-density', i, f'{len(words)} words exceed the 40-word editorial target', 'Split supporting content or simplify copy.')
        if slide.get('metric') and not slide.get('source'):
            add('warning', 'unsourced-metric', i, 'Metric has no cited source', 'Provide a verifiable source or identify it as an illustration.')
        deco = slide.get('decorative', 'none')
        deco_streak = deco_streak + 1 if deco == prev_deco else 1
        if deco != 'none' and deco_streak >= 3:
            add('advice', 'repetitive-decoration', i, f'{deco} used in {deco_streak} consecutive slides', 'Change the visual composition if repetition does not reinforce the story.')
        prev_deco = deco
    if not slides[-1].get('cta'):
        add('advice', 'cta-absent', len(slides), 'Last slide has no explicit CTA', 'Add one relevant action when the content objective calls for it.')
    scores = {'content': 25, 'visual': 25, 'arabic': 20, 'evidence': 15, 'technical': 15}
    for f in items:
        category = 'evidence' if f['code'] in ('unsourced-metric',) else 'visual' if 'contrast' in f['code'] or 'decoration' in f['code'] else 'content'
        scores[category] = max(0, scores[category] - {'blocker': 8, 'warning': 3, 'advice': 1}[f['severity']])
    score = sum(scores.values())
    blockers = sum(f['severity'] == 'blocker' for f in items)
    return {'version': '3.0', 'kind': 'preflight-not-visual-certification',
            'profile': p, 'score_estimate': score, 'score_breakdown': scores,
            'passed_preflight': score >= 90 and blockers == 0,
            'requires_visual_review': True, 'findings': items, 'suggested_layouts': suggest_layouts(deck)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('deck')
    ap.add_argument('--out', default='')
    ap.add_argument('--strict', action='store_true', help='Exit nonzero if any blocker')
    args = ap.parse_args()
    report = critique(load_deck(args.deck))
    data = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(data, encoding='utf-8')
    print(data)
    return 1 if args.strict and any(f['severity'] == 'blocker' for f in report['findings']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
