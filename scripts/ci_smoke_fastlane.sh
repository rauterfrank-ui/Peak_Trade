#!/usr/bin/env bash
# scripts/ci_smoke_fastlane.sh
# =============================================================================
# CI Smoke Fast Lane
# =============================================================================
# Ultra-fast, deterministic smoke tests for CI/CD.
#
# Purpose:
#   - Catch critical issues FAST (< 2-3 min target)
#   - No external calls, no secrets, no live risk
#   - Fail fast on import/config/gating issues
#
# Outputs:
#   - reports/ci_smoke/junit.xml (pytest JUnit format)
#   - reports/ci_smoke/pytest.txt (test output)
#   - reports/ci_smoke/env.txt (environment snapshot)
#
# Usage:
#   bash scripts/ci_smoke_fastlane.sh
#   make ci-smoke
#
# Exit codes:
#   0 = All smoke tests passed
#   1 = Smoke tests failed (critical issue)
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="${REPO_ROOT}/reports/ci_smoke"

echo "============================================================================="
echo "CI Smoke Fast Lane"
echo "============================================================================="
echo "Repo: ${REPO_ROOT}"
echo "Reports: ${REPORTS_DIR}"
echo ""

# Create reports directory
mkdir -p "${REPORTS_DIR}"

# =============================================================================
# Step 1: Environment Snapshot
# =============================================================================
echo -e "${YELLOW}[1/4] Capturing environment snapshot...${NC}"

{
    echo "=== CI Smoke Fast Lane Environment ==="
    echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    echo "Hostname: $(hostname)"
    echo "User: $(whoami)"
    echo "PWD: $(pwd)"
    echo ""
    echo "=== System ==="
    uname -a
    echo ""
    echo "=== Python ==="
    python3 --version
    python3 -c "import sys; print(f'Executable: {sys.executable}')"
    python3 -c "import sys; print(f'Path: {sys.path}')"
    echo ""
    echo "=== Installed Packages ==="
    pip freeze || pip3 freeze || echo "pip freeze failed"
    echo ""
    echo "=== Git ==="
    git rev-parse --short HEAD 2>/dev/null || echo "Not a git repo"
    git branch --show-current 2>/dev/null || echo "No current branch"
    git status --short 2>/dev/null || echo "Git status unavailable"
} > "${REPORTS_DIR}/env.txt"

echo -e "${GREEN}✓ Environment snapshot saved${NC}"
echo ""

# =============================================================================
# Step 2: Syntax Check (compileall)
# =============================================================================
echo -e "${YELLOW}[2/4] Running Python syntax check (compileall)...${NC}"

if python3 -m compileall -q src; then
    echo -e "${GREEN}✓ Syntax check passed${NC}"
else
    echo -e "${RED}✗ Syntax check FAILED${NC}"
    echo "Run locally: python3 -m compileall src"
    exit 1
fi
echo ""

# =============================================================================
# Step 3: Smoke Tests (pytest)
# =============================================================================
echo -e "${YELLOW}[3/4] Running smoke tests...${NC}"

# Run pytest with JUnit XML output
if python3 -m pytest tests/smoke/ \
    --junitxml="${REPORTS_DIR}/junit.xml" \
    --tb=short \
    -v \
    2>&1 | tee "${REPORTS_DIR}/pytest.txt"; then

    PYTEST_EXIT=0
    echo -e "${GREEN}✓ Smoke tests PASSED${NC}"
else
    PYTEST_EXIT=1
    echo -e "${RED}✗ Smoke tests FAILED${NC}"
fi

echo ""

# =============================================================================
# Step 4: Summary
# =============================================================================
echo -e "${YELLOW}[4/4] Summary${NC}"
echo ""

if [ ${PYTEST_EXIT} -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ CI SMOKE FAST LANE: PASSED${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Reports:"
    echo "  - ${REPORTS_DIR}/junit.xml"
    echo "  - ${REPORTS_DIR}/pytest.txt"
    echo "  - ${REPORTS_DIR}/env.txt"
    echo ""
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ CI SMOKE FAST LANE: FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Check reports:"
    echo "  - ${REPORTS_DIR}/pytest.txt (test output)"
    echo "  - ${REPORTS_DIR}/junit.xml (JUnit XML)"
    echo "  - ${REPORTS_DIR}/env.txt (environment)"
    echo ""
    echo "Debug locally:"
    echo "  python3 -m pytest tests/smoke/ -v"
    echo ""
    exit 1
fi
