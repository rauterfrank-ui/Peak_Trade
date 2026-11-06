#!/usr/bin/env bash
set -euo pipefail

# Knowledge DB Smoke Runner with Auto-Restart
# ============================================
# This version automatically starts/stops the server for each mode test.

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
PORT="${PORT:-8000}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Knowledge DB Smoke Runner (Auto-Restart)"
echo "BASE_URL: ${BASE_URL}"
echo "PROJECT_ROOT: ${PROJECT_ROOT}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

http_code() {
  curl -s -o /dev/null -w "%{http_code}" "$@"
}

expect() {
  local label="$1"
  local got="$2"
  local want="$3"
  if [[ "$got" != "$want" ]]; then
    echo "❌ FAIL: $label (got $got, want $want)"
    return 1
  fi
  echo "✅ OK:   $label ($got)"
}

start_server() {
  local ro="$1"
  local web_write="$2"

  echo "   🚀 Starting server with READONLY=${ro}, WEB_WRITE=${web_write}..."

  cd "${PROJECT_ROOT}"
  KNOWLEDGE_READONLY="${ro}" \
  KNOWLEDGE_WEB_WRITE_ENABLED="${web_write}" \
  uv run uvicorn src.webui.app:app --host 127.0.0.1 --port "${PORT}" \
    > /tmp/knowledge_smoke_server.log 2>&1 &

  SERVER_PID=$!
  echo "   Server PID: ${SERVER_PID}"

  # Wait for server to be ready
  for i in {1..30}; do
    if curl -s -f "${BASE_URL}/api/health" > /dev/null 2>&1; then
      echo "   ✓ Server ready after ${i}s"
      return 0
    fi
    sleep 1
  done

  echo "   ❌ Server failed to start after 30s"
  cat /tmp/knowledge_smoke_server.log
  return 1
}

stop_server() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    echo "   🛑 Stopping server (PID ${SERVER_PID})..."
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
    sleep 1
  fi
}

post_snippet() {
  http_code -X POST "${BASE_URL}/api/knowledge/snippets" \
    -H "Content-Type: application/json" \
    -d '{"category":"insight","title":"smoke","content":"c","tags":["x"]}'
}

get_snippets() {
  http_code "${BASE_URL}/api/knowledge/snippets?limit=1"
}

post_strategy() {
  http_code -X POST "${BASE_URL}/api/knowledge/strategies" \
    -H "Content-Type: application/json" \
    -d '{"name":"smoke_strat","description":"Smoke test strategy","status":"rd","tier":"experimental"}'
}

get_strategies() {
  http_code "${BASE_URL}/api/knowledge/strategies?limit=1"
}

get_search() {
  http_code "${BASE_URL}/api/knowledge/search?q=test&k=3"
}

run_mode() {
  local mode="$1"
  local ro="$2"
  local web_write="$3"

  echo ""
  echo "───────────────────────────────────────────────────────"
  echo "▶ MODE: ${mode}"
  echo "   KNOWLEDGE_READONLY=${ro}"
  echo "   KNOWLEDGE_WEB_WRITE_ENABLED=${web_write}"
  echo "───────────────────────────────────────────────────────"

  # Start server with specific config
  start_server "${ro}" "${web_write}" || return 1

  # Give server a moment to fully initialize
  sleep 2

  # GET always expected 200
  expect "${mode}: GET snippets"    "$(get_snippets)"    "200"
  expect "${mode}: GET strategies"  "$(get_strategies)"  "200"

  # Search: allowed to be 200 or 501 (graceful degrade), but never 500
  local sc
  sc="$(get_search)"
  if [[ "$sc" == "200" || "$sc" == "501" ]]; then
    echo "✅ OK:   ${mode}: GET search ($sc)"
  else
    echo "❌ FAIL: ${mode}: GET search (got $sc, want 200 or 501)"
    stop_server
    return 1
  fi

  # POST expectations per mode
  if [[ "${mode}" == "Production" ]]; then
    expect "${mode}: POST snippets"   "$(post_snippet)"   "403"
    expect "${mode}: POST strategies" "$(post_strategy)"  "403"
  elif [[ "${mode}" == "Development" ]]; then
    expect "${mode}: POST snippets"   "$(post_snippet)"   "201"
    local ps
    ps="$(post_strategy)"
    if [[ "$ps" == "200" || "$ps" == "201" ]]; then
      echo "✅ OK:   ${mode}: POST strategies ($ps)"
    else
      echo "❌ FAIL: ${mode}: POST strategies (got $ps, want 200 or 201)"
      stop_server
      return 1
    fi
  elif [[ "${mode}" == "Research" ]]; then
    expect "${mode}: POST snippets"   "$(post_snippet)"   "403"
    expect "${mode}: POST strategies" "$(post_strategy)"  "403"
  fi

  # Stop server for next mode
  stop_server
}

# Cleanup on exit
trap stop_server EXIT INT TERM

# Run the 3 official configs
run_mode "Production"   "true"  "false"
run_mode "Development"  "false" "true"
run_mode "Research"     "false" "false"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All smoke checks passed."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
