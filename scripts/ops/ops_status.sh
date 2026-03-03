set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "${REPO_ROOT}"

python3 -m compileall -q scripts/ci scripts/ops tests >/dev/null 2>&1 || true

echo "GIT:"
git status -sb

echo ""
echo "PR-K (status report generator contract + health summary):"
uv run ruff format --check
uv run ruff check .
uv run pytest -q tests/ci/test_prk_status_report_contract.py tests/ci/test_prr_prj_status_staleness.py tests/ci/test_prs_prk_health_summary.py

echo ""
echo "PR-U (required checks drift detector):"
uv run pytest -q tests/ci/test_pru_required_checks_drift_detector.py
python3 scripts/ci/required_checks_drift_detector.py

echo ""
echo "PR-O (nightly selfcheck workflow file YAML parse):"
python3 - <<'PY'
import yaml
yaml.safe_load(open(".github/workflows/pro-prk-nightly-selfcheck.yml","r",encoding="utf-8"))
print("PRO_YAML_OK")
yaml.safe_load(open(".github/workflows/prk-prj-status-report.yml","r",encoding="utf-8"))
print("PRK_YAML_OK")
PY

echo ""
echo "== PR-BI (Live Pilot Scorecard) =="
PRBI_JSON_CANDIDATE=""
if test -f "out/ops/prbi_latest/live_pilot_scorecard/live_pilot_scorecard.json"; then
  PRBI_JSON_CANDIDATE="out/ops/prbi_latest/live_pilot_scorecard/live_pilot_scorecard.json"
else
  PRBI_JSON_CANDIDATE="$(find out/ops -type f -name live_pilot_scorecard.json -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -n 1 || true)"
fi
if test -z "${PRBI_JSON_CANDIDATE}"; then
  echo "PR-BI: SKIP (no local live_pilot_scorecard.json found)."
  echo "  Hint: run PR-BI and download artifacts, then re-run ops_status:"
  echo "    gh workflow run prbi-live-pilot-scorecard.yml --ref main"
  echo "    gh run list --workflow prbi-live-pilot-scorecard.yml --branch main --limit 5"
else
  echo "PR-BI json: ${PRBI_JSON_CANDIDATE}"
  python3 - <<PY2
import json
from pathlib import Path
p=Path("${PRBI_JSON_CANDIDATE}")
o=json.loads(p.read_text(encoding="utf-8"))
dec=o.get("decision")
score=o.get("score")
hb=o.get("hard_blocks") or []
warn=o.get("warnings") or []
print("decision:", dec)
print("score:", score)
print("hard_blocks:", hb)
print("warnings:", warn)
if dec != "READY_FOR_LIVE_PILOT":
    raise SystemExit(2)
if hb:
    raise SystemExit(2)
PY2
  echo "PR-BI: READY_FOR_LIVE_PILOT ✓"
fi

echo ""
echo "DONE"
