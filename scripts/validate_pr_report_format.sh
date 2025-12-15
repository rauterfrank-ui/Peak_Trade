#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/validate_pr_report_format.sh <file1> [file2 ...]
# If no files are provided, it auto-scans docs/ops/PR_*_FINAL_REPORT.md (and skips if none exist).

files=("$@")

if [ "${#files[@]}" -eq 0 ]; then
  if compgen -G "docs/ops/PR_*_FINAL_REPORT.md" > /dev/null; then
    # shellcheck disable=SC2206
    files=(docs/ops/PR_*_FINAL_REPORT.md)
  else
    echo "SKIP: no docs/ops/PR_*_FINAL_REPORT.md files found"
    exit 0
  fi
fi

fail=0

for f in "${files[@]}"; do
  if [ ! -f "$f" ]; then
    echo "SKIP: not a file: $f"
    continue
  fi

  echo "CHECK: $f"

  if grep -nE '^- ``' "$f" >/dev/null; then
    echo "FAIL: broken double backticks in $f"
    grep -nE '^- ``' "$f" || true
    fail=1
  fi

  # optional hardening: likely missing closing backtick for src/* bullets
  if grep -nE '^- `src/[^`]*$' "$f" >/dev/null; then
    echo "FAIL: missing closing backtick in $f"
    grep -nE '^- `src/[^`]*$' "$f" || true
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  exit 2
fi

echo "OK: all checked reports look good"
