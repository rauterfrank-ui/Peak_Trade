#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/ops/pt_docs_pr.sh "docs(ops): <commit message>"
#
# Goal:
# - deterministic docs-only workflow
# - avoid shell wildcard expansion and "silent add" failures
# - keep PR-based workflow (audit-friendly)

msg="${1:-docs(ops): update ops docs (docs-only)}"

echo "== PRE-FLIGHT =="
pwd
git rev-parse --show-toplevel >/dev/null
branch="$(git branch --show-current || true)"
if [[ -z "${branch}" ]]; then
  echo "ERROR: Detached HEAD (no branch). Checkout/create a branch first."
  git status -sb
  exit 2
fi
git status -sb

echo
echo "== STAGE (safe: git pathspec, no shell wildcard expansion) =="
# IMPORTANT:
# - We quote globs so the shell does NOT expand them.
# - Git will match them as pathspecs internally.
git add -A -- \
  docs/ops/control_center \
  docs/ops/README.md \
  docs/ops/EVIDENCE_INDEX.md \
  "docs/ops/PR_*_MERGE_LOG.md" \
  "docs/ops/PR_TBD_MERGE_LOG.md" \
  "docs/ops/PR_*_MERGE_LOG*.md" || true

echo
echo "== STAGED DIFF (name-status) =="
if git diff --cached --name-status | sed -n "1,200p" | grep -q .; then
  git diff --cached --name-status | sed -n "1,200p"
else
  echo "Nothing staged. Aborting without commit."
  git status -sb
  exit 3
fi

echo
echo "== COMMIT =="
git commit -m "${msg}"

echo
echo "== PUSH =="
git push -u origin "${branch}"

echo
echo "== PR (idempotent) =="
if gh pr view "${branch}" >/dev/null 2>&1; then
  gh pr view "${branch}" --json number,title,state,url -q '"PR #\(.number) \(.state) \(.url)\nTitle: \(.title)"'
else
  body="$(printf "%b" "## Summary\nDocs-only update.\n\n## Verification\n- pre-commit hooks ran locally\n\n## Risk\nMinimal (documentation only)\n")"
  gh pr create \
    --base main \
    --head "${branch}" \
    --title "${msg}" \
    --body "${body}"
fi
