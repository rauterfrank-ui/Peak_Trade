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

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=========================================="
echo "Peak_Trade Fast Smoke Tests"
echo "=========================================="
echo ""

# Run smoke tests only
python -m pytest \
    -m smoke \
    tests/test_resilience.py \
    tests/test_stability_smoke.py \
    -v \
    --tb=short \
    --quiet

echo ""
echo "=========================================="
echo "✅ Smoke tests completed successfully"
echo "=========================================="
