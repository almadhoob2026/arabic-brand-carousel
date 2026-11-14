# Arabic Brand Carousel 🇧🇭

**A production-oriented AI skill and open-source RTL carousel renderer for Arabic Instagram posts.**

[العربية](#بالعربية) · [English](#english) · [Quick start](#quick-start)

## بالعربية

مهارة محسّنة تساعد مساعد الذكاء الاصطناعي على تحويل موضوع واحد إلى كاروسيل عربي بهوية متسقة: تحليل، كتابة تحريرية، بناء قصة، توثيق الادعاءات، تصميم، إخراج صور PNG، وفحص جودة قبل التسليم.

**المزايا**
- تعليمات `SKILL.md` مستقلة وقابلة للاستخدام في بيئات المساعدات التي تدعم المهارات.
- خط سير إنتاج كامل من الفكرة إلى الصور، مع ضبط عربي RTL فعلي.
- محرّك HTML/Chromium محلي لإخراج شرائح 1080×1350.
- ملف JSON قابل للتعديل، HTML مستقل، PNG لكل شريحة، صورة معاينة مجمعة، وملف ZIP.
- **محرر مرئي تجريبي يعمل داخل المتصفح**: تعديل العلامة والشرائح، إضافة/نسخ/ترتيب، معاينة وتصدير PNG/JSON دون خادم. [جرّب المحرر](editor/index.html) (حمّل الملف وافتحه محليًا).
- اختبارات مبدئية للتحقق من المحتوى والمقاس والحدود، ومقياس جودة تحريري من 100 نقطة.
- لا يحتاج إلى اتصال خارجي وقت الإخراج، ولا يأتي مع خطوط أو صور محمية.

### طريقة استخدام المهارة
انسخ `SKILL.md` والمجلد `references/` إلى موقع المهارات لدى مساعدك أو ارفع المستودع كمرجع. اطلب: «صمم كاروسيل عربي عن ... لعلامتي التجارية ...». تختلف طريقة تثبيت المهارات باختلاف التطبيق، وهذا المستودع لا يدّعي توافقًا آليًا مع جميع المنتجات.

## English

This repository combines a detailed reusable **Arabic carousel skill**, a browser-based visual editor (beta), and a minimal deterministic renderer. It focuses on editorial strategy, brand consistency, RTL typesetting, evidence handling and human-in-the-loop QA. It is an example implementation, **not** an Instagram publishing integration or a general-purpose design editor.

## Visual editor (beta)

Open [`editor/index.html`](editor/index.html) in a modern browser; it supports offline editing and PNG/JSON exports. See [`editor/README.md`](editor/README.md) for the features and limitations. The Canvas preview is **not pixel-identical** to the production Chromium renderer.

## Quick start

Requires Python 3.10+, Chromium (or another Playwright-managed Chromium executable), and a local Arabic-compatible font. No font files are bundled.

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python scripts/render.py examples/demo.json --out output/demo
python scripts/audit.py output/demo --deck examples/demo.json
python -m unittest discover -s tests -v
```

If your system already has Chromium, the renderer attempts to locate it (or use `CHROME_PATH=/path/to/chromium`). Playwright's browser installation is not needed in that case.

Generated structure:

```text
output/demo/
  carousel.html           # editable self-contained design
  slide-01.png ...        # production-sized individual images
  contact-sheet.png       # combined preview
  carousel.zip            # images + source + deck
  deck.json               # copy of input
  audit.json              # programmatic checks (after audit)
```

The skill's editorial and visual acceptance criteria require human inspection. Passing a script check is **not** approval of the layout.

## Deck contract

See [`references/schema.md`](references/schema.md) and [`examples/demo.json`](examples/demo.json). The sample uses abstract decorative shapes and simulated educational content; it does not claim real-world data.

## Project structure

```text
SKILL.md
editor/index.html
editor/README.md
README.md
LICENSE
requirements.txt
scripts/render.py
scripts/audit.py
references/{editorial,design-system,qa-rubric,schema}.md
examples/demo.json
tests/test_deck.py
.github/workflows/ci.yml
```

## Security & privacy

Renderer escapes all text, does not fetch remote URLs, disallows remote asset references and keeps content on your machine. Only add images/fonts you own or have permission to use. Verify any substantive claims separately; automatic visual checks cannot validate sources.

## Contributing

Issues, Arabic wording improvements, tests for bidi edge cases and pull requests are welcome. Please include a minimal reproducible deck for rendering bugs.

## License

MIT — see [LICENSE](LICENSE). Third-party assets and fonts are **not** covered by this license.
