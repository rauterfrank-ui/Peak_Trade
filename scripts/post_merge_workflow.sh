#!/usr/bin/env bash
set -euo pipefail

cd ~/Peak_Trade

echo "============================================================"
echo "PEAK_TRADE — POST-MERGE FULL WORKFLOW (ALL-IN-ONE)"
echo "Repo: $(pwd)"
echo "============================================================"

echo
echo "=== 0) SAFETY / STATUS ==="
git status -sb
echo
echo "--- last commit ---"
git log -1 --oneline

echo
echo "=== 1) FETCH + PRUNE (Repo Hygiene) ==="
git fetch --prune

echo
echo "=== 2) ENSURE main + UPDATE ==="
git checkout main
git pull --ff-only

echo
echo "=== 3) CLEANUP LOCAL MERGE-LOG BRANCH (if exists) ==="
git branch --list "docs/ops-pr201-merge-log" | grep -q . && git branch -D "docs/ops-pr201-merge-log" || true

echo
echo "=== 4) DOCS SANITY (files exist?) ==="
for f in \
  "docs/ops/PR_201_MERGE_LOG.md" \
  "docs/ops/README.md" \
  "docs/PEAK_TRADE_STATUS_OVERVIEW.md"
do
  if [ -f "$f" ]; then
    echo "OK: $f"
  else
    echo "WARN (missing): $f"
  fi
done

echo
echo "=== 5) CORE VERIFICATION: ruff + pytest (should pass without web extras) ==="
uv run ruff check src tests scripts
uv run pytest -q

echo
echo "NOTE: Plot/Report tests require matplotlib and will be skipped without it."
echo "      To run all tests including visualization: uv sync --extra viz && uv run pytest -q"

echo
echo "=== 6) DETECT OPTIONAL-DEPENDENCIES EXTRAS (pyproject.toml) ==="
WEB_EXTRA="$(
uv run python - <<'PY'
import pathlib, tomllib

p = pathlib.Path("pyproject.toml")
data = tomllib.loads(p.read_text(encoding="utf-8"))
extras = sorted(((data.get("project") or {}).get("optional-dependencies") or {}).keys())

print("Extras:", ", ".join(extras) if extras else "<none>")

# Heuristik: wir picken den wahrscheinlichsten Web-Extra-Key
# Priorität: exakt "web", sonst alles was 'web' enthält, sonst 'ui'/'dashboard'
cands = []
if "web" in extras:
    cands = ["web"]
else:
    cands = [e for e in extras if "web" in e.lower()]
    if not cands:
        cands = [e for e in extras if any(t in e.lower() for t in ("ui", "dashboard"))]

pick = cands[0] if cands else ""
print(pick)
PY
)"

# Die Python-Ausgabe enthält 2 Zeilen: "Extras: ..." und dann den Pick.
# Wir nehmen die letzte Zeile als tatsächlichen Extra-Key:
WEB_EXTRA="$(printf "%s" "$WEB_EXTRA" | tail -n 1 | tr -d '\r')"

echo
echo "=== 7) OPTIONAL WEB STACK: install extra + rerun tests (auto if found) ==="
if [ -n "${WEB_EXTRA}" ]; then
  echo "Detected web-related extra: '${WEB_EXTRA}'"
  echo "-> Installing via: uv sync --extra ${WEB_EXTRA}"
  uv sync --extra "${WEB_EXTRA}"

  echo
  echo "--- Re-run pytest after installing web extras ---"
  # Hinweis: wenn Web-Tests über Marker/Ordner laufen, ist full-suite am sichersten:
  uv run pytest -q
else
  echo "No web-related extra detected in pyproject optional-dependencies. Skipping web-install step."
fi

echo
echo "=== 8) STAGE 1 MONITORING: run snapshot/trend if scripts exist ==="
if [ -d "scripts/obs" ]; then
  echo "Found scripts/obs"

  # Daily snapshot (wenn vorhanden)
  if [ -f "scripts/obs/stage1_daily_snapshot.py" ]; then
    echo
    echo "--- Running stage1_daily_snapshot.py ---"
    uv run python scripts/obs/stage1_daily_snapshot.py || true
  else
    echo "No scripts/obs/stage1_daily_snapshot.py"
  fi

  # Weekly trend (best-effort: erster Treffer *trend*.py)
  TREND_PY="$(ls -1 scripts/obs/*trend*.py 2>/dev/null | head -n 1 || true)"
  if [ -n "${TREND_PY}" ]; then
    echo
    echo "--- Running trend script: ${TREND_PY} ---"
    uv run python "${TREND_PY}" || true
  else
    echo "No trend script found matching scripts/obs/*trend*.py"
  fi

  # Wrapper (wenn vorhanden)
  WRAP_SH="$(ls -1 scripts/obs/*.sh 2>/dev/null | head -n 1 || true)"
  if [ -n "${WRAP_SH}" ]; then
    echo
    echo "--- Found wrapper candidate: ${WRAP_SH} (not auto-executing) ---"
    echo "If you want, run manually: bash ${WRAP_SH}"
  fi
else
  echo "No scripts/obs directory. Skipping Stage 1 monitoring run."
fi

echo
echo "=== 9) FINAL STATUS ==="
git status -sb
echo "--- last commit ---"
git log -1 --oneline

echo
echo "============================================================"
echo "DONE ✅  (All-in-one post-merge hygiene + verification complete)"
echo "============================================================"
