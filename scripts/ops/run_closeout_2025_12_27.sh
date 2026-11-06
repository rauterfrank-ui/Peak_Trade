#!/usr/bin/env bash
set -euo pipefail

SCRIPT="scripts/ops/create_closeout_2025_12_27.sh"

echo "== 0) Preflight =="
test -f "$SCRIPT" || { echo "❌ Script nicht gefunden: $SCRIPT"; exit 1; }
test -x "$SCRIPT" || { echo "ℹ️ mache Script executable"; chmod +x "$SCRIPT"; }

gh auth status >/dev/null || { echo "❌ gh auth fehlt"; exit 1; }

# clean working tree (hart)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree nicht clean:"
  git status --porcelain
  exit 1
fi

echo "== 1) main sync =="
git checkout main
git pull --ff-only

echo "== 2) Run script =="
bash "$SCRIPT"

echo "== 3) Post-run sanity (was hat sich geändert?) =="
git status
git diff --stat

# Safety: Exit gracefully if no changes (e.g., re-run on main)
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already on main). Exiting 0."
  exit 0
fi

echo "== 4) Fast local gates (best effort) =="
if [[ -f scripts/ops/ops_center.sh ]]; then
  bash scripts/ops/ops_center.sh doctor
fi
if [[ -f scripts/ops/verify_required_checks_drift.sh ]]; then
  bash scripts/ops/verify_required_checks_drift.sh
fi
if command -v uv >/dev/null 2>&1; then
  uv run ruff check .
  uv run ruff format --check .
fi

echo "== 5) If script created a PR: watch checks (optional manual) =="
echo "Tipp: Falls dir das Script die PR-Nummer/URL ausspuckt:"
echo "  gh pr checks <PR_NUM> --watch"
echo "  gh pr view <PR_NUM> --json state,merged,mergeStateStatus,autoMergeRequest"
