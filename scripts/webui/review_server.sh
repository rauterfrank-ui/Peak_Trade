#!/usr/bin/env bash
# Peak Trade WebUI Review Server Harness v1
# POSIX/macOS Bash 3.2 compatible. Avoid Bash-4-only builtins/arrays. No --reload.
#
# Commands: start | status | open | restart | stop | logs
#
# Env overrides:
#   PEAK_TRADE_WEBUI_HOST
#   PEAK_TRADE_WEBUI_PORT
#   PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS
#   PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS
#   PEAK_TRADE_WEBUI_STATE_DIR
#   PEAK_TRADE_WEBUI_HEALTH_PATH
#   PEAK_TRADE_WEBUI_REVIEW_PATH
#   PEAK_TRADE_WEBUI_LOG_TAIL_LINES
#   PEAK_TRADE_WEBUI_UV
#   PEAK_TRADE_WEBUI_REVIEW_BIND_FIXTURES  # removed with Market Dashboard product

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

HOST="${PEAK_TRADE_WEBUI_HOST:-127.0.0.1}"
PORT="${PEAK_TRADE_WEBUI_PORT:-8000}"
START_TIMEOUT="${PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS:-45}"
STOP_TIMEOUT="${PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS:-15}"
STATE_DIR="${PEAK_TRADE_WEBUI_STATE_DIR:-${REPO_ROOT}/.run/webui_review_server}"
HEALTH_PATH="${PEAK_TRADE_WEBUI_HEALTH_PATH:-/api/health}"
REVIEW_PATH="${PEAK_TRADE_WEBUI_REVIEW_PATH:-/}"
LOG_TAIL_LINES="${PEAK_TRADE_WEBUI_LOG_TAIL_LINES:-80}"
UV_BIN="${PEAK_TRADE_WEBUI_UV:-uv}"
ASGI_TARGET="src.webui.app:app"
IDENTITY_MARKER="peak_trade_webui_review_server_v1"
EXPECTED_CMD_FRAGMENT="uvicorn ${ASGI_TARGET}"
REVIEW_BIND_FIXTURES="0"

PID_FILE="${STATE_DIR}/review_server.pid"
LOG_FILE="${STATE_DIR}/review_server.log"
META_FILE="${STATE_DIR}/review_server.meta"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./scripts/webui/review_server.sh <start|status|open|restart|stop|logs> [options]

  start     Idempotent start (or healthy reuse) of detached review server
  status    Report RUNNING_HEALTHY | RUNNING_UNHEALTHY | STALE_PID |
            PORT_OCCUPIED_BY_UNKNOWN_PROCESS | STOPPED
  open      Ensure healthy server, open review URL in Google Chrome
  restart   stop + start (fail-closed on unknown port owner)
  stop      Stop only the verified harness-owned process
  logs      Show log path and last lines; optional: logs -f|--follow

Environment overrides: PEAK_TRADE_WEBUI_HOST, PEAK_TRADE_WEBUI_PORT,
PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS, PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS,
PEAK_TRADE_WEBUI_STATE_DIR, PEAK_TRADE_WEBUI_HEALTH_PATH, PEAK_TRADE_WEBUI_REVIEW_PATH
EOF
}

ensure_localhost_only() {
  case "$HOST" in
    127.0.0.1|localhost|::1) ;;
    *)
      die "LOCALHOST_ONLY violation: host='$HOST' (allowed: 127.0.0.1|localhost|::1)"
      ;;
  esac
}

ensure_state_dir() {
  mkdir -p "$STATE_DIR"
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

http_ok() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 2 "$url" >/dev/null 2>&1
    return $?
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$url" <<'PY'
import sys, urllib.request
url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=2) as resp:
        sys.exit(0 if getattr(resp, "status", 200) == 200 else 1)
except Exception:
    sys.exit(1)
PY
    return $?
  fi
  return 1
}

process_alive() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

read_pid_file() {
  if [[ ! -f "$PID_FILE" ]]; then
    return 1
  fi
  local raw
  raw="$(tr -d '[:space:]' <"$PID_FILE" 2>/dev/null || true)"
  case "$raw" in
    ''|*[!0-9]*)
      return 1
      ;;
  esac
  printf '%s' "$raw"
}

