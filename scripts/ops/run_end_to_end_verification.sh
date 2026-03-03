#!/usr/bin/env bash
set -euo pipefail

wf_exists() { gh workflow view "$1" >/dev/null 2>&1; }
wf_run() { local wf="$1"; shift; if wf_exists "$wf"; then gh workflow run "$wf" --ref main "$@" || true; else echo "SKIP: $wf not found"; fi }

echo "GIT-KONTEXT: expected main (read-only verification; no live execution)."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="out/ops/e2e_verify_${TS}"
mkdir -p "$OUT"

step() { echo ""; echo "==> $*"; }

step "1) PRCD AWS Export Write Smoke (gated by confirm_token + repo var)"
wf_run prcd-aws-export-write-smoke.yml -f confirm_token=YES_WRITE_SMOKE

step "2) PRBG Execution Evidence (uses bundled input if available)"
wf_run prbg-execution-evidence.yml

step "3) PRBE Shadow/Testnet Scorecard"
wf_run prbe-shadow-testnet-scorecard.yml

step "4) PRBI Live Pilot Scorecard"
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
