#!/usr/bin/env bash
# Validates PR final report markdown formatting
# Usage: ./validate_pr_report_format.sh <PATH_TO_REPORT>

set -euo pipefail

REPORT_FILE="${1:-}"

if [ -z "$REPORT_FILE" ]; then
  echo "ERROR: No report file specified"
  echo "Usage: $0 <PATH_TO_PR_REPORT.md>"
  exit 1
fi

if [ ! -f "$REPORT_FILE" ]; then
  echo "ERROR: Report file not found: $REPORT_FILE"
  exit 1
fi

# 1) The exact regression: broken double backticks at list start
if grep -nE '^- ``' "$REPORT_FILE" >/dev/null; then
  echo "ERROR: Broken markdown list formatting detected (double backticks)."
  echo "Offending lines:"
  grep -nE '^- ``' "$REPORT_FILE" || true
  exit 2
fi

# 2) Catch likely missing closing backtick for src/* bullets (common footgun)
if grep -nE '^- `src/[^`]*$' "$REPORT_FILE" >/dev/null; then
  echo "ERROR: Likely missing closing backtick in src/* bullet line(s)."
  echo "Offending lines:"
  grep -nE '^- `src/[^`]*$' "$REPORT_FILE" || true
  exit 3
fi

# 3) Catch likely missing closing backtick for tests/* bullets
if grep -nE '^- `tests/[^`]*$' "$REPORT_FILE" >/dev/null; then
  echo "ERROR: Likely missing closing backtick in tests/* bullet line(s)."
  echo "Offending lines:"
  grep -nE '^- `tests/[^`]*$' "$REPORT_FILE" || true
  exit 4
fi

# 4) Ensure report has required header structure (flexible for existing formats)
if ! grep -qE '^#.*PR #[0-9]+' "$REPORT_FILE"; then
  echo "ERROR: Report missing required PR header (must contain 'PR #<number>')"
  exit 5
fi

# 5) Ensure Changed Files section exists (if present, must not be empty)
# Note: Older reports may not have this section, so we only validate if it exists
if grep -q '^### Changed Files' "$REPORT_FILE"; then
  # Extract section between "### Changed Files" and next "##" or end of file
  section=$(sed -n '/^### Changed Files/,/^##/p' "$REPORT_FILE" | grep -c '^- ' || echo 0)
  if [ "$section" -eq 0 ]; then
    echo "ERROR: Changed Files section exists but is empty (no files listed)"
    exit 7
  fi
fi

echo "✅ Format validation passed: $REPORT_FILE"
exit 0
