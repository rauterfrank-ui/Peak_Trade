# Peak_Trade – Architektur

> Stand: Phase 4 – modularer Backtest-Stack mit Strategien, Position Sizing, Risk Management, Live/Paper-Trading Pipeline.

---

## 1. Ziel des Projekts

**Peak_Trade** ist ein modularer Backtest-Framework für Krypto-Strategien.

Fokus:
- Saubere Trennung von **Daten**, **Strategie**, **Backtest-Engine**, **Position Sizing**, **Risk Management**, **Live/Paper-Trading**
- Einfache Erweiterbarkeit: neue Strategien, neue Sizing-Methoden, neue Risk-Module
- Konfiguration über eine zentrale **`config.toml`**
- Vollständiges Experiment-Tracking aller Runs

---

## 2. Layer-Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI/Scripts                          │
│  run_backtest.py, preview_live_orders.py, ...              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Core Layer                               │
│  peak_config.py, position_sizing.py, risk.py, experiments.py│
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────▼─────┐ ┌───────▼───────┐ ┌─────▼─────────┐
│  Data Layer   │ │ Strategy Layer│ │ Backtest Layer│
│  src/data/    │ │ src/strategies│ │ src/backtest/ │
└───────────────┘ └───────────────┘ └───────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────▼─────┐ ┌───────▼───────┐ ┌─────▼─────────┐
│ Forward Layer │ │  Live Layer   │ │Analytics Layer│
│ src/forward/  │ │ src/live/     │ │ src/analytics/│
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## 3. Repo Structure

### Generated artifacts: `reports/`

The `reports/` directory contains generated artifacts (HTML/PNG/JSON logs, validation outputs, etc.) and is **not tracked** in git.

- Rule: `/reports/` is ignored via `.gitignore`
- Policy: Never commit anything under `reports/` (CI/guard + local checks enforce this)
- If you accidentally tracked files: `git rm -r --cached reports`

---

## 4. Data Layer (`src/data/`)

**Verantwortung:**
- Laden von Market-Daten (Kraken API, CSV)
- Caching (Parquet/CSV)
- Normalisierung zu OHLCV-DataFrames

**Wichtige Module:**
- `kraken.py` – API-Client für Kraken
- `kraken_pipeline.py` – High-Level Data Pipeline
- `cache.py` – Disk-basiertes Caching

**Beispiel:**
```python
from src.data import fetch_kraken_data

df = fetch_kraken_data(
    symbol="BTC/EUR",
    timeframe="1h",
    limit=500
)
```

---

## 5. Strategies Layer (`src/strategies/`)

**Verantwortung:**
- Definition von Trading-Strategien
- Signal-Generierung (Long/Short/Flat)
- Zentrale Registry für einfachen Zugriff

**Architektur:**

1. **BaseStrategy (ABC)** – alle Strategien erben davon
   - `generate_signals(data: pd.DataFrame) -> pd.Series`
   - `from_config(cfg, section)` – Factory-Methode
   - `KEY` – Strategie-Identifier

2. **Konkrete Strategien:**
   - `MACrossoverStrategy` (KEY=`ma_crossover`)
   - `RsiReversionStrategy` (KEY=`rsi_reversion`)
   - `DonchianBreakoutStrategy` (KEY=`breakout_donchian`)

3. **Strategy Registry** – zentrale Verwaltung
   - `get_available_strategy_keys()` → Liste aller Keys
   - `create_strategy_from_config(key, cfg)` → Instanziierung

**Beispiel:**
```python
from src.strategies.registry import create_strategy_from_config

strategy = create_strategy_from_config("ma_crossover", cfg)
signals = strategy.generate_signals(df)
```

Siehe: [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md)

---

## 6. Core Layer (`src/core/`)

**Verantwortung:**
- Config-Management
- Position Sizing
- Risk Management
- Experiment-Tracking

### 6.1 Config (`peak_config.py`)

```python
from src.core.peak_config import load_config

cfg = load_config("config.toml")
value = cfg.get("backtest.initial_cash", 10000.0)
```

### 6.2 Position Sizing (`position_sizing.py`)

Methoden: `NoopPositionSizer`, `FixedSizeSizer`, `FixedFractionSizer`

```python
from src.core.position_sizing import build_position_sizer_from_config

sizer = build_position_sizer_from_config(cfg)
target_units = sizer.get_target_position(signal=1, price=50000.0, equity=10000.0)
```

### 6.3 Risk Management (`risk.py`)

Methoden: `NoopRiskManager`, `MaxDrawdownRiskManager`, `EquityFloorRiskManager`

```python
from src.core.risk import build_risk_manager_from_config

risk_mgr = build_risk_manager_from_config(cfg)
adjusted = risk_mgr.adjust_target_position(target_units=0.2, price=50000.0, equity=9000.0)
```

