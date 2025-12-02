#!/usr/bin/env python3
"""
Peak_Trade Simple Backtest
===========================
Einfaches Backtest-Script mit TOML-Config-Loader.

Zeigt vollständige Integration:
- TOML Config Loader (ohne Pydantic)
- BacktestEngine mit Risk-Layer
- Strategie-Parameter aus Config
- Risk-Parameter aus Config

Usage:
    python scripts/run_simple_backtest.py

    # Mit custom config:
    PEAK_TRADE_CONFIG=my_config.toml python scripts/run_simple_backtest.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Simple Config Loader (TOML ohne Pydantic)
from src.core.config_simple import load_config, get_strategy_config, list_strategies

# Backtest Engine mit Risk-Layer
from src.backtest.engine import BacktestEngine

# Risk-Layer
from src.risk import (
    PositionSizer,
    PositionSizerConfig,
    RiskLimits,
    RiskLimitsConfig,
)

# Strategie
from src.strategies.ma_crossover import generate_signals


def create_test_data(n_bars: int = 200) -> pd.DataFrame:
    """Erstellt Test-OHLCV-Daten."""
    np.random.seed(42)

    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h", tz="UTC")

    # Preis-Simulation
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


def main():
    """Hauptfunktion."""
    print("\n" + "=" * 70)
    print("PEAK_TRADE SIMPLE BACKTEST")
    print("=" * 70)
    print("\nZeigt vollständige Config-Integration:\n")
    print("  ✅ TOML Config Loader (ohne Pydantic)")
    print("  ✅ BacktestEngine mit Risk-Layer")
    print("  ✅ Strategie-Parameter aus Config")
    print("  ✅ Risk-Parameter aus Config")

    # ========================================================================
    # 1. CONFIG LADEN
    # ========================================================================
    print("\n" + "-" * 70)
    print("1. Config laden")
    print("-" * 70)

    try:
        cfg = load_config()
        print(f"✅ Config geladen: config/default.toml")
    except FileNotFoundError as e:
        print(f"❌ Fehler: {e}")
        return

    # Config-Übersicht
    print(f"\n📋 Backtest-Config:")
    print(f"  Initial Cash:      ${cfg['backtest']['initial_cash']:,.2f}")
    print(f"  Results Dir:       {cfg['backtest']['results_dir']}")

    print(f"\n📋 Risk-Config:")
    print(f"  Risk per Trade:    {cfg['risk']['risk_per_trade']:.1%}")
    print(f"  Max Position:      {cfg['risk']['max_position_size']:.0%}")
    print(f"  Max Drawdown:      {cfg['risk']['max_drawdown_pct']:.1f}%")
    print(f"  Daily Loss Limit:  {cfg['risk']['daily_loss_limit_pct']:.1f}%")

    # Verfügbare Strategien
    strategies = list_strategies(cfg)
    print(f"\n📋 Verfügbare Strategien: {', '.join(strategies)}")

    # ========================================================================
    # 2. STRATEGIE-CONFIG LADEN
    # ========================================================================
    print("\n" + "-" * 70)
    print("2. Strategie-Config laden")
    print("-" * 70)

    strategy_name = "ma_crossover"
    try:
        strategy_config = get_strategy_config(cfg, strategy_name)
        print(f"✅ Strategie '{strategy_name}' geladen")
        print(f"\n📋 Parameter:")
        for key, value in strategy_config.items():
            print(f"  {key:20s}: {value}")
    except KeyError as e:
        print(f"❌ Fehler: {e}")
        return

    # ========================================================================
    # 3. RISK-LAYER INITIALISIEREN
    # ========================================================================
    print("\n" + "-" * 70)
    print("3. Risk-Layer initialisieren")
    print("-" * 70)

    # Position Sizer aus Config
    position_sizer_config = PositionSizerConfig(
        method=cfg['risk']['position_sizing_method'],
        risk_pct=cfg['risk']['risk_per_trade'] * 100,  # Dezimal -> Prozent
        max_position_pct=cfg['risk']['max_position_size'] * 100,
    )
    position_sizer = PositionSizer(position_sizer_config)
    print(f"✅ PositionSizer: {position_sizer_config.method}")

    # Risk Limits aus Config
    risk_limits_config = RiskLimitsConfig(
        max_drawdown_pct=cfg['risk']['max_drawdown_pct'],
        max_position_pct=cfg['risk']['max_position_pct'],
        daily_loss_limit_pct=cfg['risk']['daily_loss_limit_pct'],
    )
    risk_limits = RiskLimits(risk_limits_config)
    print(f"✅ RiskLimits: DD={risk_limits_config.max_drawdown_pct}%, "
          f"Pos={risk_limits_config.max_position_pct}%, "
          f"Daily={risk_limits_config.daily_loss_limit_pct}%")

    # ========================================================================
    # 4. BACKTEST-ENGINE INITIALISIEREN
    # ========================================================================
    print("\n" + "-" * 70)
    print("4. BacktestEngine initialisieren")
    print("-" * 70)

    # Engine mit Risk-Layer
    engine = BacktestEngine(
        position_sizer=position_sizer,
        risk_limits=risk_limits
    )
    print("✅ BacktestEngine mit Risk-Layer erstellt")

    # ========================================================================
    # 5. DATEN LADEN
    # ========================================================================
    print("\n" + "-" * 70)
    print("5. Daten laden")
    print("-" * 70)

    df = create_test_data(200)
    print(f"✅ Daten erstellt: {len(df)} Bars")
    print(f"  Zeitraum: {df.index[0]} bis {df.index[-1]}")

    # ========================================================================
    # 6. BACKTEST DURCHFÜHREN
    # ========================================================================
    print("\n" + "-" * 70)
    print("6. Backtest durchführen")
    print("-" * 70)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=generate_signals,
        strategy_params=strategy_config
    )

    print("✅ Backtest abgeschlossen!")

    # ========================================================================
    # 7. ERGEBNISSE
    # ========================================================================
    print("\n" + "=" * 70)
    print("BACKTEST ERGEBNISSE")
    print("=" * 70)

    print(f"\n📊 Performance:")
    print(f"  Total Return:      {result.stats['total_return']:>10.2%}")
    print(f"  Max Drawdown:      {result.stats['max_drawdown']:>10.2%}")
    print(f"  Sharpe Ratio:      {result.stats['sharpe']:>10.2f}")

    print(f"\n📊 Trades:")
    print(f"  Total Trades:      {result.stats['total_trades']:>10}")
    print(f"  Blocked Trades:    {result.blocked_trades:>10}")
    print(f"  Win Rate:          {result.stats['win_rate']:>10.1%}")
    print(f"  Profit Factor:     {result.stats['profit_factor']:>10.2f}")

    print(f"\n📊 Equity:")
    print(f"  Start Capital:     ${cfg['backtest']['initial_cash']:>10,.2f}")
    print(f"  End Capital:       ${result.equity_curve.iloc[-1]:>10,.2f}")

    # Trade-Details (erste 5)
    if len(result.trades) > 0:
        print(f"\n📋 Trade-Details (erste 5 von {len(result.trades)}):")
        print("-" * 70)
        for i, trade in enumerate(result.trades[:5], 1):
            print(f"\nTrade {i}:")
            print(f"  Entry:  {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:,.2f}")
            print(f"  Exit:   {trade.exit_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.exit_price:,.2f}")
            print(f"  Size:   {trade.size:.4f} BTC")
            print(f"  P&L:    ${trade.pnl:+,.2f} ({trade.pnl_pct:+.2f}%)")
            print(f"  Reason: {trade.exit_reason}")
    else:
        print(f"\n⚠️  Keine Trades ausgeführt!")
        print(f"   Alle {result.blocked_trades} Trades wurden durch Risk-Limits blockiert.")
        print(f"\n   Mögliche Gründe:")
        print(f"   - Position zu klein (min_position_value = ${cfg['risk']['min_position_value']:.0f})")
        print(f"   - Max Position zu niedrig (max_position_pct = {cfg['risk']['max_position_pct']:.0%})")
        print(f"   - Stop-Distanz zu eng")

    print("\n" + "=" * 70)
    print("✅ DEMO ABGESCHLOSSEN!")
    print("=" * 70)

    print("\n💡 Nächste Schritte:")
    print("  1. Risk-Parameter in config/default.toml anpassen")
    print("  2. Mit echten Kraken-Daten testen")
    print("  3. Andere Strategien ausprobieren")

    print("\n📝 Config anpassen:")
    print("  vim config/default.toml")
    print("  # Oder:")
    print("  PEAK_TRADE_CONFIG=my_config.toml python scripts/run_simple_backtest.py")

    print()


if __name__ == "__main__":
    main()
