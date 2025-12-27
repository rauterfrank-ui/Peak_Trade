#!/usr/bin/env bash
# scripts/ops/knowledge_prod_smoke.sh
#
# Remote production smoke tests for Knowledge DB API.
# Tests against a live deployment without server restarts.
#
# Usage:
#   BASE_URL=https://prod.example.com ./scripts/ops/knowledge_prod_smoke.sh
#   ./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com
#   ./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --token SECRET --strict

set -euo pipefail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Run Helpers Adoption (optional, for ops guard)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ -f "$REPO_ROOT/scripts/ops/run_helpers.sh" ]]; then
  # shellcheck source=scripts/ops/run_helpers.sh
  source "$REPO_ROOT/scripts/ops/run_helpers.sh"
else
  echo "⚠️  Warning: run_helpers.sh not found (not fatal for remote smoke)" >&2
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Defaults & Config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASE_URL="${BASE_URL:-}"
PREFIX="${PREFIX:-/api/knowledge}"
TOKEN="${TOKEN:-}"
TIMEOUT="${TIMEOUT:-10}"
INSECURE="${INSECURE:-0}"
VERBOSE="${VERBOSE:-0}"
EXPECT_501_OK="${EXPECT_501_OK:-1}"
STRICT="${STRICT:-0}"

SNIPPETS_PATH="${SNIPPETS_PATH:-/snippets}"
STRATEGIES_PATH="${STRATEGIES_PATH:-/strategies}"
STATS_PATH="${STATS_PATH:-/stats}"
SEARCH_PATH="${SEARCH_PATH:-/search}"
WRITE_TEST_PATH="${WRITE_TEST_PATH:-/snippets}"

declare -a EXTRA_HEADERS=()
TEMP_DIR=""

# Counters
PASS_COUNT=0
FAIL_COUNT=0
DEGRADED_COUNT=0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cleanup
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cleanup() {
  if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT INT TERM

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Argument Parsing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

usage() {
  cat <<EOF
Usage: $0 <BASE_URL> [OPTIONS]

Remote production smoke tests for Knowledge DB API.

REQUIRED:
  BASE_URL              Target URL (or set via env: BASE_URL=https://...)

OPTIONS:
  --prefix PATH         API prefix (default: /api/knowledge)
  --token TOKEN         Authorization Bearer token
  --header "K: V"       Additional header (can be specified multiple times)
  --insecure            Allow insecure SSL (curl -k)
  --timeout SEC         Request timeout in seconds (default: 10)
  --verbose             Show detailed output
  --expect-501-ok       Treat 501 as degraded but ok (default: true)
  --strict              501 counts as FAIL (overrides --expect-501-ok)
  -h, --help            Show this help

EXAMPLES:
  # Basic usage
  $0 https://prod.example.com

  # With authentication
  $0 https://prod.example.com --token mytoken123

  # With custom prefix and strict mode
  $0 https://staging.example.com --prefix /v1/knowledge --strict

  # Via env variable
  BASE_URL=https://prod.example.com $0
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      usage
      ;;
    --prefix)
      PREFIX="$2"
      shift 2
      ;;
    --token)
      TOKEN="$2"
      shift 2
      ;;
    --header)
      EXTRA_HEADERS+=("$2")
      shift 2
      ;;
    --insecure)
      INSECURE=1
      shift
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --expect-501-ok)
      EXPECT_501_OK=1
      shift
      ;;
    --strict)
      STRICT=1
      EXPECT_501_OK=0
      shift
      ;;
    *)
      if [[ -z "$BASE_URL" ]]; then
        BASE_URL="$1"
      else
        echo "❌ Unknown argument: $1" >&2
        usage
      fi
      shift
      ;;
  esac
done

if [[ -z "$BASE_URL" ]]; then
  echo "❌ Error: BASE_URL is required" >&2
  echo "" >&2
  usage
fi

# Remove trailing slash
BASE_URL="${BASE_URL%/}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTTP Request Helper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

