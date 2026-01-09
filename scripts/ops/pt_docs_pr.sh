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
# - Split into separate add commands to avoid "pathspec not found" blocking other adds.
git add -A -- docs/ops/control_center 2>/dev/null || true
git add -A -- docs/ops/README.md 2>/dev/null || true
git add -A -- docs/ops/EVIDENCE_INDEX.md 2>/dev/null || true
git add -A -- "docs/ops/PR_*_MERGE_LOG.md" 2>/dev/null || true
git add -A -- "docs/ops/PR_*_MERGE_LOG*.md" 2>/dev/null || true

echo
echo "== DOCS-ONLY GUARDRAIL =="
# If anything outside docs/ is staged, abort to preserve "docs-only" intent.
if git diff --cached --name-only | grep -qv '^docs/'; then
  echo "ERROR: Non-docs changes are staged. This helper is docs-only."
  echo "Staged files (first 200):"
  git diff --cached --name-only | sed -n '1,200p'
  echo
  echo "Suggested fix:"
  echo "  - Unstage non-docs files: git restore --staged <file>"
  echo "  - Or commit them separately, then re-run this script."
  exit 4
fi

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
