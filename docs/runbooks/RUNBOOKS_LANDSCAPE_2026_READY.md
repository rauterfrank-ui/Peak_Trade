# Peak_Trade – Runbooks Landscape (2026-ready)

Diese Übersicht dient als **zentraler Einstiegspunkt** für alle Runbooks und Operator-Guides im Peak_Trade-Projekt.

Sie ist für **Operatoren, On-Call-Engineers und Risk Owner** gedacht, die im Incident-Fall oder vor kritischen Aktionen schnell das passende Dokument finden müssen.

* Fokus: **Execution, Live-Risk, Alerts/Eskalation, Governance und R&D**
* Gültigkeit: **2026-ready** (Stand: Dezember 2025)
* Quelle: Alle Runbooks liegen unter `docs/` bzw. `docs/runbooks/` und sind im Master-Status-Dokument verlinkt.

---

## 1. Zentrale Runbook-Tabelle (2026-ready)

| Runbook                                         | Pfad                                                                    | Version         | Scope / Zweck                                                                                                                          | Primary Cluster                                            | Layer                                    | 2026-ready Status       |
| ----------------------------------------------- | ----------------------------------------------------------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------- | ----------------------- |
| **ExecutionPipeline Governance & Risk Runbook** | `docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md`        | v1.1 (Dez 2025) | Governance- und Risk-Guidance für die ExecutionPipeline: Status-Codes, Entscheidungsbaum, Incident-Artefakte, Daily Checks             | Phase 16A (ExecutionPipeline), verknüpft mit Cluster 82–85 | **Execution & Environments, Governance** | ✅ 2026-ready            |
| **Live Risk Severity Integration**              | `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md`                       | v1.0            | End-to-end Integration der Live-Risk-Severity-Ampel (GREEN/YELLOW/RED) inkl. Dashboard, Alerts und Runbook-Anweisungen                 | Cluster 80–81 (Live Risk & Severity)                       | **Live-Risk, Monitoring, Web-UI**        | ✅ 2026-ready            |
| **Live Alert Pipeline Runbook**                 | `docs/runbooks/LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md`           | v1.0            | Betrieb und Fehlerbehandlung der Alert-Pipeline (Slack, E-Mail, Severity, Routing)                                                     | Cluster 82–83 (Alert-Pipeline & Dashboard)                 | **Alerts & Monitoring**                  | ✅ 2026-ready            |
| **Incident Runbook Integration**                | `docs/runbooks/INCIDENT_RUNBOOK_INTEGRATION_V1.md`                      | v1.0            | Standardisiertes Incident-Handling, Mapping von Alerts & Risk-Events auf Incident-Flows und Operator-Actions                           | Cluster 84 (Incident Runbook Integration)                  | **Incident-Management, Governance**      | ✅ 2026-ready            |
| **Go/No-Go 2026 – Live Alerts & Escalation**    | `docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md`                       | v1.0            | Go/No-Go-Entscheidungen für Live Alerts, Escalation-Pfade und Freigabekriterien für Live-/Shadow-/Testnet-Betrieb                      | Cluster 82–85 (Live Alerts & Escalation)                   | **Governance, On-Call, Decision-Gates**  | ✅ 2026-ready            |
| **R&D-Runbook Armstrong & El Karoui**           | `docs/runbooks/R_AND_D_RUNBOOK_ARMSTRONG_EL_KAROUI_V1.md`               | v1.0            | Runbook für R&D-Experimente mit Armstrong- und El-Karoui-Modellen (Set-up, Parameter, typische Fallstricke)                            | Phase 78 / R&D Armstrong × El Karoui                       | **R&D, Research Pipelines**              | ⚠️ R&D only (kein Live) |
| **R&D-Playbook Armstrong & El Karoui**          | `docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md`              | v1.0            | Playbook mit Best Practices, Experiment-Design, Parameter-Sweeps und Auswertungs-Patterns für Armstrong/El-Karoui                      | Phase 78 / R&D Armstrong × El Karoui                       | **R&D, Methodik**                        | ⚠️ R&D only (kein Live) |
| **Armstrong × El Karoui Cross-Run Findings**    | `docs/runbooks/ARMSTRONG_ELKAROUI_CROSS_RUN_FINDINGS_V1.md`             | v1.0            | Konsolidierte Findings aus Cross-Runs (State-Rankings, Vol-Regime, Limitierungen), dient als Meta-Referenz für weitere R&D-Iterationen | Phase 78 / R&D Armstrong × El Karoui                       | **R&D, Meta-Analyse**                    | ⚠️ R&D only (kein Live) |
| **Offline-Realtime-Pipeline Runbook**           | `docs/runbooks/OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md`                 | v1.0            | Operator-Runbook für die Offline-Realtime-Pipeline mit synthetischen Ticks (`is_synthetic=True`) und MA-Crossover-Strategie im Paper-Modus | Phase 16A / Offline-Realtime Safety Sandbox                | **Offline Testing, Execution**           | ✅ Safety-Sandbox       |
<<<<<<< Updated upstream
| **Reporting Quickstart (Evidence Chain)**       | `docs/reporting/REPORTING_QUICKSTART.md`                                | v1.0            | Einstieg in Evidence-Chain Artefakte + Reporting Workflow (Quickstart)                                                                  | Reporting / Evidence Chain                                 | **Reporting, Evidence**                  | ✅ 2026-ready            |
| **RUNBOOK D3 — Watch-Only Web/API + Grafana**   | `docs/runbooks/RUNBOOK_D3_WATCH_ONLY_WEB_API_GRAFANA.md`                | v1.0 (Jan 2026) | Read-only API/UI: Runs List/Detail + Health; Grafana Panels (Observability UX)                                                         | Web/API + Grafana / Observability                          | **Web-UI, API, Monitoring**              | ✅ 2026-ready            |
| **RUNBOOK D2 — Reporting + Compare Runs**       | `docs/runbooks/RUNBOOK_D2_REPORTING.md`                                 | v1.0 (Jan 2026) | Ad-hoc Report aus Run-Artefakten generieren; optional Compare-Report für mehrere Runs                                                  | Reporting / Evidence Chain                                 | **Reporting, Evidence**                  | ✅ 2026-ready            |
| **RUNBOOK D4 — Ops/Governance Polish**          | `docs/ops/runbooks/finish_c/RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md`         | v1.0 (Jan 2026) | Templates, Frontdoor Links, Docs Gates, Evidence, Merge Logs, Release Checklist                                                        | Ops / Governance                                           | **Ops, Docs-Gates, Evidence**            | ✅ 2026-ready            |
| **RUNBOOK — To Finish (Master)**                | `docs/ops/runbooks/RUNBOOK_TO_FINISH_MASTER.md`                         | v1.0 (Jan 2026) | Docs-only Branch → PR → D2/D3/D4 DoD → SSoT „Finish“-Definition (NO‑LIVE)                                                               | Ops / Finish Workstreams                                   | **Ops, Docs-Gates, Evidence**            | ✅ 2026-ready            |
| **Finish C (Pointer) — Broker Adapter + Live‑Ops** | `docs/ops/runbooks/finish_c/RUNBOOK_FINISH_C_MASTER.md`              | v1.0 (Jan 2026) | Einstieg/Pointer in den Finish‑C Track (governance‑first, NO‑LIVE default); detaillierte Runbooks in `docs/ops/runbooks/finish_c/`     | Finish‑C Track                                             | **Ops, Governance**                      | ⚠️ Track (NO‑LIVE default) |
=======
| **RUNBOOK D2 — Reporting + Compare Runs**       | `docs/runbooks/RUNBOOK_D2_REPORTING.md`                                 | v1.0 (Jan 2026) | Ad-hoc Report aus Run-Artefakten generieren; optional Compare-Report für mehrere Runs                                                  | Reporting / Evidence Chain                                 | **Reporting, Evidence**                  | ✅ 2026-ready            |
| **RUNBOOK D3 — Watch-Only Web/API + Grafana**   | `docs/runbooks/RUNBOOK_D3_WATCH_ONLY_WEB_API_GRAFANA.md`                | v1.0 (Jan 2026) | Read-only API/UI: Runs List/Detail + Health; Grafana Panels (Observability UX)                                                         | Web/API + Grafana / Observability                          | **Web-UI, API, Monitoring**              | ✅ 2026-ready            |
>>>>>>> Stashed changes
| **Runbooks & Incident Handling**                | `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`                                | Phase 25/56     | Grundlegende Runbooks für Shadow-Modus (Shadow-Run, System Pause) und Incident-Handling-Prozess (Schweregrade, Response-Schema, Report-Template)             | Phase 25 (Governance & Safety), Phase 56 (Drills)          | **Shadow-Mode, Incident-Management**     | ✅ Shadow-Mode aktiv    |

