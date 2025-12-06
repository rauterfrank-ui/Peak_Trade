#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/demo_order_pipeline_backtest.py
"""
Peak_Trade: Demo-Script fuer Order-Pipeline-Backtest
====================================================

Demonstriert die Integration des Order-Layers (Phase 16) in die Backtest-Engine.

Features:
- Backtest mit ExecutionPipeline
- Signal → OrderRequest → OrderFill Flow
- PnL-Berechnung aus Fills
- Fees und Slippage Simulation

WICHTIG: Es werden KEINE echten Orders an Boersen gesendet.
         Alles ist Paper-/Sandbox-Simulation.

Usage:
    python scripts/demo_order_pipeline_backtest.py
    python scripts/demo_order_pipeline_backtest.py --strategy ma_crossover --symbol BTC/EUR
    python scripts/demo_order_pipeline_backtest.py --fee-bps 10 --slippage-bps 5
    python scripts/demo_order_pipeline_backtest.py --bars 500 --tag order-layer-demo
"""
from __future__ import annotations

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Pfad-Setup
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import numpy as np

from src.backtest.engine import BacktestEngine
from src.strategies import load_strategy


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Demo-Script fuer Order-Pipeline-Backtest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/demo_order_pipeline_backtest.py
  python scripts/demo_order_pipeline_backtest.py --strategy ma_crossover --symbol BTC/EUR
  python scripts/demo_order_pipeline_backtest.py --fee-bps 10 --slippage-bps 5
  python scripts/demo_order_pipeline_backtest.py --bars 500 --tag order-layer-demo
        """,
    )

    parser.add_argument(
        "--strategy",
        default="ma_crossover",
        help="Strategie-Key (default: ma_crossover)",
    )
    parser.add_argument(
        "--symbol",
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        help="Timeframe (default: 1h)",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Anzahl Bars fuer Backtest (default: 200)",
    )
    parser.add_argument(
        "--fee-bps",
        type=float,
        default=10.0,
        help="Fees in Basispunkten (default: 10.0 = 0.1%%)",
    )
    parser.add_argument(
        "--slippage-bps",
        type=float,
        default=5.0,
        help="Slippage in Basispunkten (default: 5.0 = 0.05%%)",
    )
    parser.add_argument(
        "--tag",
        help="Optionaler Tag fuer Registry-Logging",
    )
    parser.add_argument(
        "--compare-legacy",
        action="store_true",
        help="Vergleiche mit Legacy-Backtest (run_realistic)",
    )

    return parser.parse_args(argv)


def generate_sample_data(
    symbol: str,
    bars: int,
    timeframe: str = "1h",
) -> pd.DataFrame:
    """
    Generiert Sample-OHLCV-Daten fuer den Backtest.

    Args:
        symbol: Trading-Symbol
        bars: Anzahl Bars
        timeframe: Timeframe

    Returns:
        pd.DataFrame mit OHLCV-Daten
    """
    # Basis-Preis je nach Symbol
    if "BTC" in symbol:
        base_price = 50000.0
        volatility = 0.02
    elif "ETH" in symbol:
        base_price = 3000.0
        volatility = 0.025
    elif "LTC" in symbol:
        base_price = 100.0
        volatility = 0.03
    else:
        base_price = 1000.0
        volatility = 0.02

    # Seed fuer Reproduzierbarkeit
    np.random.seed(42)

    # Zeitindex erstellen
    if timeframe == "1h":
        freq = "h"
    elif timeframe == "4h":
        freq = "4h"
    elif timeframe == "1d":
        freq = "D"
    else:
        freq = "h"

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=bars)
    index = pd.date_range(start=start_time, periods=bars, freq=freq)

    # Random Walk fuer Close-Preise
    returns = np.random.normal(0.0001, volatility, bars)
    close = base_price * np.cumprod(1 + returns)

    # OHLCV generieren
    data = {
        "open": close * (1 + np.random.uniform(-0.001, 0.001, bars)),
        "high": close * (1 + np.abs(np.random.normal(0, 0.005, bars))),
        "low": close * (1 - np.abs(np.random.normal(0, 0.005, bars))),
        "close": close,
        "volume": np.random.uniform(100, 10000, bars),
    }

    df = pd.DataFrame(data, index=index)

    # Sicherstellen dass high >= max(open, close) und low <= min(open, close)
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)

    return df


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    print("\n" + "=" * 70)
    print("Peak_Trade: Order-Pipeline-Backtest Demo")
    print("=" * 70)
    print("\n⚠️  WICHTIG: Es werden KEINE echten Orders gesendet (Paper/Sandbox)")

    # 1. Sample-Daten generieren
    print(f"\n📊 Generiere Sample-Daten...")
    print(f"   Symbol: {args.symbol}")
    print(f"   Timeframe: {args.timeframe}")
    print(f"   Bars: {args.bars}")

    df = generate_sample_data(
        symbol=args.symbol,
        bars=args.bars,
        timeframe=args.timeframe,
    )

    print(f"   Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"   Preis-Range: {df['close'].min():.2f} - {df['close'].max():.2f}")

    # 2. Strategie laden
    print(f"\n🎯 Lade Strategie: {args.strategy}")
    try:
        strategy_fn = load_strategy(args.strategy)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Strategie: {e}")
        print("   Verfuegbare Strategien: ma_crossover, rsi_reversion, macd, momentum, bollinger")
        return

    # Strategie-Parameter (Standard-Werte)
    strategy_params = {
        "fast_period": 10,
        "slow_period": 30,
        "stop_pct": 0.02,
    }
    print(f"   Parameter: {strategy_params}")

    # 3. Backtest mit Order-Layer ausfuehren
    print(f"\n🔧 Starte Order-Layer-Backtest...")
    print(f"   Fees: {args.fee_bps} bps ({args.fee_bps / 100:.2f}%)")
    print(f"   Slippage: {args.slippage_bps} bps ({args.slippage_bps / 100:.2f}%)")

    engine = BacktestEngine(use_order_layer=True)

    result = engine.run_with_order_layer(
        df=df,
        strategy_signal_fn=strategy_fn,
        strategy_params=strategy_params,
        symbol=args.symbol,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
    )

    # 4. Ergebnisse anzeigen
    print("\n" + "=" * 70)
    print("📈 BACKTEST-ERGEBNISSE (Order-Layer)")
    print("=" * 70)

    print(f"\n💰 Performance:")
    print(f"   Total Return:    {result.stats['total_return']:.2%}")
    print(f"   CAGR:            {result.stats.get('cagr', 0):.2%}")
    print(f"   Max Drawdown:    {result.stats['max_drawdown']:.2%}")
    print(f"   Sharpe Ratio:    {result.stats['sharpe']:.2f}")

    print(f"\n📊 Trade-Statistiken:")
    print(f"   Total Trades:    {result.stats['total_trades']}")
    print(f"   Win Rate:        {result.stats['win_rate']:.1%}")
    print(f"   Profit Factor:   {result.stats['profit_factor']:.2f}")

    print(f"\n📝 Order-Layer Details:")
    print(f"   Total Orders:    {result.stats['total_orders']}")
    print(f"   Filled Orders:   {result.stats['filled_orders']}")
    print(f"   Rejected Orders: {result.stats['rejected_orders']}")
    print(f"   Total Fees:      {result.stats['total_fees']:.2f} EUR")

    # 5. Beispiel-Trades anzeigen
    if result.trades is not None and not result.trades.empty:
        print(f"\n📋 Erste 3 Trades:")
        print("-" * 70)
        for i, trade in result.trades.head(3).iterrows():
            side = trade.get("side", "?")
            entry = trade.get("entry_price", 0)
            exit_p = trade.get("exit_price", 0)
            pnl = trade.get("pnl", 0)
            print(
                f"   {i+1}. {side.upper():5s} | "
                f"Entry: {entry:10.2f} | Exit: {exit_p:10.2f} | "
                f"PnL: {pnl:+10.2f} EUR"
            )

    # 6. Optional: Vergleich mit Legacy-Backtest
    if args.compare_legacy:
        print("\n" + "=" * 70)
        print("🔄 VERGLEICH MIT LEGACY-BACKTEST (run_realistic)")
        print("=" * 70)

        legacy_engine = BacktestEngine(use_order_layer=False)
        legacy_result = legacy_engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_fn,
            strategy_params=strategy_params,
        )

        print(f"\n                    Order-Layer     Legacy")
        print(f"   Total Return:    {result.stats['total_return']:+8.2%}     {legacy_result.stats['total_return']:+8.2%}")
        print(f"   Sharpe Ratio:    {result.stats['sharpe']:+8.2f}     {legacy_result.stats['sharpe']:+8.2f}")
        print(f"   Total Trades:    {result.stats['total_trades']:8d}     {legacy_result.stats['total_trades']:8d}")

    # 7. Execution-Results anzeigen
    if engine.execution_results:
        print(f"\n📦 Execution-Results (erste 5 Orders):")
        print("-" * 70)
        for i, exec_result in enumerate(engine.execution_results[:5]):
            status = exec_result.status
            symbol = exec_result.request.symbol
            side = exec_result.request.side
            qty = exec_result.request.quantity
            if exec_result.fill:
                price = exec_result.fill.price
                print(f"   {i+1}. [{status.upper():8s}] {side.upper():4s} {symbol} qty={qty:.6f} @ {price:.2f}")
            else:
                print(f"   {i+1}. [{status.upper():8s}] {side.upper():4s} {symbol} qty={qty:.6f} (rejected)")

    print("\n" + "=" * 70)
    print("✅ Order-Pipeline-Backtest Demo abgeschlossen!")
    print("=" * 70)

    if args.tag:
        print(f"\n📝 Tag: {args.tag}")
        # TODO: Registry-Logging implementieren
        # log_backtest_run(..., tag=args.tag)

    print()


if __name__ == "__main__":
    main()
