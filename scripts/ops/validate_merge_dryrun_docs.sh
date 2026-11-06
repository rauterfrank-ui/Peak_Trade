#!/usr/bin/env bash
# TOOL/ORT: Terminal (Shell) im Repo ~/Peak_Trade
# ZIEL: Post-Run Checks + typische Fehlerfälle sauber abfangen (Branch exists / gh auth)

set -euo pipefail

REPO="${REPO:-$HOME/Peak_Trade}"
cd "$REPO"

BRANCH="docs/ops-merge-both-prs-dryrun-workflow"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Post-Run Validation: DRY_RUN Workflow Docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "==> Repo status"
git status
echo ""

echo "==> Current branch"
CURRENT_BRANCH=$(git branch --show-current)
echo "Current: $CURRENT_BRANCH"
if [[ "$CURRENT_BRANCH" == "$BRANCH" ]]; then
  echo "✅ On expected branch: $BRANCH"
else
  echo "⚠️  Not on expected branch (expected: $BRANCH, current: $CURRENT_BRANCH)"
fi
echo ""

echo "==> Snippet in README.md"
if grep -q "BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW" docs/ops/README.md; then
  LINE_NUM=$(grep -n "BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW" docs/ops/README.md | cut -d: -f1)
  echo "✅ Found snippet at line $LINE_NUM"
  echo ""
  grep -A 20 "BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW" docs/ops/README.md | head -25
else
  echo "❌ Snippet NOT found in README.md"
fi
echo ""

echo "==> Snippet in MERGE_BOTH_PRS_CHEATSHEET.md"
if grep -q "BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW" docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md; then
  LINE_NUM=$(grep -n "BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW" docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md | cut -d: -f1)
  echo "✅ Found snippet at line $LINE_NUM"
  echo ""
  grep -A 20 "BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW" docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md | head -25
else
  echo "❌ Snippet NOT found in MERGE_BOTH_PRS_CHEATSHEET.md"
fi
echo ""

echo "==> Check for PR"
if gh pr view --web 2>/dev/null; then
  echo "✅ PR found and opened in browser"
else
  echo "⚠️  No PR found (or gh error)"
  echo ""
  echo "If you pushed the branch but haven't created a PR yet:"
  echo ""
  echo "gh pr create \\"
  echo "  --base main \\"
  echo "  --title \"docs(ops): add DRY_RUN → Real Merge workflow\" \\"
  echo "  --body \"Adds DRY_RUN→Real Merge workflow snippet to README + cheatsheet.\" \\"
  echo "  --label \"docs/ops\""
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚨 Common Fixes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cat <<'FIXES'
1) Error: "Branch already exists"
   Fix (restart from scratch):

   git switch main
   git pull --ff-only
   git branch -D docs/ops-merge-both-prs-dryrun-workflow  # delete local
   git push origin --delete docs/ops-merge-both-prs-dryrun-workflow  # delete remote (optional)

   # Then re-run:
   ./scripts/ops/update_merge_dryrun_workflow_docs.sh

2) Error: "gh not authenticated"
   Fix:

   gh auth login
   gh auth status

3) Error: "Snippet not found in docs"
   Check:

   # Manual insert (if script failed)
   vim docs/ops/README.md
   vim docs/ops/pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md

   # Copy snippet from:
   cat scripts/ops/update_merge_dryrun_workflow_docs.sh | grep -A 30 "SNIPPET ="

4) Error: "Working tree dirty"
   Fix:

   git status
   git stash push -u -m "temp-before-dryrun-workflow"
   # Re-run script
   git stash pop

5) PR already exists but want to update
   Fix:

   # Make changes locally
   git add docs/ops/
   git commit --amend --no-edit
   git push --force-with-lease
FIXES

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Validation complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
