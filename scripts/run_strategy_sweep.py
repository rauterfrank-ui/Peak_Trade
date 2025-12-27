#!/usr/bin/env python3
"""
Peak_Trade Strategy Sweep CLI (Phase 41)
=========================================

Zentrales CLI für Strategy-Sweeps aus dem Research-Playground.

Verwendung:
    # Vordefinierte Sweeps ausführen
    python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_basic

    # Vordefinierte Sweeps auflisten
    python scripts/run_strategy_sweep.py --list-sweeps

    # Mit Symbol und Zeitraum
    python scripts/run_strategy_sweep.py \\
        --sweep-name breakout_basic \\
        --symbol BTC/EUR \\
        --start 2024-01-01 \\
        --end 2024-06-01

    # Dry-Run (nur Kombinationen anzeigen)
    python scripts/run_strategy_sweep.py --sweep-name ma_crossover_basic --dry-run

    # Limit auf N Runs
    python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_fine --max-runs 10

    # Custom Strategy Sweep (ohne vordefinierte Definition)
    python scripts/run_strategy_sweep.py \\
        --strategy ma_crossover \\
        --granularity medium

Output:
    - reports/experiments/{sweep_name}_{id}_{timestamp}.csv
    - reports/experiments/{sweep_name}_{id}_{timestamp}.parquet
    - reports/experiments/{sweep_name}_{id}_{timestamp}_summary.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments import (
    ExperimentRunner,
    get_predefined_sweep,
    list_predefined_sweeps,
    get_all_predefined_sweeps,
    get_sweeps_for_strategy,
    print_sweep_catalog,
    StrategySweepConfig,
    get_strategy_sweeps,
    list_available_strategies,
)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den ArgumentParser für Strategy-Sweeps."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Strategy Sweep CLI (Phase 41)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Sweep-Auswahl
    sweep_group = parser.add_mutually_exclusive_group()
    sweep_group.add_argument(
        "--sweep-name",
        "-s",
        type=str,
        help="Name eines vordefinierten Sweeps (z.B. rsi_reversion_basic, breakout_fine)",
    )
    sweep_group.add_argument(
        "--strategy",
        type=str,
        help="Strategie für automatischen Sweep (nutzt get_strategy_sweeps)",
    )

    # Granularität (für --strategy)
    parser.add_argument(
        "--granularity",
        "-g",
        type=str,
        choices=["coarse", "medium", "fine"],
        default="medium",
        help="Sweep-Granularität für automatische Sweeps (default: medium)",
    )

    # Symbol und Zeitraum
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
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

    # Ausführungs-Optionen
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Maximale Anzahl der Runs (optional)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Kombinationen anzeigen, keine Backtests",
    )
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
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optionaler Tag für Ergebnisse",
    )

    # Info-Optionen
    parser.add_argument(
        "--list-sweeps",
        action="store_true",
        help="Liste aller vordefinierten Sweeps anzeigen",
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Liste verfügbarer Strategien anzeigen",
    )
    parser.add_argument(
        "--show-catalog",
        action="store_true",
        help="Vollständigen Sweep-Katalog anzeigen",
    )
    parser.add_argument(
        "--show-params",
        action="store_true",
        help="Zeigt Parameter-Kombinationen ohne Ausführung",
    )

    # Config
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )

    # Logging
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser


def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilen-Argumente."""
    return build_parser().parse_args()


def list_all_sweeps() -> None:
    """Zeigt alle vordefinierten Sweeps an."""
    print("\n" + "=" * 70)
    print("Vordefinierte Strategy Sweeps (Phase 41)")
    print("=" * 70)

    sweeps = get_all_predefined_sweeps()
    by_strategy: dict = {}

    for name, sweep in sweeps.items():
        strategy = sweep.strategy_name
        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append((name, sweep))

    for strategy in sorted(by_strategy.keys()):
        print(f"\n### {strategy}")
        print("-" * 40)
        for name, sweep in by_strategy[strategy]:
            combos = sweep.num_combinations
            raw = sweep.num_raw_combinations
            note = f" (von {raw})" if raw != combos else ""
            print(f"  {name:<35} {combos:>4} Runs{note}")
            if sweep.description:
                print(f"    {sweep.description}")

    print("\n" + "=" * 70)
    print(f"Gesamt: {len(sweeps)} vordefinierte Sweeps")
    print("=" * 70)


