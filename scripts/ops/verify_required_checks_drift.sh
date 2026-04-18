#!/usr/bin/env bash
#
# verify_required_checks_drift.sh
#
# Purpose:
#   Thin ops wrapper around the canonical CI drift engine:
#   scripts/ci/required_checks_drift_detector.py
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
#   - python3
#
# Example:
#   verify_required_checks_drift.sh
#   verify_required_checks_drift.sh --warn-only
#   verify_required_checks_drift.sh --owner myorg --repo myrepo

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Defaults / Paths
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OWNER="${OWNER:-rauterfrank-ui}"
REPO="${REPO:-Peak_Trade}"
BRANCH="${BRANCH:-main}"
REQUIRED_CONFIG="config/ci/required_status_checks.json"
WARN_ONLY=0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DETECTOR="$REPO_ROOT/scripts/ci/required_checks_drift_detector.py"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Help
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
show_help() {
  cat <<'HELP'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧭 Required Checks Drift Guard (Single Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ops wrapper around the canonical CI drift detector:
  scripts/ci/required_checks_drift_detector.py
Compares JSON SSOT effective required contexts to live branch protection.

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
  - python3

CANONICAL SOURCE:
  config/ci/required_status_checks.json

CANONICAL ENGINE:
  scripts/ci/required_checks_drift_detector.py
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

  # Check python3
  if ! command -v python3 &>/dev/null; then
    echo "⚠️  python3 not found"
    echo "   Install Python 3"
    echo ""
    echo "⏭️  SKIP - python3 required for drift detector"
    exit 3
  fi

  # Check JSON SSOT config
  if [[ ! -f "$REPO_ROOT/$REQUIRED_CONFIG" ]]; then
    echo "❌ Required config not found: $REPO_ROOT/$REQUIRED_CONFIG"
    errors=$((errors + 1))
  fi

  if [[ ! -f "$DETECTOR" ]]; then
    echo "❌ Required drift detector not found: $DETECTOR"
    errors=$((errors + 1))
  fi

  if [[ $errors -gt 0 ]]; then
    echo ""
    echo "❌ Preflight failed ($errors error(s))"
    exit 1
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main() {
  # Preflight
  preflight_check

  local output=""
  local detector_status=0

  output="$(
    python3 "$DETECTOR" \
      --required-config "$REQUIRED_CONFIG" \
      --compare-live \
      --strict-live \
      --owner "$OWNER" \
      --repo "$REPO" \
      --branch-pattern "$BRANCH" 2>&1
  )" || detector_status=$?

  if [[ -n "$output" ]]; then
    echo "$output"
  fi

  case "$detector_status" in
    0)
      echo "✅ Required Checks: No Drift"
      ;;
    3)
      # Drift in live compare.
      if [[ $WARN_ONLY -eq 1 ]]; then
        exit 2
      fi
      exit 1
      ;;
    2)
      # Missing workflow-producing contexts is also drift and should fail-closed.
      if [[ $WARN_ONLY -eq 1 ]]; then
        exit 2
      fi
      exit 1
      ;;
    4)
      # Strict live compare failure is treated as hard failure after preflight.
      echo "❌ Live compare failed in canonical drift detector"
      exit 1
      ;;
    *)
      echo "❌ Drift detector failed unexpectedly (exit $detector_status)"
      exit 1
      ;;
  esac
}

main "$@"
