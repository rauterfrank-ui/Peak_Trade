#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/demo_execution_backtest.py
"""
Peak_Trade: Demo-Script fuer ExecutionPipeline-Backtest (Phase 16C/16D)
======================================================================

Demonstriert die Integration der ExecutionPipeline (Phase 16A/16B) in die
BacktestEngine sowie das Execution-Reporting (Phase 16D).

Zeigt den kompletten Workflow:

    Data -> Strategy -> ExecutionPipeline -> BacktestEngine -> Results/Logs -> Reporting

Features:
- Backtest mit ExecutionPipeline (default) oder Legacy-Modus
- Execution-Logging mit detaillierten Summaries
- Vergleich: ExecutionPipeline vs. Legacy-Modus
- Konfigurierbare Fees und Slippage
- ExecutionStats-Reporting (Phase 16D)

WICHTIG: Es werden KEINE echten Orders an Boersen gesendet.
         Alles ist Paper-/Sandbox-Simulation.

Usage:
    # ExecutionPipeline-Modus (Default)
    python -m scripts.demo_execution_backtest

    # Mit Parametern
    python -m scripts.demo_execution_backtest \\
        --symbol BTC/EUR \\
        --start 2024-01-01 \\
        --end 2024-02-01 \\
        --strategy ma_crossover

    # Legacy-Modus (ohne ExecutionPipeline)
    python -m scripts.demo_execution_backtest --use-legacy

    # Vergleichsmodus (beide Modi nebeneinander)
    python -m scripts.demo_execution_backtest --compare
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Pfad-Setup fuer direkten Aufruf
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestEngine
from src.backtest.result import BacktestResult
from src.reporting.execution_reports import (
    ExecutionStats,
    from_execution_logs,
    from_execution_results,
    format_execution_stats,
)


# =============================================================================
# Strategy Loader
# =============================================================================


def get_strategy_fn(name: str) -> Callable[[pd.DataFrame, Dict[str, Any]], pd.Series]:
    """
    Laedt die Signal-Funktion fuer eine Strategie.

    Args:
        name: Strategie-Name (z.B. "ma_crossover", "rsi_reversion", "macd")

    Returns:
        Callable: generate_signals(df, params) -> pd.Series

    Raises:
        ValueError: Wenn Strategie unbekannt ist
    """
    strategy_map = {
        "ma_crossover": "src.strategies.ma_crossover",
        "rsi_reversion": "src.strategies.rsi_reversion",
        "macd": "src.strategies.macd",
        "momentum": "src.strategies.momentum",
        "bollinger": "src.strategies.bollinger",
        "breakout_donchian": "src.strategies.breakout_donchian",
    }

    if name not in strategy_map:
        available = ", ".join(sorted(strategy_map.keys()))
        raise ValueError(f"Unbekannte Strategie '{name}'. Verfuegbar: {available}")

    module_path = strategy_map[name]
    module = __import__(module_path, fromlist=["generate_signals"])
    return module.generate_signals


def get_default_strategy_params(name: str) -> Dict[str, Any]:
    """
    Gibt sinnvolle Default-Parameter fuer eine Strategie zurueck.

    Args:
        name: Strategie-Name

    Returns:
        Dict mit Default-Parametern
    """
    defaults = {
        "ma_crossover": {
            "fast_period": 10,
            "slow_period": 30,
            "stop_pct": 0.02,
        },
        "rsi_reversion": {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70,
            "stop_pct": 0.02,
        },
        "macd": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "stop_pct": 0.02,
        },
        "momentum": {
            "lookback": 20,
            "threshold": 0.02,
            "stop_pct": 0.02,
        },
        "bollinger": {
            "period": 20,
            "num_std": 2.0,
            "stop_pct": 0.02,
        },
        "breakout_donchian": {
            "period": 20,
            "stop_pct": 0.02,
        },
    }
    return defaults.get(name, {"stop_pct": 0.02})


# =============================================================================
# Data Generation
# =============================================================================


def generate_sample_data(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    bars: int = 200,
    timeframe: str = "1h",
) -> pd.DataFrame:
    """
    Generiert Sample-OHLCV-Daten fuer den Backtest.

    Args:
        symbol: Trading-Symbol (beeinflusst Basis-Preis)
        start: Start-Datum (optional, sonst bars rueckwaerts von end)
        end: End-Datum (optional, sonst jetzt)
        bars: Anzahl Bars (wenn start nicht gesetzt)
        timeframe: Timeframe ("1h", "4h", "1d")

    Returns:
        pd.DataFrame mit OHLCV-Daten
    """
    # Basis-Preis je nach Symbol
    if "BTC" in symbol.upper():
        base_price = 50000.0
        volatility = 0.02
    elif "ETH" in symbol.upper():
        base_price = 3000.0
        volatility = 0.025
    elif "LTC" in symbol.upper():
        base_price = 100.0
        volatility = 0.03
    else:
        base_price = 1000.0
        volatility = 0.02

    # Seed fuer Reproduzierbarkeit
    np.random.seed(42)

    # Frequenz bestimmen
    freq_map = {"1h": "h", "4h": "4h", "1d": "D", "1m": "min"}
    freq = freq_map.get(timeframe, "h")

    # Zeitraum bestimmen
    if end:
        end_time = pd.to_datetime(end)
    else:
        end_time = datetime.now()

    if start:
        start_time = pd.to_datetime(start)
        index = pd.date_range(start=start_time, end=end_time, freq=freq)
        bars = len(index)
    else:
        index = pd.date_range(end=end_time, periods=bars, freq=freq)

    # Preis-Simulation mit Trend und Oszillation (fuer MA-Crossovers)
    trend = np.linspace(0, base_price * 0.1, bars)
    cycle = np.sin(np.linspace(0, 4 * np.pi, bars)) * base_price * 0.04
    noise = np.random.randn(bars).cumsum() * base_price * 0.01
    close = base_price + trend + cycle + noise

    # OHLCV generieren
    data = {
        "open": close * (1 + np.random.uniform(-0.002, 0.002, bars)),
        "high": close * (1 + np.abs(np.random.normal(0, 0.005, bars))),
        "low": close * (1 - np.abs(np.random.normal(0, 0.005, bars))),
        "close": close,
        "volume": np.random.uniform(100, 10000, bars),
    }

    df = pd.DataFrame(data, index=index)

    # Konsistenz: high >= max(open, close), low <= min(open, close)
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)

    return df


# =============================================================================
# CLI Parser
# =============================================================================


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Demo-Script fuer ExecutionPipeline-Backtest (Phase 16C)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # ExecutionPipeline-Modus (Default)
  python -m scripts.demo_execution_backtest

  # Mit Parametern
  python -m scripts.demo_execution_backtest --symbol BTC/EUR --start 2024-01-01 --end 2024-02-01

  # Legacy-Modus
  python -m scripts.demo_execution_backtest --use-legacy

  # Vergleichsmodus
  python -m scripts.demo_execution_backtest --compare
        """,
    )

    # Symbol & Zeitraum
    parser.add_argument(
        "--symbol",
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--start",
        help="Start-Datum (YYYY-MM-DD), z.B. 2024-01-01",
    )
    parser.add_argument(
        "--end",
        help="End-Datum (YYYY-MM-DD), z.B. 2024-02-01",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Anzahl Bars (wenn --start nicht gesetzt, default: 200)",
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        choices=["1h", "4h", "1d"],
        help="Timeframe (default: 1h)",
    )

    # Strategie
    parser.add_argument(
        "--strategy",
        default="ma_crossover",
        help="Strategie-Name (default: ma_crossover)",
    )

    # Execution-Parameter
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

    # Modi
    parser.add_argument(
        "--use-legacy",
        action="store_true",
        help="Legacy-Modus ohne ExecutionPipeline",
    )
    parser.add_argument(
        "--no-log-executions",
        action="store_true",
        help="Execution-Logging deaktivieren (default: aktiviert)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Vergleiche ExecutionPipeline vs. Legacy-Modus",
    )

    # Output
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausfuehrliche Ausgabe",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Detaillierte ExecutionStats ausgeben (Phase 16D)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plots speichern (Equity, Slippage, etc.)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output-Verzeichnis fuer Plots (default: reports)",
    )

    return parser.parse_args(argv)


