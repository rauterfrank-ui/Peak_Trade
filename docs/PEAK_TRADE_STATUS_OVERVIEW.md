# Peak_Trade – Projekt-Status Overview (Phasen 1–86)

Dieses Dokument beschreibt den aktuellen Gesamtstatus von **Peak_Trade**
(Phasen **1–86**, inkl. Research-/Portfolio-Track und Live-/Testnet-Track).

> **Research v1.0 Freeze:** Phase 86 markiert den Scope-Freeze für Research v1.0 und die Freigabe des Live-Track für Beta-Testing. Siehe [`PHASE_86_RESEARCH_V1_FREEZE.md`](PHASE_86_RESEARCH_V1_FREEZE.md).

> **Peak_Trade v1.0 Release-Paket:** siehe [`PEAK_TRADE_V1_RELEASE_NOTES.md`](PEAK_TRADE_V1_RELEASE_NOTES.md) und das aktualisierte Projekt-[`README.md`](../README.md).

Ziel:

* Eine **prozentuale Einschätzung** je Bereich
* Klarheit, **was schon stabil ist** und **was noch fehlt**
* Grundlage für zukünftige Roadmaps (Phase 59+)

> **Hinweis:** Prozentwerte sind bewusst als **qualitative Reifegrade** zu verstehen
> (Architektur, Codequalität, Tests, Doku, Operational Readiness), nicht als „fertig/nie-ändern".

> **Für ein Architektur-Diagramm und Layer-Übersicht siehe:** [`ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md)

> **Live-Track Doc Index:** Für eine zentrale Übersicht aller Live-Track-, Dashboard-, Playbook- und Safety-Dokumente siehe [`LIVE_TRACK_DOC_INDEX_V1.md`](LIVE_TRACK_DOC_INDEX_V1.md).

---

## Wie du den v1.0 Status liest

- **Schnell-Modus (5 Minuten):** Lies die Tabelle in [1. Gesamtstatus in Prozent](#1-gesamtstatus-in-prozent) für den High-Level-Überblick. Für den v1.0-Gesamtsnapshot mit Kennzahlen siehe den Abschnitt **„Hall of Fame – Peak_Trade v1.0 Snapshot"** in [`PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md).

- **Status-Interpretation:** Prozentwerte sind **qualitative Reifegrade** (Architektur, Codequalität, Tests, Doku, Operational Readiness) – nicht als „100% = fertig für immer" zu verstehen. Kommentare in den Tabellen erläutern den jeweiligen Stand.

- **Deep-Dive nach Layer:** Für Details zu einzelnen Bereichen navigiere zu den nummerierten Abschnitten (2–10), z.B. Data & Market Access, Backtest & Simulation, Strategy & Portfolio, Live-/Testnet & Operations.

- **Rollen-Fokus:**
  - *Research/Quant:* Abschnitte 3 (Backtest), 4 (Strategy & Portfolio), 6 (Research & Experiments)
  - *Operator/Ops:* Abschnitte 7 (Live-/Testnet), 8 (Reporting & CLI), 11 (Highlights Phasen 47–74)
  - *Reviewer/Risk:* Abschnitte 5 (Risk & Safety), 9 (Documentation & Governance), 13a (v1.0 Gesamtübersicht)

- **v1.0-Gesamtsnapshot:** Für Test-Zahlen, Tags, Commits und die verbindliche v1.0-Referenz siehe den Abschnitt **„Hall of Fame – Peak_Trade v1.0 Snapshot"** am Ende von [`PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md).

---

## Projektstatus – Gesamtüberblick (Stand: 2025-12-09)

| Bereich                         | Beschreibung                                                      | Fortschritt |
| ------------------------------- | ----------------------------------------------------------------- | ----------- |
| **Gesamtprojekt (Phasen 1–86)** | Vollständiger Peak_Trade Stack von Data bis Live                  | **≈ 98%**   |
| **Data-Layer**                  | Loader, Caches, Normalisierung, Multi-Source Support              | **100%**    |
| **Backtest-Engine**             | Portfolio-Backtests, Metriken, Registry, Run-Management           | **100%**    |
| **Strategy-Layer (Prod)**       | Kernstrategien, produktive Signals, Tier-System                   | **≈ 96%**   |
| **Strategy-Layer (R&D)**        | R&D-Strategien (Armstrong, El Karoui, Waves), Sweeps              | **≈ 98%**   |
| **Portfolio & Risk**            | Portfolio-Strategien, RiskLimits, Kelly/Exposure, Checks          | **≈ 96%**   |
| **Execution & Live-Stack**      | Paper/Testnet-Flows, Live-Risk-Gates, Order-Executors             | **≈ 95%**   |
| **Live-Track & Bridge**         | Strategy→Execution Bridge, Live-Session-Registry, Status-Overview | **≈ 96%**   |
| **R&D Web-Dashboard**           | R&D Hub, Detail-View, Report-Gallery, Multi-Run-Comparison        | **100%**    |
| **Monitoring & Alerts**         | CLI-Dashboards, Health-/Smoke-/Readiness-Checks                   | **≈ 95%**   |
| **Docs & Runbooks**             | Phase-Dokus, Status-Overview, Runbooks, AI-Guides, Changelogs     | **≈ 97%**   |
| **Tooling / Dev-Workflow**      | venv, Test-Suite (>2500 Tests), CLI-Skripte, Git-/GH-Flow         | **≈ 95%**   |

---

## 2. Data & Market Access (~95%)

**Relevante Phasen (konzeptionell):**

* **Frühe Phasen 1–5** – Data-Layer-Aufbau, Loader/Normalizer/Cache
* **Data-/Market-Access-Feinschliff** – sukzessive in späteren Phasen integriert

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

**Relevante Phasen & Doku:**

* **Backtest-Grundlagen** – frühe Backtest-Phasen (Engine & Stats)
* **Phase 30 – Reporting & Visualization**
  → `docs/PHASE_30_REPORTING_AND_VISUALIZATION.md`
* **Registry-/Experiment-Integration** – Dokumentation im Research-/Registry-Kontext

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

**Relevante Phasen & Doku:**

* **Phase 26 – Portfolio-Strategie-Bibliothek**
  → Portfolio-Layer & Multi-Strategie-Kombination
* **Phase 47 – Portfolio-Level Robustness**
  → Portfolio-Robustheitslogik & Reporting
* **Portfolio Recipes & Presets**
  → `docs/PORTFOLIO_RECIPES_AND_PRESETS.md`

**Kernkomponenten:**

* Single-Strategie-Layer:

  * `src/strategies/*.py` (z.B. MA-Crossover, Trend-Following, RSI-Reversion, Breakout, Vol-Regime-Filter)
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

**Phase Strategy-Expansion (Breakout & Vol-Regime):**

* **Breakout-Strategie** (`src/strategies/breakout.py`):
  * Klassischer Donchian-/High-Low-Breakout auf Basis von N-Bars
  * Optionaler ATR-Filter zur Vermeidung von „Noise-Breakouts"
  * Separate Lookbacks für Long/Short, Exit bei gegenteiligem Breakout
  * Drei Risk-Modes: symmetric, long_only, short_only
