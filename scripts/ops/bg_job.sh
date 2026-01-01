#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
bg_job.sh — Background Jobs mit Log/PID/Exitcode (Cursor Timeout Workaround)

Usage:
  bg_job.sh run <label> -- <command> [args...]
  bg_job.sh follow <label>
  bg_job.sh status <label>
  bg_job.sh stop <label>
  bg_job.sh latest <label>
  bg_job.sh list <label>

Notes:
- Logs/PID/Exitcode landen in <repo>/.logs/
- "stop" versucht zuerst die Prozessgruppe zu beenden (sauber auch bei Child-Prozessen).
USAGE
}

die() { echo "ERROR: $*" >&2; exit 2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${REPO_DIR}/.logs"
JOB_DIR="${LOG_DIR}/jobs"

mkdir -p "${LOG_DIR}" "${JOB_DIR}"

label_ok() {
  [[ "$1" =~ ^[A-Za-z0-9._-]+$ ]]
}

latest_file() {
  local pattern="$1"
  ls -t ${pattern} 2>/dev/null | head -1 || true
}

ensure_label() {
  local label="$1"
  [[ -n "${label}" ]] || die "Missing label"
  label_ok "${label}" || die "Invalid label '${label}' (allowed: A-Za-z0-9._-)"
}

subcmd="${1:-}"
shift || true

case "${subcmd}" in
  run)
    label="${1:-}"; shift || true
    ensure_label "${label}"

    [[ "${1:-}" == "--" ]] || die "Missing '--' delimiter. Example: bg_job.sh run docs_refs_full -- ./scripts/ops/verify_docs_reference_targets.sh"
    shift || true
    [[ $# -ge 1 ]] || die "Missing command after '--'"

    ts="$(date +%Y%m%d_%H%M%S)"
    job="${JOB_DIR}/${label}_${ts}.sh"
    log="${LOG_DIR}/${label}_${ts}.log"
    pidfile="${LOG_DIR}/${label}_${ts}.pid"
    exitfile="${LOG_DIR}/${label}_${ts}.exit"
    metafile="${LOG_DIR}/${label}_${ts}.meta"

    # Determine venv activate (optional)
    venv_activate=""
    if [[ -f "${REPO_DIR}/venv/bin/activate" ]]; then
      venv_activate="${REPO_DIR}/venv/bin/activate"
    elif [[ -f "${REPO_DIR}/.venv/bin/activate" ]]; then
      venv_activate="${REPO_DIR}/.venv/bin/activate"
    fi

    # Choose shell for "login command" behavior where needed
    shell_bin="bash"
    if command -v zsh >/dev/null 2>&1; then
      shell_bin="zsh"
    fi

    # Build exec line with safe quoting
    cmdline="$(printf '%q ' "$@")"

    # Meta
    {
      echo "ts=${ts}"
      echo "label=${label}"
      echo "repo_dir=${REPO_DIR}"
      echo "shell=${shell_bin}"
      echo "venv_activate=${venv_activate:-<none>}"
      echo "cmd=${cmdline}"
      echo "user=$(id -un 2>/dev/null || true)"
      echo "host=$(hostname 2>/dev/null || true)"
      command -v git >/dev/null 2>&1 && echo "git_sha=$(git -C "${REPO_DIR}" rev-parse --short HEAD 2>/dev/null || true)"
      command -v git >/dev/null 2>&1 && echo "git_branch=$(git -C "${REPO_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    } > "${metafile}"

    cat > "${job}" <<BASHJOB
#!/usr/bin/env bash
set -euo pipefail
trap 'ec=\$?; echo "\$ec" > "${exitfile}"; exit "\$ec"' EXIT

export PYTHONUNBUFFERED=1
export GH_PAGER=cat
export GIT_PAGER=cat

cd "${REPO_DIR}"

if [[ -n "${venv_activate}" && -f "${venv_activate}" ]]; then
  # shellcheck disable=SC1090
  source "${venv_activate}"
fi

# Ensure stdout/stderr are flushed quickly for logs
stty -echo 2>/dev/null || true

# Prefer caffeinate on macOS, fallback silently if not available.
if command -v caffeinate >/dev/null 2>&1; then
  # caffeinate runs the command and exits when the command exits
  caffeinate -dimsu ${shell_bin} -lc 'set -e; ${cmdline}'
else
  ${shell_bin} -lc 'set -e; ${cmdline}'
fi
BASHJOB

    chmod +x "${job}"

    # Start detached; record PID; compute PGID for "stop"
    nohup bash "${job}" > "${log}" 2>&1 & pid=$!
    echo "${pid}" > "${pidfile}"

    pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ' || true)"
    [[ -n "${pgid}" ]] && echo "pgid=${pgid}" >> "${metafile}"

    echo "Started: label=${label}"
    echo "  PID:  ${pid}"
    [[ -n "${pgid}" ]] && echo "  PGID: ${pgid}"
    echo "  Log:  ${log}"
    echo "  Meta: ${metafile}"
    echo "Follow: bash scripts/ops/bg_job.sh follow ${label}"
    echo "Stop:   bash scripts/ops/bg_job.sh stop ${label}"
    ;;

  follow)
    label="${1:-}"; shift || true
    ensure_label "${label}"
    log="$(latest_file "${LOG_DIR}/${label}_*.log")"
    [[ -n "${log}" ]] || die "No log found for label=${label} in ${LOG_DIR}"
    tail -f "${log}"
    ;;

  latest)
    label="${1:-}"; shift || true
    ensure_label "${label}"
    log="$(latest_file "${LOG_DIR}/${label}_*.log")"
    [[ -n "${log}" ]] || die "No log found for label=${label} in ${LOG_DIR}"
    echo "${log}"
    ;;

  list)
    label="${1:-}"; shift || true
    ensure_label "${label}"
    ls -lt "${LOG_DIR}/${label}_"*.log 2>/dev/null || die "No logs found for label=${label}"
    ;;

  status)
    label="${1:-}"; shift || true
    ensure_label "${label}"
    pidf="$(latest_file "${LOG_DIR}/${label}_*.pid")"
    [[ -n "${pidf}" ]] || die "No pid file found for label=${label}"
    pid="$(cat "${pidf}")"

    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "RUNNING label=${label} pid=${pid}"
    else
      echo "NOT RUNNING label=${label} pid=${pid}"
    fi

    exitf="$(latest_file "${LOG_DIR}/${label}_*.exit")"
    if [[ -n "${exitf}" ]]; then
      echo "EXITCODE $(cat "${exitf}") (file: ${exitf})"
    else
      echo "EXITCODE <unknown yet> (no .exit file found)"
    fi
    ;;

  stop)
    label="${1:-}"; shift || true
    ensure_label "${label}"
    pidf="$(latest_file "${LOG_DIR}/${label}_*.pid")"
    [[ -n "${pidf}" ]] || die "No pid file found for label=${label}"
    pid="$(cat "${pidf}")"

    metaf="$(latest_file "${LOG_DIR}/${label}_*.meta")"
    pgid=""
    if [[ -n "${metaf}" ]]; then
      pgid="$(grep -E '^pgid=' "${metaf}" | tail -1 | cut -d= -f2- || true)"
    fi
    if [[ -z "${pgid}" ]]; then
      pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ' || true)"
    fi

    if [[ -n "${pgid}" ]]; then
      echo "Stopping process group: PGID=${pgid} (label=${label})"
      kill -TERM -"${pgid}" 2>/dev/null || true
    else
      echo "Stopping pid: PID=${pid} (label=${label})"
      kill -TERM "${pid}" 2>/dev/null || true
    fi
    ;;

  ""|-h|--help|help)
    usage
    ;;
  *)
    usage
    die "Unknown subcommand: ${subcmd}"
    ;;
esac
