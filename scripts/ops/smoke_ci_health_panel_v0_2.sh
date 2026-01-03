#!/usr/bin/env bash
# scripts/ops/smoke_ci_health_panel_v0_2.sh
#
# Smoke test for CI & Governance Health Panel v0.2
# - Validates snapshot file paths and structure
# - Tests API endpoints (wenn WebUI läuft)
# - Prüft dass Features erreichbar sind
#
# Usage:
#   ./scripts/ops/smoke_ci_health_panel_v0_2.sh [--skip-api]
#
# Exit Codes:
#   0 = All checks passed
#   1 = One or more checks failed
#   2 = Warnings (degraded but non-critical)
#
# Environment:
#   WEBUI_BASE_URL  — Base URL for WebUI (default: http://127.0.0.1:8000)
#   SKIP_API_CHECK  — Set to "1" to skip API endpoint tests
#
# Requirements:
#   - jq (for JSON validation)
#   - curl (for API tests, optional)

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEBUI_BASE_URL="${WEBUI_BASE_URL:-http://127.0.0.1:8000}"
SKIP_API_CHECK="${SKIP_API_CHECK:-0}"

# Snapshot paths
SNAPSHOT_DIR="$REPO_ROOT/reports/ops"
SNAPSHOT_JSON="$SNAPSHOT_DIR/ci_health_latest.json"
SNAPSHOT_MD="$SNAPSHOT_DIR/ci_health_latest.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_TOTAL=0
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARN=0

# --- Helper Functions ---

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}CI Health Panel v0.2 — Smoke Test${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}--- $1 ---${NC}"
}

check_pass() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    CHECKS_WARN=$((CHECKS_WARN + 1))
    echo -e "${YELLOW}⚠${NC} $1"
}

print_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "Total checks: $CHECKS_TOTAL"
    echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
    echo -e "${YELLOW}Warnings: $CHECKS_WARN${NC}"
    echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
    echo ""

    if [[ $CHECKS_FAILED -gt 0 ]]; then
        echo -e "${RED}Status: FAIL${NC}"
        return 1
    elif [[ $CHECKS_WARN -gt 0 ]]; then
        echo -e "${YELLOW}Status: WARN (degraded but non-critical)${NC}"
        return 2
    else
        echo -e "${GREEN}Status: PASS${NC}"
        return 0
    fi
}

# --- Checks ---

check_dependencies() {
    print_section "Dependencies"

    if command -v jq &> /dev/null; then
        check_pass "jq installed"
    else
        check_fail "jq not found (required for JSON validation)"
    fi

    if command -v curl &> /dev/null; then
        check_pass "curl installed"
    else
        check_warn "curl not found (optional, für API tests)"
    fi
}

check_snapshot_files() {
    print_section "Snapshot Files"

    # Check snapshot directory
    if [[ -d "$SNAPSHOT_DIR" ]]; then
        check_pass "Snapshot directory exists: $SNAPSHOT_DIR"
    else
        check_warn "Snapshot directory not found: $SNAPSHOT_DIR (wird bei erstem API call erstellt)"
    fi

    # Check JSON snapshot
    if [[ -f "$SNAPSHOT_JSON" ]]; then
        check_pass "JSON snapshot exists: $SNAPSHOT_JSON"

        # Validate JSON structure
        if jq -e '.overall_status, .checks, .server_timestamp_utc' "$SNAPSHOT_JSON" &> /dev/null; then
            check_pass "JSON snapshot has required v0.2 fields"
        else
            check_fail "JSON snapshot missing required fields"
        fi

        # Check for v0.2 specific fields
        if jq -e '.git_head_sha, .app_version' "$SNAPSHOT_JSON" &> /dev/null; then
            check_pass "JSON snapshot has v0.2 enrichment fields"
        else
            check_warn "JSON snapshot missing optional v0.2 fields (git_head_sha, app_version)"
        fi
    else
        check_warn "JSON snapshot not found (wird bei erstem /status call erstellt)"
    fi

    # Check MD snapshot
    if [[ -f "$SNAPSHOT_MD" ]]; then
        check_pass "Markdown snapshot exists: $SNAPSHOT_MD"

        # Basic structure check
        if grep -q "CI.*Health" "$SNAPSHOT_MD" && grep -q "Overall Status" "$SNAPSHOT_MD"; then
            check_pass "Markdown snapshot has expected structure"
        else
            check_warn "Markdown snapshot structure unexpected"
        fi
    else
        check_warn "Markdown snapshot not found (wird bei erstem /status call erstellt)"
    fi
}

