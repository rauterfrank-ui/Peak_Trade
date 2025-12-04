# CLAUDE.md - Peak_Trade AI Assistant Guide

## Project Overview

**Peak_Trade** is a modular cryptocurrency trading and backtesting framework in Python 3.9+. It provides strategy development, backtesting with realistic market conditions, risk management, and live/paper trading capabilities.

## Quick Commands

```bash
# Setup
source .venv/bin/activate
pip install -e ".[dev]"

# Testing
pytest tests/ -v                              # All tests
pytest tests/test_backtest_smoke.py -v        # Specific file
pytest tests/ --cov=src --cov-report=html     # With coverage

# Linting & Formatting
ruff check src/ tests/
black src/ tests/

# Run Backtest
python scripts/run_backtest.py
python scripts/run_backtest.py --strategy rsi_reversion
python scripts/run_backtest.py --config custom_config.toml

# Sweeps & Analytics
python scripts/sweep_parameters.py --strategy ma_crossover
python scripts/list_experiments.py --sort-by sharpe
python scripts/generate_leaderboards.py

# Forward/Paper Trading
python scripts/generate_forward_signals.py --strategy ma_crossover
python scripts/check_live_risk_limits.py
python scripts/paper_trade_from_orders.py
```

## Directory Structure

```
Peak_Trade/
├── config.toml              # Central configuration (TOML)
├── config/                  # Regime/sweep configurations
├── pyproject.toml           # Dependencies & tooling
├── src/
│   ├── core/                # Config, position sizing, risk, experiments
│   ├── data/                # Data loading, caching, Kraken API
│   ├── strategies/          # Trading strategies (BaseStrategy ABC)
│   ├── backtest/            # BacktestEngine, stats, reporting
│   ├── live/                # Risk limits, orders, safety
│   ├── forward/             # Signal generation/evaluation
│   ├── orders/              # Order execution layer
│   ├── exchange/            # CCXT integration
│   ├── analytics/           # Experiment analysis, leaderboards
│   └── notifications/       # Alert system
├── scripts/                 # CLI runners (run_backtest.py, etc.)
├── tests/                   # pytest test suite
├── docs/                    # Comprehensive documentation
└── reports/                 # Generated outputs (experiments, results)
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `src/core/peak_config.py` | TOML config loading with dot-notation access |
| `src/core/position_sizing.py` | Position sizing (NoopSizer, FixedFraction, FixedSize) |
| `src/core/risk.py` | Risk management (MaxDrawdown, EquityFloor) |
| `src/core/experiments.py` | Experiment registry tracking |
| `src/strategies/base.py` | BaseStrategy ABC - all strategies inherit this |
| `src/strategies/registry.py` | Strategy lookup by key |
| `src/backtest/engine.py` | BacktestEngine - bar-by-bar simulation |
| `src/backtest/stats.py` | Performance metrics (Sharpe, Drawdown, etc.) |
| `src/live/risk_limits.py` | Pre-trade risk checks |

## Available Strategies

| Key | Type | Description |
|-----|------|-------------|
| `ma_crossover` | Trend | Moving Average Crossover |
| `rsi_reversion` | Reversion | RSI Mean-Reversion |
| `breakout_donchian` | Trend | Donchian Channel Breakout |
| `momentum_1h` | Trend | Momentum-based |
| `bollinger_bands` | Reversion | Bollinger Bands |
| `macd` | Trend | MACD Crossover |
| `trend_following` | Trend | ADX-based |
| `mean_reversion` | Reversion | Z-Score |

## Architecture Patterns

1. **Abstract Base Classes**: `BaseStrategy`, `BasePositionSizer`, `BaseRiskManager`
2. **Factory Methods**: `Strategy.from_config(cfg, section)`
3. **Dataclasses**: Type-safe data containers (`BacktestResult`, `Trade`)
4. **Registry Pattern**: Strategy and experiment registries
5. **Configuration-Driven**: All behaviors via `config.toml`

## Creating a New Strategy

```python
# src/strategies/my_strategy.py
from .base import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    KEY = "my_strategy"

    def __init__(self, param1: int = 20):
        self.param1 = param1

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Return pd.Series with values in {-1, 0, 1}
        return pd.Series(0, index=data.index)

    @classmethod
    def from_config(cls, cfg, section: str):
        return cls(param1=cfg.get(f"{section}.param1", 20))
```

Register in `src/strategies/registry.py` and add config to `config.toml`.

## Config Structure (config.toml)

```toml
[environment]
mode = "paper"                    # paper | testnet | live

[general]
base_currency = "EUR"
starting_capital = 10_000.0
active_strategy = "ma_crossover"

[position_sizing]
type = "fixed_fraction"           # noop | fixed_size | fixed_fraction
fraction = 0.1

[risk_management]
type = "max_drawdown"
max_drawdown = 0.25

[strategy.ma_crossover]
fast_window = 20
slow_window = 50

[live_risk]
enabled = true
max_daily_loss_abs = 500.0
block_on_violation = true
```

## Risk Management Layers

1. **Position Sizing** (`src/core/position_sizing.py`): signal → units
2. **Risk Management** (`src/core/risk.py`): adjusts units based on equity/drawdown
3. **Live Risk Limits** (`src/live/risk_limits.py`): pre-trade checks

## Code Style

- **Python**: 3.9+, type hints, dataclasses
- **Line length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff
- **Tests**: pytest with fixtures

## Important Notes

- Strategies return **states** (persistent positions), not events
- CLI args override `config.toml` settings
- All runs logged to `reports/experiments/experiments.csv`
- Documentation in German and English

## Key Files to Start

1. `config.toml` - Central configuration
2. `src/backtest/engine.py` - Backtest engine
3. `src/strategies/base.py` - Strategy base class
4. `scripts/run_backtest.py` - Main entry point
5. `docs/ARCHITECTURE.md` - Architecture overview
