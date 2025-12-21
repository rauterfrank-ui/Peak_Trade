#!/usr/bin/env python3
"""
Peak_Trade – Registry-Backtest Demo
====================================
Zeigt die neuen Registry-basierten Backtest-Entry-Points.

Features:
- Single-Strategy-Backtest aus Registry
- Multi-Strategy-Portfolio-Backtest
- Regime-basiertes Filtering

Run:
    cd ~/Peak_Trade
    python scripts/demo_registry_backtest.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtest.engine import (
    run_single_strategy_from_registry,
    run_portfolio_from_config,
)


def generate_fake_ohlcv(
    start: datetime,
    periods: int = 1000,
    freq: str = "1h",
    base_price: float = 50000.0,
    volatility: float = 0.02,
) -> pd.DataFrame:
    """
    Erzeugt künstliche OHLCV-Daten für Demo.

    Args:
        start: Start-Timestamp
        periods: Anzahl Bars
        freq: Timeframe (z.B. "1h", "1d")
        base_price: Basis-Preis
        volatility: Volatilität (Standardabweichung der Returns)

    Returns:
        OHLCV-DataFrame mit DatetimeIndex
    """
    # Zeitindex
    index = pd.date_range(start=start, periods=periods, freq=freq)

    # Random Walk für Close
    returns = np.random.normal(0, volatility, periods)
    close_prices = base_price * np.exp(np.cumsum(returns))

    # Konsistente OHLC
    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)

    # High = max(open, close) + random bump
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + np.random.uniform(0, 0.005, periods))

    # Low = min(open, close) - random dip
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - np.random.uniform(0, 0.005, periods))

    # Volume
    df["volume"] = np.random.uniform(100, 1000, periods)

    return df[["open", "high", "low", "close", "volume"]]


def print_section(title: str):
    """Formatierte Section-Header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_result_summary(result, strategy_name: str = None):
    """Gibt kompakte Backtest-Zusammenfassung aus."""
    name = strategy_name or result.strategy_name or "Unknown"

    print(f"📊 {name}")
    print(f"   Return: {result.stats['total_return']:.2%}")
    print(f"   Sharpe: {result.stats['sharpe']:.2f}")
    print(f"   Max DD: {result.stats['max_drawdown']:.2%}")
    print(f"   Trades: {result.stats['total_trades']}")
    print(f"   Win Rate: {result.stats['win_rate']:.1%}")
    print(f"   Profit Factor: {result.stats['profit_factor']:.2f}")
    print(f"   Blocked Trades: {result.blocked_trades}")
    print()


def demo_single_strategy():
    """Demo: Single-Strategy aus Registry."""
    print_section("1. SINGLE-STRATEGY-BACKTEST AUS REGISTRY")

    # Fake-Daten erzeugen
    print("📈 Erzeuge künstliche OHLCV-Daten...")
    df = generate_fake_ohlcv(
        start=datetime(2023, 1, 1),
        periods=1000,
        freq="1h",
        base_price=50000.0,
        volatility=0.015,
    )
    print(f"   {len(df)} Bars, Zeitraum: {df.index[0]} bis {df.index[-1]}\n")

    # MA-Crossover Backtest
    print("🎯 Starte Backtest: MA-Crossover (aus Registry)")
    result = run_single_strategy_from_registry(
        df=df,
        strategy_name="ma_crossover",
        custom_params={
            "fast_period": 20,  # überschreibt Config
            "slow_period": 50,  # überschreibt Config
        },
    )

    print_result_summary(result)

    # Momentum Backtest
    print("🎯 Starte Backtest: Momentum (aus Registry)")
    result2 = run_single_strategy_from_registry(
        df=df,
        strategy_name="momentum_1h",
    )

    print_result_summary(result2)


