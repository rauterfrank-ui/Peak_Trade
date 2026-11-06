#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Peak_Trade — Knowledge Production Deployment Drill (End-to-End)
# - CI watch -> merge PR -> sync main
# - Local demo: start uvicorn -> run knowledge_prod_smoke.sh -> cleanup
# - Optional: run against STAGING_URL / PROD_URL
# ─────────────────────────────────────────────────────────────

cd ~/Peak_Trade

# === CONFIG ===================================================
PR_NUMBER="${PR_NUMBER:-245}"

# Local demo settings
LOCAL_PORT="${LOCAL_PORT:-8000}"
LOCAL_URL="http://127.0.0.1:${LOCAL_PORT}"
LOCAL_VERBOSE="${LOCAL_VERBOSE:-1}"   # 1=verbose, 0=quiet

# Optional remote targets (set these env vars if you want remote runs)
STAGING_URL="${STAGING_URL:-}"        # e.g. https://staging.example.com
STAGING_TOKEN="${STAGING_TOKEN:-}"    # optional bearer token

PROD_URL="${PROD_URL:-}"              # e.g. https://prod.example.com
PROD_TOKEN="${PROD_TOKEN:-}"          # optional bearer token
PROD_STRICT="${PROD_STRICT:-0}"       # 1=strict (501 => FAIL), 0=degraded ok

# Merge control
DO_MERGE="${DO_MERGE:-1}"             # 1=watch+merge PR, 0=skip merge steps

# === HELPERS ==================================================
hr() { echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }
say() { echo "▶️ $*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "❌ Missing command: $1"; exit 1; }
}

run_smoke() {
  local url="$1"
  local token="$2"
  local strict="$3"
  local verbose="$4"

  local args=()
  if [[ -n "$token" ]]; then
    args+=(--token "$token")
  fi
  if [[ "$strict" == "1" ]]; then
    args+=(--strict)
  fi
  if [[ "$verbose" == "1" ]]; then
    args+=(--verbose)
  fi

  say "Running: ./scripts/ops/knowledge_prod_smoke.sh \"$url\" ${args[*]:-}"
  ./scripts/ops/knowledge_prod_smoke.sh "$url" "${args[@]}"
}

# === PREFLIGHT =================================================
hr
say "Preflight"
need_cmd git
need_cmd gh
need_cmd uv

if [[ ! -f scripts/ops/knowledge_prod_smoke.sh ]]; then
  echo "❌ scripts/ops/knowledge_prod_smoke.sh not found. Did you pull main after merge?"
  exit 1
fi

# === 1) CI WATCH + MERGE ======================================
if [[ "$DO_MERGE" == "1" ]]; then
  hr
  say "CI watch: PR #${PR_NUMBER}"
  gh pr checks "$PR_NUMBER" --watch

  hr
  say "Merge (squash) + delete branch: PR #${PR_NUMBER}"
  gh pr merge "$PR_NUMBER" --squash --delete-branch

  hr
  say "Sync main"
  git checkout main
  git pull --ff-only
else
  hr
  say "Skipping merge steps (DO_MERGE=0). Ensuring main is up-to-date."
  git checkout main
  git pull --ff-only
fi

# === 2) LOCAL DEMO DRILL ======================================
hr
say "Local demo drill on ${LOCAL_URL}"
say "Start uvicorn -> run smoke -> cleanup"

uv run uvicorn src.webui.app:app --port "${LOCAL_PORT}" >/tmp/knowledge_uvicorn.log 2>&1 &
PID=$!

cleanup() {
  hr
  say "Cleanup: stopping uvicorn (PID=${PID})"
  kill "${PID}" >/dev/null 2>&1 || true
  say "Local server logs: /tmp/knowledge_uvicorn.log"
}
trap cleanup EXIT

sleep 3

# Safety note:
# - Write-gating probe should be 403 (or 401 if auth required).
# - If it ever returns 2xx, STOP and investigate gating/config.
run_smoke "${LOCAL_URL}" "" "0" "${LOCAL_VERBOSE}"

# === 3) OPTIONAL: STAGING =====================================
if [[ -n "$STAGING_URL" ]]; then
  hr
  say "Staging drill on ${STAGING_URL}"
  run_smoke "${STAGING_URL}" "${STAGING_TOKEN}" "0" "1"
else
  hr
  say "Staging drill skipped (set STAGING_URL to enable)."
fi

# === 4) OPTIONAL: PROD ========================================
if [[ -n "$PROD_URL" ]]; then
  hr
  say "Production drill on ${PROD_URL} (PROD_STRICT=${PROD_STRICT})"
  run_smoke "${PROD_URL}" "${PROD_TOKEN}" "${PROD_STRICT}" "1"
else
  hr
  say "Production drill skipped (set PROD_URL to enable)."
fi

# === DONE ======================================================
hr
echo "✅ End-to-end drill completed."
echo "   - Local:   ${LOCAL_URL}"
echo "   - Staging: ${STAGING_URL:-<skipped>}"
echo "   - Prod:    ${PROD_URL:-<skipped>}"
