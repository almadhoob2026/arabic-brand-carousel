---
description: صمّم كاروسيل عربي بهوية علامتك من موضوع أو خبر أو رابط (مع صفحة إعدادات قبل التنفيذ)
argument-hint: <الموضوع أو النص أو الرابط> [--quick]
---

Use the **arabic-brand-carousel** skill for this request: $ARGUMENTS

1. Python: use `<skill dir>/.venv/bin/python` (the skill's base directory is shown when it loads). If it does not exist, run `bash <skill dir>/scripts/setup.sh` once.
2. **Settings first, before writing or rendering anything.** Run `<python> <skill dir>/scripts/settings.py show` in the current project, then follow `<skill dir>/references/settings.md` exactly: show the settings as `AskUserQuestion` cards (or a single "use saved settings?" card when settings exist), skip the cards only when the request contains `--quick` and settings are saved, and never ask about anything the request already states. Save with `settings.py set` when the user chooses to.
3. Start the deck from `settings.py deck-fields`, then follow the skill's workflow from intake to QA. Write the deck to `carousels/<slug>/deck.json` and render into `carousels/<slug>/output/` with the chosen formats (and `--pdf` when chosen).
4. Always include a `publish` block (caption, hashtags) and an `alt` for any slide whose meaning is visual.
5. Run critique, render and audit; fix every audit error; open every PNG before reporting. Never publish to any account.
