#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# ensure we're on main and up to date
git checkout main >/dev/null 2>&1 || true
git pull --ff-only origin main >/dev/null 2>&1 || true

check_file () {
  local path="$1"
  if git show "origin/main:$path" >/dev/null 2>&1; then
    echo "✅ $path"
  else
    echo "❌ $path"
  fi
}

echo "=== MERGE STATUS (origin/main) ==="
check_file "docs/ops/drills/GATEPACK_B1_RESEARCH_CLI.md"
check_file "docs/ops/drills/GATEPACK_B2_LIVE_OPS.md"
check_file "docs/ops/drills/GATEPACK_C_RISK.md"
check_file "src/ops/evidence.py"
check_file "scripts/research_cli.py"
check_file "scripts/live_ops.py"
check_file "src/risk/var_core.py"
check_file "scripts/risk_cli.py"

echo
echo "=== B2 FLAG CHECK (local main) ==="
if command -v rg >/dev/null 2>&1; then
  if rg -n --fixed-strings "--run-id" scripts/live_ops.py >/dev/null 2>&1; then
    echo "✅ live_ops has --run-id"
  else
    echo "❌ live_ops missing --run-id"
  fi
else
  if grep -nF -- "--run-id" scripts/live_ops.py >/dev/null 2>&1; then
    echo "✅ live_ops has --run-id"
  else
    echo "❌ live_ops missing --run-id"
  fi
fi

echo
echo "=== NEXT ACTIONS (manual merges) ==="
echo "Docs PR: https://github.com/rauterfrank-ui/Peak_Trade/compare/docs/gatepacks-merge-readiness?expand=1"
echo "B1 PR  : https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/research-cli-evidence-chain?expand=1"
echo "B2 PR  : https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/live-ops-evidence-chain?expand=1"
echo "C  PR  : https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/risk-var-core?expand=1"