def list_all_strategies() -> None:
    """Zeigt verfügbare Strategien an."""
    print("\n" + "=" * 60)
    print("Verfügbare Strategien für Sweeps")
    print("=" * 60)

    strategies = list_available_strategies()
    for strategy in strategies:
        sweeps = get_strategy_sweeps(strategy, "coarse")
        params = [s.name for s in sweeps]
        print(f"\n  {strategy}")
        print(f"    Parameter: {', '.join(params)}")

    print("\n" + "=" * 60)


def show_sweep_params(sweep: StrategySweepConfig) -> None:
    """Zeigt Parameter-Kombinationen eines Sweeps an."""
    combos = sweep.generate_param_combinations()

    print("\n" + "=" * 70)
    print(f"Parameter-Kombinationen für '{sweep.name}'")
    print("=" * 70)
    print(f"\nStrategie:     {sweep.strategy_name}")
    print(f"Symbole:       {sweep.symbols}")
    print(f"Timeframe:     {sweep.timeframe}")
    print(f"Kombinationen: {len(combos)} (von {sweep.num_raw_combinations} vor Constraints)")

    print("\nParameter-Grid:")
    for param, values in sweep.param_grid.items():
        print(f"  {param}: {values}")

    if sweep.constraints:
        print("\nConstraints:")
        for c in sweep.constraints:
            print(f"  {c.left_param} {c.operator} {c.right}")

    print("\nErste 15 Kombinationen:")
    for i, combo in enumerate(combos[:15]):
        print(f"  {i + 1:3d}. {combo}")

    if len(combos) > 15:
        print(f"  ... und {len(combos) - 15} weitere")

    print("\n" + "=" * 70)


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
        bar = "=" * filled + ">" + "." * (bar_width - filled - 1)

        print(
            f"\r[{bar}] {pct:5.1f}% | {current}/{total} | ETA: {eta:.0f}s | {message[:35]:35s}",
            end="",
            flush=True,
        )

        if current == total:
            print()  # Newline am Ende

    return callback


