#!/usr/bin/env python3
"""Slide layout families: field validation, kind inference, HTML and CSS.

Each layout is driven by structured content fields so the copy stays editable JSON:

    metric      slide.metric   = {value, label?}
    comparison  slide.compare  = {columns: [{title, points[]}, {title, points[]}]}
    before-after slide.compare (column titles default to قبل / بعد)
    quote       slide.quote    = {text, author?, role?}
    timeline    slide.timeline = [{label, text}, …]  (2–5)
    checklist   slide.bullets  (rendered with check marks)
    grid        slide.cards    = [{title, text}, …]  (2–4)
    qa          slide.answer   (headline is the question)
"""
import html

BASE_KINDS = ('cover', 'statement', 'steps', 'list', 'cta')
NEW_KINDS = ('metric', 'comparison', 'before-after', 'quote', 'timeline', 'checklist', 'grid', 'qa')
KINDS = BASE_KINDS + NEW_KINDS
REQUIRES = {'metric': 'metric', 'comparison': 'compare', 'before-after': 'compare', 'quote': 'quote',
            'timeline': 'timeline', 'grid': 'cards', 'qa': 'answer', 'checklist': 'bullets'}


def t(v):
    return html.escape(str(v or ''), quote=True)


# ---------------------------------------------------------------- validation

def _text(value, field, limit, required=True):
    if value is None and not required:
        return
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > limit:
        raise ValueError(f'{field} must be text of at most {limit} characters')


def _obj(value, field, allowed):
    if not isinstance(value, dict):
        raise ValueError(f'{field} must be an object')
    unknown = set(value) - set(allowed)
    if unknown:
        raise ValueError(f'{field} has unknown keys: {", ".join(sorted(unknown))}')


def validate_fields(s, i):
    """Validate layout-specific fields of slide number i (1-based)."""
    p = f'Slide {i}'
    if 'metric' in s:
        _obj(s['metric'], f'{p} metric', ('value', 'label'))
        _text(s['metric'].get('value'), f'{p} metric.value', 24)
        _text(s['metric'].get('label'), f'{p} metric.label', 120, required=False)
    if 'compare' in s:
        _obj(s['compare'], f'{p} compare', ('columns',))
        cols = s['compare'].get('columns')
        if not isinstance(cols, list) or len(cols) != 2:
            raise ValueError(f'{p} compare.columns must contain exactly 2 columns')
        for j, col in enumerate(cols, 1):
            _obj(col, f'{p} compare column {j}', ('title', 'points'))
            _text(col.get('title'), f'{p} compare column {j} title', 40, required=False)
            pts = col.get('points')
            if not isinstance(pts, list) or not 1 <= len(pts) <= 4:
                raise ValueError(f'{p} compare column {j} needs 1–4 points')
            for x in pts:
                _text(x, f'{p} compare point', 110)
    if 'quote' in s:
        _obj(s['quote'], f'{p} quote', ('text', 'author', 'role'))
        _text(s['quote'].get('text'), f'{p} quote.text', 280)
        _text(s['quote'].get('author'), f'{p} quote.author', 60, required=False)
        _text(s['quote'].get('role'), f'{p} quote.role', 80, required=False)
    if 'timeline' in s:
        items = s['timeline']
        if not isinstance(items, list) or not 2 <= len(items) <= 5:
            raise ValueError(f'{p} timeline needs 2–5 items')
        for x in items:
            _obj(x, f'{p} timeline item', ('label', 'text'))
            _text(x.get('label'), f'{p} timeline label', 24)
            _text(x.get('text'), f'{p} timeline text', 120)
    if 'cards' in s:
        cards = s['cards']
        if not isinstance(cards, list) or not 2 <= len(cards) <= 4:
            raise ValueError(f'{p} cards needs 2–4 items')
        for x in cards:
            _obj(x, f'{p} card', ('title', 'text'))
            _text(x.get('title'), f'{p} card title', 40)
            _text(x.get('text'), f'{p} card text', 140, required=False)
    if 'answer' in s:
        _text(s['answer'], f'{p} answer', 400)
    kind = s.get('kind')
    if kind is not None:
        if not isinstance(kind, str):
            raise ValueError(f'{p} kind must be text')
        need = REQUIRES.get(kind.lower())
        if need and not s.get(need):
            raise ValueError(f'{p} kind "{kind}" needs a "{need}" field')


# ---------------------------------------------------------------- inference

