#!/usr/bin/env bash
# Peak_Trade — PR-Management-Toolkit (Dogfooding) — End-to-End
# Ort: Terminal/Shell in deinem Repo-Checkout
# Ergebnis: PR wird erstellt und anschließend mit dem Toolkit selbst reviewed+gemerged (Meta-Moment 🎭)

set -euo pipefail
cd ~/Peak_Trade

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎭 Peak_Trade: PR-Management-Toolkit Dogfooding Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────────────
# 0) Preflight
# ─────────────────────────────────────────────────────────────
echo ""
echo "📋 Step 0: Preflight..."
command -v gh >/dev/null 2>&1 || { echo "❌ gh not found"; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "❌ gh not authenticated. Run: gh auth login"; exit 2; }

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree not clean. Fix it first:"
  git status --porcelain
  echo ""
  echo "Suggested:"
  echo "  git stash   # or commit your changes"
  exit 2
fi

git checkout main
git pull --ff-only

# ─────────────────────────────────────────────────────────────
# 1) Branch
# ─────────────────────────────────────────────────────────────
echo ""
echo "🌿 Step 1: Creating branch..."
BR="docs/pr-management-toolkit"
git checkout -b "$BR"

# ─────────────────────────────────────────────────────────────
# 2) Stage files (8)
# ─────────────────────────────────────────────────────────────
echo ""
echo "📦 Step 2: Staging files (8)..."
FILES=(
  scripts/ops/review_and_merge_pr.sh
  scripts/ops/pr_review_merge_workflow.sh
  scripts/ops/pr_review_merge_workflow_template.sh
  docs/ops/PR_MANAGEMENT_TOOLKIT.md
  docs/ops/PR_MANAGEMENT_QUICKSTART.md
  docs/ops/README.md
  tests/ops/test_pr_management_toolkit_scripts.py
  scripts/ops/pr_toolkit_deploy_workflow.sh
)

missing=0
for f in "${FILES[@]}"; do
  if [[ ! -e "$f" ]]; then
    echo "❌ Missing file: $f"
    missing=1
  fi
done
[[ "$missing" -eq 1 ]] && exit 2

git add "${FILES[@]}"
git diff --staged --stat
git status

# ─────────────────────────────────────────────────────────────
# 3) Local tests (bash -n + pytest)
# ─────────────────────────────────────────────────────────────
echo ""
echo "🧪 Step 3: Local tests..."
bash -n scripts/ops/review_and_merge_pr.sh
bash -n scripts/ops/pr_review_merge_workflow.sh
bash -n scripts/ops/pr_review_merge_workflow_template.sh
bash -n scripts/ops/pr_toolkit_deploy_workflow.sh

uv run pytest -q tests/ops/test_pr_management_toolkit_scripts.py

# ─────────────────────────────────────────────────────────────
# 4) Commit + Push
# ─────────────────────────────────────────────────────────────
echo ""
echo "💾 Step 4: Commit..."
git commit \
  -m "docs(ops): PR management toolkit + CI guards" \
  -m "Meta: Dogfooding – this PR will be reviewed and merged using the toolkit itself.

Includes:
- Ops scripts for PR review/merge workflows
- Docs: Toolkit + Quickstart + ops README update
- CI guard tests ensuring scripts exist, are executable, and pass bash -n"

echo ""
echo "⬆️ Step 5: Push..."
git push -u origin "$BR"

# ─────────────────────────────────────────────────────────────
# 5) PR creation
# ─────────────────────────────────────────────────────────────
echo ""
echo "🧷 Step 6: Create PR..."
gh pr create \
  --title "docs(ops): PR management toolkit + CI guards" \
  --body "## Summary
Complete PR management toolkit with scripts, documentation, and CI guard tests.

## Meta: Dogfooding 🎭
This PR is intended to be reviewed and merged using the toolkit itself (watch → merge).

## Components
### Scripts (scripts/ops/)
- review_and_merge_pr.sh — safe-by-default (review-only unless --merge)
- pr_review_merge_workflow.sh — one-shot workflow
- pr_review_merge_workflow_template.sh — generic template
- pr_toolkit_deploy_workflow.sh — deployment automation

### Docs (docs/ops/)
- PR_MANAGEMENT_TOOLKIT.md
- PR_MANAGEMENT_QUICKSTART.md
- README.md updated

### Tests (tests/ops/)
- test_pr_management_toolkit_scripts.py — guards: existence, executable bit, bash -n" >/dev/null

PR_NUM="$(gh pr view --json number -q .number)"
echo "✅ PR created: #$PR_NUM"

# ─────────────────────────────────────────────────────────────
# 6) 🎭 Dogfooding: toolkit reviews + merges itself
# ─────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎭 Meta-Moment: Toolkit reviews & merges itself"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 6a) Review/watch (strict)
scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --watch

# 6b) Merge (squash) + update local main (strict)
scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --merge --method squash --update-main

# ─────────────────────────────────────────────────────────────
# 7) If audit fails (known issue), rerun with allow-fail
# ─────────────────────────────────────────────────────────────
# Uncomment if needed:
# scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --watch --allow-fail audit
# scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --merge --method squash --update-main --allow-fail audit

echo ""
echo "✅ Done. main updated."
git status
git log -1 --oneline
