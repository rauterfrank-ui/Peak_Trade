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
