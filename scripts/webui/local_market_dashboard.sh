#!/usr/bin/env bash
# Peak Trade local Market Dashboard — durable LaunchAgent operator controller.
#
# CAPABILITY_ID=WEBUI_LOCAL_MARKET_DASHBOARD_LAUNCHAGENT_V1
#
# Survives Cursor window / agent-shell / Terminal tab close.
# Operator browser open uses only the regular macOS "Google Chrome" app and
# reuses an existing dashboard tab when present (exactly one dashboard tab).
#
# No runtime / trading / authority effect.
# LIVE_AUTHORIZED=false · ORDERS_ALLOWED=false · LOCALHOST_ONLY
#
# Commands:
#   ./scripts/webui/local_market_dashboard.sh start|stop|restart|status|open|logs
#
# Env overrides:
#   PEAK_TRADE_WEBUI_HOST (default 127.0.0.1)
#   PEAK_TRADE_WEBUI_PORT (default 8000)
#   PEAK_TRADE_WEBUI_REVIEW_PATH (default /market)
#   PEAK_TRADE_WEBUI_HEALTH_PATH (default /api/health)
#   PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS (default 60)
#   PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS (default 20)
#   PEAK_TRADE_WEBUI_UV (default: repo .venv python preferred, else uv)
#   PEAK_TRADE_MARKET_DASHBOARD_LABEL (default com.peaktrade.market-dashboard)

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPT_ABS="${REPO_ROOT}/scripts/webui/local_market_dashboard.sh"

HOST="${PEAK_TRADE_WEBUI_HOST:-127.0.0.1}"
PORT="${PEAK_TRADE_WEBUI_PORT:-8000}"
REVIEW_PATH="${PEAK_TRADE_WEBUI_REVIEW_PATH:-/market}"
HEALTH_PATH="${PEAK_TRADE_WEBUI_HEALTH_PATH:-/api/health}"
START_TIMEOUT="${PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS:-60}"
STOP_TIMEOUT="${PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS:-20}"
LOG_TAIL_LINES="${PEAK_TRADE_WEBUI_LOG_TAIL_LINES:-80}"
LABEL="${PEAK_TRADE_MARKET_DASHBOARD_LABEL:-com.peaktrade.market-dashboard}"

ASGI_TARGET="src.webui.app:app"
IDENTITY_MARKER="peak_trade_local_market_dashboard_launchagent_v1"
EXPECTED_CMD_FRAGMENT="uvicorn ${ASGI_TARGET}"

PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="${HOME}/Library/Logs/Peak_Trade"
STDOUT_LOG="${LOG_DIR}/market-dashboard.stdout.log"
STDERR_LOG="${LOG_DIR}/market-dashboard.stderr.log"
STATE_DIR="${REPO_ROOT}/.run/local_market_dashboard"
META_FILE="${STATE_DIR}/launchagent.meta"
THR_INTERVAL=5

die() {
  echo "ERROR: $*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./scripts/webui/local_market_dashboard.sh <start|stop|restart|status|open|logs>

  start     Install/load LaunchAgent, wait until health is OK (idempotent)
  stop      Boot out LaunchAgent and stop owned listener
  restart   stop + start
  status    Report launchd + health + port ownership
  open      Ensure healthy, open/reuse exactly one Google Chrome dashboard tab
  logs      Show stdout/stderr tails; optional: logs -f|--follow

Durable under label com.peaktrade.market-dashboard (user LaunchAgent).
EOF
}

ensure_localhost_only() {
  case "$HOST" in
    127.0.0.1|localhost|::1) ;;
    *)
      die "LOCALHOST_ONLY violation: host='$HOST'"
      ;;
  esac
}

ensure_dirs() {
  mkdir -p "$LOG_DIR" "$STATE_DIR" "$(dirname "$PLIST_PATH")"
}

base_url() {
  printf 'http://%s:%s' "$HOST" "$PORT"
}

health_url() {
  printf '%s%s' "$(base_url)" "$HEALTH_PATH"
}

