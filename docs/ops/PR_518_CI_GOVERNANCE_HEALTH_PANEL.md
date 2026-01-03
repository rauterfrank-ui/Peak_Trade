# PR #518 – CI & Governance Health Panel

**PR:** #518  
**Status:** ✅ Erstellt (Wartet auf Review)  
**Branch:** `ops/ci-governance-health-panel`  
**Date:** 2025-01-03  
**Author:** Peak_Trade Team

---

## Summary

Erweitert das **Ops Dashboard v0.1** um ein neues **CI & Governance Health Panel**.

Das Panel führt lokale CI-Checks aus und zeigt den Status als operator-freundliche Ampel-Ansicht mit detaillierten Fehlerauszügen und Links zur Dokumentation.

**Kernpunkte:**
- ✅ **Lokale CI-Checks:** Contract Guard + Docs Reference Validation
- ✅ **Ampel-System:** OK/FAIL/WARN Status Cards
- ✅ **Operator-freundlich:** Fehlerauszüge, vollständige Ausgabe, Dokumentations-Links
- ✅ **JSON API:** Für Automation/Tooling
- ✅ **12 Tests:** Alle bestanden (HTML rendering, JSON API, Error Handling)
- ✅ **Offline-lokal:** Keine externen Secrets, read-only checks

---

## Features

### 1. CI & Governance Checks

**Contract Guard:**
- Script: `scripts/ops/check_required_ci_contexts_present.sh`
- Prüft: CI-Kontext-Konfiguration (matrix checks, concurrency, job naming)
- Exit Codes: 0 = OK, 1 = FAIL

**Docs Reference Validation:**
- Script: `scripts/ops/verify_docs_reference_targets.sh --changed --warn-only`
- Prüft: Markdown-Links auf existierende Dateien (nur geänderte Dateien)
- Exit Codes: 0 = OK, 1 = FAIL, 2 = WARN

### 2. UI Components

**Status Cards:**
- Overall Status Badge (OK/WARN/FAIL)
- Check-spezifische Status-Badges
- Laufzeit + Exit Code
- Fehlerauszüge (max 20 Zeilen, collapsed)
- Vollständige Ausgabe (collapsed)

**Dokumentations-Links:**
- `docs/ops/runbooks/github_rulesets_pr_reviews_policy.md`
- `docs/ops/README.md` (GitHub Branch Protection Section)
- Click-to-copy Funktionalität

**Legend:**
- ✅ OK: Check erfolgreich
- ⚠️ WARN: Warnung, nicht kritisch
- ❌ FAIL: Check fehlgeschlagen
- ⏭️ SKIP: Script nicht verfügbar

### 3. API Endpoints

**HTML Dashboard:**
```
GET /ops/ci-health
```
- Zeigt Status Cards mit allen Checks
- Auto-Refresh möglich (kann später hinzugefügt werden)

**JSON API:**
```
GET /ops/ci-health/status
```
- Gibt strukturierte Check-Ergebnisse zurück
- Für Automation/Tooling

**Response Schema:**
```json
{
  "overall_status": "OK|WARN|FAIL",
  "summary": {
    "total": 2,
    "ok": 2,
    "warn": 0,
    "fail": 0,
    "skip": 0
  },
  "checks": [
    {
      "check_id": "contract_guard",
      "title": "Contract Guard",
      "description": "...",
      "status": "OK",
      "exit_code": 0,
      "output": "...",
      "error_excerpt": "",
      "duration_ms": 123,
      "timestamp": "2025-01-03T...",
      "script_path": "scripts/ops/...",
      "docs_refs": ["docs/ops/..."]
    }
  ],
  "generated_at": "2025-01-03T..."
}
```

---

## Implementation

### Neue Dateien

**`src/webui/ops_ci_health_router.py`** (359 lines)
- FastAPI Router für CI Health Panel
- Check-Execution-Logik (`_run_check`, `_run_all_checks`)
- HTML + JSON Endpoints
- Error Handling (Timeout, Missing Scripts, Exit Codes)

**`templates/peak_trade_dashboard/ops_ci_health.html`** (212 lines)
- Tailwind CSS basiertes UI
- Status Cards mit Ampel-System
- Collapsible Fehlerausgabe
- Click-to-copy Dokumentations-Links
- Responsive Design

**`tests/webui/test_ops_ci_health_router.py`** (359 lines)
- 12 Smoke-Tests
- Test Coverage:
  - HTML rendering
  - JSON API structure
  - Check execution
  - Missing scripts handling
  - Failing/Warning checks
  - Full workflow

### Geänderte Dateien

