#!/usr/bin/env bash
# Run this AFTER you have merged a PR in the browser.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

usage() {
  cat <<'EOF'
Usage:
  post_merge_closeout.sh [<pr_branch>]

Purpose:
  - Sync local main to origin/main, even if histories diverged (e.g., squash-merge).
  - Cleanup local/remote PR branch best-effort.
  - Run safe_delete_merged_branches dry-run for post-merge sanity.

Args:
  <pr_branch>   Optional. Remote/local PR branch name to delete after merge.

Flags:
  -h, --help    Show this help and exit.

Env:
  MAIN_BRANCH=main
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi
if [ -n "${1:-}" ] && ( [ "${1}" = "-" ] || [[ "${1}" == --* ]] ); then
  echo "ERROR: unknown flag: ${1}" >&2
  usage >&2
  exit 2
fi

MAIN_BRANCH="${MAIN_BRANCH:-main}"
PR_BRANCH="${1:-}"

echo "[Phase 1] Fetch (best-effort; may fail offline)"
git fetch origin --prune --tags || echo "WARN: git fetch failed (offline/blocked). Continuing with local refs."
git checkout "${MAIN_BRANCH}"
git pull --ff-only origin "${MAIN_BRANCH}" || {
  if [ -z "$(git status --porcelain)" ]; then
    echo "WARN: pull --ff-only failed (diverged); resetting to origin/${MAIN_BRANCH}"
    git reset --hard "origin/${MAIN_BRANCH}"
  else
    echo "ERROR: working tree dirty; refusing reset. Stash/commit first." >&2
    exit 1
  fi
}

# remove local/remote PR branch only if provided
if [ -n "${PR_BRANCH}" ]; then
  if git show-ref --verify --quiet "refs/heads/${PR_BRANCH}"; then
    git branch -d "${PR_BRANCH}" 2>/dev/null || git branch -D "${PR_BRANCH}"
  fi
  git push origin --delete "${PR_BRANCH}" 2>/dev/null || true
fi

echo "--- Post-merge dry-run: DELETE_SAFE candidates ---"
mkdir -p out/ops
./scripts/governance/safe_delete_merged_branches.sh --dry-run | tee out/ops/safe_delete_merged_branches.postmerge.dryrun.log
echo "DONE"
