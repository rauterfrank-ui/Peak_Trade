# PEAK_TRADE – Architektur & Schnelleinstieg

> **Modulares Trading-Framework mit Safety-First-Ansatz**

---

## Architektur-Map

Peak_Trade folgt einer klaren Pipeline-Architektur mit strikter Separation of Concerns:

```text
┌─────────────────────────────────────────────────────────────┐
│                       PEAK_TRADE PIPELINE                    │
└─────────────────────────────────────────────────────────────┘

┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│   DATA   │ ───▶ │ STRATEGY │ ───▶ │  SIZING  │ ───▶ │   RISK   │
│  FEEDS   │      │ SIGNALS  │      │ OVERLAY  │      │  LIMITS  │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
     │                  │                  │                  │
     │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                     BACKTEST ENGINE                          │
│  • Bar-für-Bar Execution (No Look-Ahead)                    │
│  • Portfolio State Management                               │
│  • Trade Tracking & PnL                                     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        REPORTING                             │
│  • Performance-Metriken (Sharpe, Drawdown, ...)            │
│  • Equity Curves & Visualisierung                          │
│  • Research Reports (Walk-Forward, Monte-Carlo, ...)       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   GOVERNANCE & LIVE TRACK                    │
│  • Go/No-Go-Decisions (Research-Pipeline)                  │
│  • Live-Session-Runner (Testnet & Production)              │
│  • Alerts, Monitoring, Operator-Console                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Wie starte ich schnell einen Backtest?

### 1. Minimaler Backtest (Command-Line)

```bash
# Mit vorhandener Config
python scripts/run_strategy_from_config.py --strategy ma_crossover --symbol BTC/USDT

# Mit Custom-Config
python scripts/run_strategy_from_config.py --config config/my_backtest.toml
```

### 2. Programmatischer Backtest (Python)

```python
from src.core.peak_config import load_config
from src.strategies.registry import create_strategy_from_config
from src.backtest.engine import BacktestEngine
from src.data.data_loader import load_ohlcv_data

# 1. Load Config
cfg = load_config("config/backtest_ma_crossover.toml")

# 2. Load Data
df = load_ohlcv_data(
    symbol=cfg.get("data.symbol", "BTC/USDT"),
    timeframe=cfg.get("data.timeframe", "1h"),
    start_date=cfg.get("data.start_date"),
    end_date=cfg.get("data.end_date")
)

# 3. Create Strategy from Registry
strategy = create_strategy_from_config("ma_crossover", cfg)

# 4. Run Backtest
engine = BacktestEngine.from_config(cfg)
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=strategy.generate_signals,
    strategy_params={}
)

# 5. Analyze Results
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
```

### 3. Minimal Config-Beispiel

**`config/my_backtest.toml`:**

```toml
[data]
symbol = "BTC/USDT"
timeframe = "1h"
start_date = "2024-01-01"
end_date = "2024-12-31"
exchange = "kraken"

[backtest]
initial_capital = 10000.0
position_fraction = 0.1  # 10% pro Trade

[strategy.ma_crossover]
fast_window = 20
slow_window = 50

[risk]
max_drawdown = 0.20
daily_loss_limit = 0.05
```

---

## Strategy Registry Keys

Alle verfügbaren Strategien sind in der **Strategy Registry** registriert (`src/strategies/registry.py`).

### Production-Ready Strategien

| Key | Beschreibung | Config Section |
|-----|-------------|----------------|
| `ma_crossover` | Moving Average Crossover | `strategy.ma_crossover` |
| `rsi_reversion` | RSI Mean-Reversion | `strategy.rsi_reversion` |
| `breakout_donchian` | Donchian Channel Breakout | `strategy.breakout_donchian` |
| `macd` | MACD Trend-Following | `strategy.macd` |
| `bollinger_bands` | Bollinger Bands Reversion | `strategy.bollinger_bands` |
| `momentum_1h` | Momentum-basierte Strategie | `strategy.momentum_1h` |
| `trend_following` | ADX Trend-Following | `strategy.trend_following` |
| `mean_reversion` | Z-Score Mean-Reversion | `strategy.mean_reversion` |

### Research-Track Strategien (R&D)

| Key | Beschreibung | Status |
|-----|-------------|--------|
| `armstrong_cycle` | Armstrong ECM Cycle Model | ✅ Live-Ready |
| `el_karoui_vol_model` | El Karoui Stochastic Vol | ✅ Live-Ready |
| `ehlers_cycle_filter` | Ehlers DSP Cycle Filter | 🔬 R&D-Only |
| `meta_labeling` | López de Prado Meta-Labeling | 🔬 R&D-Only |
| `bouchaud_microstructure` | Bouchaud Microstructure | 🔬 Skeleton |
| `vol_regime_overlay` | Gatheral/Cont Vol Overlay | 🔬 Skeleton |

**Hinweis:** R&D-Strategien benötigen `research.allow_r_and_d_strategies = true` in der Config.

---

## Sizing & Risk Config Sections

### Position Sizing

**`[sizing]` Section:**

```toml
[sizing]
type = "fixed_fraction"  # oder "fixed_size", "noop"
fraction = 0.1           # 10% des Kapitals pro Position
```

**Overlay Sizing (Erweitert):**

```toml
[sizing.overlay]
type = "vol_regime"
scaling_factors = {low = 1.5, medium = 1.0, high = 0.5}
```

### Risk Management

**`[risk]` Section:**

```toml
[risk]
type = "max_drawdown"      # oder "equity_floor", "noop"
max_drawdown = 0.20        # 20% Max Drawdown
equity_floor = 8000.0      # Absoluter Equity-Floor

