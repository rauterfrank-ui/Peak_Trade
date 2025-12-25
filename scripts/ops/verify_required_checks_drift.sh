#!/usr/bin/env bash
#
# verify_required_checks_drift.sh
#
# Purpose:
#   Verify that Branch Protection Required Checks (live on GitHub) match
#   the documented list in docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md
#
# Usage:
#   verify_required_checks_drift.sh [options]
#
# Options:
#   --owner OWNER       GitHub owner/org (default: rauterfrank-ui)
#   --repo REPO         Repository name (default: Peak_Trade)
#   --branch BRANCH     Branch name (default: main)
#   --doc PATH          Path to doc file (default: docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)
#   --warn-only         Exit 2 instead of 1 on drift (for soft warnings)
#   --help              Show this help
#
# Exit Codes:
#   0 - Match (no drift)
#   1 - Drift detected (or hard error)
#   2 - Drift detected in warn-only mode
#
# Requirements:
#   - gh CLI (authenticated)
#   - jq
#
# Example:
#   verify_required_checks_drift.sh
#   verify_required_checks_drift.sh --warn-only
#   verify_required_checks_drift.sh --owner myorg --repo myrepo

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Defaults
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OWNER="${OWNER:-rauterfrank-ui}"
REPO="${REPO:-Peak_Trade}"
BRANCH="${BRANCH:-main}"
DOC_PATH="docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md"
WARN_ONLY=0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Help
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
show_help() {
  cat <<'HELP'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧭 Required Checks Drift Guard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies that Branch Protection Required Checks (live)
match the documented list.

USAGE:
  verify_required_checks_drift.sh [options]

OPTIONS:
  --owner OWNER       GitHub owner/org (default: rauterfrank-ui)
  --repo REPO         Repository name (default: Peak_Trade)
  --branch BRANCH     Branch name (default: main)
  --doc PATH          Path to doc file (default: docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md)
  --warn-only         Exit 2 instead of 1 on drift
  --help              Show this help

EXIT CODES:
  0 - Match (no drift)
  1 - Drift detected (or hard error)
  2 - Drift detected in warn-only mode

EXAMPLES:
  # Quick check
  verify_required_checks_drift.sh

  # Warn-only mode (for ops_doctor)
  verify_required_checks_drift.sh --warn-only

  # Custom repo
  verify_required_checks_drift.sh --owner myorg --repo myrepo

REQUIREMENTS:
  - gh CLI (authenticated): brew install gh
  - jq: brew install jq

DOCUMENTATION:
  docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HELP
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Parse Args
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)
      OWNER="$2"
      shift 2
      ;;
    --repo)
      REPO="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --doc)
      DOC_PATH="$2"
      shift 2
      ;;
    --warn-only)
      WARN_ONLY=1
      shift
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      echo "❌ Unknown option: $1"
      echo ""
      show_help
      exit 1
      ;;
  esac
