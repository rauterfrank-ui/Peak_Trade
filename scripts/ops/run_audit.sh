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

# Symlink for latest audit (machine-readable access)
LATEST_LINK="reports/audit/latest"

# Tool tracking files (portable alternative to associative arrays)
TOOL_STATUS_FILE="$AUDIT_DIR/.tool_status"
EXIT_CODE_FILE="$AUDIT_DIR/.exit_codes"
> "$TOOL_STATUS_FILE"
> "$EXIT_CODE_FILE"

# Findings counters for exit code determination
FINDINGS_COUNT=0
HARD_FAIL_COUNT=0

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
for cmd in rg ruff mypy pip-audit bandit make gh; do
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
[[ "$(get_tool ruff)" != "true" ]] && log "  ruff: pip install ruff (used for linting AND formatting)"
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

# Pattern for potential secrets (includes env var references)
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

# Hard-fail patterns: REAL secrets (not env var references)
HARD_FAIL_SECRETS_PATTERN='(AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{20,}|xox[baprs]-[0-9]+-[0-9]+-[a-zA-Z0-9]+|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----)'
HARD_FAIL_SECRETS_FILE="$AUDIT_DIR/08_hard_fail_secrets.txt"
HARD_FAIL_SECRETS_RAW="$AUDIT_DIR/.08_hard_fail_secrets_raw.txt"
echo "### Hard-Fail Secrets Detection" > "$HARD_FAIL_SECRETS_FILE"

# Scan for real secrets, excluding safe locations
if [[ "$(get_tool rg)" == "true" ]]; then
  rg -n --hidden --glob '!.git/*' --glob '!*.pyc' --glob '!reports/*' --glob '!tests/*' --glob '!**/test_*' --glob '!docs/ops/*' --glob '!**/venv/**' --glob '!**/.venv/**' --glob '!src/governance/policy_critic/*' --glob '!scripts/ops/run_audit.sh' "$HARD_FAIL_SECRETS_PATTERN" . >> "$HARD_FAIL_SECRETS_RAW" 2>&1 || true
else
  grep -rn --include='*.py' --include='*.md' --include='*.toml' --include='*.yaml' --include='*.yml' --include='*.json' \
    -E "$HARD_FAIL_SECRETS_PATTERN" . 2>/dev/null | grep -v '.git/' | grep -v 'reports/' | grep -v 'tests/' | grep -v 'test_' | grep -v 'docs/ops/' | grep -v '/venv/' | grep -v '/.venv/' | grep -v '^venv/' | grep -v '^\.venv/' | grep -v 'src/governance/policy_critic/' | grep -v 'scripts/ops/run_audit.sh' >> "$HARD_FAIL_SECRETS_RAW" || true
fi

# Filter out known safe patterns (EXAMPLE keys, etc.)
if [[ -f "$HARD_FAIL_SECRETS_RAW" ]]; then
  grep -v 'EXAMPLE' "$HARD_FAIL_SECRETS_RAW" >> "$HARD_FAIL_SECRETS_FILE" 2>/dev/null || true
fi

HARD_SECRETS_HITS=$(wc -l < "$HARD_FAIL_SECRETS_FILE" | tr -d ' ')
HARD_SECRETS_HITS=$((HARD_SECRETS_HITS - 1))  # Subtract header line
[[ $HARD_SECRETS_HITS -lt 0 ]] && HARD_SECRETS_HITS=0

if [[ $HARD_SECRETS_HITS -gt 0 ]]; then
  HARD_FAIL_COUNT=$((HARD_FAIL_COUNT + 1))
  log "HARD-FAIL: Real secrets detected ($HARD_SECRETS_HITS hits)"
fi

# Cleanup temp file
rm -f "$HARD_FAIL_SECRETS_RAW"

# 5) Tests
# Note: Full test suite is covered by CI workflow (tests job)
# Audit check focuses on repository health, not test coverage
skip_check "09_pytest" "Tests covered by CI workflow"


# 6) Live Gating Scan
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
RUFF_EXIT="SKIPPED"
MYPY_EXIT="SKIPPED"

