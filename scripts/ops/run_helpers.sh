#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – Ops Bash Helpers (strict/robust run semantics)
#
# Usage (in other bash scripts):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   # shellcheck source=run_helpers.sh
#   source "${SCRIPT_DIR}/run_helpers.sh"
#
# Modes:
#   PT_MODE=strict|robust   (or MODE=strict|robust)
#     - strict: failures in pt_run() abort
#     - robust: failures in pt_run() warn and continue
#
# Explicit variants:
#   pt_run_required(): always aborts on failure
#   pt_run_optional(): never aborts on failure (warn only)
# ─────────────────────────────────────────────────────────────

# Guard: allow sourcing only
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "This file is meant to be sourced from other scripts." >&2
  echo "Example: source scripts/ops/run_helpers.sh" >&2
  exit 2
fi

pt_mode() {
  local m="${PT_MODE:-${MODE:-strict}}"
  case "$m" in
    strict|robust) echo "$m" ;;
    *)
      echo "strict"
      ;;
  esac
}

pt_ts() {
  date +"%Y-%m-%d %H:%M:%S"
}

pt_log() {
  echo "[$(pt_ts)] $*"
}

pt_warn() {
  echo "[$(pt_ts)] ⚠️  $*" >&2
}

pt_die() {
  echo "[$(pt_ts)] ❌ $*" >&2
  # If interactive shell, don't kill the whole terminal; otherwise exit hard.
  if [[ $- == *i* ]]; then
    return 1
  fi
  exit 1
}

pt_section() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$*"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

pt_require_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    return 0
  fi

  if [[ "$(pt_mode)" == "robust" ]]; then
    pt_warn "Missing command: ${cmd} (PT_MODE=robust → continuing)"
    return 0
  fi

  pt_die "Missing required command: ${cmd}"
}

pt_run() {
  # Controlled by PT_MODE/MODE:
  # - strict: fail → abort
  # - robust: fail → warn and continue
  local label="$1"; shift

  pt_log "▶ ${label}: $*"
  if "$@"; then
    pt_log "✔ ${label}"
    return 0
  fi

  local ec=$?
  if [[ "$(pt_mode)" == "robust" ]]; then
    pt_warn "✖ ${label} (exit ${ec}) — continuing (PT_MODE=robust)"
    return 0
  fi

  pt_die "✖ ${label} (exit ${ec})"
}

pt_run_required() {
  # Always abort on failure (even in robust mode)
  local label="$1"; shift

  pt_log "▶ ${label}: $*"
  if "$@"; then
    pt_log "✔ ${label}"
    return 0
  fi

  local ec=$?
  pt_die "✖ ${label} (exit ${ec})"
}

pt_run_optional() {
  # Never abort on failure (even in strict mode)
  local label="$1"; shift

  pt_log "▶ (optional) ${label}: $*"
  if "$@"; then
    pt_log "✔ (optional) ${label}"
    return 0
  fi

  local ec=$?
  pt_warn "✖ (optional) ${label} (exit ${ec}) — continuing"
  return 0
}
