# Knowledge DB API Smoke Tests

Manuelle Smoke Tests für die Knowledge DB WebUI API Endpoints.

## Prerequisites

Starte die WebUI:

```bash
cd /Users/frnkhrz/Peak_Trade
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

## Environment Variables

```bash
# Default: Beide flags disabled
export KNOWLEDGE_READONLY=false
export KNOWLEDGE_WEB_WRITE_ENABLED=false

# Oder in einem Terminal setzen:
unset KNOWLEDGE_READONLY
unset KNOWLEDGE_WEB_WRITE_ENABLED
```

---

## Test 1: GET /api/knowledge/stats (Always Available)

**Erwartung:** 200 OK, zeigt Backend-Status und Environment Flags

```bash
curl -s http://127.0.0.1:8000/api/knowledge/stats | jq .
```

**Erwartetes Ergebnis:**
```json
{
  "backend": "chroma",
  "available": true,
  "persist_directory": "./data/chroma_db",
  "total_documents": 42,
  "snippets": 25,
  "strategies": 17,
  "readonly_mode": false,
  "environment": {
    "KNOWLEDGE_READONLY": "false",
    "KNOWLEDGE_WEB_WRITE_ENABLED": "false"
  }
}
```

---

## Test 2: GET /api/knowledge/snippets (Read-Only, Always Available)

**Erwartung:** 200 OK, Liste von Snippets (oder graceful degradation wenn Backend fehlt)

```bash
curl -s http://127.0.0.1:8000/api/knowledge/snippets | jq .
```

**Mit Filtern:**

```bash
curl -s "http://127.0.0.1:8000/api/knowledge/snippets?limit=10&category=strategy" | jq .
```

**Erwartetes Ergebnis:**
```json
{
  "items": [
    {
      "id": "snippet_001",
      "title": "RSI Strategy Overview",
      "content": "RSI strategy works best in ranging markets...",
      "category": "strategy",
      "tags": ["rsi", "ranging"],
      "created_at": "2024-12-20T10:00:00Z"
    }
  ],
  "total": 2,
  "backend_available": true
}
```

---

## Test 3: GET /api/knowledge/strategies (Read-Only, Always Available)

**Erwartung:** 200 OK, Liste von Strategien

```bash
curl -s http://127.0.0.1:8000/api/knowledge/strategies | jq .
```

**Mit Filtern:**

```bash
curl -s "http://127.0.0.1:8000/api/knowledge/strategies?status=rd&name=RSI" | jq .
```

---

## Test 4: GET /api/knowledge/search (Semantic Search)

**Erwartung:** 200 OK wenn Backend verfügbar, 501 wenn ChromaDB fehlt

```bash
curl -s "http://127.0.0.1:8000/api/knowledge/search?q=momentum+strategy&k=5" | jq .
```

**Mit Type-Filter:**

```bash
curl -s "http://127.0.0.1:8000/api/knowledge/search?q=RSI&k=3&type=strategy" | jq .
```

**Erwartetes Ergebnis (Backend verfügbar):**
```json
{
  "query": "momentum strategy",
  "results": [
    {
      "content": "Momentum strategy works in trending markets...",
      "score": 0.95,
      "metadata": {
        "type": "snippet",
        "category": "strategy"
      }
    }
  ],
  "total": 1,
  "backend_available": true
}
```

**Erwartetes Ergebnis (Backend nicht verfügbar):**
```json
{
  "detail": {
    "error": "Knowledge DB backend not available",
    "message": "Vector database backend (chromadb) is not installed",
    "solution": "Install with: pip install chromadb"
  }
}
```

---

## Test 5: POST /api/knowledge/snippets (Write-Gated)

### 5a) Blocked: KNOWLEDGE_WEB_WRITE_ENABLED nicht gesetzt

```bash
export KNOWLEDGE_READONLY=false
unset KNOWLEDGE_WEB_WRITE_ENABLED

curl -s -X POST http://127.0.0.1:8000/api/knowledge/snippets \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test snippet content",
    "title": "Test Snippet",
    "category": "test",
    "tags": ["test", "demo"]
  }' | jq .
```

**Erwartetes Ergebnis:** 403 Forbidden
```json
{
  "detail": {
    "error": "WebUI write access disabled",
    "message": "Write operations via WebUI are disabled by default for safety",
    "solution": "Set KNOWLEDGE_WEB_WRITE_ENABLED=true to enable WebUI writes"
  }
}
```

### 5b) Blocked: KNOWLEDGE_READONLY=true (auch wenn WEB_WRITE_ENABLED=true)

```bash
export KNOWLEDGE_READONLY=true
export KNOWLEDGE_WEB_WRITE_ENABLED=true

curl -s -X POST http://127.0.0.1:8000/api/knowledge/snippets \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test snippet content",
    "title": "Test Snippet"
  }' | jq .
```

**Erwartetes Ergebnis:** 403 Forbidden
```json
{
  "detail": {
    "error": "Knowledge DB is in readonly mode",
    "message": "Write operations are blocked by KNOWLEDGE_READONLY flag",
    "solution": "Set KNOWLEDGE_READONLY=false to enable writes"
  }
}
```

### 5c) Success: Beide Flags erlauben Writes

```bash
export KNOWLEDGE_READONLY=false
export KNOWLEDGE_WEB_WRITE_ENABLED=true

