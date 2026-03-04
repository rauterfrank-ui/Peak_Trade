#!/usr/bin/env bash
set -euo pipefail

LABEL="com.peaktrade.operator_all"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl unload "${PLIST_PATH}" >/dev/null 2>&1 || true
rm -f "${PLIST_PATH}"

echo "OK"
echo "REMOVED=${PLIST_PATH}"