review_url() {
  printf '%s%s' "$(base_url)" "$REVIEW_PATH"
}

dashboard_url_prefix() {
  # Prefix used for Chrome tab reuse (must match operator URL start).
  printf 'http://127.0.0.1:%s/market' "$PORT"
}

http_ok() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 2 "$url" >/dev/null 2>&1
    return $?
  fi
  return 1
}

resolve_python() {
  if [[ -n "${PEAK_TRADE_WEBUI_PYTHON:-}" && -x "${PEAK_TRADE_WEBUI_PYTHON}" ]]; then
    printf '%s' "${PEAK_TRADE_WEBUI_PYTHON}"
    return 0
  fi
  if [[ -x "${REPO_ROOT}/.venv/bin/python3" ]]; then
    printf '%s' "${REPO_ROOT}/.venv/bin/python3"
    return 0
  fi
  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    printf '%s' "${REPO_ROOT}/.venv/bin/python"
    return 0
  fi
  die "missing repo venv python at ${REPO_ROOT}/.venv/bin/python3"
}

gui_domain() {
  printf 'gui/%s' "$(id -u)"
}

service_target() {
  printf '%s/%s' "$(gui_domain)" "$LABEL"
}

launchd_loaded() {
  launchctl print "$(service_target)" >/dev/null 2>&1
}

launchd_pid() {
  # Prefer pid from launchctl print when available.
  local out pid
  out="$(launchctl print "$(service_target)" 2>/dev/null || true)"
  pid="$(printf '%s\n' "$out" | sed -n 's/^[[:space:]]*pid = //p' | head -n 1 | tr -d '[:space:]')"
  case "${pid:-}" in
    ''|0|*[!0-9]*) printf '' ;;
    *) printf '%s' "$pid" ;;
  esac
}

listening_pids_on_port() {
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN -t 2>/dev/null | sort -u | tr '\n' ' ' | sed 's/[[:space:]]*$//'
}

process_command() {
  local pid="$1"
  ps -p "$pid" -o command= 2>/dev/null || true
}

process_alive() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

identity_ok() {
  local pid="$1" cmd
  cmd="$(process_command "$pid")"
  case "$cmd" in
    *"${EXPECTED_CMD_FRAGMENT}"*) return 0 ;;
    *) return 1 ;;
  esac
}

write_meta() {
  local pid="${1:-}"
  cat >"$META_FILE" <<EOF
identity=${IDENTITY_MARKER}
label=${LABEL}
pid=${pid}
repo_root=${REPO_ROOT}
host=${HOST}
port=${PORT}
asgi=${ASGI_TARGET}
health_path=${HEALTH_PATH}
review_path=${REVIEW_PATH}
plist_path=${PLIST_PATH}
stdout_log=${STDOUT_LOG}
stderr_log=${STDERR_LOG}
started_at_unix=$(date +%s)
EOF
}

render_plist() {
  local py
  py="$(resolve_python)"
  ensure_dirs
  cat >"$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>${THR_INTERVAL}</integer>
  <key>WorkingDirectory</key>
  <string>${REPO_ROOT}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PEAK_TRADE_WEBUI_REVIEW_MARKER</key>
    <string>${IDENTITY_MARKER}</string>
    <key>PEAK_TRADE_WEBUI_REVIEW_REPO_ROOT</key>
    <string>${REPO_ROOT}</string>
    <key>PEAK_TRADE_LOCAL_MARKET_DASHBOARD</key>
    <string>1</string>
    <key>LIVE_AUTHORIZED</key>
    <string>false</string>
    <key>ORDERS_ALLOWED</key>
    <string>false</string>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
  </dict>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${SCRIPT_ABS}</string>
    <string>_run</string>
  </array>
  <key>StandardOutPath</key>
  <string>${STDOUT_LOG}</string>
  <key>StandardErrorPath</key>
  <string>${STDERR_LOG}</string>
</dict>
</plist>
EOF
  # Embed resolved python into a sibling run note for operators (plist uses _run).
  printf 'resolved_python=%s\n' "$py" >"${STATE_DIR}/resolved_python.txt"
  if command -v plutil >/dev/null 2>&1; then
    plutil -lint "$PLIST_PATH" >/dev/null
  fi
}

