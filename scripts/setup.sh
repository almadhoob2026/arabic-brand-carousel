#!/usr/bin/env bash
# One-time setup: creates .venv next to this skill and installs the renderer's dependencies.
# Safe to re-run. Uses system Chrome/Chromium when present; otherwise downloads Playwright's Chromium.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
if [ ! -x .venv/bin/python ]; then
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
if ! .venv/bin/python - <<'PY' 2>/dev/null
import sys
sys.path.insert(0, 'scripts')
from render import browser_executable
sys.exit(0 if browser_executable() else 1)
PY
then
  .venv/bin/python -m playwright install chromium
fi
echo "Ready: $ROOT/.venv/bin/python"
