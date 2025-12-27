#!/usr/bin/env bash
# ============================================================
# Peak_Trade: Merge-Log Generator & PR Workflow
# ============================================================
# Erstellt einen kompakten Merge-Log für eine bereits gemergte PR,
# legt ihn in docs/ops/ ab, erstellt eine PR dafür und merged sie
# optional automatisch.
#
# USAGE:
#   bash scripts/ops/create_and_open_merge_log_pr.sh --pr <NUM> [OPTIONS]
#
# EXAMPLES:
#   # Standard: Merge-Log erstellen, PR öffnen, checks watch, auto-merge
#   bash scripts/ops/create_and_open_merge_log_pr.sh --pr 207
#
#   # PR erstellen, aber nicht auto-mergen (manual review)
#   bash scripts/ops/create_and_open_merge_log_pr.sh --pr 207 --no-merge
#
#   # PR erstellen ohne Browser zu öffnen
#   bash scripts/ops/create_and_open_merge_log_pr.sh --pr 207 --no-web
#
#   # Nur PR erstellen, kein Browser, kein Auto-Merge
#   bash scripts/ops/create_and_open_merge_log_pr.sh --pr 207 --no-web --no-merge
#
# REQUIREMENTS:
#   - gh CLI (authenticated)
#   - uv (Python package runner)
#   - Clean working tree
#   - Target PR must be merged
#
# ============================================================

set -euo pipefail

# ============================================================
# Argument Parsing
# ============================================================

PR=""
NO_MERGE=false
NO_WEB=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --pr)
      PR="$2"
      shift 2
      ;;
    --no-merge)
      NO_MERGE=true
      shift
      ;;
    --no-web)
      NO_WEB=true
      shift
      ;;
    *)
      echo "❌ Unknown option: $1"
      echo "Usage: $0 --pr <NUM> [--no-merge] [--no-web]"
      exit 1
      ;;
  esac
done

if [ -z "$PR" ]; then
  echo "❌ Missing required argument: --pr <NUM>"
  echo "Usage: $0 --pr <NUM> [--no-merge] [--no-web]"
  exit 1
fi

# ============================================================
# Safety Checks
# ============================================================

echo "🔍 Running safety checks..."

# Check 1: Are we in a git repo?
if [ ! -d .git ]; then
  echo "❌ Not in a git repository. Please run from Peak_Trade root."
  exit 1
fi

# Check 2: Working tree clean?
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Working tree is not clean. Please commit or stash changes first."
  git status -sb
  exit 1
fi

# Check 3: gh CLI authenticated?
if ! gh auth status &>/dev/null; then
  echo "❌ GitHub CLI not authenticated. Run: gh auth login"
  exit 1
fi

echo "✅ Safety checks passed"

# ============================================================
# PR Metadata & Validation
# ============================================================

echo "📥 Fetching PR #${PR} metadata..."

# Check if PR exists and get its state
if ! PR_DATA=$(gh pr view "$PR" --json state,mergedAt,mergeCommit,title,url,headRefName 2>&1); then
  echo "❌ Failed to fetch PR #${PR}. Does it exist?"
  echo "$PR_DATA"
  exit 1
fi

STATE=$(echo "$PR_DATA" | jq -r .state)
MERGED_AT=$(echo "$PR_DATA" | jq -r .mergedAt)
MERGE_COMMIT=$(echo "$PR_DATA" | jq -r .mergeCommit.oid)
TITLE=$(echo "$PR_DATA" | jq -r .title)
PR_URL=$(echo "$PR_DATA" | jq -r .url)
BRANCH=$(echo "$PR_DATA" | jq -r .headRefName)

# Validate PR is merged
if [ "$STATE" != "MERGED" ]; then
  echo "❌ PR #${PR} is not merged (state: ${STATE})"
  echo "   This script only works with already merged PRs."
  exit 1
fi

if [ "$MERGED_AT" = "null" ] || [ -z "$MERGED_AT" ]; then
  echo "❌ PR #${PR} has no mergedAt timestamp"
  exit 1
fi

if [ "$MERGE_COMMIT" = "null" ] || [ -z "$MERGE_COMMIT" ]; then
  echo "❌ PR #${PR} has no merge commit SHA"
  exit 1
fi

# Extract date (YYYY-MM-DD)
MERGED_DATE=$(echo "$MERGED_AT" | cut -dT -f1)

