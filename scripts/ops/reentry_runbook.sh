#!/usr/bin/env bash
# Cursor Multi-Agent Orchestration — Runbook-Fortsetzung (auto-reentry)
# Goal: read-only status harvest → infer likely entrypoint → execute next step (still guarded / non-destructive by default)
# NOTE: This script writes ONLY to out/ops/reentry_* (local artifacts). No git changes unless you explicitly run optional sections.

set -euo pipefail

# -------------------------------
# [AGENT:planner] 0) Workspace + evidence dir
# -------------------------------
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

TS="$(date +%Y%m%d_%H%M%S)"
OUT="out/ops/reentry_${TS}"
mkdir -p "$OUT"

echo "OUT=$OUT" | tee "$OUT/00_path.txt"
pwd | tee -a "$OUT/00_path.txt"

# -------------------------------
# [AGENT:planner] 1) Invariants (read-only)
# -------------------------------
{
  echo "## gh_preflight"
  ./out/ops/gh_tls/gh_preflight.sh || true
  echo
  echo "## git status"
  git status -sb || true
  echo
  echo "## fetch origin --prune"
  git fetch origin --prune || true
  echo
  echo "## git log -10"
  git log -10 --oneline --decorate || true
  echo
  echo "## current branch"
  git branch --show-current || true
} | tee "$OUT/01_invariants.txt"

