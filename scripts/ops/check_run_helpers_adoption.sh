#!/usr/bin/env bash
set -euo pipefail

# Peak_Trade – Run Helpers Adoption Guard
# - Default: strict (exit 1 on missing)
# - --warn-only: prints warnings, exits 0
# - --all-ops: scan scripts/ops/*.sh (best-effort)
# - otherwise: checks a curated list of important ops scripts

WARN_ONLY=0
SCAN_ALL_OPS=0

for arg in "$@"; do
  case "$arg" in
    --warn-only) WARN_ONLY=1 ;;
    --all-ops) SCAN_ALL_OPS=1 ;;
    -h|--help)
      echo "Usage: $0 [--warn-only] [--all-ops]"
      exit 0
      ;;
    *) ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPS_DIR="${ROOT}/scripts/ops"
HELPERS="run_helpers.sh"

fail=0

check_file() {
  local f="$1"
  if [[ ! -f "$f" ]]; then
    echo "⚠️  missing file: $f"
    fail=1
    return
  fi
  if ! grep -q "${HELPERS}" "$f"; then
    echo "❌ missing helpers include (${HELPERS}): $f"
    fail=1
  else
    echo "✅ helpers referenced: $f"
  fi
}

echo "🔎 Run-Helpers Adoption Guard"
echo "Root: ${ROOT}"

if [[ "$SCAN_ALL_OPS" -eq 1 ]]; then
  shopt -s nullglob
  files=("${OPS_DIR}"/*.sh)
  shopt -u nullglob
  if [[ "${#files[@]}" -eq 0 ]]; then
    echo "⚠️  no ops scripts found in ${OPS_DIR}"
    exit 0
  fi
  for f in "${files[@]}"; do
    check_file "$f"
  done
else
  # Curated: keep this list small & meaningful (avoid noisy gate).
  check_file "${OPS_DIR}/pr_inventory_full.sh"
  check_file "${OPS_DIR}/label_merge_log_prs.sh"
fi

if [[ "$fail" -ne 0 ]]; then
  if [[ "$WARN_ONLY" -eq 1 ]]; then
    echo "⚠️  WARN-ONLY: adoption issues found (not failing)."
    exit 0
  fi
  echo "❌ Adoption guard failed."
  exit 1
fi

echo "🎉 Adoption guard OK."
