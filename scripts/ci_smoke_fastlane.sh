#!/usr/bin/env bash
# ==============================================================================
# Peak_Trade CI Smoke Fast-Lane (Issue #19)
# ==============================================================================
#
# Ultra-fast smoke tests for CI pipeline (<2-3 min runtime).
# Runs deterministic, offline-only tests with zero external dependencies.
#
# SAFETY:
# - NO live/testnet exchanges
# - NO API keys or secrets required
# - NO external network calls
# - Fully deterministic (synthetic data only)
#
# Usage:
#   bash scripts/ci_smoke_fastlane.sh
#
# Exit codes:
#   0 = All smoke tests passed
#   1 = One or more smoke tests failed
#   2+ = Script/setup error
#
# ==============================================================================

set -euo pipefail

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Peak_Trade CI Smoke Fast-Lane${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Ensure we're in the repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo -e "${YELLOW}→ Repository root:${NC} ${REPO_ROOT}"
echo ""

# Create output directories
RESULTS_DIR="${REPO_ROOT}/test_results/ci_smoke_fastlane"
mkdir -p "${RESULTS_DIR}"

echo -e "${YELLOW}→ Results directory:${NC} ${RESULTS_DIR}"
echo ""

# ==============================================================================
# Fast-lane smoke test suite
# ==============================================================================
# These tests are carefully selected to:
# 1. Cover critical live-mode entrypoints
# 2. Validate core safety gates (risk limits, config, data quality)
# 3. Run in <2-3 minutes total
# 4. Use only synthetic/offline data (no external calls)
# ==============================================================================

SMOKE_TESTS=(
    # Live risk limits (Issue #20 dependency)
    "tests/test_live_smoke.py::test_live_order_request_creation"
    "tests/test_live_smoke.py::test_side_from_direction"
    "tests/test_live_smoke.py::test_live_risk_config_dataclass"
    "tests/test_live_smoke.py::test_live_risk_limits_from_config"
    "tests/test_live_smoke.py::test_live_risk_check_orders_empty"
    "tests/test_live_smoke.py::test_live_risk_check_orders_valid"

    # Execution pipeline (order lifecycle)
    "tests/test_execution_pipeline_smoke.py::TestSignalEvent::test_signal_event_creation"
    "tests/test_execution_pipeline_smoke.py::TestSignalEvent::test_signal_event_is_entry_long"
    "tests/test_execution_pipeline_smoke.py::TestSignalEvent::test_signal_event_is_exit_long"

    # Core backtest engine (baseline functionality)
    "tests/test_backtest_smoke.py"
)

echo -e "${YELLOW}→ Running ${#SMOKE_TESTS[@]} smoke tests...${NC}"
echo ""

# Run pytest with fast-lane configuration
# - Fail fast on first error (-x)
# - Quiet output (-q)
# - Capture short traceback (--tb=short)
# - Generate JUnit XML for CI artifact upload
# - No coverage (too slow for fast-lane)

if python3 -m pytest \
    "${SMOKE_TESTS[@]}" \
    -q \
    --tb=short \
    --junit-xml="${RESULTS_DIR}/junit.xml" \
    --disable-warnings \
    2>&1 | tee "${RESULTS_DIR}/pytest_output.txt"; then

    echo ""
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    echo ""
    exit 0
else
    PYTEST_EXIT=$?
    echo ""
    echo -e "${RED}✗ Smoke tests failed (exit code: ${PYTEST_EXIT})${NC}"
    echo ""
    echo -e "${YELLOW}Debug artifacts saved to:${NC} ${RESULTS_DIR}"
    echo -e "${YELLOW}- JUnit XML:${NC} junit.xml"
    echo -e "${YELLOW}- Pytest output:${NC} pytest_output.txt"
    echo ""
    exit 1
fi
