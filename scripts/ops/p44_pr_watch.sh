#!/usr/bin/env bash
set -euo pipefail
# Usage: ./scripts/ops/<pNN>_pr_watch.sh <PR_NUM> [--bg]
PR="${1:-}"
MODE="${2:-}"
test -n "${PR}" || { echo "missing PR number" >&2; exit 2; }
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/pr${PR}_watch_${TS}"
mkdir -p "${EVI}"
LOG="/tmp/pr${PR}_watch.log"
PID="/tmp/pr${PR}_watch.pid"
touch "${LOG}"

poll() {
  STATE="$(gh pr view "${PR}" --json state,mergedAt --jq '.state + "|" + (.mergedAt // "")' 2>/dev/null || echo "ERR|")"
  printf "%s %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${STATE}" | tee -a "${LOG}" >/dev/null
  echo "${STATE}"
}

run_watch() {
  for i in $(seq 1 240); do
    OUT="$(poll)"
    if printf "%s" "${OUT}" | grep -q '^MERGED|'; then
      gh pr view "${PR}" --json number,title,state,url,mergeCommit,mergedAt,headRefName,baseRefName,mergeable,mergeStateStatus > "${EVI}/PR_VIEW.json" 2>/dev/null || true
      (gh pr checks "${PR}" 2>/dev/null || true) > "${EVI}/PR_CHECKS.txt"
      git status -sb > "${EVI}/STATUS.txt" 2>/dev/null || true
      git rev-parse HEAD > "${EVI}/HEAD.txt" 2>/dev/null || true
      git log -n 5 --oneline --decorate > "${EVI}/LOG5.txt" 2>/dev/null || true
      shasum -a 256 "${EVI}"/* > "${EVI}/SHA256SUMS.txt" 2>/dev/null || true
      echo "WATCH_OK pr=${PR} evidence_dir=${EVI}" | tee -a "${LOG}" >/dev/null
      return 0
    fi
    sleep 15
  done
  echo "WATCH_TIMEOUT pr=${PR} log=${LOG}" | tee -a "${LOG}" >/dev/null
  return 3
}

if [[ "${MODE}" == "--bg" ]]; then
  (run_watch) &
  echo $! > "${PID}"
  echo "WATCH_BG_OK pid=$(cat "${PID}") log=${LOG}"
  exit 0
fi

run_watch
