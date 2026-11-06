#!/usr/bin/env python3
"""
Peak_Trade Extended Portfolio Backtest
========================================
Portfolio mit ALLEN 6 Strategien.

Strategien:
1. MA Crossover (Trend)
2. Momentum (Trend)
3. RSI (Mean-Reversion)
4. Bollinger Bands (Mean-Reversion)
5. MACD (Trend + Momentum)
6. ECM (Cycle-based)
"""

import sys
from pathlib import Path
from typing import Callable, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core import get_config, get_strategy_cfg, list_strategies
from src.strategies import load_strategy
from src.portfolio import PortfolioManager
from src.backtest.stats import validate_for_live_trading

DEMO_PORTFOLIO_STRATEGY_NAMES: tuple[str, ...] = (
    "ma_crossover",
    "momentum_1h",
    "rsi_strategy",
    "bollinger_bands",
    "macd",
    "ecm_cycle",
)


def resolve_portfolio_strategy(strategy_name: str) -> Tuple[Callable, Dict]:
    """
    Resolve strategy signal function and params via canonical loaders.

    Raises:
        ValueError: Unknown strategy name (load_strategy fail-closed).
        KeyError: Strategy not defined in config.toml (get_strategy_cfg fail-closed).
    """
    signal_fn = load_strategy(strategy_name)
    params = get_strategy_cfg(strategy_name)
    return signal_fn, params


def add_configured_strategies(
    pm: PortfolioManager,
    strategy_names: tuple[str, ...] = DEMO_PORTFOLIO_STRATEGY_NAMES,
) -> None:
    """Add each configured strategy to the portfolio via canonical load_strategy()."""
    for name in strategy_names:
        signal_fn, params = resolve_portfolio_strategy(name)
        pm.add_strategy(name, signal_fn, params=params)


def create_rich_dummy_data(n_bars: int = 1000) -> pd.DataFrame:
    """
    Erstellt reichhaltige Dummy-Daten mit diversen Markt-Phasen.

    Enthält:
    - Trends (gut für MA, Momentum, MACD)
    - Zyklen (gut für RSI, Bollinger)
    - Pi-basierte Komponente (gut für ECM)
    """
    np.random.seed(42)

    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    base_price = 50000

    # 1. Langzeit-Trend
    trend = np.linspace(0, 10000, n_bars)

    # 2. Mittelfrist-Zyklen (RSI, Bollinger)
    cycle_fast = np.sin(np.linspace(0, 12 * np.pi, n_bars)) * 2000
    cycle_slow = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 3500

    # 3. Pi-basierte Komponente (ECM)
    pi_cycle = np.sin(np.linspace(0, 2 * np.pi, n_bars)) * 1500

    # 4. Momentum-Bursts
    bursts = np.zeros(n_bars)
    for i in range(8):
        start_idx = np.random.randint(100, n_bars - 100)
        burst_length = np.random.randint(30, 60)
        bursts[start_idx : start_idx + burst_length] = np.linspace(0, 2000, burst_length)

    # 5. Volatilitäts-Cluster (Bollinger)
    volatility = np.random.randn(n_bars).cumsum() * 80

    # 6. Random Walk Noise
    noise = np.random.randn(n_bars) * 150

    close_prices = (
        base_price + trend + cycle_fast + cycle_slow + pi_cycle + bursts + volatility + noise
    )

    df = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.randn(n_bars) * 0.001),
            "high": close_prices * (1 + abs(np.random.randn(n_bars)) * 0.002),
            "low": close_prices * (1 - abs(np.random.randn(n_bars)) * 0.002),
            "close": close_prices,
            "volume": np.random.randint(50, 150, n_bars),
        },
        index=dates,
    )

    return df


