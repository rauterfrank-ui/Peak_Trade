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
echo ""

UNICODE_GUARD="scripts/automation/unicode_guard.py"
if [ ! -f "$UNICODE_GUARD" ]; then
  echo "WARNING: Unicode guard not found: $UNICODE_GUARD"
  echo "Skipping Unicode security checks."
  UNICODE_GUARD=""
fi

FAIL=0
for f in "${REPORTS[@]}"; do
  echo "==> $f"

  # Run format validator
  if ! bash "$VALIDATOR" "$f"; then
    echo "FAILED (format): $f"
    FAIL=1
  fi

  # Run Unicode guard if available
  if [ -n "$UNICODE_GUARD" ]; then
    if ! python3 "$UNICODE_GUARD" "$f"; then
      echo "FAILED (Unicode): $f"
      FAIL=1
    fi
  fi

  echo ""
done

if [ "$FAIL" -ne 0 ]; then
  echo "❌ One or more PR final reports failed validation."
  exit 1
fi

echo "✅ All PR final reports passed validation (format + Unicode security)."
exit 0
