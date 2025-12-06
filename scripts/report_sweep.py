#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/report_sweep.py
"""
Peak_Trade – Sweep Report Generator (Phase 21)
===============================================
Generiert einen HTML-Report für einen Hyperparameter-Sweep.

Usage:
    # Sweep-Report generieren
    python scripts/report_sweep.py --sweep-name ma_crossover_opt_v1

    # Mit spezifischer Metrik und Top-N
    python scripts/report_sweep.py --sweep-name ma_opt_v1 --metric sharpe --top-n 20

    # Report automatisch im Browser öffnen
    python scripts/report_sweep.py --sweep-name ma_opt_v1 --open

    # Nur Text-Summary ohne HTML
    python scripts/report_sweep.py --sweep-name ma_opt_v1 --text-only
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.experiments import EXPERIMENTS_CSV
from src.analytics.explorer import (
    ExperimentExplorer,
    SweepOverview,
    RankedExperiment,
)
from src.reporting.html_reports import HtmlReportBuilder


# =============================================================================
# FORMATIERUNGS-HELPER
# =============================================================================


def format_percent(value: Optional[float], decimals: int = 2) -> str:
    """Formatiert als Prozent oder gibt '-' bei None zurück."""
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "-"


def format_float(value: Optional[float], decimals: int = 3) -> str:
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
# TEXT SUMMARY
# =============================================================================


def print_text_summary(
    overview: SweepOverview,
    top_runs: List[RankedExperiment],
    metric: str,
) -> None:
    """Druckt eine Text-Zusammenfassung des Sweeps."""
    print()
    print("=" * 90)
    print("  SWEEP SUMMARY")
    print("=" * 90)

    print()
    print("--- OVERVIEW ---")
    print(f"  Sweep Name:   {overview.sweep_name}")
    print(f"  Strategy:     {overview.strategy_key}")
    print(f"  Total Runs:   {overview.run_count}")

    if overview.metric_stats:
        print()
        print(f"--- {metric.upper()} STATISTICS ---")
        stats = overview.metric_stats
        print(f"  Min:          {format_float(stats.get('min'))}")
        print(f"  Max:          {format_float(stats.get('max'))}")
        print(f"  Mean:         {format_float(stats.get('mean'))}")
        print(f"  Median:       {format_float(stats.get('median'))}")
        print(f"  Std Dev:      {format_float(stats.get('std'))}")

    if overview.param_ranges:
        print()
        print("--- PARAMETER RANGES ---")
        for param, info in overview.param_ranges.items():
            values = info.get("values", [])
            count = info.get("count", len(values))
            if len(values) <= 5:
                print(f"  {param:<16} [{', '.join(str(v) for v in values)}]")
            else:
                print(f"  {param:<16} [{count} distinct values]")

    if top_runs:
        print()
        print(f"--- TOP {len(top_runs)} RUNS (by {metric}) ---")
        print()

        # Header
        header = f"{'RANK':>4} | {'RUN ID':<12} | {metric.upper():>10} | {'RETURN':>8} | {'MAX DD':>8} | {'PARAMS':<30}"
        print(header)
        print("-" * len(header.replace("|", "+")))

        for r in top_runs:
            s = r.summary
            run_id = truncate(s.experiment_id, 12)
            metric_val = format_float(r.sort_value, 4)
            ret = format_percent(s.metrics.get("total_return"))
            dd = format_percent(s.metrics.get("max_drawdown"))

            # Parameter als String
            if s.params:
                params_str = ", ".join(f"{k}={v}" for k, v in list(s.params.items())[:3])
                params_str = truncate(params_str, 30)
            else:
                params_str = "-"

            print(f"{r.rank:>4} | {run_id:<12} | {metric_val:>10} | {ret:>8} | {dd:>8} | {params_str:<30}")

    print()


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="report_sweep.py",
        description="Peak_Trade: Generiert HTML-Report für einen Sweep.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Sweep-Report generieren
  python scripts/report_sweep.py --sweep-name ma_crossover_opt_v1

  # Mit spezifischer Metrik und Top-N
  python scripts/report_sweep.py --sweep-name ma_opt_v1 --metric sharpe --top-n 20

  # Report im Browser öffnen
  python scripts/report_sweep.py --sweep-name ma_opt_v1 --open

  # Nur Text-Summary
  python scripts/report_sweep.py --sweep-name ma_opt_v1 --text-only

  # Verfügbare Sweeps auflisten
  python scripts/report_sweep.py --list-sweeps
        """,
    )

    parser.add_argument(
        "--sweep-name",
        help="Name des Sweeps",
    )
    parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Ranking (default: sharpe)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Anzahl Top-Runs im Report (default: 20)",
    )
    parser.add_argument(
        "--out-dir",
        default="reports",
        help="Output-Verzeichnis für den Report (default: reports)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Report nach Generierung im Browser öffnen",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Nur Text-Summary ausgeben, kein HTML generieren",
    )
    parser.add_argument(
        "--list-sweeps",
        action="store_true",
        help="Alle verfügbaren Sweeps auflisten",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Report ohne Charts generieren",
    )

    return parser


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Registry-Check
    if not EXPERIMENTS_CSV.exists():
        print(f"\nFEHLER: Keine Experiment-Registry gefunden: {EXPERIMENTS_CSV}")
        print("Führe zuerst einen Backtest oder Sweep aus.\n")
        return 1

    explorer = ExperimentExplorer()

    # Liste der Sweeps anzeigen?
    if args.list_sweeps:
        sweeps = explorer.list_sweeps()
        if not sweeps:
            print("\nKeine Sweeps gefunden.")
        else:
            print(f"\nVerfügbare Sweeps ({len(sweeps)}):")
            print()
            for i, name in enumerate(sweeps, 1):
                print(f"  {i:3}. {name}")
        print()
        return 0

    # Sweep-Name erforderlich
    if not args.sweep_name:
        print("\nFEHLER: --sweep-name erforderlich.")
        print("Verwende --list-sweeps um verfügbare Sweeps anzuzeigen.\n")
        return 1

    # Sweep laden
    print(f"\nLade Sweep: {args.sweep_name}")
    print(f"  Metrik: {args.metric}")
    print(f"  Top-N: {args.top_n}")

    overview = explorer.summarize_sweep(
        args.sweep_name,
        metric=args.metric,
        top_n=args.top_n,
    )

    if overview is None:
        print(f"\nFEHLER: Sweep nicht gefunden: {args.sweep_name}")
        print("Verwende --list-sweeps um verfügbare Sweeps anzuzeigen.\n")
        return 1

    # Text-Summary ausgeben
    print_text_summary(overview, overview.best_runs, args.metric)

    # Nur Text?
    if args.text_only:
        return 0

    # HTML-Report generieren
    print("Generiere HTML-Report...")

    output_dir = Path(args.out_dir)
    builder = HtmlReportBuilder(output_dir=output_dir)

    try:
        report_path = builder.build_sweep_report(
            overview,
            overview.best_runs,
            metric=args.metric,
        )
        print(f"\nReport generiert: {report_path}")
        print(f"  Verzeichnis: {report_path.parent}")

        # Im Browser öffnen?
        if args.open:
            print("Öffne Report im Browser...")
            webbrowser.open(f"file://{report_path.absolute()}")

    except Exception as e:
        print(f"\nFEHLER beim Generieren des Reports: {e}")
        return 1

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
