#!/usr/bin/env bash
set -euo pipefail

# Scan for housekeeping issues without making changes
# Outputs a plan that can be reviewed before execution

ROOT="$(git rev-parse --show-toplevel)"
TS="$(date +%Y-%m-%d_%H-%M-%S)"
SCAN_OUT="${ROOT}/reports/housekeeping/scan_${TS}"
PLAN_OUT="${ROOT}/reports/housekeeping/cleanup_plan_${TS}.md"

mkdir -p "${SCAN_OUT}"
mkdir -p "$(dirname "${PLAN_OUT}")"

echo "=== Repo Housekeeping Scan @ ${TS} ===" | tee "${SCAN_OUT}/meta.txt"
echo "ROOT=${ROOT}" | tee -a "${SCAN_OUT}/meta.txt"

# 1. Find potential duplicate files (by name pattern)
echo "Scanning for duplicate file patterns..." | tee -a "${SCAN_OUT}/meta.txt"
git ls-files | sort | uniq -d > "${SCAN_OUT}/exact_duplicates.txt" || true

# Find similar names (case insensitive duplicates, .bak, .old, copy, etc.)
git ls-files | grep -iE '\.(bak|old|backup|copy|tmp|temp|~)$' > "${SCAN_OUT}/backup_files.txt" || true
git ls-files | grep -iE '(_old|_backup|_copy|_tmp|_temp|-old|-backup|-copy)' > "${SCAN_OUT}/versioned_names.txt" || true

# 2. Find empty directories (tracked - git doesn't track truly empty dirs)
# This finds dirs with only .gitkeep or similar
find . -type d -not -path '*/\.*' -empty 2>/dev/null > "${SCAN_OUT}/empty_dirs.txt" || true

# 3. Find files not matching naming conventions
# Top-level markdown files (should be in docs/ or specific exceptions)
git ls-files '*.md' | grep -v '^docs/' | grep -v '^README' | grep -v '^CONTRIBUTING' | grep -v '^CHANGELOG' | grep -v '^LICENSE' > "${SCAN_OUT}/toplevel_md_files.txt" || true

# 4. Find potential config duplicates
git ls-files 'config*.toml' | grep -v '^config/' > "${SCAN_OUT}/config_outside_config_dir.txt" || true
git ls-files 'config*.yaml' | grep -v '^config/' >> "${SCAN_OUT}/config_outside_config_dir.txt" || true
git ls-files 'config*.yml' | grep -v '^config/' >> "${SCAN_OUT}/config_outside_config_dir.txt" || true

# 5. Find gitignore duplicates
git ls-files '.gitignore' > "${SCAN_OUT}/all_gitignores.txt" || true
git ls-files 'gitignore' >> "${SCAN_OUT}/all_gitignores.txt" || true

# 6. Large files (>1MB)
git ls-files -z | xargs -0 -I{} bash -c 'SIZE=$(wc -c "{}" 2>/dev/null | awk "{print \$1}"); if [ "$SIZE" -gt 1048576 ]; then echo "$SIZE {}"; fi' | sort -nr > "${SCAN_OUT}/large_files.txt" || true

# 7. Detect nested duplicate structures (e.g., archive contains copies)
echo "Checking archive/ for potential duplicate structures..." | tee -a "${SCAN_OUT}/meta.txt"
if [ -d archive ]; then
  find archive -type f -name '*.py' | head -n 100 > "${SCAN_OUT}/archive_python_files.txt" || true
  find src -type f -name '*.py' | head -n 100 > "${SCAN_OUT}/src_python_files.txt" || true
fi

# 8. TODOs in filenames (rare but indicates incomplete work)
git ls-files | grep -iE 'todo' > "${SCAN_OUT}/todo_in_filenames.txt" || true

