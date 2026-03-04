#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "GIT-KONTEXT: main (morning one-shot)"
git checkout main >/dev/null
git fetch origin --prune >/dev/null
git pull --ff-only origin main >/dev/null

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="out/ops/morning_one_shot_${TS}"
mkdir -p "$OUT"

echo "1) E2E runner (best-effort)"
if [ -x scripts/ops/run_end_to_end_verification.sh ]; then
  ./scripts/ops/run_end_to_end_verification.sh || true
else
  echo "SKIP: scripts/ops/run_end_to_end_verification.sh missing"
fi

echo "1b) Pull PRBG latest execution evidence (best-effort)"
if [ -x scripts/ops/pull_latest_prbg_execution_evidence.sh ]; then
  ./scripts/ops/pull_latest_prbg_execution_evidence.sh || true
fi

echo "2) Pull PRBI latest + ops_status verdict"
if [ -x scripts/ops/pull_latest_prbi_scorecard.sh ]; then
  ./scripts/ops/pull_latest_prbi_scorecard.sh || true
fi

OPS_EXIT=0
if [ -x scripts/ops/ops_status.sh ]; then
  ./scripts/ops/ops_status.sh || OPS_EXIT=$?
fi

echo "ops_status_exit=${OPS_EXIT}" > "${OUT}/ops_status_exit.txt"

PRBI_JSON="$(find out/ops/prbi_latest -type f -name live_pilot_scorecard.json 2>/dev/null | head -n 1 || true)"
PRBI_DECISION="__MISSING__"
PRBI_SCORE="__MISSING__"
if test -n "${PRBI_JSON}"; then
  PRBI_DECISION="$(python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBI_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print(o.get("decision","__MISSING__"))
PY2
  )"
  PRBI_SCORE="$(python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBI_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print(o.get("score","__MISSING__"))
PY2
  )"
fi

PRBG_EVID_JSON="$(find out/ops/prbg_latest -type f -name execution_evidence.json 2>/dev/null | head -n 1 || true)"
if test -z "${PRBG_EVID_JSON}"; then
  PRBG_EVID_JSON="$(find out/ops -maxdepth 5 -type f -name execution_evidence.json 2>/dev/null | xargs ls -t 2>/dev/null | head -n 1 || true)"
fi
PRBG_SAMPLE_SIZE="__MISSING__"
PRBG_STATUS="__MISSING__"
PRBG_ANOMALY_COUNT="__MISSING__"
PRBG_ERROR_COUNT="__MISSING__"
if test -n "${PRBG_EVID_JSON}"; then
  PRBG_SAMPLE_SIZE="$(python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBG_EVID_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print(o.get("sample_size","__MISSING__"))
PY2
  )"
  PRBG_STATUS="$(python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBG_EVID_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print(o.get("status","__MISSING__"))
PY2
  )"
  PRBG_ANOMALY_COUNT="$(python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBG_EVID_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print(o.get("anomaly_count","__MISSING__"))
PY2
  )"
  PRBG_ERROR_COUNT="$(python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBG_EVID_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print(o.get("error_count","__MISSING__"))
PY2
  )"
fi

DONE="out/ops/MORNING_ONE_SHOT_DONE_${TS}.txt"
cat > "$DONE" <<EOF
DONE: morning_one_shot
ts_utc: ${TS}
ops_status_exit: ${OPS_EXIT}
prbi_decision: ${PRBI_DECISION}
prbi_score: ${PRBI_SCORE}
prbg_status: ${PRBG_STATUS}
prbg_sample_size: ${PRBG_SAMPLE_SIZE}
prbg_anomaly_count: ${PRBG_ANOMALY_COUNT}
prbg_error_count: ${PRBG_ERROR_COUNT}
evidence_dir: ${OUT}
EOF

python3 - <<PY
import hashlib, pathlib
p=pathlib.Path("${DONE}")
h=hashlib.sha256(p.read_bytes()).hexdigest()
p2=p.with_suffix(p.suffix+".sha256")
p2.write_text(f"{h}  {p.name}\n", encoding="utf-8")
print("WROTE", p)
print("WROTE", p2)
PY

echo "3) Append DONE to local registry (best-effort, untracked)"
if [ -f "${DONE}" ] && [ -x scripts/ops/append_done_registry.py ]; then
  python3 scripts/ops/append_done_registry.py --done "${DONE}" --sha256-ok true >/dev/null 2>&1 || true
fi

echo "DONE=${DONE}"
exit "${OPS_EXIT}"
