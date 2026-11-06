#!/usr/bin/env bash
set -euo pipefail

# collect_cursor_logs.sh
# Purpose: Collect Cursor (macOS) log sessions and minimal diagnostics into a timestamped bundle.

ts="$(date +%Y%m%d_%H%M%S)"
out_dir="${1:-./artifacts/cursor_logs_${ts}}"

mkdir -p "${out_dir}"

echo "[INFO] Writing bundle to: ${out_dir}"

# Cursor logs default location (macOS)
LOGROOT="${HOME}/Library/Application Support/Cursor/logs"

{
  echo "== System =="
  sw_vers 2>/dev/null || true
  echo
  echo "== Uname =="
  uname -a 2>/dev/null || true
  echo
  echo "== Date =="
  date
  echo
  echo "== Process snapshot (cursor/vscode) =="
  ps aux | egrep -i '(cursor|code|vscode)' | head -n 200 || true
} > "${out_dir}/system.txt"

if [ -d "${LOGROOT}" ]; then
  echo "[INFO] Found logs dir: ${LOGROOT}"
  mapfile -t newest < <(ls -1t "${LOGROOT}" 2>/dev/null | head -n 5 || true)
  if [ "${#newest[@]}" -gt 0 ]; then
    mkdir -p "${out_dir}/logs"
    for d in "${newest[@]}"; do
      src="${LOGROOT}/${d}"
      if [ -d "${src}" ]; then
        echo "[INFO] Copying ${src}"
        ditto "${src}" "${out_dir}/logs/${d}" 2>/dev/null || cp -R "${src}" "${out_dir}/logs/${d}" || true
      fi
    done
  else
    echo "[WARN] No session folders found under ${LOGROOT}" | tee "${out_dir}/warnings.txt"
  fi
else
  echo "[WARN] Logs dir not found: ${LOGROOT}" | tee "${out_dir}/warnings.txt"
fi

tarball="${out_dir}.tgz"
tar -czf "${tarball}" -C "$(dirname "${out_dir}")" "$(basename "${out_dir}")" 2>/dev/null || true
echo "[INFO] Created tarball (best effort): ${tarball}"

echo "[OK] Done."
