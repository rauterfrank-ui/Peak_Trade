#!/usr/bin/env bash
# Peak_Trade Fast Smoke Tests Runner
# ==================================
# Runs the fast smoke test suite for CI/CD pipelines
#
# Usage:
#   ./scripts/run_smoke_tests.sh
#
# Expected runtime: < 2 seconds
# Exit codes: 0 = all pass, non-zero = failures
#
# Note: Collection errors from optional dependencies (e.g., FastAPI tests)
# are ignored. Only smoke-marked tests are executed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=========================================="
echo "Peak_Trade Fast Smoke Tests"
echo "=========================================="
echo ""

# Run smoke tests only (discovers all tests marked with @pytest.mark.smoke)
# Ignore collection errors from optional dependencies
python -m pytest \
    -m smoke \
    -v \
    --tb=short \
    --continue-on-collection-errors

echo ""
echo "=========================================="
echo "✅ Smoke tests completed successfully"
echo "=========================================="
