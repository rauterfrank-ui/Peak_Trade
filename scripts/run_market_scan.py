#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/run_market_scan.py
"""
Peak_Trade: Market Scanner
==========================

Scannt mehrere Symbole/Timeframes mit einer Strategie und loggt Ergebnisse.

Zwei Modi:
- forward: Generiert Forward-Signals mit Exchange-Daten (aktuelles Signal)
- backtest-lite: Führt schnelle Backtests mit Dummy/CSV-Daten durch

Alle Ergebnisse werden als run_type="market_scan" in der Registry geloggt.

Usage:
    # Forward-Mode (mit Exchange)
    python scripts/run_market_scan.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR --mode forward

    # Backtest-Lite-Mode (mit Dummy-Daten)
    python scripts/run_market_scan.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR --mode backtest-lite

    # Mit spezifischen Optionen
    python scripts/run_market_scan.py --strategy rsi_reversion --symbols BTC/EUR,ETH/EUR,LTC/EUR \\
        --timeframe 4h --bars 300 --mode forward --tag morning-scan

    # Mit Symbol-Limit
    python scripts/run_market_scan.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR,LTC/EUR \\
        --max-symbols 2 --mode backtest-lite
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Projekt-Root zum Python-Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import PeakConfig, load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import log_market_scan_result, RUN_TYPE_MARKET_SCAN
from src.backtest.engine import BacktestEngine
from src.strategies.registry import create_strategy_from_config, get_available_strategy_keys


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Market Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Forward-Mode
    python scripts/run_market_scan.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR --mode forward

    # Backtest-Lite-Mode
    python scripts/run_market_scan.py --strategy rsi_reversion --symbols BTC/EUR,ETH/EUR,LTC/EUR \\
        --mode backtest-lite --bars 500 --tag weekly-scan

    # Mit Tag und Scan-Name
    python scripts/run_market_scan.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR \\
        --mode forward --tag daily --scan-name morning_scan
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml)",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="Strategie-Key aus der Registry (z.B. ma_crossover, rsi_reversion)",
    )

    parser.add_argument(
        "--symbols",
        type=str,
        required=True,
        help="Komma-separierte Liste von Symbolen (z.B. BTC/EUR,ETH/EUR,LTC/EUR)",
    )

    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe für OHLCV-Daten (Default: 1h)",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Anzahl Bars pro Symbol (Default: 200)",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["forward", "backtest-lite"],
        default="forward",
        help="Scan-Modus: 'forward' (Exchange-Daten) oder 'backtest-lite' (Dummy-Daten)",
    )

    parser.add_argument(
        "--max-symbols",
        type=int,
        default=None,
        help="Maximale Anzahl der zu scannenden Symbole (optional)",
    )

    parser.add_argument(
        "--scan-name",
        type=str,
        default=None,
        help="Name für den Scan (optional, für Gruppierung)",
    )

    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optionaler Tag für Registry-Logging",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Symbole anzeigen, keine Scans ausführen",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )

    return parser.parse_args(argv)


def generate_dummy_ohlcv_for_symbol(
    symbol: str,
    n_bars: int = 200,
    base_price: float = 50000.0,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """
    Generiert synthetische OHLCV-Daten für ein Symbol.
    Verwendet Symbol-Hash für unterschiedliche aber reproduzierbare Daten.
    """
    # Symbol-abhängiger Seed für unterschiedliche Daten pro Symbol
    seed = hash(symbol) % 2**32
    np.random.seed(seed)

    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    returns = np.random.normal(0, volatility, n_bars)
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend
    close_prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)

    high_bump = np.random.uniform(0, 0.005, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)

    low_dip = np.random.uniform(0, 0.005, n_bars)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)

    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def scan_symbol_forward(
    symbol: str,
    strategy_key: str,
    timeframe: str,
    bars: int,
    cfg: PeakConfig,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Scannt ein Symbol im Forward-Mode (Exchange-Daten).

    Returns:
        Dict mit signal, price, timestamp
    """
    from src.exchange import build_exchange_client_from_config

    # Exchange-Client
    try:
        ex_client = build_exchange_client_from_config(cfg)
    except Exception as e:
        return {"error": f"Exchange-Client-Fehler: {e}"}

    # OHLCV-Daten holen
    try:
        df = ex_client.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=bars,
        )
        if df.empty:
            return {"error": f"Keine Daten für {symbol}"}
    except Exception as e:
        return {"error": f"OHLCV-Fehler: {e}"}

    # Strategie
    try:
        strategy = create_strategy_from_config(strategy_key, cfg)
        signals = strategy.generate_signals(df)

        if signals is None or signals.empty:
            return {"error": "Keine Signale generiert"}

        last_signal = float(signals.iloc[-1])
        last_price = float(df["close"].iloc[-1])
        last_ts = signals.index[-1]

        return {
            "signal": last_signal,
            "price": last_price,
            "timestamp": last_ts.isoformat() if hasattr(last_ts, "isoformat") else str(last_ts),
            "bars_fetched": len(df),
        }
    except Exception as e:
        return {"error": f"Signal-Fehler: {e}"}


