#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL="com.peaktrade.operator_all"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

# Ensure a predictable PATH for launchd (minimal env by default)
# Add common locations for Homebrew + pyenv + uv + system tools
LA_ENV_PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.local/bin:${HOME}/.cargo/bin:${HOME}/.pyenv/shims:${HOME}/.pyenv/bin"

LOG_DIR="${REPO_ROOT}/out/ops/launchd"
STDOUT_LOG="${LOG_DIR}/operator_all.stdout.log"
STDERR_LOG="${LOG_DIR}/operator_all.stderr.log"

START_HOUR="${START_HOUR:-7}"
START_MINUTE="${START_MINUTE:-15}"

STRICT_ALERTS="${STRICT_ALERTS:-true}"

MODE="${MODE:-full}"  # full | registry_only
if [ "${MODE}" = "registry_only" ]; then
  RUN_E2E="false"
  RUN_ONE_SHOT="false"
  RUN_REGISTRY="true"
  STRICT_ALERTS="${STRICT_ALERTS:-true}"
else
  RUN_E2E="${RUN_E2E:-true}"
  RUN_ONE_SHOT="${RUN_ONE_SHOT:-true}"
  RUN_REGISTRY="${RUN_REGISTRY:-true}"
  STRICT_ALERTS="${STRICT_ALERTS:-true}"
fi

mkdir -p "${LOG_DIR}"

cat > "${PLIST_PATH}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>-lc</string>
      <string>cd "${REPO_ROOT}" &amp;&amp; RUN_E2E=${RUN_E2E} RUN_ONE_SHOT=${RUN_ONE_SHOT} RUN_REGISTRY=${RUN_REGISTRY} STRICT_ALERTS=${STRICT_ALERTS} ./scripts/ops/operator_all.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>${START_HOUR}</integer>
      <key>Minute</key>
      <integer>${START_MINUTE}</integer>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${STDOUT_LOG}</string>
    <key>StandardErrorPath</key>
    <string>${STDERR_LOG}</string>

    <key>WorkingDirectory</key>
    <string>${REPO_ROOT}</string>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>${LA_ENV_PATH}</string>
    </dict>
  </dict>
</plist>
PLIST

# --- PeakTrade: robust LaunchAgent label extraction (PlistBuddy) ---
_plist_label_from_path() {
  local plist_path="$1"
  if [ -z "${plist_path}" ] || [ ! -f "${plist_path}" ]; then
    return 1
  fi
  /usr/libexec/PlistBuddy -c "Print :Label" "${plist_path}" 2>/dev/null | tr -d '\r' | head -n 1
}
# --- /PeakTrade ---

launchctl unload "${PLIST_PATH}" >/dev/null 2>&1 || true
launchctl load "${PLIST_PATH}"

LA_LABEL="$(_plist_label_from_path "${PLIST_PATH}")" || true

echo "OK"
echo "PLIST=${PLIST_PATH}"
echo "LOG_DIR=${LOG_DIR}"
echo "LA_LABEL=${LA_LABEL:-$LABEL}"
echo "NEXT: tail -f ${STDOUT_LOG}"
