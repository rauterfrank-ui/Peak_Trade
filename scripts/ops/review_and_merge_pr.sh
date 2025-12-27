#!/usr/bin/env bash
# Peak_Trade – PR Review & Merge Helper (safe-by-default)
# - Default: review-only (no merge)
# - Merge only with --merge
# - Optional: --watch checks, allow specific failing checks (e.g. audit baseline)

set -euo pipefail

# ----------------------------
# Docs Diff Guard (PR files)
# ----------------------------
# Default: enabled when --merge is used
DOCS_GUARD_ENABLED=1
DOCS_GUARD_THRESHOLD=200     # per-file deletions threshold under docs/
DOCS_GUARD_WARN_ONLY=0       # 1 = warn-only, do not fail
DOCS_GUARD_PREFIX="docs/"    # guard scope (prefix match)

# Optional shared helpers (if present in repo)
if [ -f "$(dirname "$0")/run_helpers.sh" ]; then
  # shellcheck disable=SC1091
  source "$(dirname "$0")/run_helpers.sh"
fi

die() { echo "❌ $*" >&2; exit 1; }
info() { echo "ℹ️  $*"; }
ok() { echo "✅ $*"; }

usage() {
  cat <<'EOF'
Usage:
  scripts/ops/review_and_merge_pr.sh --pr <number> [options]

Options:
  --watch                 Watch PR checks until completion.
  --merge                 Perform merge (default is review-only).
  --method <squash|merge|rebase>  Merge method (default: squash).
  --delete-branch         Delete remote branch after merge (default: on).
  --no-delete-branch      Do not delete remote branch.
  --update-main           After merge, checkout main and pull --ff-only.
  --allow-fail <name>     Allow a specific check to fail (repeatable), e.g. --allow-fail audit
  --dirty-ok              Do not require clean working tree.
  --dry-run               Print actions but do not merge/update.
  --skip-docs-guard       Skip docs diff guard (not recommended).
  --docs-guard-threshold N  Per-file deletions threshold under docs/ (default: 200).
  --docs-guard-warn-only  Do not fail on violations (warn only).
  -h, --help              Show help.

Environment Variables:
  MERGEABLE_RETRIES       Number of retries for mergeable status (default: 3).
  MERGEABLE_SLEEP_SEC     Seconds to sleep between retries (default: 2).

Notes:
- Allow-fail does NOT bypass GitHub branch protection. If a failing check is required, merge will still be blocked.
- The script retries UNKNOWN mergeable status automatically (GitHub needs time to compute after pushes).
EOF
}

PR=""
WATCH=0
DO_MERGE=0
METHOD="squash"
DELETE_BRANCH=1
UPDATE_MAIN=0
DIRTY_OK=0
DRY_RUN=0
ALLOW_FAIL=()

while [ $# -gt 0 ]; do
  case "$1" in
    --pr) PR="${2:-}"; shift 2 ;;
    --watch) WATCH=1; shift ;;
    --merge) DO_MERGE=1; shift ;;
    --method) METHOD="${2:-}"; shift 2 ;;
    --delete-branch) DELETE_BRANCH=1; shift ;;
    --no-delete-branch) DELETE_BRANCH=0; shift ;;
    --update-main) UPDATE_MAIN=1; shift ;;
    --allow-fail) ALLOW_FAIL+=("${2:-}"); shift 2 ;;
    --dirty-ok) DIRTY_OK=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --skip-docs-guard) DOCS_GUARD_ENABLED=0; shift ;;
    --docs-guard-threshold) DOCS_GUARD_THRESHOLD="${2:-}"; shift 2 ;;
    --docs-guard-warn-only) DOCS_GUARD_WARN_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown arg: $1 (use --help)" ;;
  esac
done

[ -n "$PR" ] || die "Missing --pr <number>"

case "$METHOD" in
  squash|merge|rebase) ;;
  *) die "Invalid --method '$METHOD' (use squash|merge|rebase)" ;;
esac

# Preflight: repo + gh auth
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repo"
if [ "$DIRTY_OK" -eq 0 ]; then
  [ -z "$(git status --porcelain)" ] || die "Working tree not clean (use --dirty-ok to override)"
fi
gh auth status >/dev/null 2>&1 || die "gh auth not available. Run: gh auth login"

REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true)
[ -n "$REPO" ] || die "Could not resolve repo via gh (are you in the right repo?)"

