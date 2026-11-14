# Arabic Brand Carousel 🇧🇭

**A production-oriented AI skill and open-source RTL carousel renderer for Arabic Instagram posts.**

[العربية](#بالعربية) · [English](#english) · [Installation](#installation) · [Quick start](#quick-start)

## بالعربية

مهارة محسّنة تساعد مساعد الذكاء الاصطناعي على تحويل موضوع واحد إلى كاروسيل عربي بهوية متسقة: تحليل، كتابة تحريرية، بناء قصة، توثيق الادعاءات، تصميم، إخراج صور PNG، وفحص جودة قبل التسليم.

**المزايا**
- تعليمات `SKILL.md` مستقلة وقابلة للاستخدام في بيئات المساعدات التي تدعم المهارات.
- خط سير إنتاج كامل من الفكرة إلى الصور، مع ضبط عربي RTL فعلي.
- محرّك HTML/Chromium محلي لإخراج شرائح 1080×1350.
- **دعم الصور والشعار**: صورة خلفية كاملة مع طبقة تعتيم، أو صورة أعلى الشريحة، أو صورة جانبية، وشعار بجانب الحساب. الصور ملفات محلية تُضمَّن داخل الملف، مع فحص التباين والدقة وحقوق الاستخدام.
- ملف JSON قابل للتعديل، HTML مستقل، PNG لكل شريحة، صورة معاينة مجمعة، وملف ZIP.
- **محرر مرئي تجريبي يعمل داخل المتصفح**: تعديل العلامة والشرائح، إضافة/نسخ/ترتيب، معاينة وتصدير PNG/JSON دون خادم. [جرّب المحرر](editor/index.html) (حمّل الملف وافتحه محليًا).
- اختبارات مبدئية للتحقق من المحتوى والمقاس والحدود، ومقياس جودة تحريري من 100 نقطة.
- **12 تخطيطًا فعليًا** (الإصدار 4): رقم كبير، مقارنة، قبل وبعد، اقتباس، خط زمني، قائمة تحقق، بطاقات، سؤال وجواب، إلى جانب الغلاف والنص والخطوات والدعوة. يُختار التخطيط تلقائيًا من نوع المحتوى.
- **خط Cairo مرفق** (رخصة SIL OFL) ويُضمَّن في الملف، مع دعم ملف خط العلامة التجارية.
- **فحص هندسي فعلي** من المتصفح: الهوامش الآمنة، تداخل النصوص، النص فوق الصور، تجاوز المساحة، عدد أسطر العنوان، وأصغر خط.
- لا يحتاج إلى اتصال خارجي وقت الإخراج، ولا يأتي مع صور محمية.

### طريقة التثبيت

**Claude Code (على جهازك — الخيار الموصى به):**
```bash
git clone https://github.com/almadhoob2026/arabic-brand-carousel.git ~/.claude/skills/arabic-brand-carousel
cd ~/.claude/skills/arabic-brand-carousel
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium   # غير ضروري إذا كان Chrome مثبتًا
```
أعد تشغيل Claude Code، ثم اكتب `/arabic-brand-carousel` أو اطلب: «سوي لي كاروسيل عن ...». وللتثبيت داخل مشروع واحد فقط استخدم `.claude/skills/arabic-brand-carousel` بدل `~/.claude/skills/`.

**تطبيق Claude (الويب/سطح المكتب):** حمّل المستودع كملف ZIP بحيث يكون `SKILL.md` داخل مجلد `arabic-brand-carousel/`، ثم من *Settings → Capabilities → Skills* اختر *Upload skill*. في هذه البيئة قد لا يتوفر Chromium، فتعمل المهارة على التحرير والتصميم وتسلّم ملف JSON/HTML قابلًا للإخراج محليًا.

**التحديث:** `git -C ~/.claude/skills/arabic-brand-carousel pull`

## English

This repository combines a detailed reusable **Arabic carousel skill**, a browser-based visual editor (beta), and a minimal deterministic renderer. It focuses on editorial strategy, brand consistency, RTL typesetting, evidence handling and human-in-the-loop QA. It is an example implementation, **not** an Instagram publishing integration or a general-purpose design editor.

## Installation

### Claude Code (recommended)
```bash
git clone https://github.com/almadhoob2026/arabic-brand-carousel.git ~/.claude/skills/arabic-brand-carousel
cd ~/.claude/skills/arabic-brand-carousel
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium   # skip if Chrome/Chromium is installed
```
Restart Claude Code, then run `/arabic-brand-carousel` or just ask for an Arabic carousel. For a single project, clone into `<project>/.claude/skills/arabic-brand-carousel` instead. Update with `git -C ~/.claude/skills/arabic-brand-carousel pull`.

### Claude apps (web / desktop)
Zip the repository so that `SKILL.md` sits inside an `arabic-brand-carousel/` folder, then upload it under *Settings → Capabilities → Skills*. Chromium may be unavailable in that sandbox; the skill then delivers the deck JSON/HTML for local rendering.

### Browser detection
The renderer uses `CHROME_PATH` if set, otherwise `chromium`/`google-chrome` on `PATH`, then the standard macOS Chrome/Chromium/Edge locations, and finally Playwright's bundled Chromium.

## Visual editor (beta)

Open [`editor/index.html`](editor/index.html) in a modern browser; it supports offline editing and PNG/JSON exports. See [`editor/README.md`](editor/README.md) for the features and limitations. The Canvas preview is **not pixel-identical** to the production Chromium renderer.

## Quick start

Requires Python 3.10+ and Chromium (or another Playwright-managed Chromium executable). The Cairo font is bundled under the SIL Open Font License (`fonts/OFL.txt`).

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python scripts/render.py examples/demo.json --out output/demo
python scripts/render.py examples/demo-images.json --out output/demo-images  # photos + logo
python scripts/render.py examples/demo-layouts.json --out output/demo-layouts  # all 12 layouts
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
  geometry.json           # measured layout checks per slide
  audit.json              # programmatic checks (after audit)
```

The skill's editorial and visual acceptance criteria require human inspection. Passing a script check is **not** approval of the layout.

## Deck contract

See [`references/schema.md`](references/schema.md), [`examples/demo.json`](examples/demo.json) and [`examples/demo-images.json`](examples/demo-images.json) (local photos and a logo). The sample uses abstract decorative shapes and simulated educational content; it does not claim real-world data.

## Project structure

```text
SKILL.md                      # skill entry point (name + description frontmatter)
BRAND.md DESIGN.md EDITORIAL.md   # per-project decision templates
references/                   # editorial, design-system, qa-rubric, schema,
                              # taste-engine, visual-directions, anti-patterns, critique-polish
scripts/render.py             # JSON → HTML + PNG + contact sheet + ZIP
scripts/audit.py              # technical output checks
scripts/critique.py           # preflight critique (v3)
scripts/taste.py              # design direction + sliders (v3)
scripts/assets.py             # local image/logo loading and checks
scripts/layouts.py            # 12 layout families: validation, inference, HTML/CSS
fonts/                        # Cairo variable font + OFL licence
editor/index.html             # offline visual editor (beta)
examples/demo.json            # text-only sample
examples/demo-images.json     # photos + logo sample (assets/ are generated, rights-free)
examples/demo-layouts.json    # one slide per v4 layout
tests/
.github/workflows/ci.yml
```

## Security & privacy

Renderer escapes all text, does not fetch remote URLs, disallows remote asset references and keeps content on your machine. Only add images/fonts you own or have permission to use. Verify any substantive claims separately; automatic visual checks cannot validate sources.

## Contributing

Issues, Arabic wording improvements, tests for bidi edge cases and pull requests are welcome. Please include a minimal reproducible deck for rendering bugs.

## License

MIT — see [LICENSE](LICENSE). Third-party assets are **not** covered by this license. The bundled Cairo font in `fonts/` is © The Cairo Project Authors and licensed separately under the SIL Open Font License 1.1 (`fonts/OFL.txt`).
