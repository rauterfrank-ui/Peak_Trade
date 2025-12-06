
# Peak_Trade – Projektstand Ende 2025

*Stand: 4. Dezember 2025*

## 1. Kurzüberblick

**Peak_Trade** ist ein modulares Trading-Framework mit Fokus auf:
- wiederholbare Backtests,
- klar gekapselte Strategien,
- Live-/Paper-Trading-Workflows mit zentralem Risk-Management,
- Experiment-Logging & Analyse.

Ende 2025 ist der Status: **voll funktionsfähiges MVP**, mit sauberer Architektur, Doku, Tests und CI.

---

## 2. Architektur auf einen Blick

### 2.1 Haupt-Layer

- **Data-Layer (`src/data/`)**
  - Loader (CSV/Kraken/etc.)
  - Normalisierung von OHLCV-Daten
  - Parquet-Cache
- **Strategy-Layer (`src/strategies/`)**
  - OOP-Strategien mit `BaseStrategy` + `StrategyMetadata`
  - Factory für Strategieerzeugung aus Config/Registry
- **Backtest-Layer (`src/backtest/`)**
  - `BacktestEngine.run_realistic(...)` für Bar-für-Bar-Simulation
  - `BacktestResult` mit Equity, Drawdown, Trades, Stats
  - `compute_backtest_stats(...)` für Standard-Kennzahlen
- **Live-/Paper-Layer (`src/live/` + `scripts/*`)**
  - `LiveRiskLimits` mit konfigurierbaren Limits
  - zentraler Helper `run_live_risk_check(...)`
  - Scripts für Preview, Paper-Trade, Risk-Checks
- **Experiments & Registry (`src/core/experiments.py`)**
  - `RUN_TYPE_*`-Konstanten
  - Logging-Helper (Backtest, Paper, Live-Risk)
  - Analyse-Tools (`list_experiments`, `show_experiment`)
- **Doku & DX (`docs/`, `README.md`)**
  - Einstieg, Architektur, Dev-Setup
  - Strategy-Guide, Engine-Doku
  - Live-Workflows & Risk-Limits
  - Roadmap

---

## 3. Was heute zuverlässig funktioniert

### 3.1 Backtests

- Zentrales Script: `scripts/run_backtest.py`
- Flow:
  1. Config laden (`PeakConfig`)
  2. Daten laden & normalisieren
  3. Strategie über Factory instanziieren
  4. Backtest via `BacktestEngine.run_realistic(...)`
  5. Stats via `compute_backtest_stats(...)`
  6. Logging in Registry (`RUN_TYPE_BACKTEST`)

- Smoke-Tests decken ab:
  - Importierbarkeit des Pakets
  - Backtest-Smoke (künstliche Daten, MA-Crossover)
  - Strategien aus Config
  - Live-/Paper-Module

### 3.2 Strategien

- OOP-Strategien mit `KEY` + `from_config()`:
  - `MACrossoverStrategy` (`"ma_crossover"`)
  - `RsiReversionStrategy` (`"rsi_reversion"`)
  - `DonchianBreakoutStrategy` (`"breakout_donchian"`)
- Strategy-Factory:
  - Baut Instanzen aus `config.toml` + Registry-Metadaten
- Legacy-Strategien:
  - Noch vorhanden, per Fallback angebunden
  - OOP-Migration als klar definierter nächster Schritt

### 3.3 Experiments & Registry

- Einheitliches Schema mit u. a.:
  - `run_id`, `run_type`, `run_name`, `timestamp`
  - `strategy_key`, `symbol`, Zeitraum
  - `stats_json`, `metadata_json`
- Run-Typen u. a.:
  - `backtest`
  - `paper_trade`
  - `live_risk_check`
  - `portfolio_backtest`, `forward_signal`, `sweep`, `market_scan` (reserviert/teilweise genutzt)
- Tools:
  - `scripts/list_experiments.py` (Auflistung/FILTER)
  - `scripts/show_experiment.py` (Detailansicht)

### 3.4 Live-/Paper-Workflows & Risk

- Zentrales Risk-Modul:
  - `LiveRiskLimits`, `LiveRiskConfig`, `LiveRiskCheckResult`
  - Limits: Tagesverlust (absolut/prozent), Exposure gesamt/Symbol, max. offene Positionen, max. Order-Notional
  - Optionale PnL-Aggregation über Registry (`use_experiments_for_daily_pnl`)
- Zentraler Risk-Helper:
  - `run_live_risk_check(orders, ctx, ...)`
  - Berücksichtigt `skip/enforce`
  - Loggt Live-Risk-Checks in Registry
  - wirft `LiveRiskViolationError` bei Verletzung + `enforce=True`
- Scripts (vereinheitlichte CLI):
  - `scripts/preview_live_orders.py`
  - `scripts/paper_trade_from_orders.py`
  - `scripts/check_live_risk_limits.py`
- Dokumentation:
  - `docs/LIVE_WORKFLOWS.md`
  - `docs/LIVE_RISK_LIMITS.md`

### 3.5 DX, Packaging, Tests, CI

- **Doku**
  - `README.md` als schlanker Einstieg
  - `docs/ARCHITECTURE.md` mit Layer-Übersicht & Diagrammen
  - `docs/DEV_SETUP.md` mit Setup/IDE/Workflows
  - Weitere Detail-Docs (Strategy, Engine, Live)
- **Packaging**
  - `pyproject.toml` mit Paketname `peak_trade`
  - Editable Install möglich: `pip install -e ".[dev]"`
- **Tests**
  - `tests/` mit ~27 Tests (Imports, Backtest, Strategien, Live)
- **CI**
  - GitHub Actions Workflow (`.github/workflows/ci.yml`)
  - Testmatrix: Python 3.9, 3.10, 3.11
  - Pytest-Run + Coverage (3.11)
  - Linting vorbereitet (TODO für ruff/black)

---

## 4. Bekannte offene Punkte (bewusst vertagt)

- Legacy-Strategien noch nicht vollständig auf OOP-API migriert
- Kein voll integrierter echten Exchange-Live-Connector (z. B. ccxt basierter Broker)
- Tests decken vor allem Happy Paths ab, wenig Edge-Cases / Property-Tests
- Kein fertiges Docker-Image / Deployment-Template
- Kein UI/Frontend für Experiment-Browsing (nur CLI)

Diese Punkte sind bewusst für “die nächsten 10 %” bzw. 2026+ markiert.

---

## 5. Fazit Ende 2025

Ende 2025 ist **Peak_Trade**:

- **Technisch solide**: klare Schichten, OOP-Strategien, Live-Risk, Registry, Tests, CI.
- **Benutzbar**: Backtests & Paper-Sessions lassen sich per CLI und Config reproduzierbar fahren.
- **Erweiterbar**: neue Strategien, Datenquellen und Workflows können auf klaren Patterns aufsetzen.
- **Bereit für den nächsten Schritt**: echte Live-Anbindung, mehr Robustheit, und strategische Erweiterungen.
