---
name: arabic-brand-carousel
description: >-
  Plan, write, design, render and audit a branded Arabic RTL Instagram carousel
  from a topic or brief. Use for Arabic social media carousel requests involving
  content strategy, slide storytelling, typography, visual consistency, or export.
  Supports 1080x1350 PNG slides, editable HTML and accessible review previews.
  Triggers on Arabic requests such as "كاروسيل", "سوي لي كاروسيل", "شرائح انستقرام",
  "بوست سلايدات" or "حوّل هذا الموضوع إلى كاروسيل".
---

# Arabic Brand Carousel — production workflow (v5.0)

## Mission
Turn the user's topic into a concise, accurate, visually consistent Arabic carousel. Act as an editor, designer, Arabic typesetter and QA reviewer. The deliverable is not only a list of slide captions: it is a rendered and checked collection of assets plus an editable source.

## Operating principles
1. **Reuse context first.** Infer brand, audience, dialect and preferred style from provided references. Ask at most one compact question only if a truly essential detail is missing. When no identity is supplied, use a clearly declared neutral identity (near-black / warm white / one accent); never fabricate the client's logo.
2. **Default to Modern Standard Arabic** for institutions and professional accounts; match the user's dialect for informal brands when requested or clearly established. Avoid mixing registers accidentally.
3. **Content before aesthetics.** Choose the smallest slide count that tells the story. Default 7; typically 5–8, maximum 10 unless requested. No padding/filler slides.
4. **Do not hallucinate evidence.** Verify time-sensitive data against credible sources when browsing is available. Put concise source labels or citations on relevant slides and provide full references in an accompanying note. If verification is unavailable, remove numerical claims or label them as unverified rather than inventing sources.
5. **Source and permission safety.** Use brand assets and photographs supplied/licensed by the user or explicitly approved/generated visuals. Do not download, embed, or redistribute unauthorized fonts or imagery. Never claim a supplied design is unchanged if it was modified.
6. **Respect platform and system constraints.** Follow the host environment's tool rules. Prefer image-generation tools for requested visual creations when the host requires them; this repository's browser renderer is an optional deterministic implementation, not a way to bypass tool restrictions.

## Stage 1 — Intake and brand memory
Extract a structured brief with: topic, takeaway, objective (awareness/education/leads/announcement), audience, tone/register, CTA, constraints, brand name/handle/logo, color palette, assets, citations and target platform. Infer what is known. Ask only for a missing logo/wordmark and palette when meaningful brand fidelity cannot otherwise be achieved; proceed with declared defaults if the user prefers. Never ask users to choose font or layout unless they ask.

**Reusable brand profile.** If the project has `brands/*.json`, reference it with `"brand_profile": "brands/<name>.json"` instead of repeating brand values; deck values override the profile and profile hashtags become default publish hashtags. With only a logo, run `scripts/brand.py init --logo <file> --name <name> --out brands/<slug>.json` and show the user the derived palette and contrast report for confirmation; a derived palette is never presented as the official brand guide.

Brand tokens: background, foreground, accent, muted, surface, font family, safe zones, typography scale, highlight style, image treatment, category label and brand mark placement. Inspect references for these. If brand guidance conflicts with the default template, brand guidance wins unless it compromises readability or safety.


## Stage 1a — Brand-first visual intelligence (v3)
Read `BRAND.md`, `DESIGN.md`, and `EDITORIAL.md` when project-specific copies exist. Treat placeholders as unconfigured, not user facts. Brand constraints and readability override any preset. Before rendering, choose the visual direction from `references/visual-directions.md` and configure `design` sliders using `references/taste-engine.md`. Choose values for the brief rather than maximizing every slider.

The five taste dimensions are `design_variance`, `visual_density`, `contrast_level`, `typographic_expression`, and `decoration_level` (integers 1–10). In the deck JSON, use `design.direction` with optional overrides. The default direction is `editorial`; all existing decks without `design` still work. Presets do not replace the brand palette or invent logos. Design tokens affect the deterministic renderer only where implemented and tested; layout advice is not a promise of automated restructuring.

