#!/usr/bin/env bash
set -euo pipefail

# pr_safe_flow.sh — guardrailed gh PR create/merge flow
#
# Goals:
# - Never create/merge from main
# - Require clean working tree
# - Verify gh auth + GitHub API reachability (via your preflight)
# - Make upstream explicit
# - Require explicit confirmation for merge automation
#
# Usage:
#   ./scripts/ops/pr_safe_flow.sh preflight
#   ./scripts/ops/pr_safe_flow.sh create --fill
#   PT_CONFIRM_MERGE=YES ./scripts/ops/pr_safe_flow.sh automerge --squash --delete-branch
#   ./scripts/ops/pr_safe_flow.sh status
#   ./scripts/ops/pr_safe_flow.sh sync-main
#   ./scripts/ops/pr_safe_flow.sh cleanup-local

_grep() { if command -v rg >/dev/null 2>&1; then rg "$@"; else grep -E "$@"; fi; }

die() { echo "ERROR: $*" >&2; exit 2; }

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || die "not in a git repo"
}

branch() {
  git branch --show-current 2>/dev/null || true
}

ensure_not_main() {
  local b; b="$(branch)"
  [[ -n "$b" ]] || die "cannot determine current branch"
  [[ "$b" != "main" ]] || die "refusing on branch 'main' (create a feature branch)"
}

ensure_clean() {
  # fail if staged/unstaged changes exist (untracked allowed, but warned)
  local s; s="$(git status --porcelain=v1 2>/dev/null || true)"
  if echo "$s" | _grep -q '^[ MARCUDT?!]{1,2}'; then
    # allow only untracked (??) lines
    if echo "$s" | _grep -vq '^\?\? '; then
      git status -sb || true
      die "working tree not clean (commit/stash first)"
    fi
  fi
}

warn_untracked() {
  local u
  u="$(git status --porcelain=v1 2>/dev/null | _grep '^\?\? ' || true)"
  if [[ -n "$u" ]]; then
    echo "WARN: untracked files present (ok):"
    echo "$u"
  fi
}

ensure_upstream() {
  # ensure current branch has an upstream; if not, instruct
  if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
    echo "INFO: no upstream set for this branch."
    echo "Run: git push -u origin HEAD"
    return 1
  fi
  return 0
}

preflight() {
  local root; root="$(repo_root)"
  cd "$root"

  echo "== preflight =="
  ./out/ops/gh_tls/gh_preflight.sh

  echo "== git =="
  git status -sb
  git fetch origin --prune >/dev/null 2>&1 || true
  echo "HEAD:       $(git rev-parse --short HEAD)"
  echo "origin/main:$(git rev-parse --short origin/main 2>/dev/null || echo N/A)"

  echo "== gh =="
  gh auth status
  gh api rate_limit >/dev/null
  echo "OK"
}

create_pr() {
  ensure_not_main
  ensure_clean
  warn_untracked

  # ensure pushed
  if ! ensure_upstream; then
    die "no upstream set; push first: git push -u origin HEAD"
  fi

  echo "== gh pr create =="
  # default flags
  if [[ $# -eq 0 ]]; then
    gh pr create --fill
  else
    gh pr create "$@"
  fi

  echo "== pr status =="
  gh pr status
  gh pr view --web || true
}

automerge_pr() {
  ensure_not_main
  ensure_clean

  [[ "${PT_CONFIRM_MERGE:-}" == "YES" ]] || die "set PT_CONFIRM_MERGE=YES to enable merge automation"

  echo "== gh pr merge (auto) =="
  # default flags
  if [[ $# -eq 0 ]]; then
    gh pr merge --squash --auto --delete-branch
  else
    gh pr merge --auto "$@"
  fi

  gh pr view --json number,state,autoMergeRequest --jq '{number,state,autoMergeEnabled:(.autoMergeRequest.enabledAt!=null)}'
}

status_pr() {
  echo "== gh pr status =="
  gh pr status || true
  echo "== gh pr checks (current branch) =="
  gh pr checks || true
}

sync_main() {
  local root; root="$(repo_root)"
  cd "$root"
  git checkout main
  git fetch origin --prune
  git pull --ff-only origin main
  git status -sb
  git log -1 --oneline
}

cleanup_local() {
  # If current branch is merged, delete local branch safely.
  ensure_not_main
  local b; b="$(branch)"

  # Determine if merged (best-effort)
  local st
  st="$(gh pr view --json state --jq .state 2>/dev/null || true)"
  if [[ "$st" != "MERGED" ]]; then
    echo "INFO: PR state is '$st' (not MERGED) — refusing to delete local branch '$b'"
    exit 0
  fi

  echo "== cleanup local branch =="
  git checkout main
  git fetch origin --prune
  git pull --ff-only origin main
  git branch -D "$b" || true
  git status -sb
}

usage() {
  cat <<USAGE
Usage:
  $0 preflight
  $0 create [--fill|other gh pr create args]
  PT_CONFIRM_MERGE=YES $0 automerge [--squash --delete-branch | other gh pr merge args]
  $0 status
  $0 sync-main
  $0 cleanup-local
USAGE
}

main() {
  local cmd="${1:-}"; shift || true
  case "$cmd" in
    preflight) preflight "$@" ;;
    create)    create_pr "$@" ;;
    automerge) automerge_pr "$@" ;;
    status)    status_pr "$@" ;;
    sync-main) sync_main "$@" ;;
    cleanup-local) cleanup_local "$@" ;;
    -h|--help|"") usage ;;
    *) die "unknown command: $cmd" ;;
  esac
}

main "$@"
