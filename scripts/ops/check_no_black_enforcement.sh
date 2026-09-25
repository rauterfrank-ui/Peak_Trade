#!/usr/bin/env bash
set -euo pipefail

# Peak_Trade Formatter Enforcement Guardrail
# ===========================================
# Prüft, dass keine black --check Enforcement in Workflows/Scripts existiert.
# Source of Truth: ruff format --check

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛡️  Formatter Enforcement Policy Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "${REPO_ROOT}"

# Patterns für black enforcement
PATTERNS=(
  "black --check"
  "python -m black --check"
  "python3 -m black --check"
  "uv run black --check"
  "psf/black"
)

FINDINGS=0
FINDINGS_DETAILS=""

for pattern in "${PATTERNS[@]}"; do
  # Suche in .github/workflows und scripts, aber exclude dieses Script selbst
  MATCHES=$(grep -rIn --line-number -F "$pattern" .github/workflows scripts 2>/dev/null | grep -v "check_no_black_enforcement.sh" || true)

  if [[ -n "$MATCHES" ]]; then
    FINDINGS=$((FINDINGS + 1))
    FINDINGS_DETAILS="${FINDINGS_DETAILS}

❌ Pattern found: '$pattern'
$MATCHES
"
  fi
done

if [[ "$FINDINGS" -gt 0 ]]; then
  echo "❌ FAIL: Found black enforcement in workflows/scripts"
  echo ""
  echo "Formatter source of truth is 'ruff format --check', not 'black --check'."
  echo ""
  echo "Found $FINDINGS pattern(s):"
  echo "$FINDINGS_DETAILS"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Fix: Replace 'black --check' with 'ruff format --check'"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
else
  echo "✅ No black enforcement found"
  echo ""
  echo "Checked patterns:"
  for pattern in "${PATTERNS[@]}"; do
    echo "  - '$pattern'"
  done
  echo ""
  echo "Checked locations:"
  echo "  - .github/workflows"
  echo "  - scripts"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ Formatter policy: ruff format --check (enforced)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
fi
