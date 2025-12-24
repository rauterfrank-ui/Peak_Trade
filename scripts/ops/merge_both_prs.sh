#!/usr/bin/env bash
set -euo pipefail

DOCS_PR="${DOCS_PR:-}"
FEAT_PR="${FEAT_PR:-}"

BASE_BRANCH="${BASE_BRANCH:-main}"

MERGE_METHOD="${MERGE_METHOD:-squash}"       # squash | merge | rebase
DELETE_BRANCH="${DELETE_BRANCH:-true}"       # true | false
WATCH_CHECKS="${WATCH_CHECKS:-true}"         # true | false
UPDATE_MAIN="${UPDATE_MAIN:-true}"           # true | false

REQUIRE_APPROVAL="${REQUIRE_APPROVAL:-true}" # true | false
FAIL_ON_DRAFT="${FAIL_ON_DRAFT:-true}"       # true | false

# Mergeability can be UNKNOWN briefly; retry a bit.
MERGEABLE_RETRIES="${MERGEABLE_RETRIES:-10}"
MERGEABLE_SLEEP_SEC="${MERGEABLE_SLEEP_SEC:-2}"

RUN_PYTEST="${RUN_PYTEST:-true}"             # true | false
PYTEST_CMD="${PYTEST_CMD:-python -m pytest -q}"

DRY_RUN="${DRY_RUN:-false}"                 # true | false (no merge, just checks)

die() { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"; }

need git
need gh

# Basic validation
[[ -n "$DOCS_PR" && -n "$FEAT_PR" ]] || die "Set DOCS_PR and FEAT_PR (e.g. DOCS_PR=123 FEAT_PR=124)."
[[ "$DOCS_PR" =~ ^[0-9]+$ ]] || die "DOCS_PR must be a number."
[[ "$FEAT_PR" =~ ^[0-9]+$ ]] || die "FEAT_PR must be a number."

# Clean working tree (avoid accidental carry-over)
git diff --quiet || die "Working tree not clean. Commit/stash first."
git diff --cached --quiet || die "Index not clean. Commit/stash first."

# Ensure auth
gh auth status >/dev/null 2>&1 || die "gh not authenticated. Run: gh auth login"

merge_flags=( "--${MERGE_METHOD}" )
if [[ "$DELETE_BRANCH" == "true" ]]; then
  merge_flags+=( "--delete-branch" )
fi

pr_field() {
  local pr="$1" field="$2"
  gh pr view "$pr" --json "$field" --jq ".${field}"
}

pr_fields() {
  local pr="$1"
  gh pr view "$pr" --json number,url,title,state,isDraft,baseRefName,mergeable,reviewDecision --jq \
    '"#"+(.number|tostring)+" | "+.title+" | "+.url+"\nstate="+.state+" draft="+(.isDraft|tostring)+" base="+.baseRefName+" mergeable="+.mergeable+" reviewDecision="+(.reviewDecision//"null")'
}

wait_mergeable() {
  local pr="$1"
  local i=0
  local m
  while true; do
    m="$(pr_field "$pr" mergeable)"
    if [[ "$m" != "UNKNOWN" ]]; then
      echo "$m"
      return 0
    fi
    i=$((i+1))
    if (( i >= MERGEABLE_RETRIES )); then
      echo "$m"
      return 0
    fi
    sleep "$MERGEABLE_SLEEP_SEC"
  done
}

assert_pr_ready() {
  local pr="$1"

  echo "==> PR readiness check for #$pr"
  echo "$(pr_fields "$pr")"
  echo

  local state is_draft base mergeable review

  state="$(pr_field "$pr" state)"
  [[ "$state" == "OPEN" ]] || die "PR #$pr is not OPEN (state=$state)."

  is_draft="$(pr_field "$pr" isDraft)"
  if [[ "$FAIL_ON_DRAFT" == "true" && "$is_draft" == "true" ]]; then
    die "PR #$pr is a DRAFT. Mark it ready for review or set FAIL_ON_DRAFT=false."
  fi

  base="$(pr_field "$pr" baseRefName)"
  [[ "$base" == "$BASE_BRANCH" ]] || die "PR #$pr targets base '$base' (expected '$BASE_BRANCH')."

  mergeable="$(wait_mergeable "$pr")"
  [[ "$mergeable" == "MERGEABLE" ]] || die "PR #$pr is not mergeable (mergeable=$mergeable). Resolve conflicts / rebase."

  review="$(pr_field "$pr" reviewDecision || true)"
  # reviewDecision can be null if repo has no reviews or GitHub hasn't computed it.
  if [[ "$REQUIRE_APPROVAL" == "true" ]]; then
    [[ "$review" == "APPROVED" ]] || die "PR #$pr not approved (reviewDecision=$review). Get approval or set REQUIRE_APPROVAL=false."
  fi

  echo "✅ Ready: #$pr (mergeable=$mergeable, reviewDecision=${review:-null})"
}

watch_pr() {
  local pr="$1"
  echo "==> Watching checks for PR #$pr"
  gh pr checks "$pr" --watch
}

merge_pr() {
  local pr="$1"
  echo "==> Merging PR #$pr (${MERGE_METHOD})"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY_RUN=true → skipping merge for #$pr"
    return 0
  fi
  gh pr merge "$pr" "${merge_flags[@]}"
}

update_main() {
  echo "==> Updating local $BASE_BRANCH"
  git checkout "$BASE_BRANCH" >/dev/null 2>&1 || git checkout -b "$BASE_BRANCH"
  git pull --ff-only
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔀 Merge Both PRs (DOCS first, then FEATURE) — fail-fast mode"
echo "DOCS_PR=#${DOCS_PR}  FEAT_PR=#${FEAT_PR}"
echo "base=${BASE_BRANCH} method=${MERGE_METHOD} delete_branch=${DELETE_BRANCH} watch_checks=${WATCH_CHECKS}"
echo "require_approval=${REQUIRE_APPROVAL} fail_on_draft=${FAIL_ON_DRAFT} dry_run=${DRY_RUN}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# DOCS first
if [[ "$WATCH_CHECKS" == "true" ]]; then
  watch_pr "$DOCS_PR"
fi
assert_pr_ready "$DOCS_PR"
merge_pr "$DOCS_PR"
if [[ "$UPDATE_MAIN" == "true" ]]; then
  update_main
fi

# FEATURE second
if [[ "$WATCH_CHECKS" == "true" ]]; then
  watch_pr "$FEAT_PR"
fi
assert_pr_ready "$FEAT_PR"
merge_pr "$FEAT_PR"
if [[ "$UPDATE_MAIN" == "true" ]]; then
  update_main
fi

# Optional sanity
if [[ "$RUN_PYTEST" == "true" ]]; then
  echo "==> Sanity: ${PYTEST_CMD}"
  eval "$PYTEST_CMD"
fi

echo "✅ Done. Both PRs processed."