* **Vol-Regime-Filter** (`src/strategies/vol_regime_filter.py`):
  * Meta-Strategie/Signalquelle für Regime-Klassifikation (Low-Vol/High-Vol/Neutral)
  * Threshold-basierte Regime-Erkennung
  * Als Filter für andere Strategien verwendbar
* **Dokumentation:** `docs/PHASE_STRATEGY_EXPANSION_BREAKOUT_VOL_REGIME.md`

**Phase Regime-Aware Portfolios:**

* **RegimeAwarePortfolioStrategy** (`src/strategies/regime_aware_portfolio.py`):
  * Kombiniert mehrere Sub-Strategien (z.B. Breakout + RSI)
  * Nutzt Vol-Regime-Signale für dynamische Gewichtung
  * Risk-On/Neutral/Risk-Off-Skalierung (1.0/0.5/0.0)
  * Modi: "scale" (kontinuierliche Skalierung) und "filter" (binäres An/Aus)
* **Config-Varianten:**
  * `portfolio.regime_aware_breakout_rsi` - Standard-Portfolio
  * `portfolio.regime_aware_conservative` - Konservative Variante
* **Dokumentation:** `docs/PHASE_REGIME_AWARE_PORTFOLIOS.md`

**Phase Regime-Aware Portfolio Sweeps & Presets:**

* **Vordefinierte Sweep-Presets:**
  * `regime_aware_portfolio_aggressive` - Aggressiv: Breakout + RSI, hohe Aktivität in Risk-On
  * `regime_aware_portfolio_conservative` - Konservativ: Breakout + MA, Filter-Mode
  * `regime_aware_portfolio_volmetric` - Vol-Metrik-Vergleich (ATR/STD/REALIZED/RANGE)
* **Sweep-Funktionen** (`src/experiments/regime_aware_portfolio_sweeps.py`):
  * Parametrisierbare Granularität (coarse/medium/fine)
  * Integration mit Research-CLI
* **TOML-Configs** (`config/sweeps/regime_aware_portfolio_*.toml`)
* **Dokumentation:** `docs/PHASE_REGIME_AWARE_SWEEPS_AND_PRESETS.md`

**Offene Themen:**

* Weitere Strategie-Familien und Märkte.
* Erweiterte Portfolio-Optimierungs-Ansätze (z.B. Risk-Parity, CVaR-Minimierung, etc.).

> **Reifegrad:** **ca. 92%** – Phase 53 erweitert die Strategy-/Portfolio-Library um klar benannte Presets für unterschiedliche Risk-Profile (conservative/moderate/aggressive) und Multi-Style-Portfolios (Trend + Mean-Reversion). Phase 54 fügt ein umfassendes Research→Live Playbook hinzu, das den kompletten Weg von Portfolio-Presets bis zur Live-/Testnet-Aktivierung dokumentiert. Siehe `PORTFOLIO_RECIPES_AND_PRESETS.md` und [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md).

---

## 5. Risk & Safety (Research + Live) (~90%)

**Relevante Phasen & Doku:**

* **Phase 25 – Governance & Safety**
  → `docs/PHASE_25_GOVERNANCE_SAFETY_IMPLEMENTATION.md`
* **Live-Risk-Limits**
  → Konfiguration & Implementierung im Live-Layer
* **Safety & Policies**
  → `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
  → `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`

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

**Relevante Phasen & Doku:**

* **Registry- & Experiment-Integration** – Backtest-/Registry-Phasen (Registry-Demo & Doku)
* **Research-Pipeline v2 (Phase 43)** – Sweep → Promote → Walk-Forward → MC → Stress
  → Doku zur Research-Pipeline v2 in `docs/` (Phase 43)
* **Portfolio-Robustness & Recipes**
  → Phase 47 + `docs/PORTFOLIO_RECIPES_AND_PRESETS.md`

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

* Integration mit externen Tracking-Tools (MLflow, Weights & Biases – nur optional).
* Mehr Komfortfunktionen (z.B. automatische Best-Config-Snapshots für bestimmte Risk-Profile).

> **Reifegrad:** **ca. 91%** – Research-Track ist auf sehr hohem Niveau. Phase 54 fügt ein umfassendes Research→Live Playbook hinzu, das den kompletten Prozess von Portfolio-Presets bis zur Live-/Testnet-Aktivierung dokumentiert. Siehe [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md).

### R&D-Strategie-Welle v1 – Armstrong, Ehlers, El Karoui & Co.

Mit Commit `7908106` (`feat(research): add R&D strategy modules & tests`) wurde die erste **R&D-Strategie-Welle** in Peak_Trade integriert. Ziel ist es, fortgeschrittene Forschungsansätze aus der quantitativen Finance in einer sauberen, testbaren Form bereitzustellen – klar getrennt von der produktiven v1.1 Strategy-Library.

* **Phase 75 – R&D-Strategien Armstrong & El Karoui:** Die experimentellen Strategien sind in `docs/PHASE_75_STRATEGY_LIBRARY_V1_1.md` jetzt detailliert beschrieben (Scope, typische Nutzungsszenarien, klare Abgrenzung zu Paper-/Testnet-/Live-Einsatz).

**Umfang der R&D-Welle v1:**

| Modul | Beschreibung | Kategorie |
|-------|-------------|-----------|
| **Armstrong** (`src/strategies/armstrong/`) | Cycle-/Timing-orientierte Strategien (ECM-Zyklen) | cycles |
| **Ehlers** (`src/strategies/ehlers/`) | Signal-Processing & Cycle-Filter (DSP-Techniken) | cycles |
| **El Karoui** (`src/strategies/el_karoui/`) | Stochastisches Volatilitätsmodell | volatility |
| **Bouchaud** (`src/strategies/bouchaud/`) | Microstructure-Overlay (Orderbuch-Analyse) | microstructure |
| **Gatheral/Cont** (`src/strategies/gatheral_cont/`) | Vol-Regime-Overlay (Rough-Vol-Modelle) | volatility |
| **Lopez de Prado** (`src/strategies/lopez_de_prado/`) | Meta-Labeling & ML-orientierte Ansätze | ml |
| **ML-Research** (`src/research/ml/`) | Zentrale Komponenten für ML-Labeling & Meta-Labeling | ml |

**Tests & Safety:**

* 94+ R&D-bezogene Tests (u.a. `test_bouchaud_gatheral_cont_strategies.py`, `test_ehlers_lopez_strategies.py`, `test_research_strategies.py`)
* Alle Strategien laufen unter dem Label **"R&D / Experimental"** im Strategy-Tiering
* Keine dieser Strategien ist für Live-Trading freigegeben; sie dienen ausschließlich Research, Backtests, Sweeps und strukturierten Experimenten

**Integration in Strategy-Tiering & Dashboard:**

* R&D-Strategien sind im `config/strategy_tiering.toml` als `tier = "r_and_d"` registriert
* Web-Dashboard zeigt R&D-Strategien nur mit explizitem `?include_research=true` Parameter
* Kategorisierung nach: `cycles`, `volatility`, `microstructure`, `ml`
* Zusätzliche Felder: `label`, `category`, `risk_profile`, `owner`, `tags`

**Nächste Schritte (R&D-Track):**

1. ~~Einbindung der R&D-Strategien in das Strategy-Tiering und das Web-Dashboard~~ ✅ Umgesetzt
2. ~~Aufbau von Research-Presets (Sweeps, Scans, Experiment-Sets) für ausgewählte Armstrong-, Ehlers- und Lopez-de-Prado-Setups~~ ✅ Vorbereitet (Welle v2)
3. Schrittweise Evaluierung, welche R&D-Strategien später für einen möglichen Übergang in die produktive v2.x-Strategie-Library in Frage kommen

**R&D-Strategie-Welle v2 (Ready for Execution):**

* Research-Presets für Armstrong, Ehlers, Lopez de Prado definiert
* Experiment-Katalog: [`PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md`](PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md) – 18 Experiment-Templates
* Preset-Dokumentation: [`PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md`](PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md)
* Preset-Konfiguration: `config/r_and_d_presets.toml`
* Status: 🔬 Experimente definiert, Ready for Execution
* **Run-Logs:** Siehe Abschnitt [„R&D-Experiment-Welle W2 (2025-12-08) – Run-Log"](PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md#61-rd-experiment-welle-w2-2025-12-08--run-log) für dokumentierte Läufe
* **Operator-View:** Abschnitt 8 in [`PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md`](PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md#8-rd-wave-v1--operator-view-strategy-profile--experiments-viewer--dashboard) beschreibt den praktischen Operator-Workflow (Strategy-Profile → Experiments-Viewer → Dashboard)
* **R&D Experiments Viewer CLI:** `scripts/view_r_and_d_experiments.py` – zentrales Tool zur Sichtung aller R&D-Experimente (Filter nach Preset, Tag, Strategy, Datum, Trades; Detail- und JSON-Output)
* **Notebook-Template:** `notebooks/r_and_d_experiment_analysis_template.py` – DataFrame-basierte Analyse mit Filtern, Aggregationen und Plots

**Phase 76 – R&D Dashboard v0 (Design):**

* Design-Spezifikation: [`PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md)
* Ziel: Read-Only Web-Dashboard für R&D-Experimente
* Views: Experiments List, Detail, Preset/Strategy Aggregations, Charts
* Basis: `reports/r_and_d_experiments/`, CLI `view_r_and_d_experiments.py`, Notebook-Template
* Status: ✅ Implementiert

