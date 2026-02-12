#!/usr/bin/env bash
set -euo pipefail

# Guardrail: ensure uvicorn (web extra) is installed in the active environment.
# Works for uv-managed envs and standard venvs.
PY_EXEC="${PY_EXEC:-}"
if [[ -z "$PY_EXEC" ]]; then
  if command -v uv &>/dev/null; then
    PY_EXEC="uv run python"
  elif command -v python3 &>/dev/null; then
    PY_EXEC="python3"
  else
    PY_EXEC="python"
  fi
fi

$PY_EXEC - <<'PY'
import importlib.util, sys
missing = []
for pkg in ("fastapi", "uvicorn"):
    if importlib.util.find_spec(pkg) is None:
        missing.append(pkg)
if missing:
    sys.stderr.write(
        "ERROR: Missing required web packages: "
        + ", ".join(missing)
        + "\n\nFix (uv):   uv sync --extra web\n"
        + "Fix (venv): pip install -e '.[web]'\n"
    )
    raise SystemExit(2)
print("OK: web runtime deps present (fastapi, uvicorn).")
PY
