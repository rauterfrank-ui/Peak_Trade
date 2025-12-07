# Peak_Trade – Projekt-Status Overview (Phasen 1–49)

Dieses Dokument beschreibt den aktuellen Gesamtstatus von **Peak_Trade**
(Phasen **1–49**, inkl. Research-/Portfolio-Track und Live-/Testnet-Track).

Ziel:

* Eine **prozentuale Einschätzung** je Bereich
* Klarheit, **was schon stabil ist** und **was noch fehlt**
* Grundlage für zukünftige Roadmaps (Phase 50+)

> **Hinweis:** Prozentwerte sind bewusst als **qualitative Reifegrade** zu verstehen
> (Architektur, Codequalität, Tests, Doku, Operational Readiness), nicht als „fertig/nie-ändern".

---

## 1. Gesamtstatus in Prozent

### 1.1 High-Level Übersicht

| Bereich                         | Status    | Kommentar                                                                                |
| ------------------------------- | --------- | ---------------------------------------------------------------------------------------- |
| Data & Market Access            | 95%       | Data-Pipeline, Loader, Normalizer, Cache, Kraken-Integration stabil                      |
| Backtest & Simulation           | 92%       | BacktestEngine, Stats, Registry-Integration, Reporting v2                                |
| Strategy & Portfolio Layer      | 88%       | Einzel-Strategien, Portfolio-Layer, Portfolio-Robustness, Recipes                        |
| Risk & Safety (Research + Live) | 90%       | Risk-Metriken, Limits, LiveRiskLimits, Safety-Concept                                    |
| Research & Experiments          | 90%       | Registry, Sweeps, Research-CLI, Pipeline v2, Portfolio-Level-Robustness                  |
| Live-/Testnet & Operations      | 91%       | Environment & Safety, Orders, Exchange, Portfolio-Monitor, Alerts, Runbooks              |
| Reporting, Monitoring & CLI     | 88%       | Reports, Plots, Research-Reports, Live-Preview-Scripts, Portfolio-/Order-CLI             |
| Documentation & Governance      | 86%       | Governance & Safety-Doku, Live-Runbooks, Phasen-Docs, Status-Docs                        |
| Developer-Experience & Tooling  | 80%       | CLI-Skripte, strukturierte Prompts, Workflow mit AI-Tools, aber noch Ausbaupotenzial     |
| **Gesamtprojekt (Phasen 1–49)** | **≈ 88%** | Starkes Fundament, produktionsnahe Architektur, offene Themen v.a. bei Komfort & Scaling |

---

## 2. Data & Market Access (~95%)

**Relevante Phasen:** frühe Basis-Phasen (1–5), Data-Layer-Ausbau

**Kernkomponenten:**

* `src/data/loader.py`, `normalizer.py`, `cache.py`, `kraken.py`
* Demo-/Pipeline-Skripte (z.B. `demo_data_pipeline.py`)
* Nutzung von `pandas`, `numpy`, `pyarrow`, Parquet etc.
* Saubere Trennung zwischen:

  * Rohdaten-Load
  * Normalisierung / Cleaning
  * Caching / Persistenz

**Stärken:**

* Stabile Data-Pipeline für Research & Backtests.
* Kraken-/Market-Access als Referenz-Exchange implementiert.
* Data-Layer fügt sich gut in Registry, Backtest & Research-Pipeline ein.

**Offene/optionale Themen:**

* Weitere Exchanges / Feeds (z.B. CME, weitere Crypto-Exchanges).
* Mehr Data-Quality-Checks, Outlier-Handling, Holiday-Kalender, etc.
* Fortgeschrittene Features wie Regime-Erkennung im Data-Layer (später).

> **Reifegrad:** **ca. 95%** – der Data-Layer ist produktionsnah und kann als Referenz gelten.

---

## 3. Backtest & Simulation (~92%)

**Relevante Phasen:** Backtest-Engine, Stats, Registry-Integration, Reporting-Phasen (z.B. 26, 30, 43)

**Kernkomponenten:**

* `src/backtest/engine.py` – zentrale BacktestEngine
* `src/backtest/stats.py` – Metriken (Returns, Drawdown, Sharpe, etc.)
* Registry-/Experiment-Integration (Backtests als erste Klasse in der Research-Pipeline)
* Reporting:

  * `src/reporting/backtest_report.py`
  * `src/reporting/experiment_report.py`
  * `src/reporting/plots.py`
