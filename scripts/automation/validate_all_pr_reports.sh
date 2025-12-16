#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

VALIDATOR="scripts/validate_pr_report_format.sh"

if [ ! -x "$VALIDATOR" ]; then
  echo "ERROR: Validator not found or not executable: $VALIDATOR"
  echo "Hint: chmod +x $VALIDATOR"
  exit 2
fi

REPORTS=()
while IFS= read -r -d '' file; do
  REPORTS+=("$file")
done < <(find docs/ops -maxdepth 1 -name 'PR_*_FINAL_REPORT.md' -print0 2>/dev/null | sort -z || true)

if [ "${#REPORTS[@]}" -eq 0 ]; then
  echo "No PR final reports found under docs/ops/PR_*_FINAL_REPORT.md — nothing to validate."
  exit 0
fi

echo "Validating ${#REPORTS[@]} PR final report(s)..."
FAIL=0
for f in "${REPORTS[@]}"; do
  echo "==> $f"
  if ! bash "$VALIDATOR" "$f"; then
    echo "FAILED: $f"
    FAIL=1
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo "One or more PR final reports failed validation."
  exit 1
fi

echo "All PR final reports passed validation."
exit 0