process_command() {
  local pid="$1"
  # macOS/BSD ps: args= is portable enough; fall back to command=
  ps -p "$pid" -o args= 2>/dev/null || ps -p "$pid" -o command= 2>/dev/null || true
}

process_cwd() {
  local pid="$1"
  # macOS lsof cwd probe; empty if unavailable
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1 || true
}

listening_pids_on_port() {
  # Prefer lsof; empty string if none
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN -t 2>/dev/null | sort -u | tr '\n' ' ' | sed 's/[[:space:]]*$//'
    return 0
  fi
  return 0
}

pid_list_contains() {
  local needle="$1"
  local haystack="$2"
  local item
  for item in $haystack; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

identity_ok() {
  local pid="$1"
  local cmd cwd
  cmd="$(process_command "$pid")"
  [[ -n "$cmd" ]] || return 1
  # Must be uvicorn ASGI for this app; never trust PID alone.
  case "$cmd" in
    *"${EXPECTED_CMD_FRAGMENT}"*) ;;
    *) return 1 ;;
  esac
  case "$cmd" in
    *"--reload"*) return 1 ;;
  esac
  case "$cmd" in
    *"--host ${HOST}"*|*--host="${HOST}"*) ;;
    *) return 1 ;;
  esac
  case "$cmd" in
    *"--port ${PORT}"*|*--port="${PORT}"*) ;;
    *) return 1 ;;
  esac
  cwd="$(process_cwd "$pid")"
  if [[ -n "$cwd" && "$cwd" != "$REPO_ROOT" ]]; then
    # Fail closed if cwd is resolvable and not this repo worktree.
    return 1
  fi
  return 0
}

diagnose_unknown_port_owner() {
  local listeners="$1"
  local pid cmd
  echo "STATUS=PORT_OCCUPIED_BY_UNKNOWN_PROCESS"
  echo "PORT=${PORT}"
  echo "HOST=${HOST}"
  echo "LISTENERS=${listeners}"
  echo "PID_FILE=${PID_FILE}"
  echo "RECOMMENDED_MANUAL_CHECK=lsof -nP -iTCP:${PORT} -sTCP:LISTEN"
  echo "RECOMMENDED_ACTION=never adopt; use a free port, e.g. PEAK_TRADE_WEBUI_PORT=8001 ./scripts/webui/review_server.sh start"
  for pid in $listeners; do
    cmd="$(process_command "$pid")"
    echo "FOREIGN_PID=${pid}"
    echo "FOREIGN_COMMAND=${cmd}"
  done
}

child_pids() {
  local parent="$1"
  # macOS: ps -ax -o pid=,ppid=
  ps -ax -o pid=,ppid= 2>/dev/null | awk -v p="$parent" '$2 == p { print $1 }' || true
}

resolve_owned_listener_pid() {
  local boot_pid="$1"
  local listeners candidate grandchild
  listeners="$(listening_pids_on_port || true)"
  for candidate in $listeners; do
    if identity_ok "$candidate"; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  # Fall back: boot pid or its matching child / grandchild
  if identity_ok "$boot_pid"; then
    printf '%s' "$boot_pid"
    return 0
  fi
  for candidate in $(child_pids "$boot_pid"); do
    if identity_ok "$candidate"; then
      printf '%s' "$candidate"
      return 0
    fi
    for grandchild in $(child_pids "$candidate"); do
      if identity_ok "$grandchild"; then
        printf '%s' "$grandchild"
        return 0
      fi
    done
  done
  return 1
}

_kill_verified_tree() {
  local root_pid="$1"
  local child
  [[ -n "$root_pid" ]] || return 0
  if process_alive "$root_pid"; then
    if identity_ok "$root_pid" || [[ "$(process_command "$root_pid")" == *"${EXPECTED_CMD_FRAGMENT}"* ]] || [[ "$(process_command "$root_pid")" == *"uv run python -m uvicorn"* ]]; then
      for child in $(child_pids "$root_pid"); do
        if process_alive "$child"; then
          if identity_ok "$child" || [[ "$(process_command "$child")" == *"${EXPECTED_CMD_FRAGMENT}"* ]]; then
            kill -TERM "$child" 2>/dev/null || true
          fi
        fi
      done
      kill -TERM "$root_pid" 2>/dev/null || true
    fi
  fi
}

