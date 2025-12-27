#!/bin/bash
# scripts/test_knowledge_api_smoke.sh
# Smoke Tests für Knowledge DB API Endpoints
#
# Voraussetzung: Server läuft auf :8000
# uvicorn src.webui.app:app --reload --port 8000

set -e

BASE_URL="http://127.0.0.1:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Knowledge DB API Smoke Tests"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s "${BASE_URL}/api/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server not reachable at ${BASE_URL}${NC}"
    echo "Start server with: uvicorn src.webui.app:app --reload --port 8000"
    exit 1
fi

echo -e "${GREEN}✓ Server reachable${NC}"
echo ""

# Test 1: GET endpoints (should always work)
echo "Test 1: GET /api/knowledge/snippets"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/knowledge/snippets?limit=5")
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ GET snippets: ${STATUS}${NC}"
else
    echo -e "${RED}✗ GET snippets: ${STATUS} (expected 200)${NC}"
fi

echo "Test 2: GET /api/knowledge/strategies"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/knowledge/strategies?limit=5")
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ GET strategies: ${STATUS}${NC}"
else
    echo -e "${RED}✗ GET strategies: ${STATUS} (expected 200)${NC}"
fi

echo "Test 3: GET /api/knowledge/stats"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/knowledge/stats")
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ GET stats: ${STATUS}${NC}"

    # Show current flags
    RESPONSE=$(curl -s "${BASE_URL}/api/knowledge/stats")
    READONLY=$(echo "$RESPONSE" | jq -r '.environment.KNOWLEDGE_READONLY')
    WEB_WRITE=$(echo "$RESPONSE" | jq -r '.environment.KNOWLEDGE_WEB_WRITE_ENABLED')
    echo -e "  ${YELLOW}Current flags: READONLY=${READONLY}, WEB_WRITE=${WEB_WRITE}${NC}"
else
    echo -e "${RED}✗ GET stats: ${STATUS} (expected 200)${NC}"
fi

echo ""
echo "Test 4: POST /api/knowledge/snippets (default: should be 403)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}/api/knowledge/snippets" \
    -H "Content-Type: application/json" \
    -d '{"content":"Test content","title":"Test"}')

if [ "$STATUS" = "403" ]; then
    echo -e "${GREEN}✓ POST snippet (default): ${STATUS} (correctly blocked)${NC}"

    # Show error message
    ERROR=$(curl -s -X POST "${BASE_URL}/api/knowledge/snippets" \
        -H "Content-Type: application/json" \
        -d '{"content":"Test","title":"Test"}' | jq -r '.detail.error')
    echo -e "  ${YELLOW}Error: ${ERROR}${NC}"
elif [ "$STATUS" = "201" ]; then
    echo -e "${YELLOW}⚠ POST snippet: ${STATUS} (writes are enabled!)${NC}"
    echo -e "  ${YELLOW}Note: This is OK if KNOWLEDGE_WEB_WRITE_ENABLED=true${NC}"
else
    echo -e "${RED}✗ POST snippet: ${STATUS} (expected 403 or 201)${NC}"
fi

echo ""
echo "Test 5: GET /api/knowledge/search"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/knowledge/search?q=test&k=3")
if [ "$STATUS" = "200" ] || [ "$STATUS" = "501" ]; then
    echo -e "${GREEN}✓ GET search: ${STATUS}${NC}"
    if [ "$STATUS" = "501" ]; then
        echo -e "  ${YELLOW}Note: 501 = Backend not available (chromadb not installed)${NC}"
    fi
else
    echo -e "${RED}✗ GET search: ${STATUS} (expected 200 or 501)${NC}"
fi

echo ""
echo "=========================================="
echo "Manual Tests (requires server restart):"
echo "=========================================="
echo ""
echo "To enable writes, restart server with:"
echo "  export KNOWLEDGE_READONLY=false"
echo "  export KNOWLEDGE_WEB_WRITE_ENABLED=true"
echo "  uvicorn src.webui.app:app --reload --port 8000"
echo ""
echo "Then test POST:"
echo "  curl -X POST ${BASE_URL}/api/knowledge/snippets \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"content\":\"Test\",\"title\":\"Test\"}'"
echo ""
echo "To test readonly override:"
echo "  export KNOWLEDGE_READONLY=true"
echo "  export KNOWLEDGE_WEB_WRITE_ENABLED=true"
echo "  # Restart server"
echo ""
echo "=========================================="
echo "✓ Smoke tests complete"
echo "=========================================="

