# PEAK_TRADE – Global Overview (Phases 1–40)

> **Zweck:**
> Dieses Dokument gibt einen **High-Level-Überblick über alle Phasen 1–40**, mit Fokus auf den aktuellen Stand und insbesondere den **Live-/Testnet-Track**.
> Detail-Dokumente (z.B. `PHASE_30_*.md`, `PHASE_37_*.md`, `GOVERNANCE_AND_SAFETY_*.md`) bleiben die Quelle für Details.

---

## 1. Big Picture – Tracks & Status

Wir gliedern Peak_Trade grob in folgende Tracks:

* 🧱 **Core Research & Backtest** (Data, Backtest-Engine, Strategies, Portfolio)
* 🛡️ **Risk, Governance & Safety**
* 🧪 **Testnet & Live-Vorbereitung**
* 📊 **Reporting, Monitoring & Tooling**
* 🚀 **Exchange & Deployment (zukünftige Phasen)**

**Gesamtstatus (ungefähr):**

* Core Research & Backtest: **~80–85 %**
* Risk, Governance & Safety: **~80–90 %**
* Testnet & Live-Vorbereitung (bis Phase 37): **~75 %**
* Reporting & Monitoring: **~70–80 %**
* Exchange & Deployment (ab Phase 38): **geplant**

---

## 2. Phase Map – Phasen 1–40 in Clustern

Die exakten Detail-Beschreibungen der frühen Phasen (1–17) sind in
[`docs/PEAK_TRADE_OVERVIEW_PHASES_1_17.md`](PEAK_TRADE_OVERVIEW_PHASES_1_17.md) dokumentiert.
Hier eine kompakte Phase-Karte:

| Phase(n) | Cluster                                        | Track                        | Status     |
| -------- | ---------------------------------------------- | ---------------------------- | ---------- |
| 1–4      | Data-Layer & Backtest-Basis                    | Core Research & Backtest     | ✅ done     |
| 5–9      | Strategy-Layer, erste Risk-Hooks               | Core + Risk                  | ✅ done     |
| 10–14    | Backtest-Engine-Vertiefung, Stats, Experiments | Core Research & Backtest     | ✅ done     |
| 15       | Order-Layer (Sandbox & Routing)                | Core + Live-Vorbereitung     | ✅ done     |
| 16       | Execution-Layer                                | Live-/Execution-Core         | ✅ done     |
| 17       | Environment & Safety                           | Risk & Safety                | ✅ done     |
| 18–22    | Research/Strategy-Track (Erweiterungen)        | Research & Strategy          | 🔄 mixed   |
| 23       | Live-/Testnet-Blueprint                        | Live-/Testnet-Architektur    | ✅ done     |
| 24       | Shadow Execution                               | Research + Live-Brücke       | ✅ done     |
| 25       | Governance & Safety-Dokumentation              | Governance & Safety          | ✅ done     |
| 26       | Portfolio-Strategie-Layer                      | Research & Portfolio         | ✅ done     |
| 27–29    | Erweiterungen Portfolio/Experimente            | Research & Portfolio         | 🔄 partial |
| 30       | Reporting & Visualisierung                     | Reporting                    | ✅ done     |
| 31       | Shadow-/Paper-Flow-Verfeinerung                | Live-/Shadow-Track           | ✅ done     |
| 32       | Shadow/Paper Run-Logging                       | Monitoring & Logging         | ✅ done     |
| 33       | Live-/Shadow-Run-Monitoring & CLI              | Monitoring & CLI             | ✅ done     |
| 34       | Alerts & Web-UI                                | Monitoring & Alerting        | ✅ done     |
| 35       | Testnet Exchange Integration                   | Testnet & Exchange           | ✅ done     |
| 36       | Config/Test-Infra-Hardening                    | Infra & Tooling              | ✅ done     |
| 37       | Testnet-Orchestration & Limits                 | Testnet & Live-Prep          | ✅ done     |
| 38       | **Exchange-Anbindung v0 (Testnet)**            | Live-/Exchange               | 📝 geplant |
| 39       | **Live-Deployment-Playbook & Runbooks**        | Governance, Ops & Deployment | 📝 geplant |
| 40       | **Monitoring- & Observability-Dashboards**     | Monitoring & Ops             | 📝 geplant |

Die Phasen 38–40 sind **konkret als nächste Live-/Testnet-Schritte definiert** (siehe Abschnitt 4).

---

## 3. Wichtige Live-/Testnet-relevante Phasen (Rückblick)