**Phase 77 – R&D Experiment Detail & Report Viewer v1:**

* R&D API auf v1.2 erweitert (`report_links`, `duration_info`, `status`, `run_type`)
* Neuer Detail-View `/r_and_d/experiment/{run_id}` mit Meta-Panel, Metriken-Grid, Status-/Run-Type-Badges, Report-Links und einklappbarem Raw-JSON
* R&D-Übersicht `/r_and_d` um klickbare Zeilen + explizite Details-Spalte ergänzt
* Fehlerhafte oder unbekannte `run_id`s landen sauber auf `error.html` mit Rück-Link zum R&D Hub
* Status: ✅ Implementiert

**Phase 78 – R&D Report-Gallery & Multi-Run Comparison v1:**

* R&D API auf v1.3 erweitert: Neuer Batch-Endpoint `/api/r_and_d/experiments/batch` für Multi-Run-Abfragen
* Multi-Run Comparison View `/r_and_d/comparison` für den direkten Vergleich von 2–4 Experimenten
* Checkbox-Auswahl in der R&D-Übersicht mit Counter und Compare-Button
* Best-Metric-Hervorhebung (★) im Comparison-View für schnelle Identifikation der besten Runs
* Validierung: Min. 2, max. 10 Run-IDs pro Batch; teilweise ungültige IDs werden transparent gemeldet
* Design-Dokument: [`PHASE_78_R_AND_D_REPORT_GALLERY_AND_COMPARISON_V1.md`](PHASE_78_R_AND_D_REPORT_GALLERY_AND_COMPARISON_V1.md)
* Status: ✅ Implementiert

### Phase 78 v1.1 – R&D-API Helper-Refactoring

**Kernidee:** R&D-API-Helper sind jetzt klar geschichtet, framework-agnostisch und robust gegen Edge-Cases – sowohl für Web-API als auch CLI.

- **Architektur:** Neue Architekturnotiz beschreibt eine 4-Layer-Struktur:
  - **Lookup Layer:** `load_experiment_json()`, `load_experiments_from_dir()`
  - **Transform Layer:** `extract_flat_fields()`, `determine_status()`, `find_report_links()`
  - **Aggregation Layer:** `compute_summary()`, `compute_preset_stats()`, `compute_best_metrics()`
  - **Validation Layer:** `parse_and_validate_run_ids()` (wirft jetzt `ValueError` statt `HTTPException`)

- **Run-ID-Validierung:**  
  - `parse_and_validate_run_ids()` ist framework-agnostisch (nur noch `ValueError`, HTTP-Übersetzung passiert in den Endpoints).  
  - Unterstützt Deduplizierung (standardmäßig aktiv), prüft Limits (`MAX_RUN_IDS = 100`) und validiert zulässige Zeichen (alphanumerisch, `_`, `-`).

- **Best-Metrics-Aggregation:**  
  - `compute_best_metrics()` ist mit `BestMetricsDict` (TypedDict, `total=False`) typisiert.  
  - Funktioniert robust mit fehlenden oder partiellen Metrik-Sätzen, überspringt `None`-Werte und nicht-numerische Daten, ohne die Auswertung zu brechen.

- **Tests / Robustheit:**
  - 15 Edge-Case-Tests für `parse_and_validate_run_ids()` (Whitespace, Deduplizierung, Limits, ungültige Zeichen, leere Eingaben).
  - 14 Tests für `compute_best_metrics()` (leere Listen, partielle Metriken, fehlende `results`/`_filename`, `None`-Werte, nicht-numerische Felder, TypedDict-Kompatibilität).

###### Visualisierung – R&D API Helper-Flow

```mermaid
flowchart LR
    Registry[(Experiment Registry JSON)]
    API[REST API /api/r_and_d/*]
    Helper[Helper-Layer\n(find_experiment_by_run_id,\n build_experiment_detail,\n compute_best_metrics,\n parse_and_validate_run_ids)]
    HTML[HTML Views /r_and_d/*]

    Registry --> Helper
    API --> Helper
    Helper --> API
    Helper --> HTML
```

Diese Visualisierung zeigt, dass sowohl die JSON-API als auch die HTML-Views denselben Helper-Layer nutzen und die Registry nicht direkt, sondern immer über die Helper-Funktionen angesprochen wird.

