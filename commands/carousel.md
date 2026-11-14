---
description: صمّم كاروسيل عربي بهوية علامتك من موضوع أو خبر أو رابط
argument-hint: <الموضوع أو النص أو الرابط> [square|story|pdf]
---

Use the **arabic-brand-carousel** skill for this request: $ARGUMENTS

1. Follow the skill's workflow from intake to QA. Read the skill's `SKILL.md` first; its directory is the skill base directory shown when it loads.
2. Python: use `<skill dir>/.venv/bin/python`. If it does not exist, run `bash <skill dir>/scripts/setup.sh` once.
3. If a `brands/*.json` profile exists in the current project, reference it with `brand_profile` instead of repeating brand values. If the user gives a logo but no palette, offer `scripts/brand.py init`.
4. Write the deck JSON into the current project (e.g. `carousels/<slug>/deck.json`) and render into `carousels/<slug>/output/`. Add `--formats` and `--pdf` when the user mentions stories, square posts, LinkedIn or PDF.
5. Always include a `publish` block (caption, hashtags) and an `alt` for any slide whose meaning is visual.
6. Run critique, render and audit; fix every audit error; open every PNG before reporting. Never publish to any account.
