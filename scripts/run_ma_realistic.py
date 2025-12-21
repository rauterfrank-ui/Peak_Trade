#!/usr/bin/env python3
"""
Peak_Trade MA Crossover Backtest Runner (OOP Version)
======================================================
Führt Realistic Backtest mit MA-Crossover-Strategie durch.
Nutzt die neue OOP-Strategy-API mit BaseStrategy.

Usage:
    python scripts/run_ma_realistic.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.strategies.ma_crossover import MACrossoverStrategy
from src.backtest.engine import BacktestEngine
from src.backtest.stats import validate_for_live_trading


def create_dummy_data(n_bars: int = 200) -> pd.DataFrame:
    """
    Erstellt Dummy-OHLCV-Daten für Tests.

    Simuliert einen Trend mit Noise und Oszillationen.
    """
    np.random.seed(42)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Preis-Simulation mit Sinuswelle für Crossovers
    base_price = 50000

    # Langfristiger Trend
    trend = np.linspace(0, 3000, n_bars)

    # Oszillation für MA-Crossovers (mehrere Zyklen)
    cycle = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 2000

    # Random Walk Noise
    noise = np.random.randn(n_bars).cumsum() * 200

    close_prices = base_price + trend + cycle + noise

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
    print("BACKTEST PERFORMANCE REPORT")
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
    print(f"Blocked Trades:    {result.stats.get('blocked_trades', 0):>7}")

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

    print("\n🚀 Peak_Trade MA Crossover Backtest (OOP Version)")
    print("=" * 70)

    # Config laden
    print("\n⚙️  Lade Konfiguration...")
    try:
        cfg = load_config("config.toml")
        print("✅ config.toml erfolgreich geladen")
    except FileNotFoundError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nBitte erstelle eine config.toml im Projekt-Root mit:")
        print("""
[general]
base_currency = "EUR"
starting_capital = 10_000.0

[backtest]
initial_cash = 10_000.0

[strategy.ma_crossover]
fast_window = 20
slow_window = 50
price_col = "close"
position_size = 0.1
        """)
        return

    # Basis-Config anzeigen
    initial_cash = cfg.get("backtest.initial_cash", 10000.0)
    risk_per_trade = cfg.get("risk.risk_per_trade", 0.01)
    max_position_size = cfg.get("risk.max_position_size", 0.25)

    print(f"  - Initial Cash: ${initial_cash:,.2f}")
    print(f"  - Risk per Trade: {risk_per_trade:.1%}")
    print(f"  - Max Position Size: {max_position_size:.0%}")

    # Strategie erstellen
    print("\n📊 Erstelle Strategie...")
    try:
        strategy = MACrossoverStrategy.from_config(cfg)
        print(f"✅ {strategy}")
        print(f"  - Fast Window: {strategy.fast_window}")
        print(f"  - Slow Window: {strategy.slow_window}")
        print(f"  - Price Column: '{strategy.price_col}'")
    except Exception as e:
        print(f"\n❌ FEHLER beim Erstellen der Strategie: {e}")
        print("\nBitte stelle sicher, dass config.toml eine [strategy.ma_crossover] Sektion hat:")
        print("""
[strategy.ma_crossover]
fast_window = 20
slow_window = 50
price_col = "close"
        """)
        return

    # Daten erstellen (später: von Kraken holen)
    print("\n📥 Lade Daten...")
    df = create_dummy_data(n_bars=200)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")

    # Signale generieren (Test)
    print("\n🔍 Generiere Signale...")
    signals = strategy.generate_signals(df)
    n_longs = (signals == 1).sum()
    n_flats = (signals == 0).sum()
    print(f"  - Long Signale: {n_longs}")
    print(f"  - Flat Signale: {n_flats}")

    # Position Sizer erstellen
    print("\n💰 Erstelle Position Sizer...")
    position_sizer = build_position_sizer_from_config(cfg)
    print(f"✅ {position_sizer}")

    # Risk Manager erstellen
    print("\n🛡️  Erstelle Risk Manager...")
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")
    print(f"✅ {risk_manager}")

    # Backtest durchführen (mit Legacy-API für BacktestEngine)
    print("\n⚙️  Führe Realistic Backtest durch...")

    # BacktestEngine erwartet noch die alte API (strategy_signal_fn + params)
    # Wir wrappen die neue OOP-Strategie in die alte API
    def strategy_signal_fn(df, params):
        return strategy.generate_signals(df)

    # Stop-Loss aus Config holen
    stop_pct = cfg.get("strategy.ma_crossover.stop_pct", 0.02)
    strategy_params = {
        "fast_period": strategy.fast_window,
        "slow_period": strategy.slow_window,
        "stop_pct": stop_pct,
    }

    engine = BacktestEngine(core_position_sizer=position_sizer, risk_manager=risk_manager)
    result = engine.run_realistic(
        df=df, strategy_signal_fn=strategy_signal_fn, strategy_params=strategy_params
    )

    # Report drucken
    print_report(result)

    # Sample Trades anzeigen
    if result.trades is not None and not result.trades.empty:
        print("📋 Sample Trades (erste 5):")
        print("-" * 70)
        for i, (_, trade) in enumerate(result.trades.head(5).iterrows(), 1):
            print(
                f"{i}. Entry: {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} @ ${trade['entry_price']:,.2f}"
            )
            print(
                f"   Exit:  {trade['exit_time'].strftime('%Y-%m-%d %H:%M')} @ ${trade['exit_price']:,.2f}"
            )
            print(f"   PnL:   ${trade['pnl']:,.2f} ({trade['exit_reason']})")
            print()
    else:
        print("📋 Keine Trades generiert")
        print(f"   (Blocked Trades: {result.stats.get('blocked_trades', 0)})")


if __name__ == "__main__":
    main()
