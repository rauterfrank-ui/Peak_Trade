#!/usr/bin/env bash
set -euo pipefail

# --- PeakTrade: robust LaunchAgent label extraction (PlistBuddy) ---
_plist_label_from_path() {
  local plist_path="$1"
  if [ -z "${plist_path}" ] || [ ! -f "${plist_path}" ]; then
    return 1
  fi
  /usr/libexec/PlistBuddy -c "Print :Label" "${plist_path}" 2>/dev/null | tr -d '\r' | head -n 1
}
# --- /PeakTrade ---

PLIST_PATH="${HOME}/Library/LaunchAgents/com.peaktrade.operator_all.plist"
LA_LABEL="$(_plist_label_from_path "${PLIST_PATH}")" || true

launchctl unload "${PLIST_PATH}" >/dev/null 2>&1 || true
rm -f "${PLIST_PATH}"

echo "OK"
echo "REMOVED=${PLIST_PATH}"
