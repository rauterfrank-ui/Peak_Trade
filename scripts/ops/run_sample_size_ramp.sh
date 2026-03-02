#!/usr/bin/env bash
set -euo pipefail

echo "GIT-KONTEXT: main (sample-size ramp driver: PR-BJ -> PR-BG -> PRBE -> PRBI)"
PROFILE="${PROFILE:-btc_momentum}"
DURATION_MIN="${DURATION_MIN:-60}"

WORKDIR="out/ops/sample_size_ramp_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$WORKDIR"

dispatch_and_get_runid() {
  local wf="$1"; shift
  gh workflow run "$wf" --ref main "$@" >/dev/null
  sleep 4
  gh run list --workflow "$wf" --branch main --limit 10 \
    --json databaseId,status,conclusion,createdAt,event \
    --jq '.[0].databaseId'
}

download_run() {
  local rid="$1"
  local out="$2"
  rm -rf "$out" || true
  mkdir -p "$out"
  gh run download "$rid" --dir "$out" >/dev/null 2>&1 || true
}

echo "1) PR-BJ dispatch: profile=${PROFILE} duration_min=${DURATION_MIN}"
RID_BJ="$(dispatch_and_get_runid prbj-testnet-exec-events.yml -f profile="${PROFILE}" -f duration_min="${DURATION_MIN}")"
echo "RID_BJ=${RID_BJ}"
gh run watch "$RID_BJ" --exit-status || true
OUT_BJ="${WORKDIR}/prbj_${RID_BJ}"
download_run "$RID_BJ" "$OUT_BJ"

JSONL="$(find "$OUT_BJ" -type f -name execution_events.jsonl | head -n 1 || true)"
echo "JSONL=${JSONL}"
if test -n "$JSONL"; then
  LINES="$(wc -l < "$JSONL" | tr -d ' ')"
  echo "PR-BJ lines=${LINES}"
  tail -n 20 "$JSONL" || true
else
  echo "WARN: execution_events.jsonl not found in artifact"
  LINES="0"
fi

echo "2) PR-BG dispatch (build evidence from latest available source)"
RID_BG="$(dispatch_and_get_runid prbg-execution-evidence.yml)"
echo "RID_BG=${RID_BG}"
gh run watch "$RID_BG" --exit-status || true
OUT_BG="${WORKDIR}/prbg_${RID_BG}"
download_run "$RID_BG" "$OUT_BG"

P_BG_JSON="$(find "$OUT_BG" -type f -name execution_evidence.json | head -n 1 || true)"
echo "execution_evidence.json=${P_BG_JSON}"
if test -n "$P_BG_JSON"; then
  python3 - <<PY
import json
from pathlib import Path
p=Path("${P_BG_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print("status=", o.get("status"))
print("sample_size=", o.get("sample_size"))
print("anomaly_count=", o.get("anomaly_count"))
print("error_count=", o.get("error_count"))
PY
fi

echo "3) PRBE dispatch"
RID_BE="$(dispatch_and_get_runid prbe-shadow-testnet-scorecard.yml)"
echo "RID_BE=${RID_BE}"
gh run watch "$RID_BE" --exit-status || true
OUT_BE="${WORKDIR}/prbe_${RID_BE}"
download_run "$RID_BE" "$OUT_BE"

echo "4) PRBI dispatch"
RID_BI="$(dispatch_and_get_runid prbi-live-pilot-scorecard.yml)"
echo "RID_BI=${RID_BI}"
gh run watch "$RID_BI" --exit-status || true
OUT_BI="${WORKDIR}/prbi_${RID_BI}"
download_run "$RID_BI" "$OUT_BI"

echo ""
echo "DONE: ${WORKDIR}"
echo "Tip: repeat runs until PRBG sample_size >= 100 and PRBI has no INSUFFICIENT_SAMPLE_SIZE."