## Stage 2 — Research, editorial strategy and fact control
Write privately before layout: (a) one-sentence promise; (b) audience pain point; (c) distinctive editorial angle; (d) hierarchy of supporting claims; (e) desired reader action.

Choose a narrative arc deliberately: hook → context → explanation → demonstration → useful takeaway → CTA. Other valid arcs include myth/fact, problem/solution, before/after, comparison, checklist, timeline, story, and practical how-to. The hook must make sense on its own. Every middle slide must contribute one new idea. The last slide contains one clear and relevant CTA; do not automatically add engagement bait.

Maintain a claim ledger for numerical, scientific, legal, financial and historical facts: claim, source URL/title, source date, verification status and destination slide. Distinguish verified facts, opinion, examples and illustrative data. High-stakes claims need stronger verification and neutral wording. Refer to `references/editorial.md`.

## Stage 3 — Slide script
Construct an outline, then write exact copy. Slide 1: 1 arresting idea + clear subject; slides 2–N−1: 1 core idea each; final: 1 CTA + brand mark. Default target ≤35 Arabic words/slide (hard editorial target 40, exceptions for citations). Keep 1–2 short supporting lines rather than paragraphs. A word count is not a spatial fit test. Avoid arbitrary sentence splitting, excessive punctuation, or unattributed quotes.

Use varied, purposeful compositions. The renderer has real layouts for each, driven by structured fields (full table in `references/schema.md`): `metric` for one sourced number, `compare` for two options (or `"kind": "before-after"` for a change), `quote`, `timeline` for stages, `cards` for 2–4 parallel ideas, `answer` for a Q&A slide, `bullets` for steps or `"kind": "checklist"`. Put the copy into the matching field and omit `kind` to let the layout be inferred. Do not repeat the same interior layout more than twice in a row. Reserve enough whitespace to make the headline dominant. Headlines should normally fit 2–4 lines; rewrite before shrinking. Never sacrifice Arabic legibility for decorative effects.

## Stage 4 — Layout & type system
Default Instagram portrait canvas: **1080×1350 px**. RTL direction. Default safe area ≥80 px around edges, with additional reserve for a persistent brand bar. Repeat counter (upper left), category tag (upper right), brand mark (lower left), swipe cue (lower right except final). Adapt these positions only when brand assets or visual hierarchy require it.

Typography is responsive: initial headline range ~76–124 px; supporting text ~38–52 px; small labels ~26–36 px. These are *starting values*, not fixed absolutes. The headline's width, line breaks, and physical bounds determine size. Do not reduce supporting copy below readable mobile scale just to fit more words. Cairo (OFL) is bundled and embedded automatically; for a brand typeface use `brand.font_file` with a local font the user is licensed to use. Never rely on network font downloads. Carefully test Arabic joining, diacritics, Arabic-Indic digits, parentheses, mixed Latin segments, RTL alignment and punctuation.

Color: WCAG-inspired strong contrast for text. Limit to one dominant accent plus semantic exceptions. Use deliberate highlights, not a mandatory underline on every slide. Illustrations and shapes reinforce meaning and stay behind text. Respect user's 'no frames' preference when present. Photos are only used when permitted by the user and are not sourced from search without appropriate rights.

**Images and logo in the renderer.** When the user supplies a logo or images (or approves generated ones), save them next to the deck and reference them by local path: `brand.logo` and per-slide `image` with `layout` = `background` / `top` / `side`, a required Arabic `alt`, and `rights`. Prefer an image on the cover and on 1–3 key slides rather than every slide. Full field list in `references/schema.md`. Never point to remote URLs; download/convert only files the user owns or provided.

## Stage 5 — Production
Run the scripts from this skill's own directory (the folder containing this `SKILL.md`), or prefix paths with it. The repository's example implementation accepts a JSON slide deck and creates one editable HTML file, individual PNG files and a contact sheet. See `README.md` and `examples/demo.json`. When using it:

Python: use `.venv/bin/python` in this skill's directory; if it is missing, run `bash scripts/setup.sh` once (creates `.venv`, installs requirements, and Chromium only when no system browser exists).

```bash
bash scripts/setup.sh                       # once
python scripts/render.py examples/demo.json --out output/demo
python scripts/render.py examples/demo-images.json --out output/demo-images   # images + logo
python scripts/audit.py output/demo --deck examples/demo.json
```

