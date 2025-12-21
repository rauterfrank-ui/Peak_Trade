#!/usr/bin/env python3
"""
Peak_Trade Momentum Backtest Runner
=====================================
Führt Realistic Backtest mit Momentum-Strategie durch.

Usage:
    python scripts/run_momentum_realistic.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core import get_config, get_strategy_cfg
from src.strategies.momentum import generate_signals, get_strategy_description
from src.backtest.engine import BacktestEngine
from src.backtest.stats import validate_for_live_trading


def create_dummy_data(n_bars: int = 300) -> pd.DataFrame:
    """
    Erstellt Dummy-OHLCV-Daten mit Momentum-Verhalten.
    """
    np.random.seed(42)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Preis-Simulation mit Momentum-Phasen
    base_price = 50000

    # Trend + Cycle für Momentum
    trend = np.linspace(0, 5000, n_bars)
    cycle = np.sin(np.linspace(0, 6 * np.pi, n_bars)) * 3000

    # Random Walk mit Momentum-Bursts
    noise = np.random.randn(n_bars).cumsum() * 150

    # Momentum-Bursts einfügen (simuliert starke Trends)
    momentum_bursts = np.zeros(n_bars)
    for i in range(5):  # 5 Momentum-Phasen
        start_idx = np.random.randint(50, n_bars - 50)
        burst_length = np.random.randint(20, 40)
        momentum_bursts[start_idx : start_idx + burst_length] = np.linspace(0, 2000, burst_length)

    close_prices = base_price + trend + cycle + noise + momentum_bursts

    # OHLC generieren
    df = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.randn(n_bars) * 0.002),
            "high": close_prices * (1 + abs(np.random.randn(n_bars)) * 0.003),
            "low": close_prices * (1 - abs(np.random.randn(n_bars)) * 0.003),
            "close": close_prices,
            "volume": np.random.randint(10, 100, n_bars),
        },
        index=dates,
    )

    return df


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
        print("""
[strategy.momentum_1h]
lookback_period = 20
entry_threshold = 0.02
exit_threshold = -0.01
stop_pct = 0.025
        """)
        return

    # Strategie-Beschreibung anzeigen
    print(get_strategy_description(strategy_params))

    # Daten erstellen (später: von Kraken holen)
    print("\n📥 Lade Daten...")
    df = create_dummy_data(n_bars=300)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")

    # Backtest durchführen
    print("\n⚙️  Führe Realistic Backtest durch...")
    engine = BacktestEngine()
    result = engine.run_realistic(
        df=df, strategy_signal_fn=generate_signals, strategy_params=strategy_params
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