> **Hinweis:** Pfade ggf. an die tatsächlichen Dateinamen im Repository anpassen.
> R&D-Runbooks sind **nicht live-freigegeben** und ausschließlich für Offline-Backtests, Research-Pipelines und akademische Analysen gedacht.

---

## 2. Execution & Governance Runbooks

### 2.1 ExecutionPipeline Governance & Risk Runbook (v1.1)

* **Pfad:** `docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md`
* **Rolle:** Primäres Runbook für alle Themen rund um die ExecutionPipeline:

  * Interpretation von `ExecutionStatus`-Codes
  * Entscheidungsbaum für Operatoren (wann stoppen, wann eskalieren, wann retriggern)
  * Pflicht-Artefakte bei Incidents (`run_id`, `session_id`, Config-Snapshot, Logs)
  * Daily Pre-Session Checks (5-Minuten-Routine) inkl. Beispiel-Kommandos
  * Differenzierung: Bug vs. Expected-Block vs. Governance-Schutz

### 2.2 Go/No-Go 2026 – Live Alerts & Escalation

* **Pfad:** `docs/GO_NO_GO_2026_LIVE_ALERTS_CLUSTER_82_85.md`
* **Rolle:** Governance-Dokument für:

  * Go/No-Go-Entscheidungen vor kritischen Änderungen (z.B. neue Alerts, neue Risk-Limits)
  * Bewertung von Alert-Clustern (Noise vs. Signal)
  * Escalation-Level und On-Call-Übergabe
  * 2026-ready Kriterien für Live-Betrieb