### 6.4 Experiments (`experiments.py`)

Zentrales Tracking aller Runs in `reports/experiments/experiments.csv`.

**Run-Types:**
- `backtest` – Einzel-Strategie-Backtest
- `portfolio_backtest` – Multi-Asset Portfolio-Backtest
- `forward_signal` – Forward-Signal-Generierung (Out-of-Sample)
- `live_risk_check` – Live-Risk-Limits-Prüfung
- `paper_trade` – Paper-Trade-Simulation
- `sweep` – Parameter-Sweep
- `market_scan` – Multi-Market-Scan

**Logger-Funktionen:**
```python
from src.core.experiments import (
    log_backtest_result,           # Einzel-Backtest
    log_portfolio_backtest_result, # Portfolio-Backtest
    log_forward_signal_run,        # Forward-Signal
    log_live_risk_check,           # Live-Risk-Check
    log_paper_trade_run,           # Paper-Trade
)

# Beispiel: Backtest loggen
run_id = log_backtest_result(result, strategy_name="ma_crossover")

# Beispiel: Portfolio loggen
run_id = log_portfolio_backtest_result(
    portfolio_name="core_portfolio",
    equity_curve=portfolio_equity,
    component_runs=[...],
)
```

---

## 7. Backtest Layer (`src/backtest/`)

**Verantwortung:**
- Bar-für-Bar Simulation
- Trade-Execution mit Stop-Loss
- Performance-Metriken

**Hauptkomponente: BacktestEngine**

```python
from src.backtest.engine import BacktestEngine

engine = BacktestEngine(
    core_position_sizer=sizer,
    risk_manager=risk_mgr
)

result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy_fn,
    strategy_params=params
)
```

**Features:**
- Stop-Loss-Management
- Risk-Limit-Checks
- Position-Sizing-Integration
- Trade-Tracking mit PnL

Siehe: [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md)

---

## 8. Forward Layer (`src/forward/`)

**Verantwortung:**
- Forward-Signal-Generierung
- Ex-Post-Evaluation von Signalen

**Workflow:**
1. `generate_forward_signals.py` → erzeugt `reports/forward/*_signals.csv`
2. Signale beobachten (manuell oder automatisch)
3. `evaluate_forward_signals.py` → berechnet Returns

**Signale-Format:**
- `generated_at`, `as_of`, `strategy_key`, `symbol`, `direction`, `size_hint`

---

## 9. Live Layer (`src/live/`)

**Verantwortung:**
- Order-Management
- Broker-Abstraktion (Paper, Dry-Run, Real)
- Live-Risk-Limits
- Workflow-Helper

### 9.1 Orders (`orders.py`)

```python
from src.live.orders import LiveOrderRequest

order = LiveOrderRequest(
    symbol="BTC/EUR",
    side="BUY",
    order_type="MARKET",
    quantity=0.001,
    notional=500.0
)
```

### 9.2 Broker (`broker_base.py`)

- `BaseBrokerClient` (ABC)
- `DryRunBroker` – Simuliert Fills ohne echten Handel
- `PaperBroker` – Cash- und Positionsführung

### 9.3 Live-Risk-Limits (`risk_limits.py`)

Konfigurierbarer Pre-Trade-Check:
- `max_order_notional`
- `max_symbol_exposure_notional`
- `max_total_exposure_notional`
- `max_open_positions`
- `max_daily_loss_abs` / `max_daily_loss_pct`

```python
from src.live.risk_limits import LiveRiskLimits

limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)
result = limits.check_orders(orders)
```

Siehe: [LIVE_RISK_LIMITS.md](LIVE_RISK_LIMITS.md)

### 9.4 Workflows (`workflows.py`)

Zentrale Helper für konsistentes Verhalten:

```python
from src.live.workflows import run_live_risk_check, RiskCheckContext

ctx = RiskCheckContext(config=cfg, enforce=True, skip=False)
result = run_live_risk_check(orders, ctx)
```

Siehe: [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md)

---

## 10. Analytics Layer (`src/analytics/`)

**Verantwortung:**
- Experiment-Aggregationen & Strategie-Vergleiche
- Jupyter-Notebook-Helpers
- Sweep-Visualisierung
- Portfolio-Analyse
- Markdown-Report-Generierung

**Module:**

### 10.1 Experiments-Analyse (`experiments_analysis.py`)

Aggregationen und Reports für die Experiment-Registry:

