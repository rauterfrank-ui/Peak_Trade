#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/ops/p41_kickoff_scaffold_v1.sh <phase> <slug> [--branch <branch>] [--ts <UTC_YYYYMMDDTHHMMSSZ>] [--no-branch] [--with-pr-ops]

Examples:
  scripts/ops/p41_kickoff_scaffold_v1.sh p42 data-ingest-v2
  scripts/ops/p41_kickoff_scaffold_v1.sh p10 new-listings --no-branch

Behavior:
- Creates out/ops/<phase>_<slug>_<ts>/ scaffold files + worklog append helper
- Creates docs/analysis/<phase>/README.md, src/ops/<phase>/, tests/<phase>/test_<phase>_smoke.py
- By default creates/switches to branch feat/<phase>-<slug> unless --no-branch is set
- Refuses to run on a dirty working tree unless PT_ALLOW_DIRTY=YES

Notes:
- <phase> must match: p[0-9][0-9]
- <slug> should be kebab-case
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

PHASE="${1:-}"
SLUG="${2:-}"
shift 2 || true

[[ "${PHASE}" == "--help" || "${PHASE}" == "-h" ]] && {
  usage
  exit 0
}
[[ -z "${PHASE}" || -z "${SLUG}" ]] && {
  usage
  exit 2
}

if [[ ! "${PHASE}" =~ ^p[0-9]{2}$ ]]; then
  die "<phase> must be pNN (e.g. p41)"
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BRANCH="feat/${PHASE}-${SLUG}"
DO_BRANCH="yes"
WITH_PR_OPS="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --ts) TS="${2:-}"; shift 2 ;;
    --no-branch) DO_BRANCH="no"; shift 1 ;;
    --with-pr-ops) WITH_PR_OPS="1"; shift 1 ;;
    -h | --help) usage; exit 0 ;;
    *) die "unknown arg: $1" ;;
  esac
done

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "${ROOT}" ]] || die "not a git repo"
cd "${ROOT}"

if [[ "${PT_ALLOW_DIRTY:-NO}" != "YES" ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    die "working tree not clean. commit/stash or set PT_ALLOW_DIRTY=YES"
  fi
fi

BASE_MAIN="$(git rev-parse origin/main 2>/dev/null || git rev-parse main)"

if [[ "${DO_BRANCH}" == "yes" ]]; then
  git fetch origin --prune >/dev/null 2>&1 || true
  git checkout -B "${BRANCH}" >/dev/null
  git rebase origin/main >/dev/null 2>&1 || true
fi

PHASE_UPPER="$(echo "${PHASE}" | tr '[:lower:]' '[:upper:]')"
OPS_DIR="out/ops/${PHASE}_${SLUG}_${TS}"
mkdir -p "${OPS_DIR}"

cat > "${OPS_DIR}/${PHASE_UPPER}_BASELINE.txt" <<EOF
branch=${BRANCH}
base_main=${BASE_MAIN}
work_start_utc=${TS}
phase=${PHASE}
slug=${SLUG}
EOF

cat > "${OPS_DIR}/${PHASE_UPPER}_TASK.md" <<EOF
# ${PHASE_UPPER} — ${SLUG}

## Goal
<TODO>

## Scope
- IN:
- OUT:

## Plan
1)
2)
3)

## Acceptance
- [ ] tests pass
- [ ] ruff format/check pass
- [ ] PR + auto-merge + closeout evidence + tarball
EOF

: > "${OPS_DIR}/${PHASE_UPPER}_WORKLOG.ndjson"

cat > "${OPS_DIR}/${PHASE}_worklog_append.sh" <<APP
#!/usr/bin/env bash
set -euo pipefail
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
LOG="\${DIR}/${PHASE_UPPER}_WORKLOG.ndjson"
evt="\${1:-}"
detail="\${2:-}"
ts="\$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 - "\$ts" "\$evt" "\$detail" <<'PY' >> "\$LOG"
import json,sys
ts,evt,detail=sys.argv[1],sys.argv[2],sys.argv[3]
print(json.dumps({"ts":ts,"event":evt,"detail":detail}, ensure_ascii=False))
PY
echo "OK: appended \${evt}"
APP
chmod +x "${OPS_DIR}/${PHASE}_worklog_append.sh"

# Optional PR-ops helpers (watch/closeout/required-checks snapshot)
if [[ "${WITH_PR_OPS}" == "1" ]]; then
  SCRIPTS_OPS="scripts/ops"
  mkdir -p "${SCRIPTS_OPS}"

  PR_WATCH="${SCRIPTS_OPS}/${PHASE}_pr_watch.sh"
  cat > "${PR_WATCH}" <<'PRWATCH'
#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/ops/<pNN>_pr_watch.sh <PR_NUM> [--bg]
PR="${1:-}"
MODE="${2:-}"
test -n "${PR}" || { echo "missing PR number" >&2; exit 2; }
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/pr${PR}_watch_${TS}"
mkdir -p "${EVI}"
LOG="/tmp/pr${PR}_watch.log"
PID="/tmp/pr${PR}_watch.pid"
touch "${LOG}"

poll() {
  STATE="$(gh pr view "${PR}" --json state,mergedAt --jq '.state + "|" + (.mergedAt // "")' 2>/dev/null || echo "ERR|")"
  printf "%s %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${STATE}" | tee -a "${LOG}" >/dev/null
  echo "${STATE}"
}

