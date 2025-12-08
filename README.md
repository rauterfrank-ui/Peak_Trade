# Peak_Trade

Peak_Trade ist ein modulares, research-getriebenes Trading-Framework mit konsequentem Safety-First-Ansatz. Die Architektur trennt sauber zwischen Data, Strategy, Portfolio, Execution und Reporting – Research-Experimente, Shadow-Runs und Testnet-Betrieb sind klar voneinander abgegrenzt. Eine umfassende Research-Pipeline (Sweeps, Walk-Forward, Monte-Carlo, Stress-Tests) liefert fundierte Go/No-Go-Entscheidungen, während Risk-Limits auf Order- und Portfolio-Level greifen, bevor ein Trade überhaupt ausgeführt werden kann. Kurz: Ein produktionsnahes Framework, dem Future-Ich vertrauen kann.

---

## Schnelleinstieg

- 📖 **Vollständige v1.0-Übersicht:** [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](docs/PEAK_TRADE_V1_OVERVIEW_FULL.md)
- 🚀 **Onboarding „First 7 Days":** [`docs/PEAK_TRADE_FIRST_7_DAYS.md`](docs/PEAK_TRADE_FIRST_7_DAYS.md)

---

## AI-Unterstützung & Guides

Peak_Trade ist so gebaut, dass AI-Tools wie Cursor, Claude und ChatGPT beim Entwickeln, Refactoren und Dokumentieren helfen können – unter klaren Spielregeln (Safety-First, Tests respektieren, Doku mitpflegen).

- 🤖 **AI-Helper-Guide (Working Agreements & Best Practices)**
  Lies zuerst diesen Guide, wenn du mit AI an Peak_Trade arbeiten willst:
  [`docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md`](docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md)

- 🧭 **CLAUDE_GUIDE (Technische Referenz für das Repo)**
  Übersicht über Projektstruktur, Module, typische Commands und Einstiegspunkte:
  [`docs/ai/CLAUDE_GUIDE.md`](docs/ai/CLAUDE_GUIDE.md)

---

## Key Features

- 🧠 **Research & Strategy-Engine**
  - Backtest-Engine mit Portfolio-Support
  - Research-Pipeline v2 (Sweeps, Walk-Forward, Monte-Carlo, Stress-Tests)
  - Strategy- & Portfolio-Library mit vordefinierten Presets (inkl. Risk-Profilen)

- 📊 **Portfolio-Level Robustness**
  - Portfolio-Robustness-Module
  - Portfolio-Recipes & Presets (conservative/moderate/aggressive)
  - End-to-End-Playbook von Research → Live-Portfolio

- 🛡️ **Risk, Governance & Safety**
  - Live-Risk-Limits (Order- und Portfolio-Level)
  - Governance- & Safety-Doku (Checklisten, Readiness, Runbooks)
  - Incident-Drills & Drill-Log

- 🛰️ **Live-/Testnet-Track**
  - Live-Ops CLI (`live_ops`) mit Health, Orders, Portfolio
  - Alerts inkl. Logging, stderr, Webhook & Slack
  - Live-Status-Reports (Markdown/HTML) für Daily/Weekly Monitoring
  - **Live-Track Demo:** 10–15 Min Hands-On für Shadow/Testnet ([Demo-Walkthrough](docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md))

- 🤖 **AI-Assistenz-Integration**
  - `docs/ai/CLAUDE_GUIDE.md` als Guide für Coding-Assistants
  - Playbooks & Docs so strukturiert, dass sie leicht als Prompt-Kontext dienen

---

## Architektur-Snapshot

Peak_Trade ist in mehrere Layer strukturiert:

- **Data-Layer** (`src/data/`) – Daten-Loading, Caching, Exchange-Integration
- **Backtest- & Research-Layer** (`src/backtest/`, `scripts/research_cli.py`) – Backtest-Engine, Research-Pipeline
- **Strategy- & Portfolio-Layer** (`src/strategies/`, `config/config.toml`, `config/portfolio_recipes.toml`) – Strategien, Portfolio-Recipes
- **Live-/Testnet-Layer** (`src/live/`, `scripts/live_ops.py`) – Live-Ops, Alerts, Risk-Limits
- **Reporting & Status-Reports** (`src/reporting/`, `scripts/generate_live_status_report.py`) – Reports, Visualisierung
- **Governance, Safety & Runbooks** (`docs/*.md`) – Dokumentation, Prozesse, Drills

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

> Für einen Schritt-für-Schritt-Flow (inkl. Screenshots/Details) siehe:  
> [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).

---

## Live-Track Demo (Shadow/Testnet)

In **10–15 Minuten** den kompletten Live-Track praktisch erleben – ohne echtes Kapital:

```bash
# 1. Dashboard starten
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

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

## Typische Flows

- 🔍 **Neues Portfolio-Setup researchen**
  1. Portfolio-Preset in `config/portfolio_recipes.toml` auswählen
  2. Research-CLI (`scripts/research_cli.py portfolio/pipeline`) ausführen
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

- **AI-Assistenz (z.B. Claude, ChatGPT, Cursor)**  
  [`docs/ai/CLAUDE_GUIDE.md`](docs/ai/CLAUDE_GUIDE.md)

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
