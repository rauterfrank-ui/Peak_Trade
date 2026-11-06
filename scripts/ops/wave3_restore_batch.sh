#!/usr/bin/env bash
# scripts/ops/wave3_restore_batch.sh
# Wave3 Restore Queue – Batch Processing Helper
# Usage: ./scripts/ops/wave3_restore_batch.sh [tier-a|tier-b|tier-c|check-dupes|cleanup]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Tier A: Merge Log Backlog (11 branches)
TIER_A_MERGE_LOGS=(
  "docs/add-pr569-readme-link"
  "docs/merge-log-pr488"
  "docs/cursor-multi-agent-phase4-runner"
  "docs/merge-log-pr-350-docs-reference-targets-golden-corpus"
  "docs/ops-pr206-merge-log"
  "docs/ops-merge-both-prs-dryrun-workflow"
  "docs/ops/pr-87-merge-log"
  "docs/ops/pr-92-merge-log"
  "docs/ops/pr-93-merge-log"
  "docs/pr-76-merge-log"
  "docs/ops-pr-85-merge-log"
)

# Tier A: Runbooks & Standards (6 branches)
TIER_A_RUNBOOKS=(
  "docs/github-rulesets-runbook"
  "docs/frontdoor-roadmap-runner"
  "docs/fix-moved-script-paths-phase1"
  "docs/ops-doctor-noise-free-standard"
  "docs/ops-worktree-policy"
  "docs/ops-audit-logs-convention"
)

# Tier A: Roadmaps & Housekeeping (5 branches)
TIER_A_ROADMAPS=(
  "reboot/from-pr-380"
  "docs/ops-docs-reference-targets-supported-formats"
  "docs/pr-74-delivery-note"
  "docs/pr-66-finalization"
  "docs/pr-63-finalization"
)

# Tier A: Tooling (1 branch)
TIER_A_TOOLING=(
  "feat/ops-merge-log-tooling-v1"
)

# Tier A: Duplicate/Stale (check these first!)
TIER_A_DUPES=(
  "beautiful-ritchie"
  "busy-cerf"
  "determined-matsumoto"
  "keen-aryabhata"
  "serene-elbakyan"
)

# Tier A: Conflict Merges (check if obsolete!)
TIER_A_CONFLICTS=(
  "condescending-rubin"
  "dazzling-gates"
  "sweet-kapitsa"
  "magical-tesla"
)

# Tier B: Tests/CI (12 branches)
TIER_B_ALL=(
  "feat/execution-pipeline-fill-idempotency"
  "fix/ci-required-checks-docs-prs"
  "chore/github-guardrails-p0-only"
  "chore/github-guardrails-p0"
  "test/p0-guardrails-drill"
  "chore/tooling-uv-ruff"
  "chore/cleanup-gitignore-reports"
  "pr-72"
  "fix/requirements-txt-sync-correct-flags"
  "nervous-wilbur"
  "test/ci-gate-block-trigger"
)

# Tier C: DO NOT AUTO-MERGE (8 branches)
TIER_C_ALL=(
  "pr-334-rebase"
  "feat/risk-liquidity-gate-v1"
  "feat/phase-9b-rolling-backtests"
  "feat/strategy-layer-vnext-tracking"
  "vigilant-thompson"
  "stupefied-montalcini"
  "feat/phase-57-live-status-snapshot-builder-api"
  "feat/governance-g4-telemetry-automation"
)

# Tier X: DELETE candidates
TIER_X_WIP=(
  "wip/stash-archive-20251227_010347_3"
  "wip/stash-archive-20251227_010344_2"
  "wip/stash-archive-20251227_010341_1"
  "wip/stash-archive-20251227_010316_0"
  "wip/untracked-salvage-20251224_081737"
  "wip/salvage-code-tests-untracked-20251224_082521"
)

# Function: Check if branch exists
branch_exists() {
  local branch=$1
  git rev-parse --verify "origin/$branch" >/dev/null 2>&1
}