def scan_symbol_backtest_lite(
    symbol: str,
    strategy_key: str,
    timeframe: str,
    bars: int,
    cfg: PeakConfig,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Scannt ein Symbol im Backtest-Lite-Mode (Dummy-Daten, schneller Backtest).

    Returns:
        Dict mit stats (total_return, sharpe, max_drawdown, etc.)
    """
    # Dummy-Daten für dieses Symbol
    df = generate_dummy_ohlcv_for_symbol(symbol, n_bars=bars)

    # Position-Sizer und Risk-Manager
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    # Strategie
    try:
        strategy = create_strategy_from_config(strategy_key, cfg)
    except Exception as e:
        return {"error": f"Strategie-Fehler: {e}"}

    # Backtest
    try:
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        def strategy_signal_fn(data, _params):
            return strategy.generate_signals(data)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params={},
        )

        stats = result.stats or {}

        # Signal aus letztem Zeitpunkt extrahieren
        signals = strategy.generate_signals(df)
        last_signal = float(signals.iloc[-1]) if signals is not None and not signals.empty else 0.0

        return {
            "stats": stats,
            "signal": last_signal,
            "bars_fetched": len(df),
        }
    except Exception as e:
        return {"error": f"Backtest-Fehler: {e}"}


def format_signal(signal: float) -> str:
    """Formatiert Signal als lesbare Richtung."""
    if signal > 0:
        return f"+{signal:.0f} (LONG)"
    elif signal < 0:
        return f"{signal:.0f} (SHORT)"
    return "0 (FLAT)"


def print_scan_results(
    results: List[Dict[str, Any]],
    mode: str,
) -> None:
    """Gibt eine Zusammenfassungstabelle der Scan-Ergebnisse aus."""
    if not results:
        print("\nKeine Ergebnisse.")
        return

    print(f"\n{'=' * 80}")
    print(f"SCAN ERGEBNISSE ({mode.upper()})")
    print(f"{'=' * 80}")

    if mode == "forward":
        header = f"{'Symbol':<12} {'Signal':>10} {'Preis':>12} | Status"
        print(header)
        print("-" * 60)

        # Nach Signal sortieren (stärkste zuerst)
        sorted_results = sorted(
            results,
            key=lambda x: abs(x.get("signal", 0)) if "signal" in x else -1,
            reverse=True,
        )

        for res in sorted_results:
            symbol = res.get("symbol", "?")
            if "error" in res:
                print(f"{symbol:<12} {'ERROR':>10} {'-':>12} | {res['error'][:30]}")
            else:
                signal = res.get("signal", 0)
                price = res.get("price", 0)
                print(f"{symbol:<12} {format_signal(signal):>10} {price:>12.2f} | OK")

    else:  # backtest-lite
        header = f"{'Symbol':<12} {'Return':>10} {'Sharpe':>8} {'MaxDD':>10} {'Signal':>10}"
        print(header)
        print("-" * 60)

        # Nach Sharpe sortieren
        sorted_results = sorted(
            results,
            key=lambda x: x.get("stats", {}).get("sharpe", -999) if "stats" in x else -999,
            reverse=True,
        )

        for res in sorted_results:
            symbol = res.get("symbol", "?")
            if "error" in res:
                print(f"{symbol:<12} {'ERROR':>10} {'-':>8} {'-':>10} {'-':>10}")
            else:
                stats = res.get("stats", {})
                signal = res.get("signal", 0)
                total_ret = stats.get("total_return", 0)
                sharpe = stats.get("sharpe", 0)
                max_dd = stats.get("max_drawdown", 0)
                print(
                    f"{symbol:<12} {total_ret:>10.2%} {sharpe:>8.2f} {max_dd:>10.2%} {format_signal(signal):>10}"
                )


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point für Market Scanner."""
    args = parse_args(argv)

    print("\n" + "=" * 70)
    print("Peak_Trade: Market Scanner")
    print("=" * 70)

    # 1) Config laden
    print(f"\n[1/4] Lade Config: {args.config}")
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"  FEHLER: Config nicht gefunden: {config_path}")
        return 1

    try:
        cfg = load_config(config_path)
    except Exception as e:
        print(f"  FEHLER: {e}")
        return 1

    # 2) Strategie validieren
    print(f"\n[2/4] Validiere Strategie: {args.strategy}")
    available = get_available_strategy_keys()
    if args.strategy not in available:
        print(f"  FEHLER: Unbekannter Strategy-Key '{args.strategy}'")
        print(f"  Verfügbar: {', '.join(available)}")
        return 1

    # 3) Symbole parsen
    print(f"\n[3/4] Parse Symbole...")
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        print("  FEHLER: Keine gültigen Symbole angegeben")
        return 1

    if args.max_symbols and len(symbols) > args.max_symbols:
        print(f"  Limitiert auf {args.max_symbols} Symbole")
        symbols = symbols[: args.max_symbols]

    print(f"  Symbole: {symbols}")

    # Dry-Run
    if args.dry_run:
        print("\n[DRY-RUN] Folgende Symbole würden gescannt:")
        for i, sym in enumerate(symbols, 1):
            print(f"  {i:>3}. {sym}")
        print(f"\nModus: {args.mode}")
        print("(Kein Scan ausgeführt)")
        return 0

    # 4) Scans ausführen
    print(f"\n[4/4] Scanne {len(symbols)} Symbole im Modus '{args.mode}'...")

    results = []
    scan_name = args.scan_name or f"{args.strategy}_scan"

    for i, symbol in enumerate(symbols, 1):
        if args.verbose:
            print(f"  [{i}/{len(symbols)}] {symbol}")
        else:
            pct = i / len(symbols) * 100
            print(f"\r  Fortschritt: {i}/{len(symbols)} ({pct:.0f}%)", end="", flush=True)

        # Scan je nach Modus
        if args.mode == "forward":
            result = scan_symbol_forward(
                symbol=symbol,
                strategy_key=args.strategy,
                timeframe=args.timeframe,
                bars=args.bars,
                cfg=cfg,
                verbose=args.verbose,
            )
        else:  # backtest-lite
            result = scan_symbol_backtest_lite(
                symbol=symbol,
                strategy_key=args.strategy,
                timeframe=args.timeframe,
                bars=args.bars,
                cfg=cfg,
                verbose=args.verbose,
            )

        result["symbol"] = symbol

        # In Registry loggen
        if "error" not in result:
            run_id = log_market_scan_result(
                strategy_key=args.strategy,
                symbol=symbol,
                timeframe=args.timeframe,
                mode=args.mode,
                signal=result.get("signal"),
                stats=result.get("stats"),
                scan_name=scan_name,
                tag=args.tag,
                config_path=str(config_path),
                bars_fetched=result.get("bars_fetched"),
            )
            result["run_id"] = run_id

        results.append(result)

    print()  # Newline nach Fortschrittsanzeige

    # Zusammenfassung
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    print(f"\n{'=' * 70}")
    print("SCAN ABGESCHLOSSEN")
    print(f"{'=' * 70}")
    print(f"  Strategie:   {args.strategy}")
    print(f"  Modus:       {args.mode}")
    print(f"  Timeframe:   {args.timeframe}")
    print(f"  Bars:        {args.bars}")
    print(f"  Scan-Name:   {scan_name}")
    print(f"  Erfolgreich: {len(successful)}/{len(symbols)}")
    if failed:
        print(f"  Fehlgeschlagen: {len(failed)}")

    # Ergebnistabelle
    print_scan_results(results, args.mode)

    if args.tag:
        print(f"\nTag: {args.tag}")

    print("\nNächste Schritte:")
    print(f"  python scripts/list_experiments.py --run-type market_scan")
    print(f"  python scripts/analyze_experiments.py --mode top-runs --run-type market_scan")

    return 0


if __name__ == "__main__":
    sys.exit(main())