# Foreground entrypoint for launchd KeepAlive (must not daemonize).
cmd_run() {
  ensure_localhost_only
  cd "$REPO_ROOT"
  local py
  py="$(resolve_python)"
  export PEAK_TRADE_WEBUI_REVIEW_MARKER="${IDENTITY_MARKER}"
  export PEAK_TRADE_WEBUI_REVIEW_REPO_ROOT="${REPO_ROOT}"
  export PEAK_TRADE_LOCAL_MARKET_DASHBOARD=1
  export LIVE_AUTHORIZED=false
  export ORDERS_ALLOWED=false
  export PYTHONUNBUFFERED=1
  exec "$py" -m uvicorn "${ASGI_TARGET}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --log-level info
}

stop_conflicting_review_harness_if_owned() {
  # If the legacy nohup harness owns the port, stop it so LaunchAgent can bind.
  local review_status
  if [[ ! -x "${REPO_ROOT}/scripts/webui/review_server.sh" ]]; then
    return 0
  fi
  review_status="$(
    PEAK_TRADE_WEBUI_HOST="$HOST" \
    PEAK_TRADE_WEBUI_PORT="$PORT" \
    PEAK_TRADE_WEBUI_REVIEW_PATH="$REVIEW_PATH" \
    "${REPO_ROOT}/scripts/webui/review_server.sh" status 2>/dev/null || true
  )"
  if printf '%s\n' "$review_status" | grep -q '^STATUS=RUNNING_HEALTHY\|^STATUS=RUNNING_UNHEALTHY'; then
    echo "INFO: stopping legacy review_server.sh owner on port ${PORT}"
    PEAK_TRADE_WEBUI_HOST="$HOST" \
    PEAK_TRADE_WEBUI_PORT="$PORT" \
    PEAK_TRADE_WEBUI_REVIEW_PATH="$REVIEW_PATH" \
      "${REPO_ROOT}/scripts/webui/review_server.sh" stop 2>/dev/null || true
  fi
}

port_owner_class() {
  # Prints: FREE | OWNED_LAUNCHD | OWNED_UVICORN_UNKNOWN | FOREIGN
  local listeners pid cmd
  listeners="$(listening_pids_on_port || true)"
  if [[ -z "${listeners:-}" ]]; then
    echo "FREE"
    return 0
  fi
  for pid in $listeners; do
    if identity_ok "$pid"; then
      if launchd_loaded; then
        local lpid
        lpid="$(launchd_pid)"
        if [[ -n "$lpid" && "$lpid" == "$pid" ]]; then
          echo "OWNED_LAUNCHD"
          return 0
        fi
        # uvicorn identity matches and launchd loaded — treat as ours
        echo "OWNED_LAUNCHD"
        return 0
      fi
      echo "OWNED_UVICORN_UNKNOWN"
      return 0
    fi
    cmd="$(process_command "$pid")"
    echo "FOREIGN pid=${pid} cmd=${cmd}"
    return 0
  done
  echo "FOREIGN"
}

wait_for_health() {
  local start_ts now elapsed
  start_ts="$(date +%s)"
  while true; do
    if http_ok "$(health_url)"; then
      return 0
    fi
    now="$(date +%s)"
    elapsed=$((now - start_ts))
    if [[ "$elapsed" -ge "$START_TIMEOUT" ]]; then
      echo "ERROR: healthcheck timeout after ${START_TIMEOUT}s url=$(health_url)" >&2
      echo "--- stderr (tail) ---" >&2
      tail -n 40 "$STDERR_LOG" 2>/dev/null >&2 || true
      echo "--- stdout (tail) ---" >&2
      tail -n 40 "$STDOUT_LOG" 2>/dev/null >&2 || true
      return 1
    fi
    sleep 0.5
  done
}