# -------------------------------
# [AGENT:planner] 2) Runbook index discovery (read-only)
# -------------------------------
{
  echo "## docs/ops/runbooks (ls)"
  ls -la docs/ops/runbooks 2>/dev/null || true
  echo
  echo "## docs/ops (ls)"
  ls -la docs/ops 2>/dev/null || true
  echo
  echo "## runbook markdown inventory"
  ls -la docs/ops/runbooks/*.md 2>/dev/null || true
} | tee "$OUT/02_runbook_index.txt"

# -------------------------------
# [AGENT:planner] 3) Recent ops artifacts (read-only)
# -------------------------------
{
  echo "## out/ops recent files (top 120 lines)"
  find out/ops -maxdepth 6 -type f -print0 2>/dev/null \
    | xargs -0 ls -lt 2>/dev/null \
    | sed -n '1,120p' || true
} | tee "$OUT/03_recent_ops_artifacts.txt"

# -------------------------------
# [AGENT:planner] 4) Marker search (read-only)
# -------------------------------
{
  echo "## markers (RUNBOOK|closeout|checkpoint|next step|TODO|P\\d+|Phase|EVIDENCE|NO-OP)"
  ( rg -n "RUNBOOK|closeout|checkpoint|next step|TODO|P\\d+|Phase|EVIDENCE|NO-OP" docs out/ops scripts .cursor 2>/dev/null || true ) \
    | sed -n '1,220p'
} | tee "$OUT/04_marker_search.txt"

# -------------------------------
# [AGENT:planner] 5) Discover "likely entrypoints" (read-only heuristics)
# -------------------------------
{
  echo "## likely entrypoints (top recent runbook-ish artifacts)"
  find out/ops -maxdepth 6 -type f 2>/dev/null \
    | rg -n "(RUNBOOK|runbook|closeout|checkpoint|EVIDENCE|DONE|CLOSEOUT|BOOTSTRAP|P\\d+)" -S || true

  echo
  echo "## last 30 modified markdowns under docs/ops"
  find docs/ops -type f -name "*.md" -print0 2>/dev/null \
    | xargs -0 ls -lt 2>/dev/null \
    | sed -n '1,60p' || true

  echo
  echo "## last 30 modified ops artifacts under out/ops"
  find out/ops -type f -print0 2>/dev/null \
    | xargs -0 ls -lt 2>/dev/null \
    | sed -n '1,60p' || true
} | tee "$OUT/05_entrypoints_heuristics.txt"

# -------------------------------
# [AGENT:implementer] 6) PR/Branch situation (read-only; uses gh if available)
# -------------------------------
{
  echo "## branches (local, recent)"
  git branch --sort=-committerdate | sed -n '1,80p' || true
  echo
  echo "## remotes (recent heads)"
  git for-each-ref --sort=-committerdate --format='%(committerdate:iso8601) %(refname:short)' refs/remotes/origin \
    | sed -n '1,80p' || true

  echo
  echo "## gh auth/status (best-effort)"
  gh auth status || true

  echo
  echo "## gh PRs (open; best-effort)"
  gh pr list --limit 30 || true

  echo
  echo "## gh checks on current branch PR (best-effort)"
  gh pr view --json number,url,headRefName,baseRefName,state,mergeable,reviewDecision,statusCheckRollup 2>/dev/null || true
} | tee "$OUT/06_pr_branch_state.txt"

# -------------------------------
# [AGENT:critic] 7) Safety gates + wrapper discovery (read-only)
# -------------------------------
{
  echo "## wrapper presence"
  ls -la scripts/ops/pr_safe_flow.sh 2>/dev/null || true
  echo
  echo "## wrapper help (best-effort)"
  scripts/ops/pr_safe_flow.sh --help 2>/dev/null || true
  echo
  echo "## governance helpers (best-effort)"
  ls -la scripts/governance 2>/dev/null || true
  echo
  echo "## known closeout helper (best-effort)"
  ls -la scripts/governance/post_merge_closeout.sh 2>/dev/null || true
  echo
  echo "## MA ops cli (best-effort)"
  ls -la scripts/ops/ma scripts/ops/ma.py 2>/dev/null || true
} | tee "$OUT/07_wrappers_and_gates.txt"

# -------------------------------
# [AGENT:planner] 8) Decide next step automatically (non-destructive plan output)
# -------------------------------
CUR_BRANCH="$(git branch --show-current 2>/dev/null || echo "")"
IS_DIRTY="no"
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then IS_DIRTY="yes"; fi

{
  echo "CUR_BRANCH=$CUR_BRANCH"
  echo "IS_DIRTY=$IS_DIRTY"
  echo
  if [ "$IS_DIRTY" = "yes" ]; then
    echo "NEXT=STABILIZE_WORKTREE"
    echo "ACTION: inspect diff, decide stash/commit/discard (manual)."
  elif [ "$CUR_BRANCH" != "main" ] && [ -n "$CUR_BRANCH" ]; then
    echo "NEXT=RESUME_CURRENT_BRANCH"
    echo "ACTION: run local checks; if PR exists, inspect checks; else create PR via wrapper."
  else
    echo "NEXT=SELECT_ENTRYPOINT_FROM_ARTIFACTS"
    echo "ACTION: open most recent runbook/closeout artifact; then either closeout or start next P-step."
  fi
} | tee "$OUT/08_next_step_decision.txt"

# -------------------------------
# [AGENT:implementer] 9) Execute "next step" (still guarded)
# -------------------------------
# 9A) If dirty: show diffs (read-only) and stop.
if [ "$IS_DIRTY" = "yes" ]; then
  {
    echo "## WORKTREE DIRTY — READ-ONLY DIFFS"
    git status -sb || true
    echo
    echo "## staged diff (if any)"
    git diff --cached | sed -n '1,240p' || true
    echo
    echo "## unstaged diff (if any)"
    git diff | sed -n '1,240p' || true
    echo
    echo "STOP: Do not proceed until stabilized."
  } | tee "$OUT/09A_dirty_stop.txt"
  exit 0
fi

# 9B) If on non-main branch: run local preflight checks (best-effort, non-network except gh already used)
if [ "$CUR_BRANCH" != "main" ] && [ -n "$CUR_BRANCH" ]; then
  {
    echo "## RESUME BRANCH: $CUR_BRANCH"
    echo "## quick sanity"
    git status -sb
    echo
    echo "## ruff/pytest (best-effort; adjust if your repo uses different commands)"
    command -v ruff >/dev/null 2>&1 && ruff --version || true
    command -v pytest >/dev/null 2>&1 && pytest --version || true
  } | tee "$OUT/09B_resume_branch_sanity.txt"

  # Optional: run project-specific make targets if present (still local)
  {
    echo "## make targets (best-effort)"
    test -f Makefile && ( make -n governance-gate 2>/dev/null || true ) || true
  } | tee "$OUT/09B_make_targets.txt"

  # Wrapper-driven PR flow (DRY help only; actual run requires you to choose flags after seeing --help output)
  {
    echo "## PR SAFE FLOW wrapper — show help again"
    scripts/ops/pr_safe_flow.sh --help 2>/dev/null || true
  echo
  echo "## Suggested (MANUAL EXEC) after reviewing help:"
  echo "# scripts/ops/pr_safe_flow.sh preflight"
  echo "# scripts/ops/pr_safe_flow.sh create --fill"
  echo "# PT_CONFIRM_MERGE=YES scripts/ops/pr_safe_flow.sh automerge --squash --delete-branch  # only if policy allows + checks green"
  } | tee "$OUT/09B_pr_safe_flow_suggested.txt"

  exit 0
fi

# 9C) On main & clean: open the most recent runbook/closeout/checkpoint file (read-only print)
{
  echo "## MAIN CLEAN — OPEN MOST RECENT ENTRYPOINT CANDIDATE (print head)"
  CAND="$(find out/ops -maxdepth 6 -type f 2>/dev/null \
    | rg -n "(RUNBOOK|runbook|closeout|checkpoint|EVIDENCE|DONE|CLOSEOUT|BOOTSTRAP|P\\d+)" -S \
    | head -n 1 \
    | awk -F: '{print $1}')"

  if [ -n "${CAND:-}" ] && [ -f "$CAND" ]; then
    echo "CANDIDATE_FILE=$CAND"
    echo
    echo "----- FILE HEAD (1..220) -----"
    sed -n '1,220p' "$CAND" || true
  else
    echo "NO_CANDIDATE_FILE_FOUND"
    echo "Fallback: print runbook index top-of-file for likely entrypoints."
    echo
    for f in docs/ops/runbooks/*.md; do
      [ -f "$f" ] || continue
      echo "----- $f (1..60) -----"
      sed -n '1,60p' "$f" || true
      echo
    done
  fi
} | tee "$OUT/09C_open_entrypoint_candidate.txt"

# 9D) Prepare a new work branch (NO CHECKOUT by default; just prints safe commands)
{
  echo "## NEXT (MANUAL) — create a new branch once you identify the next runbook step"
  echo "# git checkout -b feat/<next-step-slug>"
  echo "# git push -u origin feat/<next-step-slug>"
  echo "# scripts/ops/pr_safe_flow.sh --help   # pick safe mode first"
} | tee "$OUT/09D_next_manual_commands.txt"

echo "DONE: Collected reentry evidence under: $OUT"
