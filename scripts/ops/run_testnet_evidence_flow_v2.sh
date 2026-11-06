#!/usr/bin/env bash
set -euo pipefail

cd /Users/frnkhrz/Peak_Trade

echo "GIT-KONTEXT: main (fix operator flow: actually run testnet orchestrator + keep CI evidence aligned with real JSONL when desired)"
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status -sb

echo "1) Confirm testnet orchestrator exists + show help"
test -f scripts/orchestrate_testnet_runs.py
python3 scripts/orchestrate_testnet_runs.py --help || true

echo "2) Run real testnet orchestrator with exec-events enabled (best-effort; adjust args as needed)"
export PT_EXEC_EVENTS_ENABLED=true
export PT_EXEC_MODE=testnet
export PT_EXEC_EVENTS_JSONL_PATH=out/ops/execution_events/execution_events.jsonl

mkdir -p out/ops/execution_events
rm -f out/ops/execution_events/execution_events.jsonl || true

# Temp config with mode=testnet (required by orchestrator; original stays "paper")
CONFIG_TESTNET="/tmp/config_testnet_$$.toml"
python3 - <<PY
import re
p = "config/config.toml"
t = open(p).read()
t = re.sub(r'(\[environment\][^\n]*\n(?:[^\n]*\n)*?)mode\s*=\s*"paper"', r'\1mode = "testnet"', t, count=1)
open("${CONFIG_TESTNET}", "w").write(t)
PY

python3 scripts/orchestrate_testnet_runs.py --config "${CONFIG_TESTNET}" --profile ma_crossover_small --override-duration 2 || true
rm -f "${CONFIG_TESTNET}" 2>/dev/null || true

echo "3) Build local execution evidence from real JSONL and inspect counts"
python3 scripts/ci/execution_evidence_producer.py --out-dir reports/status --input out/ops/execution_events/execution_events.jsonl --input-format jsonl
sed -n '1,140p' reports/status/execution_evidence.md

echo "4) If you want CI to use your real evidence without committing out/: copy JSONL to a tracked temp sample path under docs/ops/samples/ (manual, ephemeral) then dispatch PR-BG with input_path."
echo "   This is optional. Default keeps CI validation sample."
echo "   If you choose to do it, use a timestamped file and delete it afterwards."
TS="$(date -u +%Y%m%dT%H%M%SZ)"
TMP_SAMPLE="docs/ops/samples/execution_events_session_${TS}.jsonl"
if [ -s out/ops/execution_events/execution_events.jsonl ]; then
  cp -f out/ops/execution_events/execution_events.jsonl "${TMP_SAMPLE}"
  echo "Wrote ${TMP_SAMPLE} (tracked path; DO NOT COMMIT; delete after dispatch)."
  gh workflow run prbg-execution-evidence.yml --ref main -f input_path="${TMP_SAMPLE}"
  sleep 3
  gh run list --workflow prbg-execution-evidence.yml --branch main --limit 3 --json databaseId,status,conclusion,createdAt > /tmp/prbg_runs_real.json
  python3 - <<'PY'
import json
runs=json.load(open("/tmp/prbg_runs_real.json"))
print("LATEST_RUN_ID:", runs[0]["databaseId"] if runs else None)
PY
  rm -f "${TMP_SAMPLE}"
  git checkout -- "${TMP_SAMPLE}" 2>/dev/null || true
fi

echo "5) Re-run scorecards (PR-BE + PR-BI) to see if readiness improves"
gh workflow run prbe-shadow-testnet-scorecard.yml --ref main
gh workflow run prbi-live-pilot-scorecard.yml --ref main

sleep 3
gh run list --workflow prbe-shadow-testnet-scorecard.yml --branch main --limit 3 --json databaseId,status,conclusion,createdAt > /tmp/prbe_runs_real.json
gh run list --workflow prbi-live-pilot-scorecard.yml --branch main --limit 3 --json databaseId,status,conclusion,createdAt > /tmp/prbi_runs_real.json

RUN_BE="$(python3 - <<'PY'
import json
runs=json.load(open("/tmp/prbe_runs_real.json"))
print(runs[0]["databaseId"] if runs else "")
PY
)"
RUN_BI="$(python3 - <<'PY'
import json
runs=json.load(open("/tmp/prbi_runs_real.json"))
print(runs[0]["databaseId"] if runs else "")
PY
)"
echo "RUN_BE=${RUN_BE}"
echo "RUN_BI=${RUN_BI}"

mkdir -p out/ops/prbe_latest out/ops/prbi_latest
rm -rf out/ops/prbe_latest/* out/ops/prbi_latest/* 2>/dev/null || true

if [ -n "${RUN_BE}" ]; then
  gh run watch "${RUN_BE}" || true
  gh run download "${RUN_BE}" --dir out/ops/prbe_latest || true
  sed -n '1,200p' out/ops/prbe_latest/**/shadow_testnet_scorecard.md 2>/dev/null || true
fi

if [ -n "${RUN_BI}" ]; then
  gh run watch "${RUN_BI}" || true
  gh run download "${RUN_BI}" --dir out/ops/prbi_latest || true
  sed -n '1,200p' out/ops/prbi_latest/**/live_pilot_scorecard.md 2>/dev/null || true
fi
