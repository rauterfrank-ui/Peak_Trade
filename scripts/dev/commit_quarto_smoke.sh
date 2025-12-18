#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# 0) Repo-Root sicherstellen
# -----------------------------
cd "$(git rev-parse --show-toplevel)"

echo "== Git status =="
git status -sb

# -----------------------------
# 1) Quick-Verify: Quarto vorhanden?
# -----------------------------
echo "== Quarto version =="
quarto --version

# -----------------------------
# 2) Smoke Report lokal rendern
# -----------------------------
# Falls Makefile Targets existieren:
if make -q report-smoke 2>/dev/null; then
  echo "== make report-smoke =="
  make report-smoke
else
  echo "== make report-smoke target not found, trying script =="
  if [ -x scripts/dev/report_smoke.sh ]; then
    scripts/dev/report_smoke.sh
  else
    echo "ERROR: Weder Makefile target 'report-smoke' noch scripts/dev/report_smoke.sh gefunden."
    echo "=> Dann ist es doch nicht vollständig im Worktree. (Siehe unten: Claude-Code Promptblock)"
    exit 1
  fi
fi

# Optional: falls open-target existiert (nicht failen, wenn nicht vorhanden)
if make -q report-smoke-open 2>/dev/null; then
  echo "== make report-smoke-open (optional) =="
  make report-smoke-open || true
fi

# -----------------------------
# 3) Minimaler Sanity-Check: HTML irgendwo entstanden?
# -----------------------------
echo "== Find newest HTML under reports/ =="
HTML_FOUND="$(find reports -type f -name '*.html' 2>/dev/null | wc -l | tr -d ' ')"
echo "HTML count: ${HTML_FOUND}"
if [ "${HTML_FOUND}" = "0" ]; then
  echo "WARN: Keine HTML-Dateien gefunden. (CI sollte dank if-no-files-found: warn nicht failen)"
fi

# -----------------------------
# 4) (Optional) Tests laufen lassen
# -----------------------------
# Wenn du's schnell halten willst, auskommentieren.
echo "== pytest (optional) =="
python -m pytest -q || true

# -----------------------------
# 5) Commit + PR
# -----------------------------
BRANCH="feat/quarto-smoke-report"
echo "== Create/switch branch: ${BRANCH} =="
git checkout -B "${BRANCH}"

echo "== Stage changes =="
git add -A

echo "== Commit =="
git commit -m "feat(reporting): add Quarto smoke report" || {
  echo "No changes to commit (already committed)."
}

echo "== Push =="
git push -u origin "${BRANCH}"

# PR erstellen (GitHub CLI)
if command -v gh >/dev/null 2>&1; then
  echo "== Create PR =="
  gh pr create \
    --base main \
    --title "feat(reporting): Quarto smoke report" \
    --body $'Adds a minimal Quarto smoke report (self-contained HTML) + CI workflow.\n\nIncludes:\n- Quarto smoke qmd + render script/Make targets\n- CI workflow with graceful artifact handling (if-no-files-found: warn)\n- Reporting docs updates\n\nHow to run:\n- make report-smoke\n- make report-smoke-open (optional)\n'
else
  echo "gh nicht gefunden. Push ist done – PR bitte im GitHub UI erstellen."
fi
