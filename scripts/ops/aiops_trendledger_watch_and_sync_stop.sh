#!/usr/bin/env bash
set -euo pipefail

PIDFILE="${1:-}"
if [[ -z "${PIDFILE}" ]]; then
  echo "Usage: $0 <pidfile>"
  echo "Example: $0 /tmp/aiops_trendledger_pr1344_watch.pid"
  exit 2
fi

if [[ ! -f "${PIDFILE}" ]]; then
  echo "PIDFILE not found: ${PIDFILE}"
  exit 1
fi

PID="$(cat "${PIDFILE}" | tr -d '[:space:]')"
if [[ -z "${PID}" ]]; then
  echo "Empty PID in ${PIDFILE}"
  exit 1
fi

if kill -0 "${PID}" 2>/dev/null; then
  kill "${PID}"
  echo "Stopped watcher PID=${PID} (pidfile=${PIDFILE})"
else
  echo "Watcher not running (PID=${PID})"
fi
