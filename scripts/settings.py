#!/usr/bin/env python3
"""Per-project carousel defaults, chosen in the settings step before a run.

Stored in <project>/.carousel/settings.json so later runs can reuse them.

    python scripts/settings.py show
    python scripts/settings.py set --formats portrait,story --pdf --slides 7 \
        --register gulf --direction editorial --images none --brand-profile brands/acme.json
    python scripts/settings.py deck-fields      # JSON to merge into a new deck
    python scripts/settings.py clear

All commands accept --file to use another path (default: ./.carousel/settings.json).
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from formats import parse_formats  # noqa: E402
from taste import PRESETS  # noqa: E402

DEFAULT_FILE = Path('.carousel') / 'settings.json'
REGISTERS = {'msa': 'فصحى', 'gulf': 'خليجي', 'match': 'حسب أسلوب الحساب'}
IMAGES = {'own': 'صور المستخدم', 'none': 'بدون صور', 'generated': 'صور مولّدة بموافقة'}
DEFAULTS = {'formats': ['portrait'], 'pdf': False, 'slides': 7, 'register': 'msa',
            'direction': 'editorial', 'images': 'none', 'brand_profile': None}


def validate(s):
    if not isinstance(s, dict):
        raise ValueError('settings must be an object')
    unknown = set(s) - set(DEFAULTS) - {'version', 'updated'}
    if unknown:
        raise ValueError(f'unknown settings: {", ".join(sorted(unknown))}')
    out = {**DEFAULTS, **{k: v for k, v in s.items() if k in DEFAULTS}}
    out['formats'] = list(parse_formats(out['formats']))
    if type(out['pdf']) is not bool:
        raise ValueError('pdf must be true or false')
    if type(out['slides']) is not int or not 2 <= out['slides'] <= 10:
        raise ValueError('slides must be an integer from 2 to 10')
    if out['register'] not in REGISTERS:
        raise ValueError(f'register must be one of {", ".join(REGISTERS)}')
    if out['direction'] not in PRESETS:
        raise ValueError(f'direction must be one of {", ".join(PRESETS)}')
    if out['images'] not in IMAGES:
        raise ValueError(f'images must be one of {", ".join(IMAGES)}')
    bp = out['brand_profile']
    if bp is not None:
        from assets import check_reference
        check_reference(bp, 'brand_profile')
    return out


def load(path=DEFAULT_FILE):
    path = Path(path)
    if not path.exists():
        return None
    return validate(json.loads(path.read_text(encoding='utf-8')))


def save(values, path=DEFAULT_FILE):
    path = Path(path)
    current = load(path) or {}
    merged = validate({**current, **{k: v for k, v in values.items() if v is not None}})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'version': 1, 'updated': date.today().isoformat(), **merged},
                               ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return merged


def deck_fields(s):
    """Fields a new deck should start with; the copy itself is still written per topic."""
    fields = {'formats': s['formats'], 'design': {'direction': s['direction']}}
    if s['brand_profile']:
        fields['brand_profile'] = s['brand_profile']
    return fields


def summary(s):
    return (f"المقاسات: {', '.join(s['formats'])}{' + PDF' if s['pdf'] else ''} · "
            f"الشرائح: {s['slides']} · اللغة: {REGISTERS[s['register']]} · الطابع: {s['direction']} · "
            f"الصور: {IMAGES[s['images']]} · الهوية: {s['brand_profile'] or 'محايدة/من الطلب'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('show', 'deck-fields', 'clear'):
        sub.add_parser(name).add_argument('--file', default=str(DEFAULT_FILE))
    st = sub.add_parser('set')
    st.add_argument('--file', default=str(DEFAULT_FILE))
    st.add_argument('--formats')
    st.add_argument('--pdf', action=argparse.BooleanOptionalAction, default=None)
    st.add_argument('--slides', type=int)
    st.add_argument('--register', choices=list(REGISTERS))
    st.add_argument('--direction', choices=list(PRESETS))
    st.add_argument('--images', choices=list(IMAGES))
    st.add_argument('--brand-profile')
    st.add_argument('--no-brand-profile', action='store_true', help='switch back to a neutral identity')
    a = ap.parse_args()
    try:
        if a.cmd == 'show':
            s = load(a.file)
            print(json.dumps({'saved': s is not None, 'settings': s, 'summary': summary(s) if s else None},
                             ensure_ascii=False, indent=2))
        elif a.cmd == 'deck-fields':
            print(json.dumps(deck_fields(load(a.file) or validate({})), ensure_ascii=False, indent=2))
        elif a.cmd == 'clear':
            Path(a.file).unlink(missing_ok=True)
            print('cleared')
        else:
            values = {'formats': a.formats.split(',') if a.formats else None, 'pdf': a.pdf, 'slides': a.slides,
                      'register': a.register, 'direction': a.direction, 'images': a.images,
                      'brand_profile': a.brand_profile}
            s = save(values, a.file)
            if a.no_brand_profile:
                s = _drop_profile(a.file)
            print(json.dumps({'saved': True, 'settings': s, 'summary': summary(s)}, ensure_ascii=False, indent=2))
    except (ValueError, json.JSONDecodeError) as exc:
        sys.exit(f'settings error: {exc}')


def _drop_profile(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    data['brand_profile'] = None
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return validate(data)


if __name__ == '__main__':
    main()
