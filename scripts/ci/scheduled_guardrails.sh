#!/usr/bin/env bash
set -euo pipefail

req_var() {
  local k="$1"
  local v="${2:-}"
  if [ -z "${v}" ]; then
    echo "MISSING_REQUIRED_VAR=${k}" >&2
    return 1
  fi
}

req_secret() {
  local k="$1"
  local v="${2:-}"
  if [ -z "${v}" ]; then
    echo "MISSING_REQUIRED_SECRET=${k}" >&2
    return 1
  fi
}

echo "GUARDRAILS: start"
echo "UTC_NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "RUNNER_OS=${RUNNER_OS:-}"
echo "PYTHON_VERSION=$(python -V 2>/dev/null || true)"
python -c "import sys; print('PY', sys.version)" || true

echo "GUARDRAILS: required schedule vars"
req_var "PT_SCHEDULED_PAPER_TESTS_ENABLED" "${PT_SCHEDULED_PAPER_TESTS_ENABLED:-}"
req_var "PT_SCHEDULED_EXPORT_VERIFY_ENABLED" "${PT_SCHEDULED_EXPORT_VERIFY_ENABLED:-}"

echo "GUARDRAILS: export channel secrets (only required when export verify is enabled)"
if [ "${PT_SCHEDULED_EXPORT_VERIFY_ENABLED:-}" = "true" ] || [ "${PT_SCHEDULED_EXPORT_VERIFY_ENABLED:-}" = "1" ]; then
  req_secret "PT_RCLONE_CONF_B64" "${PT_RCLONE_CONF_B64:-}"
  req_secret "PT_EXPORT_REMOTE" "${PT_EXPORT_REMOTE:-}"
  req_secret "PT_EXPORT_PREFIX" "${PT_EXPORT_PREFIX:-}"
fi

echo "GUARDRAILS: ok"
