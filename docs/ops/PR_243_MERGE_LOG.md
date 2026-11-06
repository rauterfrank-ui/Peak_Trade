# MERGE LOG — PR #243 — feat(webui): knowledge API endpoints + readonly/web-write gating + smoke runners

**PR:** https://github.com/rauterfrank-ui/Peak_Trade/pull/243  
**Merged:** 2025-12-22  
**Merge Commit:** 885f4ad37cb4a6f4d9525933c8c981db8a4af92d  
**Branch:** feat/knowledge-db-strategy-vault-v0 (merged)

---

## Zusammenfassung
- Knowledge DB HTTP API mit 6 MVP-Endpoints (Snippets, Strategies, Search, Stats) implementiert – GET immer verfügbar, POST über zweistufiges Gating (KNOWLEDGE_READONLY + KNOWLEDGE_WEB_WRITE_ENABLED)
- End-to-end Operator-Smoke-Tests über automatisierte Runner (alle 3 Modes: Production/Development/Research) mit 15 Checks

## Warum
- Ermöglicht End-to-End-Verifikation des Readonly-Gatings über HTTP statt nur Unit-Tests
- Bietet robuste, operator-taugliche Smoke-Checks für alle offiziellen Config-Modi (Production/Development/Research)
- Graceful Degradation bei fehlendem Backend (Search: 200 oder 501, niemals 500)

## Änderungen
**Neu**
- `src/webui/knowledge_api.py` (456 Zeilen) — API-Router mit 6 Endpoints + Access-Control-Helpers
- `src/webui/services/knowledge_service.py` (411 Zeilen) — Service-Layer über Knowledge DB Module
- `tests/test_webui_knowledge_endpoints.py` (502 Zeilen) — 35 API-Tests (Access-Control, Errors, Graceful Degradation)
- `scripts/ops/knowledge_smoke_runner.sh` (109 Zeilen) — Manueller Smoke-Runner (Server-Restart erforderlich)
- `scripts/ops/knowledge_smoke_runner_auto.sh` (163 Zeilen) — Auto-Runner (Server-Lifecycle integriert)
- `scripts/ops/KNOWLEDGE_SMOKE_README.md` (264 Zeilen) — Umfassende Smoke-Tests-Dokumentation
- `KNOWLEDGE_API_SMOKE_TESTS.md` (394 Zeilen) — Manuelle curl-Beispiele
- `KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md` (603 Zeilen) — Vollständige API-Dokumentation

**Geändert**
- `src/webui/app.py` (+12 Zeilen) — Knowledge-API-Router eingebunden
- `requirements.txt` (+3 Zeilen) — chromadb-Dependency für CI
- `tests/test_knowledge_readonly_gating.py` (+3/-2 Zeilen) — skip_if_no_chromadb Decorator + Import-Fix

## Verifikation
**CI**
- ✅ pytest — 105 Knowledge-Tests passed (35 WebUI-Endpoints + 51 Readonly-Gating + 19 Integration)
- ✅ ruff check — All checks passed

**Lokal**
- ✅ `scripts/ops/knowledge_smoke_runner_auto.sh` — 15/15 Checks passed (3 Modes × 5 Checks)
  - Production (READONLY=true): POST blocked (403) ✓
  - Development (READONLY=false, WEB_WRITE=true): POST allowed (201) ✓
  - Research (READONLY=false, WEB_WRITE=false): POST blocked (403) ✓

## Risiko
**Risk:** 🟢 Minimal

**Begründung**
- Additive Endpoints (keine bestehende Funktionalität geändert)
- Strikte Defaults: Production-safe (READONLY=true, WEB_WRITE=false)
- Defense in Depth: Zweistufiges Gating (API-Layer + Knowledge-DB-Layer)
- Extensive Tests: 105 Unit-Tests + 15 Smoke-Tests (100% Pass-Rate)
- Graceful Degradation: Search gibt 501 (nicht 500) bei fehlendem Backend

## Operator How-To

### Smoke-Tests ausführen (empfohlen für Post-Deploy-Check)
```bash
# Automatischer Runner (empfohlen)
./scripts/ops/knowledge_smoke_runner_auto.sh

# Manuell (Server muss pro Mode neu gestartet werden)
./scripts/ops/knowledge_smoke_runner.sh
```

### API-Endpoints manuell testen
```bash
# Production Mode (Read-Only)
export KNOWLEDGE_READONLY=true
uvicorn src.webui.app:app --port 8000

# GET funktioniert
curl http://localhost:8000/api/knowledge/snippets

# POST blockiert
curl -X POST http://localhost:8000/api/knowledge/snippets \
  -H "Content-Type: application/json" \
  -d '{"title":"test","content":"test"}'
# Erwartet: 403 (Forbidden)

# Development Mode (Full Access)
export KNOWLEDGE_READONLY=false
export KNOWLEDGE_WEB_WRITE_ENABLED=true
uvicorn src.webui.app:app --port 8000

# POST funktioniert
curl -X POST http://localhost:8000/api/knowledge/snippets \
  -H "Content-Type: application/json" \
  -d '{"title":"test","content":"test"}'
# Erwartet: 201 (Created)
```

### Config-Modes im Überblick
| Mode | READONLY | WEB_WRITE | GET | POST | Use Case |
|------|----------|-----------|-----|------|----------|
| Production | true | false | ✅ 200 | ❌ 403 | Live-Systeme (safe) |
| Development | false | true | ✅ 200 | ✅ 201 | Local Dev (full access) |
| Research | false | false | ✅ 200 | ❌ 403 | Scripts only, WebUI read-only |

## Referenzen
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/243
- Commit: https://github.com/rauterfrank-ui/Peak_Trade/commit/885f4ad37cb4a6f4d9525933c8c981db8a4af92d
- Related:
  - `KNOWLEDGE_API_IMPLEMENTATION_SUMMARY.md` — Vollständige API-Doku
  - `KNOWLEDGE_API_SMOKE_TESTS.md` — Manuelle Smoke-Tests
  - `scripts/ops/KNOWLEDGE_SMOKE_README.md` — Smoke-Runner-Doku

---

### Extended

**Access Control — Zwei-Stufen-Gating**
```python
def require_write_allowed():
    # Level 1: Global Panic-Lock
    if KNOWLEDGE_READONLY == true:
        raise 403

def require_webui_write_allowed():
    # Level 1 + Level 2
    require_write_allowed()
    if KNOWLEDGE_WEB_WRITE_ENABLED != true:
        raise 403
```

**Test-Coverage-Details**
- **Unit-Tests:** 105 Knowledge-Tests (100% Pass-Rate)
  - 35 WebUI-Endpoint-Tests (Access-Control, Errors, Graceful Degradation)
  - 51 Readonly-Gating-Tests (alle Knowledge-DB-Module)
  - 19 Integration-Tests
- **Live-Smoke-Tests:** 15 Checks über 3 Modes (100% Pass-Rate)
  - Production Mode: 5/5 Checks ✅
  - Development Mode: 5/5 Checks ✅
  - Research Mode: 5/5 Checks ✅

**Nächste Schritte (optional)**
- Mock-Daten durch echte ChromaDB-Queries ersetzen
- Pagination-Support hinzufügen
- Batch-Operationen implementieren
- Audit-Logging für Write-Operationen
- HTML-Frontend für Knowledge-Browser
