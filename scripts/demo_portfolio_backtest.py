#!/usr/bin/env python3
"""
Demo: Portfolio Strategy Backtest (Phase 26)
============================================

Demonstriert den Portfolio-Strategy-Layer mit verschiedenen
Gewichtungsstrategien (Equal-Weight, Fixed-Weights, Vol-Target).

Usage:
    python scripts/demo_portfolio_backtest.py
    python scripts/demo_portfolio_backtest.py --strategy vol_target
    python scripts/demo_portfolio_backtest.py --strategy fixed_weights

WICHTIG: Nur für Research/Backtest/Shadow, NICHT für Live-Trading!
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.portfolio import (
    PortfolioConfig,
    make_portfolio_strategy,
)
from src.backtest.engine import run_portfolio_strategy_backtest
from src.strategies.ma_crossover import generate_signals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_synthetic_data(
    symbol: str,
    n_bars: int = 500,
    start_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0001,
    seed: int = None,
) -> pd.DataFrame:
    """
    Erstellt synthetische OHLCV-Daten für Tests.

    Args:
        symbol: Symbol-Name (für Seed-Berechnung)
        n_bars: Anzahl Bars
        start_price: Startpreis
        volatility: Tägliche Volatilität
        trend: Trend pro Bar
        seed: Random Seed (optional)

    Returns:
        DataFrame mit OHLCV-Daten
    """
    if seed is None:
        seed = hash(symbol) % 10000

    np.random.seed(seed)

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")
    returns = np.random.normal(trend, volatility, n_bars)
    prices = start_price * np.cumprod(1 + returns)

    df = pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.005, 0.005, n_bars)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, n_bars))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_bars))),
            "close": prices,
            "volume": np.random.uniform(1000, 10000, n_bars),
        },
        index=dates,
    )

    return df


def main():
    """Haupt-Demo-Funktion."""
    parser = argparse.ArgumentParser(description="Demo: Portfolio Strategy Backtest (Phase 26)")
    parser.add_argument(
        "--strategy",
        type=str,
        default="equal_weight",
        choices=["equal_weight", "fixed_weights", "vol_target"],
        help="Portfolio-Strategie (default: equal_weight)",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=10000.0,
        help="Startkapital (default: 10000)",
    )
    parser.add_argument(
        "--fee-bps",
        type=float,
        default=10.0,
        help="Gebühren in Basispunkten (default: 10)",
    )
    parser.add_argument(
        "--rebalance-interval",
        type=int,
        default=24,
        help="Rebalancing-Intervall in Bars (default: 24 = täglich)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("🎯 Peak_Trade - Portfolio Strategy Backtest Demo (Phase 26)")
    print("=" * 70)
    print()
    print(f"  Portfolio-Strategie:  {args.strategy}")
    print(f"  Startkapital:         ${args.initial_capital:,.2f}")
    print(f"  Gebühren:             {args.fee_bps} bps")
    print(f"  Rebalancing:          alle {args.rebalance_interval} Bars")
    print()
    print("⚠️  WICHTIG: Nur für Research/Backtest/Shadow!")
    print("=" * 70)
    print()

    # 1. Synthetische Daten erstellen
    logger.info("Erstelle synthetische Daten für 3 Symbole...")

    symbols = ["BTC/EUR", "ETH/EUR", "LTC/EUR"]
    volatilities = {"BTC/EUR": 0.025, "ETH/EUR": 0.03, "LTC/EUR": 0.035}
    start_prices = {"BTC/EUR": 50000.0, "ETH/EUR": 3000.0, "LTC/EUR": 100.0}

    data_dict = {}
    for symbol in symbols:
        df = create_synthetic_data(
            symbol=symbol,
            n_bars=500,
            start_price=start_prices[symbol],
            volatility=volatilities[symbol],
        )
        data_dict[symbol] = df
        logger.info(f"  {symbol}: {len(df)} Bars, Start=${start_prices[symbol]:,.2f}")

    # 2. Portfolio-Config erstellen
    if args.strategy == "equal_weight":
        portfolio_config = PortfolioConfig(
            enabled=True,
            name="equal_weight",
            max_single_weight=0.5,
        )
    elif args.strategy == "fixed_weights":
        portfolio_config = PortfolioConfig(
            enabled=True,
            name="fixed_weights",
            fixed_weights={
                "BTC/EUR": 0.50,
                "ETH/EUR": 0.30,
                "LTC/EUR": 0.20,
            },
        )
    else:  # vol_target
        portfolio_config = PortfolioConfig(
            enabled=True,
            name="vol_target",
            vol_lookback=20,
            vol_target=0.15,
        )

    logger.info(f"Portfolio-Strategie: {portfolio_config.name}")

    # 3. Strategie-Parameter (MA Crossover)
    strategy_params = {
        "fast_window": 20,
        "slow_window": 50,
    }

    # 4. Backtest ausführen
    logger.info("Starte Portfolio-Backtest...")
    print()

    result = run_portfolio_strategy_backtest(
        data_dict=data_dict,
        strategy_signal_fn=generate_signals,
        strategy_params=strategy_params,
        portfolio_config=portfolio_config,
        initial_capital=args.initial_capital,
        fee_bps=args.fee_bps,
        rebalance_interval=args.rebalance_interval,
    )

    # 5. Ergebnisse ausgeben
    print()
    print("=" * 70)
    print("📊 BACKTEST-ERGEBNISSE")
    print("=" * 70)
    print()

    stats = result.portfolio_stats
    print(f"  Portfolio-Strategie:    {result.portfolio_strategy_name}")
    print(f"  Symbole:                {', '.join(result.metadata['symbols'])}")
    print()
    print("  Performance:")
    print(f"    Total Return:         {stats['total_return']:>10.2%}")
    print(f"    CAGR:                 {stats.get('cagr', 0):>10.2%}")
    print(f"    Sharpe Ratio:         {stats['sharpe']:>10.2f}")
    print(f"    Max Drawdown:         {stats.get('max_drawdown', 0):>10.2%}")
    print()
    print("  Trading:")
    print(f"    Total Trades:         {stats['total_trades']:>10}")
    print(f"    Win Rate:             {stats['win_rate']:>10.1%}")
    print(f"    Rebalance Interval:   {stats['rebalance_interval']:>10} Bars")
    print()

    # 6. Gewichte-Statistik
    print("  Durchschnittliche Gewichte:")
    avg_weights = result.target_weights_history.mean()
    for symbol, weight in avg_weights.items():
        print(f"    {symbol}:".ljust(20) + f"{weight:>10.1%}")
    print()

    # 7. Symbol-Performance
    print("  Performance pro Symbol:")
    for symbol, equity in result.symbol_equities.items():
        if len(equity) > 1:
            symbol_return = (
                (equity.iloc[-1] - equity.iloc[1]) / equity.iloc[1] if equity.iloc[1] > 0 else 0
            )
            trades = len(result.trades_per_symbol.get(symbol, []))
            print(f"    {symbol}:".ljust(20) + f"Return: {symbol_return:>8.2%}, Trades: {trades}")
    print()

    # 8. Final Summary
    final_equity = result.combined_equity.iloc[-1]
    print("=" * 70)
    print(f"  Final Equity: ${final_equity:,.2f}")
    print(f"  PnL:          ${final_equity - args.initial_capital:+,.2f}")
    print("=" * 70)
    print()
    print("✅ Demo abgeschlossen!")

    return result


if __name__ == "__main__":
    main()
