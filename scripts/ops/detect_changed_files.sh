#!/usr/bin/env bash
# detect_changed_files.sh
#
# Helper script for gate workflows to detect if relevant files changed.
# Returns exit code 0 if files matching patterns were changed, 1 otherwise.
#
# Usage:
#   detect_changed_files.sh <base_sha> <head_sha> <pattern1> [pattern2 ...]
#
# Examples:
#   detect_changed_files.sh $BASE $HEAD "src/live/" "src/execution/"
#   detect_changed_files.sh $BASE $HEAD "\.py$"

set -euo pipefail

if [ $# -lt 3 ]; then
    echo "Usage: $0 <base_sha> <head_sha> <pattern1> [pattern2 ...]" >&2
    exit 2
fi

BASE_SHA="$1"
HEAD_SHA="$2"
shift 2
PATTERNS=("$@")

echo "Checking for changes between $BASE_SHA and $HEAD_SHA" >&2

# Get changed files
CHANGED_FILES=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" 2>/dev/null || {
    echo "Error: Could not get diff between $BASE_SHA and $HEAD_SHA" >&2
    exit 2
})

if [ -z "$CHANGED_FILES" ]; then
    echo "No files changed" >&2
    exit 1
fi

echo "Changed files:" >&2
echo "$CHANGED_FILES" >&2
echo >&2

# Check if any file matches any pattern
for pattern in "${PATTERNS[@]}"; do
    if echo "$CHANGED_FILES" | grep -qE "$pattern"; then
        echo "✅ Match found for pattern: $pattern" >&2
        echo "$CHANGED_FILES" | grep -E "$pattern" >&2
        exit 0
    fi
done

echo "ℹ️ No files matching patterns: ${PATTERNS[*]}" >&2
exit 1