bootstrap_agent() {
  local domain
  domain="$(gui_domain)"
  ensure_dirs
  render_plist
  if launchd_loaded; then
    launchctl bootout "$(service_target)" 2>/dev/null || true
    # Also try path-based bootout for older state
    launchctl bootout "$domain" "$PLIST_PATH" 2>/dev/null || true
    sleep 0.5
  fi
  launchctl bootstrap "$domain" "$PLIST_PATH"
  launchctl enable "$(service_target)" 2>/dev/null || true
  launchctl kickstart -k "$(service_target)" 2>/dev/null || launchctl kickstart "$(service_target)"
}

bootout_agent() {
  local domain
  domain="$(gui_domain)"
  if launchd_loaded; then
    launchctl bootout "$(service_target)" 2>/dev/null || true
  fi
  launchctl bootout "$domain" "$PLIST_PATH" 2>/dev/null || true
}

wait_for_stopped() {
  local start_ts now elapsed listeners pid
  start_ts="$(date +%s)"
  while true; do
    listeners="$(listening_pids_on_port || true)"
    pid="$(launchd_pid)"
    if [[ -z "${listeners:-}" ]] && ! launchd_loaded && [[ -z "${pid:-}" ]]; then
      return 0
    fi
    # If launchd unloaded but a matching uvicorn remains, TERM it only when identity matches.
    if ! launchd_loaded && [[ -n "${listeners:-}" ]]; then
      for pid in $listeners; do
        if identity_ok "$pid"; then
          kill -TERM "$pid" 2>/dev/null || true
        else
          echo "ERROR: refuse to kill foreign listener pid=${pid}" >&2
          return 1
        fi
      done
    fi
    now="$(date +%s)"
    elapsed=$((now - start_ts))
    if [[ "$elapsed" -ge "$STOP_TIMEOUT" ]]; then
      listeners="$(listening_pids_on_port || true)"
      if [[ -n "${listeners:-}" ]]; then
        for pid in $listeners; do
          if identity_ok "$pid"; then
            kill -KILL "$pid" 2>/dev/null || true
          fi
        done
      fi
      sleep 0.5
      listeners="$(listening_pids_on_port || true)"
      if [[ -z "${listeners:-}" ]] && ! launchd_loaded; then
        return 0
      fi
      echo "ERROR: stop timeout; listeners='${listeners:-}' launchd_loaded=$(launchd_loaded && echo true || echo false)" >&2
      return 1
    fi
    sleep 0.25
  done
}

print_status_blob() {
  local owner health loaded pid listeners
  owner="$(port_owner_class)"
  loaded=false
  launchd_loaded && loaded=true
  pid="$(launchd_pid)"
  listeners="$(listening_pids_on_port || true)"
  health=false
  http_ok "$(health_url)" && health=true

  if [[ "$loaded" == true && "$health" == true ]]; then
    echo "STATUS=RUNNING_HEALTHY"
  elif [[ "$loaded" == true && "$health" == false ]]; then
    echo "STATUS=RUNNING_UNHEALTHY"
  elif [[ "$owner" == FREE && "$loaded" == false ]]; then
    echo "STATUS=STOPPED"
  elif [[ "$owner" == OWNED_UVICORN_UNKNOWN ]]; then
    echo "STATUS=PORT_OCCUPIED_BY_ORPHAN_UVICORN"
  elif [[ "$owner" == FOREIGN* ]]; then
    echo "STATUS=PORT_OCCUPIED_BY_UNKNOWN_PROCESS"
  elif [[ "$loaded" == false && -n "${listeners:-}" ]]; then
    echo "STATUS=PORT_OCCUPIED_BY_UNKNOWN_PROCESS"
  else
    echo "STATUS=STOPPED"
  fi

  echo "LABEL=${LABEL}"
  echo "LAUNCHD_LOADED=${loaded}"
  echo "LAUNCHD_PID=${pid:-}"
  echo "PORT=${PORT}"
  echo "HOST=${HOST}"
  echo "LISTENERS=${listeners:-}"
  echo "PORT_OWNER_CLASS=${owner}"
  echo "HEALTH_OK=${health}"
  echo "HEALTH_URL=$(health_url)"
  echo "REVIEW_URL=$(review_url)"
  echo "PLIST_PATH=${PLIST_PATH}"
  echo "STDOUT_LOG=${STDOUT_LOG}"
  echo "STDERR_LOG=${STDERR_LOG}"
  echo "REPO_ROOT=${REPO_ROOT}"
}

