"""
DEMO: Risk-Module in Action (Phase 2)

Zeigt Nutzung von Position-Sizing und Risk-Guards.
"""
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine
from src.risk.position_sizing import FixedFractionalPositionSizer
from src.risk.guards import MaxDrawdownGuard, DailyLossGuard

# Testdaten erstellen
print("Erstelle Testdaten...")
np.random.seed(42)
dates = pd.date_range("2020-01-01", "2023-12-31", freq="1D")
prices = 100 * np.exp(np.cumsum(np.random.randn(len(dates)) * 0.02))
df = pd.DataFrame({"close": prices}, index=dates)

# Engine + Risk-Module
engine = BacktestEngine(
    commission_perc=0.0005,
    slippage_perc=0.0002,
)

risk_modules = [
    # 1. Position-Sizing: 1% Kapital pro 1.0 Exposure
    FixedFractionalPositionSizer(risk_fraction=0.01),
    
    # 2. Max-Drawdown-Guard: Stop bei -20%
    MaxDrawdownGuard(max_drawdown=0.20),
    
    # 3. Daily-Loss-Guard: Stop bei -5% Tagesverlust
    DailyLossGuard(max_daily_loss=0.05),
]

# Backtest ausführen
print("\nFühre Backtest mit Risk-Management aus...")
result = engine.run_realistic(
    df=df,
    strategy_name="ma_crossover",
    params={"fast": 20, "slow": 50},
    risk_modules=risk_modules,
    initial_capital=100_000.0,
)

# Ergebnisse ausgeben
print("\n" + "="*60)
print("BACKTEST WITH RISK MANAGEMENT")
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

print("\n--- METADATA ---")
for key, value in result.metadata.items():
    print(f"{key}: {value}")
