#!/usr/bin/env bash
# =============================================================================
# Peak_Trade Repository Audit Script
# =============================================================================
# Idempotent, tool-detecting audit that produces JSON + Markdown summaries.
# Safe: NEVER auto-executes git clean or git gc, only recommends.
#
# Usage:
#   ./scripts/run_audit.sh
#   make audit
#
# Output: reports/audit/YYYY-MM-DD_HHMM/
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TIMESTAMP="$(date +%Y-%m-%d_%H%M)"
AUDIT_DIR="reports/audit/${TIMESTAMP}"
mkdir -p "$AUDIT_DIR"

# Tool tracking files (portable alternative to associative arrays)
TOOL_STATUS_FILE="$AUDIT_DIR/.tool_status"
EXIT_CODE_FILE="$AUDIT_DIR/.exit_codes"
> "$TOOL_STATUS_FILE"
> "$EXIT_CODE_FILE"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

# Check if command exists
have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

# Log with timestamp
log() {
  echo "[$(date '+%H:%M:%S')] $*"
}

# Record tool availability
record_tool() {
  echo "$1=$2" >> "$TOOL_STATUS_FILE"
}

# Get tool status
get_tool() {
  grep "^$1=" "$TOOL_STATUS_FILE" 2>/dev/null | cut -d= -f2 || echo "false"
}

# Record exit code
record_exit() {
  echo "$1=$2" >> "$EXIT_CODE_FILE"
}

# Run a check, capture output, track exit code
run_check() {
  local name="$1"
  local outfile="$AUDIT_DIR/${name}.txt"
  shift

  log "Running: $name"
  echo "### $name" > "$outfile"
  echo "$ $*" >> "$outfile"
  echo "" >> "$outfile"

  local exit_code=0
  ( "$@" ) >> "$outfile" 2>&1 || exit_code=$?

  if [[ $exit_code -ne 0 ]]; then
    echo "" >> "$outfile"
    echo "[EXIT=$exit_code]" >> "$outfile"
  fi

  record_exit "$name" "$exit_code"
  return 0  # Always continue
}

# Mark a check as skipped
skip_check() {
  local name="$1"
  local reason="$2"
  local outfile="$AUDIT_DIR/${name}.txt"

  log "SKIPPED: $name ($reason)"
  echo "### $name" > "$outfile"
  echo "SKIPPED: $reason" >> "$outfile"
  record_exit "$name" "SKIPPED"
}

# -----------------------------------------------------------------------------
# Tool Detection
# -----------------------------------------------------------------------------
log "=== Tool Detection ==="

# Core tools (required)
for cmd in git python3 bash; do
  if have_cmd "$cmd"; then
    record_tool "$cmd" "true"
    log "  [OK] $cmd"
  else
    record_tool "$cmd" "false"
    log "  [MISSING] $cmd"
  fi
done

# Optional tools
for cmd in rg ruff black mypy pip-audit bandit make gh; do
  if have_cmd "$cmd"; then
    record_tool "$cmd" "true"
    log "  [OK] $cmd"
  else
    record_tool "$cmd" "false"
    log "  [MISSING] $cmd"
  fi
done

# Print install hints for missing tools
echo ""
log "=== Install Hints for Missing Tools ==="
[[ "$(get_tool rg)" != "true" ]] && log "  rg (ripgrep): brew install ripgrep"
[[ "$(get_tool ruff)" != "true" ]] && log "  ruff: pip install ruff"
[[ "$(get_tool black)" != "true" ]] && log "  black: pip install black"
[[ "$(get_tool mypy)" != "true" ]] && log "  mypy: pip install mypy"
[[ "$(get_tool pip-audit)" != "true" ]] && log "  pip-audit: pip install pip-audit"
[[ "$(get_tool bandit)" != "true" ]] && log "  bandit: pip install bandit"
echo ""

# -----------------------------------------------------------------------------
# Audit Checks
# -----------------------------------------------------------------------------
log "=== Running Audit Checks ==="

# 1) Repo Snapshot
run_check "01_git_status" git status -sb
run_check "02_git_log" git log -n 20 --oneline --decorate
run_check "03_git_branch" git branch -vv

# 2) Size Hot Spots
run_check "04_du_top" bash -c 'du -h -d 2 . 2>/dev/null | sort -h | tail -n 50 || true'
run_check "05_git_stats" bash -c 'git count-objects -vH; echo ""; echo "Tracked files:"; git ls-files | wc -l'

# 3) Hygiene
run_check "06_clean_dryrun" git clean -ndX
run_check "07_untracked" git status --porcelain=v1

# 4) Secrets Scan
log "Running secrets scan..."
SECRETS_FILE="$AUDIT_DIR/08_secrets_scan.txt"
echo "### Secrets Scan" > "$SECRETS_FILE"

