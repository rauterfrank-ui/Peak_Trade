set -euo pipefail

cd "$(cd "$(dirname "$0")/../.." && pwd)"

WORKFLOW="prk-prj-status-report.yml"
BRANCH="main"
LIMIT="20"
OUT_DIR="out/ops/prk_dashboard_latest"
RUN_ID=""

usage() {
  echo "usage: fetch_prk_dashboard_artifacts.sh [--run-id ID] [--out-dir DIR] [--workflow FILE] [--branch BRANCH] [--limit N]" >&2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --run-id) RUN_ID="${2:-}"; shift 2;;
    --out-dir) OUT_DIR="${2:-}"; shift 2;;
    --workflow) WORKFLOW="${2:-}"; shift 2;;
    --branch) BRANCH="${2:-}"; shift 2;;
    --limit) LIMIT="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "unknown arg: $1" >&2; usage; exit 2;;
  esac
done

mkdir -p "${OUT_DIR}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_META_JSON="${OUT_DIR}/run_meta_${STAMP}.json"
DL_DIR="${OUT_DIR}/download_${STAMP}"
LATEST_DIR="${OUT_DIR}/latest"

pick_latest_success_run() {
  gh run list --workflow "${WORKFLOW}" --branch "${BRANCH}" --limit "${LIMIT}" \
    --json databaseId,status,conclusion,createdAt,event,url > "${RUN_META_JSON}"

  python3 - <<PY
import json, os
p=os.environ["RUN_META_JSON"]
j=json.load(open(p,"r",encoding="utf-8"))
for r in j:
    if r.get("status")=="completed" and r.get("conclusion")=="success":
        print(r["databaseId"])
        raise SystemExit(0)
print("")
PY
}

if [ -z "${RUN_ID}" ]; then
  echo "Selecting latest successful run for workflow=${WORKFLOW} branch=${BRANCH}"
  RUN_ID="$(RUN_META_JSON="${RUN_META_JSON}" pick_latest_success_run)"
fi

if [ -z "${RUN_ID}" ]; then
  echo "ERROR: no successful completed runs found (workflow=${WORKFLOW} branch=${BRANCH})" >&2
  echo "Hint: gh run list --workflow ${WORKFLOW} --branch ${BRANCH}" >&2
  exit 3
fi

echo "RUN_ID=${RUN_ID}"
mkdir -p "${DL_DIR}"
mkdir -p "${LATEST_DIR}"

echo "Downloading artifacts to ${DL_DIR}"
gh run download "${RUN_ID}" --dir "${DL_DIR}"

echo "Copying dashboard artifacts into ${LATEST_DIR}"
for prefix in prj_status_latest prj_health_summary prj_health_dashboard; do
  find "${DL_DIR}" -name "${prefix}.*" -exec cp -f {} "${LATEST_DIR}/" \; 2>/dev/null || true
done
find "${DL_DIR}" -name "prj_health_dashboard_v1.json" -exec cp -f {} "${LATEST_DIR}/" \; 2>/dev/null || true

echo "Writing SUMMARY.md + SHA256SUMS (local-only)"
SUMMARY="${OUT_DIR}/SUMMARY_${STAMP}.md"
{
  echo "# PR-K Dashboard Fetch Summary"
  echo ""
  echo "- Timestamp (UTC): ${STAMP}"
  echo "- Workflow: ${WORKFLOW}"
  echo "- Branch: ${BRANCH}"
  echo "- Run ID: ${RUN_ID}"
  echo ""
  echo "## Files"
  (cd "${LATEST_DIR}" && ls -la) || true
} > "${SUMMARY}"

if command -v shasum >/dev/null 2>&1; then
  (cd "${LATEST_DIR}" && shasum -a 256 * 2>/dev/null || true) > "${OUT_DIR}/SHA256SUMS_${STAMP}.txt"
fi

echo "DONE:"
echo "  ${LATEST_DIR}"
ls -la "${LATEST_DIR}" || true
