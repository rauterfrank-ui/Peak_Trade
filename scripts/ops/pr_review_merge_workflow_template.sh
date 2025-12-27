#!/usr/bin/env bash
# Peak_Trade – Full PR Review → Merge Workflow
# Usage: PR=<number> scripts/ops/pr_review_merge_workflow_template.sh
#        or edit PR= line below

set -euo pipefail
cd ~/Peak_Trade

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
PR="${PR:-}"  # Set via env: PR=259 ./this_script.sh
              # Or edit this line directly: PR=259

# Checks that are allowed to fail (space-separated)
ALLOW_FAIL_CHECKS="${ALLOW_FAIL_CHECKS:-audit}"

# Mergeable retry settings
export MERGEABLE_RETRIES="${MERGEABLE_RETRIES:-5}"
export MERGEABLE_SLEEP_SEC="${MERGEABLE_SLEEP_SEC:-2}"

# Merge method (squash, merge, or rebase)
MERGE_METHOD="${MERGE_METHOD:-squash}"

# ─────────────────────────────────────────────────────────────
# Preflight Checks
# ─────────────────────────────────────────────────────────────
[ -n "$PR" ] || {
  echo "❌ Error: PR number not set."
  echo "Usage: PR=259 $0"
  echo "   or edit the PR= line in this script."
  exit 1
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚦 Peak_Trade – PR #$PR Review → Merge (Ops-safe)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Config:"
echo "  PR:            $PR"
echo "  Allow-fail:    $ALLOW_FAIL_CHECKS"
echo "  Merge method:  $MERGE_METHOD"
echo "  Retries:       $MERGEABLE_RETRIES (${MERGEABLE_SLEEP_SEC}s sleep)"
echo ""

# Working tree check (warning only, doesn't block)
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  Working Tree ist NICHT clean."
  echo "   Files: $(git status --porcelain | wc -l) uncommitted"
  echo "   Review-only nutzt --dirty-ok automatisch."
  echo ""
  DIRTY_FLAG="--dirty-ok"
else
  echo "✅ Working Tree ist clean."
  echo ""
  DIRTY_FLAG=""
fi

# Build allow-fail args
ALLOW_FAIL_ARGS=()
for check in $ALLOW_FAIL_CHECKS; do
  ALLOW_FAIL_ARGS+=(--allow-fail "$check")
done

# ─────────────────────────────────────────────────────────────
# Step 1: Review-Only
# ─────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  REVIEW-ONLY (mit Watch)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
scripts/ops/review_and_merge_pr.sh \
  --pr "$PR" \
  --watch \
  "${ALLOW_FAIL_ARGS[@]}" \
  $DIRTY_FLAG

# ─────────────────────────────────────────────────────────────
# Step 2: Merge
# ─────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  MERGE ($MERGE_METHOD) + Update main"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
scripts/ops/review_and_merge_pr.sh \
  --pr "$PR" \
  --watch \
  "${ALLOW_FAIL_ARGS[@]}" \
  --merge \
  --method "$MERGE_METHOD" \
  --update-main \
  $DIRTY_FLAG

# ─────────────────────────────────────────────────────────────
# Post-Merge Summary
# ─────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Workflow Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Post-Merge Status:"
git status -sb
echo ""
echo "📝 Latest Commit:"
git log -1 --oneline --decorate
echo ""
echo "🎉 PR #$PR successfully merged to main!"