write_meta() {
  local pid="$1"
  cat >"${META_FILE}.tmp" <<EOF
identity=${IDENTITY_MARKER}
pid=${pid}
repo_root=${REPO_ROOT}
host=${HOST}
port=${PORT}
asgi=${ASGI_TARGET}
health_path=${HEALTH_PATH}
review_path=${REVIEW_PATH}
uvicorn_reload=false
localhost_only=true
started_at_unix=$(date +%s)
EOF
  mv "${META_FILE}.tmp" "$META_FILE"
}

write_pid_atomic() {
  local pid="$1"
  printf '%s\n' "$pid" >"${PID_FILE}.tmp"
  mv "${PID_FILE}.tmp" "$PID_FILE"
}

clear_state_files() {
  rm -f "$PID_FILE" "$META_FILE" "${PID_FILE}.tmp" "${META_FILE}.tmp"
}

tail_logs() {
  local n="${1:-$LOG_TAIL_LINES}"
  if [[ -f "$LOG_FILE" ]]; then
    echo "----- last ${n} log lines (${LOG_FILE}) -----"
    tail -n "$n" "$LOG_FILE" || true
  else
    echo "----- no log file at ${LOG_FILE} -----"
  fi
}

review_fixture_env_exports() {
  # Market Dashboard fixture binding removed with product deletion.
  echo "REVIEW_BIND_FIXTURES=false"
  return 0
}

classify_status() {
  # Prints STATUS=... and supporting fields; exit 0 always for status cmd.
  local pid="" listeners="" alive=0 id_ok=0 healthy=0

  listeners="$(listening_pids_on_port || true)"

  if pid="$(read_pid_file)"; then
    if process_alive "$pid"; then
      alive=1
      if identity_ok "$pid"; then
        id_ok=1
      fi
    fi
  fi

  if http_ok "$(health_url)"; then
    healthy=1
  fi

  if [[ "$alive" -eq 1 && "$id_ok" -eq 1 ]]; then
    if [[ "$healthy" -eq 1 ]]; then
      echo "STATUS=RUNNING_HEALTHY"
      echo "PID=${pid}"
      echo "PORT=${PORT}"
      echo "HOST=${HOST}"
      echo "HEALTH_URL=$(health_url)"
      echo "REVIEW_URL=$(review_url)"
      echo "PID_FILE=${PID_FILE}"
      echo "LOG_FILE=${LOG_FILE}"
      return 0
    fi
    echo "STATUS=RUNNING_UNHEALTHY"
    echo "PID=${pid}"
    echo "PORT=${PORT}"
    echo "HOST=${HOST}"
    echo "HEALTH_URL=$(health_url)"
    echo "PID_FILE=${PID_FILE}"
    echo "LOG_FILE=${LOG_FILE}"
    return 0
  fi

  if [[ -n "$listeners" ]]; then
    # Any live listener that is not our verified identity is fail-closed.
    if [[ "$alive" -ne 1 || "$id_ok" -ne 1 ]]; then
      diagnose_unknown_port_owner "$listeners"
      return 0
    fi
  fi

  if [[ -f "$PID_FILE" && "$alive" -eq 0 ]]; then
    echo "STATUS=STALE_PID"
    echo "PID_FILE=${PID_FILE}"
    echo "STALE_PID_VALUE=${pid:-}"
    echo "PORT=${PORT}"
    echo "HOST=${HOST}"
    return 0
  fi

  echo "STATUS=STOPPED"
  echo "PORT=${PORT}"
  echo "HOST=${HOST}"
  echo "PID_FILE=${PID_FILE}"
  echo "LOG_FILE=${LOG_FILE}"
}

cmd_status() {
  ensure_localhost_only
  ensure_state_dir
  classify_status
}

