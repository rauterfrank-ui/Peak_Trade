#!/usr/bin/env bash
# Pipeline smoke: PR-BG consumes PR-BJ artifact, then PR-BJ with higher event density.
# Usage: PROFILE=btc_momentum DURATION_MIN=120 ./scripts/ops/run_pipeline_smoke_prbg_prbj.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "GIT-KONTEXT: main (pipeline smoke: PR-BG consumes PR-BJ artifact)"
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status -sb

START_BG="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
gh workflow run prbg-execution-evidence.yml --ref main

RUN_BG=""
for i in $(seq 1 30); do
  RUN_BG="$(gh run list --workflow prbg-execution-evidence.yml --branch main --limit 20 --json databaseId,createdAt,status | jq --arg start "$START_BG" -r '.[] | select(.createdAt >= $start) | .databaseId' | head -n 1 || true)"
  if [ -n "${RUN_BG}" ]; then break; fi
  sleep 2
done
echo "RUN_BG=${RUN_BG}"
test -n "${RUN_BG}"

gh run watch "${RUN_BG}" || true

OUT_BG="out/ops/prbg_smoke_${RUN_BG}"
rm -rf "${OUT_BG}" || true
mkdir -p "${OUT_BG}"
gh run download "${RUN_BG}" --dir "${OUT_BG}" >/dev/null 2>&1 || true

python3 - <<PY
from pathlib import Path
import json
base=Path("out/ops/prbg_smoke_${RUN_BG}")
p=None
for cand in base.rglob("execution_evidence.json"):
    p=cand; break
print("execution_evidence_json:", p)
obj=json.loads(p.read_text(encoding="utf-8"))
print("status:", obj.get("status"))
print("sample_size:", obj.get("sample_size"))
print("anomaly_count:", obj.get("anomaly_count"))
print("error_count:", obj.get("error_count"))
PY

echo "GIT-KONTEXT: main (increase event density: PR-BJ longer duration + different profile)"
PROFILE="${PROFILE:-btc_momentum}"
DURATION_MIN="${DURATION_MIN:-120}"
echo "PROFILE=${PROFILE} DURATION_MIN=${DURATION_MIN}"

START_BJ="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
gh workflow run prbj-testnet-exec-events.yml --ref main -f profile="${PROFILE}" -f duration_min="${DURATION_MIN}"

RUN_BJ=""
for i in $(seq 1 30); do
  RUN_BJ="$(gh run list --workflow prbj-testnet-exec-events.yml --branch main --limit 20 --json databaseId,createdAt,status | jq --arg start "$START_BJ" -r '.[] | select(.createdAt >= $start) | .databaseId' | head -n 1 || true)"
  if [ -n "${RUN_BJ}" ]; then break; fi
  sleep 2
done
echo "RUN_BJ=${RUN_BJ}"
test -n "${RUN_BJ}"

gh run watch "${RUN_BJ}" || true

OUT_BJ="out/ops/prbj_dense_${RUN_BJ}"
rm -rf "${OUT_BJ}" || true
mkdir -p "${OUT_BJ}"
gh run download "${RUN_BJ}" --dir "${OUT_BJ}" >/dev/null 2>&1 || true

JSONL_BJ="$(find "${OUT_BJ}" -type f -name execution_events.jsonl | head -n 1 || true)"
echo "JSONL_BJ=${JSONL_BJ}"
test -n "${JSONL_BJ}"
LINES="$(wc -l < "${JSONL_BJ}" | tr -d ' ')"
echo "PR-BJ lines=${LINES}"
tail -n 40 "${JSONL_BJ}" || true