cmd_status() {
  ensure_localhost_only
  print_status_blob
}

cmd_start() {
  ensure_localhost_only
  ensure_dirs

  local status_line owner
  status_line="$(print_status_blob | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" == "RUNNING_HEALTHY" ]]; then
    print_status_blob
    echo "ACTION=REUSED_EXISTING_HEALTHY"
    echo "IDEMPOTENT_START=true"
    return 0
  fi

  owner="$(port_owner_class)"
  case "$owner" in
    FOREIGN*)
      print_status_blob >&2
      die "unknown process occupies port ${PORT}; refuse to start (UNKNOWN_PORT_OWNER_FAIL_CLOSED)"
      ;;
  esac

  stop_conflicting_review_harness_if_owned

  # Clear orphan uvicorn that matches our identity but is not launchd-managed.
  owner="$(port_owner_class)"
  if [[ "$owner" == "OWNED_UVICORN_UNKNOWN" ]]; then
    local listeners pid
    listeners="$(listening_pids_on_port || true)"
    for pid in $listeners; do
      if identity_ok "$pid"; then
        echo "INFO: terminating orphan uvicorn pid=${pid} before LaunchAgent start"
        kill -TERM "$pid" 2>/dev/null || true
      fi
    done
    sleep 1
  fi

  if [[ ! -x "${REPO_ROOT}/scripts/ops/ensure_web_extra.sh" ]]; then
    die "missing ${REPO_ROOT}/scripts/ops/ensure_web_extra.sh"
  fi
  (
    cd "$REPO_ROOT"
    ./scripts/ops/ensure_web_extra.sh
  )

  # Rotate soft: keep previous logs by appending a separator marker.
  {
    echo "===== START $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  } >>"$STDOUT_LOG" 2>/dev/null || true
  {
    echo "===== START $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  } >>"$STDERR_LOG" 2>/dev/null || true

  bootstrap_agent

  if ! wait_for_health; then
    die "start failed (healthcheck not ready)"
  fi

  write_meta "$(launchd_pid)"
  print_status_blob
  echo "ACTION=STARTED"
  echo "IDEMPOTENT_START=true"
  echo "DURABLE=true"
  echo "SURVIVES_CURSOR_AND_TERMINAL_CLOSE=true"
}

cmd_stop() {
  ensure_localhost_only
  ensure_dirs

  local status_line
  status_line="$(print_status_blob | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" == "STOPPED" ]]; then
    echo "STATUS=STOPPED"
    echo "ACTION=ALREADY_STOPPED"
    return 0
  fi
  if [[ "$status_line" == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" ]]; then
    print_status_blob >&2
    die "refuse to stop unknown port owner (UNKNOWN_PORT_OWNER_FAIL_CLOSED)"
  fi

  bootout_agent
  if ! wait_for_stopped; then
    die "stop failed"
  fi
  echo "STATUS=STOPPED"
  echo "ACTION=STOPPED"
  echo "LABEL=${LABEL}"
}

cmd_restart() {
  ensure_localhost_only
  local status_line
  status_line="$(print_status_blob | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" ]]; then
    print_status_blob >&2
    die "restart refused: unknown port owner"
  fi
  if [[ "$status_line" != "STOPPED" ]]; then
    cmd_stop
  fi
  cmd_start
  echo "ACTION=RESTARTED"
}

