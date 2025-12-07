# Peak_Trade – Live-/Testnet-Track Status Overview

Dieses Dokument fasst den aktuellen Status des **Live-/Shadow-/Testnet-Tracks** von Peak_Trade zusammen.
Ziel ist eine schnelle Einschätzung der **technischen Reife**, der **operativen Readiness** und der noch offenen Themen.

Stand: 2025-12-07 (nach Phase 54)

---

## 1. Zusammenfassung in Prozent

| Bereich                                     | Status   |
| ------------------------------------------- | -------- |
| Environment & Safety                        | 95%      |
| Live Risk Limits                            | 95%      |
| Order-/Execution-Layer & Exchange-Anbindung | 85%      |
| Shadow-/Paper-/Testnet-Orchestrierung       | 85%      |
| Run-Logging & Live-Reporting                | 90%      |
| Live-/Portfolio-Monitoring & Risk Bridge    | 95%      |
| Live Alerts & Notifications                 | 95%      |
| Governance, Runbooks & Checklisten          | 94%      |
| CLI-Tooling für Live-/Testnet-Operationen   | 95%      |
| **Gesamt Live-/Testnet-Track**              | **~95%** |

Interpretation:

* Unter ~80%: noch experimentell / nicht live-reif
* 80–90%: solide, einsatzbereit mit bewussten Limitierungen
* > 90%: stabiler Kern, nur noch Feintuning / Komfort / Edge-Cases offen

Der Live-/Testnet-Track bewegt sich aktuell im Bereich **~95%** –
**funktional einsatzbereit** mit integriertem Alert-System für Risk-Violations, zentralem Live-Ops CLI (Phase 51) und umfassendem Research→Live Playbook (Phase 54).

---

## 2. Environment & Safety (≈ 95%)

**Kernkomponenten:**

* `src/core/environment.py` – Environment-/Mode-Handling (z.B. Shadow, Testnet, Live)
* `src/live/safety.py` – Safety-Layer (Kill-Switch, Safety-Guards)
* `src/orders/exchange.py` – technische Anbindungsperspektive
* `docs/LIVE_TESTNET_PREPARATION.md` – Vorbereitung & Checklisten
* Umfangreiche Tests (Environment & Safety)

**Stärken:**