* CLI-Skripte:

  * `scripts/generate_backtest_report.py`
  * `scripts/generate_experiment_report.py`

**Stärken:**

* Realistische Backtests mit Portfolio-Fähigkeiten.
* Enge Integration mit Registry & Research-CLI.
* Berichte mit Kennzahlen, Plots und Trade-Statistiken.

**Offene Themen:**

* Noch mehr „Corner-Case"-Tests (Exotische Fee-Modelle, Slippage-Szenarien, Illiquidität).
* Tooling, um Backtest-Szenarien paketiert in Presets abzulegen.
* Performance-Tuning für extrem große Backtest-Sets (Scale-Out).

> **Reifegrad:** **ca. 92%** – stabiler Kern, gut getestet und tief integriert.

---

## 4. Strategy & Portfolio Layer (~88%)

**Relevante Phasen:** Strategie-Basis, Portfolio-Layer (Phase 26), Portfolio-Robustheit (Phase 47), Recipes & Presets

**Kernkomponenten:**

* Single-Strategie-Layer:

  * `src/strategies/*.py` (z.B. MA-Crossover, Trend-Following, RSI-Reversion)
* **Portfolio-Layer (Research/Backtest):**

  * Kombination mehrerer Strategien in Portfolios
  * Gewichtung & Aggregation auf Portfolio-Ebene
* **Phase 47 – Portfolio-Level Robustness:**

  * `src/experiments/portfolio_robustness.py`
  * `src/reporting/portfolio_robustness_report.py`
  * `scripts/run_portfolio_robustness.py`
  * Portfolio-basierte Metriken, Monte-Carlo & Stress-Tests
* **Portfolio Recipes & Presets:**

  * `config/portfolio_recipes.toml`
  * `src/experiments/portfolio_recipes.py`
  * `tests/test_portfolio_recipes.py`
  * CLI-Integration in `research_cli.py` (Preset + Override)

**Stärken:**

* Strategien sind nicht nur isoliert, sondern **portfolio-fähig**.
* Portfolio-Robustheit (Monte-Carlo + Stress) ist auf Portfolio-Level angehoben.
* Recipes & Presets ermöglichen reproduzierbare, benannte Portfolio-Konfigurationen.

**Offene Themen:**

* Größere Strategie-Bibliothek (mehr Styles, mehr Märkte).
* Bessere Trennung zwischen „Einsteiger-Strategien" und „Advanced/Research-Strategien".
* Erweiterte Portfolio-Optimierungs-Ansätze (z.B. Risk-Parity, CVaR-Minimierung, etc.).

> **Reifegrad:** **ca. 88%** – funktional sehr stark, Bibliothek und Komfort können weiter ausgebaut werden.

---

## 5. Risk & Safety (Research + Live) (~90%)

**Relevante Phasen:** verschiedene Risk-/Governance-Phasen, LiveRiskLimits, Phase 25, Phase 49

**Kernkomponenten:**

* Research-Risk:

  * Metriken, Drawdown-Analysen, Stress- & Monte-Carlo-Szenarien im Research-Track.
* Live-Risk-Limits:

  * `config/config.toml` – `[live_risk]` Block mit:

    * `max_daily_loss_abs`, `max_daily_loss_pct`
    * `max_total_exposure_notional`, `max_symbol_exposure_notional`
    * `max_open_positions`, `max_order_notional`
    * `block_on_violation`, `use_experiments_for_daily_pnl`
  * `src/live/risk_limits.py`:

    * `LiveRiskConfig`, `LiveRiskCheckResult`, `LiveRiskLimits`
    * `check_orders(...)`, `evaluate_portfolio(...)` (Portfolio-Level)