**Formats and PDF.** Add `--formats portrait,square,story` (or `"formats": [...]` in the deck) when the user mentions stories, square posts or several platforms; extra formats render into `square/` and `story/`. Stories keep text out of Instagram's top 250 px and bottom 340 px. Add `--pdf` for LinkedIn document posts (vector text, one page per slide).

**Publishing pack.** Always add `"publish": {"caption", "hashtags", "first_comment"?}` (caption ≤2,200 characters, ≤30 hashtags without spaces) and an `alt` on slides whose meaning is visual; slides without `alt` get one generated from their copy. The renderer writes `caption.txt`, `alt-text.txt` and `publish.json`. It never posts anything.

If dependencies or browser are unavailable, report the limitation and supply a complete edit-ready deck/source instead of claiming renders exist. Render at native 1080×1350; do not upscale an image preview and pretend it is native resolution. Avoid remote scripts/fonts/images in the deterministic renderer.

## Stage 5a — Explainable critique and polish (v3)
Before final export, run `python scripts/critique.py examples/demo.json --out output/critique.json`. It identifies duplicate headlines, overlong content, contrast defects, repetitive decorations, and missing sources on explicit `metric` fields. Review proposed layout families *as suggestions*; respect authored kinds. Read `references/anti-patterns.md` and `references/critique-polish.md` for hard-versus-soft failures, actionable correction, rerendering and visual review. Recheck after each correction.

Never call an automatic score a visually certified design. The report is preflight only; rendered-image review and fact verification remain mandatory. Do not install third-party design skills or scrape their proprietary material to make this work.

## Stage 6 — Multi-gate QA (mandatory)
1. **Editorial:** coherent arc, clear hook, no duplicate slides, useful CTA, claim ledger reviewed.
2. **Arabic:** spelling/hamza/grammar/register, RTL, digits, glyph joining, line breaks and Latin text.
3. **Visual:** verify actual PNG, not just source; no clipping or overlap, safe-area consistency, readable hierarchy, contrast and aligned brand bars. `audit.py` reads the measured `geometry.json` (safe area, overlaps, text over images, overflow, headline lines, smallest text); fix every geometry error by shortening copy or changing layout, then re-render. Geometry passing is necessary, not sufficient: still open every PNG.
4. **Technical:** files exist, correct dimensions, correct slide ordering/count, no broken local assets, valid HTML and reproducibility.
5. **Accessibility:** legible at phone size, no information conveyed only via color, meaningful alt text in published descriptions if images carry factual content.

Open every rendered slide and the complete contact sheet. Iterate when any blocking fault occurs. Score against the 100-point rubric in `references/qa-rubric.md`, stating each deduction and its fix. A score below 90 means revise and recheck, not claim acceptance. The scoring is a human/editorial estimate, not automated proof of quality. Automated checks are supporting evidence only.

## Stage 7 — Delivery and revisions
Provide: PNG slides (per requested format), a compact montage/contact sheet, editable HTML, deck JSON, `caption.txt` and `alt-text.txt`, the PDF when requested, and optionally a ZIP. Explain the cover/story choice in 1–2 sentences. Keep iterations and original source, and ask for specific approval only where the user workflow calls for it. Clearly separate **review draft** from **approved final**; do not publish to accounts or external sites without authorization and an appropriate connected integration.

## Reference files
- `references/editorial.md`: content strategy and fact checking
- `references/design-system.md`: detailed layout and RTL rules
- `references/qa-rubric.md`: measurable 100-point review criteria
- `references/schema.md`: input and output contract
- `references/taste-engine.md`: style directions and five design parameters
- `references/visual-directions.md`: visual direction selection
- `references/anti-patterns.md`: objective defects versus subjective warnings
- `references/critique-polish.md`: preflight → visual review → polish loop
- `BRAND.md`, `DESIGN.md`, `EDITORIAL.md`: editable project decision records
- `examples/demo.json`: runnable sample deck

## Definition of done
A carousel is done when its story stands on its own, source claims are accounted for, all images are visually reviewed, no critical text is clipped, its identity stays consistent and the editable sources accompany the images.
