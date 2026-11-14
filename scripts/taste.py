#!/usr/bin/env python3
"""Brand-first, deterministic taste profile selection. No third-party skill dependency."""
from copy import deepcopy

PRESETS = {
    'editorial': {'design_variance': 7, 'visual_density': 4, 'contrast_level': 8,
                  'typographic_expression': 8, 'decoration_level': 3},
    'educational': {'design_variance': 5, 'visual_density': 6, 'contrast_level': 8,
                    'typographic_expression': 6, 'decoration_level': 2},
    'luxury': {'design_variance': 4, 'visual_density': 3, 'contrast_level': 8,
               'typographic_expression': 7, 'decoration_level': 2},
    'bold': {'design_variance': 9, 'visual_density': 4, 'contrast_level': 10,
             'typographic_expression': 10, 'decoration_level': 5},
    'heritage': {'design_variance': 6, 'visual_density': 4, 'contrast_level': 8,
                 'typographic_expression': 7, 'decoration_level': 5},
}
LEVELS = tuple(next(iter(PRESETS.values())).keys())
DECORATIONS = ('none', 'dots', 'rings', 'orb')


def taste_profile(deck):
    """Return validated effective profile; preserve the user-selected brand palette."""
    design = deck.get('design', {})
    if not isinstance(design, dict):
        raise ValueError('design must be an object')
    direction = design.get('direction', 'editorial')
    if direction not in PRESETS:
        raise ValueError('design.direction must be one of '+', '.join(PRESETS))
    values = deepcopy(PRESETS[direction])
    for key in LEVELS:
        if key in design:
            value = design[key]
            if type(value) is not int or not 1 <= value <= 10:
                raise ValueError(f'design.{key} must be an integer between 1 and 10')
            values[key] = value
    return {'direction': direction, **values}


def suggest_layouts(deck):
    """Suggest variant layouts without modifying user-authored content or explicit kinds."""
    from layouts import infer_kind
    profile = taste_profile(deck)
    slides = deck['slides']
    suggestions = []
    for i, s in enumerate(slides):
        content_kind = infer_kind({k: v for k, v in s.items() if k != 'kind'}, i + 1, len(slides))
        if content_kind not in ('cover', 'statement', 'steps', 'cta'):
            kind = content_kind  # structured content decides the layout
        elif i == 0:
            kind = 'cover'
        elif i == len(slides) - 1:
            kind = 'cta'
        elif s.get('bullets'):
            kind = 'steps'
        elif profile['design_variance'] >= 7 and i % 3 == 0:
            kind = 'metric' if s.get('metric') else 'statement'
        else:
            kind = 'statement'
        suggestions.append({'slide': i + 1, 'suggested_kind': kind,
                            'current_kind': s.get('kind', 'statement')})
    return suggestions


def css_tokens(profile):
    """Translate sliders to stable, constrained CSS variables."""
    type_expression = profile['typographic_expression']
    density = profile['visual_density']
    decoration = profile['decoration_level']
    return {
        '--headline-scale': f'{0.88 + type_expression * .024:.3f}',
        '--body-scale': f'{0.94 + density * .012:.3f}',
        '--body-leading': f'{1.82 - density * .038:.3f}',
        '--content-gap': f'{max(18, 59 - density * 4)}px',
        '--decoration-opacity': f'{decoration / 10:.2f}',
        '--layout-shift': f'{max(0, (profile["design_variance"] - 5) * 8)}px',
        '--accent-rule': f'{max(0, profile["contrast_level"] - 4)}px',
    }
