# مهارة الكاروسيل العربي للعلامات التجارية — الإصدار 3.0

مشروع مفتوح المصدر لإنشاء كاروسيل عربي من موضوع واحد، مع منهج تحرير وتصميم احترافي، ومحرّك محلي لإخراج HTML وPNG بمقاس 1080×1350، وفحوصات تقنية ومراجعة بصرية بشرية.

## مكونات المشروع
- `SKILL.md`: تعليمات وكيل الذكاء الاصطناعي، من تحليل الموضوع إلى مراجعة الجودة.
- `references/`: دليل التحرير، قواعد التصميم العربي، نموذج JSON، وتقييم الجودة.
- `scripts/render.py`: يحوّل ملف JSON إلى HTML وصور PNG وصورة معاينة وZIP.
- `scripts/audit.py`: يتحقق من المقاسات والعدد والملفات ويصدر `audit.json`.
- `scripts/critique.py` و`scripts/taste.py`: فحص مبدئي وتوجهات التصميم (الإصدار 3).
- `examples/demo.json`: مثال عربي من سبع شرائح.
- `tests/`: اختبارات صحة البيانات وأمان إدراج النصوص.

## طريقة التثبيت

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

## التشغيل
```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python scripts/render.py examples/demo.json --out output/demo
python scripts/audit.py output/demo --deck examples/demo.json
python -m unittest discover -s tests -v
```

إذا كان Chromium موجودًا على النظام فسيستخدمه البرنامج تلقائيًا، ويمكن تحديد مساره بمتغير البيئة `CHROME_PATH`. قد تحتاج إلى تثبيت خط عربي مناسب محليًا؛ لا يتضمن المشروع ملفات خطوط.

## حدود النظام
الفحص البرمجي لا يثبت صحة الادعاءات أو سلامة توزيع النصوص بصريًا؛ لذا يُلزم ملف المهارة بمراجعة بشرية لكل صورة. هذا المستودع لا ينشر المحتوى تلقائيًا على إنستغرام ولا يستخدم أي بيانات حسابات شخصية.

التفاصيل بالإنجليزية في [`README.md`](README.md). الترخيص MIT للمحتوى البرمجي الأصلي، دون حقوق الخطوط أو العلامات أو الصور الخارجية.

## المحرر المرئي (تجريبي)

يمكن فتح [`editor/index.html`](editor/index.html) محليًا في المتصفح لتعديل ألوان الهوية، والعناوين، والنصوص، وترتيب الشرائح، واستيراد ملف JSON أو تصديره، وتنزيل صور PNG بدقة 1080×1350. يعمل دون إنترنت أو رفع المحتوى إلى خادم. المعاينة تختلف قليلًا عن محرك التصيير الإنتاجي؛ للمراجعة النهائية شغّل `python scripts/render.py` ثم افحص الصور بصريًا. التفاصيل في [`editor/README.md`](editor/README.md).
