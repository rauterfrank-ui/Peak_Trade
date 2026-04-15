# Peak_Trade

Peak_Trade ist ein modulares, research-getriebenes Trading-Framework mit konsequentem Safety-First-Ansatz. Die Architektur trennt sauber zwischen Data, Strategy, Portfolio, Execution und Reporting – Research-Experimente, Shadow-Runs und Testnet-Betrieb sind klar voneinander abgegrenzt. Eine umfassende Research-Pipeline (Sweeps, Walk-Forward, Monte-Carlo, Stress-Tests) liefert fundierte Go/No-Go-Entscheidungen, während Risk-Limits auf Order- und Portfolio-Level greifen, bevor ein Trade überhaupt ausgeführt werden kann. Kurz: Ein produktionsnahes Framework, dem Future-Ich vertrauen kann.

---

## Schnelleinstieg

### 🚀 Quick Start: Ersten Backtest in 5 Minuten

```bash
# 1. Dependencies installieren (einmalig)
pip install -e .

# 2. Ersten Backtest laufen lassen
python3 scripts/run_strategy_from_config.py --strategy ma_crossover --symbol BTC/USDT

# 3. Tests ausführen
python3 -m pytest -m smoke -q  # Schnelle Smoke-Tests (~1 Sekunde)
python3 -m pytest -q           # Full Suite (~70 Sekunden)

# 4. Optionale Web-UI Dependencies (für Dashboard/API Tests)
uv sync --extra web  # oder: pip install -e ".[web]"
python3 -m pytest -m web        # Web-UI Tests ausführen
```

**Hinweis:** Web-UI Tests werden automatisch übersprungen, wenn FastAPI nicht installiert ist. Core-Tests laufen ohne Web-Stack.

**Nächste Schritte:**
- 📖 **Architektur & Überblick:** [`docs/PEAK_TRADE_OVERVIEW.md`](docs/PEAK_TRADE_OVERVIEW.md)
- 🔬 **Backtest Engine Details:** [`docs/BACKTEST_ENGINE.md`](docs/BACKTEST_ENGINE.md)
- 🎯 **Eigene Strategien entwickeln:** [`docs/STRATEGY_DEV_GUIDE.md`](docs/STRATEGY_DEV_GUIDE.md)

### 📚 Ausführliche Guides

- 📖 **Vollständige v1.0-Übersicht:** [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](docs/PEAK_TRADE_V1_OVERVIEW_FULL.md)
- 🚀 **Onboarding „First 7 Days":** [`docs/PEAK_TRADE_FIRST_7_DAYS.md`](docs/PEAK_TRADE_FIRST_7_DAYS.md)

---

## Core Architecture & Development

Für Entwickler, die mit Peak_Trade arbeiten oder Strategien entwickeln:

- 📐 **[System Overview](docs/PEAK_TRADE_OVERVIEW.md)** – Architektur-Überblick, Kernkonzepte, Quickstart
- 🔧 **[Backtest Engine](docs/BACKTEST_ENGINE.md)** – Detaillierte Engine-Dokumentation
- 🎯 **[Strategy Development Guide](docs/STRATEGY_DEV_GUIDE.md)** – Schritt-für-Schritt-Anleitung zum Entwickeln eigener Strategien
- 📝 **[Workflow Notes](docs/WORKFLOW_NOTES.md)** – Aktueller technischer Stand & gemeinsamer Workflow

---

## Security & Audit

- 🔒 **[Security Notes](SECURITY_NOTES.md)** — Known vulnerabilities, Python version limitations, CVE tracking
- 🔍 **[Audit Runbook](docs/audit/AUDIT_RUNBOOK_COMPLETE.md)** — Complete audit procedures (Security, Dependencies, Quality)
- 🛡️ **[Governance & AI Autonomy](docs/governance/README.md)** — Governance-first guardrails, Policy Critic, Evidence Packs
- 🗺️ **[Docs Truth Map](docs/ops/registry/DOCS_TRUTH_MAP.md)** — Kanonische Ops-Doku-Registry und Änderungsnachweis (truth-first)

---

## AI-Unterstützung & Guides

