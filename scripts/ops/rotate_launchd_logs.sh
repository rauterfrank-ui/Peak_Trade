#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/out/ops/launchd"
MAX_BYTES="${MAX_BYTES:-10485760}"  # 10MB
KEEP="${KEEP:-5}"

mkdir -p "${LOG_DIR}"

rotate_one() {
  local f="$1"
  if [ ! -f "${f}" ]; then
    return 0
  fi
  local size
  size="$(wc -c < "${f}" | tr -d ' ')"
  if [ "${size}" -lt "${MAX_BYTES}" ]; then
    return 0
  fi

  local ts
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  mv "${f}" "${f}.${ts}"
  : > "${f}"

  ls -1t "${f}."* 2>/dev/null | tail -n +"$((KEEP+1))" | xargs -I{} rm -f "{}" || true
}

rotate_one "${LOG_DIR}/operator_all.stdout.log"
rotate_one "${LOG_DIR}/operator_all.stderr.log"