# =============================================================================
# Output Formatting
# =============================================================================


def print_header(
    symbol: str,
    mode: str,
    start: str,
    end: str,
    strategy: str,
    params: Dict[str, Any],
) -> None:
    """Druckt den Header mit Konfiguration."""
    print("\n" + "=" * 70)
    print("Peak_Trade Demo: ExecutionPipeline-Backtest (Phase 16C)")
    print("=" * 70)
    print(f"\nSymbol:     {symbol}")
    print(f"Mode:       {mode}")
    print(f"Zeitraum:   {start} -> {end}")
    print(f"Strategy:   {strategy}")
    print(f"Params:     {params}")
    print("\n" + "-" * 70)


def print_core_stats(result: BacktestResult) -> None:
    """Druckt die Kern-Metriken."""
    stats = result.stats
    print("\n[Performance]")
    print(f"  Total Return:     {stats.get('total_return', 0):+.2%}")
    print(f"  Max Drawdown:     {stats.get('max_drawdown', 0):.2%}")
    print(f"  Sharpe Ratio:     {stats.get('sharpe', 0):.2f}")
    print(f"  Calmar Ratio:     {stats.get('calmar', 0):.2f}")


def print_trade_stats(result: BacktestResult) -> None:
    """Druckt Trade-Statistiken."""
    stats = result.stats
    print("\n[Trade-Statistiken]")
    print(f"  Total Trades:     {stats.get('total_trades', 0)}")
    print(f"  Win Rate:         {stats.get('win_rate', 0):.1%}")
    print(f"  Profit Factor:    {stats.get('profit_factor', 0):.2f}")
    print(f"  Blocked Trades:   {stats.get('blocked_trades', 0)}")