Peak_Trade ist so gebaut, dass AI-Tools wie Cursor, Claude und ChatGPT beim Entwickeln, Refactoren und Dokumentieren helfen können – unter klaren Spielregeln (Safety-First, Tests respektieren, Doku mitpflegen).

- 🤖 **AI-Helper-Guide (Working Agreements & Best Practices)**
  Lies zuerst diesen Guide, wenn du mit AI an Peak_Trade arbeiten willst:
  [`docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md`](docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md)

- 🧭 **CLAUDE_GUIDE (Technische Referenz für das Repo)**
  Übersicht über Projektstruktur, Module, typische Commands und Einstiegspunkte:
  [`docs/ai/CLAUDE_GUIDE.md`](docs/ai/CLAUDE_GUIDE.md)

- 🚀 **AI Workflow Guide (Praktische Workflows & Templates)**
  Konkrete Workflows und Prompt-Templates für effiziente AI-Nutzung:
  [`docs/ai/AI_WORKFLOW_GUIDE.md`](docs/ai/AI_WORKFLOW_GUIDE.md)

---

## Developer Experience & Productivity

- ⚡ **Developer Workflow Guide**
  Streamlined workflows und Automation-Tools für produktive Entwicklung:
  [`docs/DEVELOPER_WORKFLOW_GUIDE.md`](docs/DEVELOPER_WORKFLOW_GUIDE.md)

- 📚 **Knowledge Base Index**
  Zentraler Dokumentations-Hub mit Navigation und Lernpfaden:
  [`docs/KNOWLEDGE_BASE_INDEX.md`](docs/KNOWLEDGE_BASE_INDEX.md)

- 🎯 **Quick Reference Card**
  Schnellreferenz für häufige Commands und Patterns:
  [`docs/QUICK_REFERENCE.md`](docs/QUICK_REFERENCE.md)

- 🛠️ **Developer Workflow Script**
  Automatisierung häufiger Entwicklungsaufgaben:
  ```bash
  python3 scripts/dev_workflow.py --help
  python3 scripts/dev_workflow.py setup    # Environment setup
  python3 scripts/dev_workflow.py test     # Run tests
  python3 scripts/dev_workflow.py health   # Health check
  ```

---

## Modulare Architektur

Peak_Trade ist **strikt modular** aufgebaut. Jede Komponente ist austauschbar und testbar:

```text
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│   DATA   │ → │ STRATEGY │ → │  SIZING  │ → │   RISK   │
│  Feeds   │   │ Registry │   │ Overlay  │   │  Limits  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                    │
                              ┌─────────────────────┘
                              ▼
                        ┌──────────┐   ┌──────────┐
                        │ BACKTEST │ → │ REPORTING│
                        │  Runner  │   │  & Stats │
                        └──────────┘   └──────────┘
```

**Strategy Registry:** Alle Strategien zentral registriert, austauschbar per Config
**Position Sizing:** Fixed-Fraction, Vol-Regime-Overlay, Trend-Strength-Overlay
**Risk Management:** Max-Drawdown, Equity-Floor, Position-Limits
**Runner:** Backtest, Walk-Forward, Monte-Carlo, Live-Session

→ Details: [`docs/PEAK_TRADE_OVERVIEW.md`](docs/PEAK_TRADE_OVERVIEW.md)

---

## Key Features

- 🧠 **Research & Strategy-Engine**
  - Backtest-Engine mit Portfolio-Support & No-Lookahead-Garantie
  - Research-Pipeline v2 (Sweeps, Walk-Forward, Monte-Carlo, Stress-Tests)
  - Strategy- & Portfolio-Library mit vordefinierten Presets (inkl. Risk-Profilen)
  - **Strategy Registry:** 15+ Production-Ready Strategien, 6+ R&D-Strategien

- 📊 **Portfolio-Level Robustness**
  - Portfolio-Robustness-Module
  - Portfolio-Recipes & Presets (conservative/moderate/aggressive)
  - End-to-End-Playbook von Research → Live-Portfolio

