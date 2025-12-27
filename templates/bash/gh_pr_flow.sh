#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# gh_pr_flow.sh — reusable PR workflow helper (git + gh)
#
# Usage (examples):
#   PHASE_TAG=phase2e SLUG=ops-center-ux \
#     PR_TITLE="feat(ops): print stable shadow report paths after successful smoke run" \
#     PR_COMMIT_MSG="feat(ops): print stable shadow report paths after successful smoke run" \
#     VERIFY_CMD='bash scripts/ops/ops_center.sh shadow smoke || true' \
#     ./templates/bash/gh_pr_flow.sh
#
#   # phase2 (no letter)
#   PHASE_TAG=phase2 SLUG=latest-report-convenience ./templates/bash/gh_pr_flow.sh
#
# Branch naming defaults:
#   - Shadow pipeline PRs (SCOPE_PREFIX=shadow + PHASE_TAG set):
#       feat/shadow-${PHASE_TAG}-${SLUG}
#       e.g. feat/shadow-phase2e-ops-center-ux
#   - Non-shadow PRs:
#       <kind>/${SLUG}  where <kind> inferred from PR_COMMIT_MSG/PR_TITLE (feat|fix|docs|chore|...)
#       e.g. chore/gh-pr-flow-existing-pr
#
# Notes:
# - VERIFY_CMD is allowed to fail without aborting the script (if you include "|| true").
# - No temp files; PR body uses heredoc.
# -----------------------------------------------------------------------------

# --- Config (override via env) ------------------------------------------------
PHASE_TAG="${PHASE_TAG:-}"                 # e.g. phase2, phase2d, phase2e (NO dash between 2 and letter)
SLUG="${SLUG:-change-me}"                  # short descriptive slug, e.g. ops-center-ux
SCOPE_PREFIX="${SCOPE_PREFIX:-}"           # e.g. shadow, ops, risk, docs

PR_TITLE="${PR_TITLE:-feat: ${SLUG}}"
PR_COMMIT_MSG="${PR_COMMIT_MSG:-feat: ${SLUG}}"
BRANCH_KIND="${BRANCH_KIND:-}"             # optional explicit kind for non-shadow branches (e.g. chore|docs|fix|feat)

# What to add/commit:
FILES_TO_ADD="${FILES_TO_ADD:-.}"          # "." means all changes; set to a path list if you prefer

# Verification (optional):
RUN_VERIFY="${RUN_VERIFY:-1}"              # 1 = run VERIFY_CMD, 0 = skip
VERIFY_CMD="${VERIFY_CMD:-:}"              # ":" = no-op; example: 'bash scripts/ops/ops_center.sh shadow smoke || true'

# PR options (optional):
PR_LABELS="${PR_LABELS:-}"                 # e.g. "documentation,feat" (comma-separated)
ENABLE_AUTO_MERGE="${ENABLE_AUTO_MERGE:-0}" # 1 = enable --auto merge (requires GH settings)
MERGE_METHOD="${MERGE_METHOD:-squash}"     # squash|merge|rebase
DELETE_BRANCH="${DELETE_BRANCH:-1}"        # 1 = delete branch on merge (if supported)

# --- Helpers ------------------------------------------------------------------
die() { echo "❌ $*" >&2; exit 1; }

infer_kind_from_msg() {
  # Accepts: "chore(ops): ..." -> "chore"
  # Accepts: "docs: ..."      -> "docs"
  # Returns empty string if no match.
  local msg="${1:-}"
  if [[ "$msg" =~ ^([a-zA-Z]+)(\(|:) ]]; then
    echo "${BASH_REMATCH[1],,}"
    return 0
  fi
  echo ""
}

normalize_kind() {
  # Whitelist common conventional-commit kinds; fallback to "feat".
  local k="${1:-}"
  case "$k" in
    feat|fix|docs|chore|refactor|test|ci|perf|build|style) echo "$k" ;;
    *) echo "feat" ;;
  esac
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Command not found: $1"
}

git_clean_check() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    return 0
  fi
  return 1
}

checkout_branch() {
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git checkout "$BRANCH"
    return 0
  fi
  if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
    git checkout -t "origin/$BRANCH"
    return 0
  fi
  git checkout -b "$BRANCH"
}

