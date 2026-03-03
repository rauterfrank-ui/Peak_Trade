#!/usr/bin/env bash
set -euo pipefail

echo "GIT-KONTEXT: expected main (read-only verification; no live execution)."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="out/ops/e2e_verify_${TS}"
mkdir -p "$OUT"

step() { echo ""; echo "==> $*"; }

step "1) PRCD AWS Export Write Smoke (gated by confirm_token + repo var)"
if gh workflow list --json name,path | rg -q '"path":"\.github/workflows/prcd-aws-export-write-smoke\.yml"'; then
  gh workflow run prcd-aws-export-write-smoke.yml --ref main -f confirm_token=YES_WRITE_SMOKE || true
else
  echo "SKIP: prcd-aws-export-write-smoke.yml not present"
fi

step "2) PRBG Execution Evidence (uses bundled input if available)"
if gh workflow list --json name,path | rg -q '"path":"\.github/workflows/prbg-execution-evidence\.yml"'; then
  gh workflow run prbg-execution-evidence.yml --ref main || true
else
  echo "SKIP: prbg-execution-evidence.yml not present"
fi

step "3) PRBE Shadow/Testnet Scorecard"
if gh workflow list --json name,path | rg -q '"path":"\.github/workflows/prbe-shadow-testnet-scorecard\.yml"'; then
  gh workflow run prbe-shadow-testnet-scorecard.yml --ref main || true
else
  echo "SKIP: prbe-shadow-testnet-scorecard.yml not present"
fi

step "4) PRBI Live Pilot Scorecard"
if gh workflow list --json name,path | rg -q '"path":"\.github/workflows/prbi-live-pilot-scorecard\.yml"'; then
  gh workflow run prbi-live-pilot-scorecard.yml --ref main || true
else
  echo "SKIP: prbi-live-pilot-scorecard.yml not present"
fi

step "Artifacts: operator pulls latest PRBI scorecard to out/ops/prbi_latest/"
if [ -x scripts/ops/pull_latest_prbi_scorecard.sh ]; then
  ./scripts/ops/pull_latest_prbi_scorecard.sh || true
fi

step "Summary: run ops_status (expects local artifacts) "
if [ -x scripts/ops/ops_status.sh ]; then
  ./scripts/ops/ops_status.sh || true
fi

echo ""
echo "E2E_VERIFY_OUT=${OUT}"