* Klare Trennung der Modi (kein „versehentlich Live").
* Safety-Layer schützt vor Fehlkonfigurationen und unsicheren Setups.
* Dokumentierter Ablauf für das Hochfahren von Testnet-/Live-Umgebungen.

**Offen / später sinnvoll:**

* Vordefinierte Environment-Profile (z.B. „Tiny Live", „Standard Live").
* Feiner granulierte Safety-Presets pro Exchange/Instrument.

---

## 3. Live Risk Limits (≈ 95%)

**Kernkomponenten:**

* `[live_risk]` Block in `config/config.toml` mit u.a.:

  * `max_daily_loss_abs`, `max_daily_loss_pct`
  * `max_total_exposure_notional`, `max_symbol_exposure_notional`
  * `max_open_positions`, `max_order_notional`
  * `block_on_violation`, `use_experiments_for_daily_pnl`

* `src/live/risk_limits.py`:

  * `LiveRiskConfig`
  * `LiveRiskCheckResult`
  * `LiveRiskLimits.check_orders(...)`
  * `LiveRiskLimits.evaluate_portfolio(...)` (Portfolio-Level, Phase 48)

* Integration in `scripts/preview_live_orders.py` und Live-Flows

**Stärken:**

* Klare, zentral konfigurierte Limits.
* Sowohl **Order-Batch-Level** als auch **Portfolio-Level** Checks.
* Tests decken typische Szenarien und Violations ab.

**Offen / später sinnvoll:**

* Risk-Profile (Conservative / Moderate / Aggressive) als Preset-Schicht über den Roh-Limits.
* Historisierung von Limit-Verletzungen (z.B. für Audits und Post-Mortems).

---

## 4. Order-/Execution-Layer & Exchange-Anbindung (≈ 85%)

**Kernkomponenten:**

* Phase 15 – Order-Layer:

  * `src/orders/base.py`, `src/orders/paper.py`, `src/orders/mappers.py`
  * `docs/ORDER_LAYER_SANDBOX.md`
  * Smoke-Tests für Order-Flows

* Exchange-/Testnet-Anbindung (Phase 38):

  * Trading-/Exchange-Client mit Smoke-Tests
  * Testnet-Integration ins Live-Setup

* Execution-/Pipeline-Logik (Phase 16/16A):

  * Anbindung an Orders, Environment & Safety

**Stärken:**

* Sauber gekapselter Order-Layer (paper vs. exchange).
* Testnet-Setup und Smoke-Tests vorhanden.
* Gute Basis für weitere Exchanges und Order-Typen.

**Offen / später sinnvoll:**

* Erweiterung um weitere Exchanges / Instrumente.
* Erweiterte Order-Typen (z.B. OCO, Bracket-Orders).
* Performance-/Latenz-Tuning für echten 24/7-Live-Betrieb.

---

## 5. Shadow-/Paper-/Testnet-Orchestrierung (≈ 85%)

**Kernkomponenten:**

* Shadow-/Paper-Run-Flow mit Logging.
* Environment-/Config-Pfade für Testnet/Live.
* Governance-Doku mit Stufenmodell (0 → Shadow → Testnet → Live).

**Stärken:**

* Klare Trennung der Stufen.
* Shadow-/Paper-Runs nutzen weitgehend denselben Codepfad wie Testnet/Live.
* Dokumentierte Go-/No-Go-Entscheidungspunkte.

**Offen / später sinnvoll:**

* Komfort-CLI zum Starten/Stoppen und Degradieren/Promoten von Runs.
* Automatisierte „Promotion-Checks" (z.B. basierend auf Research-/Robustness-Ergebnissen).

---

## 6. Run-Logging & Live-Reporting (≈ 90%)

**Kernkomponenten:**

* `src/live/run_logging.py`:

  * `LiveRunLogger`, `LiveRunEvent`, `LiveRunMetadata`
  * Logging von Shadow-/Paper-/Live-Events
* Integration in Shadow-/Live-Sessions
* Nutzung als Grundlage für Run-Analysen und Incident-Handling

**Stärken:**

* Strukturierte Events statt reiner Log-Textwüste.
* Einfache Filterbarkeit und spätere Auswertbarkeit.
* Guter Hook für Dashboards und Monitoring-Tools.

**Offen / später sinnvoll:**

* Standard-Views (z.B. fertige Notebooks oder HTML-Berichte auf Run-Basis).
* Bessere Verzahnung mit Runbooks („Welche Logs bei welchem Incident zuerst prüfen?").

---

## 7. Live-/Portfolio-Monitoring & Risk Bridge (≈ 95%)

**Kernkomponenten (Phase 48):**

* `src/live/portfolio_monitor.py`:

  * `LivePositionSnapshot`
  * `LivePortfolioSnapshot`
  * `LivePortfolioMonitor`
  * Korrekte Side-Erkennung (negative size → `short`)

* `src/live/risk_limits.py`:

  * `evaluate_portfolio(snapshot: LivePortfolioSnapshot)` mit:

    * Total-Exposure-Checks
    * Symbol-Exposure-Checks
    * Open-Position-Checks
    * Einbindung von PnL-Metriken, sofern verfügbar

* `scripts/preview_live_portfolio.py`:

  * Standard-Run mit Risk-Check:

    ```bash
    python scripts/preview_live_portfolio.py --config config/config.toml
    ```

  * Ohne Risk-Check:

    ```bash
    python scripts/preview_live_portfolio.py --config config/config.toml --no-risk
    ```

  * JSON-Ausgabe:

    ```bash
    python scripts/preview_live_portfolio.py --config config/config.toml --json
    ```

  * Mit Custom Starting-Cash:

    ```bash
    python scripts/preview_live_portfolio.py --config config/config.toml --starting-cash 20000.0
    ```

* Tests:

  * `tests/test_live_portfolio_monitor.py` (9 Tests)
  * `tests/test_live_risk_limits_portfolio_bridge.py` (7 Tests)
  * `tests/test_preview_live_portfolio.py` (9 Tests)

* Doku:

  * `docs/PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md`
  * `docs/CLI_CHEATSHEET.md` – Abschnitt 11.1 „Portfolio Monitoring"

**Stärken:**

* Konsistente Portfolio-Sicht auf Live-/Shadow-Level.
* Direkte Kopplung an LiveRiskLimits, ohne Orders erzeugen zu müssen.
* Text- & JSON-Ausgabe erleichtern sowohl manuelle Kontrolle als auch Tool-Integration.

**Offen / später sinnvoll:**

* Persistente Historie von Portfolio-Snapshots (z.B. für Zeitreihen-Analysen).

---

## 7a. Live Alerts & Notifications (≈ 95%)

**Kernkomponenten (Phase 49 + 50):**

* `src/live/alerts.py`:

  * `AlertLevel` (INFO, WARNING, CRITICAL)
  * `AlertEvent` Dataclass
  * `AlertSink` Protocol mit Standard-Implementierungen:
    * `LoggingAlertSink` (Python-Logging)
    * `StderrAlertSink` (stderr)
    * `WebhookAlertSink` (generische HTTP-Webhooks, Phase 50)
    * `SlackWebhookAlertSink` (Slack-Webhooks, Phase 50)
    * `MultiAlertSink` (Weiterleitung an mehrere Sinks)
  * `LiveAlertsConfig` für Konfiguration
  * `build_alert_sink_from_config()` Factory

* `src/live/risk_limits.py`:

  * `_emit_risk_alert()` Helper-Methode
  * Integration in `check_orders()` und `evaluate_portfolio()`

* Konfiguration in `config/config.toml`:

  ```toml
  [live_alerts]
  enabled = true
  min_level = "warning"
  sinks = ["log", "slack_webhook"]
  webhook_urls = []
  slack_webhook_urls = ["https://hooks.slack.com/services/..."]
  webhook_timeout_seconds = 3.0
  ```

* Tests:

  * `tests/test_live_alerts.py` (erweitert um Webhook/Slack-Tests, Phase 50)
  * `tests/test_live_risk_alert_integration.py` (erweitert um Webhook-Integration, Phase 50)

* Doku:

  * `docs/PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`
  * `docs/PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md` (Phase 50)

**Stärken:**

* Leichtgewichtiges, erweiterbares Alert-System.
* Protocol-basiertes Sink-Interface für einfache Erweiterung.
* Automatische Alert-Emission bei Risk-Violations.
* Nicht-blockierend: Alerts dürfen den Live-Betrieb nicht stören.
* **Phase 50**: Externe Webhook- und Slack-Integration für sofortige Benachrichtigungen.

**Offen / später sinnvoll:**

* Alert-Deduplizierung und Throttling.
* Persistente Alert-Historie.
* Erweiterte Slack-Formatierung (Rich Text, Buttons).
* Weitere Sinks (E-Mail, Discord, PagerDuty).

---

## 8. Governance, Runbooks & Checklisten (≈ 90%)

**Kernkomponenten (Phase 25 ff.):**

* `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
* `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`
* `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`
* `docs/LIVE_READINESS_CHECKLISTS.md`
* Deployment-/Stufenmodelle, Incident-Runbooks (PnL-Divergenzen, Data-Gaps, System-Pause, etc.)

**Stärken:**

* Klar definierte Rollen & Entscheidungen.
* Verfahrensanweisungen für typische Incidents.
* Checklisten für Stufenübergänge (0 → Shadow → Testnet → Live).

**Offen / später sinnvoll:**

* Ergänzungen basierend auf echten Incidents & Learnings.
* Engere Verknüpfung mit Monitoring-Outputs (Konkrete Aufrufe von CLI-Scripts in Runbooks).

**Portfolio-basierte Promotions:**

Portfolio-basierte Promotions von Research → Testnet/Live folgen dem in [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) beschriebenen Ablauf (Phase 54).

**Incident-Drills (Phase 56):**

Incident-Drills sind etabliert und werden regelmäßig durchgeführt, um Runbooks, Tooling und Alerts praktisch zu validieren. Die Drill-Szenarien sind in [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) dokumentiert, alle durchgeführten Drills werden in [`INCIDENT_DRILL_LOG.md`](INCIDENT_DRILL_LOG.md) protokolliert.

---

## 9. CLI-Tooling für Live-/Testnet-Operationen (≈ 95%)

**Kernkomponenten:**

* `scripts/live_ops.py` – Zentrales Live-Ops CLI (Phase 51):
  * `live_ops orders` – Order-Preview & Risk-Check (Wrapper um `preview_live_orders.py`)
  * `live_ops portfolio` – Portfolio-Monitoring & Risk-Bridge (Wrapper um `preview_live_portfolio.py`)
  * `live_ops health` – Health-Check für Live-/Testnet-Setup (Config, Exchange, Alerts, Live-Risk)
* `scripts/preview_live_orders.py` – Order-Preview & Risk-Check (bleibt funktionsfähig).
* `scripts/preview_live_portfolio.py` – Portfolio-Monitoring & Risk-Bridge (bleibt funktionsfähig).
* Diverse Demo-/Support-Scripts (Registry, Research, Backtests).
* `docs/CLI_CHEATSHEET.md` mit eigenem Abschnitt für Live-Ops CLI.

**Stärken:**

* **Phase 51**: Zentrales Operator-Cockpit (`live_ops.py`) bündelt wichtigste Kommandos.
* Klare, fokussierte Tools für kritische Operator-Fragen („Was wird gehandelt?", „Wie sieht das Portfolio aus?").
* Einheitliches Config-Modell über `config/config.toml`.
* Health-Check für schnelle Konsistenzprüfung vor Live-Sessions.

**Offen / später sinnvoll:**

* Presets/Profiles für Standard-Workflows (z.B. „Pre-Open-Check", „End-of-Day-Check").
* Erweiterte Health-Checks (z.B. Exchange-Connectivity-Tests, Alert-Delivery-Tests).
* Health-Check-Scheduling (automatische Checks via Cron/Scheduler).

**Siehe:** [PHASE_51_LIVE_OPS_CLI.md](PHASE_51_LIVE_OPS_CLI.md) für Details.

---

## 10. Gesamtbewertung & nächste Schritte

Der Live-/Testnet-Track von Peak_Trade ist aktuell auf einem Reifegrad von **≈ 95%**:

* Technisch weitgehend komplett.
* Safety- und Governance-Schicht etabliert.
* Monitoring, Risk-Bridge und Alert-System fertig (inkl. Webhook/Slack-Sinks, Phase 50).
* Zentrales Live-Ops CLI für Operatoren (Phase 51).
* Umfassendes Research→Live Playbook für Portfolio-Promotions (Phase 54).

**Naheliegende nächste Schritte:**

1. Alert-Enhancements:

   * Alert-Deduplizierung und Throttling.
   * Persistente Alert-Historie für Audits.
   * E-Mail-Sink (SMTP), PagerDuty/Discord-Integration.

2. Erweiterung der Exchange-/Order-Funktionalität:

   * Zusätzliche Börsen / Märkte.
   * Komplexere Order-Typen (OCO, Bracket).
   * Performance-/Resilienz-Optimierungen.

3. Dashboards & Visualisierung:

   * HTML-Dashboards für Live-Monitoring.
   * Interaktive Portfolio-Views.

---

## Änderungshistorie

| Datum      | Änderung                                                    |
|------------|-------------------------------------------------------------|
| 2025-12-07 | Update nach Abschluss Phase 54 (Research→Live Playbook)    |
| 2025-12-07 | Update nach Abschluss Phase 51 (Live-Ops CLI)              |
| 2025-12-07 | Update nach Abschluss Phase 50 (Webhook & Slack-Sinks für Alerts)|
| 2025-12-07 | Update nach Abschluss Phase 49 (Live Alerts & Notifications)|
| 2025-12-07 | Initiale Version nach Abschluss Phase 48                    |

---

Dieses Dokument sollte regelmäßig aktualisiert werden, sobald neue Live-Phasen abgeschlossen sind oder größere Änderungen im Live-/Testnet-Setup erfolgen.
