#!/usr/bin/env bash
set -euo pipefail

PR="${PR:-${1:-}}"
ISSUE="${ISSUE:-}"
DO_MERGE="${DO_MERGE:-1}"          # 1 = merge ausführen, 0 = nur watch/review
RUN_FORMAT_CHECKS="${RUN_FORMAT_CHECKS:-1}"  # 1 = ruff+black nach merge

if [[ -z "${PR}" ]]; then
  echo "Usage: PR=254 ISSUE=252 DO_MERGE=1 ./scripts/ops/merge_pr_workflow.sh"
  echo "   or: ./scripts/ops/merge_pr_workflow.sh 254"
  exit 2
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Peak_Trade — PR #${PR} (Watch → Merge → Post-Merge Verify)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 0) Preflight: gh auth + clean tree
echo ""
echo "📋 Preflight..."
gh auth status -h github.com >/dev/null
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree not clean. Commit/stash first."
  git status --porcelain
  exit 3
fi

# 1) main up-to-date
echo ""
echo "🔄 Update main..."
git checkout main
git pull --ff-only

# 2) Checkout PR
echo ""
echo "🌿 Checkout PR #${PR}..."
gh pr checkout "${PR}"

BR="$(gh pr view "${PR}" --json headRefName -q .headRefName || true)"

# 3) Review snapshot
echo ""
echo "🔎 PR view..."
gh pr view "${PR}"

echo ""
echo "📊 Changed files..."
gh pr diff "${PR}" --name-only

# 4) Watch checks
echo ""
echo "🧪 Watching checks..."
gh pr checks "${PR}" --watch

echo ""
echo "🧾 Final checks snapshot:"
gh pr checks "${PR}"

# 5) Merge
if [[ "${DO_MERGE}" == "1" ]]; then
  echo ""
  echo "🔀 Merging PR #${PR} (squash + delete branch)..."
  gh pr merge "${PR}" --squash --delete-branch
else
  echo ""
  echo "ℹ️ DO_MERGE=0 → skipping merge."
  exit 0
fi

# 6) Post-merge: sync main
echo ""
echo "🔄 Sync main after merge..."
git checkout main
git pull --ff-only

# 7) Post-merge sanity
if [[ "${RUN_FORMAT_CHECKS}" == "1" ]]; then
  echo ""
  echo "✅ Post-merge checks: ruff format + ruff check..."
  uv run ruff format --check .
  uv run ruff check .
else
  echo ""
  echo "ℹ️ RUN_FORMAT_CHECKS=0 → skipping ruff format/check."
fi

# 8) Issue state (optional)
if [[ -n "${ISSUE}" ]]; then
  echo ""
  echo "🔎 Issue #${ISSUE} state:"
  gh issue view "${ISSUE}" --json state -q .state || true
fi

# 9) Cleanup local branch
if [[ -n "${BR:-}" ]]; then
  echo ""
  echo "🧹 Cleanup local branch: ${BR}"
  git branch -D "${BR}" >/dev/null 2>&1 || true
fi

echo ""
echo "🎉 DONE: PR #${PR} merged, main updated, post-merge sanity done."
