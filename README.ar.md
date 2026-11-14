# مهارة الكاروسيل العربي للعلامات التجارية — الإصدار 5.0

مشروع مفتوح المصدر لإنشاء كاروسيل عربي من موضوع واحد، مع منهج تحرير وتصميم احترافي، ومحرّك محلي لإخراج HTML وPNG بمقاس 1080×1350، وفحوصات تقنية ومراجعة بصرية بشرية.

## مكونات المشروع
- `SKILL.md`: تعليمات وكيل الذكاء الاصطناعي، من تحليل الموضوع إلى مراجعة الجودة.
- `references/`: دليل التحرير، قواعد التصميم العربي، نموذج JSON، وتقييم الجودة.
- `scripts/render.py`: يحوّل ملف JSON إلى HTML وصور PNG وصورة معاينة وZIP.
- `scripts/audit.py`: يتحقق من المقاسات والعدد والملفات ويصدر `audit.json`.
- `scripts/critique.py` و`scripts/taste.py`: فحص مبدئي وتوجهات التصميم (الإصدار 3).
- `examples/demo.json`: مثال عربي من سبع شرائح (نصي).
- `scripts/layouts.py`: التخطيطات الاثنا عشر (رقم كبير، مقارنة، قبل وبعد، اقتباس، خط زمني، قائمة تحقق، بطاقات، سؤال وجواب…) مع اختيار التخطيط تلقائيًا من المحتوى.
- `examples/demo-layouts.json`: شريحة لكل تخطيط جديد.
- `scripts/formats.py` و`scripts/publish.py` و`scripts/brand.py`: المقاسات الثلاثة، وحزمة النشر، وملفات الهوية مع استخراج الألوان من الشعار.
- `examples/demo-profile.json`: مثال يستخدم ملف هوية مشتركًا ومقاسين وحزمة نشر.
- `examples/demo-images.json`: مثال بالصور والشعار يستخدم التخطيطات الثلاثة (`background` و`top` و`side`). الصور في `examples/assets/` مولّدة برمجيًا ومسموح استخدامها.
- `tests/`: اختبارات صحة البيانات وأمان إدراج النصوص.

## طريقة التثبيت

**Claude Code كإضافة (Plugin) — الأسهل:**
```bash
claude plugin marketplace add almadhoob2026/arabic-brand-carousel
claude plugin install arabic-brand-carousel@almadhoob2026
```
أعد تشغيل Claude Code. عند أول استخدام تُثبَّت المتطلبات تلقائيًا عبر `scripts/setup.sh`. الأوامر المتاحة:
- `/carousel <الموضوع>`: كاروسيل كامل من موضوع أو خبر أو رابط.
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

## التشغيل
```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python scripts/render.py examples/demo.json --out output/demo
python scripts/render.py examples/demo-images.json --out output/demo-images  # مع صور وشعار
python scripts/render.py examples/demo-layouts.json --out output/demo-layouts --formats portrait,square,story --pdf
python scripts/render.py examples/demo-profile.json --out output/demo-profile   # ملف هوية + حزمة نشر
python scripts/audit.py output/demo --deck examples/demo.json
python -m unittest discover -s tests -v
```

إذا كان Chromium موجودًا على النظام فسيستخدمه البرنامج تلقائيًا، ويمكن تحديد مساره بمتغير البيئة `CHROME_PATH`. خط Cairo مرفق في مجلد `fonts/` برخصة SIL OFL ويُضمَّن تلقائيًا، ويمكن استخدام خط العلامة عبر `brand.font_file`.

## حدود النظام
الفحص البرمجي لا يثبت صحة الادعاءات أو سلامة توزيع النصوص بصريًا؛ لذا يُلزم ملف المهارة بمراجعة بشرية لكل صورة. هذا المستودع لا ينشر المحتوى تلقائيًا على إنستغرام ولا يستخدم أي بيانات حسابات شخصية.

التفاصيل بالإنجليزية في [`README.md`](README.md). الترخيص MIT للمحتوى البرمجي الأصلي، دون حقوق العلامات أو الصور الخارجية. خط Cairo المرفق مرخّص بشكل مستقل برخصة SIL OFL 1.1 (`fonts/OFL.txt`).

## المحرر المرئي (تجريبي)

يمكن فتح [`editor/index.html`](editor/index.html) محليًا في المتصفح لتعديل ألوان الهوية، والعناوين، والنصوص، وترتيب الشرائح، واستيراد ملف JSON أو تصديره، وتنزيل صور PNG بدقة 1080×1350. يعمل دون إنترنت أو رفع المحتوى إلى خادم. المعاينة تختلف قليلًا عن محرك التصيير الإنتاجي؛ للمراجعة النهائية شغّل `python scripts/render.py` ثم افحص الصور بصريًا. التفاصيل في [`editor/README.md`](editor/README.md).
