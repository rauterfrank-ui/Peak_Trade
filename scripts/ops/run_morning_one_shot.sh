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

echo "2) Pull PRBI latest + ops_status verdict"
if [ -x scripts/ops/pull_latest_prbi_scorecard.sh ]; then
  ./scripts/ops/pull_latest_prbi_scorecard.sh || true
fi

OPS_EXIT=0
if [ -x scripts/ops/ops_status.sh ]; then
  ./scripts/ops/ops_status.sh || OPS_EXIT=$?
fi

echo "ops_status_exit=${OPS_EXIT}" > "${OUT}/ops_status_exit.txt"

DONE="out/ops/MORNING_ONE_SHOT_DONE_${TS}.txt"
cat > "$DONE" <<EOF
DONE: morning_one_shot
ts_utc: ${TS}
ops_status_exit: ${OPS_EXIT}
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

echo "DONE=${DONE}"
exit "${OPS_EXIT}"