# 9. Generate cleanup plan
{
  echo "# Repo Housekeeping Cleanup Plan"
  echo
  echo "Generated: ${TS}"
  echo "Commit: \`$(git rev-parse --short HEAD)\`"
  echo
  echo "## Overview"
  echo "This plan identifies files and directories that may need cleanup."
  echo "Review each section carefully before executing any moves/deletions."
  echo

  echo "## 1. Backup/Old Files"
  echo
  if [ -s "${SCAN_OUT}/backup_files.txt" ]; then
    echo "Found $(wc -l < "${SCAN_OUT}/backup_files.txt") backup-style files:"
    echo '```'
    head -n 50 "${SCAN_OUT}/backup_files.txt"
    echo '```'
    echo
    echo "**Action**: Review and remove if no longer needed, or move to archive/"
  else
    echo "✓ No backup files found"
  fi
  echo

  echo "## 2. Versioned Names (old, copy, tmp)"
  echo
  if [ -s "${SCAN_OUT}/versioned_names.txt" ]; then
    echo "Found $(wc -l < "${SCAN_OUT}/versioned_names.txt") versioned filename patterns:"
    echo '```'
    head -n 50 "${SCAN_OUT}/versioned_names.txt"
    echo '```'
    echo
    echo "**Action**: Review and consolidate or archive"
  else
    echo "✓ No versioned name patterns found"
  fi
  echo

  echo "## 3. Top-level Markdown Files"
  echo
  if [ -s "${SCAN_OUT}/toplevel_md_files.txt" ]; then
    echo "Found $(wc -l < "${SCAN_OUT}/toplevel_md_files.txt") markdown files in root (should be in docs/):"
    echo '```'
    cat "${SCAN_OUT}/toplevel_md_files.txt"
    echo '```'
    echo
    echo "**Action**: Move to docs/ops/ or docs/ with \`git mv\`"
  else
    echo "✓ No misplaced markdown files"
  fi
  echo

  echo "## 4. Config Files Outside config/"
  echo
  if [ -s "${SCAN_OUT}/config_outside_config_dir.txt" ]; then
    echo "Found config files outside config/ directory:"
    echo '```'
    cat "${SCAN_OUT}/config_outside_config_dir.txt"
    echo '```'
    echo
    echo "**Action**: Consolidate into config/ or ensure there's a reason for top-level placement"
  else
    echo "✓ Config files properly organized"
  fi
  echo

  echo "## 5. Gitignore Files"
  echo
  if [ -s "${SCAN_OUT}/all_gitignores.txt" ]; then
    echo "Found gitignore files:"
    echo '```'
    cat "${SCAN_OUT}/all_gitignores.txt"
    echo '```'
    echo
    echo "**Action**: Should typically have one .gitignore at root; check for duplicates"
  else
    echo "✓ Gitignore setup normal"
  fi
  echo

  echo "## 6. Large Files (>1MB)"
  echo
  if [ -s "${SCAN_OUT}/large_files.txt" ]; then
    echo "Found large files:"
    echo '```'
    head -n 20 "${SCAN_OUT}/large_files.txt"
    echo '```'
    echo
    echo "**Action**: Consider if these belong in git or should use Git LFS"
  else
    echo "✓ No large files found"
  fi
  echo

  echo "## 7. Archive Analysis"
  echo
  echo "Archive contains Python files: $(wc -l < "${SCAN_OUT}/archive_python_files.txt" 2>/dev/null || echo 0)"
  echo "Src contains Python files: $(wc -l < "${SCAN_OUT}/src_python_files.txt" 2>/dev/null || echo 0)"
  echo
  echo "**Action**: Review archive/ to ensure it's truly deprecated and doesn't contain needed code"
  echo

  echo "## Next Steps"
  echo
  echo "1. Review this plan carefully"
  echo "2. Create a cleanup branch: \`git checkout -b chore/repo-housekeeping\`"
  echo "3. Use \`git mv\` for all moves (never copy+delete)"
  echo "4. Use \`git rm\` for deletions"
  echo "5. Run \`pytest\` after each major change"
  echo "6. Commit incrementally with descriptive messages"
  echo
  echo "## Raw Scan Data"
  echo "- Location: \`reports/housekeeping/scan_${TS}/\`"

} > "${PLAN_OUT}"

echo
echo "✓ Scan complete!"
echo "  Raw data: ${SCAN_OUT}/"
echo "  Plan: ${PLAN_OUT}"
echo
echo "Review the plan, then execute cleanup operations manually or with a follow-up script."
