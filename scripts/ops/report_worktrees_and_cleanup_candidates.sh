#!/usr/bin/env bash
# scripts/ops/report_worktrees_and_cleanup_candidates.sh
#
# ZWECK: Report-only Analyse von Worktrees und Branches mit Cleanup-Kandidaten.
#        KEINE LÖSCHUNGEN. Nur Empfehlungen ausgeben.
#
# USAGE:
#   scripts/ops/report_worktrees_and_cleanup_candidates.sh
#
# EXIT CODES:
#   0 = Success (Report erfolgreich generiert)
#   1 = Fehler (z.B. nicht im Git-Repo)
#
# SAFETY:
#   - Kein "set -e" (weiter reporten auch bei Teilfehlern)
#   - Kein "exit 1" ohne klare Diagnose
#   - Jede Sektion mit klarem Heading

set -uo pipefail

# ============================================================================
# Pre-Flight Check
# ============================================================================

echo "========================================"
echo "== Worktree & Branch Cleanup Report =="
echo "========================================"
echo ""

echo "== Pre-Flight =="
echo "Working Directory: $(pwd)"

# Git Repo Root prüfen
if ! git rev-parse --show-toplevel &>/dev/null; then
  echo "❌ ERROR: Not in a Git repository."
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
echo "Repo Root: $REPO_ROOT"
echo ""

# Git Status
echo "== Git Status =="
git status -sb
echo ""

# ============================================================================
# Worktrees
# ============================================================================

echo "== Worktrees =="
if git worktree list &>/dev/null; then
  WORKTREE_COUNT="$(git worktree list | wc -l | xargs)"
  echo "Total Worktrees: $WORKTREE_COUNT"
  echo ""
  git worktree list
  echo ""

  if [[ "$WORKTREE_COUNT" -gt 1 ]]; then
    echo "ℹ️  Multiple worktrees detected."
    echo "   → To remove: git worktree remove <path>"
    echo "   → To prune stale refs: git worktree prune"
    echo ""
  fi
else
  echo "ℹ️  No worktrees found (or git worktree command not available)."
  echo ""
fi

# ============================================================================
# Branches (Local)
# ============================================================================

echo "== Local Branches =="
BRANCH_COUNT="$(git branch --list | wc -l | xargs)"
echo "Total Local Branches: $BRANCH_COUNT"
echo ""

if [[ "$BRANCH_COUNT" -gt 10 ]]; then
  echo "Showing first 10 branches (sorted by last commit date):"
  git branch --sort=-committerdate | head -10
  echo ""
  echo "ℹ️  More than 10 branches. Use 'git branch -vv' for full list."
else
  echo "All Local Branches:"
  git branch --sort=-committerdate
fi
echo ""

# ============================================================================
# Cleanup Candidates (Reachable in main)
# ============================================================================

echo "== Cleanup Candidates (Branches reachable in main) =="

# Sicherstellen, dass main existiert
if ! git rev-parse main &>/dev/null; then
  echo "⚠️  WARNING: 'main' branch not found. Skipping reachability check."
  echo ""
else
  # Alle lokalen Branches (außer main und current branch)
  CURRENT_BRANCH="$(git branch --show-current)"
  CANDIDATES=()

  # Iterate über alle Branches
  while IFS= read -r branch; do
    # Branch-Namen trimmen (git branch gibt leading "  " oder "* ")
    branch_clean="$(echo "$branch" | sed 's/^[* ] //')"

    # Skip main und current branch
    if [[ "$branch_clean" == "main" || "$branch_clean" == "$CURRENT_BRANCH" ]]; then
      continue
    fi

    # Tip-Commit des Branch
    if ! SHA="$(git rev-parse "$branch_clean" 2>/dev/null)"; then
      echo "⚠️  Could not parse SHA for branch: $branch_clean"
      continue
    fi

    # Reachability-Check
    if git merge-base --is-ancestor "$SHA" main 2>/dev/null; then
      CANDIDATES+=("$branch_clean")
      echo "✅ Candidate: $branch_clean (tip: ${SHA:0:8}, already in main)"
    fi
  done < <(git branch --list)

  echo ""
  if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
    echo "ℹ️  No cleanup candidates found."
    echo "   (All non-main branches have commits NOT yet in main, or no branches exist.)"
  else
    echo "ℹ️  Found ${#CANDIDATES[@]} cleanup candidate(s)."
    echo ""
    echo "RECOMMENDED ACTIONS (manual):"
    for cand in "${CANDIDATES[@]}"; do
      echo "  git branch -d $cand"
    done
    echo ""
    echo "⚠️  SAFETY: Only delete after verifying with 'git log --all --decorate --oneline --graph'."
  fi
fi

echo ""

# ============================================================================
# Branches NOT in main (Warning)
# ============================================================================

echo "== Branches NOT yet in main (DO NOT DELETE) =="

if ! git rev-parse main &>/dev/null; then
  echo "⚠️  WARNING: 'main' branch not found. Skipping."
  echo ""
else
  NOT_IN_MAIN=()

  while IFS= read -r branch; do
    branch_clean="$(echo "$branch" | sed 's/^[* ] //')"

    if [[ "$branch_clean" == "main" || "$branch_clean" == "$CURRENT_BRANCH" ]]; then
      continue
    fi

    if ! SHA="$(git rev-parse "$branch_clean" 2>/dev/null)"; then
      continue
    fi

    if ! git merge-base --is-ancestor "$SHA" main 2>/dev/null; then
      NOT_IN_MAIN+=("$branch_clean")
      echo "⚠️  $branch_clean (tip: ${SHA:0:8}, NOT in main)"
    fi
  done < <(git branch --list)

  echo ""
  if [[ ${#NOT_IN_MAIN[@]} -eq 0 ]]; then
    echo "ℹ️  All branches are in main (safe state)."
  else
    echo "ℹ️  Found ${#NOT_IN_MAIN[@]} branch(es) with commits NOT in main."
    echo "   → These branches should NOT be deleted until merged."
  fi
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "== Summary =="
echo "Worktrees: $WORKTREE_COUNT"
echo "Local Branches: $BRANCH_COUNT"
echo "Cleanup Candidates (in main): ${#CANDIDATES[@]:-0}"
echo "Branches NOT in main: ${#NOT_IN_MAIN[@]:-0}"
echo ""
echo "✅ Report complete. No changes made."
echo ""
echo "NEXT STEPS:"
echo "  1) Review candidates listed above."
echo "  2) Verify with: git log --all --decorate --oneline --graph"
echo "  3) Delete manually (only after verification):"
echo "     git branch -d <branch-name>"
echo "  4) For worktrees: git worktree remove <path>"
echo ""
echo "See: docs/ops/runbooks/rebase_cleanup_workflow.md"
echo ""

exit 0
