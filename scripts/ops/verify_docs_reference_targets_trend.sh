#!/usr/bin/env bash
set -euo pipefail

# Verify Docs Reference Targets Trend
#
# Compares current full-scan missing targets against baseline.
# FAILS if current_missing_count > baseline_missing_count.
#
# This ensures we don't add NEW missing doc targets while allowing
# gradual debt paydown.
#
# Exit codes:
#   0 = OK (no new missing targets)
#   1 = FAIL (new missing targets introduced)
#   2 = WARN (baseline not found or invalid)

REPO_ROOT=""
BASELINE_FILE=""
VERBOSE=0

usage() {
  cat <<'EOF'
verify_docs_reference_targets_trend.sh

Verifies that docs reference targets debt is not increasing.

Exit codes:
  0 = OK (current <= baseline)
  1 = FAIL (current > baseline)
  2 = WARN (baseline missing or invalid)

Usage:
  scripts/ops/verify_docs_reference_targets_trend.sh [OPTIONS]

Options:
  --repo-root <path>     Repository root (default: auto-detect)
  --baseline <file>      Baseline JSON file (default: docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json)
  --verbose, -v          Verbose output
  -h, --help             Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root) REPO_ROOT="${2:-}"; [[ -n "$REPO_ROOT" ]] || { echo "Missing value for --repo-root"; exit 1; }; shift 2 ;;
    --baseline) BASELINE_FILE="${2:-}"; [[ -n "$BASELINE_FILE" ]] || { echo "Missing value for --baseline"; exit 1; }; shift 2 ;;
    -v|--verbose) VERBOSE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

# Determine repo root
if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"

# Determine baseline file
if [[ -z "$BASELINE_FILE" ]]; then
  BASELINE_FILE="$REPO_ROOT/docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json"
fi

cd "$REPO_ROOT"

# Check if baseline exists
if [[ ! -f "$BASELINE_FILE" ]]; then
  echo "⚠️  WARN: Baseline not found: $BASELINE_FILE"
  echo ""
  echo "To create baseline:"
  echo "  python scripts/ops/collect_docs_reference_targets_fullscan.py"
  echo ""
  exit 2
fi

# Load baseline
if ! baseline_data=$(python3 -c "import json, sys; print(json.load(open('$BASELINE_FILE'))['missing_count'])" 2>/dev/null); then
  echo "⚠️  WARN: Failed to parse baseline JSON: $BASELINE_FILE"
  exit 2
fi

baseline_count="$baseline_data"

echo "📊 Docs Reference Targets Trend Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Baseline: $baseline_count missing targets"
echo ""

# Run current scan to temp file
temp_scan=$(mktemp)
trap 'rm -f "$temp_scan"' EXIT

echo "🔍 Running current full-scan..."
if [[ "$VERBOSE" == "1" ]]; then
  python3 scripts/ops/collect_docs_reference_targets_fullscan.py --output "$temp_scan"
else
  python3 scripts/ops/collect_docs_reference_targets_fullscan.py --output "$temp_scan" 2>/dev/null
fi

# Extract current count
if ! current_count=$(python3 -c "import json; print(json.load(open('$temp_scan'))['missing_count'])" 2>/dev/null); then
  echo "❌ FAIL: Could not parse current scan results"
  exit 1
fi

echo "Current:  $current_count missing targets"
echo ""

# Compare
delta=$((current_count - baseline_count))

if [[ $current_count -gt $baseline_count ]]; then
  echo "❌ FAIL: NEW missing targets introduced (+$delta)"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📋 New Missing Targets (Top 20)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Show diff: find new items not in baseline
  python3 - "$BASELINE_FILE" "$temp_scan" <<'PYDIFF'
import json
import sys

baseline_path = sys.argv[1]
current_path = sys.argv[2]

with open(baseline_path) as f:
    baseline = json.load(f)

with open(current_path) as f:
    current = json.load(f)

# Create set of baseline items for quick lookup
baseline_set = set()
for item in baseline["missing_items"]:
    key = (item["source_file"], item["line_number"], item["target"])
    baseline_set.add(key)

# Find new items
new_items = []
for item in current["missing_items"]:
    key = (item["source_file"], item["line_number"], item["target"])
    if key not in baseline_set:
        new_items.append(item)

# Show top 20
for i, item in enumerate(new_items[:20], 1):
    source = item["source_file"]
    line = item["line_number"]
    target = item["target"]
    print(f"{i:3d}. {source}:{line}")
    print(f"     → {target}")

if len(new_items) > 20:
    print(f"\n... and {len(new_items) - 20} more")
PYDIFF

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "To fix:"
  echo "1. Fix the new missing references in your PR"
  echo "2. Or update baseline (if intentional):"
  echo "   python scripts/ops/collect_docs_reference_targets_fullscan.py"
  echo "   git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json"
  echo ""
  echo "See: docs/ops/DOCS_REFERENCE_TARGETS_DEBT_GUIDE.md"
  echo ""
  exit 1

elif [[ $current_count -lt $baseline_count ]]; then
  improvement=$((baseline_count - current_count))
  echo "✅ PASS: Docs debt IMPROVED! ($improvement fewer missing targets)"
  echo ""
  echo "🎉 Great work! Consider updating baseline:"
  echo "   python scripts/ops/collect_docs_reference_targets_fullscan.py"
  echo "   git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json"
  echo ""
  exit 0

else
  echo "✅ PASS: No new missing targets (debt stable)"
  echo ""
  exit 0
fi
