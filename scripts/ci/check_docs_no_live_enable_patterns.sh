#!/usr/bin/env bash
# scripts/ci/check_docs_no_live_enable_patterns.sh
#
# Purpose: Scan docs/ for dangerous live-enable patterns
# Exit 0: Clean (no dangerous patterns found)
# Exit 1: Violation detected
#
# Usage:
#   ./scripts/ci/check_docs_no_live_enable_patterns.sh
#
# Related: docs/ops/POLICY_SAFE_DOCUMENTATION_GUIDE.md

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCS_DIR="${REPO_ROOT}/docs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "🔍 Scanning docs/ for dangerous live-enable patterns..."
echo "Directory: ${DOCS_DIR}"
echo ""

# Define dangerous patterns
# These are patterns that should NEVER appear in docs as literal examples
PATTERNS=(
    "enable_live_trading\s*=\s*true"
    "enable_live_trading=true"
    "live_mode_armed\s*=\s*true"
    "live_mode_armed=true"
    "execution_mode\s*=\s*['\"]LIVE['\"]"
    "LIVE_MODE\s*=\s*true"
    "live_dry_run_mode\s*=\s*false"
    "live_dry_run_mode=false"
)

VIOLATIONS=0

# Scan for each pattern
for pattern in "${PATTERNS[@]}"; do
    echo "Checking pattern: ${pattern}"

    # Use ripgrep if available, otherwise fall back to grep
    if command -v rg &> /dev/null; then
        # ripgrep: case-insensitive, line numbers, no binary files
        if rg -i -n "${pattern}" "${DOCS_DIR}" 2>/dev/null; then
            echo -e "${RED}❌ VIOLATION: Found dangerous pattern '${pattern}' in docs/${NC}"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    else
        # fallback to grep
        if grep -r -i -n -E "${pattern}" "${DOCS_DIR}" 2>/dev/null; then
            echo -e "${RED}❌ VIOLATION: Found dangerous pattern '${pattern}' in docs/${NC}"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${VIOLATIONS} -eq 0 ]; then
    echo -e "${GREEN}✅ PASS: No dangerous live-enable patterns found in docs/${NC}"
    echo ""
    echo "Docs are safe for documentation purposes."
    exit 0
else
    echo -e "${RED}❌ FAIL: ${VIOLATIONS} violation(s) detected${NC}"
    echo ""
    echo "Please review the flagged patterns and replace them with safe alternatives:"
    echo "  - Use placeholders: enable_live_trading={true|false}"
    echo "  - Use descriptions: \"live trading flag (not shown for safety)\""
    echo "  - See: docs/ops/POLICY_SAFE_DOCUMENTATION_GUIDE.md"
    echo ""
    exit 1
fi
