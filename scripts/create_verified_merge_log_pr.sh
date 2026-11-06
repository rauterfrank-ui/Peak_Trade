#!/usr/bin/env bash
#
# create_verified_merge_log_pr.sh — Idempotent verified merge log PR creator
#
# Usage:
#   ./scripts/create_verified_merge_log_pr.sh <PR_NUMBER> [--base BRANCH] [--branch BRANCH]
#
# Examples:
#   ./scripts/create_verified_merge_log_pr.sh 418
#   ./scripts/create_verified_merge_log_pr.sh 420 --base main
#
# Exit codes:
#   0 = success (PR created or already exists)
#   1 = error (missing deps, not in repo, etc.)
#   2 = PR not merged yet (retry after merge)
#
set -euo pipefail

# ============================================================================
# Configuration & Argument Parsing
# ============================================================================

PR_NUM="${1:-}"
BASE_BRANCH="main"
BRANCH=""

if [[ -z "$PR_NUM" ]]; then
    echo "Usage: $0 <PR_NUMBER> [--base BRANCH] [--branch BRANCH]"
    echo ""
    echo "Examples:"
    echo "  $0 418"
    echo "  $0 420 --base main --branch docs/merge-log-pr-420"
    exit 1
fi

shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --base)
            BASE_BRANCH="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Default branch name if not specified
if [[ -z "$BRANCH" ]]; then
    BRANCH="docs/merge-log-pr-${PR_NUM}"
fi

MERGE_LOG_PATH="docs/ops/PR_${PR_NUM}_MERGE_LOG.md"
OPS_README="docs/ops/README.md"

# ============================================================================
# Preflight Checks
# ============================================================================

echo "🔍 Preflight checks..."

# Check git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check gh CLI
if ! command -v gh >/dev/null 2>&1; then
    echo "❌ gh CLI not found (install from https://cli.github.com/)"
    exit 1
fi

# Check python3
if ! python3 -c "import sys, json, subprocess, pathlib" 2>/dev/null; then
    echo "❌ python3 with required modules not available"
    exit 1
fi

echo "✅ All dependencies available"

# ============================================================================
# Check PR State
# ============================================================================

echo ""
echo "🔍 Checking PR #${PR_NUM} state..."

PR_STATE=$(python3 - "$PR_NUM" <<'PY'
import json, subprocess, sys

pr_num = sys.argv[1] if len(sys.argv) > 1 else None
if not pr_num:
    print("❌ PR number not provided")
    sys.exit(1)
try:
    data = subprocess.check_output(
        ["gh", "pr", "view", pr_num, "--json", "state,mergedAt,title,url"],
        text=True,
        stderr=subprocess.DEVNULL
    )
    pr = json.loads(data)

    if pr["state"] != "MERGED":
        print(f"❌ PR #{pr_num} is not merged yet (state: {pr['state']})")
        print(f"   URL: {pr['url']}")
        print(f"   Wait for merge, then re-run this script.")
        sys.exit(2)

    print(f"✅ PR #{pr_num} is merged: {pr['mergedAt']}")
    print(f"   {pr['title']}")
    print(f"   {pr['url']}")

except subprocess.CalledProcessError:
    print(f"❌ PR #{pr_num} not found")
    sys.exit(1)
PY
) || exit $?

echo "$PR_STATE"

# ============================================================================
# Check if merge log PR already exists
# ============================================================================

echo ""
echo "🔍 Checking for existing merge-log PR from branch '${BRANCH}'..."

# Check for existing PR (including merged ones)
EXISTING_PR=$(gh pr list --head "$BRANCH" --state all --json number,url,state --jq '.[0] // empty' 2>/dev/null || true)

if [[ -n "$EXISTING_PR" ]]; then
    PR_NUM_EXISTING=$(echo "$EXISTING_PR" | python3 -c "import sys, json; print(json.load(sys.stdin)['number'])")
    PR_URL=$(echo "$EXISTING_PR" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])")
    PR_STATE=$(echo "$EXISTING_PR" | python3 -c "import sys, json; print(json.load(sys.stdin)['state'])")

    echo "✅ Merge-log PR already exists: #${PR_NUM_EXISTING}"
    echo "   URL: $PR_URL"
    echo "   State: $PR_STATE"

    if [[ "$PR_STATE" == "MERGED" ]]; then
        echo ""
        echo "ℹ️  PR is already merged. Merge log should be in main."
        echo "   View with: gh pr view $PR_URL"
        exit 0
    elif [[ "$PR_STATE" == "OPEN" ]]; then
        echo ""
        echo "ℹ️  PR is open. Wait for review/merge, or update if needed."
        echo "   View with: gh pr view $PR_URL"
        exit 0
    else
        echo ""
        echo "ℹ️  PR is in state: $PR_STATE"
        echo "   View with: gh pr view $PR_URL"
        exit 0
    fi
