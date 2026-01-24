#!/usr/bin/env bash
set -euo pipefail

# Merge Train: PR #950 -> PR #951 (guarded, single-shot)
#
# Default: snapshot-only (NO MERGE). Enable merges only with DO_MERGE=1.
#
# Inputs:
#   PR_950=950
#   PR_951=951
#   EXPECT_950_SHA=...
#   EXPECT_951_SHA=...
#   DO_MERGE=0|1
#   ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS=0|1
#   DELETE_BASE_BRANCH=0|1   (compat alias; prefer ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS)

cd "$(git rev-parse --show-toplevel)"

PR_950="${PR_950:-950}"
PR_951="${PR_951:-951}"

EXPECT_950_SHA="${EXPECT_950_SHA:-6a83edafac7103b6f52dbef38c0e9a992111408d}"
EXPECT_951_SHA="${EXPECT_951_SHA:-225d9de12c6e80badff98aa3ec8984ac7cce6e33}"

DO_MERGE="${DO_MERGE:-0}"
DELETE_BASE_BRANCH="${DELETE_BASE_BRANCH:-}"
ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS="${ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS:-${DELETE_BASE_BRANCH:-0}}"

snap_pr() {
  local pr="$1"
  echo "== PR #${pr} SNAPSHOT =="
  gh pr view "$pr" --json url,state,baseRefName,headRefName,headRefOid,mergeable,mergeStateStatus -q \
    '{url,state,baseRefName,headRefName,headRefOid,mergeable,mergeStateStatus}'
  echo
  gh pr checks "$pr" || true
  echo
}

require_head_match() {
  local pr="$1"
  local expect_sha="$2"
  local got
  got="$(gh pr view "$pr" --json headRefOid -q .headRefOid)"
  if [ "${got:-}" != "${expect_sha}" ]; then
    echo "GUARD_FAIL: PR #${pr} headRefOid mismatch: got=${got:-EMPTY} expect=${expect_sha}" >&2
    exit 2
  fi
}

require_state() {
  local pr="$1"
  local want="$2"
  local got
  got="$(gh pr view "$pr" --json state -q .state)"
  if [ "${got:-}" != "${want}" ]; then
    echo "GUARD_FAIL: PR #${pr} state mismatch: got=${got:-EMPTY} want=${want}" >&2
    exit 2
  fi
}

dependents_count_for_base_branch() {
  local base_branch="$1"
  if [ -z "${base_branch:-}" ]; then
    echo "0"
    return 0
  fi
  gh pr list --state open --base "${base_branch}" --json number -q 'length'
}

print_dependents_for_base_branch() {
  local base_branch="$1"
  if [ -z "${base_branch:-}" ]; then
    return 0
  fi
  gh pr list --state open --base "${base_branch}" --json number,url,headRefName,headRefOid,title -q \
    '.[] | {number,url,headRefName,headRefOid,title}'
}

echo "== MERGE TRAIN 950 -> 951 (dry-run by default) =="
echo "DO_MERGE=${DO_MERGE}"
echo "EXPECT_950_SHA=${EXPECT_950_SHA}"
echo "EXPECT_951_SHA=${EXPECT_951_SHA}"
echo "ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS=${ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS}"
echo

snap_pr "${PR_950}"
snap_pr "${PR_951}"

if [[ "${DO_MERGE}" != "1" ]]; then
  echo "== DRY-RUN ONLY (NO MERGE) =="
  echo "To enable merges (single-shot):"
  echo "  DO_MERGE=1 EXPECT_950_SHA=... EXPECT_951_SHA=... bash scripts/ops/merge_train_950_951.sh"
  exit 0
fi

echo "== PRE-MERGE GUARD #${PR_950} =="
require_state "${PR_950}" "OPEN"
require_head_match "${PR_950}" "${EXPECT_950_SHA}"
echo "GUARD_OK"
echo

echo "== MERGE #${PR_950} (guarded) =="
base_branch_950="$(gh pr view "${PR_950}" --json headRefName -q .headRefName)"
dependents_950="$(dependents_count_for_base_branch "${base_branch_950}")"
echo "Base branch for #${PR_950}: ${base_branch_950}"
echo "Open dependent PRs with base='${base_branch_950}': ${dependents_950}"
if [ "${dependents_950}" != "0" ]; then
  echo "Dependents:"
  print_dependents_for_base_branch "${base_branch_950}" || true
fi
echo

merge_950_args=(--squash --match-head-commit "${EXPECT_950_SHA}")
if [ "${dependents_950}" = "0" ] || [ "${ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS}" = "1" ]; then
  merge_950_args+=(--delete-branch)
else
  echo "NOTE: Not deleting base branch '${base_branch_950}' because dependents exist."
  echo "      (Set ALLOW_DELETE_BASE_BRANCH_WITH_DEPENDENTS=1 to override.)"
  echo
fi

gh pr merge "${PR_950}" "${merge_950_args[@]}"
echo

echo "== POST-MERGE #${PR_950} =="
gh pr view "${PR_950}" --json state,mergedAt,mergeCommit,url -q '{state,mergedAt,mergeCommit,url}' || true
echo

echo "== GUARD: #${PR_950} must be MERGED before retarget =="
require_state "${PR_950}" "MERGED"
echo "GUARD_OK"
echo

echo "== RETARGET #${PR_951} base -> main =="
require_state "${PR_951}" "OPEN"
gh pr edit "${PR_951}" --base main
echo

echo "== SNAPSHOT #${PR_951} AFTER RETARGET =="
snap_pr "${PR_951}"

echo "== PRE-MERGE GUARD #${PR_951} =="
require_state "${PR_951}" "OPEN"
require_head_match "${PR_951}" "${EXPECT_951_SHA}"
echo "GUARD_OK"
echo

echo "== MERGE #${PR_951} (guarded) =="
gh pr merge "${PR_951}" --squash --delete-branch --match-head-commit "${EXPECT_951_SHA}"
echo

echo "== POST-MERGE #${PR_951} =="
gh pr view "${PR_951}" --json state,mergedAt,mergeCommit,url -q '{state,mergedAt,mergeCommit,url}' || true