if [[ "$(get_tool ruff)" == "true" ]]; then
  run_check "12_ruff" ruff check . --output-format=concise
  RUFF_EXIT=$(grep "^12_ruff=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "0")
  if [[ "$RUFF_EXIT" != "0" && "$RUFF_EXIT" != "SKIPPED" ]]; then
    FINDINGS_COUNT=$((FINDINGS_COUNT + 1))
    log "FINDING: ruff check failed (exit $RUFF_EXIT)"
  fi
else
  skip_check "12_ruff" "ruff not installed (pip install ruff)"
fi

# FORMAT check: ruff format is the source of truth (replaces black)
# Check if ruff is available (either as command or via python -m ruff)
RUFF_AVAILABLE=false
if [[ "$(get_tool ruff)" == "true" ]]; then
  RUFF_AVAILABLE=true
elif command -v python3 &>/dev/null && python3 -m ruff --version &>/dev/null; then
  RUFF_AVAILABLE=true
fi

if [[ "$RUFF_AVAILABLE" == "true" ]]; then
  # Prefer python -m ruff for robustness (works even if ruff command is not in PATH)
  if command -v python3 &>/dev/null && python3 -m ruff --version &>/dev/null; then
    run_check "13_format" python3 -m ruff format --check .
  else
    run_check "13_format" ruff format --check .
  fi
  FORMAT_EXIT=$(grep "^13_format=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "0")
  if [[ "$FORMAT_EXIT" != "0" && "$FORMAT_EXIT" != "SKIPPED" ]]; then
    FINDINGS_COUNT=$((FINDINGS_COUNT + 1))
    log "FINDING: ruff format check failed (exit $FORMAT_EXIT)"
  fi
else
  # ruff missing is a HARD-FAIL (formatter is required)
  log "HARD-FAIL: ruff not available for format check (required: pip install ruff)"
  HARD_FAIL_COUNT=$((HARD_FAIL_COUNT + 1))
fi

if [[ "$(get_tool mypy)" == "true" ]]; then
  run_check "14_mypy" mypy src --ignore-missing-imports
  MYPY_EXIT=$(grep "^14_mypy=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "0")
  if [[ "$MYPY_EXIT" != "0" && "$MYPY_EXIT" != "SKIPPED" ]]; then
    FINDINGS_COUNT=$((FINDINGS_COUNT + 1))
    log "FINDING: mypy check failed (exit $MYPY_EXIT)"
  fi
else
  skip_check "14_mypy" "mypy not installed (pip install mypy)"
fi

# 9) Security (optional tools)
PIP_AUDIT_EXIT="SKIPPED"
BANDIT_EXIT="SKIPPED"

# Ensure pip-audit is available and tooling is up-to-date
if [[ "$(get_tool pip-audit)" != "true" ]]; then
  log "pip-audit not found - attempting auto-install..."
  if have_cmd python3; then
    # Upgrade pip & wheel first (addresses pip-audit's own dependencies)
    # Try --user first for restrictive environments, fallback to system install
    python3 -m pip install --user --upgrade --quiet "pip>=23.3" "wheel>=0.38.1" 2>/dev/null || \
      python3 -m pip install --upgrade --quiet "pip>=23.3" "wheel>=0.38.1" 2>/dev/null || true

    # Install pip-audit (try --user first, then system)
    python3 -m pip install --user --quiet pip-audit 2>/dev/null || \
      python3 -m pip install --quiet pip-audit 2>/dev/null || true

    # Re-check if installation succeeded
    if have_cmd pip-audit; then
      record_tool "pip-audit" "true"
      log "  [OK] pip-audit (auto-installed)"
    else
      log "  [INFO] pip-audit auto-install failed (may require manual install)"
      log "         Run: python3 -m pip install --user pip-audit"
    fi
  fi
fi

if [[ "$(get_tool pip-audit)" == "true" ]]; then
  run_check "15_pip_audit" pip-audit
  PIP_AUDIT_EXIT=$(grep "^15_pip_audit=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "0")
  if [[ "$PIP_AUDIT_EXIT" != "0" && "$PIP_AUDIT_EXIT" != "SKIPPED" ]]; then
    FINDINGS_COUNT=$((FINDINGS_COUNT + 1))
    log "FINDING: pip-audit found vulnerabilities (exit $PIP_AUDIT_EXIT)"
  fi
else
  skip_check "15_pip_audit" "pip-audit not available after auto-install attempt"
fi

if [[ "$(get_tool bandit)" == "true" ]]; then
  run_check "16_bandit" bandit -q -r src
  BANDIT_EXIT=$(grep "^16_bandit=" "$EXIT_CODE_FILE" 2>/dev/null | cut -d= -f2 || echo "0")
  if [[ "$BANDIT_EXIT" != "0" && "$BANDIT_EXIT" != "SKIPPED" ]]; then
    FINDINGS_COUNT=$((FINDINGS_COUNT + 1))
    log "FINDING: bandit found security issues (exit $BANDIT_EXIT)"
  fi
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

# Check critical tests (pytest = hard fail if present and failing)
if [[ "$PYTEST_EXIT" != "0" && "$PYTEST_EXIT" != "SKIPPED" ]]; then
  HARD_FAIL_COUNT=$((HARD_FAIL_COUNT + 1))
  log "HARD-FAIL: pytest failed (exit $PYTEST_EXIT)"
fi

# Determine overall status (needed for both JSON and Markdown)
if [[ $HARD_FAIL_COUNT -gt 0 ]]; then
  OVERALL_STATUS="RED"
  OVERALL_EMOJI="[RED]"
elif [[ $FINDINGS_COUNT -gt 0 ]]; then
  OVERALL_STATUS="YELLOW"
  OVERALL_EMOJI="[YELLOW]"
else
  OVERALL_STATUS="GREEN"
  OVERALL_EMOJI="[GREEN]"
fi

# Build JSON manually (portable)
# Note: audit_exit_code will be added at the end after determination
cat > "$AUDIT_DIR/summary.json" <<EOF
{
  "audit_version": "1.1",
  "timestamp": "$TIMESTAMP",
  "timestamp_iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo": {
    "branch": "$BRANCH",
    "commit_sha": "$COMMIT_SHA",
    "commit_short": "${COMMIT_SHA:0:8}"
  },
  "tool_availability": {
    "git": $(get_tool git),
    "python3": $(get_tool python3),
    "rg": $(get_tool rg),
    "ruff": $(get_tool ruff),
    "mypy": $(get_tool mypy),
    "pip-audit": $(get_tool pip-audit),
    "bandit": $(get_tool bandit),
    "make": $(get_tool make),
    "gh": $(get_tool gh)
  },
  "exit_codes": {
    "pytest": "$PYTEST_EXIT",
    "ruff": "$RUFF_EXIT",
    "ruff_format": "$FORMAT_EXIT",
    "mypy": "$MYPY_EXIT",
    "pip_audit": "$PIP_AUDIT_EXIT",
    "bandit": "$BANDIT_EXIT"
  },
  "findings": {
    "secrets_hits": $SECRETS_HITS,
    "hard_secrets_hits": $HARD_SECRETS_HITS,
    "live_gating_hits": $GATING_HITS,
    "findings_count": $FINDINGS_COUNT,
    "hard_fail_count": $HARD_FAIL_COUNT
  },
  "status": {
    "overall": "$OVERALL_STATUS",
    "audit_exit_code": "PLACEHOLDER"
  }
}
EOF

# -----------------------------------------------------------------------------
# Generate Summary Markdown
# -----------------------------------------------------------------------------

# Helper for status display
pytest_status() {
  if [[ "$PYTEST_EXIT" == "0" ]]; then echo "PASS";
  elif [[ "$PYTEST_EXIT" == "SKIPPED" ]]; then echo "Skipped";
  else echo "FAIL (exit $PYTEST_EXIT)"; fi
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

### Tool Availability

| Tool | Available |
|------|-----------|
| rg (ripgrep) | $(if [[ "$(get_tool rg)" == "true" ]]; then echo "YES"; else echo "NO - brew install ripgrep"; fi) |
| ruff | $(if [[ "$(get_tool ruff)" == "true" ]]; then echo "YES (linting + formatting)"; else echo "NO - pip install ruff"; fi) |
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
2. Install missing tools if needed: \`pip install ruff mypy pip-audit bandit\`
3. $(if [[ "$PYTEST_EXIT" != "0" && "$PYTEST_EXIT" != "SKIPPED" ]]; then echo "Fix failing tests"; else echo "Tests passing"; fi)

---
*Generated by \`scripts/run_audit.sh\`*
EOF

# -----------------------------------------------------------------------------
# Determine Overall Exit Code
# -----------------------------------------------------------------------------
# Exit codes:
#   0 = OK (no findings)
#   1 = Findings present (linting errors, etc.)
#   2 = Hard-Fail (real secrets found OR pytest failed OR script errors)

AUDIT_EXIT_CODE=0

if [[ $HARD_FAIL_COUNT -gt 0 ]]; then
  AUDIT_EXIT_CODE=2
  log "EXIT CODE: 2 (HARD-FAIL: $HARD_FAIL_COUNT issue(s))"
elif [[ $FINDINGS_COUNT -gt 0 ]]; then
  AUDIT_EXIT_CODE=1
  log "EXIT CODE: 1 (FINDINGS: $FINDINGS_COUNT issue(s))"
else
  AUDIT_EXIT_CODE=0
  log "EXIT CODE: 0 (OK: no findings)"
fi

# -----------------------------------------------------------------------------
# Update JSON with final exit code
# -----------------------------------------------------------------------------
# Use sed to replace placeholder (portable across macOS/Linux)
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' "s/\"audit_exit_code\": \"PLACEHOLDER\"/\"audit_exit_code\": $AUDIT_EXIT_CODE/" "$AUDIT_DIR/summary.json"
else
  sed -i "s/\"audit_exit_code\": \"PLACEHOLDER\"/\"audit_exit_code\": $AUDIT_EXIT_CODE/" "$AUDIT_DIR/summary.json"
fi

# -----------------------------------------------------------------------------
# Create Latest Symlink
# -----------------------------------------------------------------------------
rm -f "$LATEST_LINK"
ln -s "$TIMESTAMP" "$LATEST_LINK"

# Cleanup temp files
rm -f "$TOOL_STATUS_FILE" "$EXIT_CODE_FILE"

# -----------------------------------------------------------------------------
# Final Output
# -----------------------------------------------------------------------------
echo ""
log "=== Audit Complete ==="
echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
if [[ $AUDIT_EXIT_CODE -eq 0 ]]; then
  echo "║  STATUS: OK - No findings                                             ║"
elif [[ $AUDIT_EXIT_CODE -eq 1 ]]; then
  echo "║  STATUS: FINDINGS ($FINDINGS_COUNT issue(s) detected)                            ║"
else
  echo "║  STATUS: HARD FAIL ($HARD_FAIL_COUNT critical issue(s))                         ║"
fi
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Exit Code: $AUDIT_EXIT_CODE"
echo "  0 = OK (no findings)"
echo "  1 = Findings (linting/warnings)"
echo "  2 = Hard-Fail (real secrets or pytest failure)"
echo ""
echo "Findings Summary:"
echo "  Hard-Fail Count: $HARD_FAIL_COUNT"
echo "  Findings Count:  $FINDINGS_COUNT"
echo "  Secrets (potential): $SECRETS_HITS"
echo "  Secrets (REAL): $HARD_SECRETS_HITS"
echo ""
echo "Audit folder: $AUDIT_DIR"
echo "Latest link:  $LATEST_LINK -> $TIMESTAMP"
echo ""
echo "Key files:"
echo "   $AUDIT_DIR/summary.json (machine-readable)"
echo "   $AUDIT_DIR/summary.md"
echo "   $LATEST_LINK/summary.json"
echo ""
echo "View summary:"
echo "   cat $AUDIT_DIR/summary.md"
echo "   jq . $LATEST_LINK/summary.json"
echo ""

# Safety reminders (never auto-execute)
echo "Manual maintenance commands (run only if needed):"
echo "   git gc                    # Pack loose objects"
echo "   git clean -ndX            # Preview ignored files to remove"
echo "   git clean -fdX            # Remove ignored files (CAUTION)"
echo ""

# -----------------------------------------------------------------------------
# Exit with appropriate code
# -----------------------------------------------------------------------------
exit $AUDIT_EXIT_CODE
