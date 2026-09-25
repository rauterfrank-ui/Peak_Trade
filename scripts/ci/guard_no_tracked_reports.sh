#!/usr/bin/env bash
set -euo pipefail

# CI Guard: Prevent tracked files in reports/ and docs/reports/
# Exit 0 if clean, exit 1 if violations found

echo "=== CI Policy Guard: No Tracked Files in Reports Directories ==="
echo ""

# Patterns to check (tracked files only)
PATTERNS=(
  "^reports/"
  "^docs/reports/"
)

VIOLATIONS=()
EXCLUDE_FILES=(".gitkeep")

# Collect all tracked files matching patterns
for pattern in "${PATTERNS[@]}"; do
  while IFS= read -r file; do
    # Skip empty lines
    [[ -z "$file" ]] && continue

    # Check if file should be excluded
    basename_file="$(basename "$file")"
    excluded=false
    for exclude in "${EXCLUDE_FILES[@]}"; do
      if [[ "$basename_file" == "$exclude" ]]; then
        excluded=true
        break
      fi
    done

    # Add to violations if not excluded
    if [[ "$excluded" == false ]]; then
      VIOLATIONS+=("$file")
    fi
  done < <(git ls-files | grep -E "$pattern" || true)
done

# Report results
if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
  echo "✅ PASS: No tracked files found in reports/ or docs/reports/"
  echo ""
  echo "Policy: Keep tracked documentation under docs/*, generated artifacts under reports/* (gitignored)"
  exit 0
else
  echo "::error::Policy violation: Tracked files found in reports/ or docs/reports/"
  echo ""
  echo "Found ${#VIOLATIONS[@]} tracked file(s) in forbidden directories:"
  echo ""
  for file in "${VIOLATIONS[@]}"; do
    echo "  - $file"
    echo "::error file=$file::File should not be tracked (reports/ directories are gitignored)"
  done
  echo ""
  echo "Policy: Keep tracked documentation under docs/*, generated artifacts under reports/* (gitignored)"
  echo ""
  echo "To fix:"
  echo "  1. Move documentation files to docs/reporting/ or docs/research/"
  echo "  2. Run: git rm --cached <file>"
  echo "  3. Ensure reports/ and docs/reports/ are in .gitignore"
  echo ""
  exit 1
fi