def print_execution_stats(result: BacktestResult) -> None:
    """Druckt ExecutionPipeline-spezifische Statistiken."""
    stats = result.stats

    # Nur anzeigen wenn Order-Layer aktiv war
    if "total_orders" not in stats:
        return

    print("\n[Execution-Details]")
    print(f"  Total Orders:     {stats.get('total_orders', 0)}")
    print(f"  Filled Orders:    {stats.get('filled_orders', 0)}")
    print(f"  Rejected Orders:  {stats.get('rejected_orders', 0)}")
    print(f"  Total Fees:       {stats.get('total_fees', 0):.2f} EUR")
    print(f"  Total Slippage:   {stats.get('total_slippage', 0):.2f} EUR")


def print_execution_logs(engine: BacktestEngine, max_entries: int = 3) -> None:
    """Druckt Execution-Log-Entries."""
    logs = engine.get_execution_logs()

    if not logs:
        print("\n[Execution-Logs]")
        print("  (keine Logs vorhanden)")
        return

    print(f"\n[Execution-Logs] ({len(logs)} Eintraege)")
    for i, log in enumerate(logs[:max_entries]):
        print(f"\n  Log #{i + 1}:")
        # Formatierte JSON-Ausgabe
        for key, value in log.items():
            if isinstance(value, float):
                print(f"    {key}: {value:.4f}")
            else:
                print(f"    {key}: {value}")


def print_detailed_execution_stats(engine: BacktestEngine, result: BacktestResult) -> None:
    """
    Druckt detaillierte ExecutionStats (Phase 16D).

    Nutzt das neue Reporting-Modul fuer aggregierte Statistiken.
    """
    # Versuche zuerst aus execution_results (detaillierter)
    if hasattr(engine, "execution_results") and engine.execution_results:
        stats = from_execution_results(engine.execution_results)
        source = "execution_results"
    else:
        # Fallback auf Logs
        logs = engine.get_execution_logs()
        stats = from_execution_logs(logs)
        source = "execution_logs"

    # Hit-Rate aus Backtest-Result uebernehmen
    if result.stats:
        stats.hit_rate = result.stats.get("win_rate", 0.0)
        n_trades = result.stats.get("total_trades", 0)
        stats.n_winning_trades = int(n_trades * stats.hit_rate)
        stats.n_losing_trades = n_trades - stats.n_winning_trades

    print(f"\n{format_execution_stats(stats, title=f'Execution Statistics (from {source})')}")


def print_sample_trades(result: BacktestResult, max_trades: int = 5) -> None:
    """Druckt Sample-Trades."""
    if result.trades is None or result.trades.empty:
        print("\n[Sample-Trades]")
        print("  (keine Trades generiert)")
        return

    print(
        f"\n[Sample-Trades] (erste {min(max_trades, len(result.trades))} von {len(result.trades)})"
    )
    print("-" * 70)

    for i, (_, trade) in enumerate(result.trades.head(max_trades).iterrows(), 1):
        entry_time = trade.get("entry_time", "?")
        entry_price = trade.get("entry_price", 0)
        exit_time = trade.get("exit_time", "?")
        exit_price = trade.get("exit_price", 0)
        pnl = trade.get("pnl", 0)
        reason = trade.get("exit_reason", "?")

        if hasattr(entry_time, "strftime"):
            entry_str = entry_time.strftime("%Y-%m-%d %H:%M")
        else:
            entry_str = str(entry_time)

        if hasattr(exit_time, "strftime"):
            exit_str = exit_time.strftime("%Y-%m-%d %H:%M")
        else:
            exit_str = str(exit_time)

        print(
            f"  {i}. Entry: {entry_str} @ {entry_price:,.2f} | "
            f"Exit: {exit_str} @ {exit_price:,.2f} | "
            f"PnL: {pnl:+,.2f} ({reason})"
        )


