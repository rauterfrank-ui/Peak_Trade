#!/usr/bin/env bash
#
# test_verify_required_checks_drift.sh
#
# Smoke tests for verify_required_checks_drift.sh
# No network dependencies (bash syntax + help output only)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/ops/verify_required_checks_drift.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stats
TOTAL=0
PASSED=0
FAILED=0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pass() {
  echo -e "${GREEN}✓${NC} $1"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
}

fail() {
  echo -e "${RED}✗${NC} $1"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Smoke Tests: verify_required_checks_drift.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Script exists
if [[ -f "$SCRIPT" ]]; then
  pass "Script exists"
else
  fail "Script exists"
  exit 1
fi

# Test 2: Script is executable
if [[ -x "$SCRIPT" ]]; then
  pass "Script is executable"
else
  fail "Script is executable"
fi

# Test 3: Bash syntax check
if bash -n "$SCRIPT" 2>/dev/null; then
  pass "Bash syntax check"
else
  fail "Bash syntax check"
fi

# Test 4: Help output works
if "$SCRIPT" --help &>/dev/null; then
  pass "Help flag works (--help)"
else
  fail "Help flag works (--help)"
fi

# Test 5: Help contains key sections
help_output="$("$SCRIPT" --help 2>&1)"

if echo "$help_output" | grep -q "Required Checks Drift Guard"; then
  pass "Help contains title"
else
  fail "Help contains title"
fi

if echo "$help_output" | grep -q "EXIT CODES"; then
  pass "Help contains exit codes section"
else
  fail "Help contains exit codes section"
fi

if echo "$help_output" | grep -q "EXAMPLES"; then
  pass "Help contains examples section"
else
  fail "Help contains examples section"
fi

if echo "$help_output" | grep -q -- "--warn-only"; then
  pass "Help documents --warn-only flag"
else
  fail "Help documents --warn-only flag"
fi

# Test 6: Doc extraction function (offline test via sourcing)
# We'll test if the awk pattern at least runs without error
doc_file="$REPO_ROOT/docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md"

if [[ -f "$doc_file" ]]; then
  pass "Documentation file exists"

  # Simple pattern test: does the extraction command run?
  if sed -n '/^## Current Required Checks/,/^---/p' "$doc_file" \
      | grep -E '^[0-9]+\. \*\*' \
      | sed -E 's/^[0-9]+\. \*\*//; s/\*\*.*$//' \
      >/dev/null 2>&1; then
    pass "Doc extraction command runs"

    # Check if we actually get output
    check_count=$(sed -n '/^## Current Required Checks/,/^---/p' "$doc_file" \
      | grep -E '^[0-9]+\. \*\*' \
      | sed -E 's/^[0-9]+\. \*\*//; s/\*\*.*$//' \
      | wc -l | tr -d ' ')

    if [[ "$check_count" -gt 0 ]]; then
      pass "Doc extraction finds checks ($check_count found)"
    else
      fail "Doc extraction finds checks (0 found)"
    fi
  else
    fail "Doc extraction command runs"
  fi
else
  fail "Documentation file exists"
fi

# Test 7: Unknown flag handling
if "$SCRIPT" --nonexistent-flag 2>&1 | grep -iq "unknown option"; then
  pass "Unknown flag produces error message"
else
  fail "Unknown flag produces error message"
fi

# Test 8: Shebang is correct
shebang="$(head -n1 "$SCRIPT")"
if [[ "$shebang" == "#!/usr/bin/env bash" ]]; then
  pass "Shebang is correct"
else
  fail "Shebang is correct (found: $shebang)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total:  $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ All tests passed${NC}"
  echo ""
  echo "Note: These are offline smoke tests only."
  echo "For live checks, run: scripts/ops/verify_required_checks_drift.sh"
  echo ""
  exit 0
else
  echo -e "${RED}❌ Some tests failed${NC}"
  echo ""
  exit 1
fi
