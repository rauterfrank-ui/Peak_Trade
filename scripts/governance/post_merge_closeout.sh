#!/usr/bin/env bash
# Run this AFTER you have merged a PR in the browser.
# Usage: ./scripts/governance/post_merge_closeout.sh [optional: PR branch name for cleanup]
# (This version: syncs main, cleans up a hardcoded PR branch; for --branch/arg parsing see hardened variant.)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "[Phase 1] Fetch (best-effort; may fail offline)"
git fetch origin --prune --tags || echo "WARN: git fetch failed (offline/blocked). Continuing with local refs."
git checkout main
git pull --ff-only origin main || {
  if [ -z "$(git status --porcelain)" ]; then
    echo "WARN: pull --ff-only failed (diverged); resetting to origin/main"
    git reset --hard origin/main
  else
    echo "ERROR: working tree dirty; refusing reset. Stash/commit first." >&2
    exit 1
  fi
}

# remove local PR branch (if present) — default branch name; override by editing or use wrapper with args
PR_BRANCH="${1:-governance/safe-delete-branches-dryrun}"
if git show-ref --verify --quiet "refs/heads/${PR_BRANCH}"; then
  git branch -d "${PR_BRANCH}" 2>/dev/null || git branch -D "${PR_BRANCH}"
fi
git push origin --delete "${PR_BRANCH}" 2>/dev/null || true

echo "--- Post-merge dry-run: DELETE_SAFE candidates ---"
mkdir -p out/ops
./scripts/governance/safe_delete_merged_branches.sh --dry-run | tee out/ops/safe_delete_merged_branches.postmerge.dryrun.log
echo "DONE"
