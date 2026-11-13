#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

git rev-parse --verify origin/main >/dev/null

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

# Read the same local origin/main revision for each probe.
hgrep () {
  local pat="$1" file="$2"
  if command -v rg >/dev/null 2>&1; then
    git show "origin/main:$file" | rg -n --fixed-strings --no-heading -- "$pat" >/dev/null 2>&1
  else
    git show "origin/main:$file" | grep -nF -- "$pat" >/dev/null 2>&1
  fi
}

echo "=== MERGE STATUS (origin/main) ==="

# Docs gatepacks
show_status "docs gatepack B1" $(has_file docs/ops/drills/GATEPACK_B1_RESEARCH_CLI.md && echo 1 || echo 0)
show_status "docs gatepack B2" $(has_file docs/ops/drills/GATEPACK_B2_LIVE_OPS.md && echo 1 || echo 0)
show_status "docs gatepack C " $(has_file docs/ops/drills/GATEPACK_C_RISK.md && echo 1 || echo 0)

# B1: research_cli evidence (signals; path built as "artifacts" / "research" in code)
b1_ok=0
if has_file scripts/research_cli.py; then
  if hgrep "--run-id" scripts/research_cli.py && (hgrep "artifacts/research" scripts/research_cli.py || (hgrep '"artifacts"' scripts/research_cli.py && hgrep '"research"' scripts/research_cli.py)); then
    b1_ok=1
  fi
fi
show_status "B1 research_cli evidence hook" "$b1_ok"

# evidence helper presence
e_ok=0
has_file src/ops/evidence.py && e_ok=1
show_status "evidence helper src/ops/evidence.py" "$e_ok"

# B2's original CSV provider was retired and no longer generates this pack.
echo "B2 historical live_ops evidence hook: RETIRED"

# C: risk core + risk_cli
c_ok=0
has_file src/risk/var_core.py && has_file scripts/risk_cli.py && c_ok=1
show_status "C risk var_core + risk_cli present" "$c_ok"

echo
echo "Status refers to the local origin/main ref; open pull requests were not queried."
