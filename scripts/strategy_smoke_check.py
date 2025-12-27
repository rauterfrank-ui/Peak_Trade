#!/usr/bin/env python3
"""
Peak_Trade – Strategy Smoke-Check CLI (Phase 76)
=================================================

CLI-Tool fuer automatisierte Smoke-Tests der Strategy-Library v1.1.

Prueft alle offiziellen v1.1-Strategien in Mini-Backtests und gibt
strukturierte Ergebnisse mit Kennzahlen aus.

WICHTIG: Rein Research/Backtest - KEIN Live-Trading!

Usage:
    # Alle v1.1-Strategien testen
    python scripts/strategy_smoke_check.py

    # Bestimmte Strategien testen
    python scripts/strategy_smoke_check.py --strategies ma_crossover,rsi_reversion

    # Mit laengerem Lookback (mehr Daten)
    python scripts/strategy_smoke_check.py --lookback-days 60

    # JSON-Output fuer Weiterverarbeitung
    python scripts/strategy_smoke_check.py --output-json test_results/smoke.json

    # Verbose-Modus mit mehr Details
    python scripts/strategy_smoke_check.py -v

Examples:
    # Schneller Check aller Strategien
    python scripts/strategy_smoke_check.py

    # Nur Trend-Strategien
    python scripts/strategy_smoke_check.py --strategies ma_crossover,trend_following,macd

    # Mit Custom-Config
    python scripts/strategy_smoke_check.py --config config/config.test.toml

Exit Codes:
    0 = Alle Strategien OK
    1 = Mindestens eine Strategie FAIL
    2 = Fehler beim Ausfuehren des Tools
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Pfad hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies.diagnostics import (
    StrategySmokeResult,
    get_v11_official_strategies,
    run_strategy_smoke_tests,
    summarize_smoke_results,
    format_smoke_result_line,
)


def parse_args() -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Strategy Smoke-Check fuer Peak_Trade v1.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )

    parser.add_argument(
        "--strategies",
        type=str,
        default=None,
        help="Kommagetrennte Liste von Strategien (default: alle v1.1-offiziellen)",
    )

    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe fuer synthetische Daten (default: 1h, nur informativ)",
    )

    parser.add_argument(
        "--market",
        type=str,
        default="BTCUSDT",
        help="Markt-Symbol (default: BTCUSDT, nur informativ)",
    )

    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Anzahl Tage fuer Backtest-Daten (default: 30)",
    )

    parser.add_argument(
        "--n-bars",
        type=int,
        default=None,
        help="Explizite Anzahl Bars (ueberschreibt --lookback-days)",
    )

    parser.add_argument(
        "--data-source",
        type=str,
        choices=["synthetic", "kraken_cache"],
        default="synthetic",
        help="Datenquelle: 'synthetic' (Default) oder 'kraken_cache' (lokaler Cache)",
    )

    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Pfad fuer JSON-Output (optional)",
    )

    parser.add_argument(
        "--output-md",
        type=str,
        default=None,
        help="Pfad fuer Markdown-Report (optional)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose-Modus mit mehr Details",
    )

    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Zeigt nur die v1.1-Strategien an, fuehrt keine Tests aus",
    )

    # Phase 79: Data-QC Modus
    parser.add_argument(
        "--check-data-only",
        action="store_true",
        help="Nur Data-QC ausfuehren ohne Strategie-Tests (nur bei kraken_cache)",
    )

    parser.add_argument(
        "--min-bars",
        type=int,
        default=None,
        help="Minimum benoetigte Bars fuer Data-QC (Default: aus Config oder 500)",
    )

    return parser.parse_args()


def print_header():
    """Gibt Header aus."""
    print("=" * 80)
    print("Peak_Trade – Strategy Smoke-Check (Phase 76)")
    print("=" * 80)
    print()
    print("HINWEIS: Rein Research/Backtest – KEIN Live-Trading!")
    print()


def print_results(results: List[StrategySmokeResult], verbose: bool = False):
    """Gibt Ergebnisse formatiert aus."""
    print("-" * 80)
    print("ERGEBNISSE")
    print("-" * 80)
    print()

    for result in results:
        print(format_smoke_result_line(result))

        # Verbose: Mehr Details
        if verbose and result.status == "ok" and result.metadata:
            meta = result.metadata
            if meta.get("category"):
                print(f"         Category: {meta['category']}")
            if meta.get("win_rate") is not None:
                print(f"         Win-Rate: {meta['win_rate']:.2%}")
            if meta.get("profit_factor") is not None:
                print(f"         Profit-Factor: {meta['profit_factor']:.2f}")
            print()

        if verbose and result.status == "fail" and result.metadata:
            tb = result.metadata.get("traceback", "")
            if tb:
                print(f"         Traceback (last 200 chars):")
                for line in tb[-200:].split("\n"):
                    print(f"           {line}")
                print()


def print_summary(summary: dict):
    """Gibt Summary aus."""
    print()
    print("-" * 80)
    print("ZUSAMMENFASSUNG")
    print("-" * 80)
    print()
    print(f"  Gesamt:    {summary['total']}")
    print(f"  OK:        {summary['ok']}")
    print(f"  FAIL:      {summary['fail']}")
    print(f"  Dauer:     {summary['total_duration_ms']:.0f} ms")
    print()

    if summary["fail"] > 0:
        print(f"  Fehlgeschlagene Strategien: {', '.join(summary['failed_strategies'])}")
        print()

    if summary["all_passed"]:
        print("  ✓ Alle Strategien haben den Smoke-Test bestanden!")
    else:
        print("  ✗ Mindestens eine Strategie ist fehlgeschlagen!")

    print()


def save_json_report(
    results: List[StrategySmokeResult],
    summary: dict,
    output_path: str,
    data_source: str = "synthetic",
    market: str = "BTC/EUR",
    timeframe: str = "1h",
):
    """Speichert JSON-Report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "data_source": data_source,
        "market": market,
        "timeframe": timeframe,
        "summary": summary,
        "results": [
            {
                "name": r.name,
                "status": r.status,
                "data_source": r.data_source,
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "num_bars": r.num_bars,
                "start_ts": str(r.start_ts) if r.start_ts else None,
                "end_ts": str(r.end_ts) if r.end_ts else None,
                "return_pct": r.return_pct,
                "sharpe": r.sharpe,
                "max_drawdown_pct": r.max_drawdown_pct,
                "num_trades": r.num_trades,
                "error": r.error,
                "duration_ms": r.duration_ms,
                "metadata": r.metadata,
                # Phase 79: Data-Health-Felder
                "data_health": r.data_health,
                "data_notes": r.data_notes,
            }
            for r in results
        ],
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"JSON-Report gespeichert: {path}")


