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
