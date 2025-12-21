#!/usr/bin/env python3
"""
Peak_Trade Complete Pipeline Demo
===================================
Demonstriert die vollständige Integration:

1. Risk-Layer (Position Sizing + Limits)
2. Config-System (TOML)
3. Kraken-Integration (Data-Layer)
4. Backtest mit allem zusammen

Usage:
    python scripts/demo_complete_pipeline.py
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

from src.core import get_config
from src.risk import (
    PositionSizer,
    PositionSizerConfig,
    RiskLimitChecker,
    RiskLimitsConfig,
    PortfolioState,
)
from src.data import KrakenDataPipeline, fetch_kraken_data
from src.strategies.ma_crossover import generate_signals
from src.backtest.engine import BacktestEngine


def demo_1_config_system():
    """Demo 1: Config-System mit TOML."""
    print("\n" + "=" * 70)
    print("DEMO 1: Config-System")
    print("=" * 70)

    # Config laden
    config = get_config()

    print("\n📋 Geladene Konfiguration:")
    print(f"  Backtest:")
    print(f"    - Initial Cash: ${config.backtest.initial_cash:,.2f}")
    print(f"    - Results Dir:  {config.backtest.results_dir}")

    print(f"\n  Risk Management:")
    print(f"    - Risk per Trade:      {config.risk.risk_per_trade:.1%}")
    print(f"    - Max Position Size:   {config.risk.max_position_size:.0%}")
    print(f"    - Max Daily Loss:      {config.risk.max_daily_loss:.1%}")
    print(f"    - Max Drawdown:        {config.risk.max_drawdown:.0%}")
    print(f"    - Max Positions:       {config.risk.max_positions}")
    print(f"    - Max Total Exposure:  {config.risk.max_total_exposure:.0%}")

    print(f"\n  Data:")
    print(f"    - Default Timeframe:   {config.data.default_timeframe}")
    print(f"    - Data Dir:            {config.data.data_dir}")
    print(f"    - Use Cache:           {config.data.use_cache}")

    print("\n✅ Config-System funktioniert!")


def demo_2_position_sizing():
    """Demo 2: Position Sizing mit Fixed Fractional und Kelly."""
    print("\n" + "=" * 70)
    print("DEMO 2: Position Sizing")
    print("=" * 70)

    capital = 10_000
    entry_price = 50_000
    stop_price = 49_000
    stop_distance = entry_price - stop_price

    # Fixed Fractional
    print("\n🔢 Fixed Fractional Method:")
    config_ff = PositionSizerConfig(
        method="fixed_fractional",
        risk_pct=1.0,  # 1%
        max_position_pct=25.0,  # 25%
    )
    sizer_ff = PositionSizer(config_ff)
    size_ff = sizer_ff.size_position(capital, stop_distance)
    value_ff = size_ff * entry_price

    print(f"  Capital:        ${capital:,.2f}")
    print(f"  Entry:          ${entry_price:,.2f}")
    print(f"  Stop:           ${stop_price:,.2f}")
    print(f"  Risk per Trade: {config_ff.risk_pct}%")
    print(f"  → Position Size: {size_ff:.4f} BTC")
    print(f"  → Position Value: ${value_ff:,.2f}")
    print(f"  → Risk Amount: ${capital * (config_ff.risk_pct / 100):,.2f}")

    # Kelly Criterion
    print("\n🎲 Kelly Criterion Method:")
    config_kelly = PositionSizerConfig(
        method="kelly",
        max_position_pct=25.0,
        kelly_scaling=0.5,  # Konservativ
    )
    sizer_kelly = PositionSizer(config_kelly)

    # Beispiel-Stats (normalerweise aus Backtest)
    win_rate = 0.55  # 55% Win-Rate
    avg_win = 200  # Durchschnittlicher Gewinn
    avg_loss = 100  # Durchschnittlicher Verlust

    size_kelly = sizer_kelly.size_position(
        capital, stop_distance, win_rate=win_rate, avg_win=avg_win, avg_loss=avg_loss
    )
    value_kelly = size_kelly * entry_price

    print(f"  Win Rate:       {win_rate:.0%}")
    print(f"  Avg Win:        ${avg_win:,.2f}")
    print(f"  Avg Loss:       ${avg_loss:,.2f}")
    print(f"  Kelly Scaling:  {config_kelly.kelly_scaling}")
    print(f"  → Kelly Fraction: {sizer_kelly.kelly_criterion(win_rate, avg_win, avg_loss):.2%}")
    print(f"  → Position Size: {size_kelly:.4f} BTC")
    print(f"  → Position Value: ${value_kelly:,.2f}")

    print("\n✅ Position Sizing funktioniert!")


def demo_3_risk_limits():
    """Demo 3: Portfolio Risk Limits."""
    print("\n" + "=" * 70)
    print("DEMO 3: Portfolio Risk Limits")
    print("=" * 70)

    # Risk Limits Config
    config = RiskLimitsConfig(
        max_daily_loss=0.03,  # 3%
        max_drawdown=0.20,  # 20%
        max_positions=2,
        max_total_exposure=0.75,  # 75%
    )
    checker = RiskLimitChecker(config)

    print("\n📊 Portfolio Risk Limits:")
    print(f"  Max Daily Loss:     {config.max_daily_loss:.0%}")
    print(f"  Max Drawdown:       {config.max_drawdown:.0%}")
    print(f"  Max Positions:      {config.max_positions}")
    print(f"  Max Total Exposure: {config.max_total_exposure:.0%}")

    # Test-Szenario 1: Alles OK
    print("\n✅ Szenario 1: Alles im grünen Bereich")
    state_ok = PortfolioState(
        equity=10_000,
        peak_equity=10_500,
        daily_start_equity=10_200,
        open_positions=1,
        total_exposure=2_000,
        current_date=date.today(),
    )

    result_ok = checker.check_limits(state_ok, proposed_position_value=2_000)
    print(f"  Current Equity:   ${state_ok.equity:,.2f}")
    print(f"  Daily P&L:        {result_ok.daily_loss:+.2%}")
    print(f"  Drawdown:         {result_ok.drawdown:.2%}")
    print(f"  Exposure:         {result_ok.exposure_pct:.1%}")
    print(f"  Open Positions:   {state_ok.open_positions}")
    print(f"  → Result: {result_ok.reason}")

    # Test-Szenario 2: Daily Loss Limit erreicht
    print("\n❌ Szenario 2: Daily Loss Limit erreicht")
    state_loss = PortfolioState(
        equity=9_700,  # -3% vom Tagesstart
        peak_equity=10_500,
        daily_start_equity=10_000,
        open_positions=1,
        total_exposure=2_000,
        current_date=date.today(),
    )

    result_loss = checker.check_limits(state_loss, proposed_position_value=2_000)
    print(f"  Current Equity:   ${state_loss.equity:,.2f}")
    print(f"  Daily Start:      ${state_loss.daily_start_equity:,.2f}")
    print(f"  Daily Loss:       {result_loss.daily_loss:.2%}")
    print(f"  → Result: {result_loss.reason}")

    # Test-Szenario 3: Max Positions erreicht
    print("\n❌ Szenario 3: Max Positions erreicht")
    state_positions = PortfolioState(
        equity=10_000,
        peak_equity=10_500,
        daily_start_equity=10_200,
        open_positions=2,  # Limit erreicht
        total_exposure=4_000,
        current_date=date.today(),
    )

    result_positions = checker.check_limits(state_positions, proposed_position_value=2_000)
    print(f"  Open Positions:   {state_positions.open_positions}/{config.max_positions}")
    print(f"  → Result: {result_positions.reason}")

    print("\n✅ Risk Limits funktionieren!")


def demo_4_kraken_pipeline():
    """Demo 4: Kraken Data Pipeline."""
    print("\n" + "=" * 70)
    print("DEMO 4: Kraken Data Pipeline")
    print("=" * 70)

    print("\n⚠️  HINWEIS: Dieses Demo benötigt eine Internetverbindung zu Kraken.")
    print("Falls keine Verbindung besteht, wird ein Fehler angezeigt.")

    try:
        # Test Kraken-Verbindung
        from src.data import test_kraken_connection

        print("\n🔌 Teste Kraken-Verbindung...")

        if not test_kraken_connection():
            print("❌ Keine Verbindung zu Kraken möglich.")
            print("   Nutze stattdessen Dummy-Daten für Demo.\n")
            return create_dummy_data()

        # Pipeline erstellen
        print("\n📡 Erstelle Kraken-Pipeline...")
        pipeline = KrakenDataPipeline(use_cache=True)

        # Daten holen
        print("\n📥 Hole BTC/USD 1h Daten (100 Bars)...")
        df = pipeline.fetch_and_prepare(symbol="BTC/USD", timeframe="1h", limit=100)

        print(f"\n✅ Daten erfolgreich geladen:")
        print(f"  Bars:      {len(df)}")
        print(f"  Zeitraum:  {df.index[0]} bis {df.index[-1]}")
        print(f"  Spalten:   {list(df.columns)}")
        print(f"\n  Erste 3 Zeilen:")
        print(df.head(3).to_string())
        print(f"\n  Stats:")
        print(df.describe().to_string())

        print("\n✅ Kraken-Pipeline funktioniert!")
        return df

    except Exception as e:
        print(f"\n⚠️  Kraken-Fehler: {e}")
        print("   Nutze Dummy-Daten für Demo.\n")
        return create_dummy_data()


def create_dummy_data(n_bars: int = 200) -> pd.DataFrame:
    """Erstellt Dummy-Daten für Demo wenn Kraken nicht verfügbar."""
    print("\n📊 Erstelle Dummy-Daten...")

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

    print(f"  ✅ {len(df)} Dummy-Bars erstellt")
    return df


def demo_5_complete_backtest(df: pd.DataFrame):
    """Demo 5: Vollständiger Backtest mit allem."""
    print("\n" + "=" * 70)
    print("DEMO 5: Kompletter Backtest")
    print("=" * 70)

    config = get_config()

    print("\n⚙️  Konfiguration:")
    print(f"  Initial Capital:  ${config.backtest.initial_cash:,.2f}")
    print(f"  Risk per Trade:   {config.risk.risk_per_trade:.1%}")
    print(f"  Max Position:     {config.risk.max_position_size:.0%}")

    # Strategie-Parameter
    strategy_params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}

    print(f"\n📈 Strategie: MA Crossover")
    print(f"  Fast Period:      {strategy_params['fast_period']}")
    print(f"  Slow Period:      {strategy_params['slow_period']}")
    print(f"  Stop Loss:        {strategy_params['stop_pct']:.1%}")

    # Backtest durchführen
    print(f"\n🔄 Führe Backtest durch...")
    print(f"  Daten: {len(df)} Bars")
    print(f"  Zeitraum: {df.index[0]} bis {df.index[-1]}")

    engine = BacktestEngine()

    try:
        result = engine.run_realistic(
            df=df, strategy_signal_fn=generate_signals, strategy_params=strategy_params
        )

        # Ergebnisse anzeigen
        print("\n" + "=" * 70)
        print("BACKTEST ERGEBNISSE")
        print("=" * 70)

        start_equity = result.equity_curve.iloc[0]
        end_equity = result.equity_curve.iloc[-1]

        print(f"\n💰 Performance:")
        print(f"  Start Equity:     ${start_equity:,.2f}")
        print(f"  End Equity:       ${end_equity:,.2f}")
        print(f"  Total Return:     {result.stats.get('total_return', 0):+.2%}")
        print(f"  Max Drawdown:     {result.stats.get('max_drawdown', 0):.2%}")

        print(f"\n📊 Risk-Adjusted:")
        print(f"  Sharpe Ratio:     {result.stats.get('sharpe', 0):.2f}")

        print(f"\n🎯 Trades:")
        print(f"  Total Trades:     {result.stats.get('total_trades', 0)}")
        print(f"  Win Rate:         {result.stats.get('win_rate', 0):.1%}")
        print(f"  Profit Factor:    {result.stats.get('profit_factor', 0):.2f}")

        # Sample Trades
        if result.trades and len(result.trades) > 0:
            print(f"\n📋 Beispiel-Trades (erste 3):")
            for i, trade in enumerate(result.trades[:3], 1):
                pnl_pct = (trade.pnl / (trade.size * trade.entry_price)) if trade.size > 0 else 0
                print(f"\n  Trade {i}:")
                print(
                    f"    Entry:  {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:,.2f}"
                )
                print(
                    f"    Exit:   {trade.exit_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.exit_price:,.2f}"
                )
                print(f"    Size:   {trade.size:.4f} BTC")
                print(f"    P&L:    ${trade.pnl:+,.2f} ({pnl_pct:+.2%})")
                print(f"    Reason: {trade.exit_reason}")

        print("\n✅ Backtest abgeschlossen!")

    except Exception as e:
        print(f"\n❌ Backtest-Fehler: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Hauptfunktion - führt alle Demos durch."""
    print("\n" + "=" * 70)
    print("PEAK_TRADE COMPLETE PIPELINE DEMO")
    print("=" * 70)
    print("\nDieses Demo zeigt:")
    print("  1. Config-System (TOML)")
    print("  2. Position Sizing (Fixed Fractional + Kelly)")
    print("  3. Portfolio Risk Limits")
    print("  4. Kraken Data Pipeline")
    print("  5. Vollständiger Backtest")

    try:
        # Demo 1: Config
        demo_1_config_system()

        # Demo 2: Position Sizing
        demo_2_position_sizing()

        # Demo 3: Risk Limits
        demo_3_risk_limits()

        # Demo 4: Kraken Pipeline (liefert Daten für Demo 5)
        df = demo_4_kraken_pipeline()

        # Demo 5: Kompletter Backtest
        demo_5_complete_backtest(df)

        print("\n" + "=" * 70)
        print("✅ ALLE DEMOS ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 70)

        print("\n📚 Weitere Infos:")
        print("  - Risk-Layer:      src/risk/position_sizer.py + limits.py")
        print("  - Config-System:   src/core/config.py + config.toml")
        print("  - Kraken-Pipeline: src/data/kraken_pipeline.py")
        print("  - Backtest-Engine: src/backtest/engine.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo abgebrochen.")
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
