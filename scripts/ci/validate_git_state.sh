#!/usr/bin/env bash
set -euo pipefail

REMOTE="origin"
BRANCH="main"
STRICT=0
JSON=0
SKIP_FETCH=0

usage() {
  cat <<USAGE
validate_git_state.sh - Git state validation

Usage:
  scripts/validate_git_state.sh [--remote <name>] [--branch <name>] [--skip-fetch] [--json] [--strict]

Options:
  --remote <name>     Remote name (default: origin)
  --branch <name>     Expected branch name (default: main)
  --skip-fetch        Do not run git fetch
  --json              Emit JSON summary
  --strict            Treat warnings as failures (exit 3)
  -h, --help          Show help

Exit codes:
  0  success (or warnings in graceful mode)
  2  usage error
  3  strict failure (warnings treated as failures)
  10 internal error
USAGE
}

die_usage() { echo "ERROR: $*" >&2; usage >&2; exit 2; }
internal() { echo "ERROR: $*" >&2; exit 10; }

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --remote"; REMOTE="$1"; shift;;
    --branch) shift; [[ $# -gt 0 ]] || die_usage "Missing value for --branch"; BRANCH="$1"; shift;;
    --skip-fetch) SKIP_FETCH=1; shift;;
    --json) JSON=1; shift;;
    --strict) STRICT=1; shift;;
    -h|--help) usage; exit 0;;
    *) die_usage "Unknown argument: $1";;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || internal "Not inside a git repository"
ROOT="$(git rev-parse --show-toplevel)"
HEAD_SHA="$(git rev-parse HEAD)"
CUR_BRANCH="$(git branch --show-current 2>/dev/null || true)"
[[ -n "$CUR_BRANCH" ]] || CUR_BRANCH="(detached)"

PORCELAIN="$(git status --porcelain || true)"
DIRTY=0
[[ -n "$PORCELAIN" ]] && DIRTY=1

warns=()
if [[ "$CUR_BRANCH" == "(detached)" ]]; then
  warns+=("detached_head")
fi
if [[ "$DIRTY" -eq 1 ]]; then
  warns+=("working_tree_dirty")
fi
if [[ "$CUR_BRANCH" != "$BRANCH" && "$CUR_BRANCH" != "(detached)" ]]; then
  warns+=("wrong_branch:${CUR_BRANCH}")
fi

FETCH_OK=1
if [[ "$SKIP_FETCH" -eq 0 ]]; then
  if ! git fetch "$REMOTE" --prune --tags >/dev/null 2>&1; then
    FETCH_OK=0
    warns+=("fetch_failed:${REMOTE}")
  fi
fi

AHEAD=0
BEHIND=0
REMOTE_REF="refs/remotes/${REMOTE}/${BRANCH}"
if git show-ref --verify --quiet "$REMOTE_REF"; then
  # rev-list format: "<behind>\t<ahead>" for HEAD...REMOTE when using left-right --count
  COUNTS="$(git rev-list --left-right --count "HEAD...${REMOTE}/${BRANCH}" 2>/dev/null || echo "0	0")"
  # Use read to parse tab-separated values
  read -r BEHIND AHEAD <<<"$COUNTS"
  if [[ "$AHEAD" != "0" || "$BEHIND" != "0" ]]; then
    warns+=("diverged:ahead=${AHEAD},behind=${BEHIND}")
  fi
else
  warns+=("remote_branch_missing:${REMOTE}/${BRANCH}")
fi

OK=1
EXIT=0
if [[ "$STRICT" -eq 1 && ${#warns[@]} -gt 0 ]]; then
  OK=0
  EXIT=3
fi

if [[ "$JSON" -eq 1 ]]; then
  # Convert bash array to JSON array
  warns_json="["
  for i in "${!warns[@]}"; do
    [[ $i -gt 0 ]] && warns_json+=","
    warns_json+="\"${warns[$i]}\""
  done
  warns_json+="]"

  cat <<JSON
{
  "ok": ${OK},
  "strict": ${STRICT},
  "repo_root": "${ROOT}",
  "head": "${HEAD_SHA}",
  "current_branch": "${CUR_BRANCH}",
  "expected_branch": "${BRANCH}",
  "remote": "${REMOTE}",
  "skip_fetch": ${SKIP_FETCH},
  "fetch_ok": ${FETCH_OK},
  "dirty": ${DIRTY},
  "divergence": {"ahead": ${AHEAD}, "behind": ${BEHIND}},
  "warnings": ${warns_json}
}
JSON
else
  echo "Repo: $ROOT"
  echo "HEAD: $HEAD_SHA"
  echo "Branch: $CUR_BRANCH (expected: $BRANCH)"
  echo "Dirty: $DIRTY"
  echo "Remote: $REMOTE  FetchOK: $FETCH_OK  Divergence: ahead=$AHEAD behind=$BEHIND"
  if [[ ${#warns[@]} -gt 0 ]]; then
    echo "Warnings:"
    for w in "${warns[@]}"; do echo "  - $w"; done
  else
    echo "Warnings: none"
  fi
  if [[ "$STRICT" -eq 1 && ${#warns[@]} -gt 0 ]]; then
    echo "Strict mode: FAIL"
  else
    echo "Result: OK"
  fi
fi

exit "$EXIT"
