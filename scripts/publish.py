#!/usr/bin/env python3
"""Publishing pack: caption, hashtags, first comment and per-slide alt text.

The renderer never posts anything. It writes text files the user pastes into the
platform. Limits follow Instagram's caption (2,200 characters) and hashtag (30) caps.
"""
import json
import re

from layouts import slide_text

CAPTION_MAX = 2200
HASHTAGS_MAX = 30
ALT_MAX = 300
HASHTAG = re.compile(r'^#?[0-9A-Za-z_؀-ۿݐ-ݿ]{1,100}$')


def validate_publish(pub):
    if not isinstance(pub, dict):
        raise ValueError('publish must be an object')
    unknown = set(pub) - {'caption', 'hashtags', 'first_comment'}
    if unknown:
        raise ValueError(f'publish has unknown keys: {", ".join(sorted(unknown))}')
    for key in ('caption', 'first_comment'):
        if key in pub and (not isinstance(pub[key], str) or len(pub[key]) > CAPTION_MAX):
            raise ValueError(f'publish.{key} must be text of at most {CAPTION_MAX} characters')
    tags = pub.get('hashtags', [])
    if not isinstance(tags, list) or len(tags) > HASHTAGS_MAX:
        raise ValueError(f'publish.hashtags must be a list of at most {HASHTAGS_MAX} tags')
    for tag in tags:
        if not isinstance(tag, str) or not HASHTAG.fullmatch(tag):
            raise ValueError(f'Invalid hashtag {tag!r}: letters, digits and _ only, no spaces')


def validate_slide_alt(slide, i):
    alt = slide.get('alt')
    if alt is not None and (not isinstance(alt, str) or not alt.strip() or len(alt) > ALT_MAX):
        raise ValueError(f'Slide {i} alt must be text of at most {ALT_MAX} characters')


def normalise_tags(tags):
    seen, out = set(), []
    for tag in tags:
        tag = '#' + tag.lstrip('#')
        if tag.lower() not in seen:
            seen.add(tag.lower())
            out.append(tag)
    return out


def default_alt(slide, i, n):
    """Readable description built from the slide copy when no alt is authored."""
    head = slide['headline'].strip()
    if head[-1:] not in ('.', '؟', '?', '!', ':', '…'):
        head += '.'
    rest = re.sub(r'\s+', ' ', slide_text({k: v for k, v in slide.items() if k != 'headline'})).strip()
    text = f'{head} {rest}' if rest else head
    if slide.get('image'):
        text = f'{slide["image"]["alt"]} — {text}'
    alt = f'الشريحة {i} من {n}: {text}'
    return alt if len(alt) <= ALT_MAX else alt[:ALT_MAX - 1].rstrip() + '…'


def build_pack(deck):
    pub = deck.get('publish') or {}
    n = len(deck['slides'])
    tags = normalise_tags(pub.get('hashtags', []))
    caption = pub.get('caption', '').strip()
    full = caption + ('\n\n' + ' '.join(tags) if tags else '')
    alts = [s.get('alt') or default_alt(s, i, n) for i, s in enumerate(deck['slides'], 1)]
    warnings = []
    if not caption:
        warnings.append('No caption written; add publish.caption before posting.')
    if len(full) > CAPTION_MAX:
        warnings.append(f'Caption plus hashtags is {len(full)} characters; Instagram allows {CAPTION_MAX}.')
    return {
        'caption': caption, 'hashtags': tags, 'caption_with_hashtags': full,
        'first_comment': pub.get('first_comment', ''),
        'alt_text': [{'slide': i, 'alt': a, 'authored': bool(s.get('alt'))}
                     for i, (s, a) in enumerate(zip(deck['slides'], alts), 1)],
        'warnings': warnings,
    }


def write_pack(deck, dest):
    pack = build_pack(deck)
    (dest / 'publish.json').write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding='utf-8')
    (dest / 'caption.txt').write_text(pack['caption_with_hashtags'] + '\n', encoding='utf-8')
    (dest / 'alt-text.txt').write_text(
        '\n'.join(f'{a["slide"]:02d}: {a["alt"]}' for a in pack['alt_text']) + '\n', encoding='utf-8')
    return pack