def print_comparison(
    ep_result: BacktestResult,
    legacy_result: BacktestResult,
) -> None:
    """Druckt Vergleich zwischen ExecutionPipeline und Legacy."""
    print("\n" + "=" * 70)
    print("VERGLEICH: ExecutionPipeline vs. Legacy")
    print("=" * 70)

    ep = ep_result.stats
    lg = legacy_result.stats

    print("\n                        ExecutionPipeline     Legacy")
    print("-" * 60)
    print(
        f"  Total Return:         {ep.get('total_return', 0):+12.2%}    {lg.get('total_return', 0):+12.2%}"
    )
    print(
        f"  Max Drawdown:         {ep.get('max_drawdown', 0):12.2%}    {lg.get('max_drawdown', 0):12.2%}"
    )
    print(f"  Sharpe Ratio:         {ep.get('sharpe', 0):12.2f}    {lg.get('sharpe', 0):12.2f}")
    print(
        f"  Total Trades:         {ep.get('total_trades', 0):12d}    {lg.get('total_trades', 0):12d}"
    )
    print(f"  Win Rate:             {ep.get('win_rate', 0):12.1%}    {lg.get('win_rate', 0):12.1%}")

    if "total_orders" in ep:
        print(f"\n  [nur ExecutionPipeline]")
        print(f"  Total Orders:         {ep.get('total_orders', 0):12d}")
        print(f"  Filled Orders:        {ep.get('filled_orders', 0):12d}")
        print(f"  Total Fees:           {ep.get('total_fees', 0):12.2f} EUR")


# =============================================================================
# Plot Functions (Phase 16D)
# =============================================================================


def _save_execution_plots(
    engine: BacktestEngine,
    result: BacktestResult,
    output_dir: str,
    symbol: str,
) -> None:
    """
    Speichert Execution-Plots (Phase 16D).

    Args:
        engine: BacktestEngine mit execution_results
        result: BacktestResult mit equity_curve
        output_dir: Output-Verzeichnis
        symbol: Symbol fuer Dateinamen
    """
    try:
        from src.reporting.execution_plots import (
            check_matplotlib,
            plot_slippage_histogram,
            plot_fee_histogram,
            plot_notional_histogram,
            plot_equity_with_trades,
            plot_execution_summary,
            extract_slippages_from_results,
            extract_fees_from_results,
            extract_notionals_from_results,
        )
    except ImportError as e:
        print(f"\n[Plot] Konnte Plot-Module nicht laden: {e}")
        return

    if not check_matplotlib():
        print("\n[Plot] Matplotlib nicht verfuegbar - ueberspringe Plots")
        return

    # Output-Verzeichnis erstellen
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Symbol fuer Dateinamen bereinigen
    safe_symbol = symbol.replace("/", "_")

    print(f"\n[Plot] Erstelle Plots in '{output_dir}'...")

    plots_created = 0

    # Slippage-Histogram
    if hasattr(engine, "execution_results") and engine.execution_results:
        slippages = extract_slippages_from_results(engine.execution_results)
        if slippages:
            plot_slippage_histogram(
                slippages,
                title=f"Slippage Distribution - {symbol}",
                output_path=output_path / f"{safe_symbol}_slippage_hist.png",
            )
            plots_created += 1

        # Fee-Histogram
        fees = extract_fees_from_results(engine.execution_results)
        if fees:
            plot_fee_histogram(
                fees,
                title=f"Fee Distribution - {symbol}",
                output_path=output_path / f"{safe_symbol}_fee_hist.png",
            )
            plots_created += 1

        # Notional-Histogram
        notionals = extract_notionals_from_results(engine.execution_results)
        if notionals:
            plot_notional_histogram(
                notionals,
                title=f"Trade Size Distribution - {symbol}",
                output_path=output_path / f"{safe_symbol}_notional_hist.png",
            )
            plots_created += 1

        # ExecutionStats Summary
        stats = from_execution_results(engine.execution_results)
        plot_execution_summary(
            stats,
            title=f"Execution Summary - {symbol}",
            output_path=output_path / f"{safe_symbol}_execution_summary.png",
        )
        plots_created += 1

    # Equity mit Trades
    if result.equity_curve is not None and len(result.equity_curve) > 0:
        plot_equity_with_trades(
            result.equity_curve,
            trades_df=result.trades,
            title=f"Equity Curve with Trades - {symbol}",
            output_path=output_path / f"{safe_symbol}_equity_trades.png",
        )
        plots_created += 1

    print(f"[Plot] {plots_created} Plots erstellt in '{output_dir}'")


