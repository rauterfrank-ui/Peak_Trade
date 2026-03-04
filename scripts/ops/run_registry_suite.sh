#!/usr/bin/env bash
set -euo pipefail

cd "$(cd "$(dirname "$0")/../.." && pwd)"

REGISTRY="out/ops/registry/morning_one_shot_done_registry.jsonl"
OUTDIR="out/ops/registry/reports"

RUN_ONE_SHOT="${RUN_ONE_SHOT:-false}"

echo "GIT-KONTEXT: main (run_registry_suite)"
echo "RUN_ONE_SHOT=${RUN_ONE_SHOT}"
echo "REGISTRY=${REGISTRY}"
echo "OUTDIR=${OUTDIR}"

STRICT_ALERTS="${STRICT_ALERTS:-false}"
echo "STRICT_ALERTS=${STRICT_ALERTS}"

mkdir -p "${OUTDIR}"

if [ "${RUN_ONE_SHOT}" = "true" ]; then
  if [ -x "./scripts/ops/run_morning_one_shot.sh" ]; then
    ./scripts/ops/run_morning_one_shot.sh
  fi
fi

test -f "${REGISTRY}"

python3 scripts/ops/registry_trend_report.py --limit 30 --outdir "${OUTDIR}"
python3 scripts/ops/registry_weekly_digest.py --days 7 --outdir "${OUTDIR}"
python3 scripts/ops/registry_monthly_digest.py --days 30 --outdir "${OUTDIR}"

python3 scripts/ops/registry_alerts_gate.py --registry "${REGISTRY}" --out "${OUTDIR}/alerts_latest.txt" || RC=$?
RC="${RC:-0}"
if [ "${STRICT_ALERTS}" = "true" ] && [ "${RC}" -ne 0 ]; then
  echo "FAIL: alerts present (STRICT_ALERTS=true)"
  exit "${RC}"
fi

echo ""
echo "OK: wrote"
ls -la "${OUTDIR}" | tail -n 50
