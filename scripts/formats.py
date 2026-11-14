#!/usr/bin/env python3
"""Output formats. Every format is 1080 px wide; layouts adapt through CSS overrides.

safe: minimum distance (px) between any rendered glyph and the slide edge, checked by
the geometry pass. Stories reserve extra space where Instagram draws its own UI
(progress bar and profile on top, reply bar at the bottom).
"""

FORMATS = {
    'portrait': {
        'size': (1080, 1350), 'scale': 1.0, 'folder': '',
        'safe': {'top': 64, 'bottom': 64, 'side': 64},
        'use': 'Instagram/Facebook feed carousel (4:5), LinkedIn PDF',
        'css': '',
    },
    'square': {
        'size': (1080, 1080), 'scale': 0.84, 'folder': 'square',
        'safe': {'top': 48, 'bottom': 48, 'side': 64},
        'use': 'Square feeds, X/Twitter, LinkedIn image posts (1:1)',
        'css': """
    .slide{height:1080px}
    .topbar{top:52px}.footer{bottom:50px}
    .content{top:168px;bottom:132px}
    .source{bottom:108px}
    .eyebrow{margin-bottom:22px;font-size:31px}
    .body{margin-top:28px}
    .metric-value{font-size:180px}.metric-label{margin-bottom:26px}
    .quote-text{font-size:56px}.quote-block{margin-top:26px}
    .compare,.cards,.timeline{margin-top:30px}.timeline{gap:18px}
    .steps{margin-top:24px;gap:12px}.steps li{padding:16px 24px;font-size:32px}
    .col{padding:26px 24px}.col li{font-size:29px}.card{padding:24px}.card-text{font-size:28px}
    .tl-text{font-size:32px}.answer{font-size:35px}.qa-a{margin-top:32px;padding:28px}
    .img-top .media{top:160px;height:300px}
    .img-top .content{top:490px}
    .img-side .media{top:160px;bottom:125px;width:360px}
    .img-side .content,.img-side:nth-child(3n) .content{left:485px}
    .img-side .source{left:485px}
    .img-background .credit{top:118px}""",
    },
    'story': {
        'size': (1080, 1920), 'scale': 1.0, 'folder': 'story',
        'safe': {'top': 250, 'bottom': 340, 'side': 64},
        'use': 'Instagram/Facebook stories and reels covers (9:16)',
        'css': """
    .slide{height:1920px}
    .topbar{top:260px}.footer{bottom:360px}
    .content{top:420px;bottom:500px}
    .source{bottom:460px}
    .swipe{display:none}
    .img-top .media{top:400px;height:560px}
    .img-top .content{top:1000px}
    .img-side .media{top:420px;bottom:520px;width:400px}
    .img-background .credit{top:400px}""",
    },
}


def parse_formats(value):
    """'portrait,story' or a list → validated tuple, portrait first when present."""
    if value is None:
        return ('portrait',)
    items = value.split(',') if isinstance(value, str) else value
    if not isinstance(items, (list, tuple)) or not items:
        raise ValueError('formats must be a list such as ["portrait", "story"]')
    out = []
    for f in items:
        f = str(f).strip().lower()
        if f not in FORMATS:
            raise ValueError(f'Unknown format "{f}"; use {", ".join(FORMATS)}')
        if f not in out:
            out.append(f)
    return tuple(sorted(out, key=list(FORMATS).index))
