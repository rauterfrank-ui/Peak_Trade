#!/usr/bin/env python3
"""
Peak_Trade Donchian Breakout Backtest Runner (OOP Version)
===========================================================
Führt Realistic Backtest mit Donchian-Channel-Breakout-Strategie durch.
Nutzt die neue OOP-Strategy-API mit BaseStrategy.

Usage:
    python scripts/run_donchian_realistic.py
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
from src.strategies import load_strategy
from src.backtest.engine import BacktestEngine
from src.backtest.stats import validate_for_live_trading

DONCHIAN_STRATEGY_KEY = "breakout_donchian"
DONCHIAN_CONFIG_SECTION = "strategy.breakout_donchian"


def create_dummy_data(n_bars: int = 200) -> pd.DataFrame:
    """
    Erstellt Dummy-OHLCV-Daten für Tests.

    Simuliert Trend mit Breakouts für Donchian-Strategie.
    """
    np.random.seed(42)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Preis-Simulation mit Trend und Breakouts
    base_price = 50000

    # Langfristiger Trend mit Stufen
    trend = np.zeros(n_bars)
    for i in range(0, n_bars, 40):
        end = min(i + 40, n_bars)
        trend[i:end] = (i // 40) * 2000

    # Noise
    noise = np.random.randn(n_bars).cumsum() * 100

    close_prices = base_price + trend + noise

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
    print(f"Blocked Trades:    {result.blocked_trades:>7}")

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


def _load_donchian_strategy_params(cfg) -> dict:
    """Lädt Donchian-Parameter aus Config; fail-closed bei fehlender Sektion."""
    lookback = cfg.get(f"{DONCHIAN_CONFIG_SECTION}.lookback")
    if lookback is None:
        raise KeyError(f"Config-Sektion [{DONCHIAN_CONFIG_SECTION}] fehlt oder ist unvollständig")
    return {
        "lookback": lookback,
        "stop_pct": cfg.get(f"{DONCHIAN_CONFIG_SECTION}.stop_pct", 0.02),
        "price_col": cfg.get(f"{DONCHIAN_CONFIG_SECTION}.price_col", "close"),
    }


def _long_only_signal_fn(df, params):
    """Long-only Wrapper: Short-Signale (-1) in Flat (0) für Long-Only Engine."""
    sigs = load_strategy(DONCHIAN_STRATEGY_KEY)(df, params)
    return sigs.replace(-1, 0)


def main():
    """Main-Funktion."""

    print("\n🚀 Peak_Trade Donchian Breakout Backtest (OOP Version)")
    print("=" * 70)

    # Config laden
    print("\n⚙️  Lade Konfiguration...")
    try:
        cfg = load_config("config.toml")
        print("✅ config.toml erfolgreich geladen")
    except FileNotFoundError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nBitte erstelle eine config.toml im Projekt-Root mit:")
        print(
            """
[strategy.breakout_donchian]
lookback = 20
price_col = "close"
        """
        )
        sys.exit(1)

    # Basis-Config anzeigen
    initial_cash = cfg.get("backtest.initial_cash", 10000.0)
    risk_per_trade = cfg.get("risk.risk_per_trade", 0.01)
    max_position_size = cfg.get("risk.max_position_size", 0.25)

    print(f"  - Initial Cash: ${initial_cash:,.2f}")
    print(f"  - Risk per Trade: {risk_per_trade:.1%}")
    print(f"  - Max Position Size: {max_position_size:.0%}")

    # Strategie-Parameter laden
    print("\n📊 Strategie-Parameter...")
    try:
        strategy_params = _load_donchian_strategy_params(cfg)
        print(f"  - Lookback: {strategy_params['lookback']}")
        print(f"  - Price Column: '{strategy_params['price_col']}'")
    except KeyError as e:
        print(f"\n❌ FEHLER: {e}")
        print(
            "\nBitte stelle sicher, dass config.toml eine [strategy.breakout_donchian] Sektion hat."
        )
        sys.exit(1)

    # Kanonische Strategie für Signale (unwrapped)
    base_signal_fn = load_strategy(DONCHIAN_STRATEGY_KEY)

    # Daten erstellen (später: von Kraken holen)
    print("\n📥 Lade Daten...")
    df = create_dummy_data(n_bars=200)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")

    # Signale generieren (Test)
    print("\n🔍 Generiere Signale...")
    signals = base_signal_fn(df, strategy_params)
    n_longs = (signals == 1).sum()
    n_shorts = (signals == -1).sum()
    n_flats = (signals == 0).sum()
    print(f"  - Long Signale: {n_longs}")
    print(f"  - Short Signale: {n_shorts}")
    print(f"  - Flat Signale: {n_flats}")

    # Position Sizer erstellen
    print("\n💰 Erstelle Position Sizer...")
    position_sizer = build_position_sizer_from_config(cfg)
    print(f"✅ {position_sizer}")

    # Risk Manager erstellen
    print("\n🛡️  Erstelle Risk Manager...")
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")
    print(f"✅ {risk_manager}")

    # Backtest durchführen (Long-Only Wrapper für Engine)
    print("\n⚙️  Führe Realistic Backtest durch...")

    engine = BacktestEngine(core_position_sizer=position_sizer, risk_manager=risk_manager)
    result = engine.run_realistic(
        df=df, strategy_signal_fn=_long_only_signal_fn, strategy_params=strategy_params
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
    else:
        print("📋 Keine Trades generiert")
        print(f"   (Blocked Trades: {result.blocked_trades})")


if __name__ == "__main__":
    main()