def demo_portfolio_all_active():
    """Demo: Portfolio mit allen aktiven Strategien."""
    print_section("2. PORTFOLIO-BACKTEST (ALLE AKTIVEN STRATEGIEN)")

    # Fake-Daten
    print("📈 Erzeuge künstliche OHLCV-Daten...")
    df = generate_fake_ohlcv(
        start=datetime(2023, 1, 1),
        periods=2000,
        freq="1h",
        base_price=50000.0,
        volatility=0.02,
    )
    print(f"   {len(df)} Bars\n")

    # Portfolio-Backtest
    print("🎯 Starte Portfolio-Backtest (Equal Weight)")
    result = run_portfolio_from_config(df=df)

    # Portfolio-Stats
    print("📊 PORTFOLIO-ERGEBNIS")
    print(f"   Return: {result.portfolio_stats['total_return']:.2%}")
    print(f"   Sharpe: {result.portfolio_stats['sharpe']:.2f}")
    print(f"   Max DD: {result.portfolio_stats['max_drawdown']:.2%}")
    print(f"   Strategien: {result.portfolio_stats['num_strategies']}")
    print(f"   Allocation: {result.portfolio_stats['allocation_method']}")
    print()

    # Individual Strategy Stats
    print("📋 INDIVIDUAL STRATEGY RESULTS:")
    for name, strat_result in result.strategy_results.items():
        weight = result.allocation[name]
        print(f"\n   {name} (Weight: {weight:.1%})")
        print(f"      Return: {strat_result.stats['total_return']:.2%}")
        print(f"      Sharpe: {strat_result.stats['sharpe']:.2f}")
        print(f"      Trades: {strat_result.stats['total_trades']}")


def demo_portfolio_regime_filter():
    """Demo: Portfolio mit Regime-Filter."""
    print_section("3. PORTFOLIO-BACKTEST (TRENDING-STRATEGIEN)")

    # Fake-Daten
    df = generate_fake_ohlcv(
        start=datetime(2023, 1, 1),
        periods=1500,
        freq="1h",
        volatility=0.025,
    )

    # Portfolio mit Regime-Filter
    print("🎯 Starte Portfolio-Backtest (nur Trending-Strategien)")
    result = run_portfolio_from_config(
        df=df,
        regime_filter="trending",
    )

    # Stats
    print("📊 PORTFOLIO-ERGEBNIS (Trending)")
    print(f"   Return: {result.portfolio_stats['total_return']:.2%}")
    print(f"   Sharpe: {result.portfolio_stats['sharpe']:.2f}")
    print(f"   Strategien: {list(result.strategy_results.keys())}")
    print()


def demo_portfolio_custom_list():
    """Demo: Portfolio mit Custom-Strategie-Liste."""
    print_section("4. PORTFOLIO-BACKTEST (CUSTOM STRATEGIE-LISTE)")

    # Fake-Daten
    df = generate_fake_ohlcv(
        start=datetime(2023, 1, 1),
        periods=1000,
        freq="1h",
    )

    # Portfolio mit expliziter Strategie-Liste
    print("🎯 Starte Portfolio-Backtest (nur MA + Momentum)")
    result = run_portfolio_from_config(
        df=df,
        strategy_filter=["ma_crossover", "momentum_1h"],
    )

    # Stats
    print("📊 PORTFOLIO-ERGEBNIS (Custom)")
    print(f"   Return: {result.portfolio_stats['total_return']:.2%}")
    print(f"   Sharpe: {result.portfolio_stats['sharpe']:.2f}")
    print(f"   Strategien: {list(result.strategy_results.keys())}")
    print()


def main():
    """Hauptfunktion."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     Peak_Trade Registry-Backtest Demo                           ║
║     =====================================                         ║
║                                                                  ║
║     Zeigt neue Registry-basierte Entry-Points                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    try:
        # Demo 1: Single Strategy
        demo_single_strategy()

        # Demo 2: Portfolio All Active
        demo_portfolio_all_active()

        # Demo 3: Portfolio Regime-Filter
        demo_portfolio_regime_filter()

        # Demo 4: Portfolio Custom List
        demo_portfolio_custom_list()

        print_section("✅ ALLE DEMOS ERFOLGREICH")
        print("Die Registry-Backtest-Integration funktioniert! 🚀")
        print("\nNächste Schritte:")
        print("1. Nutze run_single_strategy_from_registry() für einzelne Strategien")
        print("2. Nutze run_portfolio_from_config() für Portfolio-Backtests")
        print("3. Passe config.toml an (strategies.active, portfolio.*)")
        print("4. Siehe docs/ für ausführliche Dokumentation")

    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
