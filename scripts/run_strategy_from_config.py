#!/usr/bin/env python3
"""
Peak_Trade Generic Strategy Runner
===================================
Generischer Runner der ALLE Bausteine nutzt:
- Strategy-Registry
- Position Sizing
- Risk Management
- Data-Pipeline

Usage:
    python scripts/run_strategy_from_config.py
    python scripts/run_strategy_from_config.py --strategy rsi_reversion
    python scripts/run_strategy_from_config.py --strategy breakout_donchian --bars 500
    python scripts/run_strategy_from_config.py --list-strategies
"""

import sys
import argparse
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.tracking import build_tracker_from_config
from src.core.experiments import log_experiment_from_result
from src.strategies.registry import (
    get_available_strategy_keys,
    create_strategy_from_config,
    list_strategies,
)
from src.backtest.engine import BacktestEngine
from src.backtest.stats import validate_for_live_trading


def create_dummy_data(n_bars: int = 200) -> pd.DataFrame:
    """
    Erstellt Dummy-OHLCV-Daten für Tests.

    Simuliert verschiedene Marktbedingungen für flexible Strategie-Tests.
    """
    np.random.seed(42)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Preis-Simulation mit Trend, Oszillation und Noise
    base_price = 50000

    # Langfristiger Trend
    trend = np.linspace(0, 3000, n_bars)

    # Oszillation (für verschiedene Strategien)
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