# Erweitertes Risk Management
daily_loss_limit = 0.05    # 5% Tagesverlust-Limit
max_open_positions = 3     # Max 3 gleichzeitige Positionen
max_position_notional_pct = 0.3  # Max 30% Kapital pro Position
```

---

## Live-Track & Governance

### Go/No-Go Research-Pipeline

Vor einem Live-Deployment durchläuft jede Strategie eine systematische Prüfung:

1. **Backtest** – Historische Performance
2. **Walk-Forward** – Out-of-Sample-Validierung
3. **Monte-Carlo** – Robustheit gegen Zufall
4. **Stress-Tests** – Verhalten in Extremszenarien
5. **Shadow-Run** – Testnet-Monitoring (papier-basiert)
6. **Testnet-Run** – Echte Orders mit Testnet-Geld
7. **Production** – Live-Deployment mit Risk-Limits

**Dokumentation:**
- 📖 **Playbook:** [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)
- 🎯 **Live-Track Demo:** [`docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

### Live-Ops Tools

```bash
# Live-Status abrufen
python -m src.cli.live_ops status

# Portfolio-Snapshot
python -m src.cli.live_ops portfolio

# Offene Orders
python -m src.cli.live_ops orders

# Health-Check
python -m src.cli.live_ops health
```

---

## Weitere Dokumentation

### Schnelleinstieg

- 🚀 **First 7 Days:** [`PEAK_TRADE_FIRST_7_DAYS.md`](PEAK_TRADE_FIRST_7_DAYS.md)
- 📖 **v1.0 Overview:** [`PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md)

### Technische Guides

- 🏗️ **Architektur:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
- 🔬 **Backtest Engine:** [`BACKTEST_ENGINE.md`](BACKTEST_ENGINE.md)
- 🎯 **Strategy Development:** [`STRATEGY_DEV_GUIDE.md`](STRATEGY_DEV_GUIDE.md)
- 🧪 **Research-Pipeline:** [`RESEARCH_PIPELINE_V2.md`](RESEARCH_PIPELINE_V2.md)

### Developer Guides

- ⚡ **Developer Workflow:** [`DEVELOPER_WORKFLOW_GUIDE.md`](DEVELOPER_WORKFLOW_GUIDE.md)
- 🤖 **AI-Helper Guide:** [`ai/PEAK_TRADE_AI_HELPER_GUIDE.md`](ai/PEAK_TRADE_AI_HELPER_GUIDE.md)
- 📚 **Knowledge Base Index:** [`KNOWLEDGE_BASE_INDEX.md`](KNOWLEDGE_BASE_INDEX.md)

### Operations & Safety

- 🛡️ **Risk Management:** [`RISK_MANAGEMENT_V1.md`](RISK_MANAGEMENT_V1.md)
- 🚨 **Incident Drills:** [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md)
- 📊 **Monitoring & Alerts:** [`OBSERVABILITY_AND_MONITORING_PLAN.md`](OBSERVABILITY_AND_MONITORING_PLAN.md)
- 🔐 **Resilience Guide:** [`resilience_guide.md`](resilience_guide.md)

---

## Repository-Struktur

```text
Peak_Trade/
├── src/
│   ├── strategies/       # Strategy-Implementierungen
│   │   ├── registry.py   # Zentrale Strategy-Registry
│   │   ├── base.py       # BaseStrategy-Contract
│   │   └── ...
│   ├── backtest/         # Backtest-Engine
│   ├── data/             # Data-Loading & Caching
│   ├── core/             # Core-Module (Config, Sizing, Risk)
│   ├── live/             # Live-Trading-Components
│   ├── reporting/        # Reports & Visualisierung
│   └── governance/       # Go/No-Go-Logic
├── config/               # TOML-Configs für Backtests
├── scripts/              # CLI-Tools & Utilities
├── tests/                # Pytest Test-Suite
└── docs/                 # Dokumentation
```

---

## Quick Commands

```bash
# Tests ausführen
pytest -q

# Targeted Tests (Position-Sizing)
pytest tests/test_vol_regime_overlay_sizer.py -q

# Linting
python3 -m ruff check src tests scripts

# Backtest ausführen
python scripts/run_strategy_from_config.py --strategy ma_crossover

# Research-Pipeline
python scripts/run_walkforward.py --strategy ma_crossover
python scripts/run_monte_carlo.py --strategy ma_crossover
python scripts/run_stress_tests.py --portfolio moderate

# Live-Status
python -m src.cli.live_ops status
```

---

## Nächste Schritte

1. **Ersten Backtest laufen lassen:** Folge dem [Quickstart](#wie-starte-ich-schnell-einen-backtest) oben
2. **Eigene Strategie entwickeln:** Siehe [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md)
3. **Research-Pipeline testen:** Siehe [RESEARCH_PIPELINE_V2.md](RESEARCH_PIPELINE_V2.md)
4. **Live-Track kennenlernen:** Siehe [PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

---

**📌 Wichtig:** Peak_Trade ist ein Safety-First-Framework. Lies immer die Docs, bevor du etwas in Production deployest!
