#!/usr/bin/env bash
set -euo pipefail

BASE="origin/main"
THRESHOLD=200
WARN_ONLY=0
PATHS=("docs")

usage() {
  cat <<USAGE
Usage: $(basename "$0") [--base <ref>] [--threshold <n>] [--warn-only] [--paths <p1,p2,...>]

Checks git diff numstat against BASE and fails if any file under PATHS has deletions >= THRESHOLD.
Default: BASE=origin/main, THRESHOLD=200, PATHS=docs, fail (exit 1) on violation.

Examples:
  $(basename "$0")
  $(basename "$0") --threshold 500
  $(basename "$0") --warn-only
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="$2"; shift 2;;
    --threshold) THRESHOLD="$2"; shift 2;;
    --warn-only) WARN_ONLY=1; shift 1;;
    --paths)
      IFS=',' read -r -a PATHS <<< "$2"
      shift 2
      ;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

# Ensure base exists locally
git fetch origin >/dev/null 2>&1 || true

echo "🔎 Docs Diff Guard"
echo "  BASE:       $BASE"
echo "  THRESHOLD:  $THRESHOLD deletions per file"
echo "  PATHS:      ${PATHS[*]}"
echo ""

# Collect numstat; ignore binary files (shown as '-' '-')
VIOLATIONS=0
TOTAL_DEL=0

while IFS=$'\t' read -r add del path; do
  [[ "$add" == "-" || "$del" == "-" ]] && continue
  TOTAL_DEL=$((TOTAL_DEL + del))
  if [[ "$del" -ge "$THRESHOLD" ]]; then
    VIOLATIONS=$((VIOLATIONS + 1))
    echo "🚨 Large deletion: -$del  $path"
  fi
done < <(git diff --numstat "$BASE"...HEAD -- "${PATHS[@]}")

echo ""
echo "Total deletions under ${PATHS[*]}: $TOTAL_DEL"
echo "Violations (per-file >= $THRESHOLD): $VIOLATIONS"
echo ""

if [[ "$VIOLATIONS" -gt 0 ]]; then
  if [[ "$WARN_ONLY" -eq 1 ]]; then
    echo "⚠️ WARN-ONLY: violations detected but not failing."
    exit 0
  fi
  echo "❌ FAIL: docs deletions exceed threshold. If intentional, rerun with --warn-only or raise --threshold."
  exit 1
fi

echo "✅ OK: no large doc deletions detected."
