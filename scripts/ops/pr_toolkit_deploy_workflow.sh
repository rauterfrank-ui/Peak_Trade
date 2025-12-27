#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – PR-Management-Toolkit Deploy Workflow (Dogfooding)
# Creates PR for the toolkit, then reviews+merges it using the toolkit itself.
#
# Usage:
#   cd ~/Peak_Trade
#   ./scripts/ops/pr_toolkit_deploy_workflow.sh
#
# Optional env:
#   BR=docs/pr-management-toolkit
#   ALLOW_FAIL_CHECKS="audit"   # space-separated list (passed as repeated --allow-fail)
# ─────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

BR="${BR:-docs/pr-management-toolkit}"
TITLE="${TITLE:-docs(ops): PR management toolkit + CI guards}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎭 Peak_Trade: PR Toolkit Deploy (Dogfooding)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Branch: $BR"
echo

# 0) Preflight
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ gh (GitHub CLI) not found. Install gh first." >&2
  exit 2
fi
gh auth status >/dev/null 2>&1 || {
  echo "❌ gh not authenticated. Run: gh auth login" >&2
  exit 2
}

git status --porcelain | grep -q . && {
  echo "❌ Working tree not clean. Please commit/stash changes first." >&2
  git status --porcelain
  exit 2
}

git checkout main
git pull --ff-only

# 1) Branch
git checkout -b "$BR"

# 2) Required files list (includes this deploy script)
FILES=(
  scripts/ops/review_and_merge_pr.sh
  scripts/ops/pr_review_merge_workflow.sh
  scripts/ops/pr_review_merge_workflow_template.sh
  scripts/ops/pr_toolkit_deploy_workflow.sh
  docs/ops/PR_MANAGEMENT_TOOLKIT.md
  docs/ops/PR_MANAGEMENT_QUICKSTART.md
  docs/ops/README.md
  tests/ops/test_pr_management_toolkit_scripts.py
)

missing=0
for f in "${FILES[@]}"; do
  if [[ ! -e "$f" ]]; then
    echo "❌ Missing file: $f" >&2
    missing=1
  fi
done
[[ "$missing" -eq 1 ]] && exit 2

# 3) Stage
git add "${FILES[@]}"

echo
echo "📊 Staged diff:"
git diff --staged --stat

# 4) Quick verification (fast)
echo
echo "🧪 Bash syntax checks..."
bash -n scripts/ops/review_and_merge_pr.sh
bash -n scripts/ops/pr_review_merge_workflow.sh
bash -n scripts/ops/pr_review_merge_workflow_template.sh
bash -n scripts/ops/pr_toolkit_deploy_workflow.sh

echo
echo "🧪 Guard tests..."
uv run pytest -q tests/ops/test_pr_management_toolkit_scripts.py

# Optional (fast-ish): all ops tests
# uv run pytest -q tests/ops/.

# --- Idempotency: exit cleanly if generator produced no changes ---
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already up-to-date). Exiting 0."
  exit 0
fi
# --- /Idempotency ---

# 5) Commit
echo
echo "💾 Commit..."
git commit \
  -m "$TITLE" \
  -m "Meta: Dogfooding – this PR will be reviewed and merged using the toolkit itself.

Includes:
- Ops scripts for PR review/merge workflows
- Docs: Toolkit + Quickstart + ops README update
- CI guard tests ensuring scripts exist, are executable, and pass bash -n"

# 6) Push
echo
echo "⬆️ Push..."
git push -u origin "$BR"

# 7) Create or reuse PR
echo
echo "🔎 Finding/creating PR..."
PR_NUM="$(gh pr list --head "$BR" --json number --jq '.[0].number' || true)"

if [[ -z "${PR_NUM:-}" || "$PR_NUM" == "null" ]]; then
  gh pr create \
    --title "$TITLE" \
    --body "## Summary
Complete PR management toolkit with scripts, documentation, and CI guard tests.

## Dogfooding
This PR is intended to be reviewed and merged using the toolkit itself (watch → merge).

## Components
### Scripts (scripts/ops/)
- review_and_merge_pr.sh — safe-by-default (review-only unless --merge)
- pr_review_merge_workflow.sh — one-shot workflow
- pr_review_merge_workflow_template.sh — generic template
- pr_toolkit_deploy_workflow.sh — this deployment automation

### Docs (docs/ops/)
- PR_MANAGEMENT_TOOLKIT.md
- PR_MANAGEMENT_QUICKSTART.md
- README.md updated

### Tests (tests/ops/)
- test_pr_management_toolkit_scripts.py — guards: existence, executable bit, bash -n

## Usage
\`\`\`bash
scripts/ops/review_and_merge_pr.sh --pr 259
scripts/ops/review_and_merge_pr.sh --pr 259 --watch --allow-fail audit
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main
\`\`\`" >/dev/null

  PR_NUM="$(gh pr list --head "$BR" --json number --jq '.[0].number')"
fi

echo "✅ PR: #$PR_NUM"
echo

# 8) Dogfood: review/watch + merge using the toolkit
ALLOW_ARGS=()
if [[ -n "${ALLOW_FAIL_CHECKS:-}" ]]; then
  for c in $ALLOW_FAIL_CHECKS; do
    ALLOW_ARGS+=(--allow-fail "$c")
  done
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎭 Dogfooding: toolkit reviews and merges itself"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --watch "${ALLOW_ARGS[@]}"
scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --merge --method squash --update-main "${ALLOW_ARGS[@]}"

echo
echo "✅ Done. main updated."
git status
git log -1 --oneline
