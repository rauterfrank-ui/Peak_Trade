#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# -------------------------
# Agent 0 — Preflight
# -------------------------
git checkout main
git fetch origin --prune
git reset --hard origin/main
git status -sb

# -------------------------
# Agent 1 — Create P61 evidence scaffold (idempotent)
# -------------------------
TS="$(date -u +%Y%m%dT%H%M%SZ)"
PHASE="p61"
SLUG="online-readiness-contract-v1"
EVI="out/ops/${PHASE}_${SLUG}_${TS}"
mkdir -p "${EVI}"

cat > "${EVI}/P61_BASELINE.txt" <<EOF
branch=
base_main=$(git rev-parse HEAD)
work_start_utc=${TS}
phase=${PHASE}
slug=${SLUG}
EOF

cat > "${EVI}/P61_TASK.md" <<'EOF'
# P61 — online-readiness-contract-v1

## Goal
Define what "ONLINE" means operationally without enabling live/record:
- deterministic paper/shadow readiness run
- evidence pack only when out_dir is set
- deny live/record by default

## Acceptance
- tests pass
- ruff format/check pass
- paper/shadow only (PermissionError for live/record)
- PR + auto-merge + closeout evidence + tarball
EOF

# Optional breadcrumb (ndjson format)
python3 -c "
import json,sys
ts='${TS}'
evi='${EVI}'
print(json.dumps({'ts':ts,'event':'p61_scaffold_written','detail':f'evi={evi}'}, ensure_ascii=False))
" >> "${EVI}/P61_WORKLOG.ndjson"

# -------------------------
# Agent 2 — Feature branch (only if you're not already on one)
# -------------------------
BR="feat/${PHASE}-${SLUG}"
git checkout -b "${BR}" 2>/dev/null || git checkout "${BR}"

# -------------------------
# Agent 3 — Add/commit P61 changes (only if not already committed)
# -------------------------
python3 -m ruff format src/ops/p61 tests/p61
python3 -m ruff check src/ops/p61 tests/p61
python3 -m pytest -q tests/p61

git add \
  src/ops/p61 \
  tests/p61 \
  docs/ops/ai/online_readiness_runbook_v1.md \
  docs/analysis/p61/README.md \
  scripts/ops/p61_full_workflow.sh

# Commit only if there is something staged
if ! git diff --cached --quiet; then
  git commit -m "feat(p61): online readiness contract v1 (paper/shadow only)"
fi

git push -u origin HEAD

# -------------------------
# Agent 4 — PR + Auto-merge + Watch
# -------------------------
./scripts/ops/gh_tls_wrap.sh pr create --fill || true
PR="$(./scripts/ops/gh_tls_wrap.sh pr list --head "${BR}" --json number --jq '.[0].number')"

# Ensure auto-merge is on (squash + delete)
./scripts/ops/gh_tls_wrap.sh pr merge "${PR}" --auto --squash --delete-branch || true

# Watch + retrigger-on-waiting (canonical)
./scripts/ops/pr_ops_v1.sh "${PR}" --watch --retrigger-on-waiting

# -------------------------
# Agent 5 — Closeout + Bundle
# -------------------------
./scripts/ops/pr_ops_v1.sh "${PR}" --closeout --bundle

# -------------------------
# Agent 6 — Repo clean baseline pin
# -------------------------
EVI2="out/ops/repo_clean_baseline_${TS}/"
mkdir -p "${EVI2}"
git status -sb > "${EVI2}/STATUS.txt"
git rev-parse HEAD > "${EVI2}/MAIN_HEAD.txt"
git log -n 10 --oneline --decorate > "${EVI2}/LOG10.txt"
./scripts/ops/gh_tls_wrap.sh pr list --state open --json number,title,headRefName > "${EVI2}/OPEN_PRS.json"

# SHA256SUMS (portable: no -print0/-z for macOS sort)
find "${EVI2}" -maxdepth 1 -type f ! -name 'SHA256SUMS.txt' \
  | LC_ALL=C sort \
  | while IFS= read -r f; do shasum -a 256 "$f"; done > "${EVI2}/SHA256SUMS.txt"

BUNDLE="out/ops/repo_clean_baseline_${TS}.bundle.tgz"
tar -czf "${BUNDLE}" "${EVI2%/}"
shasum -a 256 "${BUNDLE}" > "${BUNDLE}.sha256"

PIN="out/ops/REPO_CLEAN_BASELINE_DONE.txt"
cat > "${PIN}" <<EOF
REPO_CLEAN_BASELINE_DONE OK
timestamp_utc=${TS}
main_head=$(git rev-parse HEAD)
evi=${EVI2%/}
bundle=${BUNDLE}
bundle_sha256=$(cut -d' ' -f1 "${BUNDLE}.sha256")
EOF
shasum -a 256 "${PIN}" > "${PIN}.sha256"

echo "OK: P61 PR merged + closeout + baseline pin. PR=${PR} evi=${EVI}"
