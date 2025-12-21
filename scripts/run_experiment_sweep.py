#!/usr/bin/env python3
"""
Peak_Trade Experiment Sweep CLI (Phase 29)
==========================================

CLI-Tool für Parameter-Sweeps über Strategien und Regime-Konfigurationen.

Verwendung:
    # Einfacher Strategy-Sweep
    python scripts/run_experiment_sweep.py --strategy ma_crossover --granularity medium

    # Mit Symbol und Zeitraum
    python scripts/run_experiment_sweep.py \\
        --strategy vol_breakout \\
        --symbol BTC/EUR \\
        --start 2024-01-01 \\
        --end 2024-06-01

    # Mit Regime-Detection
    python scripts/run_experiment_sweep.py \\
        --strategy vol_breakout \\
        --with-regime \\
        --detector volatility_breakout

    # Parallel ausführen
    python scripts/run_experiment_sweep.py \\
        --strategy ma_crossover \\
        --parallel \\
        --workers 4

    # Dry-Run (nur Parameter generieren)
    python scripts/run_experiment_sweep.py \\
        --strategy ma_crossover \\
        --dry-run

    # Liste verfügbarer Strategien
    python scripts/run_experiment_sweep.py --list-strategies

    # Liste verfügbarer Regime-Detectors
    python scripts/run_experiment_sweep.py --list-regimes

Output:
    - reports/experiments/{strategy}_{id}_{timestamp}.csv
    - reports/experiments/{strategy}_{id}_{timestamp}.parquet
    - reports/experiments/{strategy}_{id}_{timestamp}_summary.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments import (
    ExperimentConfig,
    ExperimentRunner,
    ParamSweep,
    get_strategy_sweeps,
    get_regime_detector_sweeps,
    get_combined_regime_strategy_sweeps,
    list_available_strategies,
    STRATEGY_SWEEP_REGISTRY,
    REGIME_SWEEP_REGISTRY,
)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Experiment Sweep CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Haupt-Argumente
    parser.add_argument(
        "--strategy",
        "-s",
        type=str,
        help="Name der Strategie (z.B. ma_crossover, vol_breakout)",
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        help="Name des Experiments (optional)",
    )

    # Symbol und Zeitraum
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        help="Mehrere Symbole (überschreibt --symbol)",
    )
    parser.add_argument(
        "--timeframe",
        "-t",
        type=str,
        default="1h",
        help="Zeitrahmen (default: 1h)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start-Datum (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End-Datum (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Startkapital (default: 10000)",
    )

    # Sweep-Konfiguration
    parser.add_argument(
        "--granularity",
        "-g",
        type=str,
        choices=["coarse", "medium", "fine"],
        default="medium",
        help="Sweep-Granularität (default: medium)",
    )
    parser.add_argument(
        "--custom-sweeps",
        type=str,
        help="JSON-String mit Custom-Sweeps",
    )

    # Regime-Optionen
    parser.add_argument(
        "--with-regime",
        action="store_true",
        help="Aktiviert Regime-Detection-Parameter im Sweep",
    )
    parser.add_argument(
        "--detector",
        type=str,
        default="volatility_breakout",
        choices=["volatility_breakout", "range_compression"],
        help="Regime-Detector (default: volatility_breakout)",
    )

    # Ausführungs-Optionen
    parser.add_argument(
        "--parallel",
        "-p",
        action="store_true",
        help="Parallel ausführen",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Anzahl paralleler Worker (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Parameter generieren, keine Backtests",
    )

    # Output-Optionen
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="reports/experiments",
        help="Ausgabe-Verzeichnis (default: reports/experiments)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Ergebnisse nicht speichern",
    )

    # Info-Optionen
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Liste verfügbarer Strategien anzeigen",
    )
    parser.add_argument(
        "--list-regimes",
        action="store_true",
        help="Liste verfügbarer Regime-Detectors anzeigen",
    )
    parser.add_argument(
        "--show-params",
        action="store_true",
        help="Zeigt Parameter-Kombinationen ohne Ausführung",
    )

    # Logging
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser.parse_args()


def list_strategies() -> None:
    """Zeigt verfügbare Strategien an."""
    print("\n" + "=" * 60)
    print("Verfügbare Strategien für Parameter-Sweeps")
    print("=" * 60)

    strategies = list_available_strategies()
    for strategy in strategies:
        sweeps = get_strategy_sweeps(strategy, "coarse")
        params = [s.name for s in sweeps]
        print(f"\n  {strategy}")
        print(f"    Parameter: {', '.join(params)}")

    print("\n" + "=" * 60)


def list_regimes() -> None:
    """Zeigt verfügbare Regime-Detectors an."""
    print("\n" + "=" * 60)
    print("Verfügbare Regime-Detectors für Parameter-Sweeps")
    print("=" * 60)

    for name in sorted(REGIME_SWEEP_REGISTRY.keys()):
        sweeps = REGIME_SWEEP_REGISTRY[name]("coarse")
        params = [s.name for s in sweeps]
        print(f"\n  {name}")
        print(f"    Parameter: {', '.join(params)}")

    print("\n" + "=" * 60)


def show_params(config: ExperimentConfig) -> None:
    """Zeigt Parameter-Kombinationen an."""
    combos = config.generate_param_combinations()

    print("\n" + "=" * 60)
    print(f"Parameter-Kombinationen für '{config.name}'")
    print("=" * 60)
    print(f"\nStrategie: {config.strategy_name}")
    print(f"Symbole: {config.symbols}")
    print(f"Anzahl Kombinationen: {len(combos)}")
    print(f"Gesamt-Runs: {config.num_combinations}")

    print("\nSweep-Parameter:")
    for sweep in config.param_sweeps:
        print(f"  {sweep.name}: {sweep.values}")

    print("\nErste 10 Kombinationen:")
    for i, combo in enumerate(combos[:10]):
        print(f"  {i + 1:3d}. {combo}")

    if len(combos) > 10:
        print(f"  ... und {len(combos) - 10} weitere")

    print("\n" + "=" * 60)


def create_progress_callback():
    """Erstellt Progress-Callback für Terminal."""
    start_time = datetime.now()

    def callback(current: int, total: int, message: str) -> None:
        elapsed = (datetime.now() - start_time).total_seconds()
        if current > 0:
            eta = (elapsed / current) * (total - current)
        else:
            eta = 0

        pct = (current / total) * 100 if total > 0 else 0
        bar_width = 30
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        print(
            f"\r[{bar}] {pct:5.1f}% | {current}/{total} | ETA: {eta:.0f}s | {message[:40]:40s}",
            end="",
            flush=True,
        )

        if current == total:
            print()  # Newline am Ende

    return callback


def main() -> int:
    """Haupt-Entry-Point."""
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Info-Befehle
    if args.list_strategies:
        list_strategies()
        return 0

    if args.list_regimes:
        list_regimes()
        return 0

    # Strategie erforderlich für Sweep
    if not args.strategy:
        print("Fehler: --strategy ist erforderlich")
        print("Verwende --list-strategies für verfügbare Strategien")
        return 1

    # Symbole
    symbols = args.symbols if args.symbols else [args.symbol]

    # Parameter-Sweeps erstellen
    try:
        if args.with_regime:
            param_sweeps = get_combined_regime_strategy_sweeps(
                args.strategy,
                args.detector,
                args.granularity,
            )
        else:
            param_sweeps = get_strategy_sweeps(args.strategy, args.granularity)
    except ValueError as e:
        print(f"Fehler: {e}")
        return 1

    # Custom Sweeps hinzufügen
    if args.custom_sweeps:
        import json

        try:
            custom = json.loads(args.custom_sweeps)
            for name, values in custom.items():
                param_sweeps.append(ParamSweep(name, values))
        except json.JSONDecodeError as e:
            print(f"Fehler beim Parsen von --custom-sweeps: {e}")
            return 1

    # Experiment-Name
    exp_name = args.name or f"{args.strategy.upper()} Parameter Sweep"

    # Regime-Config falls aktiviert
    regime_config = None
    if args.with_regime:
        regime_config = {
            "enabled": True,
            "detector_name": args.detector,
        }

    # ExperimentConfig erstellen
    config = ExperimentConfig(
        name=exp_name,
        strategy_name=args.strategy,
        param_sweeps=param_sweeps,
        symbols=symbols,
        timeframe=args.timeframe,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        regime_config=regime_config,
        parallel=args.parallel,
        max_workers=args.workers,
        save_results=not args.no_save,
        output_dir=args.output_dir,
        tags=[args.granularity, "cli"],
    )

    # Nur Parameter anzeigen
    if args.show_params:
        show_params(config)
        return 0

    # Runner erstellen
    runner = ExperimentRunner(
        progress_callback=create_progress_callback() if not args.verbose else None,
    )

    # Experiment-Info ausgeben
    print("\n" + "=" * 60)
    print(f"Peak_Trade Experiment Sweep")
    print("=" * 60)
    print(f"Experiment:    {config.name}")
    print(f"Strategie:     {config.strategy_name}")
    print(f"Symbole:       {', '.join(symbols)}")
    print(f"Timeframe:     {config.timeframe}")
    print(f"Granularität:  {args.granularity}")
    print(f"Kombinationen: {config.num_combinations}")
    print(f"Parallel:      {'Ja' if args.parallel else 'Nein'}")
    if args.with_regime:
        print(f"Regime:        {args.detector}")
    print("=" * 60 + "\n")

    # Dry-Run
    if args.dry_run:
        logger.info("Dry-Run: Keine Backtests werden ausgeführt")
        result = runner.run(config, dry_run=True)
        show_params(config)
        return 0

    # Experiment ausführen
    try:
        if args.parallel:
            result = runner.run_parallel(config)
        else:
            result = runner.run(config)
    except Exception as e:
        logger.error(f"Experiment fehlgeschlagen: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    # Ergebnisse anzeigen
    print("\n" + "=" * 60)
    print("Ergebnisse")
    print("=" * 60)
    print(f"Runs:          {result.num_runs}")
    print(f"Erfolgreich:   {result.num_successful}")
    print(f"Fehlgeschlagen:{result.num_failed}")
    print(f"Erfolgsrate:   {result.success_rate * 100:.1f}%")
    print(f"Laufzeit:      {result.total_runtime_seconds:.1f}s")

    # Beste Ergebnisse anzeigen
    if result.num_successful > 0:
        print("\n--- Top 5 nach Sharpe Ratio ---")
        best = result.get_best_by_metric("sharpe_ratio", top_n=5)
        for i, r in enumerate(best, 1):
            sharpe = r.metrics.get("sharpe_ratio", float("nan"))
            ret = r.metrics.get("total_return", float("nan"))
            print(f"  {i}. Sharpe: {sharpe:.3f}, Return: {ret * 100:.1f}%")
            print(f"     Params: {r.params}")

        print("\n--- Top 5 nach Total Return ---")
        best = result.get_best_by_metric("total_return", top_n=5)
        for i, r in enumerate(best, 1):
            sharpe = r.metrics.get("sharpe_ratio", float("nan"))
            ret = r.metrics.get("total_return", float("nan"))
            print(f"  {i}. Return: {ret * 100:.1f}%, Sharpe: {sharpe:.3f}")
            print(f"     Params: {r.params}")

    # Summary Stats
    summary = result.get_summary_stats()
    if summary:
        print("\n--- Summary Statistics ---")
        for key in ["sharpe_ratio_mean", "total_return_mean", "max_drawdown_mean"]:
            if key in summary:
                print(f"  {key}: {summary[key]:.4f}")

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