# Resolve default branch name (unless explicitly provided via BRANCH=...).
resolve_branch_name() {
  if [[ -n "${BRANCH:-}" ]]; then
    return 0
  fi

  # Shadow pipeline naming stays stable and explicit.
  if [[ "${SCOPE_PREFIX:-}" == "shadow" && -n "${PHASE_TAG:-}" ]]; then
    BRANCH="feat/${SCOPE_PREFIX}-${PHASE_TAG}-${SLUG}"
    return 0
  fi

  # Non-shadow: infer branch kind from commit/title, unless BRANCH_KIND is provided.
  local inferred="${BRANCH_KIND:-}"
  if [[ -z "$inferred" ]]; then
    inferred="$(infer_kind_from_msg "$PR_COMMIT_MSG")"
  fi
  if [[ -z "$inferred" ]]; then
    inferred="$(infer_kind_from_msg "$PR_TITLE")"
  fi
  inferred="$(normalize_kind "$inferred")"
  BRANCH="${inferred}/${SLUG}"
}

# --- Main ---------------------------------------------------------------------
need_cmd git

resolve_branch_name

echo "🔧 Branch: $BRANCH"
echo "🧾 Title:  $PR_TITLE"

# Ensure we're inside a git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repository."

# Make sure there is something to commit (optional, but helps avoid empty PRs)
if ! git_clean_check; then
  echo "⚠️  Working tree looks clean (no staged/unstaged diffs)."
  echo "    If that's unexpected, make changes first, then rerun."
fi

# 1) Branch
checkout_branch

# 2) Optional verify step (allowed to fail if user includes '|| true' in VERIFY_CMD)
if [[ "$RUN_VERIFY" == "1" ]]; then
  echo "🧪 Verify: $VERIFY_CMD"
  bash -lc "$VERIFY_CMD"
else
  echo "⏭️  Verify skipped (RUN_VERIFY=0)"
fi

# 3) Commit
echo "➕ git add $FILES_TO_ADD"
git add $FILES_TO_ADD

# Avoid failing on empty commits
if git diff --cached --quiet; then
  echo "⚠️  Nothing staged; skipping commit."
else
  echo "✅ Commit: $PR_COMMIT_MSG"
  git commit -m "$PR_COMMIT_MSG"
fi

# 4) Push
echo "⬆️  Push: origin $BRANCH"
git push -u origin "$BRANCH"

# 5) Create PR (requires gh)
if command -v gh >/dev/null 2>&1; then
  PR_BODY="$(cat <<'EOF'
## Summary
<fill me>

## Why
<fill me>

## Changes
- <fill me>

## Verification
- <fill me>

## Risk
LOW — <fill me>
EOF
)"

  PR_NUM=""
  echo "🧷 Creating PR via gh..."
  GH_ARGS=(pr create --title "$PR_TITLE" --body "$PR_BODY")

  # If an open PR already exists for this head branch, update it instead of failing.
  existing_pr_num="$(gh pr list --head "$BRANCH" --state open --json number --jq '.[0].number' 2>/dev/null || true)"
  if [[ -n "${existing_pr_num:-}" && "${existing_pr_num:-}" != "null" ]]; then
    PR_NUM="$existing_pr_num"
    echo "✅ PR already exists (#$PR_NUM). Updating title/body..."
    gh pr edit "$PR_NUM" --title "$PR_TITLE" --body "$PR_BODY"
  else
    gh "${GH_ARGS[@]}"
    PR_NUM="$(gh pr view --json number --jq '.number' 2>/dev/null || true)"
  fi

  # Apply labels (for both new and existing PR)
  if [[ -n "$PR_LABELS" ]]; then
    IFS=',' read -ra labels <<< "$PR_LABELS"
    for lbl in "${labels[@]}"; do
      lbl_trim="$(echo "$lbl" | xargs)"
      [[ -n "$lbl_trim" ]] && gh pr edit "${PR_NUM:-}" --add-label "$lbl_trim" || true
    done
  fi

  if [[ "$ENABLE_AUTO_MERGE" == "1" ]]; then
    echo "🤖 Enabling auto-merge ($MERGE_METHOD)..."
    AM_ARGS=(pr merge --auto "--$MERGE_METHOD")
    [[ "$DELETE_BRANCH" == "1" ]] && AM_ARGS+=(--delete-branch)
    if [[ -n "${PR_NUM:-}" ]]; then
      gh pr merge "$PR_NUM" --auto "--$MERGE_METHOD" $([[ "$DELETE_BRANCH" == "1" ]] && echo "--delete-branch" || true)
    else
      gh "${AM_ARGS[@]}"
    fi
  else
    echo "ℹ️  Auto-merge not enabled (ENABLE_AUTO_MERGE=0)."
  fi
else
  echo "ℹ️  gh not found; PR not created automatically."
  echo "    Install gh or create the PR via GitHub Web UI."
fi

echo "✅ Done."
