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

# Test 6: Single-path detector wiring (offline checks)
detector="$REPO_ROOT/scripts/ci/required_checks_drift_detector.py"
config_json="$REPO_ROOT/config/ci/required_status_checks.json"

if [[ -f "$detector" ]]; then
  pass "Canonical detector exists"
else
  fail "Canonical detector exists"
fi

if [[ -f "$config_json" ]]; then
  pass "JSON SSOT config exists"
else
  fail "JSON SSOT config exists"
fi

if echo "$help_output" | grep -q -- "--required-config"; then
  pass "Help documents --required-config flag"
else
  fail "Help documents --required-config flag"
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