def run_from_args(args: argparse.Namespace) -> int:
    """Führt einen Strategy-Sweep basierend auf Argumenten aus.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Info-Befehle
    if args.list_sweeps:
        list_all_sweeps()
        return 0

    if args.list_strategies:
        list_all_strategies()
        return 0

    if args.show_catalog:
        print(print_sweep_catalog())
        return 0

    # Sweep laden oder erstellen
    sweep_config: Optional[StrategySweepConfig] = None

    if args.sweep_name:
        # Vordefinierter Sweep
        try:
            sweep_config = get_predefined_sweep(args.sweep_name)
            logger.info(f"Lade vordefinierten Sweep: {args.sweep_name}")
        except KeyError as e:
            print(f"Fehler: {e}")
            print("\nVerwende --list-sweeps für verfügbare Sweeps")
            return 1

    elif args.strategy:
        # Automatischer Sweep aus Strategy-Sweeps
        try:
            from src.experiments import ParamSweep

            param_sweeps = get_strategy_sweeps(args.strategy, args.granularity)

            # Konvertiere ParamSweeps zu param_grid
            param_grid = {ps.name: ps.values for ps in param_sweeps}

            sweep_config = StrategySweepConfig(
                name=f"{args.strategy}_{args.granularity}_auto",
                strategy_name=args.strategy,
                param_grid=param_grid,
                symbols=[args.symbol],
                timeframe=args.timeframe,
                tags=[args.granularity, "auto_sweep"],
            )
            logger.info(f"Erstelle automatischen Sweep für: {args.strategy}")
        except ValueError as e:
            print(f"Fehler: {e}")
            print("\nVerwende --list-strategies für verfügbare Strategien")
            return 1

    else:
        print("Fehler: --sweep-name oder --strategy erforderlich")
        print("\nVerwende --list-sweeps für vordefinierte Sweeps")
        print("Verwende --list-strategies für Strategien")
        return 1

    # Symbol überschreiben wenn angegeben
    if args.symbol != "BTC/EUR" or args.sweep_name is None:
        sweep_config.symbols = [args.symbol]

    if args.timeframe != "1h" or args.sweep_name is None:
        sweep_config.timeframe = args.timeframe

    # Tag hinzufügen
    if args.tag:
        sweep_config.tags.append(args.tag)

    # Nur Parameter anzeigen
    if args.show_params or args.dry_run:
        show_sweep_params(sweep_config)
        if args.dry_run:
            return 0

    # ExperimentConfig erstellen
    exp_config = sweep_config.to_experiment_config(
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        output_dir=args.output_dir,
    )
    exp_config.save_results = not args.no_save
    exp_config.parallel = args.parallel
    exp_config.max_workers = args.workers

    # Runner erstellen
    runner = ExperimentRunner(
        progress_callback=create_progress_callback() if not args.verbose else None,
    )

    # Kombinationen mit Constraints filtern
    combinations = sweep_config.generate_param_combinations()

    if args.max_runs and len(combinations) > args.max_runs:
        logger.info(f"Limitiere auf {args.max_runs} von {len(combinations)} Kombinationen")
        combinations = combinations[: args.max_runs]

    # Experiment-Info ausgeben
    print("\n" + "=" * 70)
    print("Peak_Trade Strategy Sweep (Phase 41)")
    print("=" * 70)
    print(f"Sweep:         {sweep_config.name}")
    print(f"Strategie:     {sweep_config.strategy_name}")
    print(f"Symbole:       {', '.join(sweep_config.symbols)}")
    print(f"Timeframe:     {sweep_config.timeframe}")
    print(f"Kombinationen: {len(combinations)}")
    if sweep_config.num_raw_combinations != len(combinations):
        print(f"               (von {sweep_config.num_raw_combinations} vor Constraints)")
    print(f"Parallel:      {'Ja' if args.parallel else 'Nein'}")
    if sweep_config.description:
        print(f"Beschreibung:  {sweep_config.description}")
    print("=" * 70 + "\n")

    # Experiment ausführen
    try:
        if args.parallel:
            result = runner.run_parallel(exp_config)
        else:
            result = runner.run(exp_config)
    except Exception as e:
        logger.error(f"Sweep fehlgeschlagen: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    # Ergebnisse anzeigen
    print("\n" + "=" * 70)
    print("Ergebnisse")
    print("=" * 70)
    print(f"Runs:           {result.num_runs}")
    print(f"Erfolgreich:    {result.num_successful}")
    print(f"Fehlgeschlagen: {result.num_failed}")
    print(f"Erfolgsrate:    {result.success_rate * 100:.1f}%")
    print(f"Laufzeit:       {result.total_runtime_seconds:.1f}s")

    # Beste Ergebnisse anzeigen
    if result.num_successful > 0:
        print("\n--- Top 5 nach Sharpe Ratio ---")
        best_sharpe = result.get_best_by_metric("sharpe_ratio", top_n=5)
        for i, r in enumerate(best_sharpe, 1):
            sharpe = r.metrics.get("sharpe_ratio", float("nan"))
            ret = r.metrics.get("total_return", float("nan"))
            print(f"  {i}. Sharpe: {sharpe:7.3f}, Return: {ret * 100:6.1f}%")
            # Kompakte Parameter-Anzeige
            params_str = ", ".join(f"{k}={v}" for k, v in list(r.params.items())[:4])
            print(f"     {params_str}")

        print("\n--- Top 5 nach Total Return ---")
        best_return = result.get_best_by_metric("total_return", top_n=5)
        for i, r in enumerate(best_return, 1):
            sharpe = r.metrics.get("sharpe_ratio", float("nan"))
            ret = r.metrics.get("total_return", float("nan"))
            max_dd = r.metrics.get("max_drawdown", float("nan"))
            print(
                f"  {i}. Return: {ret * 100:6.1f}%, Sharpe: {sharpe:7.3f}, MaxDD: {max_dd * 100:6.1f}%"
            )

        print("\n--- Top 5 nach niedrigstem Max Drawdown ---")
        best_dd = result.get_best_by_metric("max_drawdown", ascending=False, top_n=5)
        for i, r in enumerate(best_dd, 1):
            sharpe = r.metrics.get("sharpe_ratio", float("nan"))
            ret = r.metrics.get("total_return", float("nan"))
            max_dd = r.metrics.get("max_drawdown", float("nan"))
            print(
                f"  {i}. MaxDD: {max_dd * 100:6.1f}%, Return: {ret * 100:6.1f}%, Sharpe: {sharpe:7.3f}"
            )

    # Summary Stats
    summary = result.get_summary_stats()
    if summary:
        print("\n--- Summary Statistics ---")
        for key in [
            "sharpe_ratio_mean",
            "sharpe_ratio_max",
            "total_return_mean",
            "max_drawdown_mean",
        ]:
            if key in summary:
                print(f"  {key}: {summary[key]:.4f}")

    print("\n" + "=" * 70)
    print("Nächste Schritte:")
    print(f"  # Report generieren:")
    print(f"  python scripts/generate_strategy_sweep_report.py --sweep-name {sweep_config.name}")
    print("=" * 70)

    return 0


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