### 2.3 Incident Runbook Integration

* **Pfad:** `docs/runbooks/INCIDENT_RUNBOOK_INTEGRATION_V1.md`
* **Rolle:** Brücke zwischen technischen Alerts und Incident-Management:

  * Mapping Alert → Incident-Typ → Operator-Aktion
  * Standardisierte Timeline & Kommunikationspfade
  * Integration mit Severity-System und Go/No-Go-Entscheidungen

---

## 3. Live Risk & Severity Runbooks

### 3.1 Live Risk Severity Integration

* **Pfad:** `docs/runbooks/LIVE_RISK_SEVERITY_INTEGRATION.md`
* **Rolle:** End-to-end Dokumentation der **Severity-Ampel (GREEN/YELLOW/RED)**:

  * Architektur (Risk-Limits → Severity-Bewertung → Alerts → Dashboard)
  * Web-Dashboard-Ansichten (Globale Ampel, Session-Detail-View)
  * Operator-Guidance: Was tun bei YELLOW? Was tun bei RED?
  * Integration mit Live-Track, Alert-Pipeline und Incident-Runbooks

---

## 4. Alerts, Escalation & On-Call Runbooks

### 4.1 Live Alert Pipeline Runbook

* **Pfad:** `docs/runbooks/LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md`
* **Rolle:** Laufender Betrieb der Alert-Pipeline:

  * Konfiguration von Severity, Channels (Slack, E-Mail) und Routing
  * Typische Fehlerbilder (keine Alerts, zu viele Alerts, Duplikate)
  * Debugging-Checkliste (Config, Logs, Test-Alerts)
  * Verbindung zu Dashboard und Incident-Runbooks

### 4.2 Incident Runbook Integration (siehe oben)

* Bindeglied zwischen Alerts und echten Incidents.
* Ergänzt die Alert-Pipeline um Operator-Flows und Governance-Aspekte.

### 4.3 Go/No-Go (siehe oben)

* Speziell relevant für On-Call-Entscheidungen:

  * „Bleiben wir im aktuellen Modus?"
  * „Brauchen wir eine temporäre Trading-Pause?"
  * „Müssen Limits sofort angepasst oder Systeme in einen Safe-Mode versetzt werden?"

---

## 5. R&D & Research Runbooks (Armstrong × El Karoui)

### 5.1 R&D-Runbook Armstrong & El Karoui

* **Pfad:** `docs/runbooks/R_AND_D_RUNBOOK_ARMSTRONG_EL_KAROUI_V1.md`
* **Rolle:** Technischer Leitfaden für:

  * Setup der Strategien Armstrong-Cycle und El-Karoui-Vol-Modell
  * Parameter-Räume und typische Konfigurationen
  * Einbindung in R&D-Pipelines (Backtests, Sweeps, Forward-Signals)

### 5.2 R&D-Playbook Armstrong & El Karoui

