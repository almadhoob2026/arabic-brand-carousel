---
description: راجع كاروسيل موجود (ملف deck.json) وأصلح مشاكله قبل النشر
argument-hint: <path/to/deck.json>
---

Use the **arabic-brand-carousel** skill to review the deck at: $ARGUMENTS

1. Python: `<skill dir>/.venv/bin/python` (run `bash <skill dir>/scripts/setup.sh` once if missing).
2. Run `scripts/critique.py <deck> --out <deck dir>/output/critique.json`, then `scripts/render.py <deck> --out <deck dir>/output` (keep the deck's `formats`), then `scripts/audit.py <deck dir>/output --deck <deck>`.
3. Open every PNG and the contact sheet. Score with `references/qa-rubric.md`.
4. Report: blockers first (audit errors, geometry issues, contrast, unsourced numbers), then warnings, then the rubric score with one concrete fix per deduction.
5. Ask before editing the deck. After approved edits, re-render and re-audit until there are no errors.
