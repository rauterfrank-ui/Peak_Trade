#!/usr/bin/env python3
"""
Peak_Trade Walk-Forward Backtest Runner
=========================================

Führt Walk-Forward-Analysen für Top-N-Konfigurationen aus Sweeps durch.

Verwendung:
    # Walk-Forward für Top-3 aus Sweep
    python scripts/run_walkforward_backtest.py \
        --sweep-name rsi_reversion_basic \
        --top-n 3 \
        --train-window 180d \
        --test-window 30d

    # Mit spezifischem Zeitraum
    python scripts/run_walkforward_backtest.py \
        --sweep-name ma_crossover_basic \
        --top-n 5 \
        --train-window 90d \
        --test-window 15d \
        --start-date 2024-01-01 \
        --end-date 2024-12-31

    # Mit Dummy-Daten (für Tests)
    python scripts/run_walkforward_backtest.py \
        --sweep-name rsi_reversion_basic \
        --top-n 3 \
        --train-window 180d \
        --test-window 30d \
        --use-dummy-data \
        --dummy-bars 1000

Output:
    - reports/walkforward/{sweep_name}/{config_id}_walkforward_YYYYMMDD.md
    - reports/walkforward/{sweep_name}/comparison_YYYYMMDD.md (Multi-Config)
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
import numpy as np

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtest.walkforward import (
    WalkForwardConfig,
    run_walkforward_for_top_n_from_sweep,
)
from src.reporting.walkforward_report import (
    build_walkforward_report,
    build_multi_config_report,
    save_walkforward_report,
)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def create_dummy_data(n_bars: int = 1000) -> pd.DataFrame:
    """
    Erstellt Dummy-OHLCV-Daten für Tests.

    Args:
        n_bars: Anzahl der Bars

    Returns:
        DataFrame mit OHLCV-Daten und DatetimeIndex
    """
    np.random.seed(42)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq='1h')

    # Preis-Simulation
    base_price = 50000
    trend = np.linspace(0, 5000, n_bars)
    cycle = np.sin(np.linspace(0, 6 * np.pi, n_bars)) * 2000
    noise = np.random.randn(n_bars).cumsum() * 200

    close_prices = base_price + trend + cycle + noise

    # OHLC generieren
    df = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(n_bars) * 0.002),
        'high': close_prices * (1 + abs(np.random.randn(n_bars)) * 0.003),
        'low': close_prices * (1 - abs(np.random.randn(n_bars)) * 0.003),
        'close': close_prices,
        'volume': np.random.randint(10, 100, n_bars)
    }, index=dates)

    return df


def load_data_from_file(filepath: Path) -> pd.DataFrame:
    """
    Lädt OHLCV-Daten aus Datei (CSV oder Parquet).

    Args:
        filepath: Pfad zur Datei

    Returns:
        DataFrame mit OHLCV-Daten
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Daten-Datei nicht gefunden: {filepath}")

    if filepath.suffix == ".parquet":
        df = pd.read_parquet(filepath)
    elif filepath.suffix == ".csv":
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")

    # Validierung
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Fehlende Spalten: {missing}")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame muss einen DatetimeIndex haben")

    return df


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den ArgumentParser für Walk-Forward-Backtests."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Walk-Forward Backtest Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Sweep-Auswahl
    parser.add_argument(
        "--sweep-name", "-s",
        type=str,
        required=True,
        help="Name des Sweeps (z.B. rsi_reversion_basic)",
    )

    # Walk-Forward-Konfiguration
    parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=3,
        help="Anzahl der Top-Konfigurationen (default: 3)",
    )
    parser.add_argument(
        "--train-window", "-t",
        type=str,
        required=True,
        help="Trainingsfenster-Dauer (z.B. 180d, 6M)",
    )
    parser.add_argument(
        "--test-window",
        type=str,
        required=True,
        help="Testfenster-Dauer (z.B. 30d, 1M)",
    )
    parser.add_argument(
        "--step-size",
        type=str,
        default=None,
        help="Schrittgröße zwischen Fenstern (default: test-window)",
    )

    # Daten-Optionen
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument(
        "--data-file", "-d",
        type=str,
        help="Pfad zur OHLCV-Datei (CSV oder Parquet)",
    )
    data_group.add_argument(
        "--use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten für Tests",
    )

    parser.add_argument(
        "--dummy-bars",
        type=int,
        default=1000,
        help="Anzahl Bars für Dummy-Daten (default: 1000)",
    )

    # Zeitraum-Optionen
    parser.add_argument(
        "--start-date",
        type=str,
        help="Startdatum (YYYY-MM-DD, optional)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="Enddatum (YYYY-MM-DD, optional)",
    )

    # Weitere Optionen
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--metric-primary",
        type=str,
        default="metric_sharpe_ratio",
        help="Primäre Metrik für Top-N-Auswahl (default: metric_sharpe_ratio)",
    )
    parser.add_argument(
        "--metric-fallback",
        type=str,
        default="metric_total_return",
        help="Fallback-Metrik (default: metric_total_return)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="reports/walkforward",
        help="Ausgabe-Verzeichnis (default: reports/walkforward)",
    )

    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser


