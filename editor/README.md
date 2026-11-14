# Arabic Brand Carousel — Visual Editor (beta)

A static, Arabic-first visual editor that runs entirely in your browser, with no server and no external dependencies.

## Start

Open `editor/index.html` in Chrome, Chromium, Edge, Firefox, or Safari. You can also serve the repository with `python -m http.server 8000` and navigate to `http://localhost:8000/editor/`.

## Features

- Edit brand identity (name, social handle, category, five colors, preferred local font).
- Edit headline, eyebrow, body, numbered bullet list, call-to-action, source, slide kind and decoration.
- Add, duplicate, delete and reorder 2–10 slides.
- Browse a live 4:5 preview with thumbnails.
- Import/export the deck JSON format, with client-side schema checks.
- Attach a **logo** and a **per-slide image** from your computer (PNG, JPEG, WebP or SVG) — see [Images and logo](#images-and-logo).
- Export individual 1080×1350 PNG files (or request downloads for all slides; your browser may ask permission).
- Fully offline: no network calls, third-party CDN scripts, font files or user tracking.

## Images and logo

The editor supports the same image fields as `scripts/render.py` (full spec: [`references/schema.md`](../references/schema.md#images-and-logo)): `brand.logo` and per-slide `image` = `{src, alt, layout, overlay, fit, position, credit, rights}`.

- **Attach** — use *إرفاق صورة* in the slide panel or *إرفاق شعار* under the brand fields. Files are read in the browser with `FileReader` as data URIs; nothing is uploaded. The type is detected from the file bytes, SVGs with scripts, event handlers or external references are refused, and the renderer's limits apply (10 MB per file, 40 MB per deck).
- **Layouts** — `background` (full bleed with an overlay of the brand background colour, 0–0.95), `top` (rounded image, 910×430, text below) and `side` (rounded image on the left, 400×980, text column on the right). Geometry matches the renderer's CSS; decorations are hidden on image slides. The logo is drawn next to the handle in the footer (max 220×56).
- **Validation** mirrors `load_deck`: `alt` is required (≤300 chars), `layout`, `fit` and `rights` must be one of the allowed values, `overlay` must be a number from 0 to 0.95, `credit` ≤120 chars, `position` like `center`, `top` or `50% 30%`, and unknown keys are rejected. Export buttons stay disabled until the deck is valid. Non-blocking hints flag missing `rights` and images smaller than the layout area, like `scripts/critique.py`.
- **Importing JSON with paths** (e.g. `examples/demo-images.json`) — a page opened from `file://` cannot read paths relative to the JSON, so each such image shows a *أعد إرفاق الصورة* (re-attach) placeholder on the canvas and in the panel. Re-attach the file once and every slide that used the same path is filled. PNG export asks for confirmation while placeholders remain.

### Exporting JSON

`render.py` accepts only local file paths (it rejects `data:` URIs), so there are two JSON exports. The panel lists, per image, what each one will do.

| Button | Attached images | Images imported as paths | Use with |
|---|---|---|---|
| **تصدير JSON للمحرك (render.py)** | Downloaded as separate files (`carousel-slide-01-desk.jpg`, `carousel-logo-….svg`) referenced from `carousel-deck.json` — keep them in the same folder | Original path kept (also after re-attaching a file with the same name) — save the JSON where the imported one was | `python scripts/render.py carousel-deck.json` |
| **تصدير JSON بصور مضمّنة** | Embedded as `data:` URIs | Original path kept | Re-opening in the editor later (not accepted by `render.py`) |

## Limitations

The editor is a **beta** companion and canvas-based preview. Its rendering can differ from the Python/Chromium production renderer. It does not produce ZIP files or post to Instagram. For publication-critical typography, use `python scripts/render.py deck.json` and visually inspect the resulting images. It does not automatically verify factual content or copyright permissions. The v4 layout fields (`metric`, `compare`, `quote`, `timeline`, `cards`, `answer`, and kinds such as `checklist` or `before-after`) and `brand.font_file` are accepted on import and exported unchanged, but the canvas preview does not draw those layouts yet; it shows the headline, body and other v3 fields only. Render with `scripts/render.py` to see them. The editor does not compute image-vs-text contrast; run `python scripts/critique.py` on the exported deck for that check.

## Arabic support

Uses Canvas's RTL direction and available locally installed Arabic fonts. To use Cairo, install the font on your system; it is not bundled in this repository.

## v3 Design Intelligence

The right-hand brand editor now includes five design sliders and visual direction presets. These are stored in the deck's optional `design` JSON object. Export the JSON and run `python scripts/critique.py <deck.json>` for explainable preflight findings. The browser preview approximates the Chromium renderer; verify final PNGs with `scripts/render.py` and `scripts/audit.py`.
