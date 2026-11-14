---
description: اضبط إعدادات الكاروسيل الافتراضية لهذا المشروع (المقاسات، الشرائح، اللغة، الطابع، الهوية)
argument-hint: [show | clear]
---

Use the **arabic-brand-carousel** skill to manage this project's carousel defaults. Request: $ARGUMENTS

1. Python: `<skill dir>/.venv/bin/python` (run `bash <skill dir>/scripts/setup.sh` once if missing).
2. `show`: run `<python> <skill dir>/scripts/settings.py show` and report the summary line. `clear`: run `settings.py clear` and confirm.
3. Otherwise show both settings cards from `<skill dir>/references/settings.md` as `AskUserQuestion` cards, with the currently saved values as the first (recommended) option of each question. Then save with `settings.py set …` (always save; this command exists to save) and report the new summary.
4. Do not create a carousel here. Tell the user `/carousel <topic> --quick` now uses these settings without asking.