def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilen-Argumente."""
    return build_parser().parse_args()


def run_from_args(args: argparse.Namespace) -> int:
    """Führt Walk-Forward-Backtest basierend auf Argumenten aus.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # 1. Daten laden
        logger.info("Lade Daten...")
        if args.use_dummy_data:
            df = create_dummy_data(n_bars=args.dummy_bars)
            logger.info(f"Dummy-Daten erstellt: {len(df)} Bars ({df.index[0]} - {df.index[-1]})")
        elif args.data_file:
            df = load_data_from_file(Path(args.data_file))
            logger.info(f"Daten geladen: {len(df)} Bars ({df.index[0]} - {df.index[-1]})")
        else:
            raise ValueError("Entweder --data-file oder --use-dummy-data muss angegeben werden")

        # 2. Walk-Forward-Config erstellen
        wf_config = WalkForwardConfig(
            train_window=args.train_window,
            test_window=args.test_window,
            step_size=args.step_size,
            symbol=args.symbol,
            output_dir=Path(args.output_dir),
        )

        # Zeitraum setzen (falls angegeben)
        if args.start_date:
            wf_config.start_date = pd.Timestamp(args.start_date)
        if args.end_date:
            wf_config.end_date = pd.Timestamp(args.end_date)

        logger.info(
            f"Walk-Forward-Config: Train={wf_config.train_window}, "
            f"Test={wf_config.test_window}, Symbol={wf_config.symbol}"
        )

        # 3. Walk-Forward ausführen
        logger.info(f"Starte Walk-Forward-Analyse für Top-{args.top_n} aus Sweep: {args.sweep_name}")
        results = run_walkforward_for_top_n_from_sweep(
            sweep_name=args.sweep_name,
            wf_config=wf_config,
            top_n=args.top_n,
            df=df,
            metric_primary=args.metric_primary,
            metric_fallback=args.metric_fallback,
        )

        logger.info(f"{len(results)} Walk-Forward-Ergebnisse erzeugt")

        # 4. Reports generieren und speichern
        output_dir = Path(args.output_dir)
        report_paths = []

        for result in results:
            # Einzelner Report
            report = build_walkforward_report(
                result,
                sweep_name=args.sweep_name,
                wf_config=wf_config,
            )
            report_path = save_walkforward_report(
                report,
                output_dir,
                sweep_name=args.sweep_name,
                config_id=result.config_id,
            )
            report_paths.append(report_path)

        # Multi-Config-Vergleichs-Report
        if len(results) > 1:
            comparison_report = build_multi_config_report(
                results,
                sweep_name=args.sweep_name,
            )
            comparison_path = output_dir / args.sweep_name / f"comparison_{datetime.now().strftime('%Y%m%d')}.md"
            comparison_path.parent.mkdir(parents=True, exist_ok=True)
            with open(comparison_path, "w", encoding="utf-8") as f:
                f.write(comparison_report.to_markdown())
            logger.info(f"Vergleichs-Report gespeichert: {comparison_path}")
            report_paths.append(comparison_path)

        # 5. Zusammenfassung ausgeben
        print("\n" + "=" * 70)
        print("Walk-Forward Analysis Summary")
        print("=" * 70)
        print(f"Sweep:           {args.sweep_name}")
        print(f"Top N:           {args.top_n}")
        print(f"Train Window:    {wf_config.train_window}")
        print(f"Test Window:     {wf_config.test_window}")
        print(f"Configs Tested:  {len(results)}")
        print(f"Reports:         {len(report_paths)}")

        # Beste Konfiguration
        if results:
            best = max(results, key=lambda r: r.aggregate_metrics.get("avg_sharpe", 0.0))
            print("\nBest Configuration:")
            print("-" * 70)
            print(f"Config ID:       {best.config_id}")
            print(f"Strategy:        {best.strategy_name}")
            print(f"Avg Sharpe:      {best.aggregate_metrics.get('avg_sharpe', 0):.2f}")
            print(f"Avg Return:      {best.aggregate_metrics.get('avg_return', 0):.2%}")
            print(f"Win Rate:        {best.aggregate_metrics.get('win_rate_windows', 0):.1%}")
            print(f"Windows:         {best.aggregate_metrics.get('total_windows', 0)}")

        print("\n" + "=" * 70)
        print(f"\n✅ Walk-Forward-Analyse abgeschlossen")
        print(f"Reports gespeichert in: {output_dir / args.sweep_name}")
        return 0

    except FileNotFoundError as e:
        print(f"❌ Fehler: {e}")
        print(f"\nTipp: Führe zuerst einen Sweep aus:")
        print(f"  python scripts/run_strategy_sweep.py --sweep-name {args.sweep_name}")
        return 1

    except ValueError as e:
        print(f"❌ Fehler: {e}")
        return 1

    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Haupt-Entry-Point."""
    parser = build_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(list(argv))
    return run_from_args(args)


if __name__ == "__main__":
    sys.exit(main())