run_watch() {
  for i in $(seq 1 240); do
    OUT="$(poll)"
    if printf "%s" "${OUT}" | grep -q '^MERGED|'; then
      gh pr view "${PR}" --json number,title,state,url,mergeCommit,mergedAt,headRefName,baseRefName,mergeable,mergeStateStatus > "${EVI}/PR_VIEW.json" 2>/dev/null || true
      (gh pr checks "${PR}" 2>/dev/null || true) > "${EVI}/PR_CHECKS.txt"
      git status -sb > "${EVI}/STATUS.txt" 2>/dev/null || true
      git rev-parse HEAD > "${EVI}/HEAD.txt" 2>/dev/null || true
      git log -n 5 --oneline --decorate > "${EVI}/LOG5.txt" 2>/dev/null || true
      shasum -a 256 "${EVI}"/* > "${EVI}/SHA256SUMS.txt" 2>/dev/null || true
      echo "WATCH_OK pr=${PR} evidence_dir=${EVI}" | tee -a "${LOG}" >/dev/null
      return 0
    fi
    sleep 15
  done
  echo "WATCH_TIMEOUT pr=${PR} log=${LOG}" | tee -a "${LOG}" >/dev/null
  return 3
}

if [[ "${MODE}" == "--bg" ]]; then
  (run_watch) &
  echo $! > "${PID}"
  echo "WATCH_BG_OK pid=$(cat "${PID}") log=${LOG}"
  exit 0
fi

run_watch
PRWATCH
  chmod +x "${PR_WATCH}"

  CLOSEOUT="${SCRIPTS_OPS}/${PHASE}_oneshot_closeout.sh"
  cat > "${CLOSEOUT}" <<'CLOSEOUTSH'
#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/ops/<pNN>_oneshot_closeout.sh <PR_NUM>
PR="${1:-}"
test -n "${PR}" || { echo "missing PR number" >&2; exit 2; }
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/pr${PR}_closeout_${TS}"
mkdir -p "${EVI}"

STATE="$(gh pr view "${PR}" --json state --jq .state 2>/dev/null || echo "")"
test "${STATE}" = "MERGED" || { echo "NOT_MERGED_YET pr=${PR} state=${STATE}" >&2; exit 3; }

git checkout main
git fetch origin --prune
git pull --ff-only origin main

gh pr view "${PR}" --json number,title,state,url,mergeCommit,mergedAt,headRefName,baseRefName,mergeable,mergeStateStatus > "${EVI}/PR_VIEW.json" 2>/dev/null || true
(gh pr checks "${PR}" 2>/dev/null || true) > "${EVI}/PR_CHECKS.txt"
git status -sb > "${EVI}/STATUS.txt"
git rev-parse HEAD > "${EVI}/MAIN_HEAD.txt"
git log -n 12 --oneline --decorate > "${EVI}/LOG12.txt"
shasum -a 256 "${EVI}"/* > "${EVI}/SHA256SUMS.txt" 2>/dev/null || true

TARBALL="${EVI}.bundle.tgz"
tar -czf "${TARBALL}" "${EVI}"
shasum -a 256 "${TARBALL}" > "${TARBALL}.sha256"
echo "CLOSEOUT_OK pr=${PR} evidence_dir=${EVI} tarball=${TARBALL} main_head=$(cat "${EVI}/MAIN_HEAD.txt")"
CLOSEOUTSH
  chmod +x "${CLOSEOUT}"

  REQ="${SCRIPTS_OPS}/${PHASE}_required_checks_snapshot.sh"
  cat > "${REQ}" <<'REQSH'
#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/ops/<pNN>_required_checks_snapshot.sh <PR_NUM>
PR="${1:-}"
test -n "${PR}" || { echo "missing PR number" >&2; exit 2; }
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/pr${PR}_required_checks_${TS}"
mkdir -p "${EVI}"

gh pr view "${PR}" --json number,title,state,url,headRefName,baseRefName,mergeable,mergeStateStatus > "${EVI}/PR_VIEW.json" 2>/dev/null || true
(gh pr checks "${PR}" 2>/dev/null || true) > "${EVI}/PR_CHECKS.txt"

BASE="$(jq -r '.baseRefName // "main"' "${EVI}/PR_VIEW.json" 2>/dev/null || echo "main")"
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true)"
if [[ -n "${REPO}" ]]; then
  gh api "repos/${REPO}/branches/${BASE}/protection/required_status_checks" > "${EVI}/REQUIRED_STATUS_CHECKS.json" 2>/dev/null || true
fi

shasum -a 256 "${EVI}"/* > "${EVI}/SHA256SUMS.txt" 2>/dev/null || true
echo "REQ_SNAPSHOT_OK pr=${PR} evidence_dir=${EVI}"
REQSH
  chmod +x "${REQ}"
fi

mkdir -p "docs/analysis/${PHASE}" "src/ops/${PHASE}" "tests/${PHASE}"

if [[ ! -f "docs/analysis/${PHASE}/README.md" ]]; then
  cat > "docs/analysis/${PHASE}/README.md" <<EOF
# ${PHASE_UPPER} — ${SLUG}
EOF
fi

TEST_PATH="tests/${PHASE}/test_${PHASE}_smoke.py"
if [[ ! -f "${TEST_PATH}" ]]; then
  cat > "${TEST_PATH}" <<EOF
def test_${PHASE}_smoke() -> None:
    assert True
EOF
fi

echo "OK: created ${OPS_DIR}"
echo "OK: phase=${PHASE} slug=${SLUG} ts=${TS}"
echo "OK: branch=${BRANCH} (do_branch=${DO_BRANCH})"
