# JSON deck contract (renderer v1)

Root:
- `brand` (required): `{name, handle?, category?, background?, foreground?, accent?, muted?, surface?, font_family?}`
- `slides` (required): 2–10 items, each with `{kind?, eyebrow?, headline, body?, bullets?, source?, cta?, decorative?}`.
- `kind`: `cover`, `statement`, `steps`, `list`, `cta` (others render using statement layout).
- `bullets`: array of at most 5 short strings. `body`: short supporting prose.
- `decorative`: `rings`, `dots`, `orb`, or `none`.

Text is treated as plain text (HTML-escaped). Input must not contain remote image/font URLs. No external assets are embedded. This minimal renderer intentionally supports typographic and abstract-shape layouts only; richer designs require extending the HTML template or using another graphic generation workflow.

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
