#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") <branch-name>

Creates a new branch from origin/main with hygiene checks:
- working tree must be clean
- local main must NOT be ahead of origin/main (prevents accidental unpushed commits)
- fetches origin and uses origin/main as the base
USAGE
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

BRANCH="$1"

# Ensure clean working tree
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree not clean. Commit/stash first."
  git status --porcelain
  exit 1
fi

# Ensure we are on main
CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT" != "main" ]]; then
  echo "ℹ️ Switching to main (was: $CURRENT)"
  git checkout main
fi

# Update origin refs
git fetch origin

# Prevent drift: local main ahead of origin/main
AHEAD="$(git rev-list --count origin/main..main || echo 0)"
BEHIND="$(git rev-list --count main..origin/main || echo 0)"

if [[ "${AHEAD}" != "0" ]]; then
  echo "❌ local main is AHEAD of origin/main by ${AHEAD} commit(s)."
  echo "   This usually means you have local unpushed commits. Push them or reset main before branching."
  echo ""
  echo "   Inspect:"
  echo "     git log --oneline --decorate -n 20 origin/main..main"
  echo ""
  echo "   Options:"
  echo "     # (A) Push commits (if intended)"
  echo "     git push origin main"
  echo "     # (B) Reset local main to origin/main (DANGER if you want to keep local commits)"
  echo "     git reset --hard origin/main"
  exit 1
fi

if [[ "${BEHIND}" != "0" ]]; then
  echo "ℹ️ local main is BEHIND origin/main by ${BEHIND} commit(s). Fast-forwarding."
  git pull --ff-only
fi

# Create branch from origin/main explicitly
git switch -c "$BRANCH" origin/main
echo "✅ Created branch '$BRANCH' from origin/main"
