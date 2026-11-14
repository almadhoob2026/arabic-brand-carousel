# Visual Taste Engine — explainable configuration

A local, original implementation influenced by the general *layered design* concepts discussed in the user-provided **Design Skills Guide**. This repository does not copy or depend on the external skill projects mentioned in that guide.

## Five integer sliders (1–10)

- `design_variance`: deliberate variation of layout; high is not intrinsically better.
- `visual_density`: target amount of text and supporting material; readability always wins.
- `contrast_level`: desired emphasis. It **never overrides** contrast/accessibility minimums.
- `typographic_expression`: relative scale of display headings; prevents arbitrary font choices.
- `decoration_level`: strength of supporting decorations; never place ornaments over copy.

## Directions

`editorial`, `educational`, `luxury`, `bold`, `heritage` are starting points. `design` in the deck can override any slider, as shown:

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

The browser renderer currently maps typography, line spacing and decoration opacity from these tokens. Direction changes the default slider profile, not the user's colors. Suggestions for slide kinds are **advisory**; manually chosen kinds are preserved. Other aesthetic decisions remain human-reviewed until implemented and tested.

Use `python scripts/critique.py examples/demo.json` for a preflight report, including the effective profile.
