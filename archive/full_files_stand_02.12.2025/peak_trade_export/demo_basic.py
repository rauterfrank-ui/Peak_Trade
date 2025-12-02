"""
DEMO: Basic Portfolio Backtest (Phase 1)

Zeigt grundlegende Nutzung ohne Risk-Module.
"""
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine
from src.portfolio.manager import PortfolioManager, StrategyConfig

# Testdaten erstellen
print("Erstelle Testdaten...")
np.random.seed(42)
dates = pd.date_range("2020-01-01", "2023-12-31", freq="1D")
prices = 100 * np.exp(np.cumsum(np.random.randn(len(dates)) * 0.02))
df = pd.DataFrame({"close": prices}, index=dates)

# Engine initialisieren
engine = BacktestEngine(
    commission_perc=0.0005,  # 5 bps
    slippage_perc=0.0002,    # 2 bps
)

# Portfolio-Manager erstellen
pm = PortfolioManager(engine)

# Strategien definieren
strategies = [
    StrategyConfig(
        name="ma_crossover",
        params={"fast": 20, "slow": 50},
        weight=1.0,
    ),
    StrategyConfig(
        name="rsi_reversion",
        params={"period": 14, "upper": 70, "lower": 30},
        weight=1.0,
    ),
    StrategyConfig(
        name="bollinger_band",
        params={"window": 20, "num_std": 2.0},
        weight=1.0,
    ),
]

# Backtest ausführen
print("\nFühre Portfolio-Backtest aus...")
result = pm.run_portfolio(
    df=df,
    strategies=strategies,
    initial_capital=100_000.0,
)

# Ergebnisse ausgeben
print("\n" + "="*60)
print("PORTFOLIO BACKTEST RESULTS")
print("="*60)

print("\n--- STATS ---")
for key, value in result.stats.items():
    if isinstance(value, float):
        print(f"{key:30s}: {value:>12.4f}")
    else:
        print(f"{key:30s}: {value:>12}")

print("\n--- EQUITY CURVE (Last 10) ---")
print(result.equity_curve.tail(10))

print("\n--- TRADES (First 5) ---")
if not result.trades.empty:
    print(result.trades.head())
else:
    print("No trades executed.")

print("\n--- WORST DRAWDOWNS ---")
print(result.drawdown_curve.nsmallest(5))