> **Wichtig:** R&D-Strategien sind **nicht live-freigegeben**. Sie sind ausschließlich für Offline-Backtests, Research-Pipelines und akademische Analysen gedacht.

#### Done-Definition R&D-Strategie-Welle v1

* Alle R&D-Module der Welle v1 sind implementiert und in der Strategy-Registry sichtbar (Armstrong, Ehlers, El Karoui, Bouchaud, Gatheral/Cont, Lopez de Prado).
* Zu allen R&D-Modulen existieren Tests; alle R&D-bezogenen Tests laufen grün (aktuell 94 Tests für den R&D-Track).
* Strategy-Tiering & Web-Dashboard kennen den Tier `r_and_d` und können den Research-Layer explizit ein-/ausblenden (inkl. `?include_research=true`).
* Die R&D-Strategien sind in der Doku verankert (`PHASE_75_STRATEGY_LIBRARY_V1_1.md`, `PEAK_TRADE_STATUS_OVERVIEW.md`, `PEAK_TRADE_V1_OVERVIEW_FULL.md`).
* Live-Mode ist für alle R&D-Strategien explizit blockiert (`allow_live = false` / Safety-Gates dokumentiert); Nutzung nur für Offline-Backtests, Research-Sweeps und strukturierte Experimente.

#### Einstiegskriterien für R&D-Strategie-Welle v2

* Es liegen mehrere abgeschlossene R&D-Experimente/Reports mit Welle v1 vor (z.B. Parameter-Sweeps, Robustheits-Checks, Regime-Vergleiche).
* Aus den Ergebnissen von Welle v1 wurden konkrete „Gaps" oder neue Hypothesen abgeleitet (z.B. zusätzliche Volatilitätsmodelle, Execution-Cost-Modelle, Orderbuch-/Microstructure-Signale, ML-Regime-Classifier).
* Für mindestens 1–2 neue Baustein-Kategorien existiert ein klar umrissener Scope (z.B. *Execution-Cost / Almgren-Chriss*, *Market-Making / Avellaneda-Stoikov*, *Regime-Classifier / ML*).
* R&D-Welle v1 ist stabil: keine offenen Blocker-/TODOs im Code, Strategy-Tiering oder Web-Dashboard, nur noch inkrementelle Verbesserungen.

### Phase 41B – Strategy Robustness & Tiering (Experiments)

**Status:** ✅ abgeschlossen

**Kernpunkte:**

- Neues Modul `src/experiments/strategy_profiles.py` mit:
  - `StrategyProfile`-Datenmodell (Metadata, Performance, Robustness, Regimes, Tiering)
  - Builder-Pattern und Export (JSON + Markdown)
- Tiering-Konfiguration in `config/strategy_tiering.toml`:
  - 14 Strategien als `core` / `aux` / `legacy` klassifiziert
  - Empfohlene Config-IDs + Live-/Trading-Flags
- CLI-Erweiterung `scripts/research_cli.py`:
  - Subcommand `strategy-profile` mit MC-/Stress-/Regime-Integration
  - Beispiel:
    `python scripts/research_cli.py strategy-profile --strategy-id rsi_reversion --use-dummy-data --with-montecarlo --with-stress --with-regime --output-format both`
- Reports:
  - JSON in `reports/strategy_profiles/`
  - Markdown in `docs/strategy_profiles/`
- Tests:
  - 34 neue Tests (StrategyProfiles + CLI) grün
  - 60 bestehende Tests weiterhin grün

---

## 7. Live-/Testnet & Operations (~91%)

**Relevante Phasen & Doku:**

* **Phase 17 – Environment & Safety**
  → `docs/LIVE_TESTNET_PREPARATION.md`
* **Phase 15 – Order-Layer (Sandbox & Routing)**
  → `docs/ORDER_LAYER_SANDBOX.md`
* **Phase 48 – Live Portfolio Monitoring & Risk Bridge**
  → `docs/PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md`
* **Phase 49 – Live Alerts & Notifications**
  → `docs/PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`
* **Live-/Testnet-Track-Status**
  → `docs/LIVE_TESTNET_TRACK_STATUS.md`

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

**Relevante Phasen & Doku:**

* **Phase 30 – Reporting & Visualization**
  → `docs/PHASE_30_REPORTING_AND_VISUALIZATION.md`
* **Research-/Portfolio-Reports (inkl. Phase 47)** – Backtest-/Experiment-/Portfolio-Reporting
* **Regime-Aware Reporting & Heatmaps** – Regime-spezifische Kennzahlen und Visualisierungen
  → `docs/PHASE_REGIME_AWARE_REPORTING.md`
* **Phase 48 & 49 – Live Monitoring & Alerts**
  → `docs/PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md`
  → `docs/PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`
* **CLI-Referenz**
  → `docs/CLI_CHEATSHEET.md`

**Kernkomponenten:**

* Reporting:

  * `src/reporting/base.py`, `backtest_report.py`, `experiment_report.py`, `portfolio_robustness_report.py`
  * `src/reporting/regime_reporting.py` – Regime-Aware Reporting
  * Plots mit `src/reporting/plots.py` (inkl. Regime-Overlay)
  * Reports für:

    * Einzel-Backtests (mit Regime-Analyse)
    * Sweeps / Experiments (mit Regime-Heatmaps)
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