* **Pfad:** `docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md`
* **Rolle:** Methodisches Playbook:

  * Wie experimentieren? (Design, Hypothesen, Auswertungen)
  * Best Practices für Parameter-Sweeps und Cross-Run Analysen
  * Typische Fragestellungen und Auswertungs-Muster

### 5.3 Armstrong × El Karoui Cross-Run Findings

* **Pfad:** `docs/runbooks/ARMSTRONG_ELKAROUI_CROSS_RUN_FINDINGS_V1.md`
* **Rolle:** Meta-Dokument:

  * Konsolidierte Ergebnisse aus vielen Runs (State-Rankings, Vol-Regime, Edge-Stabilität)
  * Einschränkungen und offene Fragen
  * Basis für weitere R&D-Iterationen

> **Wichtig:** Diese drei R&D-Dokumente sind **nicht** für Live-Betrieb gedacht, sondern ausschließlich für Forschung und Offline-Analysen.

---

## 6. Offline-Testing & Safety-Sandbox Runbooks

### 6.1 Offline-Realtime-Pipeline Runbook

* **Pfad:** `docs/runbooks/OFFLINE_REALTIME_PIPELINE_RUNBOOK_V1.md`
* **Rolle:** Operator-Runbook für die Offline-Realtime-Pipeline:

  * Setup & Workflow für synthetische Ticks (`is_synthetic=True`)
  * MA-Crossover-Strategie im Paper-Modus
  * Typische Szenarien: Smoke-Tests, Stress-Tests, Regime-Varianz, Seed-Sweeps
  * Report-Generierung (Einzel-Run & Meta-Overview)
  * Safety-Guardrails & Troubleshooting

> **Safety:** Diese Pipeline ist eine **komplett sichere Sandbox** – synthetische Daten, Paper-Execution, keine echten Markt-Interaktionen.

---

## 7. Quick-Reference: Welche Situation → Welches Runbook?

| Situation                                                   | Relevante Runbooks                                                          | Kommentar                                                                                              |
| ----------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Pre-Session-Check vor Live/Paper-Session**                | ExecutionPipeline Governance & Risk Runbook, Live Risk Severity Integration | Daily Checks, Live-Risk-Ampel prüfen, Execution- und Risk-Pfade verifizieren                           |
| **Order wird blockiert (ExecutionStatus ≠ OK)**             | ExecutionPipeline Governance & Risk Runbook, Go/No-Go 2026                  | Status-Code nachschlagen, Entscheidungsbaum folgen, ggf. Go/No-Go-Prozess triggern                     |
| **RED Severity im Live-Dashboard**                          | Live Risk Severity Integration, Incident Runbook Integration, Go/No-Go 2026 | Severity-Runbook folgen, Incident eröffnen, Governance-Entscheidung (Weiterlaufen vs. Stoppen) treffen |
| **Unklare Incident-Ursache (viele Alerts, wenig Klarheit)** | Live Alert Pipeline Runbook, Incident Runbook Integration                   | Alert-Pipeline debuggen, Incident-Flow nutzen, korrekte Klassifikation sicherstellen                   |
| **Neue Alerts oder Änderungen an Escalation-Logik geplant** | Go/No-Go 2026, Live Alert Pipeline Runbook                                  | Änderungen nur über Go/No-Go-Prozess, Impact auf Operator-Flows prüfen                                 |
| **R&D-Strategie Armstrong/El Karoui: Neuer Experiment-Run** | R&D-Runbook Armstrong & El Karoui, R&D-Playbook                             | Setup & Methodik prüfen, Parameter-Sets und Hypothesen sauber dokumentieren                            |
| **Cross-Run-Analyse / Meta-Auswertung**                     | Armstrong × El Karoui Cross-Run Findings, R&D-Playbook                      | Bestehende Findings als Referenz nutzen, neue Runs konsistent einsortieren                             |
| **Execution-Pipeline offline testen (Safety-Sandbox)**       | Offline-Realtime-Pipeline Runbook                                            | Synthetische Ticks + Paper-Execution, komplett sicher, ideal für Strategie-Tests                        |
| **MA-Crossover-Strategie Parameter-Tuning**                  | Offline-Realtime-Pipeline Runbook                                            | Seed-Sweeps, verschiedene MA-Fenster, Regime-Varianz testen                                             |
<<<<<<< Updated upstream
| **Reporting (Evidence Chain) – Einstieg / Quickstart**       | Reporting Quickstart (Evidence Chain)                                        | Evidence-Chain Artefakte verstehen, Reports rendern, Troubleshooting                                     |
=======
>>>>>>> Stashed changes
| **HTML-Report / Compare-Report aus Run-Artefakten**          | RUNBOOK D2 — Reporting + Compare Runs                                        | Für ad-hoc Auswertung und Run-Vergleiche (Reporting/Evidence Chain)                                      |
| **Read-only Runs UI/API + Grafana Panels verifizieren**      | RUNBOOK D3 — Watch-Only Web/API + Grafana                                    | Runs List/Detail, Health, Observability UX (Panels/Queries Snapshot)                                     |

