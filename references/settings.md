# Settings step (before any writing or rendering)

The user sees the choices as interactive question cards (Claude Code's `AskUserQuestion` tool: up to 4 questions per card, 2–4 options each, header ≤12 characters; every question also offers "Other" for free text). Ask in Arabic. Put the recommended option first and mark it «(موصى به)».

## When to show it

| Situation | Do |
|---|---|
| `.carousel/settings.json` exists and the user wrote `--quick` | skip the cards, use the saved settings, state them in one line |
| settings exist, no `--quick` | one card, one question: «استخدم إعداداتك المحفوظة؟» with the summary from `settings.py show` → options «نعم، ابدأ (موصى به)» / «عدّل الإعدادات» |
| no saved settings | card 1 then card 2 below |
| the request already fixes a choice (e.g. «ستوري»، «بالخليجي»، «٥ شرائح») | pre-fill it and leave that question out; never ask what the user already said |
| `AskUserQuestion` is not available (claude.ai, API) | ask the same choices as one short numbered list in a single message, with defaults |

## Card 1: الإخراج

| header | question | options | multi |
|---|---|---|---|
| المقاسات | أي مقاسات تحتاج؟ | منشور 4:5 (موصى به) · مربع 1:1 · ستوري 9:16 · PDF لينكدإن | yes |
| الشرائح | كم شريحة؟ | ٧ (موصى به) · ٥ · ١٠ | no |
| اللغة | بأي أسلوب لغوي؟ | فصحى (موصى به للجهات الرسمية) · خليجي · حسب أسلوب الحساب | no |
| الطابع | أي طابع بصري؟ | تحريري (موصى به) · تعليمي · جريء · فاخر | no |

Map: منشور→portrait, مربع→square, ستوري→story, PDF→`--pdf`; فصحى→msa, خليجي→gulf, حسب الحساب→match; تحريري→editorial, تعليمي→educational, جريء→bold, فاخر→luxury (free text «تراثي» → heritage).

## Card 2: الهوية والحفظ

| header | question | options | multi |
|---|---|---|---|
| الهوية | أي هوية نستخدم؟ | one option per `brands/*.json` found (max 2, by name) · شعار جديد · هوية محايدة | no |
| الصور | هل نستخدم صورًا؟ | بدون صور (موصى به للسرعة) · صوري الخاصة · صور مولّدة بموافقتي | no |
| الحفظ | نحفظ هذه الإعدادات لمرات قادمة؟ | احفظها كافتراضية (موصى به) · لهذه المرة فقط | no |

- «شعار جديد»: ask for the logo file, then run `scripts/brand.py init` (as in `/carousel-brand`) and use the new profile.
- «صوري الخاصة»: ask for the files after the cards; «صور مولّدة»: only with the user's approval and a generation tool in this host; set `rights: generated`.

## After the cards

1. If «احفظها»: `python <skill>/scripts/settings.py set --formats … [--pdf] --slides N --register … --direction … --images … [--brand-profile …]` (run in the user's project). Otherwise keep the values for this run only.
2. Start the deck from `settings.py deck-fields` (formats, design.direction, brand_profile). Slide count and register guide the copy; `--pdf` is passed to `render.py`.
3. Confirm the choices in one line, then continue with the workflow. Do not ask again later in the same run.