echo "✅ PR Metadata:"
echo "   PR:           #${PR}"
echo "   Title:        ${TITLE}"
echo "   Branch:       ${BRANCH}"
echo "   Merged:       ${MERGED_DATE}"
echo "   Merge Commit: ${MERGE_COMMIT:0:8}"
echo "   URL:          ${PR_URL}"

# ============================================================
# Create Branch for Merge-Log
# ============================================================

MERGE_LOG_BRANCH="docs/ops-pr${PR}-merge-log"
echo "🌿 Creating branch: ${MERGE_LOG_BRANCH}"
git switch -c "$MERGE_LOG_BRANCH"

# ============================================================
# Generate Merge-Log
# ============================================================

echo "📝 Generating merge log..."

uv run python scripts/ops/create_merge_log.py \
  --pr "$PR" \
  --title "$TITLE" \
  --date "$MERGED_DATE" \
  --commit "$MERGE_COMMIT" \
  --pr-url "$PR_URL" \
  --branch "$BRANCH"

LOGFILE="docs/ops/PR_${PR}_MERGE_LOG.md"

if [ ! -f "$LOGFILE" ]; then
  echo "❌ Expected merge log file not created: ${LOGFILE}"
  exit 1
fi

echo "✅ Merge log created: ${LOGFILE}"

# ============================================================
# Run Guard (non-blocking for legacy violations)
# ============================================================

echo "🛡️  Running ops merge log guard..."

if uv run python scripts/audit/check_ops_merge_logs.py; then
  echo "✅ Guard passed: no violations"
else
  EXIT_CODE=$?
  echo "⚠️  Guard exited with code ${EXIT_CODE}"
  echo "    This may indicate legacy violations in older logs."
  echo "    If the new log (PR #${PR}) looks good, you can proceed."
  echo ""
  read -p "Continue anyway? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted by user"
    git switch main
    git branch -D "$MERGE_LOG_BRANCH" 2>/dev/null || true
    exit 1
  fi
fi

# ============================================================
# Show Diff
# ============================================================

echo "📊 Changes:"
git status -sb
git diff --stat

# ============================================================
# Commit & Push
# ============================================================

echo "💾 Committing changes..."

# Add expected files
git add "$LOGFILE"
[ -f docs/ops/README.md ] && git add docs/ops/README.md
[ -f docs/PEAK_TRADE_STATUS_OVERVIEW.md ] && git add docs/PEAK_TRADE_STATUS_OVERVIEW.md

git commit -m "docs(ops): add PR #${PR} merge log"

echo "🚀 Pushing branch..."
git push -u origin HEAD

# ============================================================
# Create PR for Merge-Log
# ============================================================

echo "📬 Creating PR for merge log..."

CREATE_ARGS=(
  --title "docs(ops): add PR #${PR} merge log"
  --body "Adds compact ops merge log for PR #${PR}."
)

if [ "$NO_WEB" = false ]; then
  CREATE_ARGS+=(--web)
fi

gh pr create "${CREATE_ARGS[@]}"

# Get the newly created PR number
NEW_PR=$(gh pr view --json number -q .number)
echo "✅ Created PR #${NEW_PR}"

# ============================================================
# Optional: Watch Checks & Auto-Merge
# ============================================================

if [ "$NO_MERGE" = false ]; then
  echo "⏳ Watching PR checks..."
  gh pr checks "$NEW_PR" --watch

  echo "🔀 Merging PR #${NEW_PR}..."
  gh pr merge "$NEW_PR" --squash --delete-branch

  echo "✅ PR #${NEW_PR} merged"

  # ============================================================
  # Post-Merge: Update Local Main
  # ============================================================

  echo "🔄 Updating local main branch..."
  git switch main
  git pull --ff-only

  echo "📋 Latest commit on main:"
  git log -1 --oneline
else
  echo "⏭️  Skipping auto-merge (--no-merge flag set)"
  echo "   Review and merge PR #${NEW_PR} manually when ready."
fi

# ============================================================
# Done
# ============================================================

echo ""
echo "✅ DONE"
echo ""
echo "Summary:"
echo "  - Merge log created: ${LOGFILE}"
echo "  - PR created: #${NEW_PR}"
if [ "$NO_MERGE" = false ]; then
  echo "  - PR merged and branch deleted"
  echo "  - Local main updated"
else
  echo "  - PR awaiting review/merge"
  echo "  - Current branch: ${MERGE_LOG_BRANCH}"
fi