# Extract OWNER and REPO_NAME for docs diff guard API calls
OWNER="$(echo "$REPO" | cut -d/ -f1)"
REPO_NAME="$(echo "$REPO" | cut -d/ -f2)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔎 Peak_Trade – PR Review & Merge Helper"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
info "Repo: $REPO"
info "PR:   #$PR"
info "Mode: $([ "$DO_MERGE" -eq 1 ] && echo "MERGE" || echo "REVIEW-ONLY")"
info "Watch: $WATCH | Method: $METHOD | Delete-branch: $DELETE_BRANCH | Update-main: $UPDATE_MAIN | Dry-run: $DRY_RUN"
if [ "${#ALLOW_FAIL[@]}" -gt 0 ]; then
  info "Allow-fail checks: ${ALLOW_FAIL[*]}"
fi
echo ""

# Show PR summary
ok "PR summary:"
gh pr view "$PR" --json number,title,author,labels,baseRefName,headRefName,mergeable,reviewDecision \
  --jq '{number,title,author:.author.login,base:.baseRefName,head:.headRefName,mergeable,reviewDecision,labels:[.labels[].name]}' | cat
echo ""

ok "Diff files:"
gh pr diff "$PR" --name-only
echo ""

# Hard guard (only blocks when actually merging): GitHub-side mergeability
# Retries help when GitHub reports mergeable=UNKNOWN briefly after pushes.
MERGEABLE_RETRIES="${MERGEABLE_RETRIES:-3}"
MERGEABLE_SLEEP_SEC="${MERGEABLE_SLEEP_SEC:-2}"

MERGEABLE=""
for i in $(seq 1 "$MERGEABLE_RETRIES"); do
  MERGEABLE=$(gh pr view "$PR" --json mergeable --jq .mergeable 2>/dev/null || echo "")
  [ -n "$MERGEABLE" ] || MERGEABLE="UNKNOWN"

  if [ "$MERGEABLE" != "UNKNOWN" ]; then
    break
  fi

  info "PR mergeable status is UNKNOWN (try ${i}/${MERGEABLE_RETRIES})…"
  sleep "$MERGEABLE_SLEEP_SEC"
done

case "$MERGEABLE" in
  MERGEABLE)
    ok "PR is mergeable."
    ;;
  CONFLICTING)
    if [ "$DO_MERGE" -eq 1 ]; then
      die "PR has merge conflicts (mergeable=CONFLICTING). Resolve conflicts first."
    else
      info "PR has merge conflicts (mergeable=CONFLICTING). Review-only continues."
    fi
    ;;
  UNKNOWN)
    info "PR mergeable status is still UNKNOWN after retries. Continuing; merge may still be blocked by GitHub."
    ;;
  *)
    info "PR mergeable status: $MERGEABLE (continuing)."
    ;;
esac

echo ""

# Optional guard: require an approving review decision for merge mode
# (keeps review-only flexible; enforces only when --merge is set)
if [ "$DO_MERGE" -eq 1 ]; then
  REVIEW_DECISION=$(gh pr view "$PR" --json reviewDecision --jq .reviewDecision 2>/dev/null || echo "")
  # reviewDecision can be: APPROVED, CHANGES_REQUESTED, REVIEW_REQUIRED, null
  if [ "$REVIEW_DECISION" = "CHANGES_REQUESTED" ]; then
    die "Review decision is CHANGES_REQUESTED. Not merging."
  fi
  if [ "$REVIEW_DECISION" = "REVIEW_REQUIRED" ]; then
    info "Review decision is REVIEW_REQUIRED. Merge may still be blocked by branch protection."
    # If you want this to be a hard fail, replace info -> die.
  fi
  if [ "$REVIEW_DECISION" = "APPROVED" ]; then
    ok "PR has been approved."
  fi
  echo ""
fi

# Watch checks if requested
if [ "$WATCH" -eq 1 ]; then
  ok "Watching checks…"
  gh pr checks "$PR" --watch
  echo ""
fi

# Evaluate checks via JSON if available, else fall back to plain output
has_json=0
if gh pr checks "$PR" --json name,state --jq '.[0].name' >/dev/null 2>&1; then
  has_json=1
fi

is_allowed_fail() {
  local name="$1"
  local name_lower
  local a
  local a_lower
  name_lower="$(echo "$name" | tr '[:upper:]' '[:lower:]')"
  for a in "${ALLOW_FAIL[@]:-}"; do
    a_lower="$(echo "$a" | tr '[:upper:]' '[:lower:]')"
    if [ "$a_lower" = "$name_lower" ]; then
      return 0
    fi
  done
  return 1
}