def infer_kind(slide, idx, n):
    """Explicit known kinds win; otherwise choose from the content fields present."""
    kind = str(slide.get('kind') or '').lower()
    if kind in KINDS:
        return kind
    if kind:  # unknown legacy kinds keep the old behaviour
        return 'statement'
    for field, k in (('metric', 'metric'), ('compare', 'comparison'), ('quote', 'quote'),
                     ('timeline', 'timeline'), ('cards', 'grid'), ('answer', 'qa')):
        if slide.get(field):
            return k
    if slide.get('bullets'):
        return 'steps'
    if idx == 1:
        return 'cover'
    if idx == n and slide.get('cta'):
        return 'cta'
    return 'statement'


def slide_text(slide):
    """All human-readable copy on a slide, for density checks."""
    parts = [slide.get('headline', ''), slide.get('body', ''), slide.get('cta', ''), slide.get('answer', '')]
    parts += slide.get('bullets') or []
    if slide.get('metric'):
        parts += [slide['metric'].get('value', ''), slide['metric'].get('label', '')]
    for col in (slide.get('compare') or {}).get('columns', []):
        parts += [col.get('title', '')] + col.get('points', [])
    if slide.get('quote'):
        parts += [slide['quote'].get(k, '') for k in ('text', 'author', 'role')]
    for x in slide.get('timeline') or []:
        parts += [x.get('label', ''), x.get('text', '')]
    for x in slide.get('cards') or []:
        parts += [x.get('title', ''), x.get('text', '')]
    return ' '.join(str(p) for p in parts if p)


# ---------------------------------------------------------------- html

def _headline(slide, extra=''):
    return f'<h1 class="headline{extra}" data-fit>{t(slide["headline"])}</h1>'


def _body(slide):
    return f'<p class="body">{t(slide["body"])}</p>' if slide.get('body') else ''


def _cta(slide):
    return f'<p class="cta-line">{t(slide["cta"])}</p>' if slide.get('cta') else ''


def _list(items, marker):
    rows = []
    for j, b in enumerate(items, 1):
        mark = f'<span class="step-num">{j:02}</span>' if marker == 'num' else '<span class="check" aria-hidden="true">✓</span>'
        rows.append(f'<li>{mark}<span>{t(b)}</span></li>')
    return f'<ul class="steps">{"".join(rows)}</ul>'


def _columns(slide, kind):
    cols = slide['compare']['columns']
    defaults = ('قبل', 'بعد') if kind == 'before-after' else ('', '')
    out = []
    for j, col in enumerate(cols):
        title = col.get('title') or defaults[j]
        pts = ''.join(f'<li>{t(x)}</li>' for x in col['points'])
        head = f'<h2 class="col-title">{t(title)}</h2>' if title else ''
        out.append(f'<div class="col{" alt" if j == 1 else ""}">{head}<ul>{pts}</ul></div>')
    arrow = '<div class="ba-arrow" aria-hidden="true">←</div>' if kind == 'before-after' else ''
    return f'<div class="compare">{out[0]}{arrow}{out[1]}</div>'


def content_html(slide, kind):
    """Inner HTML of <main class="content"> for the given layout kind."""
    eyebrow = f'<div class="eyebrow">{t(slide.get("eyebrow", ""))}</div>'
    if kind == 'metric':
        m = slide['metric']
        label = f'<div class="metric-label">{t(m["label"])}</div>' if m.get('label') else ''
        return (f'{eyebrow}<div class="metric-value" data-fit><bdi>{t(m["value"])}</bdi></div>{label}'
                f'{_headline(slide)}{_body(slide)}{_cta(slide)}')
    if kind in ('comparison', 'before-after'):
        return f'{eyebrow}{_headline(slide)}{_body(slide)}{_columns(slide, kind)}{_cta(slide)}'
    if kind == 'quote':
        q = slide['quote']
        by = '، '.join(x for x in (q.get('author'), q.get('role')) if x)
        by_html = f'<footer class="quote-by">— {t(by)}</footer>' if by else ''
        return (f'{eyebrow}{_headline(slide)}<blockquote class="quote-block">'
                f'<p class="quote-text" data-fit>«{t(q["text"])}»</p>{by_html}</blockquote>{_cta(slide)}')
    if kind == 'timeline':
        items = ''.join(f'<li><span class="tl-label"><bdi>{t(x["label"])}</bdi></span>'
                        f'<span class="tl-text">{t(x["text"])}</span></li>' for x in slide['timeline'])
        return f'{eyebrow}{_headline(slide)}{_body(slide)}<ol class="timeline">{items}</ol>{_cta(slide)}'
    if kind == 'grid':
        cards = slide['cards']
        html_cards = ''.join(f'<div class="card"><h2 class="card-title">{t(c["title"])}</h2>'
                             + (f'<p class="card-text">{t(c["text"])}</p>' if c.get('text') else '') + '</div>'
                             for c in cards)
        return f'{eyebrow}{_headline(slide)}{_body(slide)}<div class="cards n{len(cards)}">{html_cards}</div>{_cta(slide)}'
    if kind == 'qa':
        return (f'{eyebrow}<div class="qa-q"><span class="qa-badge" aria-hidden="true">س</span>{_headline(slide)}</div>'
                f'<div class="qa-a"><span class="qa-badge alt" aria-hidden="true">ج</span>'
                f'<p class="answer">{t(slide["answer"])}</p></div>{_cta(slide)}')
    if kind == 'checklist':
        return f'{eyebrow}{_headline(slide)}{_body(slide)}{_list(slide["bullets"], "check")}{_cta(slide)}'
    bullets = _list(slide['bullets'], 'num') if slide.get('bullets') else ''
    return f'{eyebrow}{_headline(slide)}{_body(slide)}{bullets}{_cta(slide)}'