### 3.1 Phase 15 – Order-Layer (Sandbox & Routing)

* **Ziel:**
  Trennung von Signal-Generierung und Order-Ausführung; einheitlicher Order-Layer zur Anbindung von Paper-/Sandbox- und später Exchange-Executors.

* **Kernelemente:**
  * `src/orders/base.py` – `OrderRequest`, `OrderFill`, `OrderExecutionResult`, `OrderExecutor`-Protocol
  * `src/orders/paper.py` – `PaperOrderExecutor`, `PaperMarketContext`
  * CLI: `scripts/paper_trade_from_orders.py`, `scripts/preview_live_orders.py`

* **Bedeutung:**
  Grundlage, auf der Phase 38 (Exchange-Anbindung v0) direkt aufbauen kann.

---

### 3.2 Phase 16 – Execution-Layer

* **Ziel:**
  Saubere Ausführungspipeline von Signalen → Orders → Fills, mit klaren Schnittstellen für unterschiedliche Execution-Modes.

* **Kernelemente:**
  * `src/execution/pipeline.py` – Execution-Pipeline
  * Kopplung an Order-Layer (`OrderExecutor`)
  * Hooks für Logging, Risk-Checks, Environment-Checks

* **Bedeutung:**
  „Rückgrat" der Trade-Ausführung, welches später nur noch um Exchange-Executors ergänzt werden muss.

---

### 3.3 Phase 17 – Environment & Safety

* **Ziel:**
  Ein **zentrales Environment-Modell** (`paper`, `shadow`, `testnet`, `live`) plus Safety-Checks.

* **Kernelemente:**
  * `src/core/environment.py` – `TradingEnvironment`, `EnvironmentConfig`
  * `src/live/safety.py` – `SafetyGuard`, Safety-Gates

* **Bedeutung:**
  Pflichtgrundlage für echte Exchange-Anbindung (Phase 38), um Unfälle zu vermeiden.

* **Dokumentation:** [`docs/PHASE_25_GOVERNANCE_SAFETY_IMPLEMENTATION.md`](PHASE_25_GOVERNANCE_SAFETY_IMPLEMENTATION.md)

---

### 3.4 Phase 23 – Live-Testnet-Blueprint

* **Ziel:**
  Ein **konzeptioneller Blueprint**, wie Peak_Trade die Stufen `research → shadow → testnet → live` durchläuft.

* **Dokumentation:** [`docs/PHASE_23_LIVE_TESTNET_BLUEPRINT.md`](PHASE_23_LIVE_TESTNET_BLUEPRINT.md)

---

### 3.5 Phase 25 – Governance & Safety-Dokumentation

* **Ziel:**
  Governance, Policies und Runbooks **explizit dokumentieren**.