- 🛡️ **Risk, Governance & Safety**
  - Live-Risk-Limits (Order- und Portfolio-Level)
  - Governance- & Safety-Doku (Checklisten, Readiness, Runbooks)
  - Incident-Drills & Drill-Log
  - **Comprehensive Error Handling:** Structured error taxonomy with actionable hints
    - 9 specialized error types (DataContractError, ConfigError, ProviderError, etc.)
    - Consistent message/hint/context/cause pattern for all errors
    - Exception chaining for root cause analysis
    - **Default:** All new code uses `src.core.errors` taxonomy
    - **Quick Usage:**
      ```python
      # Raise with hint + context
      raise DataContractError("Invalid OHLCV", hint="Check columns", context={"cols": df.columns})
      # Chain exceptions
      raise ConfigError("Load failed", hint="Check syntax", cause=original_error)
      ```
    - **Documentation:** [Error Handling Guide](docs/ERROR_HANDLING_GUIDE.md)
    - **Audit Tool:** `python scripts/audit/check_error_taxonomy_adoption.py`

- 🔄 **Resilience & Stability**
  - Circuit Breaker Pattern für alle kritischen Module
  - Rate Limiting für externe APIs und Datenquellen
  - Prometheus-Metriken für System-Monitoring
  - Health Check API (`/health`, `/health/detailed`)
  - Konfigurierbare Resilience-Settings pro Modul
  - **Dokumentation:** [`docs/resilience_guide.md`](docs/resilience_guide.md)

- 🛰️ **Live-/Testnet-Track**
  - Live-Ops CLI (`live_ops`) mit Health, Orders, Portfolio
  - Alerts inkl. Logging, stderr, Webhook & Slack
  - Live-Status-Reports (Markdown/HTML) für Daily/Weekly Monitoring
  - **Live-Track Demo:** 10–15 Min Hands-On für Shadow/Testnet ([Demo-Walkthrough](docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md))

- 🤖 **AI-Assistenz-Integration**
  - `docs/ai/CLAUDE_GUIDE.md` als Guide für Coding-Assistants
  - Playbooks & Docs so strukturiert, dass sie leicht als Prompt-Kontext dienen

- 🧠 **Knowledge Databases & AI Research**
  - Vector-DB-Integration (Chroma, Pinecone, Qdrant) für semantische Suche
  - Time-Series-DB für Ticks und Portfolio-Historien
  - RAG (Retrieval-Augmented Generation) für KI-gestützte Research-Entscheidungen
  - API-Security & Key-Management mit Rotation-Tracking
  - **Governance Playbook:** Systematische Prüfung externer Wissensquellen ([Playbook](docs/KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md))

- 🤖 **Autonomer KI-gesteuerter Workflow**
  - Intelligente Entscheidungsfindung basierend auf Markt-, Signal- und Performance-Metriken
  - Automatisierte Workflow-Ausführung mit AI-enhanced Decision Engine
  - Integration mit Scheduler für kontinuierliches Monitoring
  - Details: [`docs/AUTONOMOUS_AI_WORKFLOW.md`](docs/AUTONOMOUS_AI_WORKFLOW.md)

---

## Architektur-Snapshot

Peak_Trade ist in mehrere Layer strukturiert:

- **Data-Layer** (`src/data/`) – Daten-Loading, Caching, Exchange-Integration
- **Knowledge-Layer** (`src/knowledge/`) – Vector-DB, Time-Series-DB, RAG-Pipeline für AI-Research
- **Backtest- & Research-Layer** (`src/backtest/`, `scripts/research_cli.py`) – Backtest-Engine, Research-Pipeline
- **Strategy- & Portfolio-Layer** (`src/strategies/`, `config/config.toml`, `config/portfolio_recipes.toml`) – Strategien, Portfolio-Recipes
- **Live-/Testnet-Layer** (`src/live/`, `scripts/live_ops.py`) – Live-Ops, Alerts, Risk-Limits
- **Autonomous Workflow-Layer** (`src/autonomous/`, `scripts/run_autonomous_workflow.py`) – AI-gesteuerter autonomer Workflow, Decision Engine
- **Reporting & Status-Reports** (`src/reporting/`, `scripts/generate_live_status_report.py`) – Reports, Visualisierung
- **Governance, Safety & Runbooks** (`docs&#47;*.md`) – Dokumentation, Prozesse, Drills

