#!/usr/bin/env bash
#
# ops_center.sh - Central entry point for Peak_Trade operator workflows
#
# Usage:
#   ops_center.sh help                 Show this help
#   ops_center.sh status               Show repo status
#   ops_center.sh pr <NUM>             Review PR (no merge)
#   ops_center.sh merge-log            Show merge log quick reference
#   ops_center.sh doctor               Run ops_doctor health checks
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
  status              Show repo status (git + gh)
  pr <NUM>            Review PR (safe, no merge)
  merge-log           Show merge log quick reference
  doctor [--quick]    Run ops_doctor health checks (+ merge-log validation)

EXAMPLES:
  # Check repo status
  ops_center.sh status

  # Review PR #263
  ops_center.sh pr 263

  # Get merge log quick links
  ops_center.sh merge-log

  # Run full health check (includes merge-log tests)
  ops_center.sh doctor

  # Quick health check (skip merge-log tests)
  ops_center.sh doctor --quick

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
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📊 Repository Status"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  cd "$REPO_ROOT"

  # Git basics
  echo ""
  echo "🔹 Branch:"
  git rev-parse --abbrev-ref HEAD

  echo ""
  echo "🔹 Working Tree:"
  if [[ -z "$(git status --porcelain)" ]]; then
    echo "✅ Clean"
  else
    echo "⚠️  Uncommitted changes:"
    git status --short
  fi

  echo ""
  echo "🔹 Remote Status:"
  git fetch --quiet 2>/dev/null || echo "⚠️  Could not fetch (offline?)"

  local branch
  branch="$(git rev-parse --abbrev-ref HEAD)"
  local upstream
  upstream="$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || echo "")"

  if [[ -n "$upstream" ]]; then
    local ahead behind
    ahead=$(git rev-list --count "${upstream}..HEAD" 2>/dev/null || echo "0")
    behind=$(git rev-list --count "HEAD..${upstream}" 2>/dev/null || echo "0")

    if [[ "$ahead" -eq 0 && "$behind" -eq 0 ]]; then
      echo "✅ Up-to-date with $upstream"
    else
      echo "Ahead: $ahead | Behind: $behind (vs $upstream)"
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
  if command -v gh &>/dev/null; then
    if gh auth status &>/dev/null; then
      echo "✅ gh authenticated"
    else
      echo "⚠️  gh not authenticated (run: gh auth login)"
    fi
  else
    echo "⚠️  gh not installed (optional)"
  fi

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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
  # No args → show quick reference
  if [[ "$#" -eq 0 ]]; then
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
    echo "🔹 Batch Generator:"
    echo "   ops_center.sh merge-log <PR> [<PR> ...]"
    echo ""
    echo "   Examples:"
    echo "     ops_center.sh merge-log 281"
    echo "     ops_center.sh merge-log 278 279 280"
    echo "     ops_center.sh merge-log --dry-run 281"
    echo "     ops_center.sh merge-log --keep-going 278 279 999"
    echo ""
    echo "🔹 Quick Start:"
    echo "   scripts/ops/create_and_open_merge_log_pr.sh"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 0
  fi

  # With args → delegate to batch generator
  local script="$SCRIPT_DIR/generate_merge_logs_batch.sh"

  if [[ ! -x "$script" ]]; then
    echo "❌ Error: Script not found or not executable: $script"
    echo "ℹ️  Expected location: scripts/ops/generate_merge_logs_batch.sh"
    exit 1
  fi

  # Check for gh CLI
  if ! command -v gh &>/dev/null; then
    echo "❌ Error: gh CLI not found"
    echo "ℹ️  Install: brew install gh"
    echo "ℹ️  Docs: https://cli.github.com/"
    exit 1
  fi

  # Check gh auth
  if ! gh auth status &>/dev/null; then
    echo "❌ Error: gh not authenticated"
    echo "ℹ️  Run: gh auth login"
    exit 1
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📋 Generating Merge Logs"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "PRs: $*"
  echo ""

  "$script" "$@"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Doctor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cmd_doctor() {
  local script="$SCRIPT_DIR/ops_doctor.sh"
  local quick_mode=0
  local doctor_args=()

  # Parse --quick flag (ours only, not passed to Python doctor)
  for arg in "$@"; do
    if [[ "$arg" == "--quick" ]]; then
      quick_mode=1
    else
      doctor_args+=("$arg")
    fi
  done

  if [[ ! -x "$script" ]]; then
    echo "⚠️  Script not found or not executable: $script"
    echo "ℹ️  Install ops_doctor: see docs/ops/OPS_DOCTOR_README.md"
    exit 0
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🏥 Running Ops Doctor"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Run main doctor checks (without --quick flag)
  local doctor_exit=0
  if [[ "${#doctor_args[@]}" -gt 0 ]]; then
    "$script" "${doctor_args[@]}" || doctor_exit=$?
  else
    "$script" || doctor_exit=$?
  fi

  # Merge-Log Health Checks
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📋 Merge-Log Health"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  local validator="$SCRIPT_DIR/validate_merge_logs_setup.sh"
  local tests="$SCRIPT_DIR/tests/test_generate_merge_logs_batch.sh"
  local merge_log_exit=0

  # 1) Validator (always run, fast)
  if [[ -x "$validator" ]]; then
    echo "🔍 Validator: validate_merge_logs_setup.sh"
    if "$validator" >/dev/null 2>&1; then
      echo "   ✅ PASS - Setup validated"
    else
      echo "   ❌ FAIL - Setup validation failed"
      echo "   Details: Run 'scripts/ops/validate_merge_logs_setup.sh' for details"
      merge_log_exit=1
    fi
  else
    echo "⚠️  Validator not found: $validator"
    merge_log_exit=1
  fi

  # 2) Tests (skip in --quick mode or if not present)
  if [[ "$quick_mode" -eq 1 ]]; then
    echo "⏭️  Tests: SKIP (--quick mode)"
  elif [[ -x "$tests" ]]; then
    echo "🧪 Tests: test_generate_merge_logs_batch.sh"
    if "$tests" >/dev/null 2>&1; then
      echo "   ✅ PASS - All offline tests passed"
    else
      echo "   ⚠️  FAIL - Some tests failed"
      echo "   Details: Run 'scripts/ops/tests/test_generate_merge_logs_batch.sh'"
      merge_log_exit=1
    fi
  else
    echo "ℹ️  Tests: SKIP (not present)"
  fi

  echo ""

  # Formatter Policy Health Check
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🛡️  Formatter Policy Health"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  local formatter_check="$SCRIPT_DIR/check_no_black_enforcement.sh"
bash scripts/ops/check_formatter_policy_ci_enforced.sh
  local formatter_exit=0

  # Always run (fast, offline check)
  if [[ -x "$formatter_check" ]]; then
    echo "🔍 Check: no black enforcement in workflows/scripts"
    if "$formatter_check" >/dev/null 2>&1; then
      echo "   ✅ PASS - Formatter policy enforced (ruff format)"
    else
      echo "   ❌ FAIL - black enforcement detected"
      echo "   Details: Run 'scripts/ops/check_no_black_enforcement.sh'"
      formatter_exit=1
    fi
  else
    echo "⚠️  Formatter policy check not found: $formatter_check"
    formatter_exit=1
  fi

  echo ""

  # Exit with non-zero if any checks failed
  local final_exit=$((doctor_exit | merge_log_exit | formatter_exit))
  if [[ $final_exit -ne 0 ]]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Health checks failed (exit $final_exit)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  fi

  return $final_exit
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
    *)
      echo "❌ Unknown command: $cmd"
      echo ""
      show_help
      exit 1
      ;;
  esac
}

main "$@"
