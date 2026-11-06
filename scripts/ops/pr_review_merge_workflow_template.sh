#!/usr/bin/env bash
# Peak_Trade – Full PR Review → Merge Workflow
# Usage: [PR=<number>|PR_NUM=<number>|PR_NUMBER=<number>] scripts/ops/pr_review_merge_workflow_template.sh [--help|-h]
#
#   PR / PR_NUM / PR_NUMBER:  Optional PR number (aliases supported)
#   --help / -h:               Show this help and exit
#
#   If no PR is set/found, runs in Pre-PR mode (local validation only).
#   Auto-detects PR from current branch via 'gh pr view' if not specified.

set -euo pipefail

# Help must exit (no execution)
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Peak_Trade – PR Review → Merge (Ops-safe)

USAGE
  PR=<number>     scripts/ops/pr_review_merge_workflow_template.sh
  PR_NUM=<number> scripts/ops/pr_review_merge_workflow_template.sh   (alias)
  PR_NUMBER=<number> scripts/ops/pr_review_merge_workflow_template.sh (alias)

FLAGS
  -h, --help      Show this help and exit (no execution).

BEHAVIOR
  • If PR is set (or auto-detected for the current branch), the script runs PR operations.
  • If no PR is set/found, the script runs in Pre-PR mode and skips GitHub PR operations.

EXAMPLES
  PR=123 scripts/ops/pr_review_merge_workflow_template.sh
  PR_NUM=123 scripts/ops/pr_review_merge_workflow_template.sh
  scripts/ops/pr_review_merge_workflow_template.sh   # Pre-PR mode (if no PR found)

NOTES
  • PR is expected via env var PR (primary). PR_NUM / PR_NUMBER are accepted aliases.
  • In Pre-PR mode, PR steps are skipped and logged as "skipping: gh pr ...".

EXIT CODES
  0  Success (including --help).
  2  Invalid PR value (non-numeric when explicitly provided).

EOF
  exit 0
fi

cd ~/Peak_Trade

# -----------------------------
# PR number input (optional + compat)
# -----------------------------
PR="${PR:-${PR_NUM:-${PR_NUMBER:-}}}"

# Auto-resolve PR for current branch if not provided
if [[ -z "${PR}" ]] && command -v gh >/dev/null 2>&1; then
  PR="$(gh pr view --json number --jq .number 2>/dev/null || true)"
fi

# Validate if set
if [[ -n "${PR}" && ! "${PR}" =~ ^[0-9]+$ ]]; then
  echo "❌ Error: PR must be numeric if set (got: '${PR}')." >&2
  exit 2
fi

PRE_PR_MODE="false"
if [[ -z "${PR}" ]]; then
  PRE_PR_MODE="true"
fi

# -----------------------------
# gh pr wrapper (skip in pre-pr mode)
# -----------------------------
gh_pr() {
  if [[ "${PRE_PR_MODE}" == "true" ]]; then
    echo "↪️  Pre-PR mode: skipping: gh pr $*"
    return 0
  fi
  command gh pr "$@"
}

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
# Header
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -n "${PR:-}" ]]; then
  echo "🚦 Peak_Trade – PR #${PR} Review → Merge (Ops-safe)"
else
  echo "🚦 Peak_Trade – Pre-PR Review → Merge (Ops-safe)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Config:"
echo "  PR:            ${PR:-<none, pre-PR mode>}"
echo "  Pre-PR mode:   ${PRE_PR_MODE}"
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
if [[ "${PRE_PR_MODE}" == "true" ]]; then
  echo "1️⃣  LOCAL VALIDATION (pre-PR mode)"
else
  echo "1️⃣  REVIEW-ONLY (mit Watch)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "${PRE_PR_MODE}" == "true" ]]; then
  # Pre-PR mode: Run local checks only (no --pr flag)
  scripts/ops/review_and_merge_pr.sh \
    --watch \
    "${ALLOW_FAIL_ARGS[@]}" \
    $DIRTY_FLAG
else
  # Normal PR mode
  scripts/ops/review_and_merge_pr.sh \
    --pr "$PR" \
    --watch \
    "${ALLOW_FAIL_ARGS[@]}" \
    $DIRTY_FLAG
fi

# ─────────────────────────────────────────────────────────────
# Step 2: Merge (only in PR mode)
# ─────────────────────────────────────────────────────────────
if [[ "${PRE_PR_MODE}" == "false" ]]; then
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
fi

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Workflow Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Status:"
git status -sb
echo ""
echo "📝 Latest Commit:"
git log -1 --oneline --decorate
echo ""

if [[ "${PRE_PR_MODE}" == "true" ]]; then
  echo "✅ Pre-PR validation complete! Ready to create PR."
else
  echo "🎉 PR #$PR successfully merged to main!"
fi
