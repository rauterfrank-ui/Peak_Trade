#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/experiments_explorer.py
"""
Peak_Trade – Experiment & Metrics Explorer CLI (Phase 22)
=========================================================
Zentrales CLI-Tool zum Durchsuchen, Filtern und Analysieren von Experimenten.

Subcommands:
    list            Experimente auflisten mit Filtern
    top             Top-N Experimente nach Metrik
    details         Details zu einem einzelnen Experiment
    sweep-summary   Übersicht für einen Sweep
    sweeps          Alle verfügbaren Sweeps listen
    compare         Mehrere Sweeps vergleichen
    export          Export in CSV oder Markdown

Usage:
    # Alle Backtest-Experimente einer Strategie
    python scripts/experiments_explorer.py list --run-type backtest --strategy ma_crossover

    # Top-10 nach Sharpe
    python scripts/experiments_explorer.py top --metric sharpe --top-n 10

    # Sweep-Auswertung
    python scripts/experiments_explorer.py sweep-summary --sweep-name ma_crossover_opt_v1 --metric sharpe

    # Export
    python scripts/experiments_explorer.py export --sweep-name ma_crossover_opt_v1 --csv out/export.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.experiments import VALID_RUN_TYPES, EXPERIMENTS_CSV
from src.analytics.explorer import (
    ExperimentFilter,
    ExperimentSummary,
    RankedExperiment,
    SweepOverview,
    ExperimentExplorer,
)


# =============================================================================
# FORMATIERUNGS-HELPER
# =============================================================================


def format_percent(value: Optional[float], decimals: int = 1) -> str:
    """Formatiert als Prozent oder gibt '-' bei None zurück."""
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "-"


def format_float(value: Optional[float], decimals: int = 2) -> str:
    """Formatiert Float oder gibt '-' bei None zurück."""
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "-"


def truncate(s: str, maxlen: int) -> str:
    """Kürzt String auf maxlen Zeichen."""
    if len(s) <= maxlen:
        return s
    return s[: maxlen - 3] + "..."


# =============================================================================
# OUTPUT FUNCTIONS
# =============================================================================


def print_header(title: str) -> None:
    """Druckt einen formatierten Header."""
    print()
    print("=" * 90)
    print(f"  {title}")
    print("=" * 90)


def print_experiments_table(experiments: List[ExperimentSummary]) -> None:
    """Druckt eine Tabelle mit Experimenten."""
    if not experiments:
        print("\nKeine Experimente gefunden.")
        return

    print()
    header = f"{'RUN_ID':<36} | {'TYPE':<15} | {'STRATEGY':<15} | {'RETURN':>8} | {'SHARPE':>7} | {'TIMESTAMP':<16}"
    print(header)
    print("-" * len(header.replace("|", "+")))

    for exp in experiments:
        run_id = truncate(exp.experiment_id, 36)
        run_type = truncate(exp.run_type, 15)
        strategy = truncate(exp.strategy_name or "-", 15)
        total_return = format_percent(exp.metrics.get("total_return"))
        sharpe = format_float(exp.metrics.get("sharpe"))
        timestamp = exp.created_at.strftime("%Y-%m-%d %H:%M") if exp.created_at else "-"

        print(f"{run_id:<36} | {run_type:<15} | {strategy:<15} | {total_return:>8} | {sharpe:>7} | {timestamp:<16}")

    print()
    print(f"Gefunden: {len(experiments)} Experiment(s)")


def print_ranked_table(ranked: List[RankedExperiment], metric: str) -> None:
    """Druckt eine Ranking-Tabelle."""
    if not ranked:
        print("\nKeine Experimente gefunden.")
        return

    print()
    header = f"{'RANK':>4} | {'RUN_ID':<12} | {'TYPE':<12} | {'STRATEGY':<12} | {metric.upper():>10} | {'RETURN':>8} | {'MAX DD':>8}"
    print(header)
    print("-" * len(header.replace("|", "+")))

    for r in ranked:
        s = r.summary
        run_id = truncate(s.experiment_id, 12)
        run_type = truncate(s.run_type, 12)
        strategy = truncate(s.strategy_name or "-", 12)
        metric_val = format_float(r.sort_value, 3)
        total_return = format_percent(s.metrics.get("total_return"))
        max_dd = format_percent(s.metrics.get("max_drawdown"))

        print(f"{r.rank:>4} | {run_id:<12} | {run_type:<12} | {strategy:<12} | {metric_val:>10} | {total_return:>8} | {max_dd:>8}")

    print()


def print_experiment_details(exp: ExperimentSummary) -> None:
    """Druckt Details zu einem Experiment."""
    print()
    print("--- ALLGEMEIN ---")
    print(f"  Run-ID:       {exp.experiment_id}")
    print(f"  Run-Type:     {exp.run_type}")
    print(f"  Run-Name:     {exp.run_name}")
    if exp.created_at:
        print(f"  Timestamp:    {exp.created_at.isoformat()}")
    if exp.strategy_name:
        print(f"  Strategy:     {exp.strategy_name}")
    if exp.symbol:
        print(f"  Symbol:       {exp.symbol}")
    if exp.sweep_name:
        print(f"  Sweep:        {exp.sweep_name}")
    if exp.portfolio_name:
        print(f"  Portfolio:    {exp.portfolio_name}")
    if exp.tags:
        print(f"  Tags:         {', '.join(exp.tags)}")

    print()
    print("--- METRIKEN ---")
    for key, val in exp.metrics.items():
        if key in ["total_return", "max_drawdown", "cagr", "win_rate"]:
            print(f"  {key:<16} {format_percent(val)}")
        else:
            print(f"  {key:<16} {format_float(val)}")

    if exp.params:
        print()
        print("--- PARAMETER ---")
        for key, val in exp.params.items():
            print(f"  {key:<16} {val}")


def print_sweep_overview(overview: SweepOverview, metric: str) -> None:
    """Druckt eine Sweep-Übersicht."""
    print()
    print("--- SWEEP INFO ---")
    print(f"  Sweep-Name:   {overview.sweep_name}")
    print(f"  Strategy:     {overview.strategy_key}")
    print(f"  Run Count:    {overview.run_count}")

    if overview.metric_stats:
        print()
        print(f"--- {metric.upper()} STATISTIKEN ---")
        print(f"  Min:          {format_float(overview.metric_stats.get('min'))}")
        print(f"  Max:          {format_float(overview.metric_stats.get('max'))}")
        print(f"  Mean:         {format_float(overview.metric_stats.get('mean'))}")
        print(f"  Median:       {format_float(overview.metric_stats.get('median'))}")
        print(f"  Std:          {format_float(overview.metric_stats.get('std'))}")

    if overview.param_ranges:
        print()
        print("--- PARAMETER-BEREICHE ---")
        for param, info in overview.param_ranges.items():
            values = info.get("values", [])
            if len(values) <= 5:
                print(f"  {param:<16} [{', '.join(values)}]")
            else:
                print(f"  {param:<16} [{len(values)} verschiedene Werte]")

    if overview.best_runs:
        print()
        print(f"--- TOP {len(overview.best_runs)} RUNS (nach {metric}) ---")
        print_ranked_table(overview.best_runs, metric)


def print_sweeps_list(sweeps: List[str]) -> None:
    """Druckt eine Liste von Sweeps."""
    if not sweeps:
        print("\nKeine Sweeps gefunden.")
        return

    print()
    print(f"Verfügbare Sweeps ({len(sweeps)}):")
    print()
    for i, name in enumerate(sweeps, 1):
        print(f"  {i:3}. {name}")
    print()


def print_sweep_comparison(overviews: List[SweepOverview], metric: str) -> None:
    """Druckt einen Sweep-Vergleich."""
    if not overviews:
        print("\nKeine Sweeps zum Vergleichen gefunden.")
        return

    print()
    header = f"{'SWEEP NAME':<30} | {'STRATEGY':<15} | {'RUNS':>6} | {'BEST':>10} | {'MEAN':>10} | {'STD':>10}"
    print(header)
    print("-" * len(header.replace("|", "+")))

    for o in overviews:
        name = truncate(o.sweep_name, 30)
        strategy = truncate(o.strategy_key, 15)
        runs = o.run_count
        best = format_float(o.metric_stats.get("max"))
        mean = format_float(o.metric_stats.get("mean"))
        std = format_float(o.metric_stats.get("std"))

        print(f"{name:<30} | {strategy:<15} | {runs:>6} | {best:>10} | {mean:>10} | {std:>10}")

    print()


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser mit Subcommands."""
    parser = argparse.ArgumentParser(
        prog="experiments_explorer.py",
        description="Peak_Trade Experiment & Metrics Explorer (Phase 22)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Backtests listen
  python scripts/experiments_explorer.py list --run-type backtest --limit 20

  # Top-10 nach Sharpe für eine Strategie
  python scripts/experiments_explorer.py top --strategy ma_crossover --metric sharpe --top-n 10

  # Sweep-Auswertung
  python scripts/experiments_explorer.py sweep-summary --sweep-name ma_crossover_opt_v1 --metric sharpe

  # Sweep-Vergleich
  python scripts/experiments_explorer.py compare --sweeps ma_crossover_opt_v1,rsi_reversion_opt_v1 --metric sharpe

  # Export in CSV
  python scripts/experiments_explorer.py export --run-type sweep --csv out/sweeps.csv
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Subcommands")

    # --- list ---
    list_parser = subparsers.add_parser("list", help="Experimente auflisten")
    _add_filter_args(list_parser)
    list_parser.add_argument(
        "--sort-by",
        default="timestamp",
        help="Spalte für Sortierung (default: timestamp)",
    )
    list_parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (default: absteigend)",
    )

    # --- top ---
    top_parser = subparsers.add_parser("top", help="Top-N Experimente nach Metrik")
    _add_filter_args(top_parser)
    top_parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Ranking (default: sharpe)",
    )
    top_parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Anzahl Top-Ergebnisse (default: 10)",
    )
    top_parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (für 'niedriger ist besser' Metriken)",
    )

    # --- details ---
    details_parser = subparsers.add_parser("details", help="Details zu einem Experiment")
    details_parser.add_argument(
        "--id",
        required=True,
        help="Run-ID des Experiments",
    )

    # --- sweep-summary ---
    sweep_parser = subparsers.add_parser("sweep-summary", help="Übersicht für einen Sweep")
    sweep_parser.add_argument(
        "--sweep-name",
        required=True,
        help="Name des Sweeps",
    )
    sweep_parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Ranking (default: sharpe)",
    )
    sweep_parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Anzahl Top-Runs in der Übersicht (default: 10)",
    )

    # --- sweeps ---
    subparsers.add_parser("sweeps", help="Alle verfügbaren Sweeps listen")

    # --- compare ---
    compare_parser = subparsers.add_parser("compare", help="Sweeps vergleichen")
    compare_parser.add_argument(
        "--sweeps",
        required=True,
        help="Komma-separierte Liste von Sweep-Namen",
    )
    compare_parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Vergleich (default: sharpe)",
    )

    # --- export ---
    export_parser = subparsers.add_parser("export", help="Export in CSV oder Markdown")
    _add_filter_args(export_parser)
    export_parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Sortierung (default: sharpe)",
    )
    export_parser.add_argument(
        "--top-n",
        type=int,
        default=100,
        help="Anzahl Experimente (default: 100)",
    )
    export_parser.add_argument(
        "--csv",
        dest="csv_path",
        help="Pfad für CSV-Export",
    )
    export_parser.add_argument(
        "--markdown",
        dest="md_path",
        help="Pfad für Markdown-Export",
    )

    return parser


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Filter-Argumente zu einem Parser hinzu."""
    parser.add_argument(
        "--run-type",
        choices=VALID_RUN_TYPES,
        help="Filter nach run_type",
    )
    parser.add_argument(
        "--strategy",
        help="Filter nach strategy_key",
    )
    parser.add_argument(
        "--symbol",
        help="Filter nach Symbol",
    )
    parser.add_argument(
        "--sweep-name",
        help="Filter nach sweep_name",
    )
    parser.add_argument(
        "--tag",
        help="Filter nach Tag",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximale Anzahl Ergebnisse (default: 50)",
    )


def build_filter(args: argparse.Namespace) -> ExperimentFilter:
    """Baut einen ExperimentFilter aus CLI-Args."""
    return ExperimentFilter(
        run_types=[args.run_type] if getattr(args, "run_type", None) else None,
        strategies=[args.strategy] if getattr(args, "strategy", None) else None,
        symbols=[args.symbol] if getattr(args, "symbol", None) else None,
        sweep_names=[args.sweep_name] if getattr(args, "sweep_name", None) else None,
        tags=[args.tag] if getattr(args, "tag", None) else None,
        limit=getattr(args, "limit", None),
    )


# =============================================================================
# COMMAND HANDLERS
# =============================================================================


def cmd_list(args: argparse.Namespace) -> int:
    """Handler für 'list' Command."""
    print_header("Peak_Trade – Experiment Explorer: List")

    explorer = ExperimentExplorer()
    flt = build_filter(args)

    experiments = explorer.list_experiments(
        flt,
        sort_by=args.sort_by,
        ascending=args.ascending,
    )

    # Filter-Info
    filters = []
    if args.run_type:
        filters.append(f"run_type={args.run_type}")
    if args.strategy:
        filters.append(f"strategy={args.strategy}")
    if args.sweep_name:
        filters.append(f"sweep_name={args.sweep_name}")
    if args.tag:
        filters.append(f"tag={args.tag}")

    if filters:
        print(f"\nFilter: {', '.join(filters)}")
    print(f"Sortiert nach: {args.sort_by} ({'asc' if args.ascending else 'desc'})")
    print(f"Limit: {args.limit}")

    print_experiments_table(experiments)
    return 0


def cmd_top(args: argparse.Namespace) -> int:
    """Handler für 'top' Command."""
    print_header(f"Peak_Trade – Experiment Explorer: Top {args.top_n} nach {args.metric}")

    explorer = ExperimentExplorer()
    flt = build_filter(args)

    ranked = explorer.rank_experiments(
        flt,
        metric=args.metric,
        top_n=args.top_n,
        descending=not args.ascending,
    )

    # Filter-Info
    filters = []
    if args.run_type:
        filters.append(f"run_type={args.run_type}")
    if args.strategy:
        filters.append(f"strategy={args.strategy}")

    if filters:
        print(f"\nFilter: {', '.join(filters)}")

    print_ranked_table(ranked, args.metric)
    return 0


def cmd_details(args: argparse.Namespace) -> int:
    """Handler für 'details' Command."""
    print_header("Peak_Trade – Experiment Explorer: Details")

    explorer = ExperimentExplorer()
    exp = explorer.get_experiment_details(args.id)

    if exp is None:
        print(f"\nExperiment nicht gefunden: {args.id}")
        return 1

    print_experiment_details(exp)
    print()
    return 0


def cmd_sweep_summary(args: argparse.Namespace) -> int:
    """Handler für 'sweep-summary' Command."""
    print_header(f"Peak_Trade – Experiment Explorer: Sweep '{args.sweep_name}'")

    explorer = ExperimentExplorer()
    overview = explorer.summarize_sweep(
        args.sweep_name,
        metric=args.metric,
        top_n=args.top_n,
    )

    if overview is None:
        print(f"\nSweep nicht gefunden: {args.sweep_name}")
        return 1

    print_sweep_overview(overview, args.metric)
    return 0


def cmd_sweeps(args: argparse.Namespace) -> int:
    """Handler für 'sweeps' Command."""
    print_header("Peak_Trade – Experiment Explorer: Verfügbare Sweeps")

    explorer = ExperimentExplorer()
    sweeps = explorer.list_sweeps()

    print_sweeps_list(sweeps)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Handler für 'compare' Command."""
    sweep_names = [s.strip() for s in args.sweeps.split(",")]

    print_header(f"Peak_Trade – Experiment Explorer: Sweep-Vergleich nach {args.metric}")
    print(f"\nVergleiche: {', '.join(sweep_names)}")

    explorer = ExperimentExplorer()
    overviews = explorer.compare_sweeps(sweep_names, metric=args.metric)

    print_sweep_comparison(overviews, args.metric)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Handler für 'export' Command."""
    print_header("Peak_Trade – Experiment Explorer: Export")

    if not args.csv_path and not args.md_path:
        print("\nFEHLER: Mindestens --csv oder --markdown angeben.")
        return 1

    explorer = ExperimentExplorer()
    flt = build_filter(args)

    if args.csv_path:
        csv_path = Path(args.csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        ranked = explorer.rank_experiments(flt, metric=args.metric, top_n=args.top_n)

        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "rank", "run_id", "run_type", "strategy", "symbol",
                "total_return", "sharpe", "max_drawdown", "cagr",
                "sweep_name", "timestamp"
            ])
            for r in ranked:
                s = r.summary
                writer.writerow([
                    r.rank,
                    s.experiment_id,
                    s.run_type,
                    s.strategy_name or "",
                    s.symbol or "",
                    s.metrics.get("total_return", ""),
                    s.metrics.get("sharpe", ""),
                    s.metrics.get("max_drawdown", ""),
                    s.metrics.get("cagr", ""),
                    s.sweep_name or "",
                    s.created_at.isoformat() if s.created_at else "",
                ])

        print(f"\nCSV exportiert: {csv_path}")
        print(f"  Anzahl Zeilen: {len(ranked)}")

    if args.md_path:
        md_path = Path(args.md_path)
        output_path = explorer.export_to_markdown(flt, md_path, args.metric, args.top_n)
        print(f"\nMarkdown exportiert: {output_path}")

    print()
    return 0


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Registry-Check
    if not EXPERIMENTS_CSV.exists():
        print(f"\nKeine Experiment-Registry gefunden: {EXPERIMENTS_CSV}")
        print("Führe zuerst einen Backtest aus, um Experiments zu erzeugen.\n")
        return 1

    # Command-Dispatch
    handlers = {
        "list": cmd_list,
        "top": cmd_top,
        "details": cmd_details,
        "sweep-summary": cmd_sweep_summary,
        "sweeps": cmd_sweeps,
        "compare": cmd_compare,
        "export": cmd_export,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    print(f"Unbekannter Command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