# Function: Check if already merged
is_merged() {
  local branch=$1
  git merge-base --is-ancestor "origin/$branch" origin/main 2>/dev/null
}

# Function: Process single branch (rebase + PR)
process_branch() {
  local branch=$1
  local tier=$2

  log_info "Processing: $branch (Tier $tier)"

  # Check if exists
  if ! branch_exists "$branch"; then
    log_warn "Branch origin/$branch does not exist, skipping"
    return 1
  fi

  # Check if already merged
  if is_merged "$branch"; then
    log_success "Branch $branch already merged, skipping"
    return 0
  fi

  # Create local restore branch
  local restore_branch="restore/wave3/$branch"
  log_info "Creating restore branch: $restore_branch"

  git checkout -b "$restore_branch" "origin/$branch" || {
    log_error "Failed to checkout $branch"
    return 1
  }

  # Rebase onto main
  log_info "Rebasing onto main..."
  if ! git rebase origin/main; then
    log_error "Rebase conflict on $branch"
    log_warn "Manual resolution required. Aborting rebase."
    git rebase --abort
    git checkout main
    git branch -D "$restore_branch" 2>/dev/null || true
    return 1
  fi

  # Show diff stats
  log_info "Changes in this branch:"
  git diff origin/main --stat | head -20

  # Verify docs (Tier A only)
  if [[ "$tier" == "A" ]] && [[ -f Makefile ]]; then
    log_info "Running docs validation..."
    if make docs-validate 2>/dev/null; then
      log_success "Docs validation passed"
    else
      log_warn "Docs validation failed (non-blocking for now)"
    fi
  fi

  # Run tests (Tier B/C)
  if [[ "$tier" == "B" || "$tier" == "C" ]]; then
    log_info "Running tests..."
    if make test 2>/dev/null; then
      log_success "Tests passed"
    else
      log_error "Tests failed on $branch"
      git checkout main
      git branch -D "$restore_branch" 2>/dev/null || true
      return 1
    fi
  fi

  log_success "Branch $branch processed successfully"
  log_info "Next: Create PR with 'gh pr create' or push with 'git push -u origin $restore_branch'"

  # Stay on restore branch for review
  return 0
}

# Function: Batch process multiple branches
batch_process() {
  local tier=$1
  shift
  local branches=("$@")

  local success_count=0
  local fail_count=0
  local skip_count=0

  log_info "Starting batch processing: ${#branches[@]} branches (Tier $tier)"

  # Ensure we're on main
  git checkout main
  git fetch --prune origin

  for branch in "${branches[@]}"; do
    log_info "=== Branch $((success_count + fail_count + skip_count + 1))/${#branches[@]}: $branch ==="

    if process_branch "$branch" "$tier"; then
      ((success_count++))
      # Return to main for next branch
      git checkout main 2>/dev/null || true
    else
      if is_merged "$branch" 2>/dev/null; then
        ((skip_count++))
      else
        ((fail_count++))
      fi
      # Ensure cleanup
      git checkout main 2>/dev/null || true
      git branch -D "restore/wave3/$branch" 2>/dev/null || true
    fi

    echo ""
  done

  log_info "=== Batch Processing Complete ==="
  log_success "Success: $success_count"
  log_warn "Skipped (already merged): $skip_count"
  log_error "Failed: $fail_count"
}

# Function: Check duplicates
check_dupes() {
  log_info "Checking duplicate branches..."

  for branch in "${TIER_A_DUPES[@]}"; do
    if branch_exists "$branch"; then
      log_info "Branch: $branch"
      git log -1 --format='  Date: %ci%n  Subject: %s' "origin/$branch"
      git diff origin/main.."origin/$branch" --stat | head -5
      echo ""
    fi
  done

  log_info "Check complete. Review diffs and decide: merge ONE or delete ALL?"
}