def save_md_report(
    results: List[StrategySmokeResult],
    summary: dict,
    output_path: str,
    data_source: str = "synthetic",
    market: str = "BTC/EUR",
    timeframe: str = "1h",
):
    """Speichert Markdown-Report."""
    # Datenbereich aus ersten OK-Result ermitteln
    ok_results = [r for r in results if r.status == "ok"]
    num_bars = ok_results[0].num_bars if ok_results and ok_results[0].num_bars else "N/A"
    start_ts = ok_results[0].start_ts if ok_results and ok_results[0].start_ts else None
    end_ts = ok_results[0].end_ts if ok_results and ok_results[0].end_ts else None

    # Phase 79: Data-Health aus erstem Result extrahieren
    first_result = results[0] if results else None
    data_health = first_result.data_health if first_result else None
    data_notes = first_result.data_notes if first_result else None

    lines = [
        "# Strategy Smoke-Check Report",
        "",
        f"**Generiert:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Daten-Setup",
        "",
        f"- **Datenquelle:** {data_source}",
        f"- **Market:** {market}",
        f"- **Timeframe:** {timeframe}",
        f"- **Bars:** {num_bars}",
    ]

    if start_ts and end_ts:
        lines.append(f"- **Zeitraum:** {start_ts} bis {end_ts}")

    # Phase 79: Data-Health-Block
    if data_health:
        lines.append(f"- **Data-Health:** {data_health}")
    if data_notes:
        lines.append(f"- **Data-Notes:** {data_notes}")

    lines.extend(
        [
            "",
            "## Zusammenfassung",
            "",
            f"- **Gesamt:** {summary['total']}",
            f"- **OK:** {summary['ok']}",
            f"- **FAIL:** {summary['fail']}",
            f"- **Dauer:** {summary['total_duration_ms']:.0f} ms",
            "",
        ]
    )

    if summary["fail"] > 0:
        lines.append(f"**Fehlgeschlagen:** {', '.join(summary['failed_strategies'])}")
        lines.append("")

    lines.append("## Ergebnisse")
    lines.append("")
    lines.append("| Strategy | Status | Return | Sharpe | MaxDD | Trades | Data-Health |")
    lines.append("|----------|--------|--------|--------|-------|--------|-------------|")

    for r in results:
        health_str = r.data_health if r.data_health else "-"
        if r.status == "ok":
            ret = f"{r.return_pct:+.2f}%" if r.return_pct is not None else "N/A"
            sharpe = f"{r.sharpe:.2f}" if r.sharpe is not None else "N/A"
            dd = f"{r.max_drawdown_pct:.2f}%" if r.max_drawdown_pct is not None else "N/A"
            trades = str(r.num_trades) if r.num_trades is not None else "N/A"
            lines.append(f"| {r.name} | OK | {ret} | {sharpe} | {dd} | {trades} | {health_str} |")
        else:
            error_short = r.error[:30] + "..." if r.error and len(r.error) > 30 else r.error
            lines.append(f"| {r.name} | FAIL | - | - | - | {error_short} | {health_str} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generiert von `scripts/strategy_smoke_check.py` (Phase 76/79)*")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write("\n".join(lines))

    print(f"Markdown-Report gespeichert: {path}")