chrome_open_reuse_tab() {
  local url prefix
  url="$(review_url)"
  prefix="$(dashboard_url_prefix)"

  if [[ ! -d "/Applications/Google Chrome.app" ]]; then
    die "Google Chrome not found at /Applications/Google Chrome.app (refusing Safari / Playwright)"
  fi

  # Regular Google Chrome only. Reuse existing dashboard tab when present.
  # Forbidden: new Chrome instance flags, temp profiles, Playwright, Chrome process kills.
  osascript \
    -e "set targetURL to \"${url}\"" \
    -e "set targetPrefix to \"${prefix}\"" \
    -e 'tell application "Google Chrome"
  set foundWindow to missing value
  set foundTabIndex to 0
  set windowCount to count of windows
  repeat with w from 1 to windowCount
    set tabCount to count of tabs of window w
    repeat with t from 1 to tabCount
      set tabURL to URL of tab t of window w
      if tabURL starts with targetPrefix then
        set foundWindow to w
        set foundTabIndex to t
        exit repeat
      end if
    end repeat
    if foundWindow is not missing value then exit repeat
  end repeat

  if foundWindow is not missing value then
    set active tab index of window foundWindow to foundTabIndex
    set index of window foundWindow to 1
    activate
    return "REUSED_EXISTING_TAB"
  end if

  if (count of windows) > 0 then
    tell window 1
      set newTab to make new tab with properties {URL:targetURL}
      set active tab index to (count of tabs)
    end tell
    set index of window 1 to 1
    activate
    return "OPENED_NEW_TAB_IN_EXISTING_WINDOW"
  end if

  activate
  if (count of windows) = 0 then
    make new window
  end if
  set URL of active tab of window 1 to targetURL
  activate
  return "OPENED_NEW_WINDOW_TAB"
end tell'
}

cmd_open() {
  ensure_localhost_only
  local status_line action
  status_line="$(print_status_blob | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" != "RUNNING_HEALTHY" ]]; then
    cmd_start
  fi
  status_line="$(print_status_blob | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" != "RUNNING_HEALTHY" ]]; then
    print_status_blob >&2
    die "refusing open: dashboard not RUNNING_HEALTHY"
  fi

  action="$(chrome_open_reuse_tab)"
  print_status_blob
  echo "OPENED_URL=$(review_url)"
  echo "PRIMARY_BROWSER=GOOGLE_CHROME"
  echo "BROWSER_ACTION=${action}"
  echo "TAB_REUSE_POLICY=PREFIX_http://127.0.0.1:${PORT}/market"
  echo "PLAYWRIGHT_USED=false"
  echo "TEMP_PROFILE_USED=false"
}

cmd_logs() {
  ensure_dirs
  echo "STDOUT_LOG=${STDOUT_LOG}"
  echo "STDERR_LOG=${STDERR_LOG}"
  case "${1:-}" in
    -f|--follow)
      if [[ -f "$STDOUT_LOG" || -f "$STDERR_LOG" ]]; then
        tail -n "$LOG_TAIL_LINES" -F "$STDOUT_LOG" "$STDERR_LOG"
      else
        echo "INFO: log files not created yet"
      fi
      ;;
    *)
      echo "===== STDOUT (tail) ====="
      if [[ -f "$STDOUT_LOG" ]]; then
        tail -n "$LOG_TAIL_LINES" "$STDOUT_LOG"
      else
        echo "INFO: stdout log not created yet"
      fi
      echo "===== STDERR (tail) ====="
      if [[ -f "$STDERR_LOG" ]]; then
        tail -n "$LOG_TAIL_LINES" "$STDERR_LOG"
      else
        echo "INFO: stderr log not created yet"
      fi
      ;;
  esac
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    start) cmd_start "$@" ;;
    stop) cmd_stop "$@" ;;
    restart) cmd_restart "$@" ;;
    status) cmd_status "$@" ;;
    open) cmd_open "$@" ;;
    logs) cmd_logs "$@" ;;
    _run) cmd_run "$@" ;;
    -h|--help|help|"") usage; [[ -n "$cmd" ]] || exit 2; exit 0 ;;
    *) usage >&2; die "unknown command: ${cmd}" ;;
  esac
}

main "$@"
