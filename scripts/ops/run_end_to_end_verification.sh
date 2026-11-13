#!/usr/bin/env bash
set -euo pipefail

dispatch_failed=0
wf_run() {
  local workflow="$1"
  if ! gh workflow view "$workflow" >/dev/null; then
    echo "ERROR: could not resolve $workflow" >&2
    dispatch_failed=1
  elif ! gh workflow run "$workflow" --ref main; then
    echo "ERROR: dispatch failed for $workflow" >&2
    dispatch_failed=1
  fi
}

echo "GIT-KONTEXT: dispatching evidence and scorecard workflows on main."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="out/ops/e2e_verify_${TS}"
mkdir -p "$OUT"

step() { echo ""; echo "==> $*"; }

step "1) PRBG Execution Evidence (uses bundled input if available)"
wf_run prbg-execution-evidence.yml

step "2) PRBE Shadow/Testnet Scorecard"
wf_run prbe-shadow-testnet-scorecard.yml

step "3) PRBI Live Pilot Scorecard"
wf_run prbi-live-pilot-scorecard.yml

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
exit "$dispatch_failed"
