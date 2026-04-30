#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

echo "============================================================"
echo "Peak_Trade Optional Dependency Leak Scan"
echo "============================================================"
echo

# Optional deps allowlist policy:
# - ccxt darf nur in Provider-Modulen und research/new_listings (read-only collector) importiert werden.
# - Tests/Docs sind ausgenommen (dürfen Snippets/Mocks enthalten).
#
# NOTE: We use different regex flavors for rg vs grep:
# - ripgrep supports \s and \b
# - POSIX grep -E does NOT support \s; use [[:space:]] instead
# - GNU grep -E does not treat \b as a word boundary; use \> (end of word)
PATTERN_RG='^\s*(import\s+ccxt\b|from\s+ccxt\b)'
PATTERN_GREP='^[[:space:]]*(import[[:space:]]+ccxt\>|from[[:space:]]+ccxt\>)'

ALLOW_GLOBS=(
  "src/data/providers/**"
  "src/research/new_listings/**"
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

  # grep's --exclude-dir only matches each directory's *basename*, so paths like
  # `src/data/providers` are not excluded. Mirror rg's directory exclusions with
  # find -path … -prune, then grep the remaining regular files only.
  RESULTS="$(
    find . \
      -path './src/data/providers' -prune -o \
      -path './src/research/new_listings' -prune -o \
      -path './tests' -prune -o \
      -path './docs' -prune -o \
      -path './src/docs' -prune -o \
      -path './.git' -prune -o \
      -path '*/__pycache__' -prune -o \
      -type f -print0 \
      | xargs -0 grep -nIHE "${PATTERN_GREP}" 2>/dev/null || true
  )"
fi

if [[ -n "${RESULTS}" ]]; then
  echo "FAIL: optional dependency leak scan (ccxt)"
  echo
  echo "Found ccxt imports outside allowlist:"
  echo "${RESULTS}"
  echo
  echo "Allowlist: src/data/providers/**, src/research/new_listings/**"
  exit 1
fi

echo "PASS: optional deps leak scan (ccxt)"