wait_for_health() {
  local boot_pid="$1"
  local start_ts now elapsed listeners owned
  start_ts="$(date +%s)"
  while true; do
    if http_ok "$(health_url)"; then
      return 0
    fi
    listeners="$(listening_pids_on_port || true)"
    owned="$(resolve_owned_listener_pid "$boot_pid" || true)"
    if ! process_alive "$boot_pid" && [[ -z "$owned" ]] && [[ -z "$listeners" ]]; then
      echo "ERROR: review server process exited during start (boot_pid=${boot_pid})" >&2
      tail_logs 40 >&2
      return 1
    fi
    now="$(date +%s)"
    elapsed=$((now - start_ts))
    if [[ "$elapsed" -ge "$START_TIMEOUT" ]]; then
      echo "ERROR: healthcheck timeout after ${START_TIMEOUT}s url=$(health_url)" >&2
      tail_logs 40 >&2
      return 1
    fi
    sleep 0.25
  done
}

recover_stale_pid_if_needed() {
  local status_line
  status_line="$(classify_status | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" == "STALE_PID" ]]; then
    echo "INFO: recovering stale PID file"
    clear_state_files
  fi
}

cmd_start() {
  ensure_localhost_only
  ensure_state_dir

  local status_blob status_line listeners pid

  status_blob="$(classify_status)"
  status_line="$(printf '%s\n' "$status_blob" | sed -n 's/^STATUS=//p' | head -n 1)"

  if [[ "$status_line" == "RUNNING_HEALTHY" ]]; then
    printf '%s\n' "$status_blob"
    echo "ACTION=REUSED_EXISTING_HEALTHY"
    echo "IDEMPOTENT_START=true"
    return 0
  fi

  if [[ "$status_line" == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" ]]; then
    printf '%s\n' "$status_blob" >&2
    die "unknown process occupies port ${PORT}; refuse to start or adopt (UNKNOWN_PORT_OWNER_FAIL_CLOSED). Use a free port, e.g. PEAK_TRADE_WEBUI_PORT=8001 ./scripts/webui/review_server.sh start"
  fi

  if [[ "$status_line" == "RUNNING_UNHEALTHY" ]]; then
    printf '%s\n' "$status_blob" >&2
    die "owned process is RUNNING_UNHEALTHY; use restart after diagnosing logs"
  fi

  if [[ "$status_line" == "STALE_PID" ]]; then
    echo "INFO: clearing stale PID state before start"
    clear_state_files
  fi

  listeners="$(listening_pids_on_port || true)"
  if [[ -n "$listeners" ]]; then
    diagnose_unknown_port_owner "$listeners" >&2
    die "port ${PORT} already in use by unknown process"
  fi

  if [[ ! -x "${REPO_ROOT}/scripts/ops/ensure_web_extra.sh" ]]; then
    die "missing ${REPO_ROOT}/scripts/ops/ensure_web_extra.sh"
  fi
  (
    cd "$REPO_ROOT"
    ./scripts/ops/ensure_web_extra.sh
  )

  if ! command -v "$UV_BIN" >/dev/null 2>&1; then
    die "uv not found (PEAK_TRADE_WEBUI_UV=${UV_BIN})"
  fi

  : >"$LOG_FILE"

  echo "REVIEW_BIND_FIXTURES=false"

  # Detached start: nohup + closed stdin; no --reload.
  # Boot PID may be `uv`; after health we re-bind pidfile to the verified listener.
  (
    cd "$REPO_ROOT"
    # shellcheck disable=SC2086
    nohup env \
      PEAK_TRADE_WEBUI_REVIEW_MARKER="${IDENTITY_MARKER}" \
      PEAK_TRADE_WEBUI_REVIEW_REPO_ROOT="${REPO_ROOT}" \
      LIVE_AUTHORIZED=false \
      ORDERS_ALLOWED=false \
      ${UV_BIN} run python -m uvicorn "${ASGI_TARGET}" \
        --host "${HOST}" \
        --port "${PORT}" \
        --log-level info \
      </dev/null >>"${LOG_FILE}" 2>&1 &
    echo $!
  ) >"${PID_FILE}.boot"

  boot_pid="$(tr -d '[:space:]' <"${PID_FILE}.boot")"
  rm -f "${PID_FILE}.boot"
  case "$boot_pid" in
    ''|*[!0-9]*)
      die "failed to capture review server boot pid"
      ;;
  esac

  write_pid_atomic "$boot_pid"
  write_meta "$boot_pid"

  if ! wait_for_health "$boot_pid"; then
    # Controlled cleanup of our failed start tree only.
    _kill_verified_tree "$boot_pid"
    clear_state_files
    die "start failed (healthcheck not ready)"
  fi

  pid="$(resolve_owned_listener_pid "$boot_pid" || true)"
  if [[ -z "${pid:-}" ]]; then
    echo "ERROR: could not resolve owned listener pid after healthy start" >&2
    _kill_verified_tree "$boot_pid"
    clear_state_files
    die "listener identity resolution failed"
  fi

  if ! identity_ok "$pid"; then
    echo "ERROR: started pid=${pid} failed process identity validation" >&2
    echo "COMMAND=$(process_command "$pid")" >&2
    _kill_verified_tree "$boot_pid"
    _kill_verified_tree "$pid"
    clear_state_files
    die "process identity validation failed"
  fi

  write_pid_atomic "$pid"
  write_meta "$pid"
  # Keep boot wrapper alive if distinct: terminating `uv` can tear down the listener.

  echo "STATUS=RUNNING_HEALTHY"
  echo "ACTION=STARTED"
  echo "PID=${pid}"
  echo "BOOT_PID=${boot_pid}"
  echo "PORT=${PORT}"
  echo "HOST=${HOST}"
  echo "HEALTH_URL=$(health_url)"
  echo "REVIEW_URL=$(review_url)"
  echo "PID_FILE=${PID_FILE}"
  echo "LOG_FILE=${LOG_FILE}"
  echo "UVICORN_RELOAD=false"
  echo "LOCALHOST_ONLY=true"
  echo "IDEMPOTENT_START=true"
}

cmd_stop() {
  ensure_localhost_only
  ensure_state_dir

  local status_blob status_line pid start_ts now elapsed

  status_blob="$(classify_status)"
  status_line="$(printf '%s\n' "$status_blob" | sed -n 's/^STATUS=//p' | head -n 1)"

  if [[ "$status_line" == "STOPPED" ]]; then
    clear_state_files
    echo "STATUS=STOPPED"
    echo "ACTION=ALREADY_STOPPED"
    return 0
  fi

  if [[ "$status_line" == "STALE_PID" ]]; then
    # Only clear if no unknown listener was reported as primary last STATUS.
    # classify may print STALE then PORT_OCCUPIED; handle carefully.
    if printf '%s\n' "$status_blob" | grep -q '^FOREIGN_PID='; then
      printf '%s\n' "$status_blob" >&2
      die "refuse to stop: port occupied by unknown process"
    fi
    clear_state_files
    echo "STATUS=STOPPED"
    echo "ACTION=CLEARED_STALE_PID"
    return 0
  fi

  if [[ "$status_line" == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" ]]; then
    printf '%s\n' "$status_blob" >&2
    die "refuse to stop unknown port owner (UNKNOWN_PORT_OWNER_FAIL_CLOSED)"
  fi

  pid="$(read_pid_file || true)"
  if [[ -z "${pid:-}" ]]; then
    die "missing pid file for stop"
  fi
  if ! process_alive "$pid"; then
    clear_state_files
    echo "STATUS=STOPPED"
    echo "ACTION=CLEARED_DEAD_PID"
    return 0
  fi
  if ! identity_ok "$pid"; then
    echo "PID=${pid}" >&2
    echo "COMMAND=$(process_command "$pid")" >&2
    die "refuse to stop: process identity validation failed"
  fi

  # Capture parent before signaling; `uv` wrappers must be considered for stop.
  parent_pid="$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d '[:space:]' || true)"
  parent_cmd=""
  if [[ -n "${parent_pid:-}" && "$parent_pid" != "1" ]]; then
    parent_cmd="$(process_command "$parent_pid")"
  fi

  _kill_verified_tree "$pid"
  case "$parent_cmd" in
    *"uv run python -m uvicorn"*|*"${EXPECTED_CMD_FRAGMENT}"*)
      kill -TERM "$parent_pid" 2>/dev/null || true
      ;;
  esac

  start_ts="$(date +%s)"
  while process_alive "$pid"; do
    now="$(date +%s)"
    elapsed=$((now - start_ts))
    if [[ "$elapsed" -ge "$STOP_TIMEOUT" ]]; then
      echo "WARN: TERM timeout; escalating to KILL for verified pid=${pid}" >&2
      kill -KILL "$pid" 2>/dev/null || true
      case "$parent_cmd" in
        *"uv run python -m uvicorn"*|*"${EXPECTED_CMD_FRAGMENT}"*)
          if process_alive "$parent_pid"; then
            kill -KILL "$parent_pid" 2>/dev/null || true
          fi
          ;;
      esac
      break
    fi
    sleep 0.2
  done

  # Final wait slice after KILL
  start_ts="$(date +%s)"
  while process_alive "$pid"; do
    now="$(date +%s)"
    elapsed=$((now - start_ts))
    if [[ "$elapsed" -ge 5 ]]; then
      die "verified pid=${pid} did not exit after KILL"
    fi
    sleep 0.2
  done

  clear_state_files
  echo "STATUS=STOPPED"
  echo "ACTION=STOPPED"
  echo "PID=${pid}"
}

cmd_restart() {
  ensure_localhost_only
  local status_blob status_line
  status_blob="$(classify_status)"
  status_line="$(printf '%s\n' "$status_blob" | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" ]]; then
    printf '%s\n' "$status_blob" >&2
    die "restart refused: unknown port owner"
  fi
  if [[ "$status_line" != "STOPPED" ]]; then
    cmd_stop
  fi
  status_blob="$(classify_status)"
  status_line="$(printf '%s\n' "$status_blob" | sed -n 's/^STATUS=//p' | head -n 1)"
  if [[ "$status_line" == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" ]]; then
    printf '%s\n' "$status_blob" >&2
    die "restart refused after stop: unknown port owner remains"
  fi
  clear_state_files
  cmd_start
  echo "ACTION=RESTARTED"
}

chrome_open() {
  local url="$1"
  if [[ -d "/Applications/Google Chrome.app" ]]; then
    open -a "Google Chrome" "$url"
    return 0
  fi
  if command -v google-chrome >/dev/null 2>&1; then
    google-chrome "$url" >/dev/null 2>&1 &
    return 0
  fi
  if command -v chromium >/dev/null 2>&1; then
    echo "WARN: Google Chrome missing; using documented Chromium fallback" >&2
    chromium "$url" >/dev/null 2>&1 &
    echo "CHROMIUM_FALLBACK_USED=true"
    return 0
  fi
  die "Google Chrome not found (refusing Safari as primary browser)"
}

cmd_open() {
  cmd_start
  local url
  url="$(review_url)"
  chrome_open "$url"
  echo "OPENED_URL=${url}"
  echo "PRIMARY_BROWSER=GOOGLE_CHROME"
}

cmd_logs() {
  ensure_state_dir
  echo "LOG_FILE=${LOG_FILE}"
  if [[ ! -f "$LOG_FILE" ]]; then
    echo "INFO: log file not created yet"
    return 0
  fi
  case "${1:-}" in
    -f|--follow)
      tail -n "$LOG_TAIL_LINES" -f "$LOG_FILE"
      ;;
    *)
      tail -n "$LOG_TAIL_LINES" "$LOG_FILE"
      ;;
  esac
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    start) cmd_start "$@" ;;
    status) cmd_status "$@" ;;
    open) cmd_open "$@" ;;
    restart) cmd_restart "$@" ;;
    stop) cmd_stop "$@" ;;
    logs) cmd_logs "$@" ;;
    -h|--help|help|"") usage; [[ -n "$cmd" ]] || exit 2; exit 0 ;;
    *) usage >&2; die "unknown command: ${cmd}" ;;
  esac
}

main "$@"
