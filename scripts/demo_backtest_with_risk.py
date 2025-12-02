#!/usr/bin/env python3
"""
Peak_Trade Backtest mit Risk-Layer Demo
========================================
Demonstriert BacktestEngine mit vollständiger Risk-Integration.

Usage:
    python scripts/demo_backtest_with_risk.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core import get_config
from src.backtest.engine import BacktestEngine
from src.risk import PositionSizer, PositionSizerConfig, RiskLimits, RiskLimitsConfig
from src.strategies.ma_crossover import generate_signals


def create_test_data(n_bars: int = 200) -> pd.DataFrame:
    """Erstellt Test-OHLCV-Daten."""
    np.random.seed(42)

    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h", tz="UTC")

    # Preis-Simulation mit Trend und Oszillation
    base_price = 50000
    trend = np.linspace(0, 3000, n_bars)
    cycle = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 2000
    noise = np.random.randn(n_bars).cumsum() * 200

    close_prices = base_price + trend + cycle + noise

    df = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.randn(n_bars) * 0.002),
            "high": close_prices * (1 + abs(np.random.randn(n_bars)) * 0.003),
            "low": close_prices * (1 - abs(np.random.randn(n_bars)) * 0.003),
            "close": close_prices,
            "volume": np.random.randint(10, 100, n_bars).astype(float),
        },
        index=dates,
    )

    return df


def demo_default_risk():
    """Demo: Backtest mit Default Risk-Config."""
    print("\n" + "=" * 70)
    print("DEMO 1: Backtest mit Default Risk-Config")
    print("=" * 70)

    # Daten erstellen
    df = create_test_data(200)
    print(f"\nDaten: {len(df)} Bars von {df.index[0]} bis {df.index[-1]}")

    # Strategie-Parameter
    strategy_params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}

    # Engine mit Default-Config
    engine = BacktestEngine()

    print("\nRisk-Config (Default):")
    print(f"  Max Drawdown: {engine.risk_limits.config.max_drawdown_pct}%")
    print(f"  Max Position: {engine.risk_limits.config.max_position_pct}%")
    print(f"  Daily Loss Limit: {engine.risk_limits.config.daily_loss_limit_pct}%")

    # Backtest durchführen
    print("\n⚙️  Führe Backtest durch...")
    result = engine.run_realistic(df, generate_signals, strategy_params)

    # Ergebnisse
    print("\n📊 Ergebnisse:")
    print(f"  Total Return:     {result.stats['total_return']:+.2%}")
    print(f"  Max Drawdown:     {result.stats['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio:     {result.stats['sharpe']:.2f}")
    print(f"  Total Trades:     {result.stats['total_trades']}")
    print(f"  Blocked Trades:   {result.blocked_trades}")
    print(f"  Win Rate:         {result.stats['win_rate']:.1%}")
    print(f"  Profit Factor:    {result.stats['profit_factor']:.2f}")


def demo_strict_risk():
    """Demo: Backtest mit strengen Risk-Limits."""
    print("\n" + "=" * 70)
    print("DEMO 2: Backtest mit STRENGEN Risk-Limits")
    print("=" * 70)

    # Daten erstellen
    df = create_test_data(200)

    # Strategie-Parameter
    strategy_params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}

    # Strenge Risk-Config
    risk_config = RiskLimitsConfig(
        max_drawdown_pct=10.0,  # Nur 10% DD erlaubt
        max_position_pct=5.0,  # Nur 5% Position erlaubt
        daily_loss_limit_pct=2.0,  # Nur 2% Daily Loss erlaubt
    )

    risk_limits = RiskLimits(risk_config)
    engine = BacktestEngine(risk_limits=risk_limits)

    print("\nRisk-Config (STRENG):")
    print(f"  Max Drawdown: {risk_config.max_drawdown_pct}%")
    print(f"  Max Position: {risk_config.max_position_pct}%")
    print(f"  Daily Loss Limit: {risk_config.daily_loss_limit_pct}%")

    # Backtest durchführen
    print("\n⚙️  Führe Backtest durch...")
    result = engine.run_realistic(df, generate_signals, strategy_params)

    # Ergebnisse
    print("\n📊 Ergebnisse:")
    print(f"  Total Return:     {result.stats['total_return']:+.2%}")
    print(f"  Max Drawdown:     {result.stats['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio:     {result.stats['sharpe']:.2f}")
    print(f"  Total Trades:     {result.stats['total_trades']}")
    print(f"  Blocked Trades:   {result.blocked_trades} ⚠️")
    print(f"  Win Rate:         {result.stats['win_rate']:.1%}")
    print(f"  Profit Factor:    {result.stats['profit_factor']:.2f}")

    print(f"\n⚠️  Mit strengen Limits wurden {result.blocked_trades} Trades blockiert!")


def demo_aggressive_risk():
    """Demo: Backtest mit aggressiven Risk-Limits."""
    print("\n" + "=" * 70)
    print("DEMO 3: Backtest mit AGGRESSIVEN Risk-Limits")
    print("=" * 70)

    # Daten erstellen
    df = create_test_data(200)

    # Strategie-Parameter
    strategy_params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}

    # Aggressive Risk-Config
    position_config = PositionSizerConfig(
        method="fixed_fractional", risk_pct=2.0, max_position_pct=50.0  # 2% Risk  # 50% Position erlaubt
    )

    risk_config = RiskLimitsConfig(
        max_drawdown_pct=30.0, max_position_pct=50.0, daily_loss_limit_pct=10.0
    )

    position_sizer = PositionSizer(position_config)
    risk_limits = RiskLimits(risk_config)
    engine = BacktestEngine(position_sizer=position_sizer, risk_limits=risk_limits)

    print("\nRisk-Config (AGGRESSIV):")
    print(f"  Risk per Trade: {position_config.risk_pct}%")
    print(f"  Max Position: {position_config.max_position_pct}%")
    print(f"  Max Drawdown: {risk_config.max_drawdown_pct}%")
    print(f"  Daily Loss Limit: {risk_config.daily_loss_limit_pct}%")

    # Backtest durchführen
    print("\n⚙️  Führe Backtest durch...")
    result = engine.run_realistic(df, generate_signals, strategy_params)

    # Ergebnisse
    print("\n📊 Ergebnisse:")
    print(f"  Total Return:     {result.stats['total_return']:+.2%}")
    print(f"  Max Drawdown:     {result.stats['max_drawdown']:.2%}")
    print(f"  Sharpe Ratio:     {result.stats['sharpe']:.2f}")
    print(f"  Total Trades:     {result.stats['total_trades']}")
    print(f"  Blocked Trades:   {result.blocked_trades}")
    print(f"  Win Rate:         {result.stats['win_rate']:.1%}")
    print(f"  Profit Factor:    {result.stats['profit_factor']:.2f}")


def demo_trade_details():
    """Demo: Trade-Details anzeigen."""
    print("\n" + "=" * 70)
    print("DEMO 4: Trade-Details")
    print("=" * 70)

    # Daten erstellen
    df = create_test_data(200)

    # Strategie-Parameter
    strategy_params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}

    # Engine
    engine = BacktestEngine()

    # Backtest durchführen
    result = engine.run_realistic(df, generate_signals, strategy_params)

    # Erste 5 Trades anzeigen
    print(f"\n📋 Erste 5 von {len(result.trades)} Trades:\n")

    for i, trade in enumerate(result.trades[:5], 1):
        print(f"Trade {i}:")
        print(f"  Entry:  {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:,.2f}")
        print(f"  Exit:   {trade.exit_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.exit_price:,.2f}")
        print(f"  Size:   {trade.size:.4f} BTC")
        print(f"  Stop:   ${trade.stop_price:,.2f}")
        print(f"  P&L:    ${trade.pnl:+,.2f} ({trade.pnl_pct:+.2f}%)")
        print(f"  Reason: {trade.exit_reason}")
        print()


def main():
    """Hauptfunktion."""
    print("\n" + "=" * 70)
    print("PEAK_TRADE BACKTEST MIT RISK-LAYER DEMO")
    print("=" * 70)
    print("\nZeigt BacktestEngine mit verschiedenen Risk-Configs:")

    try:
        demo_default_risk()
        demo_strict_risk()
        demo_aggressive_risk()
        demo_trade_details()

        print("\n" + "=" * 70)
        print("✅ ALLE DEMOS ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 70)

        print("\n📝 Integration erfolgreich:")
        print("  ✅ Position Sizing aktiv")
        print("  ✅ Risk Limits (Drawdown, Daily Loss, Position Size)")
        print("  ✅ Stop-Loss-Management")
        print("  ✅ Trade-Tracking mit PnL")

        print("\n🚀 Nächste Schritte:")
        print("  1. Mit echten Kraken-Daten testen")
        print("  2. Parameter-Optimierung")
        print("  3. Multi-Strategy-Backtests")

    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
