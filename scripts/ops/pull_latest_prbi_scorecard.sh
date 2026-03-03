set -euo pipefail

echo "GIT-KONTEXT: main (pull latest PR-BI live pilot scorecard artifact into out/ops/prbi_latest)"

OUT="out/ops/prbi_latest"
rm -rf "${OUT}" || true
mkdir -p "${OUT}"

RUN_ID="$(gh run list --workflow prbi-live-pilot-scorecard.yml --branch main --limit 10 --json databaseId,status,conclusion,createdAt,event --jq '.[] | select(.status=="completed") | select(.conclusion=="success") | .databaseId' | head -n 1)"
echo "RUN_ID=${RUN_ID}"
test -n "${RUN_ID}"

gh run download "${RUN_ID}" --dir "${OUT}" >/dev/null 2>&1 || true

P_JSON="$(find "${OUT}" -type f -name live_pilot_scorecard.json | head -n 1 || true)"
echo "live_pilot_scorecard.json=${P_JSON}"
test -n "${P_JSON}"

python3 - <<PY
import json
from pathlib import Path
p=Path("${P_JSON}")
o=json.loads(p.read_text(encoding="utf-8"))
print("decision:", o.get("decision"))
print("score:", o.get("score"))
print("hard_blocks:", o.get("hard_blocks") or [])
print("warnings:", o.get("warnings") or [])
PY

echo "OK: updated ${OUT}"
