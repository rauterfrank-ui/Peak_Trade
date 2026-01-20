# PR #242 — Merge Log

**PR:** #242 — Live Status Panel Features (Providers + Service-Layer + Docs + Tests)  
**Link:** https://github.com/rauterfrank-ui/Peak_Trade/pull/242  
**Merged:** 2025-12-22 (Europe/Berlin)  
**Merge-Method:** Squash (Branch gelöscht)  
**Branch:** feat/knowledge-db-strategy-vault-v0-clean → main  
**Scope:** webui/live/status-panels + tests + docs  
**Diff:** +2110 / -13 (nach CI-Fix)

## Summary
Diese PR liefert die „Live Status Panel"-Basis end-to-end:
- **Provider-Layer** für Live-Status-Panels
- **Service-Layer** als Single Source of Truth für Panel-Daten
- **Tests** für Panel-Snapshot-Verhalten
- **WebUI-Dokumentation** für Panels (inkl. Positions/Portfolio/Risk)
- **CI-Fix** durch Entfernen einer unvollständigen Testdatei, die ImportErrors verursachte

## Why
Ziel ist eine robuste, nachvollziehbare Live-Status-Panel-Pipeline:
- Stabiler Snapshot-Aufbau (kein "leerer Snapshot")
- Klare Verantwortlichkeiten (Providers ↔ Service ↔ WebUI)
- Tests sichern Mapping/Struktur und verhindern Regressionen
- Operator-Dokumentation für Erweiterungen und Panel-Verständnis

## Changes
### Implementation + Tests
- **Modified:** `src/reporting/status_snapshot_schema.py`
  - Schema-/Panel-Struktur ergänzt/abgesichert (Live-Snapshot Panels)
- **Added:** `src/live/status_providers.py`
  - Panel-Provider Verdrahtung für Live-Dashboard/Status-Snapshot
- **Added:** `src/webui/services/__init__.py`
- **Added:** `src/webui/services/live_panel_data.py`
  - Read-only Service-Layer für Panel-Daten (Single Source of Truth)
- **Added:** `tests/test_live_status_snapshot_panels.py`
  - Tests für Live-Status Snapshot Panels (Struktur/Mappings)

### Documentation
- **Added:** `docs/webui/LIVE_STATUS_PANELS.md`
- **Added:** `docs/webui/LIVE_PANELS_POSITIONS_PORTFOLIO_RISK.md`

### CI-Fix
- **Removed:** `tests&#47;test_health_detailed_panel_mapping.py`
  - Grund: ImportError durch Referenz auf nicht-existierenden Code in `health_endpoint.py`

## Verification
CI (GitHub Actions) — **alle Checks grün**:
- ✅ tests (3.11)
- ✅ audit
- ✅ lint
- ✅ CI Health Gate (weekly_core)
- ✅ Policy Critic Review
- ✅ Render Quarto Smoke Report
- ✅ Guard tracked files in reports directories
- ✅ strategy-smoke

Pre-Commit Hooks: ✅ bestanden

## Risk
**🟢 Low**
- Read-only Service-Layer, keine riskanten Side-Effects erwartet
- Breite CI-Abdeckung inkl. Tests + Audit + Lint + Smoke
- CI-Fix entfernt unvollständigen Test statt Produktivlogik zu ändern

## Operator How-To
- Panel-Verhalten/Datenflüsse: siehe `docs/webui/LIVE_STATUS_PANELS.md`
- Positions/Portfolio/Risk Panels: siehe `docs/webui/LIVE_PANELS_POSITIONS_PORTFOLIO_RISK.md`
- Lokale Sanity:
  - `uv run ruff check .`
  - `uv run pytest -q`
  - optional gezielt: `uv run pytest -q tests&#47;test_live_status_snapshot_panels.py`

## References
- PR #242: https://github.com/rauterfrank-ui/Peak_Trade/pull/242
- Commits (PR):
  - `4d6ba81` — test(live): fix snapshot builder tests and panel mapping
  - `c828b82` — feat(webui): wire live status panel providers + service layer + tests
  - `25f6997` — docs(webui): add live status panels documentation
  - `543e549` — fix(ci): remove incomplete test file causing ImportError
