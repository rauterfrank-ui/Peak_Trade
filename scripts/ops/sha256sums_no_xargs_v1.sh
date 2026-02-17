#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/ops/sha256sums_no_xargs_v1.sh <target_dir> [output_file]
# Notes:
# - Produces paths relative to repo root (current working dir).
# - Avoids xargs/ARG_MAX issues; bash 3.2 compatible.
# - Skips output file itself if it exists in target_dir.

TARGET_DIR="${1:-}"
OUT_FILE="${2:-SHA256SUMS.txt}"

if [[ -z "${TARGET_DIR}" ]]; then
  echo "SHA256SUMS_NO_XARGS_FAIL: missing_target_dir" >&2
  exit 2
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "SHA256SUMS_NO_XARGS_FAIL: target_dir_missing target_dir=${TARGET_DIR}" >&2
  exit 3
fi

# normalize OUT path inside target_dir if relative
if [[ "${OUT_FILE}" != /* ]]; then
  OUT_PATH="${TARGET_DIR%/}/${OUT_FILE}"
else
  OUT_PATH="${OUT_FILE}"
fi

# Write deterministically
tmp="${OUT_PATH}.tmp.$$"
rm -f "${tmp}" 2>/dev/null || true

# Find files (excluding OUT file), sort, hash one by one.
# Use -print0 to handle spaces.
# Sorting: LC_ALL=C, null-delimited.
# Output paths should remain relative to repo root (caller should run from repo root).
find "${TARGET_DIR}" -type f -print0 \
  | LC_ALL=C sort -z \
  | while IFS= read -r -d '' f; do
      # skip OUT file and its temp artifacts
      [[ "${f}" == "${OUT_PATH}" ]] && continue
      [[ "${f}" == "${tmp}" ]] && continue
      shasum -a 256 "${f}" >> "${tmp}"
    done

mv -f "${tmp}" "${OUT_PATH}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "${SCRIPT_DIR}/sha256sums_style_guard_v1.sh" "${OUT_PATH}"
echo "SHA256SUMS_NO_XARGS_OK out=${OUT_PATH} target_dir=${TARGET_DIR}"
