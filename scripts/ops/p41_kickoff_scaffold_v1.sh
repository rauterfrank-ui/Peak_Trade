#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/ops/p41_kickoff_scaffold_v1.sh <phase> <slug> [--branch <branch>] [--ts <UTC_YYYYMMDDTHHMMSSZ>] [--no-branch]

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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --ts) TS="${2:-}"; shift 2 ;;
    --no-branch) DO_BRANCH="no"; shift 1 ;;
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
