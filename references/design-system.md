# Design system and Arabic typography

## Tokens and canvas
Portrait 1080×1350 px. Safe outer space min 80 px. Text area inside top chrome ~210 px and above footer ~160 px. Neutral palette by default: background #111418, foreground #F7F5F1, muted #B5BDC8, surface #232A33, accent #F3C969. Always prefer actual brand tokens when supplied.

## Mobile-first hierarchy
Headline approx 76–124px (dependent on copy length). Supporting 38–52px. Metadata 26–36px. Cover should read in 2 seconds. Headlines ideally 2–4 lines. Avoid using font size reduction as first resort; simplify copy or alter layout. Keep leading and word spacing comfortable for Arabic glyph forms.

## Arabic-specific checklist
- Ensure `lang="ar"`, `dir="rtl"` on document and RTL text containers.
- Isolate mixed Latin snippets with `<bdi dir="ltr">` or explicit spans when needed.
- Check joining forms, diacritics, tatweel, punctuation, digit styles, and stray English ordering.
- Manual line breaks should respect grammatical units; do not isolate prepositions.
- Do not use a western display font without Arabic glyph coverage.

## Layout families
The renderer implements 12 layouts (see `schema.md`): cover, statement, steps/list, checklist, metric, comparison, before-after, quote, timeline, grid, Q&A and CTA. Choose the layout from the *shape of the content*, not for novelty: a number → metric; two options → comparison; a change → before-after; a sequence → timeline or steps; parallel ideas → grid; a common question → Q&A. Write the content into the matching field and let the layout follow. Avoid the same interior layout three times in a row (critique flags it).

## Image treatment
Images must be provided, licensed or explicitly approved for generation; do not assume arbitrary web image usage is permitted. Each illustration should communicate a point. Avoid decorative frames if inconsistent with brand direction.

Renderer layouts (see `schema.md`): `background` for covers and emotional statements (raise `overlay` until critique shows no contrast blocker), `top` for an object or scene that the headline explains, `side` for a diagram/product next to steps or a list. Use at most one image per slide and vary layouts across the deck. Use `fit: "contain"` for diagrams, charts, screenshots and logos-as-content so nothing meaningful is cropped; `cover` suits photos. Crop with `position` so faces and key details avoid the text area. Always set a meaningful Arabic `alt` and the `rights` status.

## Visual QA
Scan each output at 100%, then view montage at mobile-equivalent width. Text must not be clipped or obscured, brand bar aligned, accent consistent, source labels legible, no decorative object under headline. Contrast and readability trump stylistic flair.
