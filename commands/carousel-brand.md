---
description: أنشئ ملف هوية قابل لإعادة الاستخدام من شعار علامتك
argument-hint: <path/to/logo> <اسم العلامة> [@handle] [dark|light]
---

Use the **arabic-brand-carousel** skill to create a reusable brand profile from: $ARGUMENTS

1. Python: `<skill dir>/.venv/bin/python` (run `bash <skill dir>/scripts/setup.sh` once if missing).
2. Run `scripts/brand.py init --logo <logo> --name <name> [--handle <handle>] [--theme dark|light] --out brands/<slug>.json` in the current project.
3. Show the user the palette and the contrast report. The palette is derived from the logo, not the official brand guide: ask the user to confirm or supply exact brand colours, and edit the profile accordingly.
4. Explain that new decks can use it with `"brand_profile": "brands/<slug>.json"`, and that profile hashtags become the default publish hashtags.
