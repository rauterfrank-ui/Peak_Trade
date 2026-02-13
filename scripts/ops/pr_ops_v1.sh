#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/ops/pr_ops_v1.sh <PR_NUM> [--watch] [--retrigger-on-waiting] [--closeout] [--bundle]
Defaults:
  --watch --retrigger-on-waiting --closeout --bundle
Notes:
  - Retrigger happens ONLY when required checks contain "Expected — Waiting for status to be reported" (or similar EXPECTED/WAITING states).
  - Uses gh; if you have TLS wrapper, run: alias gh='scripts/ops/gh_tls_wrap.sh'
USAGE
}

if [[ "${1:-}" == "" || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 1; fi
PR="${1}"
shift || true

WATCH=1
RETRIGGER=1
CLOSEOUT=1
BUNDLE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --watch) WATCH=1 ;;
    --no-watch) WATCH=0 ;;
    --retrigger-on-waiting) RETRIGGER=1 ;;
    --no-retrigger) RETRIGGER=0 ;;
    --closeout) CLOSEOUT=1 ;;
    --no-closeout) CLOSEOUT=0 ;;
    --bundle) BUNDLE=1 ;;
    --no-bundle) BUNDLE=0 ;;
    *) echo "ERR: unknown arg: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

need_gh() { command -v gh >/dev/null 2>&1 || { echo "ERR: gh not found" >&2; exit 3; }; }
need_git() { command -v git >/dev/null 2>&1 || { echo "ERR: git not found" >&2; exit 3; }; }

need_gh
need_git

TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/pr${PR}_ops_v1_${TS}"
mkdir -p "$EVI"

# Snapshot
gh pr view "$PR" --json number,title,state,url,mergedAt,mergeCommit,headRefName,baseRefName,mergeStateStatus > "$EVI/PR_VIEW_PRE.json" 2>/dev/null || true
gh pr checks "$PR" --json name,state,link > "$EVI/PR_CHECKS_PRE.json" 2>/dev/null || true

# Watch required checks
if [[ "$WATCH" -eq 1 ]]; then
  gh pr checks "$PR" --watch --required 2>/dev/null || true
fi

# Retrigger once if any check is EXPECTED/WAITING (required-context reporting hole)
if [[ "$RETRIGGER" -eq 1 ]]; then
  WAITING_REQ="$(gh pr checks "$PR" --json name,state --jq '[.[] | select(.state|test("EXPECTED|WAITING";"i")) | .name] | length' 2>/dev/null || echo 0)"
  echo "WAITING_REQUIRED_COUNT=${WAITING_REQ}" | tee "$EVI/WAITING_REQUIRED_COUNT.txt"

  if [[ "${WAITING_REQ}" -gt 0 ]]; then
    BR="$(gh pr view "$PR" --json headRefName --jq .headRefName)"
    echo "RETRIGGER_ONCE branch=${BR}" | tee "$EVI/RETRIGGER.txt"
    git fetch origin --prune
    git checkout "$BR"
    git pull --ff-only origin "$BR"
    git status --porcelain | awk 'NF{exit 9}' || { echo "ERR: working tree not clean; abort retrigger" >&2; exit 9; }
    git commit --allow-empty -m "ci: retrigger required PR checks (synchronize)"
    git push origin HEAD
    gh pr checks "$PR" --watch --required 2>/dev/null || true
  fi
fi

# Closeout if merged
gh pr view "$PR" --json state,mergedAt,mergeCommit --jq '{state,mergedAt,mergeCommit}' > "$EVI/PR_VIEW_POST_MIN.json" 2>/dev/null || true
STATE="$(jq -r '.state' "$EVI/PR_VIEW_POST_MIN.json" 2>/dev/null || echo OPEN)"
MERGED_AT="$(jq -r '.mergedAt' "$EVI/PR_VIEW_POST_MIN.json" 2>/dev/null || echo null)"

if [[ "$CLOSEOUT" -eq 1 && ( "$STATE" == "MERGED" || "$MERGED_AT" != "null" ) ]]; then
  git checkout main
  git fetch origin --prune
  # Use reset --hard to avoid "Cannot fast-forward to multiple branches" when upstream ambiguous
  git reset --hard origin/main
  git status -sb > "$EVI/GIT_STATUS.txt"
  git rev-parse HEAD > "$EVI/MAIN_HEAD.txt"
  git log -n 12 --oneline --decorate > "$EVI/MAIN_LOG12.txt"
  echo "CLOSEOUT_OK pr=${PR} main_head=$(cat "$EVI/MAIN_HEAD.txt") evi=${EVI}" | tee "$EVI/CLOSEOUT_OK.txt"
else
  echo "NOT_MERGED_YET pr=${PR} state=${STATE} mergedAt=${MERGED_AT}" | tee "$EVI/NOT_MERGED_YET.txt"
fi

# Bundle
if [[ "$BUNDLE" -eq 1 ]]; then
  tar -czf "${EVI}.bundle.tgz" "$EVI"
  shasum -a 256 "${EVI}.bundle.tgz" > "${EVI}.bundle.tgz.sha256"
fi

echo "PR_OPS_V1_DONE pr=${PR} evi=${EVI}"