---

## 8. Architektur-Übersicht (Runbooks & Governance)

```text
                      +--------------------------------------+
                      |  Runbooks Landscape (2026-ready)     |
                      |  docs/runbooks/RUNBOOKS_LANDSCAPE_   |
                      |                  2026_READY.md       |
                      +-------------------------+------------+
                                                |
        +-------------------------------+-------+-------------------------------+
        |                               |                                       |
+-------+----------------+   +----------+-------------------+        +----------+------------------+
| Execution & Governance |   | Live Risk & Severity         |        | Alerts, Escalation & On-Call|
+------------------------+   +------------------------------+        +-----------------------------+
| - ExecutionPipeline    |   | - Live Risk Severity         |        | - Live Alert Pipeline       |
|   Governance & Risk    |   |   Integration                |        |   Runbook                   |
|   Runbook (v1.1)       |   |                              |        | - Incident Runbook          |
| - Go/No-Go 2026        |   |                              |        |   Integration               |
| - Incident Runbook     |   |                              |        | - Go/No-Go 2026             |
|   Integration          |   |                              |        |                             |
+------------------------+   +------------------------------+        +-----------------------------+
                                |
                                |
                                v
                    +-------------------------------+
                    | R&D & Research (Armstrong ×   |
                    | El Karoui, Phase 78)          |
                    +-------------------------------+
                    | - R&D-Runbook                 |
                    | - R&D-Playbook                |
                    | - Cross-Run Findings          |
                    +-------------------------------+
                                |
                                v
                    +-------------------------------+
                    | Offline Testing & Safety      |
                    | Sandbox                       |
                    +-------------------------------+
                    | - Offline-Realtime-Pipeline   |
                    |   Runbook (v1.0)              |
                    +-------------------------------+
```

---

## 9. Governance-Verankerung & Code-Referenzen

Die Runbooks sind nicht isoliert, sondern eng mit dem Code verknüpft:

* `src/governance/go_no_go.py` – Programmlogik für Go/No-Go-Entscheidungen im Kontext von Live Alerts & Escalation.
* `src/live/risk_limits.py` & verwandte Module – Basis für die Severity-Integration und Live-Risk-Evaluierung.
* `src/execution/` – ExecutionPipeline-Implementierung, auf die sich das ExecutionPipeline-Runbook direkt bezieht.
* `src/live/` – Alert-Infrastruktur der Live-Pipeline (u.a. `alert_pipeline.py`, `alerts.py`, `alert_manager.py`) und deren Integration in Dashboard & Incident-Flows.
* `src/infra/escalation/` & `src/infra/runbooks/` – Infrastruktur für Escalation-Management und Runbook-Registry.

Operatoren sollten Runbooks **immer im Kontext** dieser Module lesen – die Dokumentation beschreibt den beabsichtigten Use-Case, der Code erzwingt die technischen Grenzen.

---

## 10. Change-Log

* **v1.2 – Januar 2026**

  * Ergänzung: **RUNBOOK D2 — Reporting + Compare Runs (v1.0)**
  * Ergänzung: **RUNBOOK D3 — Watch-Only Web/API + Grafana (v1.0)**

* **v1.1 – Dezember 2025**

  * Ergänzung: **Offline-Realtime-Pipeline Runbook (v1.0)** – Safety-Sandbox für synthetische Ticks & Paper-Execution
  * Neue Sektion 6: "Offline-Testing & Safety-Sandbox Runbooks"
  * Quick-Reference erweitert um Offline-Testing-Szenarien
  * Architektur-Diagramm erweitert

* **v1.0 – Dezember 2025 – 2026-ready**

  * Initiale Erstellung der zentralen Runbook-Landscape mit 8 Runbooks.
  * Einführung der Tabellenstruktur inkl. `Primary Cluster`, `Layer` und `2026-ready Status`.
  * Ergänzung einer Quick-Reference-Tabelle für typische Operator-Situationen.
  * Hinzufügen eines Architektur-Diagramms und Governance-Verankerung.
