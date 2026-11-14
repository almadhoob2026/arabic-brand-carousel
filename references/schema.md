# JSON deck contract (renderer v1)

Root:
- `brand` (required): `{name, handle?, category?, logo?, background?, foreground?, accent?, muted?, surface?, font_family?}`
- `slides` (required): 2–10 items, each with `{kind?, eyebrow?, headline, body?, bullets?, source?, cta?, decorative?, image?}`.
- `kind`: `cover`, `statement`, `steps`, `list`, `cta` (others render using statement layout).
- `bullets`: array of at most 5 short strings. `body`: short supporting prose.
- `decorative`: `rings`, `dots`, `orb`, or `none`.

Text is treated as plain text (HTML-escaped). Input must not contain remote image/font URLs.

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
