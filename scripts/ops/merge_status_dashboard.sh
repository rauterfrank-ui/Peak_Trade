#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

git checkout main >/dev/null 2>&1 || true
git pull --ff-only origin main >/dev/null 2>&1 || true

has_file () {
  local path="$1"
  git show "origin/main:$path" >/dev/null 2>&1
}

show_status () {
  local label="$1" ok="$2"
  if [[ "$ok" == "1" ]]; then
    echo "✅ $label"
  else
    echo "❌ $label"
  fi
}

# grep helper on local main (more reliable in constrained env)
hgrep () {
  local pat="$1" file="$2"
  if command -v rg >/dev/null 2>&1; then
    rg -n --fixed-strings "$pat" "$file" >/dev/null 2>&1
  else
    grep -nF -- "$pat" "$file" >/dev/null 2>&1
  fi
}

echo "=== MERGE STATUS (origin/main) ==="

# Docs gatepacks
show_status "docs gatepack B1" $([[ -f docs/ops/drills/GATEPACK_B1_RESEARCH_CLI.md ]] && echo 1 || echo 0)
show_status "docs gatepack B2" $([[ -f docs/ops/drills/GATEPACK_B2_LIVE_OPS.md ]] && echo 1 || echo 0)
show_status "docs gatepack C " $([[ -f docs/ops/drills/GATEPACK_C_RISK.md ]] && echo 1 || echo 0)

# B1: research_cli evidence (signals)
b1_ok=0
if [[ -f scripts/research_cli.py ]]; then
  if hgrep "--run-id" scripts/research_cli.py && hgrep "artifacts/research" scripts/research_cli.py; then
    b1_ok=1
  fi
fi
show_status "B1 research_cli evidence hook" "$b1_ok"

# evidence helper presence
e_ok=0
[[ -f src/ops/evidence.py ]] && e_ok=1
show_status "evidence helper src/ops/evidence.py" "$e_ok"

# B2: live_ops evidence (signals)
b2_ok=0
if [[ -f scripts/live_ops.py ]]; then
  if hgrep "--run-id" scripts/live_ops.py && hgrep 'mode": "no_live' scripts/live_ops.py; then
    b2_ok=1
  fi
fi
show_status "B2 live_ops evidence hook (no_live)" "$b2_ok"

# C: risk core + risk_cli
c_ok=0
[[ -f src/risk/var_core.py ]] && [[ -f scripts/risk_cli.py ]] && c_ok=1
show_status "C risk var_core + risk_cli present" "$c_ok"

echo
echo "=== NEXT ACTIONS (manual merges) ==="
echo "Docs PR: https://github.com/rauterfrank-ui/Peak_Trade/compare/docs/gatepacks-merge-readiness?expand=1"
echo "B1 PR  : https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/research-cli-evidence-chain?expand=1"
echo "B2 PR  : https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/live-ops-evidence-chain?expand=1"
echo "C  PR  : https://github.com/rauterfrank-ui/Peak_Trade/compare/feat/risk-var-core?expand=1"