**Details & Diagramme:** siehe [`docs/ARCHITECTURE_OVERVIEW.md`](docs/ARCHITECTURE_OVERVIEW.md).

---

## Quickstart

> **Hinweis:** Details & Screenshots findest du in [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).

### 1. Umgebung vorbereiten

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ersten Research-Run starten (Portfolio-Preset)

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_conservative \
  --format both
```

### 3. Live-/Testnet Health & Portfolio prüfen (ohne echte Orders)

```bash
python scripts/live_ops.py health --config config/config.toml
python scripts/live_ops.py portfolio --config config/config.toml --json
```

### 4. Daily Live-Status-Report generieren (Markdown)

```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format markdown \
  --tag daily
```

### 5. Autonomer KI-gesteuerter Workflow ausführen

```bash
# Einmalige Ausführung mit automatischer Entscheidung
python scripts/run_autonomous_workflow.py --once --dry-run

# Mit Scheduler: Täglich automatisch
python scripts/run_scheduler.py \
  --config config/scheduler/jobs.toml \
  --include-tags autonomous
```

> Für einen Schritt-für-Schritt-Flow (inkl. Screenshots/Details) siehe:  
> [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).

---

## Live-Track Demo (Shadow/Testnet)

In **10–15 Minuten** den kompletten Live-Track praktisch erleben – ohne echtes Kapital:

```bash
# 1. Dashboard starten (siehe auch "Web UI" weiter unten)
RELOAD=1 ./scripts/ops/run_webui.sh

# 2. Shadow-Session (10 Steps)
python scripts/run_execution_session.py --strategy ma_crossover --steps 10

# 3. Registry prüfen
python scripts/report_live_sessions.py --summary-only --stdout

# 4. Dashboard öffnen: http://127.0.0.1:8000/
```

**Was du siehst:** Session-Start → Order-Simulation → Registry-Eintrag → Live-Track Panel mit Status, PnL, Drawdown.

> **Safety-First:** Nur Shadow-/Testnet-Mode. Live-Mode bleibt durch Safety-Gates blockiert.
> **Vollständiger Walkthrough:** [`docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

---

## Web UI

### Install deps (uv)

```bash
uv sync --extra web
```

### Run (recommended wrapper)

Operator-Dashboard (Session Explorer, R&D, Ops). **Port 8000** (`http://127.0.0.1:8000/`).

```bash
./scripts/ops/run_webui.sh
# Reload:
RELOAD=1 ./scripts/ops/run_webui.sh
```

### Live dashboard

Run-zentriertes Dashboard (Runs-Liste, Snapshots, Alerts) für Shadow-/Testnet-Monitoring. **Port 8010** (Override: `PORT=8000 .&#47;scripts&#47;ops&#47;run_live_webui.sh`).

```bash
./scripts/ops/run_live_webui.sh
# Reload:
RELOAD=1 ./scripts/ops/run_live_webui.sh
```

**Alternativen (nicht alle starten dieselbe App):**

- `python3 scripts/live_web_server.py` → `src.live.web.app` (Live-Dashboard mit `/api/v0/*`, `/runs/*`, `/dashboard`)
- `bash scripts/ops/run_live_webui.sh` → `src.live.web.app` (Wrapper für das Live-Dashboard)
- `bash scripts/ops/run_webui.sh` → `src.webui.app` (Operator-WebUI mit `/api/live_sessions`, `/api/execution/*`, `/ops`, `/r_and_d`)
- `python3 scripts/serve_live_dashboard.py` → `src.live.web.app` (alternativer Live-Dashboard-Entrypoint)

| Entrypoint | Port | Hinweis |
|------------|------|---------|
| `run_live_webui.sh` | 8010 | Shell-Wrapper mit `uv` (oben) |
| `python3 scripts/live_web_server.py` | 8000 | Empfohlen in Runbooks, CLI-Argumente |
| `python -m scripts.serve_live_dashboard` | 8000 | Config aus `config/config.toml` |

### HTTP-Routen — Operator-WebUI, Ops-Hub & live.web (Local Defaults)

Ports **8000** (Operator-WebUI) und **8010** (live.web mit `scripts/ops/run_live_webui.sh`) sind **README-Defaults** auf `127.0.0.1`. Die Prozesse sind **getrennt**; es gibt **keine gemeinsame Control Plane**. Die Pfade dienen der **Orientierung** (read-only UI; keine Änderung an Ausführungs- oder Freigabesemantik).