LAYOUT_CSS = """
    .metric-value{font-size:230px;font-weight:900;line-height:1.05;color:var(--accent);letter-spacing:-2px;max-width:100%}
    .metric-label{font-size:40px;font-weight:700;color:var(--muted);margin:6px 0 46px;line-height:1.4}
    .metric .headline{font-size:calc(70px * var(--headline-scale))}
    .comparison .headline,.before-after .headline{font-size:calc(80px * var(--headline-scale))}
    .compare{display:grid;grid-template-columns:1fr 1fr;gap:26px;width:100%;margin-top:46px;align-items:stretch}
    .before-after .compare{grid-template-columns:1fr auto 1fr;gap:18px}
    .ba-arrow{align-self:center;font-size:56px;color:var(--accent);font-weight:900}
    .col{background:var(--surface);border-radius:26px;padding:34px 30px}
    .col.alt{box-shadow:inset 0 0 0 3px var(--accent)}
    .col-title{font-size:42px;font-weight:900;margin:0 0 20px;color:var(--accent);line-height:1.3}
    .col ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:16px}
    .col li{font-size:32px;font-weight:600;line-height:1.45;padding-right:26px;position:relative}
    .col li::before{content:'';position:absolute;right:0;top:.62em;width:10px;height:10px;border-radius:50%;background:var(--muted)}
    .col.alt li::before{background:var(--accent)}
    .quote .headline{font-size:44px;font-weight:700;color:var(--muted);letter-spacing:0;line-height:1.4}
    .quote-block{margin:40px 0 0;border-right:8px solid var(--accent);padding:6px 44px 6px 0}
    .quote-text{font-size:66px;font-weight:800;line-height:1.45;margin:0}
    .quote-by{margin-top:34px;font-size:34px;color:var(--accent);font-weight:700}
    .timeline .headline{font-size:calc(80px * var(--headline-scale))}
    .timeline{list-style:none;margin:46px 0 0;padding:0 56px 0 0;position:relative;width:100%;display:flex;flex-direction:column;gap:28px}
    .timeline li{position:relative;display:flex;flex-direction:column;gap:2px}
    .timeline li:not(:last-child)::after{content:'';position:absolute;right:-43px;top:42px;bottom:-28px;width:4px;background:var(--surface)}
    .timeline li::before{content:'';position:absolute;right:-56px;top:12px;width:30px;height:30px;border-radius:50%;background:var(--background);border:6px solid var(--accent);box-sizing:border-box}
    .tl-label{font-size:30px;font-weight:800;color:var(--accent);line-height:1.4}
    .tl-text{font-size:36px;font-weight:600;line-height:1.42}
    .check{width:48px;height:48px;flex-shrink:0;border-radius:50%;background:var(--accent);color:var(--background);display:grid;place-items:center;font-size:28px;font-weight:900;font-family:Arial,sans-serif}
    .grid .headline{font-size:calc(80px * var(--headline-scale))}
    .cards{display:grid;grid-template-columns:1fr 1fr;gap:24px;width:100%;margin-top:46px}
    .cards.n3 .card:first-child{grid-column:span 2}
    .card{background:var(--surface);border-radius:26px;padding:32px 30px}
    .card-title{font-size:40px;font-weight:900;color:var(--accent);margin:0 0 10px;line-height:1.3}
    .card-text{font-size:31px;line-height:1.5;font-weight:600;margin:0}
    .qa-q,.qa-a{display:flex;gap:28px;align-items:flex-start;width:100%}
    .qa-badge{flex-shrink:0;width:86px;height:86px;border-radius:24px;background:var(--accent);color:var(--background);font-size:46px;font-weight:900;display:grid;place-items:center}
    .qa-badge.alt{background:var(--background);color:var(--accent)}
    .qa .headline{font-size:calc(80px * var(--headline-scale))}
    .qa-a{margin-top:52px;background:var(--surface);border-radius:28px;padding:34px}
    .answer{font-size:40px;line-height:1.55;font-weight:600;margin:0}
"""