check_source_code() {
    print_section "Source Code"

    # Check router file
    ROUTER_FILE="$REPO_ROOT/src/webui/ops_ci_health_router.py"
    if [[ -f "$ROUTER_FILE" ]]; then
        check_pass "Router file exists: $ROUTER_FILE"

        # Check for v0.2 features
        if grep -q "_persist_snapshot" "$ROUTER_FILE"; then
            check_pass "Snapshot persistence code present"
        else
            check_fail "Snapshot persistence code missing"
        fi

        if grep -q "POST /ops/ci-health/run" "$ROUTER_FILE" || grep -q '@router.post.*"/run"' "$ROUTER_FILE"; then
            check_pass "Run endpoint code present"
        else
            check_fail "Run endpoint code missing"
        fi

        if grep -q "threading.Lock" "$ROUTER_FILE"; then
            check_pass "Concurrency lock present"
        else
            check_fail "Concurrency lock missing"
        fi
    else
        check_fail "Router file not found: $ROUTER_FILE"
    fi

    # Check template file
    TEMPLATE_FILE="$REPO_ROOT/templates/peak_trade_dashboard/ops_ci_health.html"
    if [[ -f "$TEMPLATE_FILE" ]]; then
        check_pass "Template file exists: $TEMPLATE_FILE"

        # Check for v0.2 UI features
        if grep -q "run-checks-btn" "$TEMPLATE_FILE"; then
            check_pass "Run checks button present in template"
        else
            check_fail "Run checks button missing in template"
        fi

        if grep -q "auto-refresh" "$TEMPLATE_FILE"; then
            check_pass "Auto-refresh toggle present in template"
        else
            check_warn "Auto-refresh toggle missing in template"
        fi
    else
        check_fail "Template file not found: $TEMPLATE_FILE"
    fi
}

check_api_endpoints() {
    # Parse arguments
    if [[ "${1:-}" == "--skip-api" ]] || [[ "$SKIP_API_CHECK" == "1" ]]; then
        print_section "API Endpoints (skipped)"
        check_warn "API endpoint checks skipped (use without --skip-api to test)"
        return 0
    fi

    print_section "API Endpoints"

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        check_warn "curl not available, skipping API tests"
        return 0
    fi

    # Test /ops/ci-health (HTML page)
    if curl -s -f -o /dev/null -w "%{http_code}" "$WEBUI_BASE_URL/ops/ci-health" | grep -q "200"; then
        check_pass "GET /ops/ci-health returns 200"
    else
        check_warn "GET /ops/ci-health not reachable (is WebUI running? uvicorn src.webui.app:app)"
    fi

    # Test /ops/ci-health/status (JSON API)
    STATUS_RESPONSE=$(curl -s -f "$WEBUI_BASE_URL/ops/ci-health/status" 2>/dev/null || echo "{}")
    if echo "$STATUS_RESPONSE" | jq -e '.overall_status' &> /dev/null; then
        check_pass "GET /ops/ci-health/status returns valid JSON"

        # Check v0.2 fields
        if echo "$STATUS_RESPONSE" | jq -e '.server_timestamp_utc, .git_head_sha' &> /dev/null; then
            check_pass "Status API has v0.2 fields"
        else
            check_warn "Status API missing v0.2 fields"
        fi
    else
        check_warn "GET /ops/ci-health/status not reachable or invalid JSON"
    fi

    # Test /ops/ci-health/run (POST)
    RUN_RESPONSE=$(curl -s -f -X POST -H "Content-Type: application/json" "$WEBUI_BASE_URL/ops/ci-health/run" 2>/dev/null || echo "{}")
    if echo "$RUN_RESPONSE" | jq -e '.overall_status' &> /dev/null; then
        check_pass "POST /ops/ci-health/run returns valid JSON"

        if echo "$RUN_RESPONSE" | jq -e '.run_triggered' &> /dev/null; then
            check_pass "Run API has run_triggered field"
        else
            check_warn "Run API missing run_triggered field"
        fi
    else
        check_warn "POST /ops/ci-health/run not reachable or invalid JSON"
    fi
}

check_documentation() {
    print_section "Documentation"

    # Check PR docs
    if [[ -f "$REPO_ROOT/docs/ops/PR_518_CI_HEALTH_PANEL_V0_2.md" ]]; then
        check_pass "v0.2 Snapshot docs exist"
    else
        check_warn "v0.2 Snapshot docs missing"
    fi

    if [[ -f "$REPO_ROOT/docs/ops/PR_519_CI_HEALTH_BUTTONS_V0_2.md" ]]; then
        check_pass "v0.2 Buttons docs exist"
    else
        check_warn "v0.2 Buttons docs missing"
    fi

    # Check if documented in README
    if grep -q "CI.*Health.*Panel" "$REPO_ROOT/docs/ops/README.md"; then
        check_pass "CI Health Panel documented in docs/ops/README.md"
    else
        check_warn "CI Health Panel not documented in docs/ops/README.md"
    fi
}

# --- Main ---

main() {
    print_header

    echo "Repository: $REPO_ROOT"
    echo "WebUI URL: $WEBUI_BASE_URL"
    echo ""

    check_dependencies
    check_snapshot_files
    check_source_code
    check_api_endpoints "$@"
    check_documentation

    print_summary
}

# Run
main "$@"