def print_report(result, strategy_name: str):
    """Druckt Performance-Report."""

    print("\n" + "=" * 70)
    print(f"BACKTEST PERFORMANCE REPORT - {strategy_name.upper()}")
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

    # Risk-Adjusted (inkl. CAGR)
    print("\n📈 RISK-ADJUSTED METRIKEN")
    print("-" * 70)
    if "cagr" in result.stats:
        print(f"CAGR:              {result.stats['cagr']:>7.2%}")
    print(f"Sharpe Ratio:      {result.stats['sharpe']:>7.2f}")

    # Trade-Stats
    print("\n🎯 TRADE STATISTIKEN")
    print("-" * 70)
    print(f"Total Trades:      {result.stats['total_trades']:>7}")
    print(f"Win Rate:          {result.stats['win_rate']:>7.2%}")
    print(f"Profit Factor:     {result.stats['profit_factor']:>7.2f}")
    blocked_trades = result.stats.get("blocked_trades", result.metadata.get("blocked_trades", 0))
    print(f"Blocked Trades:    {blocked_trades:>7}")

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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Generic Strategy Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default strategy from config.toml
  python scripts/run_strategy_from_config.py

  # Run with specific strategy
  python scripts/run_strategy_from_config.py --strategy rsi_reversion

  # Run with more data bars
  python scripts/run_strategy_from_config.py --strategy breakout_donchian --bars 500

  # List all available strategies
  python scripts/run_strategy_from_config.py --list-strategies
        """,
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Strategy key (overrides config.toml). Use --list-strategies to see available options.",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Number of bars to generate for backtest (default: 200)",
    )

    parser.add_argument(
        "--list-strategies", action="store_true", help="List all available strategies and exit"
    )

    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Optional name for this backtest run (for reports)",
    )

    parser.add_argument(
        "--no-report", action="store_true", help="If set, no report files will be written"
    )

    return parser.parse_args()


def main():
    """Main-Funktion."""

    # Parse CLI arguments
    args = parse_args()

    # List strategies if requested
    if args.list_strategies:
        print("\n🚀 Peak_Trade Strategy Registry")
        print("=" * 70)
        list_strategies(verbose=True)
        return

    print("\n🚀 Peak_Trade Generic Strategy Runner")
    print("=" * 70)

    # Config laden
    print("\n⚙️  Lade Konfiguration...")
    try:
        cfg = load_config("config.toml")
        print("✅ config.toml erfolgreich geladen")
    except FileNotFoundError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nBitte erstelle eine config.toml im Projekt-Root.")
        return

    # Basis-Config anzeigen
    initial_cash = cfg.get("general.starting_capital", 10000.0)
    risk_per_trade = cfg.get("risk.risk_per_trade", 0.01)
    max_position_size = cfg.get("risk.max_position_size", 0.25)

    print(f"  - Initial Cash: ${initial_cash:,.2f}")
    print(f"  - Risk per Trade: {risk_per_trade:.1%}")
    print(f"  - Max Position Size: {max_position_size:.0%}")

    # Strategie auswählen
    if args.strategy:
        strategy_key = args.strategy
        print(f"\n📊 CLI-Override: Nutze Strategie '{strategy_key}'")
    else:
        strategy_key = cfg.get("general.active_strategy", "ma_crossover")
        print(f"\n📊 Nutze aktive Strategie aus Config: '{strategy_key}'")

    # Strategie erstellen
    print(f"\n🔨 Erstelle Strategie '{strategy_key}'...")
    try:
        strategy = create_strategy_from_config(strategy_key, cfg)
        print(f"✅ {strategy}")
    except KeyError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nVerfügbare Strategien:")
        list_strategies(verbose=False)
        return
    except Exception as e:
        print(f"\n❌ FEHLER beim Erstellen der Strategie: {e}")
        return

    # Daten erstellen (später: von Kraken holen)
    print(f"\n📥 Lade Daten ({args.bars} bars)...")
    df = create_dummy_data(n_bars=args.bars)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")

    # Signale generieren (Test)
    print("\n🔍 Generiere Signale...")
    signals = strategy.generate_signals(df)
    n_longs = (signals == 1).sum()
    n_shorts = (signals == -1).sum()
    n_flats = (signals == 0).sum()
    print(f"  - Long Signale: {n_longs}")
    if n_shorts > 0:
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

    # Tracker erstellen (optional, default: None)
    tracker = build_tracker_from_config(cfg)
    if tracker:
        print("\n📊 Tracker aktiviert")

    # Backtest durchführen
    print("\n⚙️  Führe Realistic Backtest durch...")

    # Wrapper für Legacy-API
    def strategy_signal_fn(df, params):
        # Konvertiere Short-Signale (-1) in Flat (0) für Long-Only Engine
        sigs = strategy.generate_signals(df)
        return sigs.replace(-1, 0)

    # Stop-Loss aus Config holen (strategie-spezifisch oder global)
    stop_pct = cfg.get(f"strategy.{strategy_key}.stop_pct", 0.02)
    strategy_params = {
        "stop_pct": stop_pct,
    }

    engine = BacktestEngine(
        core_position_sizer=position_sizer, 
        risk_manager=risk_manager,
        tracker=tracker
    )
    
    # Tracker: Start Run
    if tracker:
        run_name = f"{strategy_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tracker.start_run(run_name=run_name, tags={"strategy": strategy_key, "env": "dev"})
    
    try:
        result = engine.run_realistic(
            df=df, strategy_signal_fn=strategy_signal_fn, strategy_params=strategy_params
        )
    finally:
        # Tracker: End Run (auch bei Exception)
        if tracker:
            tracker.end_run(status="FINISHED")

    # Report drucken
    print_report(result, strategy_key)

    # Sample Trades anzeigen
    if result.trades is not None and len(result.trades) > 0:
        print("📋 Sample Trades (erste 5):")
        print("-" * 70)
        for i, row in result.trades.head(5).iterrows():
            print(
                f"{i + 1}. Entry: {row['entry_time'].strftime('%Y-%m-%d %H:%M')} @ ${row['entry_price']:,.2f}"
            )
            print(
                f"   Exit:  {row['exit_time'].strftime('%Y-%m-%d %H:%M')} @ ${row['exit_price']:,.2f}"
            )
            print(f"   PnL:   ${row['pnl']:,.2f} ({row['exit_reason']})")
            print()
    else:
        print("📋 Keine Trades generiert")
        blocked_trades = result.stats.get(
            "blocked_trades", result.metadata.get("blocked_trades", 0)
        )
        print(f"   (Blocked Trades: {blocked_trades})")

    # Reports speichern (falls nicht deaktiviert)
    if not args.no_report:
        from pathlib import Path
        from src.backtest.reporting import save_full_report

        # Run-Name bestimmen
        base_name = args.run_name or "run"
        run_name = f"{strategy_key}_{base_name}"

        print(f"\n💾 Speichere Reports...")
        save_full_report(
            result=result,
            output_dir="reports",
            run_name=run_name,
            save_plots_flag=True,
            save_html_flag=True,
        )
        print(f"✅ Reports gespeichert unter: reports/{run_name}_* [csv/json/png/html]")

        # Experiment in Registry loggen
        log_experiment_from_result(
            result=result,
            run_type="single_backtest",
            run_name=run_name,
            strategy_key=strategy_key,
            symbol=result.metadata.get("symbol"),
            report_dir=Path("reports"),
            report_prefix=run_name,
            extra_metadata={
                "runner": "run_strategy_from_config.py",
            },
        )
        print(f"📊 Experiment geloggt in Registry")

    print(f"\n✅ Backtest für '{strategy_key}' abgeschlossen!\n")


if __name__ == "__main__":
    main()