* **Kernelemente:**
  * [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md)
  * [`docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`](SAFETY_POLICY_TESTNET_AND_LIVE.md)
  * [`docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md)
  * [`docs/LIVE_READINESS_CHECKLISTS.md`](LIVE_READINESS_CHECKLISTS.md)

* **Bedeutung:**
  Grundlage, auf der Phase 39 (Live-Deployment-Playbook) aufbauen wird.

---

### 3.6 Phase 30 – Reporting & Visualization

* **Ziel:**
  Standardisierte Reports für Backtests & Experimente, inkl. Plots und Kennzahlen.

* **Kernelemente:**
  * `src/reporting/base.py`, `src/reporting/plots.py`
  * `src/reporting/backtest_report.py`, `src/reporting/experiment_report.py`
  * `scripts/generate_backtest_report.py`, `scripts/generate_experiment_report.py`

* **Dokumentation:** [`docs/PHASE_30_REPORTING_AND_VISUALIZATION.md`](PHASE_30_REPORTING_AND_VISUALIZATION.md)

---

### 3.7 Phase 32 – Shadow/Paper Run-Logging

* **Ziel:**
  Laufende Runs strukturiert loggen – inklusive PnL, Risk-Infos, Orders.

* **Kernelemente:**
  * `src/live/run_logging.py` – `LiveRunLogger`, `LiveRunMetadata`, `LiveRunEvent`

* **Dokumentation:** [`docs/PHASE_32_SHADOW_PAPER_LOGGING_AND_REPORTING.md`](PHASE_32_SHADOW_PAPER_LOGGING_AND_REPORTING.md)

---

### 3.8 Phase 33 – Monitoring & CLI-Dashboards

* **Ziel:**
  Lightweight-Monitoring für Live-/Shadow-Runs per CLI.

* **Kernelemente:**
  * `src/live/monitoring.py` – `LiveRunSnapshot`, `load_run_snapshot()`, `render_summary()`
  * `scripts/monitor_live_run.py`

* **Dokumentation:** [`docs/PHASE_33_LIVE_MONITORING_AND_CLI_DASHBOARDS.md`](PHASE_33_LIVE_MONITORING_AND_CLI_DASHBOARDS.md)

---

### 3.9 Phase 35 – Testnet Exchange Integration

* **Ziel:**
  Erste Exchange-Integration im Testnet-Modus mit Kraken.

* **Kernelemente:**
  * `src/exchange/kraken_testnet.py` – `KrakenTestnetClient`, HMAC-Signierung, `validate_only=true`
  * `src/orders/testnet_executor.py` – `TestnetExchangeOrderExecutor`
  * `scripts/run_testnet_session.py`

* **Dokumentation:** [`docs/PHASE_35_TESTNET_EXCHANGE_INTEGRATION.md`](PHASE_35_TESTNET_EXCHANGE_INTEGRATION.md)

---

### 3.10 Phase 36 – Config/Test-Infra Hardening

* **Ziel:**
  Config-Handling und Test-Infrastruktur robust machen.

* **Kernelemente:**
  * `config/config.toml` – Produktions-Config
  * `config/config.test.toml` – Test-Config mit sicheren Defaults
  * `src/core/peak_config.py` – `load_config()` + `PEAK_TRADE_CONFIG_PATH`
  * `tests/conftest.py` – zentrales Test-Setup

* **Dokumentation:** [`docs/PHASE_36_TEST_SUITE_AND_CONFIG_HYGIENE.md`](PHASE_36_TEST_SUITE_AND_CONFIG_HYGIENE.md)

---

### 3.11 Phase 37 – Testnet Orchestration & Limits

* **Ziel:**
  Testnet-Runs **profilbasiert und limitbewusst** orchestrieren.

* **Kernelemente:**
  * `src/live/testnet_limits.py` – `TestnetLimitsController`, `TestnetUsageStore`
  * `src/live/testnet_profiles.py` – `TestnetSessionProfile`, Profile-Loader
  * `scripts/orchestrate_testnet_runs.py` – CLI: `--list`, `--budget`, `--profile`, `--dry-run`
  * Config: `[testnet_limits.*]`, `[testnet_profiles.*]`, `[testnet_orchestration]`

* **Dokumentation:** [`docs/PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md`](PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md)

---

## 4. Nächste Live-/Testnet-Phasen (konkret definiert)

Die folgenden drei Phasen sind als nächste Schritte definiert:

### 4.1 Phase 38 – Exchange-Anbindung v0 (Testnet)

**Ziel:**
Eine erste, streng begrenzte **Exchange-Anbindung im Testnet-Modus**, die den bestehenden Order-/Execution-Layer nutzt.

**Scope:**
* Nur **Testnet-Umgebung** (`environment = testnet`)
* Limitierte Ordergröße + harte Risk-Gates
* Keine Auto-Scale-Up-Mechanismen

**Mögliche Artefakte:**
* `src/exchange/base.py` – `ExchangeClient`-Interface
* `src/exchange/kraken_testnet.py` – Erweiterung zum vollwertigen Client
* `src&#47;orders&#47;exchange.py` – `ExchangeOrderExecutor`
* Config: `[exchange.kraken_testnet]` erweitert
* CLI: `scripts&#47;testnet_ping_exchange.py`, `scripts&#47;testnet_place_smoke_order.py` (illustrative) <!-- pt:ref-target-ignore -->

**Status:** 📝 geplant

---

### 4.2 Phase 39 – Live-Deployment-Playbook & Runbooks

**Ziel:**
Ein **klarer, schriftlich fixierter Weg** von „Testnet ok" zu „vorsichtiges Live".

**Scope:**
* Fokus auf Dokumentation + kleine Helper-Scripts
* Keine großen neuen Core-Module

**Mögliche Artefakte:**
* `docs/LIVE_DEPLOYMENT_PLAYBOOK.md`
  * Voraussetzungen, Stufenplan, Checklisten
* `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
  * Start/Stop, Fehler-Handling, Kommunikationswege
* `scripts/check_live_readiness.py`
* `scripts/smoke_test_testnet_stack.py`

**Status:** 📝 geplant

---

### 4.3 Phase 40 – Monitoring- & Observability-Dashboards

**Ziel:**
**Besseres Monitoring für laufende Systeme** – von TUI-Dashboards bis zu KPIs.

**Scope:**
* Fokus auf Lesbarkeit und Reaktionsfähigkeit
* Nutzt `LiveRunLogger`, Reporting-Module, Limits-Infos

**Mögliche Artefakte:**
* `src&#47;monitoring&#47;dashboard.py` – TUI mit `rich` <!-- pt:ref-target-ignore -->
* (Optional) `scripts&#47;run_monitoring_server.py` – Web-Dashboard (illustrative) <!-- pt:ref-target-ignore -->
* Alerting/Signals (leichtgewichtig)

**Status:** 📝 geplant

---

## 5. Test-Status

**Aktuelle Testsuite (nach Phase 37):**

```
1251 passed, 4 skipped
```

| Phase | Neue Tests |
|-------|------------|
| Phase 35 | Testnet Exchange Integration |
| Phase 36 | Config/Test-Infra |
| Phase 37 | +73 Tests (Limits, Profile, Orchestrator) |

---

## 6. Dateistruktur (Auswahl)

```
Peak_Trade/
├── config/
│   ├── config.toml              # Produktions-Config
│   └── config.test.toml         # Test-Config
├── src/
│   ├── core/
│   │   ├── environment.py       # TradingEnvironment
│   │   ├── peak_config.py       # Config-Loader
│   │   └── config_pydantic.py   # Pydantic-Config
│   ├── exchange/
│   │   └── kraken_testnet.py    # Kraken Testnet Client
│   ├── execution/
│   │   └── pipeline.py          # Execution Pipeline
│   ├── live/
│   │   ├── safety.py            # Safety Guards
│   │   ├── risk_limits.py       # Live Risk Limits
│   │   ├── run_logging.py       # Run Logging
│   │   ├── monitoring.py        # Monitoring
│   │   ├── testnet_limits.py    # Testnet Limits (Phase 37)
│   │   └── testnet_profiles.py  # Testnet Profiles (Phase 37)
│   ├── orders/
│   │   ├── base.py              # Order-Dataclasses
│   │   ├── paper.py             # Paper Executor
│   │   └── testnet_executor.py  # Testnet Executor
│   └── reporting/
│       ├── base.py              # Report-Basis
│       └── backtest_report.py   # Backtest Reports
├── scripts/
│   ├── orchestrate_testnet_runs.py  # Testnet Orchestrator (Phase 37)
│   ├── run_testnet_session.py       # Testnet Session (Phase 35)
│   └── monitor_live_run.py          # Live Monitoring (Phase 33)
├── tests/
│   ├── conftest.py                  # Test-Setup
│   ├── test_testnet_limits.py       # Phase 37 Tests
│   ├── test_testnet_profiles.py     # Phase 37 Tests
│   └── test_testnet_orchestration.py # Phase 37 Tests
└── docs/
    ├── PEAK_TRADE_OVERVIEW_PHASES_1_40.md  # Dieses Dokument
    ├── PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md
    ├── PHASE_36_TEST_SUITE_AND_CONFIG_HYGIENE.md
    ├── PHASE_35_TESTNET_EXCHANGE_INTEGRATION.md
    └── ...
```

---

## 7. Wie dieses Dokument genutzt werden soll

* **Phasen-Übersicht:**
  Schnelles Nachschlagen, in welcher Phase welche großen Bausteine angelegt wurden.

* **Planung:**
  Insbesondere Abschnitt 4 als **Fahrplan für Live-/Testnet-Weiterentwicklung** (38–40).

* **Verlinkung:**
  Jede Phase verweist auf ihr Detail-Dokument.
  Dieses Overview-Dokument bleibt „Top-Level-Landkarte" und wird inkrementell erweitert.

---

## 8. Deep-Research-Track (Phasen 60–90)

> **Hinweis:** Der Inhalt für diesen Abschnitt wird vom Nutzer eingefügt.

---

## 9. Nächste sinnvolle Schritte (Meta)

1. **Bei Umsetzung von Phase 38–40:**
   * Entsprechende Abschnitte hier von „📝 geplant" auf „✅ done" stellen.
   * Neue Detail-Doku-Dateien hinzufügen (z.B. `PHASE_38_EXCHANGE_V0.md`).

2. **Links validieren:**
   * Prüfen, ob alle referenzierten Dokumente existieren.

3. **Regelmäßige Aktualisierung:**
   * Nach jeder abgeschlossenen Phase dieses Dokument aktualisieren.
