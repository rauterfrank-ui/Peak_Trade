#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/report_experiment.py
"""
Peak_Trade – Experiment Report Generator (Phase 21)
====================================================
Generiert einen HTML-Report für ein einzelnes Experiment.

Usage:
    # Report für ein Experiment generieren
    python scripts/report_experiment.py --id abc12345-6789-...

    # Mit benutzerdefiniertem Output-Verzeichnis
    python scripts/report_experiment.py --id abc12345 --out-dir reports/my_reports

    # Report automatisch im Browser öffnen
    python scripts/report_experiment.py --id abc12345 --open

    # Nur Text-Summary ohne HTML
    python scripts/report_experiment.py --id abc12345 --text-only
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
from src.analytics.explorer import ExperimentExplorer, ExperimentSummary
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


def format_float(value: Optional[float], decimals: int = 2) -> str:
    """Formatiert Float oder gibt '-' bei None zurück."""
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "-"


# =============================================================================
# TEXT SUMMARY
# =============================================================================


def print_text_summary(summary: ExperimentSummary) -> None:
    """Druckt eine Text-Zusammenfassung des Experiments."""
    print()
    print("=" * 70)
    print("  EXPERIMENT SUMMARY")
    print("=" * 70)

    print()
    print("--- OVERVIEW ---")
    print(f"  Run ID:       {summary.experiment_id}")
    print(f"  Run Type:     {summary.run_type}")
    print(f"  Run Name:     {summary.run_name}")
    if summary.strategy_name:
        print(f"  Strategy:     {summary.strategy_name}")
    if summary.symbol:
        print(f"  Symbol:       {summary.symbol}")
    if summary.created_at:
        print(f"  Created:      {summary.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if summary.sweep_name:
        print(f"  Sweep:        {summary.sweep_name}")
    if summary.tags:
        print(f"  Tags:         {', '.join(summary.tags)}")

    if summary.metrics:
        print()
        print("--- METRICS ---")

        metric_order = [
            ("total_return", "Total Return", True),
            ("sharpe", "Sharpe Ratio", False),
            ("max_drawdown", "Max Drawdown", True),
            ("cagr", "CAGR", True),
            ("sortino", "Sortino Ratio", False),
            ("calmar", "Calmar Ratio", False),
            ("win_rate", "Win Rate", True),
            ("profit_factor", "Profit Factor", False),
            ("total_trades", "Total Trades", False),
        ]

        for key, label, is_percent in metric_order:
            if key in summary.metrics:
                value = summary.metrics[key]
                if key == "total_trades":
                    formatted = str(int(value)) if value else "-"
                elif is_percent:
                    formatted = format_percent(value)
                else:
                    formatted = format_float(value)
                print(f"  {label:<16} {formatted:>12}")

    if summary.params:
        print()
        print("--- PARAMETERS ---")
        for key, value in summary.params.items():
            print(f"  {key:<16} {value}")

    print()


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="report_experiment.py",
        description="Peak_Trade: Generiert HTML-Report für ein Experiment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Report generieren
  python scripts/report_experiment.py --id abc12345-6789-...

  # Mit benutzerdefiniertem Output-Verzeichnis
  python scripts/report_experiment.py --id abc12345 --out-dir reports/custom

  # Report im Browser öffnen
  python scripts/report_experiment.py --id abc12345 --open

  # Nur Text-Summary
  python scripts/report_experiment.py --id abc12345 --text-only
        """,
    )

    parser.add_argument(
        "--id",
        required=True,
        help="Run-ID des Experiments (UUID)",
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
        print("Führe zuerst einen Backtest aus, um Experiments zu erzeugen.\n")
        return 1

    # Experiment laden
    print(f"\nLade Experiment: {args.id}")
    explorer = ExperimentExplorer()
    summary = explorer.get_experiment_details(args.id)

    if summary is None:
        print(f"\nFEHLER: Experiment nicht gefunden: {args.id}")
        print("Hinweis: Die Run-ID muss exakt übereinstimmen (vollständige UUID).\n")
        return 1

    # Text-Summary ausgeben
    print_text_summary(summary)

    # Nur Text?
    if args.text_only:
        return 0

    # HTML-Report generieren
    print("Generiere HTML-Report...")

    output_dir = Path(args.out_dir)
    builder = HtmlReportBuilder(output_dir=output_dir)

    # Equity-Kurve laden (falls verfügbar)
    # Hinweis: Equity-Kurve ist nicht direkt in ExperimentSummary,
    # müsste aus separater Quelle geladen werden (z.B. CSV-Export)
    equity_curve = None

    try:
        report_path = builder.build_experiment_report(
            summary,
            equity_curve=equity_curve if not args.no_charts else None,
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
