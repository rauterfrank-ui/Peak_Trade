#!/usr/bin/env bash
#
# run_required_checks_drift_guard_pr.sh
#
# Deterministic wrapper for Required Checks Drift Guard PR workflow.
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

SCRIPT="scripts/ops/create_required_checks_drift_guard_pr.sh"
echo "🔎 Verwende kanonischen Drift-Guard Entrypoint: $SCRIPT"

if [ ! -f "$SCRIPT" ]; then
  echo "❌ Kanonischer Entrypoint nicht gefunden: $SCRIPT" >&2
  exit 1
fi
chmod +x "$SCRIPT"

echo
echo "== HELP (falls verfügbar) =="
"$SCRIPT" --help 2>/dev/null || echo "ℹ️ Keine --help Option verfügbar"

echo
echo "== RUN =="
# Optional: Overrides
export BRANCH="${BRANCH:-feat/required-checks-drift-guard-v1}"
export BASE="${BASE:-main}"
export LABELS_CSV="${LABELS_CSV:-ops,ci}"

# Pass all CLI args through deterministically.
"$SCRIPT" "$@"
