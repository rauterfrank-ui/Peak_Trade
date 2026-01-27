#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

echo "============================================================"
echo "Peak_Trade Optional Dependency Leak Scan"
echo "============================================================"
echo

# Optional deps allowlist policy:
# - ccxt darf nur in Provider-Modulen importiert werden.
# - Tests/Docs sind ausgenommen (dürfen Snippets/Mocks enthalten).
#
# NOTE: We use different regex flavors for rg vs grep:
# - ripgrep supports \s
# - POSIX grep -E does NOT (use [[:space:]] instead)
PATTERN_RG='^\s*(import\s+ccxt\b|from\s+ccxt\b)'
PATTERN_GREP='^[[:space:]]*(import[[:space:]]+ccxt\\b|from[[:space:]]+ccxt\\b)'

ALLOW_GLOBS=(
  "src/data/providers/**"
)

EXCLUDE_GLOBS=(
  "tests/**"
  "docs/**"
  "src/docs/**"
  ".git/**"
  "**/__pycache__/**"
)

echo "Scanning for ccxt imports outside allowlist..."
echo "pattern: ${PATTERN_RG}"
echo

RESULTS=""

if command -v rg >/dev/null 2>&1; then
  # Search everything, but exclude allowlisted + excluded paths via globs.
  # NOTE: We explicitly exclude providers from the scan, so any remaining hit is a leak.
  RG_ARGS=(rg -n --hidden --no-messages "${PATTERN_RG}" .)

  for g in "${ALLOW_GLOBS[@]}"; do
    RG_ARGS+=(--glob "!${g}")
  done
  for g in "${EXCLUDE_GLOBS[@]}"; do
    RG_ARGS+=(--glob "!${g}")
  done

  RESULTS="$("${RG_ARGS[@]}" || true)"
else
  echo "WARN: rg not found, falling back to grep."
  echo

  # Build grep excludes (directories)
  # providers excluded (allowlist)
  GREP_EXCLUDES=(
    "--exclude-dir=src/data/providers"
    "--exclude-dir=tests"
    "--exclude-dir=docs"
    "--exclude-dir=.git"
    "--exclude-dir=__pycache__"
  )

  # grep -R: recursive, -n: line numbers, -I: ignore binary, -E: extended regex
  # IMPORTANT: options must come BEFORE the path, otherwise grep treats them as filenames.
  RESULTS="$(grep -RInIE "${PATTERN_GREP}" "${GREP_EXCLUDES[@]}" . 2>/dev/null || true)"
fi

if [[ -n "${RESULTS}" ]]; then
  echo "FAIL: optional dependency leak scan (ccxt)"
  echo
  echo "Found ccxt imports outside allowlist:"
  echo "${RESULTS}"
  echo
  echo "Allowlist: src/data/providers/**"
  exit 1
fi

echo "PASS: optional deps leak scan (ccxt)"