# =============================================================================
# Main Functions
# =============================================================================


def run_backtest(
    df: pd.DataFrame,
    strategy_fn: Callable,
    strategy_params: Dict[str, Any],
    symbol: str,
    fee_bps: float,
    slippage_bps: float,
    use_execution_pipeline: bool = True,
    log_executions: bool = True,
) -> tuple[BacktestResult, BacktestEngine]:
    """
    Fuehrt einen Backtest durch.

    Args:
        df: OHLCV-Daten
        strategy_fn: Signal-Funktion
        strategy_params: Strategie-Parameter
        symbol: Trading-Symbol
        fee_bps: Fees in Basispunkten
        slippage_bps: Slippage in Basispunkten
        use_execution_pipeline: ExecutionPipeline verwenden
        log_executions: Execution-Logging aktivieren

    Returns:
        Tuple aus (BacktestResult, BacktestEngine)
    """
    engine = BacktestEngine(
        use_execution_pipeline=use_execution_pipeline,
        log_executions=log_executions,
    )

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_fn,
        strategy_params=strategy_params,
        symbol=symbol,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
    )

    return result, engine


def main(argv: Optional[List[str]] = None) -> Optional[BacktestResult]:
    """
    Main-Funktion des Demo-Scripts.

    Args:
        argv: CLI-Argumente (optional, fuer Tests)

    Returns:
        BacktestResult (fuer Tests) oder None
    """
    args = parse_args(argv)

    # Strategie laden
    try:
        strategy_fn = get_strategy_fn(args.strategy)
    except ValueError as e:
        print(f"\nFehler: {e}")
        return None

    strategy_params = get_default_strategy_params(args.strategy)

    # Daten generieren
    df = generate_sample_data(
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        bars=args.bars,
        timeframe=args.timeframe,
    )

    # Zeitraum-Strings fuer Output
    start_str = df.index[0].strftime("%Y-%m-%d")
    end_str = df.index[-1].strftime("%Y-%m-%d")

    # Modus bestimmen
    use_execution_pipeline = not args.use_legacy
    log_executions = not args.no_log_executions
    mode = "execution_pipeline_backtest" if use_execution_pipeline else "realistic_legacy"

    # Header ausgeben
    print_header(
        symbol=args.symbol,
        mode=mode,
        start=start_str,
        end=end_str,
        strategy=args.strategy,
        params=strategy_params,
    )

    print(f"\nDaten: {len(df)} Bars ({args.timeframe})")
    print(f"Preis-Range: {df['close'].min():,.2f} - {df['close'].max():,.2f}")
    print(f"Fees: {args.fee_bps} bps ({args.fee_bps / 100:.2f}%)")
    print(f"Slippage: {args.slippage_bps} bps ({args.slippage_bps / 100:.2f}%)")

    print("\n" + "-" * 70)
    print("BACKTEST wird ausgefuehrt...")
    print("-" * 70)

    # Backtest ausfuehren
    result, engine = run_backtest(
        df=df,
        strategy_fn=strategy_fn,
        strategy_params=strategy_params,
        symbol=args.symbol,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        use_execution_pipeline=use_execution_pipeline,
        log_executions=log_executions,
    )

    # Ergebnisse ausgeben
    print_core_stats(result)
    print_trade_stats(result)

    if use_execution_pipeline:
        print_execution_stats(result)
        if log_executions:
            print_execution_logs(engine, max_entries=2)

    # Detaillierte ExecutionStats (Phase 16D)
    if args.stats and use_execution_pipeline:
        print_detailed_execution_stats(engine, result)

    if args.verbose:
        print_sample_trades(result, max_trades=5)

    # Vergleichsmodus
    if args.compare:
        print("\nFuehre Legacy-Backtest fuer Vergleich durch...")
        legacy_result, _ = run_backtest(
            df=df,
            strategy_fn=strategy_fn,
            strategy_params=strategy_params,
            symbol=args.symbol,
            fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps,
            use_execution_pipeline=False,
            log_executions=False,
        )
        print_comparison(result, legacy_result)

    # Plots erstellen (Phase 16D)
    if args.plot and use_execution_pipeline:
        _save_execution_plots(engine, result, args.output_dir, args.symbol)

    # Footer
    print("\n" + "=" * 70)
    print("Demo abgeschlossen!")
    print("=" * 70)
    print("\nWICHTIG: Es wurden KEINE echten Orders gesendet (Paper/Sandbox)")
    print()

    return result


if __name__ == "__main__":
    main()
