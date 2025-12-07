# Peak_Trade v1.0 – Release Notes (Research & Live-Beta)

> **Status:** Research v1.0 abgeschlossen (Scope-Freeze), Live-Track: Shadow/Testnet produktionsreif, Live weiterhin als „Beta" klassifiziert.

---

## 1. Überblick

**Peak_Trade v1.0** markiert den Zustand, in dem:

- die komplette Research-/Backtest-Plattform stabil, reproduzierbar und durch Tests/Docs abgesichert ist (**Research v1.0**), und
- der Live-Track (Shadow/Testnet) über klare Gates, Policies und Operator-Tools verfügt und für kontrollierte Beta-Einsätze geeignet ist (**Live-Beta**).

Dieses Dokument fasst die wichtigsten Bausteine, Änderungen und Einschränkungen von v1.0 zusammen.

---

## 2. Kern-Features in v1.0

### 2.1 Data- & Core-Layer

- Stabiler Data-Layer mit Caching, Normalisierung und QC.
- Konfigurierbares Config-System (main/test) mit ENV-Support und sauberen Defaults.
- Backtest-Engine für Single-Strategien und Portfolios mit:
  - Performance-Metriken (CAGR, Sharpe, MaxDD, Volatilität, etc.).
  - Portfolio-Level-Backtests und Risiko-Auswertung.

### 2.2 Strategy-Library & StrategyProfiles

- Strategy-Library v1.1 mit mehreren Kernstrategien (z.B. RSI-Reversion, Breakout, etc.).
- Zentrales `StrategyProfile`-Datenmodell mit:
  - Metadata
  - PerformanceMetrics
  - RobustnessMetrics (z.B. Monte-Carlo/Stress)
  - RegimeProfile
  - StrategyTieringInfo (`core`, `aux`, `legacy`)
- Tiering-Config in `config/strategy_tiering.toml`:
  - Strategien mit Tier, empfohlener Config-ID und Live-Flags.

### 2.3 Research-Pipeline v2

- Research-Pipeline mit:
  - Sweeps (Parameter-Scans)
  - optionalem Walk-Forward
  - optionaler Monte-Carlo-Analyse
  - optionalen Stress-Tests
- CLI-Integration (z.B. `research_cli.py`) für komplette Pipelines.
- StrategyProfile- & Report-Erzeugung als Standard-Ausgabe.

### 2.4 Portfolio & Regime

- Regime-Detection und Regime-Reporting.
- Regime-aware Portfolio-Presets & Sweeps.
- Tiered Portfolio Presets v1.0:
  - Nutzung von `core` / `aux` / `legacy` bei Portfolio-Zusammenstellungen.
  - Presets z.B. für Balanced-, Trend+MeanReversion- und Aggro-Setups.

---

## 3. Micro-Phasen 80–86 (Mini-Roadmap umgesetzt)

Im Rahmen der Mini-Roadmap wurden die Micro-Phasen 80–86 vollständig umgesetzt. Auszug (Details siehe Phasen-Dokumente):

- **Phase 80 – Tiered Portfolio Presets v1.0**
  - Tier-basierte Portfolio-Presets auf Basis von `strategy_tiering.toml`.
  - Eigene Testsuite für Preset-/Tiering-Logik.
- **Phase 81 – Research Golden Paths & Recipes**
  - Dokumentierte Golden Paths für typische Research-Flows.
- **Phase 82 – Research QA & Szenario-Library**
  - Szenario-Configs und End-to-End Research-Tests.
- **Phase 83 – Live-Gating & Risk Policies v1.0**
  - Live-Gates & Policies als Brücke von Research → Shadow/Testnet/Live.
- **Phase 84 – Operator Dashboards & Alerts v1.0**
  - CLI-Dashboards & erste Alerts für Operatoren.
- **Phase 85 – Live-Beta Drill (Shadow/Testnet)**
  - End-to-End Drill für Shadow/Testnet.
- **Phase 86 – Research v1.0 Freeze & Live-Beta Label**
  - Scope-Freeze für Research v1.0 und formale Live-Beta-Klassifikation.

Verweise:

- `docs/PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md`
- Phasen-Dokumente: `PHASE_80_…` bis `PHASE_86_…`
- `docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md`

---

## 4. Live-Track & Live-Beta

### 4.1 Live-Gates & Policies

- Live-Gates-Modul (z.B. `src/live/live_gates.py`) mit:
  - Eligibility-Checks basierend auf:
    - Tier (`core`)
    - Live-Permissions (`allow_live`)
    - optionalen Profil-Metriken (Sharpe, MaxDD, Monte-Carlo-Spanne).
- `config/live_policies.toml` definiert:
  - globale und/oder pro-Strategie Grenzwerte.

### 4.2 Operator-Tools

- Operator-Dashboard-Skript(e), z.B.:
  - Übersicht über Strategien, Tiering, Live-Eligibility.
  - Status der letzten Research-/Profil-Runs.
- Alerts z.B. für:
  - veraltete Profile,
  - verletzte Policies.

### 4.3 Live-Beta Drill (Shadow/Testnet)

- Live-Beta Drill (Phase 85) als End-to-End-Simulation:
  - Nutzung der Live-Gates.
  - Start von Shadow-/Testnet-Sessions.
  - Incident-Simulation (z.B. Datenlücken, Drawdown).

---

## 5. Tests & Qualität

- Im Projekt wurden über die Zeit eine umfangreiche Testsuite aufgebaut (Details siehe CI/Status-Doku).
- Im Rahmen der Micro-Phasen 80–86 kamen über 150 zusätzliche Tests hinzu.
- Sämtliche Research-/Portfolio-/Live-Beta-Funktionen laufen:
  - offline,
  - reproduzierbar,
  - ohne externe Secrets/Keys.

---

## 6. Einschränkungen & Nicht-Ziele in v1.0

- Echtes Live-Trading ist weiterhin:
  - über harte Gates eingeschränkt,
  - als **„Live-Beta"** klassifiziert.
- Keine Garantie für Produktionsreife in volatilen Echtmarkt-Umgebungen:
  - v1.0 richtet sich primär an Research, Shadow und Testnet.
- Erweiterte Multi-Asset-/Multi-Exchange-Live-Deployments sind Thema für zukünftige Versionen.

---

## 7. Ausblick auf v1.1 / v2

Mögliche Themen für künftige Versionen:

- Erweiterte Universe-Unterstützung (mehr Assets/Exchanges).
- Tiefere Portfolio-Optimierung (z.B. Risk Parity, CVaR).
- Erweiterte Operator-UI (Web-Dashboards).
- Automatisierte „Continuous Research"-Pipelines.
- Weitere Guardrails und Observability für echten Live-Betrieb.

---

## 8. Tagging & Versionierung

Empfohlene Git-Tags für diesen Stand (vom User manuell zu setzen):

- `v1.0-research`
- `v1.0-live-beta`

Diese Release Notes beschreiben den Stand, auf den diese Tags zeigen sollten.
