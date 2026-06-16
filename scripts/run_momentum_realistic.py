#!/usr/bin/env python3
"""
Peak_Trade Momentum Backtest Runner
=====================================
Führt Realistic Backtest mit Momentum-Strategie durch.

Usage:
    python scripts/run_momentum_realistic.py
"""

import importlib
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_backtest import load_ohlcv_data
from src.core import get_config, get_strategy_cfg
from src.strategies import load_strategy

MOMENTUM_STRATEGY_KEY = "momentum_1h"
from src.backtest.engine import BacktestEngine
from src.backtest.stats import validate_for_live_trading


def _strategy_module(strategy_key: str):
    generate_signals = load_strategy(strategy_key)
    return importlib.import_module(generate_signals.__module__)


def print_report(result):
    """Druckt Performance-Report."""

    print("\n" + "=" * 70)
    print("BACKTEST PERFORMANCE REPORT - MOMENTUM STRATEGY")
    print("=" * 70)

    # Equity-Metriken
    print("\n📊 EQUITY METRIKEN")
    print("-" * 70)
    start_equity = result.equity_curve.iloc[0]
    end_equity = result.equity_curve.iloc[-1]
    print(f"Start Equity:      ${start_equity:,.2f}")
    print(f"End Equity:        ${end_equity:,.2f}")
    print(f"Total Return:      {result.stats['total_return']:>7.2%}")
    print(f"Max Drawdown:      {result.stats['max_drawdown']:>7.2%}")

    # Risk-Adjusted
    print("\n📈 RISK-ADJUSTED METRIKEN")
    print("-" * 70)
    print(f"Sharpe Ratio:      {result.stats['sharpe']:>7.2f}")

    # Trade-Stats
    print("\n🎯 TRADE STATISTIKEN")
    print("-" * 70)
    print(f"Total Trades:      {result.stats['total_trades']:>7}")
    print(f"Win Rate:          {result.stats['win_rate']:>7.2%}")
    print(f"Profit Factor:     {result.stats['profit_factor']:>7.2f}")

    # Live-Trading-Validierung
    print("\n🔒 LIVE-TRADING-VALIDIERUNG")
    print("-" * 70)

    passed, warnings = validate_for_live_trading(result.stats)

    if passed:
        print("✅ STRATEGIE FREIGEGEBEN für Live-Trading!")
    else:
        print("❌ STRATEGIE NICHT FREIGEGEBEN:")
        for w in warnings:
            print(f"  - {w}")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main-Funktion."""

    print("\n🚀 Peak_Trade Momentum Backtest")
    print("=" * 70)

    # Config laden
    cfg = get_config()
    print(f"\n⚙️  Config geladen:")
    print(f"  - Initial Cash: ${cfg.backtest.initial_cash:,.2f}")
    print(f"  - Risk per Trade: {cfg.risk.risk_per_trade:.1%}")
    print(f"  - Max Position Size: {cfg.risk.max_position_size:.0%}")

    # Strategie-Parameter laden
    try:
        strategy_params = get_strategy_cfg("momentum_1h")
    except KeyError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nBitte füge folgende Konfiguration zu config.toml hinzu:")
        print(
            """
[strategy.momentum_1h]
lookback_period = 20
entry_threshold = 0.02
exit_threshold = -0.01
stop_pct = 0.025
        """
        )
        return

    # Strategie-Beschreibung anzeigen
    print(_strategy_module(MOMENTUM_STRATEGY_KEY).get_strategy_description(strategy_params))

    # Daten erstellen (später: von Kraken holen)
    print("\n📥 Lade Daten...")
    df = load_ohlcv_data(None, None, None, n_bars=300)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")

    # Backtest durchführen
    print("\n⚙️  Führe Realistic Backtest durch...")
    engine = BacktestEngine()
    strategy_signal_fn = load_strategy(MOMENTUM_STRATEGY_KEY)
    result = engine.run_realistic(
        df=df, strategy_signal_fn=strategy_signal_fn, strategy_params=strategy_params
    )

    # Report drucken
    print_report(result)

    # Sample Trades anzeigen
    if result.trades:
        print("📋 Sample Trades (erste 5):")
        print("-" * 70)
        for i, trade in enumerate(result.trades[:5], 1):
            print(
                f"{i}. Entry: {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:,.2f}"
            )
            print(
                f"   Exit:  {trade.exit_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.exit_price:,.2f}"
            )
            print(f"   PnL:   ${trade.pnl:,.2f} ({trade.exit_reason})")
            print()


if __name__ == "__main__":
    main()
