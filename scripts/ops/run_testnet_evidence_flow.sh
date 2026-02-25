#!/usr/bin/env bash
set -euo pipefail

cd /Users/frnkhrz/Peak_Trade

echo "GIT-KONTEXT: main (ORCHESTRATOR: execute steps 1..5 for testnet evidence -> scorecards)"
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status -sb

: <<'CURSOR_MULTI_AGENT'
AGENT 1 (Planner)
Execute operator flow:
1) Enable exec event capture env (testnet mode), clear JSONL
2) Run the testnet session entrypoint (best-effort autodetect; fallback to operator-provided command)
3) Build execution evidence locally from JSONL
4) Dispatch PR-BG with tracked sample OR attach evidence by dispatching mock_profile=missing? (Prefer: keep CI validation sample; for real local evidence, store locally and just use it to drive local decision; CI dispatch can remain sample-based unless you want to commit evidence, which we will not.)
5) Dispatch PR-BE + PR-BI and download artifacts to out/ops/

Important: We will NOT commit out/ artifacts. All results stay under out/.

AGENT 2 (Repo Scout)
Find testnet entrypoint candidate:
- look for scripts containing "testnet" or "run_testnet"
- otherwise locate paper/shadow runner and testnet flag

AGENT 3 (Operator)
Run chosen command; ensure PT_EXEC_EVENTS_* env is set; collect logs.

AGENT 4 (Evidence)
Run execution_evidence_producer.py on JSONL; print summary.

AGENT 5 (CI Dispatcher)
Dispatch PR-BG (sample path) AND run PR-BE / PR-BI; download artifacts.

AGENT 6 (Reviewer)
If sample_size < thresholds or errors>0, interpret which gating blocks apply and next adjustments.

CURSOR_MULTI_AGENT

echo "STEP 1) Enable exec events + clear JSONL (local only)"
export PT_EXEC_EVENTS_ENABLED=true
export PT_EXEC_MODE=testnet
export PT_EXEC_EVENTS_JSONL_PATH=out/ops/execution_events/execution_events.jsonl

mkdir -p out/ops/execution_events
rm -f out/ops/execution_events/execution_events.jsonl || true
ls -la out/ops/execution_events

echo "STEP 2) Find and run a testnet session entrypoint (best-effort autodetect)"
rg -n "testnet" scripts src -S > /tmp/testnet_hits.txt 2>/dev/null || true
sed -n '1,220p' /tmp/testnet_hits.txt 2>/dev/null || true

CMD=""
if rg -n "run_.*testnet|testnet.*session|run_testnet" scripts -S >/dev/null 2>&1; then
  CMD="$(rg -n "run_.*testnet|testnet.*session|run_testnet" scripts -S 2>/dev/null | head -n 1 | cut -d: -f1)"
fi

if [ -n "${CMD}" ]; then
  echo "Detected script candidate: ${CMD}"
  python3 "${CMD}" --help 2>/dev/null || true
fi

echo "If you have a known testnet command, run it now. Otherwise, this step is a placeholder."
echo "PLACEHOLDER: (no automatic testnet runner executed)"

echo "STEP 2b) Minimal smoke event (ensures wiring works even if runner not found)"
python3 - <<'PY'
from src.observability.execution_events import emit
emit(event_type="session_start", level="info", msg="testnet session start (placeholder)")
emit(event_type="rate_limit", level="warning", is_anomaly=True, msg="placeholder anomaly")
PY

echo "STEP 3) Build execution evidence locally from JSONL"
python3 scripts/ci/execution_evidence_producer.py --out-dir reports/status --input out/ops/execution_events/execution_events.jsonl --input-format jsonl
sed -n '1,140p' reports/status/execution_evidence.md
cat reports/status/execution_evidence.json

echo "STEP 4) Dispatch PR-BG execution evidence (CI validation sample) and wait"
gh workflow run prbg-execution-evidence.yml --ref main -f input_path=docs/ops/samples/execution_events_sample.jsonl

sleep 3
gh run list --workflow prbg-execution-evidence.yml --branch main --limit 5 --json databaseId,status,conclusion,createdAt > /tmp/prbg_runs.json
RUN_BG="$(python3 - <<'PY'
import json
runs=json.load(open("/tmp/prbg_runs.json"))
print(runs[0]["databaseId"] if runs else "")
PY
)"
echo "RUN_BG=${RUN_BG}"
if [ -n "${RUN_BG}" ]; then
  gh run watch "${RUN_BG}" || true
  mkdir -p "out/ops/prbg_${RUN_BG}"
  gh run download "${RUN_BG}" --dir "out/ops/prbg_${RUN_BG}" || true
fi

echo "STEP 5) Dispatch PR-BE and PR-BI and download artifacts"
gh workflow run prbe-shadow-testnet-scorecard.yml --ref main
gh workflow run prbi-live-pilot-scorecard.yml --ref main

sleep 3
gh run list --workflow prbe-shadow-testnet-scorecard.yml --branch main --limit 5 --json databaseId,status,conclusion,createdAt > /tmp/prbe_runs.json
gh run list --workflow prbi-live-pilot-scorecard.yml --branch main --limit 5 --json databaseId,status,conclusion,createdAt > /tmp/prbi_runs.json

RUN_BE="$(python3 - <<'PY'
import json
runs=json.load(open("/tmp/prbe_runs.json"))
print(runs[0]["databaseId"] if runs else "")
PY
)"
RUN_BI="$(python3 - <<'PY'
import json
runs=json.load(open("/tmp/prbi_runs.json"))
print(runs[0]["databaseId"] if runs else "")
PY
)"
echo "RUN_BE=${RUN_BE}"
echo "RUN_BI=${RUN_BI}"

if [ -n "${RUN_BE}" ]; then
  gh run watch "${RUN_BE}" || true
  mkdir -p "out/ops/prbe_${RUN_BE}"
  gh run download "${RUN_BE}" --dir "out/ops/prbe_${RUN_BE}" || true
  sed -n '1,200p' "out/ops/prbe_${RUN_BE}"/**/shadow_testnet_scorecard.md 2>/dev/null || true
fi

if [ -n "${RUN_BI}" ]; then
  gh run watch "${RUN_BI}" || true
  mkdir -p "out/ops/prbi_${RUN_BI}"
  gh run download "${RUN_BI}" --dir "out/ops/prbi_${RUN_BI}" || true
  sed -n '1,200p' "out/ops/prbi_${RUN_BI}"/**/live_pilot_scorecard.md 2>/dev/null || true
fi

echo "DONE (all outputs are local-only under out/ and reports/status/)"
