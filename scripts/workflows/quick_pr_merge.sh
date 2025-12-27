#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Quick PR Merge – Für bereits committete Docs-Updates
# Usage: bash scripts/quick_pr_merge.sh
# =============================================================================

cd ~/Peak_Trade

# 0) Safety: sauberer Status + richtiger Branch
echo "==> Safety checks"
git status -sb
CURRENT_BRANCH="$(git branch --show-current)"
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "ERROR: Cannot run from main branch. Checkout your feature branch first."
  exit 1
fi

# 1) PR erstellen (Branch wird automatisch erkannt)
echo ""
echo "==> Creating PR"
gh pr create \
  --title "docs(ops): PR #203 merge log + index update" \
  --body "Adds merge log for PR #203 (matplotlib/viz tests optionalization) + updates ops README and changelog." \
  --base main

# 2) Checks live verfolgen
echo ""
echo "==> Watching PR checks (Ctrl+C to skip)"
gh pr checks --watch || true

# Optional: Warten auf Benutzer-Bestätigung vor Merge
echo ""
read -p "Press ENTER to merge PR (or Ctrl+C to abort)..." DUMMY

# 3) Merge (squash + branch löschen)
echo ""
echo "==> Merging PR (squash + delete branch)"
gh pr merge --squash --delete-branch

# 4) main aktualisieren
echo ""
echo "==> Updating main"
git checkout main
git pull --ff-only

echo ""
echo "✅ PR docs merged + main up-to-date"
git log -1 --oneline