def print_extended_report(result):
    """Druckt erweiterten Portfolio-Report."""

    print("\n" + "=" * 70)
    print("FULL PORTFOLIO BACKTEST - 6 STRATEGIEN")
    print("=" * 70)

    # Portfolio-Performance
    print("\n💼 PORTFOLIO PERFORMANCE")
    print("-" * 70)
    start = result.portfolio_equity.iloc[0]
    end = result.portfolio_equity.iloc[-1]

    print(f"Start Capital:     ${start:,.2f}")
    print(f"End Capital:       ${end:,.2f}")
    print(f"Total Return:      {result.stats['total_return']:>7.2%}")
    print(f"Max Drawdown:      {result.stats['max_drawdown']:>7.2%}")
    print(f"Sharpe Ratio:      {result.stats['sharpe']:>7.2f}")
    print(f"Total Trades:      {result.stats['total_trades']:>7}")

    # Strategien nach Performance sortiert
    print("\n📊 STRATEGY RANKINGS (by Return)")
    print("-" * 70)
    print(f"{'Rank':<5} {'Strategy':<20} {'Return':>10} {'Sharpe':>8} {'Trades':>8}")
    print("-" * 70)

    # Sortieren nach Return
    sorted_strategies = sorted(
        result.strategy_results.items(), key=lambda x: x[1].stats["total_return"], reverse=True
    )

    for rank, (name, strat_result) in enumerate(sorted_strategies, 1):
        ret = strat_result.stats["total_return"]
        sharpe = strat_result.stats["sharpe"]
        trades = strat_result.stats["total_trades"]

        print(f"{rank:<5} {name:<20} {ret:>9.2%} {sharpe:>8.2f} {trades:>8}")

    # Strategie-Typen
    print("\n🎯 STRATEGY TYPES")
    print("-" * 70)
    print("Trend-Following:")
    print("  - MA Crossover")
    print("  - Momentum")
    print("  - MACD")
    print("\nMean-Reversion:")
    print("  - RSI")
    print("  - Bollinger Bands")
    print("\nCycle-Based:")
    print("  - ECM")

    # Live-Trading-Validierung
    print("\n🔒 LIVE-TRADING-VALIDIERUNG")
    print("-" * 70)

    passed, warnings = validate_for_live_trading(result.stats)

    if passed:
        print("✅ PORTFOLIO FREIGEGEBEN für Live-Trading!")
    else:
        print("❌ PORTFOLIO NICHT FREIGEGEBEN:")
        for w in warnings:
            print(f"  - {w}")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main-Funktion."""

    print("\n🚀 Peak_Trade FULL Portfolio Backtest")
    print("=" * 70)
    print("Testing ALL 6 Strategies in one Portfolio")

    # Verfügbare Strategien anzeigen
    print("\n📋 Verfügbare Strategien:")
    for i, name in enumerate(list_strategies(), 1):
        print(f"  {i}. {name}")

    # Config
    cfg = get_config()
    print(f"\n⚙️  Portfolio-Config:")
    print(f"  - Total Capital: ${cfg.backtest.initial_cash:,.2f}")

    # Portfolio-Manager
    pm = PortfolioManager()
    pm.total_capital = cfg.backtest.initial_cash

    # Alle Strategien hinzufügen
    print(f"\n📥 Lade Strategien...")

    add_configured_strategies(pm)
    for name in DEMO_PORTFOLIO_STRATEGY_NAMES:
        print(f"  ✅ {name}")

    # Daten erstellen
    print("\n📊 Erstelle reichhaltige Testdaten...")
    df = create_rich_dummy_data(n_bars=1000)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")
    print(f"  - Preisspanne: ${df['close'].min():,.0f} - ${df['close'].max():,.0f}")

    # Portfolio-Backtest
    print("\n⚙️  Führe Portfolio-Backtest durch...")
    print("  (Dies kann einige Sekunden dauern...)")

    result = pm.run_backtest(df=df, allocation_method="equal")

    # Report
    print_extended_report(result)

    # Diversifikation
    print("📈 DIVERSIFIKATIONS-ANALYSE")
    print("-" * 70)

    equity_curves = pd.DataFrame(
        {name: res.equity_curve.pct_change() for name, res in result.strategy_results.items()}
    )

    corr = equity_curves.corr()

    print("\nKorrelations-Matrix (Top 3 Paare):")
    # Oberes Dreieck extrahieren
    upper_tri = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

    # Top 3 Korrelationen
    corr_pairs = upper_tri.stack().sort_values(ascending=False).head(3)

    for (strat1, strat2), corr_val in corr_pairs.items():
        print(f"  {strat1:20s} <-> {strat2:20s}: {corr_val:>6.2f}")

    avg_corr = corr.values[np.triu_indices_from(corr.values, k=1)].mean()
    print(f"\nØ Korrelation: {avg_corr:.2f}")

    if avg_corr < 0.3:
        print("✅ Exzellente Diversifikation!")
    elif avg_corr < 0.5:
        print("✅ Gute Diversifikation")
    else:
        print("⚠️  Moderate Diversifikation")


if __name__ == "__main__":
    main()
