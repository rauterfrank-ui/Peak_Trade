#!/usr/bin/env bash
#
# validate_merge_logs_setup.sh - Fast offline validation for merge logs infrastructure
#
# Purpose:
#   - Checks that merge logs batch generator is executable
#   - Checks that docs contain required markers
#   - Runs in <1s (no network calls)
#
# Exit codes:
#   0 = All checks passed
#   1 = One or more checks failed

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAILED=0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
check_pass() {
  echo "✅ $1"
}

check_fail() {
  echo "❌ $1"
  FAILED=1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Checks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Merge Logs Setup Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$REPO_ROOT"

# ──────────────────────────────────────────────────────────
# 1) Check batch script exists + executable
# ──────────────────────────────────────────────────────────
BATCH_SCRIPT="scripts/ops/generate_merge_logs_batch.sh"

if [[ ! -f "$BATCH_SCRIPT" ]]; then
  check_fail "$BATCH_SCRIPT: File not found"
elif [[ ! -x "$BATCH_SCRIPT" ]]; then
  check_fail "$BATCH_SCRIPT: Not executable (run: chmod +x $BATCH_SCRIPT)"
else
  check_pass "$BATCH_SCRIPT: Exists + executable"
fi

# ──────────────────────────────────────────────────────────
# 2) Check docs contain markers
# ──────────────────────────────────────────────────────────
START_MARKER="<!-- MERGE_LOG_EXAMPLES:START -->"
END_MARKER="<!-- MERGE_LOG_EXAMPLES:END -->"

for DOC in "docs/ops/README.md" "docs/ops/MERGE_LOG_WORKFLOW.md"; do
  if [[ ! -f "$DOC" ]]; then
    check_fail "$DOC: File not found"
    continue
  fi

  if ! grep -qF "$START_MARKER" "$DOC"; then
    check_fail "$DOC: Missing marker $START_MARKER"
  elif ! grep -qF "$END_MARKER" "$DOC"; then
    check_fail "$DOC: Missing marker $END_MARKER"
  else
    check_pass "$DOC: Markers present"
  fi
done

# ──────────────────────────────────────────────────────────
# 3) Check ops_center.sh has merge-logs subcommand
# ──────────────────────────────────────────────────────────
OPS_CENTER="scripts/ops/ops_center.sh"

if [[ ! -f "$OPS_CENTER" ]]; then
  check_fail "$OPS_CENTER: File not found"
elif ! grep -qF "cmd_merge_logs()" "$OPS_CENTER"; then
  check_fail "$OPS_CENTER: Missing cmd_merge_logs() function"
elif ! grep -qF "merge-logs)" "$OPS_CENTER"; then
  check_fail "$OPS_CENTER: Missing 'merge-logs)' case branch"
else
  check_pass "$OPS_CENTER: merge-logs subcommand present"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$FAILED" -eq 0 ]]; then
  echo "✅ All checks passed"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
else
  echo "❌ One or more checks failed"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi
