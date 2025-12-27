#!/usr/bin/env bash
#
# ops_center.sh - Central entry point for Peak_Trade operator workflows
#
# Usage:
#   ops_center.sh help                 Show this help
#   ops_center.sh status [--json]      Show repo status (optionally as JSON)
#   ops_center.sh pr <NUM>             Review PR (no merge)
#   ops_center.sh merge-log            Show merge log quick reference
#   ops_center.sh doctor               Run ops_doctor health checks
#   ops_center.sh selftest             Run smoke tests
#
# Safe-by-default: No destructive actions, no merges without explicit flags.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="$REPO_ROOT/scripts/ops"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Help
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
show_help() {
  cat <<'HELP'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Peak_Trade Ops Center
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Central entry point for operator workflows.

USAGE:
  ops_center.sh <command> [args...]

COMMANDS:
  help                Show this help
  status [--json]     Show repo status (git + gh), optionally as JSON
  pr <NUM>            Review PR (safe, no merge)
  merge-log           Show merge log quick reference
  doctor              Run ops_doctor health checks
  selftest            Run smoke tests on ops_center itself

EXAMPLES:
  # Check repo status
  ops_center.sh status

  # Get machine-readable status
  ops_center.sh status --json

  # Review PR #263
  ops_center.sh pr 263

  # Get merge log quick links
  ops_center.sh merge-log

  # Run full health check
  ops_center.sh doctor

  # Run ops_center smoke tests
  ops_center.sh selftest

SAFE-BY-DEFAULT:
  - No destructive actions
  - No merges without explicit flags
  - Missing tools → friendly warnings (not errors)

DOCUMENTATION:
  docs/ops/OPS_OPERATOR_CENTER.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HELP
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cmd_status() {
  local json_mode=false

  # Parse flags
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --json)
        json_mode=true
        shift
        ;;
      *)
        echo "❌ Unknown flag: $1" >&2
        echo "Usage: ops_center.sh status [--json]" >&2
        exit 1
        ;;
    esac
  done

  cd "$REPO_ROOT"

  # Check if we're in a git repo
  if ! git rev-parse --git-dir &>/dev/null; then
    if $json_mode; then
      echo '{"error": "not a git repository"}' >&2
      exit 1
    else
      echo "❌ Error: Not a git repository" >&2
      exit 1
    fi
  fi

  # Collect git info
  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"

  local porcelain
  porcelain="$(git status --porcelain 2>/dev/null || echo "")"
  local working_tree_clean=true
  if [[ -n "$porcelain" ]]; then
    working_tree_clean=false
  fi

  local untracked_count=0
  local modified_count=0
  if [[ -n "$porcelain" ]]; then
    untracked_count=$(echo "$porcelain" | grep -c "^??" || true)
    modified_count=$(echo "$porcelain" | grep -c "^[MADRCU ]" || true)
  fi

  # Remote status
  git fetch --quiet 2>/dev/null || true

  local upstream
  upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || echo "")"

  local ahead=0
  local behind=0
  local remote="null"

  if [[ -n "$upstream" ]]; then
    remote="$upstream"
    ahead=$(git rev-list --count "${upstream}..HEAD" 2>/dev/null || echo 0)
    behind=$(git rev-list --count "HEAD..${upstream}" 2>/dev/null || echo 0)
  fi

  # Recent commits (JSON array)
  local recent_commits_json="[]"
  if $json_mode; then
    recent_commits_json=$(git log --format='{"sha":"%h","subject":"%s"}' -5 2>/dev/null | jq -s '.' 2>/dev/null || echo "[]")
  fi

  # GitHub CLI status
  local gh_available=false
  local gh_authenticated="null"
  if command -v gh &>/dev/null; then
    gh_available=true
    if gh auth status &>/dev/null 2>&1; then
      gh_authenticated="true"
    else
      gh_authenticated="false"
    fi
  fi

  # Output
  if $json_mode; then
    # JSON mode - single valid JSON object, no extra output
    cat <<JSON_OUTPUT
{
  "repo_root": "$REPO_ROOT",
  "branch": "$branch",
  "working_tree_clean": $working_tree_clean,
  "untracked_count": $untracked_count,
  "modified_count": $modified_count,
  "ahead": $ahead,
  "behind": $behind,
  "remote": $(if [[ "$remote" == "null" ]]; then echo "null"; else echo "\"$remote\""; fi),
  "recent_commits": $recent_commits_json,
  "gh_available": $gh_available,
  "gh_authenticated": $gh_authenticated
}
JSON_OUTPUT
  else
    # Human-readable mode
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Repository Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo ""
    echo "🔹 Branch:"
    echo "$branch"

    echo ""
    echo "🔹 Working Tree:"
    if $working_tree_clean; then
      echo "✅ Clean"
    else
      echo "⚠️  Uncommitted changes:"
      git status --short
    fi

    echo ""
    echo "🔹 Remote Status:"
    if [[ "$remote" != "null" ]]; then
      if [[ "$ahead" -eq 0 && "$behind" -eq 0 ]]; then
        echo "✅ Up-to-date with $remote"
      else
        echo "Ahead: $ahead | Behind: $behind (vs $remote)"
      fi
    else
      echo "⚠️  No upstream configured for branch '$branch'"
    fi

    echo ""
    echo "🔹 Recent Commits:"
    git log --oneline -5

    # GitHub CLI status
    echo ""
    echo "🔹 GitHub CLI:"
    if $gh_available; then
      if [[ "$gh_authenticated" == "true" ]]; then
        echo "✅ gh authenticated"
      else
        echo "⚠️  gh not authenticated (run: gh auth login)"
      fi
    else
      echo "⚠️  gh not installed (optional)"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PR Review
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cmd_pr() {
  local pr_num="${1:-}"

  if [[ -z "$pr_num" ]]; then
    echo "❌ Error: PR number required"
    echo "Usage: ops_center.sh pr <NUM>"
    exit 1
  fi

  local script="$SCRIPT_DIR/review_and_merge_pr.sh"

  if [[ ! -x "$script" ]]; then
    echo "⚠️  Script not found or not executable: $script"
    echo "ℹ️  Install PR toolkit: see docs/ops/PR_MANAGEMENT_TOOLKIT.md"
    exit 0
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🔍 PR Review (Safe Mode)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "PR #$pr_num"
  echo ""
  echo "ℹ️  Running in REVIEW-ONLY mode (no merge)"
  echo "ℹ️  To merge: use --merge flag directly in review_and_merge_pr.sh"
  echo ""

  "$script" --pr "$pr_num"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Merge Log Quick Reference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cmd_merge_log() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📋 Merge Log Quick Reference"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "🔹 Workflow:"
  echo "   docs/ops/MERGE_LOG_WORKFLOW.md"
  echo ""
  echo "🔹 Template:"
  echo "   templates/ops/merge_log_template.md"
  echo ""
  echo "🔹 Examples:"

  local logs_dir="$REPO_ROOT/docs/ops"
  if ls "$logs_dir"/PR_*_MERGE_LOG.md &>/dev/null; then
    echo ""
    ls -1 "$logs_dir"/PR_*_MERGE_LOG.md | while read -r f; do
      local bn
      bn="$(basename "$f")"
      echo "   - $bn"
    done
  else
    echo "   (no merge logs found yet)"
  fi

  echo ""
  echo "🔹 Quick Start:"
  echo "   scripts/ops/create_and_open_merge_log_pr.sh"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Doctor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cmd_doctor() {
  local script="$SCRIPT_DIR/ops_doctor.sh"

  if [[ ! -x "$script" ]]; then
    echo "⚠️  Script not found or not executable: $script"
    echo "ℹ️  Install ops_doctor: see docs/ops/OPS_DOCTOR_README.md"
    exit 0
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🏥 Running Ops Doctor"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  "$script" "$@"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Selftest
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cmd_selftest() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🧪 Ops Center Selftest"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  local failed=0
  local ops_center_script="$REPO_ROOT/scripts/ops/ops_center.sh"

  # Test 1: help command
  echo "🔹 Test: ops_center.sh help"
  if bash "$ops_center_script" help >/dev/null 2>&1; then
    echo "   ✅ PASS"
  else
    echo "   ❌ FAIL (exit code: $?)"
    ((failed++))
  fi

  # Test 2: status command
  echo "🔹 Test: ops_center.sh status"
  if bash "$ops_center_script" status >/dev/null 2>&1; then
    echo "   ✅ PASS"
  else
    echo "   ❌ FAIL (exit code: $?)"
    ((failed++))
  fi

  # Test 3: status --json command
  echo "🔹 Test: ops_center.sh status --json"
  local json_output
  json_output=$(bash "$ops_center_script" status --json 2>&1)
  local status_exit=$?

  if [[ $status_exit -eq 0 ]]; then
    # Verify it's valid JSON
    if echo "$json_output" | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1; then
      echo "   ✅ PASS (valid JSON)"
    else
      echo "   ❌ FAIL (invalid JSON)"
      ((failed++))
    fi
  else
    echo "   ❌ FAIL (exit code: $status_exit)"
    ((failed++))
  fi

  # Test 4: pytest smoke tests (if available)
  echo "🔹 Test: pytest smoke tests"
  local test_file="$REPO_ROOT/tests/ops/test_ops_center_smoke.py"

  if [[ ! -f "$test_file" ]]; then
    echo "   ⚠️  SKIP (test file not found)"
  else
    # Try uv run pytest first, fallback to pytest
    local pytest_cmd=""
    if command -v uv &>/dev/null; then
      pytest_cmd="uv run pytest"
    elif command -v pytest &>/dev/null; then
      pytest_cmd="pytest"
    else
      echo "   ⚠️  SKIP (pytest not available)"
      return 0
    fi

    if $pytest_cmd -q "$test_file" >/dev/null 2>&1; then
      echo "   ✅ PASS"
    else
      echo "   ❌ FAIL"
      ((failed++))
    fi
  fi

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ $failed -eq 0 ]]; then
    echo "✅ All tests passed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 0
  else
    echo "❌ $failed test(s) failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 1
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main() {
  local cmd="${1:-help}"
  shift || true

  case "$cmd" in
    help|--help|-h)
      show_help
      ;;
    status)
      cmd_status "$@"
      ;;
    pr)
      cmd_pr "$@"
      ;;
    merge-log)
      cmd_merge_log "$@"
      ;;
    doctor)
      cmd_doctor "$@"
      ;;
    selftest)
      cmd_selftest "$@"
      ;;
    *)
      echo "❌ Unknown command: $cmd"
      echo ""
      show_help
      exit 1
      ;;
  esac
}

main "$@"