```python
from src.analytics.experiments_analysis import (
    load_experiments_df_filtered,
    summarize_strategies,
    summarize_portfolios,
    top_runs_by_metric,
    compare_strategies,
    write_markdown_report,
)

# Gefilterte Experiments laden
df = load_experiments_df_filtered(
    run_types=["backtest"],
    strategy_keys=["ma_crossover"],
)

# Strategie-Übersicht
summaries = summarize_strategies(df)  # → List[StrategySummary]

# Top Runs nach Metrik
top_df = top_runs_by_metric(df, metric="sharpe", n=10)

# Strategien vergleichen
comparison = compare_strategies(df, strategies=["ma_crossover", "rsi_reversion"])

# Markdown-Report
write_markdown_report(summaries, Path("reports/strategy_summary.md"))
```

**CLI-Script:** `scripts/analyze_experiments.py`

```bash
# Strategie-Übersicht (Backtests)
python scripts/analyze_experiments.py --mode summary --run-type backtest

# Top 10 Backtests nach Sharpe
python scripts/analyze_experiments.py --mode top-runs --metric sharpe --limit 10

# Portfolio-Runs analysieren
python scripts/analyze_experiments.py --mode portfolios

# Strategien vergleichen
python scripts/analyze_experiments.py --mode compare --strategies ma_crossover,rsi_reversion

# Markdown-Report schreiben
python scripts/analyze_experiments.py --mode summary --write-report reports/summary.md
```

### 10.2 Leaderboard (`leaderboard.py`)

Standard-Leaderboards für Experimente.

### 10.3 Notebook Helpers (`notebook_helpers.py`)

Jupyter-Helper: `load_experiments()`, `filter_experiments()`, `sweep_scatter()`, `sweep_heatmap()`

### 10.4 Risk Monitor (`risk_monitor.py`)

Risiko-Analyse und Policy-Checks für Runs.

---

## 11. Config-Philosophie (`config.toml`)

Alle Einstellungen in **einer zentralen TOML-Datei**:

```toml
[general]
active_strategy = "ma_crossover"

[backtest]
initial_cash = 10000.0

[position_sizing]
type = "fixed_fraction"
fraction = 0.1

[risk_management]
type = "max_drawdown"
max_drawdown = 0.25

[strategy.ma_crossover]
fast_window = 20
slow_window = 50

[live]
base_currency = "EUR"
starting_cash_default = 10000.0
fee_bps = 10.0
slippage_bps = 5.0

[live_risk]
enabled = true
max_daily_loss_abs = 500.0
max_total_exposure_notional = 5000.0
```

---

## 12. System-Flow (End-to-End)

```
┌─────────────────┐
│  config.toml    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Script/Runner  │────▶│  Load Config     │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Strategy       │────▶│  Registry Lookup │
│  Registry       │     │  + from_config() │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Data Pipeline  │
│  (OHLCV)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Strategy       │
│  generate_      │
│  signals()      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  BacktestEngine / LiveWorkflow      │
│  ┌─────────────────────────────┐   │
│  │  1. Position Sizer          │   │
│  │  2. Risk Manager            │   │
│  │  3. Live-Risk-Limits        │   │
│  │  4. Trade Execution         │   │
│  └─────────────────────────────┘   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Result/Report  │
│  + Registry Log │
└─────────────────┘
```

---

## 13. Erweiterbarkeit

### Neue Strategie hinzufügen

1. Strategie-Klasse erstellen (erbt von `BaseStrategy`)
2. `KEY` Attribut setzen
3. In Registry registrieren (`src/strategies/registry.py`)
4. Config-Section anlegen (`config.toml`)

Siehe: [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md)

### Neues Position Sizing

1. Klasse erstellen (erbt von `BasePositionSizer`)
2. Factory-Funktion erweitern (`build_position_sizer_from_config`)

### Neues Risk Management

1. Klasse erstellen (erbt von `BaseRiskManager`)
2. Factory-Funktion erweitern (`build_risk_manager_from_config`)

---

## 14. Best Practices

### Development

- Neue Strategien über Registry registrieren
- Config-driven – Hardcoding vermeiden
- `from_config()` für alle Strategien implementieren
- Tests mit Dummy-Daten vor Live-Daten

### Backtesting

- Realistic Mode verwenden
- Stop-Loss immer setzen
- Position Sizing aktivieren
- Risk Manager nutzen
- Genug Bars (min. 200+)

### Live/Paper Trading

- `--enforce-live-risk` für kritische Runs
- `starting_cash` für prozentuale Limits übergeben
- Registry-Logs für Audit-Trail prüfen

---

## 15. Weiterführende Dokumentation

- [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md) – Engine-Details
- [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) – Strategie-Entwicklung
- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) – Forward/Paper/Live Workflows
- [LIVE_RISK_LIMITS.md](LIVE_RISK_LIMITS.md) – Risk-Limits Konfiguration
- [Peak_Trade_Roadmap.md](Peak_Trade_Roadmap.md) – Projekt-Roadmap

---

## Lizenz

Privates Projekt – alle Rechte vorbehalten.
