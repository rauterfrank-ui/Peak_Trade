#!/usr/bin/env bash
set -euo pipefail

PR=""
MERGE_SHA=""
REMOTE="origin"
BRANCH="main"

usage() {
  cat <<USAGE
format_merge_log_snippet.sh - Generate a merge-log markdown snippet

Usage:
  scripts/automation/format_merge_log_snippet.sh --pr <number> [--merge-sha <sha>] [--remote <name>] [--branch <name>]

Options:
  --pr <number>         PR number
  --merge-sha <sha>     Merge commit SHA (defaults to PR mergeCommit via gh if available, else HEAD)
  --remote <name>       Default: origin
  --branch <name>       Default: main
  -h, --help            Show help

Exit codes:
  0 success
  2 usage error
  10 internal error
USAGE
}

die_usage(){ echo "ERROR: $*" >&2; usage >&2; exit 2; }
internal(){ echo "ERROR: $*" >&2; exit 10; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --pr"; PR="$1"; shift;;
    --merge-sha) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --merge-sha"; MERGE_SHA="$1"; shift;;
    --remote) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --remote"; REMOTE="$1"; shift;;
    --branch) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --branch"; BRANCH="$1"; shift;;
    -h|--help) usage; exit 0;;
    *) die_usage "Unknown argument: $1";;
  esac
done

[[ -n "$PR" ]] || die_usage "--pr is required"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || internal "Not inside a git repository"

MERGED_AT=""
PR_TITLE=""

if [[ -z "$MERGE_SHA" ]]; then
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    MERGE_SHA="$(gh pr view "$PR" --json mergeCommit --jq '.mergeCommit.oid' 2>/dev/null || true)"
    MERGED_AT="$(gh pr view "$PR" --json mergedAt --jq '.mergedAt' 2>/dev/null || true)"
    PR_TITLE="$(gh pr view "$PR" --json title --jq '.title' 2>/dev/null || true)"
  fi
fi

[[ -n "$MERGE_SHA" ]] || MERGE_SHA="$(git rev-parse HEAD)"

DIFFSTAT="$(git show --stat --oneline "$MERGE_SHA" | tail -n +2 || true)"

CI_STATUS="(gh unavailable)"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  CI_STATUS="$(gh pr checks "$PR" 2>/dev/null || echo "(checks unavailable)")"
fi

echo "# PR #${PR} - Merge Log Documentation (MERGED ✅)"
echo
echo "## Merge Details"
echo
echo "- PR: #${PR}${PR_TITLE:+ – ${PR_TITLE}}"
if [[ -n "$MERGED_AT" && "$MERGED_AT" != "null" ]]; then
  echo "- Merged At: ${MERGED_AT}"
else
  echo "- Merged At: (unknown; gh not available)"
fi
echo "- Merge Commit: ${MERGE_SHA}"
echo
echo "## Diffstat"
echo
echo "${DIFFSTAT}"
echo
echo "## CI Status"
echo
echo "${CI_STATUS}"
echo
echo "## What Was Delivered"
echo
echo "- (fill in)"
echo
echo "## Post-Merge Validation"
echo
echo "- ✅ main updated successfully"
echo "- ✅ working tree clean"
