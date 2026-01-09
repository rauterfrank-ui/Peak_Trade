#!/usr/bin/env bash
set -euo pipefail

# 4B Milestone 2 — Worktree Setup
# Usage:
#   bash scripts/ops/setup_worktree_4b_m2.sh /Users/frnkhrz/Peak_Trade
#
# Notes:
# - If you are stuck in a continuation prompt (>, dquote>, heredoc>): press Ctrl-C first.

REPO_ROOT="${1:-}"
if [[ -z "${REPO_ROOT}" ]]; then
  echo "ERROR: Provide repo root path as first argument."
  echo "Example: bash scripts/ops/setup_worktree_4b_m2.sh /Users/frnkhrz/Peak_Trade"
  exit 2
fi

echo "== Pre-flight =="
cd "${REPO_ROOT}"
pwd
git rev-parse --show-toplevel
git status -sb

echo "== Fetch origin =="
git fetch origin --prune

WT_BASE="${HOME}/.cursor-worktrees/Peak_Trade"
WT_PATH="${WT_BASE}/4b-m2"
BRANCH="feat/4b-m2-cursor-multi-agent"

mkdir -p "${WT_BASE}"

echo "== Create worktree =="
if [[ -d "${WT_PATH}/.git" || -d "${WT_PATH}" ]]; then
  echo "Worktree path already exists: ${WT_PATH}"
  echo "If you want a clean recreate, remove it manually:"
  echo "  rm -rf \"${WT_PATH}\""
else
  git worktree add "${WT_PATH}" -b "${BRANCH}" origin/main
fi

echo "== Initialize session artifacts in worktree =="
cd "${WT_PATH}"
pwd
git rev-parse --show-toplevel
git status -sb

mkdir -p docs/ops/sessions

STAMP="$(date +%Y%m%d)"
LOG="docs/ops/sessions/SESSION_4B_M2_${STAMP}.md"
BOARD="docs/ops/sessions/SESSION_4B_M2_TASKBOARD.md"
DECISIONS="docs/ops/sessions/SESSION_4B_M2_DECISIONS.md"

if [[ ! -f "${LOG}" ]]; then
  cat > "${LOG}" <<EOF
# SESSION 4B M2 — ${STAMP}

## Objective
- Prepare Cursor Multi-Agent Chat workspace for 4B Milestone 2.

## Verification
- [ ] ruff format --check
- [ ] ruff check
- [ ] pytest -q (targeted)

## Notes
EOF
fi

if [[ ! -f "${BOARD}" ]]; then
  cat > "${BOARD}" <<'EOF'
# 4B M2 — TASKBOARD

## P0 (Must)
- [ ] Worktree clean & on feat/4b-m2-cursor-multi-agent
- [ ] Cursor Multi-Agent system prompt pasted + roles assigned
- [ ] Minimal gates runnable locally (ruff + pytest subset)
- [ ] PR skeleton prepared

## P1 (Should)
- [ ] Audit gate status clarified (pip-audit ok OR remediation plan)
- [ ] Docs gates safe (no accidental path-like references)

## P2 (Nice)
- [ ] Session decisions logged
EOF
fi

if [[ ! -f "${DECISIONS}" ]]; then
  cat > "${DECISIONS}" <<EOF
# 4B M2 — DECISIONS (${STAMP})

Record trade-offs and rationale:
- Date:
- Decision:
- Options considered:
- Rationale:
- Follow-up:
EOF
fi

echo "== Done =="
echo "Worktree: ${WT_PATH}"
echo "Branch:   ${BRANCH}"
echo "Artifacts:"
echo "  - ${LOG}"
echo "  - ${BOARD}"
echo "  - ${DECISIONS}"