**Operator-WebUI** (Standard `http://127.0.0.1:8000`):

- `/` — Haupt-Dashboard
- `/ops` — Ops Cockpit
- `/ops/stage1` — Stage1 Ops Dashboard
- `/ops/workflows` — Ops-Workflow-Hub
- `/ops/ci-health` — CI & Governance Health
- `/session/{session_id}` — Session-Detail (HTML, read-only)

**Weitere Operator-WebUI-Nav** (read-only; Anzeigenamen wie in der Kopfzeile: `templates/peak_trade_dashboard/base.html`):

- `/execution_watch` — Execution Watch
- `/live/alerts` — Alerts
- `/r_and_d` — R&D Experiments
- `/r_and_d/experiment/{run_id}` — R&D Experiment-Detail (HTML, read-only)
- `/r_and_d/comparison` — R&D Multi-Run-Vergleich (HTML, read-only)
- `/live/telemetry` — Telemetry

**live.web** (Standard `http://127.0.0.1:8010` mit `scripts/ops/run_live_webui.sh`):

- `/` und `/dashboard` — Live-Dashboard (Runs)
- `/watch` — Watch-Übersicht
- `/watch/runs/{run_id}` — Run-Detail (Watch)
- `/sessions/{run_id}` — Alias zum gleichen Run-Detail

Zusätzlich stellt live.web **read-only** JSON unter dem Präfix **`/api/v0`** bereit (u. a. für Watch-/Status-Zugriff); Details und Beispiele: [`docs/LIVE_OPERATIONAL_RUNBOOKS.md`](docs/LIVE_OPERATIONAL_RUNBOOKS.md) (Abschnitt 10d.4), Implementierung: [`src/live/web/api_v0.py`](src/live/web/api_v0.py).

Die **Companion**-Hinweise in live.web (Haupt-Dashboard und Watch-/Session-HTML) verlinken **lesend** (Navigation only) auf **`http://127.0.0.1:8000/`**, **`http://127.0.0.1:8000/ops`**, **`http://127.0.0.1:8000/ops/ci-health`** und den Run-UI-Standard **`http://127.0.0.1:8010/`** — README-Default-Hosts/-Ports, **getrennte Prozesse**, **keine gemeinsame Control Plane** (Implementierung: `src/live/web/app.py`).

