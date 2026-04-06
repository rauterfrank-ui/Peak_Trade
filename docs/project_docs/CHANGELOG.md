# CHANGELOG

> Hinweis: Datum und Versionen kannst du nach Bedarf anpassen.
> Dieser Eintrag fasst die Änderungen aus `FILES_CHANGED.md` und
> später `archive&#47;full_files_stand_02.12.2025` zusammen.

---

## 2025-12-09 – Phase 81: Live Session Registry & Risk Severity v1

### Phase 81 – Live Session Registry & Risk Severity v1

- Neu: `PHASE_81_LIVE_SESSION_REGISTRY.md` als Design- und Flow-Dokument für die Live Session Registry.
- Neu: `PHASE_81_LIVE_RISK_SEVERITY_AND_ALERTS_V1.md` – Live Risk Severity & Alert Runbook v1 (Severity-Ampel, Alert-Helper, Operator-Runbook).
- Live-Track Dashboard zeigt jetzt eine Severity-Ampel (GREEN/YELLOW/RED) pro Session sowie Runbook-Hinweise im Session-Detail.
- Risk-Stack erweitert um `risk_alert_helpers` und `risk_runbook` – 102 neue/erweiterte Tests für Severity, Szenarien und Runbook-Logik.
- Keine Breaking Changes; Live-/Shadow-/Testnet-Flows bleiben kompatibel, Severity wirkt als zusätzliche Safety- und UX-Schicht oben auf den bestehenden Risk-Limits.

---

## 2025-12-09 – Live-Risk Severity in UI, Alerts & Runbook

### Live-Risk: Severity in UI, Alerts & Runbook

- **Neu:** End-to-end Integration des Live-Risk Severity-Systems (`OK`, `WARNING`, `BREACH`) in:
  - Web-Dashboard (Risk-Ampel pro Session, Risk-Detail-Ansicht),
  - Alerting & Logging (Slack/CLI/Logs),
  - Runbook-/Operator-Sicht (vollständige Handlungsempfehlungen).
- **Neu:** `src/live/risk_alert_helpers.py`
  - Formatierung von Risk-Alerts (inkl. Slack-Format),
  - Mapping von `RiskCheckSeverity` auf Alert-Level,
  - CLI/Terminal-Formatter mit ANSI-Farben.
- **Neu:** `src/live/risk_runbook.py`
  - Strukturierte Runbook-Einträge pro Status (`green`, `yellow`, `red`),
  - Sofortmaßnahmen, Checklisten und Eskalationspfade für Operatoren.
- **Neu:** `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md`
  - Vollständige Dokumentation: Architektur, Dashboard, Alerting, Runbook, Tests, Konfiguration, Usage-Beispiele und Next Steps.
- **Verbessert:** `src/webui/live_track.py` und Dashboard-Templates
  - Sessions-Übersicht mit Risk-Ampel (🟢/🟡/🔴),
  - Session-Detail-Seite mit Risk-Status, Limit-Details und Operator-Guidance.
- **Tests:**
  - Neue Suiten `tests/test_risk_alert_helpers.py` und `tests/test_risk_runbook.py`,
  - Insgesamt **102 Tests**, alle bestanden.
- **Rückwärtskompatibel:** Keine Breaking Changes – bestehende Live-/Execution-Flows funktionieren unverändert, profitieren aber von zusätzlicher Transparenz (Severity, Alerts, Runbook).

---

## 2025-12-09 – R&D-Strategien Dokumentation

### Docs

* Verfeinerte Beschreibung der R&D-Strategien **ArmstrongCycleStrategy** und **ElKarouiVolModelStrategy** in `docs/PHASE_75_STRATEGY_LIBRARY_V1_1.md`
  * Klarer R&D-Scope (Hypothesen- und Regime-Research, keine Live-/Paper-/Testnet-Freigabe)
  * Dokumentierte typische Nutzungsszenarien für beide Strategien

---

## 2025-12-02 – Risk- & Data-Layer Erweiterungen (Phase 2)

### Neue Dateien

**Risk-Layer**

- `src/risk/limits.py`
  Portfolio Risk Limits & Guards (globale Risiko-Limits und Schutzmechanismen für das Portfolio).

- `src/risk/position_sizer.py`
  Erweiterte Version des Position Sizers (inkl. Kelly-Logik und flexibler Parametrisierung).

- `src&#47;risk&#47;position_sizer_old_backup.py`
  Backup der alten Position-Sizing-Implementierung (nur zur Referenz, nicht produktiv genutzt).

**Data-Layer**

- `src/data/kraken_pipeline.py`
  Vollständige Kraken-Datenpipeline (End-to-End-Flow von Raw-Daten bis normalisierten OHLCV-Serien).

**Demo-Scripts**

- `scripts/demo_complete_pipeline.py`
  Demo-Skript für die komplette Pipeline (Data + Risk + Backtest).

- `scripts/demo_kraken_simple.py`
  Vereinfachte Demo der Kraken-Pipeline.

**Dokumentation**

- `docs/NEW_FEATURES.md`
  Detaildokumentation der neuen Features.

- `docs/project_docs/IMPLEMENTATION_SUMMARY.md`
  Zusammenfassung der Implementierung (Architektur, Module, Datenfluss).

- `docs/project_docs/FILES_CHANGED.md`
  Technische Änderungsübersicht für diese Phase.

### Geänderte Dateien

**Config**

- `config/config.toml`
  Erweiterung um neue Risk-Parameter (z.B. Limits, Kelly-Faktoren, Safety-Grenzen).

**Module Exports**

- `src/risk/__init__.py`
  Exports für neue Risk-Module (`limits`, erweiterter `position_sizer`) ergänzt.

- `src/data/__init__.py`
  Exports für `kraken_pipeline.py` ergänzt, damit die Pipeline über den Data-Namespace verfügbar ist.

### Unverändert (aber Teil der bestehenden Integration)

- `src/core/config.py` – zentrales Config-System (bereits in Produktion).
- `src/data/kraken.py` – Kraken-Client.
- `src/data/normalizer.py` – Data Normalizer.
- `src/data/cache.py` – Parquet Cache.
- `src/backtest/engine.py` – Backtest Engine.

> Zusammenfassung:
> **Neue Dateien:** 9
> **Geänderte Dateien:** 3
> **Backup-Dateien:** 1
> Alle Änderungen sind rückwärtskompatibel und brechen bestehenden Code nicht.

---

## 2025-12-01 – Archivierter Stand (aus `full_files_stand_02.12.2025`)

*(Platzhalter – hier die wichtigsten Änderungen aus `archive&#47;full_files_stand_02.12.2025` eintragen, sobald der Inhalt konsolidiert ist. Vorschlag: nach Themenblöcken „Backtest", „Daten", „Strategien", „Projektorganisation" zusammenfassen.)*