# Function: Check conflict branches
check_conflicts() {
  log_info "Checking conflict resolution branches..."

  # Check if PR #70 is in main
  log_info "Searching for PR #70 in main history..."
  if git log origin/main --oneline | grep -i "#70\|pr-70\|pr 70" | head -5; then
    log_success "PR #70 found in main → conflict branches likely obsolete"
  else
    log_warn "PR #70 not found in main → may need these branches"
  fi

  echo ""
  for branch in "${TIER_A_CONFLICTS[@]}"; do
    if branch_exists "$branch"; then
      log_info "Branch: $branch"
      git log -1 --format='  Date: %ci%n  Subject: %s' "origin/$branch"
      echo ""
    fi
  done
}

# Function: Cleanup Tier X
cleanup_tier_x() {
  log_warn "=== Tier X Cleanup (DELETE) ==="
  log_warn "This will DELETE remote branches permanently!"
  read -p "Are you sure? Type 'YES' to continue: " confirm

  if [[ "$confirm" != "YES" ]]; then
    log_info "Cleanup cancelled"
    return 0
  fi

  local delete_count=0

  for branch in "${TIER_X_WIP[@]}"; do
    if branch_exists "$branch"; then
      log_info "Deleting: $branch"
      if git push origin --delete "$branch"; then
        log_success "Deleted: $branch"
        ((delete_count++))
      else
        log_error "Failed to delete: $branch"
      fi
    fi
  done

  log_success "Deleted $delete_count branches"
}

# Function: Status report
status_report() {
  log_info "=== Wave3 Restore Queue Status ==="

  echo ""
  echo "Tier A: Docs/Tooling (Safe)"
  echo "  Merge Logs: ${#TIER_A_MERGE_LOGS[@]} branches"
  echo "  Runbooks: ${#TIER_A_RUNBOOKS[@]} branches"
  echo "  Roadmaps: ${#TIER_A_ROADMAPS[@]} branches"
  echo "  Tooling: ${#TIER_A_TOOLING[@]} branches"
  echo "  (+ ${#TIER_A_DUPES[@]} dupes to check)"
  echo "  (+ ${#TIER_A_CONFLICTS[@]} conflict branches to check)"

  echo ""
  echo "Tier B: Tests/CI (Review + pytest)"
  echo "  Total: ${#TIER_B_ALL[@]} branches"

  echo ""
  echo "Tier C: Src/Risk (OPERATOR SIGNOFF)"
  echo "  Total: ${#TIER_C_ALL[@]} branches"

  echo ""
  echo "Tier X: Cleanup (DELETE)"
  echo "  WIP stashes: ${#TIER_X_WIP[@]} branches"

  echo ""
  log_info "Use: $0 [tier-a|tier-b|tier-c|check-dupes|cleanup|status]"
}

# Main
main() {
  local command=${1:-status}

  case "$command" in
    tier-a-merge-logs)
      batch_process "A" "${TIER_A_MERGE_LOGS[@]}"
      ;;
    tier-a-runbooks)
      batch_process "A" "${TIER_A_RUNBOOKS[@]}"
      ;;
    tier-a-roadmaps)
      batch_process "A" "${TIER_A_ROADMAPS[@]}"
      ;;
    tier-a-tooling)
      batch_process "A" "${TIER_A_TOOLING[@]}"
      ;;
    tier-a-all)
      log_info "Processing ALL Tier A branches (except dupes/conflicts)"
      batch_process "A" "${TIER_A_MERGE_LOGS[@]}"
      batch_process "A" "${TIER_A_RUNBOOKS[@]}"
      batch_process "A" "${TIER_A_ROADMAPS[@]}"
      batch_process "A" "${TIER_A_TOOLING[@]}"
      ;;
    tier-b)
      batch_process "B" "${TIER_B_ALL[@]}"
      ;;
    tier-c)
      log_error "Tier C requires manual processing with operator signoff"
      log_info "Use 'process_branch <branch> C' for individual branches"
      ;;
    check-dupes)
      check_dupes
      ;;
    check-conflicts)
      check_conflicts
      ;;
    cleanup)
      cleanup_tier_x
      ;;
    status)
      status_report
      ;;
    *)
      log_error "Unknown command: $command"
      status_report
      exit 1
      ;;
  esac
}

main "$@"