curl -s -X POST http://127.0.0.1:8000/api/knowledge/snippets \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test snippet content about RSI strategy",
    "title": "RSI Strategy Notes",
    "category": "strategy",
    "tags": ["rsi", "mean-reversion"]
  }' | jq .
```

**Erwartetes Ergebnis:** 201 Created
```json
{
  "success": true,
  "snippet": {
    "id": "snippet_abc123",
    "title": "RSI Strategy Notes",
    "content": "Test snippet content about RSI strategy",
    "category": "strategy",
    "tags": ["rsi", "mean-reversion"],
    "created_at": "2024-12-22T00:00:00Z"
  }
}
```

---

## Test 6: POST /api/knowledge/strategies (Write-Gated)

### 6a) Blocked: Web Write Disabled

```bash
export KNOWLEDGE_READONLY=false
unset KNOWLEDGE_WEB_WRITE_ENABLED

curl -s -X POST http://127.0.0.1:8000/api/knowledge/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Strategy",
    "description": "A test strategy for demonstration",
    "status": "rd",
    "tier": "experimental"
  }' | jq .
```

**Erwartetes Ergebnis:** 403 Forbidden

### 6b) Blocked: Readonly Mode

```bash
export KNOWLEDGE_READONLY=true
export KNOWLEDGE_WEB_WRITE_ENABLED=true

curl -s -X POST http://127.0.0.1:8000/api/knowledge/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Strategy",
    "description": "A test strategy for demonstration",
    "status": "rd",
    "tier": "experimental"
  }' | jq .
```

**Erwartetes Ergebnis:** 403 Forbidden

### 6c) Success: Both Flags Enabled

```bash
export KNOWLEDGE_READONLY=false
export KNOWLEDGE_WEB_WRITE_ENABLED=true

curl -s -X POST http://127.0.0.1:8000/api/knowledge/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bollinger Bands Mean Reversion",
    "description": "Mean reversion strategy using Bollinger Bands as entry/exit signals",
    "status": "rd",
    "tier": "experimental"
  }' | jq .
```

**Erwartetes Ergebnis:** 201 Created
```json
{
  "success": true,
  "strategy": {
    "id": "strategy_bollinger_bands_mean_reversion",
    "name": "Bollinger Bands Mean Reversion",
    "description": "Mean reversion strategy using Bollinger Bands as entry/exit signals",
    "status": "rd",
    "tier": "experimental",
    "created_at": "2024-12-22T00:00:00Z"
  }
}
```

---

## Test 7: Backend Unavailable (Graceful Degradation)

Teste ohne ChromaDB Installation:

```bash
# ChromaDB temporär deinstallieren (optional)
# pip uninstall chromadb -y

# GET Endpoints: Graceful degradation (empty list)
curl -s http://127.0.0.1:8000/api/knowledge/snippets | jq .
```

**Erwartetes Ergebnis:**
```json
{
  "items": [],
  "total": 0,
  "backend_available": false,
  "message": "Knowledge DB backend not available (chromadb not installed)"
}
```

```bash
# Search: 501 Not Implemented
curl -s http://127.0.0.1:8000/api/knowledge/search?q=test | jq .
```

**Erwartetes Ergebnis:** 501 Not Implemented
```json
{
  "detail": {
    "error": "Knowledge DB backend not available",
    "message": "Vector database backend (chromadb) is not installed",
    "solution": "Install with: pip install chromadb"
  }
}
```

---

## Access Control Matrix

| READONLY | WEB_WRITE | GET Endpoints | POST Endpoints |
|----------|-----------|---------------|----------------|
| false    | false     | ✅ 200        | ❌ 403 (web write disabled) |
| false    | true      | ✅ 200        | ✅ 201 (success) |
| true     | false     | ✅ 200        | ❌ 403 (readonly) |
| true     | true      | ✅ 200        | ❌ 403 (readonly blocks) |

**Wichtig:** `KNOWLEDGE_READONLY=true` blockiert IMMER Writes, auch wenn `KNOWLEDGE_WEB_WRITE_ENABLED=true`.

---

## Cleanup

Räume Test-Daten auf:

```bash
# Stoppe WebUI (Ctrl+C)
# Optional: Lösche Test-Datenbank
rm -rf /Users/frnkhrz/Peak_Trade/data/chroma_db
```

---

## Automatisierte Tests

Führe die vollständige Test-Suite aus:

```bash
cd /Users/frnkhrz/Peak_Trade

# WebUI Endpoint Tests
python3 -m pytest tests/test_webui_knowledge_endpoints.py -v

# Readonly Gating Tests (alle Knowledge DB Module)
python3 -m pytest tests/test_knowledge_readonly_gating.py -v

# Alle Knowledge Tests
python3 -m pytest tests/test_knowledge*.py -v
```

**Erwartetes Ergebnis:**
- `test_webui_knowledge_endpoints.py`: 35 passed
- `test_knowledge_readonly_gating.py`: 51 passed
- Gesamt: 86+ passed