Details: [`docs/CLI_CHEATSHEET.md`](docs/CLI_CHEATSHEET.md#18-live-web-dashboard-phase-67), [`docs/LIVE_OPERATIONAL_RUNBOOKS.md`](docs/LIVE_OPERATIONAL_RUNBOOKS.md) Abschnitt 10d.

---

## Typische Flows

- 🔍 **Neues Portfolio-Setup researchen**
  1. Portfolio-Preset in `config/portfolio_recipes.toml` auswählen
  2. Research-CLI (`scripts&#47;research_cli.py portfolio&#47;pipeline`) ausführen
3. Portfolio-Robustness & Reports prüfen
4. Entscheidung anhand des Playbooks treffen: [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)

- 🛰️ **Bestehendes Portfolio im Shadow-/Testnet-Mode betreiben**
  1. Live-Konfiguration & Risk-Limits prüfen (`[live_risk]` in `config/config.toml`)
  2. `scripts/live_ops.py` verwenden (Health, Portfolio)
  3. Daily/Weekly Live-Status-Reports generieren
  4. Incident-Drills regelmäßig ausführen: [`docs/INCIDENT_SIMULATION_AND_DRILLS.md`](docs/INCIDENT_SIMULATION_AND_DRILLS.md)

- 🧪 **Incident-Handling üben**
  1. Drill-Szenario auswählen (Data-Gap, PnL-Divergenz, Risk-Limit, Alerts)
  2. Drill gemäß `INCIDENT_SIMULATION_AND_DRILLS.md` durchführen
  3. Ergebnis & Erkenntnisse im `INCIDENT_DRILL_LOG.md` dokumentieren

---

## Dokumentation – Einstiegspunkte

- **Ops / Operator Hub:** `docs/ops/README.md`

- **Vollständige v1.0-Übersicht**  
  [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](docs/PEAK_TRADE_V1_OVERVIEW_FULL.md)

- **Projekt-Status & Phasen-Übersicht**  
  [`docs/PEAK_TRADE_STATUS_OVERVIEW.md`](docs/PEAK_TRADE_STATUS_OVERVIEW.md)

- **Architektur**  
  [`docs/ARCHITECTURE_OVERVIEW.md`](docs/ARCHITECTURE_OVERVIEW.md)

- **Getting Started (erste Stunde)**
  [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)

- **First 7 Days Onboarding (erste Woche)**
  [`docs/PEAK_TRADE_FIRST_7_DAYS.md`](docs/PEAK_TRADE_FIRST_7_DAYS.md)

- **Research → Live Portfolios (Playbook)**  
  [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)

- **Live-Status-Reports**  
  [`docs/LIVE_STATUS_REPORTS.md`](docs/LIVE_STATUS_REPORTS.md)

- **Incident-Drills & Runbooks**  
  - [`docs/INCIDENT_SIMULATION_AND_DRILLS.md`](docs/INCIDENT_SIMULATION_AND_DRILLS.md)  
  - [`docs/INCIDENT_DRILL_LOG.md`](docs/INCIDENT_DRILL_LOG.md)  
  - [`docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`](docs/RUNBOOKS_AND_INCIDENT_HANDLING.md)

- **Governance & Safety**  
  [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md)

- **Knowledge Databases & AI Research**  
  - [`docs/KNOWLEDGE_DB_ARCHITECTURE.md`](docs/KNOWLEDGE_DB_ARCHITECTURE.md)  
  - [`docs/KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md`](docs/KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md)  
  - [`docs/KNOWLEDGE_SOURCES_REGISTRY.md`](docs/KNOWLEDGE_SOURCES_REGISTRY.md)

- **AI-Assistenz (z.B. Claude, ChatGPT, Cursor)**  
  [`docs/ai/CLAUDE_GUIDE.md`](docs/ai/CLAUDE_GUIDE.md)

---

## Audit & Tooling

Peak_Trade includes a comprehensive audit system for repository health checks.

### Quick Audit

```bash
# Run full audit (safe, idempotent)
make audit
# or directly:
./scripts/run_audit.sh
```

**Output:** `reports&#47;audit&#47;YYYY-MM-DD_HHMM&#47;` with:
- `summary.json` - Machine-readable results
- `summary.md` - Human-readable report with status indicators
- Individual check outputs (pytest, secrets scan, live gating, etc.)

> **Note:** `reports&#47;` contains generated artifacts and is ignored by git (`/reports/` in `.gitignore`). See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for details.

### Install Audit Tools

```bash
# Show install hints
make audit-tools

# macOS
brew install ripgrep

# Python tools
pip install ruff black mypy pip-audit bandit
```

### Git Maintenance

```bash
# Pack loose objects (safe)
make gc
```

> **Note:** Audit outputs are stored in `reports&#47;audit&#47;` and are gitignored.

---

## Safety & Governance

Peak_Trade ist bewusst so gebaut, dass:

- Research, Shadow, Testnet und Live klar getrennt sind,
- Live-Risk-Limits vor jedem Trade greifen können,
- Alerts & Status-Reports dich auf Probleme hinweisen,
- Governance-Dokumente & Checklisten den Übergang in Live regeln.

➡ Alle sicherheitsrelevanten Prozesse sind in  
[`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md)  
und den zugehörigen Runbooks/Playbooks dokumentiert.

---

## Disclaimer

**Trading birgt erhebliche Risiken.** Dieses Projekt dient zu Bildungs- und Forschungszwecken. Verwende niemals Kapital, dessen Verlust du dir nicht leisten kannst.

---

## Lizenz

Privates Projekt – alle Rechte vorbehalten.

## Bounded Acceptance Documentation Chain
- start here: `docs&#47;ops&#47;reviews&#47;bounded_acceptance_start_here_page&#47;START_HERE.md`
- index, runbook, cheat sheet, go/no-go snapshot, readiness matrix, and governance framing are linked from there
