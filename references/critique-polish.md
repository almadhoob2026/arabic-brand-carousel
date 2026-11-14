# Critique → Polish loop

1. **Brief**: verify purpose, brand permissions and claims.
2. **Draft**: author a minimal coherent story, not filler.
3. **Preflight**: `python scripts/critique.py path/to/deck.json --out output/critique.json`.
4. **Render**: `python scripts/render.py path/to/deck.json --out output/...`.
5. **Technical audit**: `python scripts/audit.py output/... --deck path/to/deck.json`.
6. **Visual review**: inspect each full-sized PNG and contact sheet, including mobile scale, manually.
7. **Polish**: change the fewest variables needed (copy first, then hierarchy, then decoration); log before/after.
8. **Approval**: no blockers, rubric >=90 if human-rated; clearly label unreviewed drafts.

Preflight catches text repetition, overlong copy, unsourced explicit metric fields and measurable color contrast. It **cannot** determine whether an arbitrary number embedded in text is factually true, whether the design is tasteful, or whether a line is clipped in a rendered image. Never state that it can.
