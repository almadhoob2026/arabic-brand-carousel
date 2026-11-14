#!/usr/bin/env python3
"""Explainable, conservative carousel preflight critique; no false visual certification."""
import argparse
import json
import re
from pathlib import Path
from render import load_deck
from taste import taste_profile, suggest_layouts
from layouts import infer_kind, slide_text


def rgb(color):
    return tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))


def luminance(hexcolor):
    channels = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb(hexcolor)]
    return sum(x * y for x, y in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return round((x + .05) / (y + .05), 2)


def blend(rgb, hexcolor, alpha):
    """Colour of an overlay of hexcolor at opacity alpha on top of rgb, as #RRGGBB."""
    over = [int(hexcolor[i:i+2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(c * (1 - alpha) + o * alpha):02X}' for c, o in zip(rgb, over))


def image_findings(deck, base_dir, colors, add):
    from assets import load_image, LAYOUT_BOX
    refs = []
    if deck['brand'].get('logo'):
        refs.append((None, 'logo', deck['brand']['logo'], None))
    for i, slide in enumerate(deck['slides'], 1):
        if slide.get('image'):
            img = slide['image']
            refs.append((i, img.get('layout', 'background'), img['src'], img))
    for slide_no, layout, src, spec in refs:
        try:
            info = load_image(src, base_dir)
        except (OSError, ValueError) as exc:
            add('blocker', 'image-unreadable', slide_no, str(exc), 'Fix the path or supply a PNG/JPEG/WebP/SVG file you have rights to.')
            continue
        if spec is not None and not spec.get('rights'):
            add('warning', 'image-rights', slide_no, 'Image has no declared rights status',
                'Set image.rights to owned / licensed / generated / client-supplied after confirming permission.')
        box_w, box_h = LAYOUT_BOX[layout]
        if info['width'] and (info['width'] < box_w * 0.9 or info['height'] < box_h * 0.9):
            add('warning', 'image-low-resolution', slide_no,
                f'{info["width"]}x{info["height"]} px is smaller than the {box_w}x{box_h} px {layout} area',
                'Supply a larger original; upscaled images look soft on phones.')
        if layout == 'background' and info['bright_rgb']:
            ov = float(spec.get('overlay', 0.62))
            worst = contrast(colors['foreground'], blend(info['bright_rgb'], colors['background'], ov))
            typical = contrast(colors['foreground'], blend(info['mean_rgb'], colors['background'], ov))
            if worst < 4.5:
                add('blocker', 'image-text-contrast', slide_no,
                    f'Text over the brighter parts of the image ≈{worst}:1 (average {typical}:1, overlay {ov:.2f}); needs ≥4.5:1',
                    'Raise image.overlay, use a darker/calmer photo, or switch layout to top/side.')
            elif worst < 7:
                add('advice', 'image-busy-background', slide_no,
                    f'Bright areas leave ≈{worst}:1 contrast; fine for large text, tight for small labels',
                    'Inspect the PNG; raise overlay if a word sits on a bright detail.')


def critique(deck, base_dir=None):
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
    kinds = []
    deco_streak = 0
    for i, slide in enumerate(slides, 1):
        head = re.sub(r'\s+', ' ', slide['headline']).strip()
        if head in headlines:
            add('blocker', 'repeated-headline', i, f'Headline duplicated with slide {headlines[head]}', 'Rewrite one slide to carry a distinct idea.')
        headlines[head] = i
        if len(head) > 75:
            add('warning', 'long-headline', i, f'Headline contains {len(head)} characters', 'Condense the headline before shrinking typography.')
        words = slide_text(slide).split()
        if len(words) > 40:
            add('warning', 'content-density', i, f'{len(words)} words exceed the 40-word editorial target', 'Split supporting content or simplify copy.')
        if slide.get('metric') and not slide.get('source'):
            add('warning', 'unsourced-metric', i, 'Metric has no cited source', 'Provide a verifiable source or identify it as an illustration.')
        deco = slide.get('decorative', 'none')
        deco_streak = deco_streak + 1 if deco == prev_deco else 1
        if deco != 'none' and deco_streak >= 3:
            add('advice', 'repetitive-decoration', i, f'{deco} used in {deco_streak} consecutive slides', 'Change the visual composition if repetition does not reinforce the story.')
        prev_deco = deco
        kinds.append(infer_kind(slide, i, len(slides)))
    interior = kinds[1:-1]
    for j in range(2, len(interior)):
        if interior[j] == interior[j-1] == interior[j-2]:
            add('advice', 'repetitive-layout', j + 2, f'Layout "{interior[j]}" used on three consecutive slides',
                'Use a comparison, metric, quote, timeline, grid or Q&A layout where the content allows.')
            break
    if base_dir is not None:
        image_findings(deck, base_dir, colors, add)
    if not slides[-1].get('cta'):
        add('advice', 'cta-absent', len(slides), 'Last slide has no explicit CTA', 'Add one relevant action when the content objective calls for it.')
    scores = {'content': 25, 'visual': 25, 'arabic': 20, 'evidence': 15, 'technical': 15}
    for f in items:
        category = ('evidence' if f['code'] in ('unsourced-metric', 'image-rights') else
                    'technical' if f['code'] in ('image-unreadable', 'image-low-resolution') else
                    'visual' if 'contrast' in f['code'] or 'decoration' in f['code'] or f['code'].startswith('image-') else 'content')
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
    report = critique(load_deck(args.deck), base_dir=Path(args.deck).parent)
    data = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(data, encoding='utf-8')
    print(data)
    return 1 if args.strict and any(f['severity'] == 'blocker' for f in report['findings']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
