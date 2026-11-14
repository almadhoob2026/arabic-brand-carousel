# JSON deck contract (renderer v1)

Root:
- `brand_profile` (optional): path to a reusable profile `{brand, design?, hashtags?}`; deck values override it. Create one with `scripts/brand.py init`.
- `formats` (optional): any of `portrait` (1080×1350), `square` (1080×1080), `story` (1080×1920). CLI `--formats` overrides it.
- `publish` (optional): `{caption ≤2200, hashtags[≤30], first_comment?}` → `caption.txt`, `publish.json`.
- `brand` (required unless the profile supplies it): `{name, handle?, category?, logo?, background?, foreground?, accent?, muted?, surface?, font_family?, font_file?}`
- `slides` (required): 2–10 items, each with `{kind?, eyebrow?, headline, body?, bullets?, source?, cta?, decorative?, image?, metric?, compare?, quote?, timeline?, cards?, answer?, alt?}`. `alt` (≤300 chars) is the accessibility text for the published image; when omitted it is generated from the slide copy into `alt-text.txt`.

## Layouts (v4)

| Layout (`kind`) | Content field | Use it for |
|---|---|---|
| `cover` | — (slide 1 by default) | the hook |
| `statement` | `body` | one idea with a short explanation |
| `steps` / `list` | `bullets` (≤5) | numbered actions |
| `checklist` | `bullets` + `"kind": "checklist"` | pre-flight or verification lists |
| `metric` | `metric: {value, label?}` + `source` | one striking, sourced number |
| `comparison` | `compare: {columns: [{title?, points[1–4]}, {…}]}` | two options side by side |
| `before-after` | `compare` + `"kind": "before-after"` | a transformation (titles default to قبل / بعد) |
| `quote` | `quote: {text, author?, role?}` | a principle or attributed quote |
| `timeline` | `timeline: [{label, text}] (2–5)` | stages, history, a process |
| `grid` | `cards: [{title, text?}] (2–4)` | parallel options or categories |
| `qa` | `answer` (headline = question) | FAQs and myth-busting |
| `cta` | `cta` (last slide by default) | the single closing action |

`kind` is optional: when it is omitted the layout is **inferred from the content field** present (`metric` → metric, `compare` → comparison, `quote`, `timeline`, `cards` → grid, `answer` → qa, `bullets` → steps; first slide → cover; last slide with `cta` → cta). An explicit `kind` always wins; unknown legacy kinds render as `statement`. A kind that needs a field (e.g. `metric` without `metric`) is rejected.
- `bullets`: array of at most 5 short strings. `body`: short supporting prose.
- `decorative`: `rings`, `dots`, `orb`, or `none`.

Text is treated as plain text (HTML-escaped). Input must not contain remote image/font URLs.

## Fonts

Cairo (SIL Open Font License 1.1, `fonts/OFL.txt`) is bundled in `fonts/` and embedded into `carousel.html` whenever `font_family` mentions Cairo, so output no longer depends on what is installed. To use a licensed brand font, set `brand.font_file` to a local TTF/OTF/WOFF/WOFF2 (≤5 MB); it is embedded as `BrandFont` and placed first in the font stack, and copied to `assets/` in the output.

## Geometry report

`render.py` writes `geometry.json`, measured from real glyph boxes in Chromium: `outside-safe-area` (text within 64 px of an edge), `text-overlap` (between top bar, content, source and footer), `text-over-image` (top/side layouts), `content-overflow`, plus `headline_lines`, `min_font_px` and how much display text was shrunk to fit. `audit.py` treats issues as errors and flags headlines over 4 lines, text under 22 px and shrinking over 15% as warnings.

## Images and logo

`brand.logo` and `slide.image.src` are **local file paths**, relative to the deck JSON (or absolute). URLs, `data:` and `file:` references are rejected. Accepted types are detected from the file bytes: PNG, JPEG, WebP and SVG (SVG without scripts, event handlers or external references). Limits: 10 MB per file, 40 MB per deck. Images are embedded as data URIs, so `carousel.html` stays self-contained; the output folder also gets `assets/` copies and a `deck.json` pointing at them.

```json
"image": {
  "src": "assets/photo.jpg",
  "alt": "وصف عربي مختصر لمحتوى الصورة",
  "layout": "background",
  "overlay": 0.65,
  "fit": "cover",
  "position": "50% 30%",
  "rights": "owned",
  "credit": "تصوير: …"
}
```

| Field | Required | Values |
|---|---|---|
| `src` | yes | local path |
| `alt` | yes | ≤300 chars; describes the image for accessibility and review |
| `layout` | no | `background` (full bleed + overlay, default), `top` (rounded image above text, 910×430 area), `side` (image left / text right, 400×990 area) |
| `overlay` | no | 0–0.95, background colour over the image on `background` layout (default 0.62) |
| `fit` | no | `cover` (default) or `contain` |
| `position` | no | CSS object-position keywords or percentages, e.g. `center`, `top`, `50% 30%` |
| `rights` | no* | `owned`, `licensed`, `generated`, `client-supplied` (*critique warns when missing) |
| `credit` | no | ≤120 chars, shown on the image |

Decorations are suppressed on image slides. The logo appears next to the handle in the footer (max 220×56 px area). `scripts/critique.py` checks image rights, resolution versus the layout area, and text contrast against the **brighter regions** of a background image after the overlay.

Output always renders slides at 1080x1350. Inputs must be UTF-8. The tool rejects an unsupported or excessively large deck.

## Optional design intelligence (v3)

The `design` object is optional. When omitted, defaults come from the `editorial` preset. Existing v2 decks remain valid.

```json
"design": {
  "direction": "educational",
  "design_variance": 5,
  "visual_density": 6,
  "contrast_level": 8,
  "typographic_expression": 6,
  "decoration_level": 2
}
```

Direction enum: `editorial`, `educational`, `luxury`, `bold`, `heritage`; each slider is an integer from 1 to 10. The five sliders currently influence a subset of layout/typographic presentation: they do not constitute autonomous artistic judgment. The renderer and visual editor implement their own previews and can differ in layout. `scripts/critique.py` produces a preflight report, not a rendered-image certification.