* Governance & Safety:

  * `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
  * `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`
  * `docs/LIVE_READINESS_CHECKLISTS.md`
  * `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`

**Stärken:**

* Risk ist **nicht nachträglich draufgestöpselt**, sondern zentraler Bestandteil des Designs.
* Harte Limits vor Order-Ausführung + auf Portfolio-Level im Live-Bereich.
* Research-Track arbeitet schon mit Stress- und Robustheits-Methoden.

**Offene Themen:**

* Risk-Profile (Conservative/Moderate/Aggressive) als zusätzliche Abstraktion über Roh-Limits.
* Einheitliche Risk-Language zwischen Research-Reports, Live-Monitoring und Governance-Doku.
* Mehr Automatisierung Richtung „Risk-Dashboards".

> **Reifegrad:** **ca. 90%** – konzeptionell stark und tief integriert, eher Feinschliff & UX-Themen offen.

---

## 6. Research & Experiments (~90%)

**Relevante Phasen:** Registry-/Experiment-Phasen, Research-CLI, Pipeline v2, Portfolio-Robustness (47), Recipes

**Kernkomponenten:**

* Experiment-/Registry-Layer:

  * Speicherung von Backtests, Sweeps, Parametern, Metriken.
  * Demo-Skripte und Tests für Registry-Backtests.
* **Research-Pipeline v2 (Phase 43):**

  * Orchestrierung:

    * Sweep → Report → Promote → Walk-Forward → Monte-Carlo → Stress-Tests
* Research-CLI:

  * `scripts/research_cli.py`
  * Subcommands für Sweeps, Reports, Research-Pipelines, Portfolios
* Portfolio-Level Research:

  * Phase 47 – Portfolio-Robustness
  * Portfolio-Recipes & Presets

**Stärken:**

* „Research wie in einem Mini-Quant-Lab": Sweeps, Promotion, Out-of-Sample, Monte-Carlo, Stress.
* CLI-Workflows sind automatisierbar und skriptbar.
* Portfolio-Robustheit direkt in die Research-Pipeline integriert.

**Offene Themen:**

* Mehr Standard-Workflows dokumentieren („Wie finde ich neue stabile Portfolios in 5 Schritten?").
* Integration mit externen Tracking-Tools (MLflow, Weights & Biases – nur optional).
* Mehr Komfortfunktionen (z.B. automatische Best-Config-Snapshots für bestimmte Risk-Profile).

> **Reifegrad:** **ca. 90%** – Research-Track ist auf sehr hohem Niveau, eher Komfort & Library-Ausbau sind offen.

---

## 7. Live-/Testnet & Operations (~91%)

**Relevante Phasen:** Environment & Safety (17), Order-/Exchange-Layer (15, 38), Live-Monitoring (48), Alerts (49), Governance (25), Live-Status-Doku

**Kernkomponenten:**

* Environment & Safety:

  * `src/core/environment.py`
  * `src/live/safety.py`
  * Stufenmodell (Shadow → Testnet → Live)
  * `docs/LIVE_TESTNET_PREPARATION.md`
* Order-/Exchange-Layer:

  * `src/orders/base.py`, `src/orders/paper.py`, `src/orders/mappers.py`
  * `docs/ORDER_LAYER_SANDBOX.md`
  * Exchange-/Testnet-Anbindung (z.B. Phase 38)
* Run-Logging:

  * `src/live/run_logging.py`
  * Run-Events & Run-Metadaten für Shadow-/Paper-/Live-Runs
* Live-Portfolio-Monitoring (Phase 48):

  * `src/live/portfolio_monitor.py`
  * `scripts/preview_live_portfolio.py`
  * Portfolio-Snapshots + Risk-Evaluation
* Live-Alerts & Notifications (Phase 49):

  * `src/live/alerts.py`
  * Alert-Level, AlertEvent, Logging-/Stderr-/Multi-Sinks
  * `LiveAlertsConfig` + Config-Integration (`[live_alerts]`)
  * Alerts in `LiveRiskLimits.check_orders/evaluate_portfolio`
* Governance & Status:

  * `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
  * `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`
  * `docs/LIVE_READINESS_CHECKLISTS.md`
  * `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`
  * `docs/LIVE_TESTNET_TRACK_STATUS.md` (Track-Status ≈ 91%)

**Stärken:**

* Live-/Testnet-Track **konzeptionell geschlossen**:

  * Safety → Risk → Orders → Monitoring → Alerts → Runbooks
* Monitoring & Alerts sind **read-only**, stören den Flow nicht, melden aber Probleme.
* Doku & Runbooks machen das Ganze **operational nutzbar**.