**`src/webui/app.py`** (+8 lines)
- Import `ops_ci_health_router`
- Router-Integration mit `set_ci_health_config` + `app.include_router`

---

## Testing

### Smoke Tests

```bash
python3 -m pytest tests/webui/test_ops_ci_health_router.py -v
```

**Ergebnis:**
```
============================= test session starts ==============================
collected 12 items

tests/webui/test_ops_ci_health_router.py::test_ci_health_dashboard_renders PASSED [  8%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_dashboard_shows_status PASSED [ 16%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_dashboard_shows_check_count PASSED [ 25%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_status_json PASSED [ 33%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_status_check_structure PASSED [ 41%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_status_includes_contract_guard PASSED [ 50%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_status_includes_docs_validation PASSED [ 58%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_executes_checks PASSED [ 66%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_handles_missing_script PASSED [ 75%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_handles_failing_check PASSED [ 83%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_handles_warning_check PASSED [ 91%]
tests/webui/test_ops_ci_health_router.py::test_ci_health_full_workflow PASSED [100%]

============================== 12 passed in 0.40s
==============================
```

✅ Alle Tests bestanden

### Linter

```bash
ruff check src/webui/ops_ci_health_router.py
ruff check tests/webui/test_ops_ci_health_router.py
```

✅ Keine Fehler

---

## Usage

### Dashboard starten

```bash
# Im Repo-Root
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

### Panel öffnen

```bash
# Browser
open http://127.0.0.1:8000/ops/ci-health

# Oder JSON API
curl http://127.0.0.1:8000/ops/ci-health/status | jq
```

### Navigation

Das Panel ist im Dashboard-Header verlinkt:
- Dashboard Home: `/`
- Stage1 Ops: `/ops/stage1`
- Workflows Hub: `/ops/workflows`
- **CI Health: `/ops/ci-health`** ← NEU

---

## Safety & Design

### Safety

✅ **Offline-lokal:**
- Keine externen API-Calls
- Keine Secrets erforderlich
- Nur lokale Script-Ausführung

✅ **Read-only:**
- Keine destructive operations
- Nur Check-Ausführung + Status-Anzeige

✅ **Error Handling:**
- Timeouts (30s default)
- Missing scripts → SKIP status
- Exit codes → OK/WARN/FAIL mapping

### Design

**Konsistent mit bestehenden Panels:**
- Folgt dem Design von `/ops/stage1` und `/ops/workflows`
- Tailwind CSS basiert
- Sticky Header mit Navigation
- Dark Theme (slate-950 background)

**Operator-freundlich:**
- Ampel-System für schnelle Übersicht
- Fehlerauszüge für Debugging
- Dokumentations-Links für Kontext
- Click-to-copy für Pfade

---

## Future Enhancements

**Mögliche Erweiterungen (nicht in diesem PR):**

1. **Auto-Refresh:**
   - Automatische Aktualisierung alle 30s (wie Stage1 Panel)

2. **Weitere Checks:**
   - `scripts/ops/verify_policy_pack_coverage.sh`
   - `scripts/ops/check_docs_freshness.sh`
   - Custom checks via config

3. **History:**
   - Check-Historie speichern (JSON files)
   - Trend-Analyse über Zeit

4. **Notifications:**
   - Slack/Email bei FAIL status
   - Integration mit Alerting-System

5. **CI Integration:**
   - GitHub Actions Workflow für scheduled checks
   - Report-Upload als Artifacts

---

## Checklist

- [x] Neue Komponenten erstellt
- [x] Router in app.py integriert
- [x] Tests geschrieben (12 Tests, alle bestanden)
- [x] Linter clean (ruff, pre-commit)
- [x] Dokumentation verlinkt
- [x] Offline-lokal, keine Secrets
- [x] PR erstellt (#518)
- [x] Commit message: "ops(dashboard): add CI & governance health panel"

---

## Related

- Basiert auf: `/ops/stage1` (Phase 16K), `/ops/workflows`
- Nutzt: `scripts/ops/check_required_ci_contexts_present.sh`
- Nutzt: `scripts/ops/verify_docs_reference_targets.sh`
- Dokumentation: `docs/ops/runbooks/github_rulesets_pr_reviews_policy.md`
- Dokumentation: `docs/ops/README.md`

---

## Files Changed

```
src/webui/ops_ci_health_router.py                    | 359 ++++++++++++++++++
templates/peak_trade_dashboard/ops_ci_health.html    | 212 +++++++++++
tests/webui/test_ops_ci_health_router.py             | 359 ++++++++++++++++++
src/webui/app.py                                     |   8 +
4 files changed, 938 insertions(+)
```

---

**PR Link:** https://github.com/rauterfrank-ui/Peak_Trade/pull/518
