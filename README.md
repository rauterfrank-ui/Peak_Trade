# Peak_Trade

Modularer Trading- und Backtest-Stack für Krypto-Strategien.

**Aktueller Stand:** Phase 1-4 abgeschlossen – Data Layer, Backtest Engine, Strategy Registry, Risk Management und Live/Paper-Trading Pipeline sind produktionsreif.

---

## Disclaimer

**Trading birgt erhebliche Risiken.** Dieses Projekt dient zu Bildungs- und Forschungszwecken. Verwende niemals Kapital, dessen Verlust du dir nicht leisten kannst.

---

## Features

- **Data Layer** – Kraken API, CSV-Import, Caching (Parquet)
- **Backtest Engine** – Realistic Mode mit Fees, Slippage, Stop-Loss
- **Strategy Registry** – OOP-Strategien (MA Crossover, RSI, Donchian), einfach erweiterbar
- **Position Sizing** – Fixed Fractional, ATR-based, Kelly
- **Risk Management** – Daily Loss, Max Drawdown, Exposure Limits
- **Forward/Paper Trading** – Signal-Generierung, Order-Preview, Paper-Broker
- **Live-Risk-Limits** – Konfigurierbarer Pre-Trade-Check
- **Experiment Registry** – Automatisches Tracking aller Runs (CSV)
- **Jupyter Analytics** – Notebook-Templates für Sweep-/Portfolio-Analyse

---

## Quickstart

### 1. Installation

```bash
# Repository klonen
git clone <repo-url>
cd Peak_Trade

# Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

### 2. Konfiguration

Kopiere `config.toml.example` (falls vorhanden) oder erstelle `config.toml`:

```toml
[general]
active_strategy = "ma_crossover"

[strategy.ma_crossover]
fast_window = 20
slow_window = 50
price_col = "close"

[backtest]
initial_capital = 10000.0
fee_bps = 10.0
slippage_bps = 5.0

[risk_management]
max_daily_loss_pct = 5.0
max_drawdown_pct = 15.0
```

### 3. Backtest ausführen

```bash
# Standard-Backtest mit Dummy-Daten
python scripts/run_backtest.py

# Mit CSV-Daten
python scripts/run_backtest.py --data-file data/btc_eur_1h.csv

# Mit anderer Strategie
python scripts/run_backtest.py --strategy rsi_reversion
```

### 4. Forward-Signale & Paper-Trading

```bash
# 1. Forward-Signale generieren
python scripts/generate_forward_signals.py --strategy ma_crossover

# 2. Order-Preview erstellen
python scripts/preview_live_orders.py --signals reports/forward/*_signals.csv

# 3. Paper-Trade ausführen
python scripts/paper_trade_from_orders.py --orders reports/live/*_orders.csv
```

---

## Projektstruktur

```
Peak_Trade/
├── config.toml              # Zentrale Konfiguration
├── src/
│   ├── core/                # Config, Position Sizing, Risk
│   ├── data/                # Data Loading, Caching
│   ├── backtest/            # Engine, Stats, Reporting
│   ├── strategies/          # BaseStrategy, Registry, Strategien
│   ├── live/                # Orders, Broker, Risk-Limits, Workflows
│   └── forward/             # Forward-Signale, Evaluation
├── scripts/                 # CLI-Runner für alle Workflows
├── docs/                    # Detaillierte Dokumentation
├── reports/                 # Generierte Reports (nicht im Git)
└── tests/                   # Unit Tests
```

---

## Verfügbare Strategien

| Key | Beschreibung | Regime |
|-----|--------------|--------|
| `ma_crossover` | Moving Average Crossover (SMA/EMA) | trend_following |
| `rsi_reversion` | RSI-basierte Mean-Reversion | mean_reversion |
| `breakout_donchian` | Donchian Channel Breakout | trend_following |

Neue Strategien: siehe [docs/STRATEGY_DEV_GUIDE.md](docs/STRATEGY_DEV_GUIDE.md)

---

## CLI-Scripts Übersicht

### Backtesting

| Script | Beschreibung |
|--------|--------------|
| `run_backtest.py` | Zentraler Backtest-Runner |
| `run_strategy_from_config.py` | Strategie aus config.toml |
| `sweep_parameters.py` | Parameter-Sweep mit Grid-Search |
| `scan_markets.py` | Multi-Symbol-Scan |

### Forward/Paper Trading

| Script | Beschreibung |
|--------|--------------|
| `generate_forward_signals.py` | Forward-Signale erzeugen |
| `preview_live_orders.py` | Orders aus Signalen erstellen |
| `paper_trade_from_orders.py` | Paper-Trade-Simulation |
| `check_live_risk_limits.py` | Risk-Check ohne Ausführung |

### Analyse & Reporting

| Script | Beschreibung |
|--------|--------------|
| `list_experiments.py` | Experiment-Registry anzeigen |
| `generate_leaderboards.py` | Leaderboard-Dashboard |
| `analyze_risk_profile.py` | Risk-Monitoring-Report |
| `report_paper_kpis.py` | Paper-Trading KPI-Dashboard |

---

## Weiterführende Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architektur-Überblick |
| [BACKTEST_ENGINE.md](docs/BACKTEST_ENGINE.md) | Backtest-Engine Details |
| [STRATEGY_DEV_GUIDE.md](docs/STRATEGY_DEV_GUIDE.md) | Neue Strategien entwickeln |
| [LIVE_WORKFLOWS.md](docs/LIVE_WORKFLOWS.md) | Forward/Paper/Live Workflows |
| [LIVE_RISK_LIMITS.md](docs/LIVE_RISK_LIMITS.md) | Live-Risk-Limits Konfiguration |
| [Peak_Trade_Roadmap.md](docs/Peak_Trade_Roadmap.md) | Projekt-Roadmap |
| [DEV_SETUP.md](docs/DEV_SETUP.md) | Entwickler-Setup |

---

## Experiment Registry

Alle Runs werden automatisch in `reports/experiments/experiments.csv` geloggt:

```bash
# Alle Experimente anzeigen
python scripts/list_experiments.py

# Nach Sharpe sortieren
python scripts/list_experiments.py --sort-by sharpe

# Nur Backtests
python scripts/list_experiments.py --run-type single_backtest
```

Run-Types: `single_backtest`, `sweep`, `portfolio`, `market_scan`, `forward_signals`, `forward_eval`, `paper_trade`, `live_risk_check`

---

## Tests

```bash
# Alle Tests
pytest tests/

# Mit Coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Lizenz

Privates Projekt – alle Rechte vorbehalten.
