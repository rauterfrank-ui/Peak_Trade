#!/usr/bin/env bash
set -euo pipefail

WF=".github/workflows/lint_gate.yml"
NEEDLE="scripts/ops/check_no_black_enforcement.sh"

echo "🛡️  Checking CI enforcement presence (Lint Gate contains formatter policy drift guard)..."

if [[ ! -f "$WF" ]]; then
  echo "❌ FAIL: Workflow not found: $WF"
  exit 1
fi

if grep -R --line-number --fixed-strings "$NEEDLE" "$WF" >/dev/null; then
  echo "✅ PASS: CI enforcement present (found: $NEEDLE in $WF)"
  exit 0
fi

echo "❌ FAIL: CI enforcement missing."
echo "   Expected to find: $NEEDLE"
echo "   In workflow:      $WF"
exit 1
