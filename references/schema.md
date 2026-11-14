# JSON deck contract (renderer v1)

Root:
- `brand` (required): `{name, handle?, category?, background?, foreground?, accent?, muted?, surface?, font_family?}`
- `slides` (required): 2–10 items, each with `{kind?, eyebrow?, headline, body?, bullets?, source?, cta?, decorative?}`.
- `kind`: `cover`, `statement`, `steps`, `list`, `cta` (others render using statement layout).
- `bullets`: array of at most 5 short strings. `body`: short supporting prose.
- `decorative`: `rings`, `dots`, `orb`, or `none`.

Text is treated as plain text (HTML-escaped). Input must not contain remote image/font URLs. No external assets are embedded. This minimal renderer intentionally supports typographic and abstract-shape layouts only; richer designs require extending the HTML template or using another graphic generation workflow.

Output always renders slides at 1080x1350. Inputs must be UTF-8. The tool rejects an unsupported or excessively large deck.
