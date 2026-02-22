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
echo "DONE"
