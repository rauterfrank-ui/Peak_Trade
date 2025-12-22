#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Knowledge DB Smoke Runner"
echo "BASE_URL: ${BASE_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

http_code() {
  # Usage: http_code <curl args...>
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
  echo "   export KNOWLEDGE_READONLY=${ro}"
  echo "   export KNOWLEDGE_WEB_WRITE_ENABLED=${web_write}"
  echo "───────────────────────────────────────────────────────"

  export KNOWLEDGE_READONLY="${ro}"
  export KNOWLEDGE_WEB_WRITE_ENABLED="${web_write}"

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
    return 1
  fi

  # POST expectations per mode
  if [[ "${mode}" == "Production" ]]; then
    expect "${mode}: POST snippets"   "$(post_snippet)"   "403"
    expect "${mode}: POST strategies" "$(post_strategy)"  "403"
  elif [[ "${mode}" == "Development" ]]; then
    expect "${mode}: POST snippets"   "$(post_snippet)"   "201"
    # Some implementations return 200; accept 200/201
    local ps
    ps="$(post_strategy)"
    if [[ "$ps" == "200" || "$ps" == "201" ]]; then
      echo "✅ OK:   ${mode}: POST strategies ($ps)"
    else
      echo "❌ FAIL: ${mode}: POST strategies (got $ps, want 200 or 201)"
      return 1
    fi
  elif [[ "${mode}" == "Research" ]]; then
    expect "${mode}: POST snippets"   "$(post_snippet)"   "403"
    expect "${mode}: POST strategies" "$(post_strategy)"  "403"
  fi
}

# Run the 3 official configs
run_mode "Production"   "true"  "false"
run_mode "Development"  "false" "true"
run_mode "Research"     "false" "false"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All smoke checks passed."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