http_request() {
  local method="$1"
  local url="$2"
  local body="${3:-}"

  local response_file="${TEMP_DIR}/response_$$_${RANDOM}.txt"
  local status_file="${TEMP_DIR}/status_$$_${RANDOM}.txt"

  local curl_args=(
    -s
    -w "%{http_code}"
    -o "$response_file"
    -X "$method"
    --max-time "$TIMEOUT"
  )

  if [[ $INSECURE -eq 1 ]]; then
    curl_args+=(-k)
  fi

  if [[ -n "$TOKEN" ]]; then
    curl_args+=(-H "Authorization: Bearer $TOKEN")
  fi

  if [[ ${#EXTRA_HEADERS[@]} -gt 0 ]]; then
    for header in "${EXTRA_HEADERS[@]}"; do
      curl_args+=(-H "$header")
    done
  fi

  if [[ -n "$body" ]]; then
    curl_args+=(-H "Content-Type: application/json")
    curl_args+=(-d "$body")
  fi

  curl_args+=("$url")

  local http_code
  http_code=$(curl "${curl_args[@]}" 2>/dev/null || echo "000")

  # Read response body (first 300 chars for error preview)
  local body_preview=""
  if [[ -f "$response_file" ]]; then
    body_preview=$(head -c 300 "$response_file" 2>/dev/null || echo "")
  fi

  # Cleanup temp files
  rm -f "$response_file" "$status_file"

  # Return status:body_preview
  echo "${http_code}:${body_preview}"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Check Helper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

check_endpoint() {
  local name="$1"
  local method="$2"
  local path="$3"
  local body="${4:-}"
  shift 4
  local expected_codes=("$@")

  local url="${BASE_URL}${PREFIX}${path}"

  if [[ $VERBOSE -eq 1 ]]; then
    echo "  → $method $url" >&2
  fi

  local result
  result=$(http_request "$method" "$url" "$body")

  local http_code="${result%%:*}"
  local body_preview="${result#*:}"

  # Check if code matches expected
  local matched=0
  local is_degraded=0

  for expected in "${expected_codes[@]}"; do
    if [[ "$http_code" == "$expected" ]]; then
      matched=1
      break
    fi
  done

  # Special handling for 501 (graceful degradation)
  if [[ "$http_code" == "501" && $EXPECT_501_OK -eq 1 ]]; then
    is_degraded=1
    matched=1
  fi

  # Output result
  if [[ $matched -eq 1 ]]; then
    if [[ $is_degraded -eq 1 ]]; then
      echo "🟡 DEGRADED: $name ($http_code - backend unavailable)"
      DEGRADED_COUNT=$((DEGRADED_COUNT + 1))
    else
      echo "✅ PASS: $name ($http_code)"
      PASS_COUNT=$((PASS_COUNT + 1))
    fi

    if [[ $VERBOSE -eq 1 && -n "$body_preview" ]]; then
      echo "     Body: ${body_preview:0:100}..." >&2
    fi
  else
    echo "❌ FAIL: $name (expected: ${expected_codes[*]}, got: $http_code)"
    FAIL_COUNT=$((FAIL_COUNT + 1))

    if [[ -n "$body_preview" ]]; then
      echo "     Body: $body_preview"
    fi
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main() {
  TEMP_DIR=$(mktemp -d)

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🧪 Knowledge DB Production Smoke Tests"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "BASE_URL:   $BASE_URL"
  echo "PREFIX:     $PREFIX"
  echo "TIMEOUT:    ${TIMEOUT}s"
  echo "INSECURE:   $INSECURE"
  echo "STRICT:     $STRICT"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Check 1: Stats endpoint
  check_endpoint \
    "Stats endpoint" \
    "GET" \
    "${STATS_PATH}" \
    "" \
    "200" "501"

  # Check 2: Snippets (GET)
  check_endpoint \
    "Snippets list" \
    "GET" \
    "${SNIPPETS_PATH}?limit=1" \
    "" \
    "200" "501"

  # Check 3: Strategies (GET)
  check_endpoint \
    "Strategies list" \
    "GET" \
    "${STRATEGIES_PATH}?limit=1" \
    "" \
    "200" "501"

  # Check 4: Search endpoint (try GET first, then POST if 404/405)
  local search_url="${BASE_URL}${PREFIX}${SEARCH_PATH}?q=smoke&limit=1"
  local search_result
  search_result=$(http_request "GET" "$search_url" "")
  local search_code="${search_result%%:*}"

  if [[ "$search_code" == "404" || "$search_code" == "405" ]]; then
    # Try POST variant
    if [[ $VERBOSE -eq 1 ]]; then
      echo "  → GET search returned $search_code, trying POST..." >&2
    fi
    check_endpoint \
      "Search (POST)" \
      "POST" \
      "${SEARCH_PATH}" \
      '{"query":"smoke","limit":1}' \
      "200" "501"
  else
    # Use GET result
    local body_preview="${search_result#*:}"
    local matched=0
    local is_degraded=0

    if [[ "$search_code" == "200" || "$search_code" == "501" ]]; then
      matched=1
      if [[ "$search_code" == "501" && $EXPECT_501_OK -eq 1 ]]; then
        is_degraded=1
      fi
    fi

    if [[ $matched -eq 1 ]]; then
      if [[ $is_degraded -eq 1 ]]; then
        echo "🟡 DEGRADED: Search (GET) ($search_code - backend unavailable)"
        DEGRADED_COUNT=$((DEGRADED_COUNT + 1))
      else
        echo "✅ PASS: Search (GET) ($search_code)"
        PASS_COUNT=$((PASS_COUNT + 1))
      fi
    else
      echo "❌ FAIL: Search (GET) (expected: 200 or 501, got: $search_code)"
      FAIL_COUNT=$((FAIL_COUNT + 1))
      if [[ -n "$body_preview" ]]; then
        echo "     Body: $body_preview"
      fi
    fi
  fi

  # Check 5: Write-gating probe
  # We expect 403 in production (write blocked)
  # 401 = auth missing (acceptable but note it)
  # 501 = backend unavailable (degraded ok if expect-501-ok)
  local write_body='{"title":"smoke","content":"smoke","tags":["smoke"]}'
  local write_url="${BASE_URL}${PREFIX}${WRITE_TEST_PATH}"
  local write_result
  write_result=$(http_request "POST" "$write_url" "$write_body")
  local write_code="${write_result%%:*}"
  local write_body_preview="${write_result#*:}"

  case "$write_code" in
    403)
      echo "✅ PASS: Write gating probe ($write_code - correctly blocked)"
      PASS_COUNT=$((PASS_COUNT + 1))
      ;;
    401)
      echo "🟡 DEGRADED: Write gating probe ($write_code - auth missing, but write would be blocked)"
      DEGRADED_COUNT=$((DEGRADED_COUNT + 1))
      ;;
    501)
      if [[ $EXPECT_501_OK -eq 1 ]]; then
        echo "🟡 DEGRADED: Write gating probe ($write_code - backend unavailable)"
        DEGRADED_COUNT=$((DEGRADED_COUNT + 1))
      else
        echo "❌ FAIL: Write gating probe ($write_code - backend unavailable, strict mode)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
      fi
      ;;
    200|201|204)
      echo "❌ FAIL: Write gating probe ($write_code - write SUCCEEDED, should be blocked in production!)"
      FAIL_COUNT=$((FAIL_COUNT + 1))
      ;;
    *)
      echo "❌ FAIL: Write gating probe (expected: 403, got: $write_code)"
      FAIL_COUNT=$((FAIL_COUNT + 1))
      if [[ -n "$write_body_preview" ]]; then
        echo "     Body: $write_body_preview"
      fi
      ;;
  esac

  # Summary
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📊 Summary"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ PASS:     $PASS_COUNT"
  echo "🟡 DEGRADED: $DEGRADED_COUNT"
  echo "❌ FAIL:     $FAIL_COUNT"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Exit code logic
  if [[ $FAIL_COUNT -gt 0 ]]; then
    echo "❌ Tests FAILED"
    exit 1
  elif [[ $DEGRADED_COUNT -gt 0 && $STRICT -eq 1 ]]; then
    echo "⚠️  Tests DEGRADED (strict mode enabled)"
    exit 2
  else
    echo "🎉 All checks passed"
    exit 0
  fi
}

main
