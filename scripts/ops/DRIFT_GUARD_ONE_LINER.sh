#!/usr/bin/env bash
#
# DRIFT_GUARD_ONE_LINER.sh
#
# Ultra-quick copy/paste script for Required Checks Drift Guard setup + test
#
# Usage (copy entire block to terminal):
#
# bash <(curl -s https://raw.githubusercontent.com/YOUR_ORG/Peak_Trade/main/scripts/ops/DRIFT_GUARD_ONE_LINER.sh)
#
# Or locally:
#
# cd ~/Peak_Trade && bash scripts/ops/DRIFT_GUARD_ONE_LINER.sh
#

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Required Checks Drift Guard — One-Liner Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
cd "$REPO_DIR"

# 1) Run setup (if exists)
if [ -x scripts/ops/setup_drift_guard_pr_workflow.sh ]; then
  echo "📦 1) Running setup_drift_guard_pr_workflow.sh"
  bash scripts/ops/setup_drift_guard_pr_workflow.sh
else
  echo "⚠️  Setup script not found, skipping setup"
fi

# 2) Run smoke tests
if [ -x scripts/ops/tests/test_drift_guard_pr_workflow.sh ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🧪 2) Running smoke tests"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  bash scripts/ops/tests/test_drift_guard_pr_workflow.sh
fi

# 3) Run dry-run (offline only)
if [ -x scripts/ops/run_required_checks_drift_guard_pr.sh ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🧪 3) Running dry-run (offline only)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  bash scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ One-Liner Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "   # Test with live check (requires gh + jq)"
echo "   scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run"
echo ""
echo "   # Create PR (production)"
echo "   scripts/ops/run_required_checks_drift_guard_pr.sh"
echo ""
echo "   # Run ops doctor (includes drift check)"
echo "   scripts/ops/ops_center.sh doctor"
echo ""
echo "📚 Docs: docs/ops/DRIFT_GUARD_QUICK_START.md"
echo ""
