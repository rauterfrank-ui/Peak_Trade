#!/usr/bin/env bash
#
# run_required_checks_drift_guard_pr.sh
#
# One-block wrapper that finds and runs the Required Checks Drift Guard PR workflow.
#
# Usage:
#   run_required_checks_drift_guard_pr.sh
#
# Environment Variables (optional):
#   REPO_DIR     Repository directory (default: $HOME/Peak_Trade)
#   BRANCH       Feature branch name (default: feat/required-checks-drift-guard-v1)
#   BASE         Base branch (default: main)
#   LABELS_CSV   Labels to add (default: ops,ci)

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
cd "$REPO_DIR"

echo "🔎 Suche Drift-Guard PR-Workflow Script…"
SCRIPT="$(
  git ls-files 'scripts/ops/*.sh' \
  | grep -E 'drift|required[_-]?checks' \
  | grep -v 'run_required_checks_drift_guard_pr.sh' \
  | grep -v 'verify_required_checks_drift.sh' \
  | grep -v 'test_verify_required_checks_drift.sh' \
  | head -n 1
)"

if [ -z "${SCRIPT:-}" ]; then
  echo "❌ Konnte kein passendes Script finden (Pattern: drift|required_checks)." >&2
  echo "   Tipp: nenne es z.B. scripts/ops/create_required_checks_drift_guard_pr.sh" >&2
  exit 1
fi

echo "✅ Script gefunden: $SCRIPT"
chmod +x "$SCRIPT"

echo
echo "== HELP (falls verfügbar) =="
"$SCRIPT" --help 2>/dev/null || echo "ℹ️ Keine --help Option verfügbar"

echo
echo "== RUN =="
# Optional: Overrides (nur relevant, wenn das Script ENV-Overrides unterstützt)
export BRANCH="${BRANCH:-feat/required-checks-drift-guard-v1}"
export BASE="${BASE:-main}"
export LABELS_CSV="${LABELS_CSV:-ops,ci}"

"$SCRIPT"