done

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Preflight
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
preflight_check() {
  local errors=0

  # Check gh CLI
  if ! command -v gh &>/dev/null; then
    echo "❌ gh CLI not found"
    echo "   Install: brew install gh"
    errors=$((errors + 1))
  elif ! gh auth status &>/dev/null 2>&1; then
    echo "❌ gh not authenticated"
    echo "   Run: gh auth login"
    errors=$((errors + 1))
  fi

  # Check jq
  if ! command -v jq &>/dev/null; then
    echo "❌ jq not found"
    echo "   Install: brew install jq"
    errors=$((errors + 1))
  fi

  # Check doc file
  if [[ ! -f "$REPO_ROOT/$DOC_PATH" ]]; then
    echo "❌ Doc file not found: $REPO_ROOT/$DOC_PATH"
    errors=$((errors + 1))
  fi

  if [[ $errors -gt 0 ]]; then
    echo ""
    echo "❌ Preflight failed ($errors error(s))"
    exit 1
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Extract Required Checks from Doc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Extracts the numbered list under "## Current Required Checks (main)"
# Expected format:
#   1. **Check Name**
#   2. **Another Check** (optional comment)
#
# Output: sorted unique list of check names (one per line)
extract_doc_checks() {
  local doc_file="$REPO_ROOT/$DOC_PATH"

  # Extract section between "## Current Required Checks" and next "##" or "---"
  # Then parse lines like: "1. **Check Name**"
  # Use sed for better portability
  sed -n '
    /^## Current Required Checks/,/^---/p
  ' "$doc_file" \
    | grep -E '^[0-9]+\. \*\*' \
    | sed -E 's/^[0-9]+\. \*\*//; s/\*\*.*$//' \
    | sort -u
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fetch Live Required Checks from GitHub
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Output: sorted unique list of check names (one per line)
fetch_live_checks() {
  gh api -H "Accept: application/vnd.github+json" \
    "/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks" \
    2>/dev/null \
    | jq -r '.contexts[]? // empty' \
    | sort -u
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Compare Sets
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
compare_checks() {
  local doc_checks="$1"
  local live_checks="$2"

  # Save to temp files for comm
  local tmp_doc
  local tmp_live
  tmp_doc="$(mktemp)"
  tmp_live="$(mktemp)"

  echo "$doc_checks" > "$tmp_doc"
  echo "$live_checks" > "$tmp_live"

  # comm requires sorted input (already sorted)
  # comm -23: in doc but not in live (missing from live)
  # comm -13: in live but not in doc (extra in live)
  local missing
  local extra
  missing="$(comm -23 "$tmp_doc" "$tmp_live")"
  extra="$(comm -13 "$tmp_doc" "$tmp_live")"

  rm -f "$tmp_doc" "$tmp_live"

  # Check for drift
  if [[ -z "$missing" && -z "$extra" ]]; then
    # Perfect match
    return 0
  else
    # Drift detected
    echo "🔍 Required Checks Drift Detected"
    echo ""

    if [[ -n "$missing" ]]; then
      echo "❌ Missing from Live (in doc, not on GitHub):"
      while IFS= read -r check; do
        [[ -n "$check" ]] && echo "   - $check"
      done <<< "$missing"
      echo ""
    fi

    if [[ -n "$extra" ]]; then
      echo "⚠️  Extra in Live (on GitHub, not in doc):"
      while IFS= read -r check; do
        [[ -n "$check" ]] && echo "   - $check"
      done <<< "$extra"
      echo ""
    fi

    echo "📖 Doc: $DOC_PATH"
    echo "🔗 Live: ${OWNER}/${REPO} (branch: ${BRANCH})"
    echo ""
    echo "💡 Action Required:"
    echo "   Update doc to match live state, or adjust branch protection."

    return 1
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main() {
  # Preflight
  preflight_check

  # Extract
  local doc_checks
  doc_checks="$(extract_doc_checks)"

  if [[ -z "$doc_checks" ]]; then
    echo "❌ Error: No checks found in doc"
    echo "   Doc: $DOC_PATH"
    echo "   Expected section: ## Current Required Checks (main)"
    exit 1
  fi

  # Fetch
  local live_checks
  if ! live_checks="$(fetch_live_checks)"; then
    echo "❌ Error: Failed to fetch live checks from GitHub"
    echo "   Repo: ${OWNER}/${REPO}"
    echo "   Branch: ${BRANCH}"
    echo "   Ensure branch protection is configured."
    exit 1
  fi

  if [[ -z "$live_checks" ]]; then
    echo "❌ Error: No required checks configured on GitHub"
    echo "   Repo: ${OWNER}/${REPO}"
    echo "   Branch: ${BRANCH}"
    exit 1
  fi

  # Compare
  if compare_checks "$doc_checks" "$live_checks"; then
    echo "✅ Required Checks: No Drift"
    echo ""
    echo "📖 Doc matches live state"
    echo "🔗 ${OWNER}/${REPO} (${BRANCH})"

    # Show count
    local count
    count="$(echo "$doc_checks" | wc -l | tr -d ' ')"
    echo "📊 Total checks: $count"

    exit 0
  else
    # Drift detected
    if [[ $WARN_ONLY -eq 1 ]]; then
      exit 2
    else
      exit 1
    fi
  fi
}

main "$@"