**Offene Themen:**

* Externe Notification-Sinks (Slack/Webhook/Mail).
* Konsolidierter „Live-Ops CLI" mit Subcommands (statt mehrere Einzel-Scripts).
* Langfristige Historisierung von Portfolio-Snapshots & Alerts.

> **Reifegrad:** **ca. 91%** – sehr weit, Live-System ist bewusst konservativ (kein Autopilot), aber technisch reif.

---

## 8. Reporting, Monitoring & CLI (~88%)

**Relevante Phasen:** Reporting-Phasen (30, 43, 47), Monitoring-Phasen (32, 48, 49), CLI-Cheatsheets

**Kernkomponenten:**

* Reporting:

  * `src/reporting/base.py`, `backtest_report.py`, `experiment_report.py`, `portfolio_robustness_report.py`
  * Plots mit `src/reporting/plots.py`
  * Reports für:

    * Einzel-Backtests
    * Sweeps / Experiments
    * Portfolio-Robustness
* Live-/Monitoring-CLI:

  * `scripts/preview_live_orders.py`
  * `scripts/preview_live_portfolio.py`
* Research-CLI & Tools:

  * `scripts/research_cli.py`
  * `scripts/run_portfolio_robustness.py`
* Dokumentation:

  * `docs/CLI_CHEATSHEET.md` – zentrale Übersicht über wichtige CLI-Commands.

**Stärken:**

* Einheitlicher Reporting-Stil über Research & Backtests.
* Klar getrennte CLIs für Operator-Fragen (Orders / Portfolio) und Research-Fragen.
* Cheatsheet-Doku erleichtert Einstieg und Tages-Workflow.

**Offene Themen:**

