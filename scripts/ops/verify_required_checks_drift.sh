#!/usr/bin/env bash
#
# verify_required_checks_drift.sh
#
# Purpose:
#   Verify that Branch Protection Required Checks (live on GitHub) match
#   the canonical JSON SSOT effective required contexts.
#
# Usage:
#   verify_required_checks_drift.sh [options]
#
# Options:
#   --owner OWNER       GitHub owner/org (default: rauterfrank-ui)
#   --repo REPO         Repository name (default: Peak_Trade)
#   --branch BRANCH     Branch name (default: main)
#   --required-config   Path to JSON SSOT config
#   --warn-only         Exit 2 instead of 1 on drift (for soft warnings)
#   --help              Show this help
#
# Exit Codes:
#   0 - Match (no drift)
#   1 - Drift detected (or hard error)
#   2 - Drift detected in warn-only mode
#   3 - Cannot run (missing dependencies: gh CLI or auth)
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
REQUIRED_CONFIG="config/ci/required_status_checks.json"
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
match JSON SSOT effective required contexts.

USAGE:
  verify_required_checks_drift.sh [options]

OPTIONS:
  --owner OWNER       GitHub owner/org (default: rauterfrank-ui)
  --repo REPO         Repository name (default: Peak_Trade)
  --branch BRANCH     Branch name (default: main)
  --required-config   Path to JSON SSOT config
                     (default: config/ci/required_status_checks.json)
  --warn-only         Exit 2 instead of 1 on drift
  --help              Show this help

EXIT CODES:
  0 - Match (no drift)
  1 - Drift detected (or hard error)
  2 - Drift detected in warn-only mode
  3 - Cannot run (missing dependencies)

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

CANONICAL SOURCE:
  config/ci/required_status_checks.json
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
    --required-config)
      REQUIRED_CONFIG="$2"
      shift 2
      ;;
    --doc)
      echo "⚠️  --doc is deprecated and ignored. JSON SSOT is authoritative."
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
  local warnings=0

  # Detect CI environment
  local in_ci=0
  if [[ "${CI:-}" == "true" ]] || [[ "${GITHUB_ACTIONS:-}" == "true" ]] || [[ -n "${GITHUB_WORKFLOW:-}" ]]; then
    in_ci=1
  fi

  # Check gh CLI
  if ! command -v gh &>/dev/null; then
    echo "⚠️  gh CLI not found"
    echo "   Install: brew install gh"
    echo ""
    echo "⏭️  SKIP - gh CLI required for live check"
    exit 3
  elif ! gh auth status &>/dev/null 2>&1; then
    echo "⚠️  gh not authenticated"
    echo "   Run: gh auth login"
    echo ""
    echo "⏭️  SKIP - gh auth required for live check"
    exit 3
  fi

  # Check jq
  if ! command -v jq &>/dev/null; then
    echo "⚠️  jq not found"
    echo "   Install: brew install jq"
    echo ""
    echo "⏭️  SKIP - jq required for live check"
    exit 3
  fi

  # Check JSON SSOT config
  if [[ ! -f "$REPO_ROOT/$REQUIRED_CONFIG" ]]; then
    echo "❌ Required config not found: $REPO_ROOT/$REQUIRED_CONFIG"
    errors=$((errors + 1))
  fi

  if [[ $errors -gt 0 ]]; then
    echo ""
    echo "❌ Preflight failed ($errors error(s))"
    exit 1
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Extract Effective Required Checks from JSON SSOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Output: sorted unique list of check names (one per line)
extract_expected_checks() {
  jq -r '
    (.required_contexts // []) as $required
    | ((.ignored_contexts // []) | unique) as $ignored
    | $required[]
    | tostring
    | select(($ignored | index(.)) | not)
  ' "$REPO_ROOT/$REQUIRED_CONFIG" \
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
  local expected_checks="$1"
  local live_checks="$2"

  # Save to temp files for comm
  local tmp_expected
  local tmp_live
  tmp_expected="$(mktemp)"
  tmp_live="$(mktemp)"

  echo "$expected_checks" > "$tmp_expected"
  echo "$live_checks" > "$tmp_live"

  # comm requires sorted input (already sorted)
  # comm -23: expected in SSOT but not in live (missing from live)
  # comm -13: in live but not in SSOT effective required list (extra in live)
  local missing
  local extra
  missing="$(comm -23 "$tmp_expected" "$tmp_live")"
  extra="$(comm -13 "$tmp_expected" "$tmp_live")"

  rm -f "$tmp_expected" "$tmp_live"

  # Check for drift
  if [[ -z "$missing" && -z "$extra" ]]; then
    # Perfect match
    return 0
  else
    # Drift detected
    echo "🔍 Required Checks Drift Detected"
    echo ""

    if [[ -n "$missing" ]]; then
      echo "❌ Missing from Live (in JSON SSOT effective required, not on GitHub):"
      while IFS= read -r check; do
        [[ -n "$check" ]] && echo "   - $check"
      done <<< "$missing"
      echo ""
    fi

    if [[ -n "$extra" ]]; then
      echo "⚠️  Extra in Live (on GitHub, not in JSON SSOT effective required):"
      while IFS= read -r check; do
        [[ -n "$check" ]] && echo "   - $check"
      done <<< "$extra"
      echo ""
    fi

    echo "📖 JSON SSOT: $REQUIRED_CONFIG"
    echo "🔗 Live: ${OWNER}/${REPO} (branch: ${BRANCH})"
    echo ""
    echo "💡 Action Required:"
    echo "   Update JSON SSOT or adjust branch protection."

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
  local expected_checks
  expected_checks="$(extract_expected_checks)"

  if [[ -z "$expected_checks" ]]; then
    echo "❌ Error: No effective required checks found in JSON SSOT"
    echo "   Config: $REQUIRED_CONFIG"
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
  if compare_checks "$expected_checks" "$live_checks"; then
    echo "✅ Required Checks: No Drift"
    echo ""
    echo "📖 JSON SSOT effective required contexts match live state"
    echo "🔗 ${OWNER}/${REPO} (${BRANCH})"

    # Show count
    local count
    count="$(echo "$expected_checks" | wc -l | tr -d ' ')"
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
