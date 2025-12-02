# Peak_Trade – Phase 1 + Phase 2

**Risk-First Algorithmic Trading Framework**

## Überblick

Peak_Trade ist ein Python-basiertes Trading-Framework mit Fokus auf:
- **Robuste Backtest-Engine** (Kommission, Slippage, realistische Simulation)
- **Multi-Strategy-Portfolio-Management**
- **Professionelles Risk-Management** (Position-Sizing, Drawdown-Guards)
- **Saubere Architektur** (modulare Strategien, pluggable Risk-Module)

## Installation

```bash
# Dependencies installieren
pip install pandas numpy

# Optional: Für erweiterte Features
pip install matplotlib scipy
```

## Projektstruktur

```
Peak_Trade/
├── src/
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py          # BacktestEngine
│   │   └── results.py         # BacktestResult
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py            # BaseStrategy
│   │   ├── registry.py        # Strategy-Registry
│   │   ├── ma_crossover.py    # MA-Crossover
│   │   ├── rsi_reversion.py   # RSI Mean-Reversion
│   │   └── bollinger_band.py  # Bollinger-Bands
│   ├── portfolio/
│   │   ├── __init__.py
│   │   └── manager.py         # PortfolioManager
│   └── risk/
│       ├── __init__.py
│       ├── base.py            # BaseRiskModule
│       ├── position_sizing.py # Position-Sizing-Module
│       └── guards.py          # Risk-Guards
├── demo_basic.py              # Demo: Portfolio-Backtest
├── demo_risk.py               # Demo: Risk-Management
└── README.md
```

## Quick Start

### 1. Basic Portfolio-Backtest (Phase 1)

```python
from src.backtest.engine import BacktestEngine
from src.portfolio.manager import PortfolioManager, StrategyConfig

# Engine initialisieren
engine = BacktestEngine()
pm = PortfolioManager(engine)

# Strategien definieren
strategies = [
    StrategyConfig("ma_crossover", {"fast": 20, "slow": 50}, 1.0),
    StrategyConfig("rsi_reversion", {"period": 14}, 1.0),
]

# Backtest ausführen
result = pm.run_portfolio(df, strategies)
print(result.stats)
```

### 2. Risk-Management (Phase 2)

```python
from src.backtest.engine import BacktestEngine
from src.risk.position_sizing import FixedFractionalPositionSizer
from src.risk.guards import MaxDrawdownGuard

engine = BacktestEngine()

risk_modules = [
    FixedFractionalPositionSizer(risk_fraction=0.01),
    MaxDrawdownGuard(max_drawdown=0.20),
]

result = engine.run_realistic(
    df=df,
    strategy_name="ma_crossover",
    params={"fast": 20, "slow": 50},
    risk_modules=risk_modules,
)
```

## Verfügbare Strategien

1. **ma_crossover**: Moving-Average-Crossover
   - Parameter: `fast`, `slow`
   
2. **rsi_reversion**: RSI Mean-Reversion
   - Parameter: `period`, `upper`, `lower`
   
3. **bollinger_band**: Bollinger-Bands
   - Parameter: `window`, `num_std`

## Verfügbare Risk-Module

### Position-Sizing

1. **FixedFractionalPositionSizer**
   - Fixed-Fractional Position-Sizing
   - Parameter: `risk_fraction` (default: 0.01)

2. **VolatilityTargetPositionSizer**
   - Volatility-Targeting
   - Parameter: `target_vol_annual`, `lookback_days`, `max_leverage`

### Guards

1. **MaxDrawdownGuard**
   - Hard-Stop bei Drawdown-Schwelle
   - Parameter: `max_drawdown` (default: 0.2)

2. **DailyLossGuard**
   - Stop bei Tagesverlusten
   - Parameter: `max_daily_loss` (default: 0.05)

## Demo ausführen

```bash
# Basic Portfolio-Backtest
python demo_basic.py

# Risk-Management Demo
python demo_risk.py
```

## BacktestResult Struktur

```python
result.equity_curve      # pd.Series: Equity über Zeit
result.trades            # pd.DataFrame: Alle Trades
result.stats             # Dict: Kennzahlen
result.drawdown_curve    # pd.Series: Drawdowns
result.daily_returns     # pd.Series: Tagesrenditen
result.metadata          # Dict: Zusatzinfos
```

## Wichtige Stats

- `total_return`: Gesamtrendite
- `cagr`: Annualisierte Rendite
- `sharpe`: Sharpe-Ratio
- `max_drawdown`: Maximaler Drawdown
- `max_drawdown_duration_bars`: Dauer des Max-DD

## Nächste Schritte

1. **Echte Daten integrieren** (Kraken-API, CSV-Import)
2. **Weitere Strategien implementieren** (MACD, ECM, etc.)
3. **Advanced Risk-Module** (CVaR, Kelly-Criterion)
4. **Phase 3: El-Karoui-Quant-Layer** (BSDEs, HJB, Robuste Bewertung)

## Lizenz

Proprietär – Franky's Peak_Trade Framework