fi

echo "✅ No existing PR found - will create new one"

# ============================================================================
# Sync base branch
# ============================================================================

echo ""
echo "📥 Syncing base branch '$BASE_BRANCH'..."

git fetch origin "$BASE_BRANCH"
git checkout "$BASE_BRANCH"
git pull --ff-only origin "$BASE_BRANCH"

echo "✅ Base branch synced"

# ============================================================================
# Handle target branch (idempotent)
# ============================================================================

echo ""
echo "🌿 Handling branch '$BRANCH'..."

# Check if branch exists on origin first
if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
    echo "ℹ️  Branch exists on origin - fetching"
    git fetch origin "$BRANCH"

    # Delete local if exists, then checkout from origin
    git branch -D "$BRANCH" 2>/dev/null || true
    git checkout -b "$BRANCH" "origin/$BRANCH"

    echo "ℹ️  Resetting to latest base"
    git reset --hard "origin/$BASE_BRANCH"
elif git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "ℹ️  Branch exists locally only - checking out and resetting"
    git checkout "$BRANCH"
    git reset --hard "$BASE_BRANCH"
else
    echo "✅ Creating new branch"
    git checkout -b "$BRANCH"
fi

# ============================================================================
# Generate merge log content
# ============================================================================

echo ""
echo "📝 Generating merge log content..."

python3 - "$PR_NUM" "$MERGE_LOG_PATH" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

pr_num = sys.argv[1]
merge_log_path = Path(sys.argv[2])

# Fetch PR metadata
try:
    data = subprocess.check_output(
        ["gh", "pr", "view", pr_num, "--json",
         "title,url,mergedAt,mergeCommit,commits,files,additions,deletions,body"],
        text=True
    )
    pr = json.loads(data)
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to fetch PR #{pr_num} metadata", file=sys.stderr)
    sys.exit(1)

# Extract metadata
title = pr.get("title", "")
url = pr.get("url", "")
merged_at = pr.get("mergedAt", "")
merge_commit_oid = (pr.get("mergeCommit") or {}).get("oid", "")[:7]
additions = pr.get("additions", 0)
deletions = pr.get("deletions", 0)

files = [f.get("path", "") for f in (pr.get("files") or []) if f.get("path")]
commits = [
    f"{c.get('oid', '')[:7]} - {c.get('messageHeadline', '')}"
    for c in (pr.get("commits") or [])
]

# Check if file already exists with substantial content
if merge_log_path.exists():
    existing = merge_log_path.read_text(encoding="utf-8")
    # If it already has core metadata, keep it
    if f"PR #{pr_num}" in existing and merged_at in existing and len(existing) > 500:
        print(f"ℹ️  Merge log already exists with content ({len(existing)} bytes)")
        print(f"   Keeping existing: {merge_log_path}")
        sys.exit(0)

# Generate content
content = f"""# PR #{pr_num} — {title}

**Status:** ✅ **MERGED**
**Merged At:** {merged_at}
**Merge Commit:** {merge_commit_oid}
**URL:** {url}

---

## Summary

{pr.get('body', 'No description provided.')[:500]}

## Changes

**Files Changed:** {len(files)}
**Additions:** +{additions}
**Deletions:** -{deletions}

### Commits ({len(commits)})

{chr(10).join(f"- {c}" for c in commits)}

### Files Modified

{chr(10).join(f"- `{f}`" for f in files[:50])}
{f'... and {len(files) - 50} more files' if len(files) > 50 else ''}

## Verification

See PR discussion and CI results at: {url}

## Risk Assessment

See PR description for risk assessment.

---

**Merge Log Generated:** {subprocess.check_output(['date', '-u', '+%Y-%m-%d %H:%M:%S UTC'], text=True).strip()}
**Script:** `scripts/create_verified_merge_log_pr.sh`
"""

# Write file
merge_log_path.parent.mkdir(parents=True, exist_ok=True)
merge_log_path.write_text(content, encoding="utf-8")
print(f"✅ Generated: {merge_log_path}")
print(f"   Size: {len(content)} bytes")
PY

