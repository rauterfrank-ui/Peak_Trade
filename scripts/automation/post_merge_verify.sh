#!/usr/bin/env bash
set -euo pipefail

EXPECTED=""
PR=""
MERGE_LOG_PR=""
REMOTE="origin"
BRANCH="main"
SKIP_FETCH=0
RUN_TESTS=0
PYTEST_ARGS="-q"
STRICT=0

usage() {
  cat <<USAGE
post_merge_verify.sh - Post-merge verification

Usage:
  scripts/automation/post_merge_verify.sh [--expected-head <sha>] [options]

Optional:
  --expected-head <sha>     Expected HEAD commit SHA (short or long)
                            If omitted, defaults to origin/main after git fetch
  --pr <number>             Feature PR number (context only)
  --target-pr <number>      Alias for --pr
  --merge-log-pr <number>   PR number that contains merge-log documentation (meta PR)
  --remote <name>           Default: origin
  --branch <name>           Default: main
  --skip-fetch              Do not git fetch
  --run-tests               Run pytest after checks
  --pytest-args "<args>"    Default: -q
  --strict                  Treat warnings as failures where possible
  -h, --help                Show help

Exit codes:
  0  success
  2  usage error
  3  strict fail / warnings treated as failures
  4  HEAD mismatch
  6  tests failed
  10 internal error
USAGE
}

die_usage(){ echo "ERROR: $*" >&2; usage >&2; exit 2; }
internal(){ echo "ERROR: $*" >&2; exit 10; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --expected-head) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --expected-head"; EXPECTED="$1"; shift;;
    --pr|--target-pr) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --pr"; PR="$1"; shift;;
    --merge-log-pr) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --merge-log-pr"; MERGE_LOG_PR="$1"; shift;;
    --remote) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --remote"; REMOTE="$1"; shift;;
    --branch) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --branch"; BRANCH="$1"; shift;;
    --skip-fetch) SKIP_FETCH=1; shift;;
    --run-tests) RUN_TESTS=1; shift;;
    --pytest-args) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --pytest-args"; PYTEST_ARGS="$1"; shift;;
    --strict) STRICT=1; shift;;
    -h|--help) usage; exit 0;;
    *) die_usage "Unknown argument: $1";;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || internal "Not inside a git repository"

# Default EXPECTED to origin/main if not provided
if [[ -z "$EXPECTED" ]]; then
  echo "⚠️  WARN: --expected-head not provided; defaulting to origin/${BRANCH} after git fetch" >&2
  git fetch "$REMOTE" --prune --tags >/dev/null 2>&1 || internal "Failed to fetch ${REMOTE}"
  EXPECTED="$(git rev-parse "${REMOTE}/${BRANCH}")" || internal "Failed to resolve ${REMOTE}/${BRANCH}"
  SKIP_FETCH=1  # Already fetched
fi

HEAD_SHA="$(git rev-parse HEAD)"
HEAD_SHORT="$(git rev-parse --short HEAD)"
eh="$(echo "$EXPECTED" | tr '[:upper:]' '[:lower:]')"
hh="$(echo "$HEAD_SHA" | tr '[:upper:]' '[:lower:]')"

# Prefix-match required: allow short expected hash
if [[ "$hh" == "$eh" || "$hh" == "$eh"* || "$eh" == "$hh"* ]]; then
  :
else
  echo "FAIL: HEAD mismatch"
  echo "  expected: $EXPECTED"
  echo "  actual:   $HEAD_SHA ($HEAD_SHORT)"
  exit 4
fi

warns=()

CUR_BRANCH="$(git branch --show-current 2>/dev/null || true)"
[[ -n "$CUR_BRANCH" ]] || CUR_BRANCH="(detached)"
if [[ "$CUR_BRANCH" == "(detached)" ]]; then
  warns+=("detached_head")
elif [[ "$CUR_BRANCH" != "$BRANCH" ]]; then
  warns+=("wrong_branch:${CUR_BRANCH} (expected ${BRANCH})")
fi

if [[ "$SKIP_FETCH" -eq 0 ]]; then
  if ! git fetch "$REMOTE" --prune --tags >/dev/null 2>&1; then
    warns+=("fetch_failed:${REMOTE}")
  fi
fi

AHEAD=0
BEHIND=0
if git show-ref --verify --quiet "refs/remotes/${REMOTE}/${BRANCH}"; then
  COUNTS="$(git rev-list --left-right --count "HEAD...${REMOTE}/${BRANCH}" 2>/dev/null || echo "0	0")"
  # Use read to parse tab-separated values
  read -r BEHIND AHEAD <<<"$COUNTS"
  if [[ "$AHEAD" != "0" || "$BEHIND" != "0" ]]; then
    warns+=("diverged:ahead=${AHEAD},behind=${BEHIND}")
  fi
else
  warns+=("remote_branch_missing:${REMOTE}/${BRANCH}")
fi

# Optional GH context
GH_OK=0
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    GH_OK=1
  else
    warns+=("gh_auth_unavailable")
  fi
else
  warns+=("gh_not_installed")
fi

if [[ "$GH_OK" -eq 1 ]]; then
  if [[ -n "$PR" ]]; then
    if ! gh pr view "$PR" --json state,mergedAt,title,url >/dev/null 2>&1; then
      warns+=("gh_pr_view_failed:pr=${PR}")
    fi
    if ! gh pr checks "$PR" >/dev/null 2>&1; then
      warns+=("gh_pr_checks_unavailable:pr=${PR}")
    fi
  fi
  if [[ -n "$MERGE_LOG_PR" ]]; then
    if ! gh pr view "$MERGE_LOG_PR" --json state,mergedAt,title,url >/dev/null 2>&1; then
      warns+=("gh_pr_view_failed:merge_log_pr=${MERGE_LOG_PR}")
    fi
  fi
fi

# Strict handling for gh auth failure (as requested pattern)
if [[ "$STRICT" -eq 1 ]]; then
  for w in "${warns[@]}"; do
    if [[ "$w" == "gh_auth_unavailable" ]]; then
      echo "FAIL (strict): gh auth unavailable"
      exit 3
    fi
  done
fi

# Run tests if requested
if [[ "$RUN_TESTS" -eq 1 ]]; then
  if ! command -v pytest >/dev/null 2>&1; then
    echo "FAIL: pytest not found but --run-tests was set"
    exit 6
  fi
  # shellcheck disable=SC2086
  if ! pytest ${PYTEST_ARGS}; then
    echo "FAIL: tests failed"
    exit 6
  fi
fi

echo "Verification Result"
echo "✅ HEAD matches expected: $EXPECTED"
echo "Repo: $(git rev-parse --show-toplevel)"
echo "Branch: $CUR_BRANCH (expected: $BRANCH)"
echo "Divergence vs ${REMOTE}/${BRANCH}: behind=$BEHIND ahead=$AHEAD"

if [[ ${#warns[@]} -gt 0 ]]; then
  echo "⚠️  Warnings:"
  for w in "${warns[@]}"; do echo "  - $w"; done
else
  echo "Warnings: none"
fi

if [[ "$STRICT" -eq 1 && ${#warns[@]} -gt 0 ]]; then
  echo "❌ Strict mode: warnings treated as failures."
  exit 3
fi

exit 0
