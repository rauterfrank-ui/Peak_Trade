#!/usr/bin/env bash
# multi-agent:noop_branch_cleanup_after_merge
# Clean up a no-op branch (identical to main) after merge: prove identity, delete local + remote.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 0) Prove branch is identical to main (local + remote)
git fetch origin --prune
git checkout docs/runbook-index-new-listings
git rev-parse --short HEAD
git rev-parse --short main
MB="$(git merge-base main HEAD)"
echo "merge-base(main,HEAD) = $(git rev-parse --short "$MB")"
test "$(git rev-parse main)" = "$(git rev-parse HEAD)" && echo "OK: HEAD == main" || echo "DIFF: HEAD != main"
git diff --name-status main...HEAD || true

git rev-parse --short origin/main origin/docs/runbook-index-new-listings
git diff --name-status origin/main...origin/docs/runbook-index-new-listings || true

# 1) Delete local branch
git checkout main
git branch -D docs/runbook-index-new-listings || true

# 2) Delete remote branch (no-op branch)
git push origin --delete docs/runbook-index-new-listings || true

# 3) Final sync + verify index entry still present on main
git pull --ff-only origin main
rg -n "## Research & New Listings|new_listings_crawler_runbook\\.md" docs/ops/runbooks/README.md

# __REF_PARSE_HELPERS__

ref_soft() {
  local ref="$1"
  echo "$ref = $(git rev-parse --short "$ref" 2>/dev/null || echo MISSING)"
}

ref_hard() {
  local ref="$1"
  git rev-parse --short "$ref" >/dev/null
  echo "$ref OK"
}