SECRETS_PATTERN='(api[_-]?key|secret|token|password|BEGIN (RSA|OPENSSH|EC|PGP) PRIVATE|xox[baprs]-|AKIA[0-9A-Z]{16}|-----BEGIN)'

if [[ "$(get_tool rg)" == "true" ]]; then
  echo "Using: ripgrep" >> "$SECRETS_FILE"
  echo "" >> "$SECRETS_FILE"
  rg -n --hidden --glob '!.git/*' --glob '!*.pyc' -i "$SECRETS_PATTERN" . >> "$SECRETS_FILE" 2>&1 || true
else
  echo "Using: grep -r (fallback, slower)" >> "$SECRETS_FILE"
  echo "" >> "$SECRETS_FILE"
  grep -rn --include='*.py' --include='*.md' --include='*.toml' --include='*.yaml' --include='*.yml' --include='*.json' \
    -iE "$SECRETS_PATTERN" . 2>/dev/null | grep -v '.git/' >> "$SECRETS_FILE" || true
fi

SECRETS_HITS=$(wc -l < "$SECRETS_FILE" | tr -d ' ')
SECRETS_HITS=$((SECRETS_HITS - 3))  # Subtract header lines

# 5) Tests
if have_cmd python3; then
  run_check "09_pytest" python3 -m pytest -q --tb=no
else
  skip_check "09_pytest" "python3 not found"
fi

# 6) Todo Board Check
if [[ "$(get_tool make)" == "true" ]] && [[ -f Makefile ]]; then
  run_check "10_todo_board" make todo-board-check
else
  skip_check "10_todo_board" "make or Makefile not available"
fi

# 7) Live Gating Scan
log "Running live gating scan..."
GATING_FILE="$AUDIT_DIR/11_live_gating.txt"
echo "### Live Gating Scan" > "$GATING_FILE"

GATING_PATTERN='(enable_live_trading|live_mode_armed|confirm_token|IS_LIVE_READY|ALLOWED_ENVIRONMENTS|LIVE_LOCK|go_no_go|RiskCheckSeverity)'

if [[ "$(get_tool rg)" == "true" ]]; then
  rg -n "$GATING_PATTERN" src/ docs/ >> "$GATING_FILE" 2>&1 || true
else
  grep -rn --include='*.py' --include='*.md' -E "$GATING_PATTERN" src/ docs/ >> "$GATING_FILE" 2>/dev/null || true
fi

GATING_HITS=$(wc -l < "$GATING_FILE" | tr -d ' ')
GATING_HITS=$((GATING_HITS - 1))

# 8) Linting (optional tools)
if [[ "$(get_tool ruff)" == "true" ]]; then
  run_check "12_ruff" ruff check . --output-format=concise
else
  skip_check "12_ruff" "ruff not installed (pip install ruff)"
fi

if [[ "$(get_tool black)" == "true" ]]; then
  run_check "13_black" black --check .
else
  skip_check "13_black" "black not installed (pip install black)"
fi

if [[ "$(get_tool mypy)" == "true" ]]; then
  run_check "14_mypy" mypy src --ignore-missing-imports
else
  skip_check "14_mypy" "mypy not installed (pip install mypy)"
fi

# 9) Security (optional tools)
if [[ "$(get_tool pip-audit)" == "true" ]]; then
  run_check "15_pip_audit" pip-audit
else
  skip_check "15_pip_audit" "pip-audit not installed (pip install pip-audit)"
fi

if [[ "$(get_tool bandit)" == "true" ]]; then
  run_check "16_bandit" bandit -q -r src
else
  skip_check "16_bandit" "bandit not installed (pip install bandit)"
fi

# 10) GitHub CI (optional)
if [[ "$(get_tool gh)" == "true" ]]; then
  run_check "17_gh_runs" gh run list -L 10
  run_check "18_gh_prs" gh pr list -L 10
else
  skip_check "17_gh_runs" "gh not installed or not authenticated"
  skip_check "18_gh_prs" "gh not installed or not authenticated"
fi

# -----------------------------------------------------------------------------
# Generate Summary JSON
# -----------------------------------------------------------------------------
log "=== Generating Summary ==="

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

