# Arabic Brand Carousel — Visual Editor (beta)

A static, Arabic-first visual editor that runs entirely in your browser, with no server and no external dependencies.

## Start

Open `editor/index.html` in Chrome, Chromium, Edge, Firefox, or Safari. You can also serve the repository with `python -m http.server 8000` and navigate to `http://localhost:8000/editor/`.

## Features

- Edit brand identity (name, social handle, category, five colors, preferred local font).
- Edit headline, eyebrow, body, numbered bullet list, call-to-action, source, slide kind and decoration.
- Add, duplicate, delete and reorder 2–10 slides.
- Browse a live 4:5 preview with thumbnails.
- Import/export the existing v2 deck JSON format, with client-side schema checks.
- Export individual 1080×1350 PNG files (or request downloads for all slides; your browser may ask permission).
- Fully offline: no network calls, third-party CDN scripts, font files or user tracking.

## Limitations

The editor is a **beta** companion and canvas-based preview. Its rendering can differ from the Python/Chromium production renderer. It does not produce ZIP files or post to Instagram. For publication-critical typography, use `python scripts/render.py deck.json` and visually inspect the resulting images. It does not automatically verify factual content or copyright permissions.

## Arabic support

Uses Canvas's RTL direction and available locally installed Arabic fonts. To use Cairo, install the font on your system; it is not bundled in this repository.
