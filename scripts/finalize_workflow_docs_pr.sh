#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Finalize Workflow Scripts Documentation PR
# =============================================================================

cd ~/Peak_Trade

echo "==> Current branch status"
git status -sb

BR="$(git branch --show-current)"
echo "Current branch: $BR"

if [ "$BR" != "docs/ops-workflow-scripts-docs" ]; then
  echo "WARNING: Not on expected branch docs/ops-workflow-scripts-docs"
  echo "Current branch: $BR"
  read -p "Continue anyway? (y/N) " CONFIRM
  if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Aborted."
    exit 1
  fi
fi

echo ""
echo "==> Commits on this branch"
git log origin/main..HEAD --oneline

echo ""
echo "==> Push branch"
git push -u origin "$BR"

echo ""
echo "==> Create PR"
gh pr create \
  --title "docs(ops): workflow scripts documentation + automation infrastructure" \
  --body "Adds comprehensive documentation for ops automation scripts.

## New Documentation
- **docs/ops/WORKFLOW_SCRIPTS.md** – Complete guide for workflow automation
  - post_merge_workflow_pr203.sh (all-in-one PR #203 docs + merge)
  - quick_pr_merge.sh (quick PR merge when docs already committed)
  - post_merge_workflow.sh (generic post-merge verification)
  - Workflow patterns, troubleshooting, best practices

## Updated Files
- docs/ops/README.md – Added link to WORKFLOW_SCRIPTS.md in Guides section
- docs/PEAK_TRADE_STATUS_OVERVIEW.md – Changelog entry

## New Scripts
- scripts/post_merge_workflow_pr203.sh – Automated PR #203 merge log workflow
- scripts/quick_pr_merge.sh – Quick PR merge utility

## Use-Case
Streamlines post-merge documentation and PR automation workflows for ops team.

## Related
- PR #201 (web-ui tests optional)
- PR #203 (matplotlib/viz tests optional)
- Ops automation infrastructure buildout" \
  --base main

echo ""
echo "==> Watch PR checks"
gh pr checks --watch || true

echo ""
read -p "Press ENTER to merge PR (or Ctrl+C to abort)..." DUMMY

echo ""
echo "==> Merge PR"
gh pr merge --squash --delete-branch

echo ""
echo "==> Update main"
git checkout main
git pull --ff-only

echo ""
echo "✅ DONE"
git log -1 --oneline