* Konsolidiertes CLI-Tool (z.B. `peak_trade` oder `live_ops`) als „Meta-Entry-Point".
* HTML-/Dashboard-Frontends für ausgewählte Reports/Monitoring-Ansichten.
* Erweiterte Monitoring-Views (Equity, Drawdown, Risk-Events in „quasi-real-time").

> **Reifegrad:** **ca. 88%** – viel Funktionalität, noch Luft nach oben bei UX & Konsolidierung.

---

## 9. Documentation & Governance (~86%)

**Relevante Phasen:** Governance & Safety (Phase 25), Live-Doku, Phasen-Reports, Status-Dokus

**Kernkomponenten (Auszug):**

* Governance & Safety:

  * `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
  * `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`
* Runbooks & Checklisten:

  * `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`
  * `docs/LIVE_READINESS_CHECKLISTS.md`
* Live-/Testnet-Status:

  * `docs/LIVE_TESTNET_TRACK_STATUS.md`
* Research & Backtest:

  * Verschiedene Phasen-Dokus (`PHASE_XX_*.md`)
  * Reports & Overviews
* Gesamt-Projekt:

  * Dieses Dokument: `docs/PEAK_TRADE_STATUS_OVERVIEW.md` (Status Phasen 1–49)

**Stärken:**

* Governance & Safety sind explizit festgehalten.
* Live-/Testnet-Track hat ein eigenes Status-Dokument.
* Viele Phasen haben eigene Abschlussberichte & Doku-Snippets.

**Offene Themen:**

* Eine noch stärkere **Top-Down-Architekturübersicht** (Architektur-Diagramme, Modul-Maps).
* Trennung in:

  * „Operator-Handbuch"
  * „Developer-Handbuch"
  * „Quant-/Research-Handbuch"
* Index / Inhaltsverzeichnis für die wichtigsten Docs.

> **Reifegrad:** **ca. 86%** – viel Substanz, aber die „Meta-Struktur" kann noch besser werden.

---

## 10. Developer Experience & Tooling (~80%)

**Relevante Bausteine:**

* Python-Projektstruktur (`src/`, `tests/`, `docs/`, `scripts/`, `config/`).
* Test-/CI-Mindset (viele Tests, klare Phasen-Commits).
* CLI-basierte Workflows:

  * Research-CLI, Preview-Skripte, Demo-Skripte.
* AI-gestützter Entwicklungs-Workflow:

  * Strukturierte Prompt-Blöcke für Claude/Cursor.
  * Konsistenter „Peak_Trade-Workflow" über mehrere Tools.

**Stärken:**

* Solide, nachvollziehbare Projektstruktur.
* Tests sind fester Bestandteil der Entwicklung (nicht optional).
* AI-Tools sind **integriert** (nicht nur „ein bisschen Copy-Paste").

**Offene Themen:**

* (Optional) Dev-Container / Docker-Setup, um Setup-Aufwand weiter zu senken.
* CI-Pipeline (GitHub Actions o.ä.) mit automatischem Testing / Linting.
* Mehr „Developer-Guides" (z.B. „How to add a new strategy", „How to add a new exchange").

> **Reifegrad:** **ca. 80%** – sehr gut nutzbar, aber mit viel Potenzial für „Luxury Dev Experience".

---

## 11. Highlights der letzten Phasen (47–49)

Die Phasen **47–49** haben das System auf ein neues Level gehoben:

1. **Phase 47 – Portfolio-Level Robustness**

   * Portfolio-Robustheit (Metriken, Monte-Carlo, Stress) auf Portfolio-Ebene.
   * Reports für Portfolios statt nur für Einzel-Strategien.
2. **Portfolio Recipes & Presets**

   * `config/portfolio_recipes.toml` + Loader + Research-CLI-Integration.
   * Benannte Portfolio-Configs mit Defaults für MC & Stress.
3. **Phase 48 – Live Portfolio Monitoring & Risk Bridge**

   * Live-Portfolio-Snapshots mit Notional, PnL, Symbol-Exposure.
   * Portfolio-Level Risk-Evaluation im Live-Bereich.
   * CLI `scripts/preview_live_portfolio.py`.
4. **Phase 49 – Live Alerts & Notifications**

   * Zentrales Alert-System (`src/live/alerts.py`) mit Logging-/Stderr-Sinks.
   * Automatische Alerts bei Risk-Violations (Orders & Portfolio).
   * Integration in LiveRiskLimits und Live-/Testnet-Status-Doku.

Diese Bausteine schließen die Lücke zwischen:

* **Research-Robustness** (Backtests, Sweeps, Monte-Carlo, Stress)
* und **Live-/Testnet-Safety & Monitoring** (Portfolio, Risk, Alerts, Runbooks)

---

## 12. Empfohlene nächste Schritte (Phase 50+)

Basierend auf dem aktuellen Stand (≈ 88% Gesamt-Reifegrad) bieten sich folgende nächste Phasen an:

1. **Externe Notifications & Integrationen (Phase 50+)**

   * Webhook-/Slack-/Mail-Sinks für das Alert-System.
   * Basis-Throttling / Deduplizierung von Alerts.
2. **Konsolidierter Live-Ops-CLI**

   * `scripts/live_ops.py` mit Subcommands:

     * `live_ops orders`
     * `live_ops portfolio`
     * `live_ops health`
   * Ein einziger Entry-Point für Operatoren.
3. **Architektur & Developer-Guides**

   * Ein „Architecture Overview"-Dokument mit Diagrammen.
   * Developer-Guides (Strategie hinzufügen, Exchange hinzufügen, neues Risk-Feature hinzufügen).
4. **Weitere Strategie-/Portfolio-Library**

   * Mehr Strategien, mehr Märkte.
   * Portfolio-Recipes für verschiedene Risk-Profile.
5. **Optionale Dashboards**

   * HTML-/Notebook-Dashboards für:

     * Research-Results
     * Live-Monitoring (Equity/Drawdown, Portfolio-Exposure, Risk-Events)

---

## 13. Änderungshistorie dieses Dokuments

| Datum      | Commit    | Änderung                                                        |
|------------|-----------|-----------------------------------------------------------------|
| 2025-12-07 | f015c8a   | Erste Version Live-/Testnet-Status (`LIVE_TESTNET_TRACK_STATUS.md`) |
| 2025-12-07 | c63ea36   | Abschluss Phase 49 – Live Alerts & Notifications                |
| 2025-12-07 | (aktuell) | Erstellung `PEAK_TRADE_STATUS_OVERVIEW.md` (Phasen 1–49)        |

---

**Peak_Trade** – Ein produktionsnahes Trading-Research-Framework mit integrierter Safety-First-Architektur.