def run_data_qc_only(args) -> int:
    """
    Phase 79: Nur Data-QC ausfuehren ohne Strategie-Tests.

    Args:
        args: CLI-Argumente

    Returns:
        Exit-Code (0=OK, 1=QC-Problem, 2=Fehler)
    """
    from pathlib import Path

    print("-" * 80)
    print("DATA-QC ONLY MODE (Phase 79)")
    print("-" * 80)
    print()

    if args.data_source != "kraken_cache":
        print("WARNUNG: --check-data-only ist nur sinnvoll mit --data-source kraken_cache")
        print("         Bei synthetic Daten gibt es keine sinnvolle QC.")
        return 0

    # Lade QC-Funktionen
    try:
        from src.data.kraken_cache_loader import (
            check_data_health_only,
            get_real_market_smokes_config,
            list_available_cache_files,
        )
    except ImportError as e:
        print(f"Fehler beim Import: {e}")
        return 2

    # Config laden
    rms_cfg = get_real_market_smokes_config(args.config)
    base_path = Path(rms_cfg["base_path"])

    # Falls test_base_path existiert und base_path nicht, verwende test_base_path
    test_base_path = Path(rms_cfg.get("test_base_path", "tests/data/kraken_smoke"))
    if test_base_path.exists() and not base_path.exists():
        base_path = test_base_path
        print(f"INFO: Verwende test_base_path: {base_path}")

    min_bars = args.min_bars if args.min_bars else rms_cfg.get("min_bars", 500)

    print(f"Config: {args.config}")
    print(f"Base-Path: {base_path}")
    print(f"Market: {args.market}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Min-Bars: {min_bars}")
    print()

    # Verfuegbare Cache-Dateien anzeigen
    print("Verfuegbare Cache-Dateien:")
    available = list_available_cache_files(base_path)
    if available:
        for name, info in available.items():
            print(f"  - {name}: {info['size_kb']:.1f} KB, modified: {info['modified']}")
    else:
        print("  (keine)")
    print()

    # Data-QC ausfuehren
    print(f"Data-QC fuer {args.market} / {args.timeframe}...")
    health = check_data_health_only(
        base_path=base_path,
        market=args.market,
        timeframe=args.timeframe,
        min_bars=min_bars,
    )

    print()
    print("-" * 80)
    print("DATA-QC ERGEBNIS")
    print("-" * 80)
    print()
    print(f"  Status:      {health.status}")
    print(f"  Num-Bars:    {health.num_bars}")
    print(f"  Start-TS:    {health.start_ts}")
    print(f"  End-TS:      {health.end_ts}")
    print(
        f"  Lookback:    {health.lookback_days_actual:.1f} Tage"
        if health.lookback_days_actual
        else "  Lookback:    N/A"
    )
    print(f"  File-Path:   {health.file_path}")
    if health.notes:
        print(f"  Notes:       {health.notes}")
    print()

    if health.is_ok:
        print("Data-QC: OK")
        return 0
    else:
        print(f"Data-QC: PROBLEM ({health.status})")
        return 1


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    print_header()

    # Phase 79: Data-QC-Only Modus
    if args.check_data_only:
        return run_data_qc_only(args)

    # List-Modus: Nur Strategien anzeigen
    if args.list_strategies:
        print("v1.1-offizielle Strategien:")
        print()
        try:
            strategies = get_v11_official_strategies(args.config)
            for s in strategies:
                print(f"  - {s}")
            print()
            print(f"Gesamt: {len(strategies)} Strategien")
        except Exception as e:
            print(f"Fehler beim Laden der Strategien: {e}")
            return 2
        return 0

    # Strategien parsen
    strategy_names = None
    if args.strategies:
        strategy_names = [s.strip() for s in args.strategies.split(",")]
        print(f"Teste Strategien: {', '.join(strategy_names)}")
    else:
        try:
            strategy_names = get_v11_official_strategies(args.config)
            print(f"Teste alle v1.1-offiziellen Strategien ({len(strategy_names)})")
        except Exception as e:
            print(f"Warnung: Konnte v1.1-Strategien nicht aus Config laden: {e}")
            print("Verwende Fallback-Liste")

    print(f"Config: {args.config}")
    print(f"Data-Source: {args.data_source}")
    print(f"Market: {args.market}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Lookback: {args.lookback_days} Tage")
    if args.n_bars:
        print(f"Explizite Bars: {args.n_bars}")
    if args.min_bars:
        print(f"Min-Bars (QC): {args.min_bars}")
    print()

    # Smoke-Tests ausfuehren
    print("Fuehre Smoke-Tests aus...")
    print()

    # min_bars fuer QC
    min_bars = args.min_bars if args.min_bars else 200

    try:
        results = run_strategy_smoke_tests(
            strategy_names=strategy_names,
            config_path=args.config,
            market=args.market,
            timeframe=args.timeframe,
            lookback_days=args.lookback_days,
            n_bars=args.n_bars,
            data_source=args.data_source,
            min_bars=min_bars,
        )
    except Exception as e:
        print(f"Fehler beim Ausfuehren der Smoke-Tests: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 2

    # Ergebnisse ausgeben
    print_results(results, verbose=args.verbose)

    # Summary
    summary = summarize_smoke_results(results)
    print_summary(summary)

    # Optional: JSON-Output
    if args.output_json:
        save_json_report(
            results,
            summary,
            args.output_json,
            data_source=args.data_source,
            market=args.market,
            timeframe=args.timeframe,
        )

    # Optional: Markdown-Output
    if args.output_md:
        save_md_report(
            results,
            summary,
            args.output_md,
            data_source=args.data_source,
            market=args.market,
            timeframe=args.timeframe,
        )

    # Exit-Code
    if summary["all_passed"]:
        print("Exit-Code: 0 (alle OK)")
        return 0
    else:
        print(f"Exit-Code: 1 ({summary['fail']} FAIL)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
