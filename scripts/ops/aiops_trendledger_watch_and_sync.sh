#!/usr/bin/env bash
# Usage: PR_NUM=1344 ./scripts/ops/aiops_trendledger_watch_and_sync.sh
#    or: ./scripts/ops/aiops_trendledger_watch_and_sync.sh 1344
#    or: ./scripts/ops/aiops_trendledger_watch_and_sync.sh 1344 --bg  (background, non-blocking)
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

PR_NUM="${PR_NUM:-${1:-}}"
BG="${2:-}"

if [[ -z "${PR_NUM}" ]]; then
  echo "Usage: PR_NUM=1344 $0"
  echo "   or: $0 1344"
  echo "   or: $0 1344 --bg   (background watch, non-blocking)"
  echo "SET PR_NUM first, e.g.:  PR_NUM=1344"
  exit 1
fi

LOG="/tmp/aiops_trendledger_pr${PR_NUM}_watch.log"

if [[ "${BG}" == "--bg" ]]; then
  # [AGENT:watcher] background watch (non-blocking)
  touch "${LOG}"
  nohup ./scripts/ops/aiops_trendledger_pr_watch.sh "${PR_NUM}" >> "${LOG}" 2>&1 &
  PID=$!
  PIDFILE="/tmp/aiops_trendledger_pr${PR_NUM}_watch.pid"
  echo "${PID}" > "${PIDFILE}"
  echo "BG: watcher started (PID=${PID}). Log: ${LOG}"
  echo "BG: follow with: tail -f \"${LOG}\""
  echo "BG: stop with: ./scripts/ops/aiops_trendledger_watch_and_sync_stop.sh \"${PIDFILE}\""
  exit 0
fi

# [AGENT:watcher] foreground watch (non-fatal)
./scripts/ops/aiops_trendledger_pr_watch.sh "${PR_NUM}" && RC=0 || RC=$?

# [AGENT:closer] after MERGED
if [[ "${RC:-1}" -eq 0 ]]; then
  echo "MERGED. Syncing main..."
  git checkout main
  git fetch origin --prune
  git pull --ff-only origin main
  git log -n 3 --oneline --decorate
else
  echo "Not merged yet. To watch in background: $0 ${PR_NUM} --bg"
fi