MERGE_LOG_STATUS=$?
if [[ $MERGE_LOG_STATUS -eq 0 ]] && [[ -f "$MERGE_LOG_PATH" ]]; then
    # Check if file was skipped (already exists)
    if grep -q "Keeping existing" <(python3 - "$PR_NUM" "$MERGE_LOG_PATH" 2>&1 <<'PY'
import sys
from pathlib import Path
pr_num = sys.argv[1]
merge_log_path = Path(sys.argv[2])
if merge_log_path.exists():
    existing = merge_log_path.read_text(encoding="utf-8")
    if f"PR #{pr_num}" in existing and len(existing) > 500:
        print("Keeping existing")
PY
    ); then
        MERGE_LOG_SKIPPED=true
    else
        MERGE_LOG_SKIPPED=false
    fi
fi

# ============================================================================
# Patch docs/ops/README.md
# ============================================================================

echo ""
echo "📝 Patching $OPS_README..."

python3 - "$PR_NUM" "$OPS_README" "$MERGE_LOG_PATH" <<'PY'
import sys
from pathlib import Path

pr_num = sys.argv[1]
readme_path = Path(sys.argv[2])
merge_log_rel = sys.argv[3]

# Ensure README exists
if not readme_path.exists():
    print(f"⚠️  {readme_path} not found - creating basic structure")
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(
        f"# Operations Documentation\n\n"
        f"## Verified Merge Logs\n\n",
        encoding="utf-8"
    )

text = readme_path.read_text(encoding="utf-8")

# Build entry
entry = f"- **PR #{pr_num}** → `{merge_log_rel}`"

# Check if already present
if entry in text or f"PR #{pr_num}" in text:
    print(f"✅ README already contains PR #{pr_num} entry")
    sys.exit(0)

# Find or create "Verified Merge Logs" section
header = "## Verified Merge Logs"

if header in text:
    # Insert after header
    parts = text.split(header, 1)
    before, after = parts[0], parts[1]

    # Ensure blank line after header
    after_lines = after.splitlines(keepends=True)
    if after_lines and after_lines[0].strip():
        after_lines.insert(0, "\n")

    # Insert entry after first blank/empty line
    insert_idx = 1 if len(after_lines) > 1 else 0
    after_lines.insert(insert_idx, entry + "\n")

    new_text = before + header + "".join(after_lines)
else:
    # Append section at end
    new_text = text.rstrip() + f"\n\n{header}\n\n{entry}\n"

readme_path.write_text(new_text, encoding="utf-8")
print(f"✅ Added PR #{pr_num} to {readme_path}")
PY

README_STATUS=$?

# ============================================================================
# Check if there are changes to commit
# ============================================================================

echo ""
echo "🔍 Checking for changes..."

if git diff --quiet && git diff --cached --quiet; then
    echo "ℹ️  No changes detected - merge log already up to date"
    echo ""
    echo "✅ Everything is already in place. Nothing to commit."
    exit 0
fi

# Show what changed
echo ""
echo "📊 Changes to commit:"
git status --short

# ============================================================================
# Commit changes
# ============================================================================

echo ""
echo "💾 Committing changes..."

git add "$MERGE_LOG_PATH" "$OPS_README"

git commit -m "docs(ops): add verified merge log for PR #${PR_NUM}

- Add merge log: $MERGE_LOG_PATH
- Update $OPS_README with verified entry

Generated by: scripts/create_verified_merge_log_pr.sh"

echo "✅ Changes committed"

# ============================================================================
# Push branch
# ============================================================================

echo ""
echo "📤 Pushing branch '$BRANCH'..."

git push -u origin "$BRANCH" --force-with-lease

echo "✅ Branch pushed"

# ============================================================================
# Create PR
# ============================================================================

echo ""
echo "🎯 Creating PR..."

PR_URL=$(gh pr create \
  --title "docs(ops): add verified merge log for PR #${PR_NUM}" \
  --body "Adds verified merge log for PR #${PR_NUM}.

## Changes
- Add merge log document: \`$MERGE_LOG_PATH\`
- Update \`$OPS_README\` with verified entry

## Metadata
- Target PR: #${PR_NUM}
- Generated by: \`scripts/create_verified_merge_log_pr.sh\`

## Verification
- [x] Merge log contains PR metadata
- [x] README updated with entry
- [x] Pre-commit hooks passed" 2>&1)

echo "$PR_URL"
echo ""
echo "✅ Done! Merge log PR created."
echo ""
echo "📋 Next steps:"
echo "   - Review: gh pr view --web"
echo "   - Enable auto-merge: gh pr merge --auto --squash --delete-branch"
