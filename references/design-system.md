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
hero, statement, numbered steps, compact list, comparison, metric, quote and CTA. Vary according to content; contrast and spacing matter more than novelty.

## Image treatment
Images must be provided, licensed or explicitly approved for generation; do not assume arbitrary web image usage is permitted. Each illustration should communicate a point. Avoid decorative frames if inconsistent with brand direction.

## Visual QA
Scan each output at 100%, then view montage at mobile-equivalent width. Text must not be clipped or obscured, brand bar aligned, accent consistent, source labels legible, no decorative object under headline. Contrast and readability trump stylistic flair.
