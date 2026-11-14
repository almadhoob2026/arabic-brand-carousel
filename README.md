# Arabic Brand Carousel 🇧🇭

**A production-oriented AI skill and open-source RTL carousel renderer for Arabic Instagram posts.**

[العربية](#بالعربية) · [English](#english) · [Installation](#installation) · [Quick start](#quick-start)

## بالعربية

مهارة محسّنة تساعد مساعد الذكاء الاصطناعي على تحويل موضوع واحد إلى كاروسيل عربي بهوية متسقة: تحليل، كتابة تحريرية، بناء قصة، توثيق الادعاءات، تصميم، إخراج صور PNG، وفحص جودة قبل التسليم.

**المزايا**
- تعليمات `SKILL.md` مستقلة وقابلة للاستخدام في بيئات المساعدات التي تدعم المهارات.
- خط سير إنتاج كامل من الفكرة إلى الصور، مع ضبط عربي RTL فعلي.
- محرّك HTML/Chromium محلي يُخرج الشرائح بمقاسات المنشور والمربع والستوري، مع PDF.
- **دعم الصور والشعار**: صورة خلفية كاملة مع طبقة تعتيم، أو صورة أعلى الشريحة، أو صورة جانبية، وشعار بجانب الحساب. الصور ملفات محلية تُضمَّن داخل الملف، مع فحص التباين والدقة وحقوق الاستخدام.
- ملف JSON قابل للتعديل، HTML مستقل، PNG لكل شريحة، صورة معاينة مجمعة، وملف ZIP.
- **محرر مرئي تجريبي يعمل داخل المتصفح**: تعديل العلامة والشرائح، إضافة/نسخ/ترتيب، معاينة وتصدير PNG/JSON دون خادم. [جرّب المحرر](editor/index.html) (حمّل الملف وافتحه محليًا).
- **صفحة إعدادات قبل التنفيذ**: بطاقات اختيار للمقاسات وعدد الشرائح واللغة والطابع والهوية والصور، تُحفظ كإعدادات افتراضية للمشروع.
- اختبارات آلية (منها إخراج حقيقي في المتصفح)، ومقياس جودة تحريري من 100 نقطة.
- **12 تخطيطًا فعليًا** (الإصدار 4): رقم كبير، مقارنة، قبل وبعد، اقتباس، خط زمني، قائمة تحقق، بطاقات، سؤال وجواب، إلى جانب الغلاف والنص والخطوات والدعوة. يُختار التخطيط تلقائيًا من نوع المحتوى.
- **خط Cairo مرفق** (رخصة SIL OFL) ويُضمَّن في الملف، مع دعم ملف خط العلامة التجارية.
- **ثلاثة مقاسات من ملف واحد**: منشور 1080×1350، مربع 1080×1080، ستوري 1080×1920 مع مناطق آمنة لواجهة انستقرام، وملف **PDF للينكدإن** بنص حقيقي قابل للبحث.
- **حزمة نشر**: كابشن وهاشتاقات ووصف بديل لكل شريحة في ملفات جاهزة للصق.
- **ملف هوية قابل لإعادة الاستخدام** (`brand_profile`) مع استخراج الألوان من الشعار وفحص التباين.
- **إضافة لـ Claude Code** بثلاثة أوامر: `/carousel` و`/carousel-review` و`/carousel-brand`.
- **فحص هندسي فعلي** من المتصفح: الهوامش الآمنة، تداخل النصوص، النص فوق الصور، تجاوز المساحة، عدد أسطر العنوان، وأصغر خط.
- لا يحتاج إلى اتصال خارجي وقت الإخراج، ولا يأتي مع صور محمية.

### طريقة التثبيت

**Claude Code كإضافة (Plugin) — الأسهل:**
```bash
claude plugin marketplace add almadhoob2026/arabic-brand-carousel
claude plugin install arabic-brand-carousel@almadhoob2026
```
أعد تشغيل Claude Code. عند أول استخدام تُثبَّت المتطلبات تلقائيًا عبر `scripts/setup.sh`. الأوامر المتاحة:
- `/carousel <الموضوع>`: كاروسيل كامل من موضوع أو خبر أو رابط، يبدأ ببطاقات الإعدادات (أضف `--quick` لاستخدام الإعدادات المحفوظة مباشرة).
- `/carousel-settings`: ضبط الإعدادات الافتراضية للمشروع.
- `/carousel-review <deck.json>`: مراجعة كاروسيل موجود وإصلاحه قبل النشر.
- `/carousel-brand <الشعار> <الاسم>`: ملف هوية قابل لإعادة الاستخدام من شعارك.

**Claude Code بالنسخ المباشر (بديل):**
```bash
git clone https://github.com/almadhoob2026/arabic-brand-carousel.git ~/.claude/skills/arabic-brand-carousel
bash ~/.claude/skills/arabic-brand-carousel/scripts/setup.sh
```
يعمل المجلد كإضافة تلقائيًا بنفس الأوامر. استخدم طريقة واحدة فقط من الطريقتين حتى لا تظهر المهارة مرتين.

**تطبيق Claude (الويب/سطح المكتب):** حمّل المستودع كملف ZIP بحيث يكون `SKILL.md` داخل مجلد `arabic-brand-carousel/`، ثم من *Settings → Capabilities → Skills* اختر *Upload skill*. في هذه البيئة قد لا يتوفر Chromium، فتعمل المهارة على التحرير والتصميم وتسلّم ملف JSON/HTML قابلًا للإخراج محليًا.

**التحديث:** `claude plugin update arabic-brand-carousel@almadhoob2026` للإضافة، أو `git -C ~/.claude/skills/arabic-brand-carousel pull` للنسخ المباشر.

## English

This repository combines a detailed reusable **Arabic carousel skill**, a browser-based visual editor (beta), and a minimal deterministic renderer. It focuses on editorial strategy, brand consistency, RTL typesetting, evidence handling and human-in-the-loop QA. It is an example implementation, **not** an Instagram publishing integration or a general-purpose design editor.

## Installation

### Claude Code plugin (recommended)
```bash
claude plugin marketplace add almadhoob2026/arabic-brand-carousel
claude plugin install arabic-brand-carousel@almadhoob2026
```
Restart Claude Code. Dependencies are installed on first use by `scripts/setup.sh` (into `.venv` inside the plugin). Commands:

| Command | Does |
|---|---|
| `/carousel <topic, text or link> [--quick]` | settings cards → brief → copy → layouts → render → audit |
| `/carousel-settings [show\|clear]` | set this project's defaults (`.carousel/settings.json`) |
| `/carousel-review <deck.json>` | critique + render + audit + rubric, fixes after approval |
| `/carousel-brand <logo> <name>` | reusable brand profile from a logo, with contrast report |

Update with `claude plugin update arabic-brand-carousel@almadhoob2026`.

### Claude Code by cloning (alternative)
```bash
git clone https://github.com/almadhoob2026/arabic-brand-carousel.git ~/.claude/skills/arabic-brand-carousel
bash ~/.claude/skills/arabic-brand-carousel/scripts/setup.sh
```
The folder loads as a skills-dir plugin with the same commands. Update with `git -C ~/.claude/skills/arabic-brand-carousel pull`. Use one method, not both, or the skill appears twice.

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
python scripts/render.py examples/demo-layouts.json --out output/demo-layouts --formats portrait,square,story --pdf
python scripts/render.py examples/demo-profile.json --out output/demo-profile   # brand profile + publish pack
python scripts/brand.py init --logo examples/assets/logo.svg --name "علامتي" --out brands/mine.json
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
  carousel.pdf            # with --pdf: vector PDF (LinkedIn document post)
  caption.txt             # caption + hashtags, ready to paste
  alt-text.txt            # alt text per slide
  publish.json            # the publishing pack as data
  render.json             # formats produced by this run (audit checks exactly these)
  square/  story/         # with --formats: same files per extra format
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
scripts/formats.py            # portrait / square / story sizes and safe areas
scripts/publish.py            # caption, hashtags, alt text
scripts/brand.py              # brand profiles + palette from logo (CLI: init)
scripts/setup.sh              # one-time .venv + dependencies
scripts/settings.py           # project defaults chosen in the settings step
scripts/eval_triggers.py      # trigger eval runner (uses the claude CLI)
.claude-plugin/               # plugin.json + marketplace.json
commands/                     # /carousel, /carousel-review, /carousel-brand
evals/triggers.json           # should / should-not trigger prompts
fonts/                        # Cairo variable font + OFL licence
editor/index.html             # offline visual editor (beta)
examples/demo.json            # text-only sample
examples/demo-images.json     # photos + logo sample (assets/ are generated, rights-free)
examples/demo-layouts.json    # one slide per v4 layout
examples/demo-profile.json    # brand_profile + formats + publish pack
examples/brands/sample.json   # sample profile made with scripts/brand.py
tests/
.github/workflows/ci.yml
```

## Security & privacy

Renderer escapes all text, does not fetch remote URLs, disallows remote asset references and keeps content on your machine. Only add images/fonts you own or have permission to use. Verify any substantive claims separately; automatic visual checks cannot validate sources.

## Contributing

Issues, Arabic wording improvements, tests for bidi edge cases and pull requests are welcome. Please include a minimal reproducible deck for rendering bugs.

## License

MIT — see [LICENSE](LICENSE). Third-party assets are **not** covered by this license. The bundled Cairo font in `fonts/` is © The Cairo Project Authors and licensed separately under the SIL Open Font License 1.1 (`fonts/OFL.txt`).