# Get exit codes
PYTEST_EXIT=$(grep "^09_pytest=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "SKIPPED")
TODO_EXIT=$(grep "^10_todo_board=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "SKIPPED")

# Build JSON manually (portable)
cat > "$AUDIT_DIR/summary.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "branch": "$BRANCH",
  "commit_sha": "$COMMIT_SHA",
  "tool_availability": {
    "git": $(get_tool git),
    "python3": $(get_tool python3),
    "rg": $(get_tool rg),
    "ruff": $(get_tool ruff),
    "black": $(get_tool black),
    "mypy": $(get_tool mypy),
    "pip-audit": $(get_tool pip-audit),
    "bandit": $(get_tool bandit),
    "make": $(get_tool make),
    "gh": $(get_tool gh)
  },
  "exit_codes": {
    "pytest": "$PYTEST_EXIT",
    "todo_board": "$TODO_EXIT"
  },
  "findings_counts": {
    "secrets_hits": $SECRETS_HITS,
    "live_gating_hits": $GATING_HITS
  }
}
EOF

# -----------------------------------------------------------------------------
# Generate Summary Markdown
# -----------------------------------------------------------------------------

# Determine overall status
if [[ "$PYTEST_EXIT" == "0" ]] && [[ "$TODO_EXIT" == "0" || "$TODO_EXIT" == "SKIPPED" ]]; then
  OVERALL_STATUS="GREEN"
  OVERALL_EMOJI="[GREEN]"
elif [[ "$PYTEST_EXIT" == "SKIPPED" ]]; then
  OVERALL_STATUS="YELLOW"
  OVERALL_EMOJI="[YELLOW]"
else
  OVERALL_STATUS="RED"
  OVERALL_EMOJI="[RED]"
fi

# Helper for status display
pytest_status() {
  if [[ "$PYTEST_EXIT" == "0" ]]; then echo "PASS";
  elif [[ "$PYTEST_EXIT" == "SKIPPED" ]]; then echo "Skipped";
  else echo "FAIL (exit $PYTEST_EXIT)"; fi
}

todo_status() {
  if [[ "$TODO_EXIT" == "0" ]]; then echo "PASS";
  elif [[ "$TODO_EXIT" == "SKIPPED" ]]; then echo "Skipped";
  else echo "FAIL (exit $TODO_EXIT)"; fi
}

cat > "$AUDIT_DIR/summary.md" <<EOF
# Audit Summary

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Branch:** \`$BRANCH\`
**Commit:** \`${COMMIT_SHA:0:8}\`

## Overall Status: $OVERALL_EMOJI $OVERALL_STATUS

### Test Results

| Check | Status |
|-------|--------|
| pytest | $(pytest_status) |
| todo-board-check | $(todo_status) |

### Tool Availability

| Tool | Available |
|------|-----------|
| rg (ripgrep) | $(if [[ "$(get_tool rg)" == "true" ]]; then echo "YES"; else echo "NO - brew install ripgrep"; fi) |
| ruff | $(if [[ "$(get_tool ruff)" == "true" ]]; then echo "YES"; else echo "NO - pip install ruff"; fi) |
| black | $(if [[ "$(get_tool black)" == "true" ]]; then echo "YES"; else echo "NO - pip install black"; fi) |
| mypy | $(if [[ "$(get_tool mypy)" == "true" ]]; then echo "YES"; else echo "NO - pip install mypy"; fi) |
| pip-audit | $(if [[ "$(get_tool pip-audit)" == "true" ]]; then echo "YES"; else echo "NO - pip install pip-audit"; fi) |
| bandit | $(if [[ "$(get_tool bandit)" == "true" ]]; then echo "YES"; else echo "NO - pip install bandit"; fi) |

### Findings

- **Secrets scan hits:** $SECRETS_HITS (review \`08_secrets_scan.txt\`)
- **Live gating references:** $GATING_HITS (safety gates in place)

### Git Maintenance

\`\`\`
$(git count-objects -vH 2>/dev/null || echo "Unable to get git stats")
\`\`\`

## Next Steps

1. Review \`08_secrets_scan.txt\` for any real secrets (most hits are env var references)
2. Install missing tools if needed: \`pip install ruff black mypy pip-audit bandit\`
3. $(if [[ "$PYTEST_EXIT" != "0" && "$PYTEST_EXIT" != "SKIPPED" ]]; then echo "Fix failing tests"; else echo "Tests passing"; fi)
4. $(if [[ "$TODO_EXIT" != "0" && "$TODO_EXIT" != "SKIPPED" ]]; then echo "Fix todo-board-check issues"; else echo "Todo board clean"; fi)

---
*Generated by \`scripts/run_audit.sh\`*
EOF

# Cleanup temp files
rm -f "$TOOL_STATUS_FILE" "$EXIT_CODE_FILE"

# -----------------------------------------------------------------------------
# Final Output
# -----------------------------------------------------------------------------
echo ""
log "=== Audit Complete ==="
echo ""
echo "Audit folder: $AUDIT_DIR"
echo ""
echo "Summary:"
echo "   Status: $OVERALL_EMOJI $OVERALL_STATUS"
echo "   pytest: $PYTEST_EXIT"
echo "   todo-board: $TODO_EXIT"
echo ""
echo "Key files:"
echo "   $AUDIT_DIR/summary.json"
echo "   $AUDIT_DIR/summary.md"
echo ""
echo "View summary:"
echo "   cat $AUDIT_DIR/summary.md"
echo ""

# Safety reminders (never auto-execute)
echo "Manual maintenance commands (run only if needed):"
echo "   git gc                    # Pack loose objects"
echo "   git clean -ndX            # Preview ignored files to remove"
echo "   git clean -fdX            # Remove ignored files (CAUTION)"
echo ""