docs_diff_guard_pr_files() {
  local pr="$1"
  local threshold="$2"
  local warn_only="$3"
  local prefix="$4"

  echo "🛡️ Docs Diff Guard (PR #$pr via GitHub API)"
  echo "  Scope:     ${prefix}*"
  echo "  Threshold: -${threshold} deletions per file"
  echo ""

  local page=1
  local violations=0
  local total_del=0
  while :; do
    # returns lines: additions<TAB>deletions<TAB>filename
    local lines
    lines="$(gh api "repos/${OWNER}/${REPO_NAME}/pulls/${pr}/files?per_page=100&page=${page}" \
      --jq '.[] | "\(.additions)\t\(.deletions)\t\(.filename)"' 2>/dev/null || true)"

    [[ -z "$lines" ]] && break

    while IFS=$'\t' read -r add del file; do
      [[ -z "${file:-}" ]] && continue
      [[ "$file" != "$prefix"* ]] && continue
      # del should be an int
      total_del=$((total_del + del))
      if (( del >= threshold )); then
        violations=$((violations + 1))
        echo "🚨 Large deletion: -$del  $file"
      fi
    done <<< "$lines"

    page=$((page + 1))
  done

  echo ""
  echo "Total deletions under ${prefix}*: $total_del"
  echo "Violations (per-file >= $threshold): $violations"
  echo ""

  if (( violations > 0 )); then
    if (( warn_only == 1 )); then
      echo "⚠️ WARN-ONLY: violations detected but continuing."
      return 0
    fi
    echo "❌ FAIL: docs deletions exceed threshold."
    echo "   If intentional: use --docs-guard-warn-only, --docs-guard-threshold <n>, or --skip-docs-guard."
    return 1
  fi

  echo "✅ OK: no large doc deletions detected."
  return 0
}

BAD=()
PENDING=()

if [ "$has_json" -eq 1 ]; then
  while IFS=$'\t' read -r name state; do
    case "$state" in
      SUCCESS|SKIPPED|NEUTRAL) ;;
      PENDING|IN_PROGRESS)
        PENDING+=("$name:$state")
        ;;
      FAILURE|ERROR|CANCELLED|TIMED_OUT|ACTION_REQUIRED)
        if is_allowed_fail "$name"; then
          info "Allowed fail: $name ($state)"
        else
          BAD+=("$name:$state")
        fi
        ;;
      *)
        BAD+=("$name:$state")
        ;;
    esac
  done < <(gh pr checks "$PR" --json name,state --jq '.[] | [.name,.state] | @tsv')
else
  # Fallback: textual output (less strict)
  info "gh pr checks --json not supported; falling back to text parsing."
  mapfile -t BAD < <(gh pr checks "$PR" | awk 'BEGIN{IGNORECASE=1} $0 ~ /(fail|cancel|timed out|error)/ {print $0}')
  # We can't reliably detect pending here; rely on --watch if needed.
fi

if [ "${#PENDING[@]}" -gt 0 ]; then
  echo ""
  die "Checks still pending/in progress: ${PENDING[*]} (use --watch)"
fi

if [ "${#BAD[@]}" -gt 0 ]; then
  echo ""
  echo "❌ Failing checks (not allowed):"
  printf ' - %s\n' "${BAD[@]}"
  exit 1
fi

ok "Checks OK (or only allowed fails)."
echo ""

if [ "$DO_MERGE" -eq 0 ]; then
  ok "Review-only complete. Re-run with --merge to merge."
  exit 0
fi

# Run Docs Diff Guard BEFORE merge (safe-by-default)
if [ "$DOCS_GUARD_ENABLED" -eq 1 ]; then
  # If threshold is empty or non-numeric, fail fast
  if ! [[ "${DOCS_GUARD_THRESHOLD}" =~ ^[0-9]+$ ]]; then
    die "--docs-guard-threshold must be an integer (got: '${DOCS_GUARD_THRESHOLD}')"
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    info "DRY-RUN: would run docs diff guard for PR #$PR (threshold=$DOCS_GUARD_THRESHOLD, warn_only=$DOCS_GUARD_WARN_ONLY)"
  else
    docs_diff_guard_pr_files "$PR" "$DOCS_GUARD_THRESHOLD" "$DOCS_GUARD_WARN_ONLY" "$DOCS_GUARD_PREFIX"
  fi
else
  info "⚠️ Docs Diff Guard skipped (--skip-docs-guard)."
fi
echo ""

# Merge
MERGE_ARGS=(--"${METHOD}")
if [ "$DELETE_BRANCH" -eq 1 ]; then
  MERGE_ARGS+=(--delete-branch)
fi

ok "Merging PR #$PR…"
if [ "$DRY_RUN" -eq 1 ]; then
  info "DRY-RUN: gh pr merge $PR ${MERGE_ARGS[*]}"
else
  gh pr merge "$PR" "${MERGE_ARGS[@]}"
fi
echo ""

# Update main
if [ "$UPDATE_MAIN" -eq 1 ]; then
  ok "Updating local main…"
  if [ "$DRY_RUN" -eq 1 ]; then
    info "DRY-RUN: git checkout main && git pull --ff-only"
  else
    git checkout main
    git pull --ff-only
  fi
  echo ""
fi

ok "Done."