* HTML-/Dashboard-Frontends für ausgewählte Reports/Monitoring-Ansichten.
* Erweiterte Monitoring-Views (Equity, Drawdown, Risk-Events in „quasi-real-time").

> **Reifegrad:** **ca. 89%** – Phase 51 fügt ein zentrales Live-Ops CLI hinzu (`live_ops.py`), das die wichtigsten Operator-Kommandos bündelt. Viel Funktionalität vorhanden, noch Luft nach oben bei UX & Dashboards.

---

## 9. Documentation & Governance (~86%)

**Relevante Doku-Dateien:**

* `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`
* `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`
* `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`
* `docs/LIVE_READINESS_CHECKLISTS.md`
* `docs/LIVE_TESTNET_TRACK_STATUS.md`
* Diverse Phasen-Dokumente (`docs/PHASE_XX_*.md`)

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

> **Reifegrad:** **ca. 88%** – Phase 52 fügt umfassende Architektur-Dokumentation und Developer-Guides hinzu. Phase 54 fügt ein Research→Live Playbook hinzu. Phase 55 konsolidiert die AI-/Claude-Dokumentation. Viel Substanz vorhanden, Meta-Struktur verbessert sich kontinuierlich.

---

## 10. Developer Experience & Tooling (~90%)

**Relevante Doku & Artefakte:**

* **Architektur & Developer-Guides (Phase 52):**
  * `docs/ARCHITECTURE_OVERVIEW.md` – High-Level-Architektur mit Diagramm
  * `docs/DEV_GUIDE_ADD_STRATEGY.md` – Neue Strategie hinzufügen
  * `docs/DEV_GUIDE_ADD_EXCHANGE.md` – Neuen Exchange-Adapter hinzufügen
  * `docs/DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md` – Neues Live-Risk-Limit hinzufügen
  * `docs/DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md` – Neues Portfolio-Rezept hinzufügen

* Projektstruktur & CLI-Cheatsheet:

  * `docs/CLI_CHEATSHEET.md`
* AI-/Prompt-Setup:

  * `docs/ai/CLAUDE_GUIDE.md` – AI-Assistenz-Guide
  * weitere AI-/Tooling-Doku in `docs/ai/`

**Relevante Bausteine:**

* Python-Projektstruktur (`src/`, `tests/`, `docs/`, `scripts/`, `config/`).
* Test-/CI-Mindset (viele Tests, klare Phasen-Commits).
* CLI-basierte Workflows:

  * Research-CLI, Preview-Skripte, Demo-Skripte.
* AI-gestützter Entwicklungs-Workflow:

  * Strukturierte Prompt-Blöcke für Claude/Cursor.
  * Konsistenter „Peak_Trade-Workflow" über mehrere Tools.

**Stärken:**

* **Phase 52**: Umfassende Architektur-Dokumentation und Developer-Guides für typische Erweiterungen
* Klare Struktur für neue Entwickler
* AI-Tools können Developer-Guides als Kontext nutzen
* Solide, nachvollziehbare Projektstruktur.
* Tests sind fester Bestandteil der Entwicklung (nicht optional).

**Weiterlesen:**

* Strategy & Portfolio → `DEV_GUIDE_ADD_STRATEGY.md`, `DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md`
* Risk & Safety → `DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md`
* Live-/Testnet & Ops → `PHASE_51_LIVE_OPS_CLI.md`
* Architektur → `ARCHITECTURE_OVERVIEW.md`
* AI-Tools sind **integriert** (nicht nur „ein bisschen Copy-Paste").

**Offene Themen:**

* (Optional) Dev-Container / Docker-Setup, um Setup-Aufwand weiter zu senken.
* CI-Pipeline (GitHub Actions o.ä.) mit automatischem Testing / Linting.
* Mehr „Developer-Guides" (z.B. „How to add a new strategy", „How to add a new exchange").

> **Reifegrad:** **ca. 90%** – sehr gut nutzbar mit umfassender Architektur-Dokumentation und Developer-Guides.

---

## 11. Highlights der letzten Phasen (47–53)

**Relevante Phasen & Doku:**

* **Phase 47 – Portfolio-Level Robustness**
  → Portfolio-Robustness-Logik & Reports (Dokument in `docs/PHASE_47_*.md`, Code in `src/experiments/portfolio_robustness.py`)
* **Portfolio Recipes & Presets**
  → `docs/PORTFOLIO_RECIPES_AND_PRESETS.md`
* **Phase 48 – Live Portfolio Monitoring & Risk Bridge**
  → `docs/PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md`
* **Phase 49 – Live Alerts & Notifications**
  → `docs/PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`
* **Live-/Testnet-Track-Status**
  → `docs/LIVE_TESTNET_TRACK_STATUS.md`

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

5. **Phase 50 – Live Alert Webhooks & Slack**

   * Webhook- und Slack-Sinks für das Alert-System.
   * `src/live/alerts.py` erweitert um HTTP-/Slack-Integration.
   * Konfiguration über `[live_alerts]` Block in `config.toml`.

6. **Phase 51 – Live-Ops-CLI**

   * `scripts/live_ops.py` als zentraler Entry-Point für Live-Operationen.
   * Subcommands: `orders`, `portfolio`, `alerts`, `health`.
   * Ein einziger CLI-Entry-Point für Operatoren.

7. **Phase 52 – Architecture Overview & Developer-Guides**

   * `docs/ARCHITECTURE_OVERVIEW.md` mit High-Level-Diagramm.
   * Developer-Guides für typische Erweiterungen:
     * `DEV_GUIDE_ADD_STRATEGY.md`
     * `DEV_GUIDE_ADD_EXCHANGE.md`
     * `DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md`
     * `DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md`

8. **Phase 53 – Strategy & Portfolio Library Push**

   * Klar benannte Strategie-Konfigurationen (`[strategy.*]` in `config.toml`):
     * RSI-Reversion (BTC/ETH, 3 Risk-Profile)
     * MA-Crossover (BTC, 3 Risk-Profile)
     * Trend-Following (ETH, 3 Risk-Profile)
   * 5 neue Portfolio-Recipes mit expliziten Risk-Profilen:
     * `rsi_reversion_conservative`, `rsi_reversion_moderate`, `rsi_reversion_aggressive`
     * `multi_style_moderate`, `multi_style_aggressive`
   * Risk-Profile-Schema: `conservative`, `moderate`, `aggressive`
   * Naming-Konvention: `<family>_<market>_<profile>`

9. **Phase 71 – Live-Execution-Design & Gating**

10. **Phase 72 – Live-Operator-Konsole & Status-CLI (Read-Only)**

    **Status:** ✅ Abgeschlossen (100%)

    **Ziel:** Read-Only Operator-Interface für transparenten Live-/Gating-/Risk-Status

    **Was implementiert wurde:**
    * `scripts/live_operator_status.py` – Status-CLI für Operatoren
    * Status-Report-Generierung mit allen relevanten Informationen
    * Integration von `is_live_execution_allowed()` für klare Gating-Erklärungen
    * LiveRiskLimits-Anzeige (Phase 71: Design)
    * Phase-71/72-Hinweise für Operatoren
    * Tests für Status-Logik

    **WICHTIG:** Phase 72 ist **reiner Status & Transparenz** – keine Config-Änderungen, keine State-Änderungen, keine echten Orders.

    **Details:** Siehe [`docs/PHASE_72_LIVE_OPERATOR_CONSOLE.md`](PHASE_72_LIVE_OPERATOR_CONSOLE.md)

11. **Phase 73 – Live-Dry-Run Drills & Safety-Validation**

    **Status:** ✅ Abgeschlossen (100%)

    **Ziel:** Systematische Sicherheitsübungen im Dry-Run zur Validierung von Gating & Safety-Mechanismen

    **Was implementiert wurde:**
    * Drill-System (`src/live/drills.py`) mit `LiveDrillScenario`, `LiveDrillResult`, `LiveDrillRunner`
    * Standard-Drills definiert (A-G: Voll gebremst, Gate 1/2, Dry-Run, Token, Risk-Limits, Nicht-Live)
    * CLI für Drill-Ausführung (`scripts/run_live_dry_run_drills.py`)
    * Tests für Drill-Logik
    * Dokumentation

    **WICHTIG:** Phase 73 ist **reine Simulation & Validierung** – keine Config-Änderungen, keine State-Änderungen, keine echten Orders.

    **Details:** Siehe [`docs/PHASE_73_LIVE_DRY_RUN_DRILLS.md`](PHASE_73_LIVE_DRY_RUN_DRILLS.md)

12. **Phase 74 – Live-Config Audit & Export (Read-Only)**

    **Status:** ✅ Abgeschlossen (100%)

    **Ziel:** Audit-Snapshot für Governance, Audits und "Proof of Safety"

    **Was implementiert wurde:**
    * Audit-Modul (`src/live/audit.py`) mit `LiveAuditSnapshot`, `LiveAuditGatingState`, etc.
    * CLI für Audit-Export (`scripts/export_live_audit_snapshot.py`)
    * JSON- und Markdown-Export
    * Tests für Audit-Logik
    * Dokumentation

    **WICHTIG:** Phase 74 ist **reiner Audit-Export** – keine Config-Änderungen, keine State-Änderungen, keine Token-Werte exportiert.

    **Details:** Siehe [`docs/PHASE_74_LIVE_AUDIT_EXPORT.md`](PHASE_74_LIVE_AUDIT_EXPORT.md)

13. **Phase 80 – Strategy-to-Execution Bridge & Shadow/Testnet Runner v0**

    **Status:** ✅ Abgeschlossen (100%)

    **Ziel:** Orchestrierter Flow von konfigurierten Strategien über Signale zu Orders via ExecutionPipeline

    **Was implementiert wurde:**
    * `LiveSessionRunner` + `LiveSessionConfig` + `LiveSessionMetrics` (`src/execution/live_session.py`)
    * CLI `scripts/run_execution_session.py` (Shadow/Testnet-Sessions)
    * Shadow/Testnet-Session-Flow: Strategy → Signals → Orders → `ExecutionPipeline.execute_with_safety()`
    * LIVE-Mode explizit und hart blockiert (Safety-First, an 3 Stellen)
    * Integration mit bestehenden Safety-Komponenten (SafetyGuard, LiveRiskLimits, ExecutionPipeline)
    * 24 Tests (Config, Runner, CLI, Pipeline-Integration) grün

    **WICHTIG:** Phase 80 ist **Safety-First** – LIVE-Mode ist technisch blockiert, nur Shadow/Testnet erlaubt.

    **Details:** Siehe [`docs/PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md`](PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md)

14. **Phase 81 – Live-Session-Registry & Report-CLI**

    **Status:** ✅ Abgeschlossen

    **Ziel:** Live-/Shadow-/Testnet-Sessions analog zu Experiment-Runs erfassen und auswerten.

    **Kernpunkte:**

    * **Datenmodell & Storage**
      * `LiveSessionRecord` (analog zu `SweepResultRow`) als zentrale Dataclass für einzelne Live-Session-Runs
      * Felder u.a.: `session_id`, `run_id`, `run_type`, `mode`, `env_name`, `symbol`, `status`, `started_at`, `finished_at`, `config`, `metrics`, `cli_args`, `error`, `created_at`
      * Persistierung als JSON unter:
        * `reports/experiments/live_sessions/*.json`
        * 1 Datei pro Session-Run (`<timestamp>_<run_type>_<session_id>.json`)

    * **Run-Types & Modi**
      * Run-Types: `live_session_shadow`, `live_session_testnet` (erweiterbar z.B. `live_session_live`)
      * Modes: z.B. `shadow`, `testnet`, `live`, `paper`

    * **Registry-Funktionen (Code)**
      * Modul: `src/experiments/live_session_registry.py`
      * `register_live_session_run()` – persistiert einen Session-Record (Config + Metrics + CLI-Args)
      * `list_session_records()` – Query-API (Filter: Run-Type, Status, Limit)
      * `get_session_summary()` – Aggregation (Anzahl, Status-Verteilung, Total PnL, Avg Drawdown)
      * `render_session_markdown()` / `render_sessions_markdown()` – Markdown-Reports
      * `render_session_html()` / `render_sessions_html()` – HTML-Reports

    * **Integration in Execution-Flow**
      * `scripts/run_execution_session.py`: Lifecycle mit `try/except/finally`
      * Nach jeder Session (auch bei Fehler/Abbruch) wird ein `LiveSessionRecord` erzeugt und über `register_live_session_run()` registriert
      * **Safety-Design:** Fehler in der Registry werden geloggt, dürfen aber die eigentliche Session nicht abbrechen

    * **CLI-Tool für Auswertungen**
      * Skript: `scripts/report_live_sessions.py`
      * Nutzbare Flags (Auszug):
        * `--run-type` (Filter nach Run-Type, z.B. `live_session_shadow`)
        * `--status` (Filter nach Status, z.B. `completed`)
        * `--limit` (Maximalanzahl Sessions)
        * `--output-format` (`markdown` | `html` | `both`)
        * `--summary-only` (nur Summary statt aller Sessions)
        * `--output-dir` (Ziel-Verzeichnis für Reports)
        * `--stdout` (Report zusätzlich auf STDOUT ausgeben)
      * Typische Nutzung, z.B.:
        ```bash
        python scripts/report_live_sessions.py \
          --run-type live_session_shadow \
          --status completed \
          --output-format markdown \
          --summary-only \
          --stdout
        ```

    * **Qualität & Tests**
      * `tests/test_live_session_registry.py` – Roundtrip-, Persistenz-, Query-, Summary- und Renderer-Tests (31 grüne Tests)
      * `tests/test_report_live_sessions_cli.py` – CLI-Tests für Summary-only, Markdown/HTML-Output, No-Sessions-Fälle (22 grüne Tests)
      * Zusätzlich manueller Smoke-Test-Run mit dem CLI-Skript

    **Details:** Siehe [`docs/PHASE_81_LIVE_SESSION_REGISTRY.md`](PHASE_81_LIVE_SESSION_REGISTRY.md)

15. **Phase 82 – Live-Track Panel im Web-Dashboard**

    **Status:** ✅ Abgeschlossen

    **Ziel:** Live-Sessions im Web-Dashboard visualisieren

    **Was implementiert wurde:**
    * `LiveSessionSummary` Pydantic-Modell für API-Responses (`src/webui/live_track.py`)
    * `get_recent_live_sessions()` Service-Funktion
    * API-Endpoint `GET /api/live_sessions` mit Limit-Parameter
    * API-Endpoint `GET /api/health` für Health-Checks
    * Dashboard-UI mit:
      * Snapshot-Kachel (letzte Session)
      * Sessions-Tabelle (letzte N Sessions)
      * Status-Badges, PnL-Farbcodierung, Mode-Badges
    * 26 Tests (Model, Service, API, Dashboard, Integration)

    **Details:** Siehe [`docs/PHASE_82_LIVE_TRACK_DASHBOARD.md`](PHASE_82_LIVE_TRACK_DASHBOARD.md)

16. **Phase 83 – Live-Track Operator Workflow**

    **Status:** ✅ Abgeschlossen

    **Ziel:** Strukturierter Operator-Workflow für Live-Track Panel

    **Was dokumentiert wurde:**
    * Täglicher Ablauf (Pre-Session, Während Session, Post-Session)
    * Konkrete Checks im Live-Track Panel (Snapshot-Kachel, Sessions-Tabelle)
    * Fehlerbehandlung für Failed-Sessions
    * Governance-Anforderungen und Eskalationspfad
    * Quick-Reference für URLs und CLI-Befehle
    * Integration in `LIVE_DEPLOYMENT_PLAYBOOK.md` (Abschnitt 12)
    * Neues Runbook 12a in `LIVE_OPERATIONAL_RUNBOOKS.md`

    **Details:** Siehe [`docs/PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md`](PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md)

17. **Phase 84 – Live-Track Demo Walkthrough & Case Study**

    **Status:** ✅ Dokumentiert

    **Ziel:** Praxisnaher Walkthrough für Operatoren (10–15 Minuten Demo)

    **Was dokumentiert wurde:**
    * Schritt-für-Schritt Demo-Anleitung (Shadow/Testnet)
    * System-Prüfung (Dashboard, Health-Check)
    * Session-Start mit Phase-80-Runner
    * Registry-Prüfung via CLI (Phase 81)
    * Live-Track Panel Verifikation (Phase 82)
    * Plausibilitäts-Checks nach Phase 83
    * Beispiel-Szenarien (Success/Failure)
    * Quick-Reference und Checklisten

    **Details:** Siehe [`docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

18. **Phase 85 – Live-Track Session Explorer (Web-Dashboard v1)**

    **Status:** ✅ Abgeschlossen

    **Ziel:** Operatoren bekommen im Web-Dashboard eine durchsuchbare, filterbare Übersicht aller Live-Track Sessions (Shadow/Testnet/Live) inkl. Detailansicht, Metriken und Sicherheits-Hinweisen.

    **Code:**
    * `src/webui/live_track.py` – Live-Track Panel, Filter-Logik, Detail-View, Stats
    * `src/webui/app.py` – API-Endpoints für Filter, Detail und Statistiken
    * Templates: `.../index.html`, `.../session_detail.html` – UI für Liste & Detail
    * Tests: `tests/test_webui_live_track.py` (54 Tests)

    **Features:**
    * Filterbare Session-Liste über Query-Params (`mode`, `status`)
      * `/?mode=shadow`
      * `/?mode=testnet&status=failed`
    * Klickbare Sessions → Detailseite `/session/{session_id}`
      * Config-Snapshot, Kennzahlen, Dauer, Run-Typ
      * CLI-Hinweise zum Reproduzieren / Debuggen
    * API-Endpoints:
      * `/api/live_sessions?mode=testnet&status=completed`
      * `/api/live_sessions/{session_id}`
      * `/api/live_sessions/stats` (Aggregat-Statistiken)
    * Safety: Live-Sessions werden im UI mit ⚠️ hervorgehoben

    **Details:** Siehe [`docs/PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md`](PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md)

   * Live-Execution-Path als Design modelliert (Dry-Run)
   * `LiveOrderExecutor` implementiert (nur Logging, keine echten Orders)
   * Factory-Funktion `create_order_executor()` für Execution-Pfad-Auswahl
   * Zweistufiges Gating (`enable_live_trading` + `live_mode_armed`)
   * `live_dry_run_mode = True` blockt echte Orders technisch
   * Live-spezifische Limits in Config modelliert:
     * `max_live_notional_per_order`
     * `max_live_notional_total`
     * `live_trade_min_size`
   * Tests für Design & Gating hinzugefügt
   * **WICHTIG:** Keine echte Live-Order-Ausführung aktiviert!
   * Siehe [`docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md`](PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md)

Diese Bausteine schließen die Lücke zwischen:

* **Research-Robustness** (Backtests, Sweeps, Monte-Carlo, Stress)
* und **Live-/Testnet-Safety & Monitoring** (Portfolio, Risk, Alerts, Runbooks)
* und bieten eine **fertige Bibliothek aus robusten, benannten Setups**

#### Live-Track-Stack v1 & Web-Dashboard v1 – Operator-Reifegrad

Die Phasen 80/81/83/84/85 bilden zusammen den Live-Track-Stack v1 inkl. Web-Dashboard v1:

- **Phase 80** – Strategy-to-Execution Bridge (CLI-Runner, Safety-Gates vor Live)
- **Phase 81** – Live-Session-Registry & Reports (Post-Session-Metadaten & Auswertungen)
- **Phase 83** – Operator-Workflow & Runbooks (Live-Track Playbook & Runbooks, inkl. Session Explorer)
- **Phase 84** – Demo-Walkthrough & Hall-of-Fame (10–15 Minuten Demo-Flow, Onboarding & Showcases)
- **Phase 85** – Live-Track Session Explorer & Dashboard-Integration (Web-Dashboard v1 Panels & Explorer)

**Operator-Reifegrad (Stand v1.0):**

- **Technik:** Shadow-/Testnet-Flow ist End-to-End implementiert (CLI → Registry → Reports → Web-Dashboard v1).
- **Dokumentation:** Playbook, Runbooks (inkl. Dashboard-Check), Demo-Walkthrough & Storyboard sind vorhanden.
- **Safety:** Live-Mode bleibt durch Environment-Config, Risk-Limits und Safety-Gates blockiert.
- **Use-Cases:** Realistisches Testen, Monitoring, Reviews, Drills & Demos im Shadow-/Testnet-Mode sind voll unterstützt.

**Kurz-Fazit:**  
Der Live-Track-Stack v1 ist für Shadow-/Testnet-Betrieb operativ bereit („operator-ready"), 
während echte Live-Orders weiterhin bewusst nicht freigegeben sind.

---

## 12. Empfohlene nächste Schritte (Phase 54+)

Basierend auf dem aktuellen Stand (≈ 91% Gesamt-Reifegrad) bieten sich folgende nächste Phasen an:

1. **Weitere Strategie-/Portfolio-Library-Erweiterungen**

   * Mehr Strategien (z.B. Bollinger Bands, MACD als Risk-Profile-Varianten).
   * Mehr Märkte (z.B. Altcoins, traditionelle Assets).
   * Multi-Asset-Portfolios über verschiedene Asset-Klassen.

2. **Optionale Dashboards**

   * HTML-/Notebook-Dashboards für:
     * Research-Results
     * Live-Monitoring (Equity/Drawdown, Portfolio-Exposure, Risk-Events)
   * Interaktive Visualisierung von Portfolio-Robustness-Ergebnissen.

3. **CI/CD & Automation**

   * GitHub Actions für automatisches Testing / Linting.
   * Automatische Backtest-Runs bei Code-Änderungen.
   * Docker-Setup für reproduzierbare Umgebungen.

4. **Advanced Portfolio-Optimierung**

   * Risk-Parity, CVaR-Minimierung, etc.
   * Dynamische Gewichts-Anpassung basierend auf Regime-Erkennung.

5. **Live-Trading-Verfeinerung**

   * Mail-Sinks für Alerts (zusätzlich zu Webhook/Slack).
   * Alert-Throttling / Deduplizierung.
   * Historisierung von Portfolio-Snapshots & Alerts.

---

## Research v1.0 & Live-Beta – Status nach Phasen 80–86

**Research v1.0**

- Alle für v1.0 geplanten Research-Komponenten sind implementiert und getestet:
  - Strategy-Library v1.1 mit StrategyProfiles & Tiering
  - Tiered Portfolio Presets (Phase 80)
  - Research Golden Paths & Recipes (Phase 81)
  - Research QA & Szenario-Library (Phase 82)
- Insgesamt wurden im Rahmen der Micro-Phasen 80–86 **159 zusätzliche Tests** ergänzt.
- Research v1.0 steht unter **Scope-Freeze**: Änderungen passieren nur noch gezielt und rückwärts-kompatibel.

**Live-Track / Live-Beta**

- Live-/Shadow-/Testnet-Track nutzt nun:
  - Live-Gating & Risk Policies v1.0 (Phase 83)
  - Operator Dashboard & Alerts v1.0 (Phase 84)
  - Live-Beta Drill (Shadow/Testnet) als End-to-End-Validierung (Phase 85)
- Shadow-/Testnet-Stack ist als **„produktionsreif" für Beta-Einsätze** markiert.
- Echtes Live-Trading bleibt:
  - weiterhin **streng gegated** (Tiering + Profil + Policies),
  - als **„Live-Beta"** klassifiziert, nicht als voll freigegebener Produktionsmodus.

**Kurzfazit**

- ✅ Research v1.0: abgeschlossen
- ✅ Shadow-/Testnet-Beta: betriebsbereit
- ⚠️ Live-Beta: vorhanden, aber bewusst konservativ gerahmt (Gates & Policies müssen explizit passiert werden)

---

## 13. Reference Scenario

Für einen vollständigen, praxisnahen Durchlauf (Research → Portfolio-Robustheit → Playbook → Shadow/Testnet → Status-Report → Incident-Drill) siehe:

- [`docs/REFERENCE_SCENARIO_MULTI_STYLE_MODERATE.md`](REFERENCE_SCENARIO_MULTI_STYLE_MODERATE.md)

Dieses Scenario demonstriert den **aktuellen v1.0-Stack** am konkreten Beispiel des Portfolio-Presets `multi_style_moderate` und bietet einen durchinszenierten Golden Path von A–Z.

---

## 13a. v1.0 Gesamtübersicht

Für eine zusammenhängende, narrative Beschreibung von Architektur, Flows, Rollen und Governance siehe:

- [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md)

Dieses Dokument bietet eine vollständige v1.0-Übersicht mit Rollen- und Flow-Perspektive und verknüpft alle wichtigen Dokumente des Projekts.

---

## 13b. Live-Track Doc Index

Für eine zentrale Sammlung aller Live-Track-, Dashboard-, Playbook- und Safety-Dokumente siehe:

- [**Live-Track Doc Index v1.1**](./LIVE_TRACK_DOC_INDEX_V1.md) – Zentrale Übersicht für den gesamten Live-Track-Stack (Phasen 71–85), inkl. Web-Dashboard, Demo-Scripts, Operator-Workflow, Playbooks, Safety-Policies und Monitoring/Alerts.

---

## 14. Releases / Changelog

- **v1.1 – Live-Track Web-Dashboard & Demo-Pack (2025-12-08)**
  - Web-Dashboard v1.1 mit Live-Track Operator View
  - Phase-84-Demo-Walkthrough (CLI → Registry → Dashboard)
  - 2-Minuten-Demo-Script + Playbook-How-To (Abschnitt 12.5)
  - Details: [`docs/RELEASE_NOTES_V1_1_LIVE_TRACK_DASHBOARD.md`](RELEASE_NOTES_V1_1_LIVE_TRACK_DASHBOARD.md)

---

## 15. Änderungshistorie dieses Dokuments

| Datum      | Commit    | Änderung                                                        |
|------------|-----------|-----------------------------------------------------------------|
| 2025-12-07 | f015c8a   | Erste Version Live-/Testnet-Status (`LIVE_TESTNET_TRACK_STATUS.md`) |
| 2025-12-07 | c63ea36   | Abschluss Phase 49 – Live Alerts & Notifications                |
| 2025-12-07 | 226dfac   | Erstellung `PEAK_TRADE_STATUS_OVERVIEW.md` (Phasen 1–49)        |
| 2025-12-07 | (aktuell) | Update mit konkreten Phasen-Referenzen                          |
| 2025-12-07 | (aktuell) | Phase 52 – Architecture Overview & Developer-Guides             |
| 2025-12-07 | (aktuell) | Phase 53 – Strategy & Portfolio Library Push                    |
| 2025-12-07 | (aktuell) | Phase 54 – Research → Live Portfolios Playbook                  |
| 2025-12-07 | (aktuell) | Phase 55 – Clean-Up & Polishing (Docs, Status, CLI-Cheatsheet) |
| 2025-12-07 | (aktuell) | Phase 60 – Reference Scenario `multi_style_moderate`             |
| 2025-12-07 | (aktuell) | Phase 71 – Live-Execution-Design & Gating                        |
| 2025-12-07 | (aktuell) | Phase 72 – Live-Operator-Konsole & Status-CLI (Read-Only)        |
| 2025-12-07 | (aktuell) | Phase 73 – Live-Dry-Run Drills & Safety-Validation               |
| 2025-12-07 | (aktuell) | Phase 74 – Live-Config Audit & Export (Read-Only)                |
| 2025-12-08 | (aktuell) | Phase 80 – Strategy-to-Execution Bridge & Shadow/Testnet Runner v0 |
| 2025-12-08 | (aktuell) | Phase 81 – Live-Session-Registry & Report-CLI                        |
| 2025-12-08 | (aktuell) | Phase 82 – Live-Track Panel im Web-Dashboard                         |
| 2025-12-08 | (aktuell) | Phase 83 – Live-Track Operator Workflow                              |
| 2025-12-08 | (aktuell) | Phase 84 – Live-Track Demo Walkthrough & Case Study                  |
| 2025-12-08 | (aktuell) | Phase 85 – Live-Track Session Explorer (Web-Dashboard v1)           |
| 2025-12-08 | 7908106   | R&D-Strategie-Welle v1 (Armstrong, Ehlers, El Karoui, etc.)          |
| 2025-12-08 | (aktuell) | **R&D-Experiment-Welle W2 Run-Log** – Verweis auf Run-Logs hinzugefügt |
| 2025-12-09 | (aktuell) | **Phase 77** – R&D Experiment Detail & Report Viewer v1 (API v1.2, Detail-View, Report-Links) |
| 2025-12-09 | (aktuell) | **Phase 78** – R&D Report-Gallery & Multi-Run Comparison v1 (API v1.3, Batch-Endpoint, Comparison-View) |

---

**Peak_Trade** – Ein produktionsnahes Trading-Research-Framework mit integrierter Safety-First-Architektur.
