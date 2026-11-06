#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/list_experiments.py
"""
Peak_Trade – Experiment-Liste anzeigen
======================================
Zeigt eine tabellarische Übersicht über Registry-Runs.

Usage:
    # Alle Experiments (Standard: letzte 20)
    python scripts/list_experiments.py

    # Nur Backtests
    python scripts/list_experiments.py --run-type backtest

    # Mit Tag-Filter
    python scripts/list_experiments.py --tag dev-test

    # Mehr Ergebnisse
    python scripts/list_experiments.py --limit 50
"""

from __future__ import annotations

import sys
import argparse
import json
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.experiments import EXPERIMENTS_CSV, VALID_RUN_TYPES


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Experimente (Runs) aus der Registry listen/filtern.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/list_experiments.py
  python scripts/list_experiments.py --run-type backtest
  python scripts/list_experiments.py --tag phase2-test --limit 10
  python scripts/list_experiments.py --sort-by sharpe
        """,
    )
    parser.add_argument(
        "--run-type",
        choices=VALID_RUN_TYPES,
        help=f"Filter nach run_type. Optionen: {', '.join(VALID_RUN_TYPES)}",
    )
    parser.add_argument(
        "--tag",
        help="Filter nach Tag im metadata_json (z.B. 'dev-test').",
    )
    parser.add_argument(
        "--strategy",
        help="Filter nach strategy_key.",
    )
    parser.add_argument(
        "--symbol",
        help="Filter nach symbol.",
    )
    parser.add_argument(
        "--portfolio",
        help="Filter nach portfolio_name.",
    )
    parser.add_argument(
        "--sweep-name",
        help="Filter nach sweep_name.",
    )
    parser.add_argument(
        "--scan-name",
        help="Filter nach scan_name.",
    )
    parser.add_argument(
        "--sort-by",
        default="timestamp",
        help=(
            "Spalte, nach der sortiert werden soll "
            "(z.B. sharpe, total_return, cagr, max_drawdown, timestamp). Default: timestamp"
        ),
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (Standard: absteigend).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximale Anzahl Zeilen in der Ausgabe (Default: 20).",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Alias für --limit (Rückwärtskompatibilität).",
    )
    return parser.parse_args(argv)


def get_tag_from_metadata(metadata_json: str) -> Optional[str]:
    """Extrahiert Tag aus metadata_json."""
    try:
        meta = json.loads(metadata_json)
        return meta.get("tag")
    except (json.JSONDecodeError, TypeError):
        return None


def format_percent(value) -> str:
    """Formatiert als Prozent oder gibt '-' bei None zurück."""
    if pd.isna(value) or value is None:
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return "-"


def format_float(value, decimals: int = 2) -> str:
    """Formatiert Float oder gibt '-' bei None zurück."""
    if pd.isna(value) or value is None:
        return "-"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "-"


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    csv_path = EXPERIMENTS_CSV
    if not csv_path.is_file():
        print(f"\nKeine Experiment-Registry gefunden: {csv_path}")
        print("Führe zuerst einen Backtest aus, um Experiments zu erzeugen.\n")
        return

    df = pd.read_csv(csv_path)

    # Limit bestimmen (--max-rows hat Vorrang für Rückwärtskompatibilität)
    limit = args.max_rows if args.max_rows is not None else args.limit

    # Filter anwenden
    if args.run_type:
        df = df[df["run_type"] == args.run_type]

    if args.strategy:
        df = df[df["strategy_key"] == args.strategy]

    if args.symbol:
        df = df[df["symbol"] == args.symbol]

    if args.portfolio:
        df = df[df["portfolio_name"] == args.portfolio]

    if args.sweep_name:
        df = df[df["sweep_name"] == args.sweep_name]

    if args.scan_name:
        df = df[df["scan_name"] == args.scan_name]

    # Tag-Filter (aus metadata_json)
    if args.tag:
        df["_tag"] = df["metadata_json"].apply(get_tag_from_metadata)
        df = df[df["_tag"] == args.tag]
        df = df.drop(columns=["_tag"])

    # Sortierung
    if args.sort_by and args.sort_by in df.columns:
        df = df.sort_values(by=args.sort_by, ascending=args.ascending)

    # Limit anwenden
    if limit > 0:
        df = df.head(limit)

    if df.empty:
        print("\nKeine Experimente mit diesen Filtern gefunden.\n")
        return

    # Header
    print("\n" + "=" * 100)
    print("  Peak_Trade Experiment Registry")
    print("=" * 100)

    # Filter-Info
    filters = []
    if args.run_type:
        filters.append(f"run_type={args.run_type}")
    if args.tag:
        filters.append(f"tag={args.tag}")
    if args.strategy:
        filters.append(f"strategy={args.strategy}")
    if filters:
        print(f"  Filter: {', '.join(filters)}")
    print(f"  Sortiert nach: {args.sort_by} ({'asc' if args.ascending else 'desc'})")
    print(f"  Limit: {limit}")
    print()

    # Kompakte tabellarische Ausgabe
    print(
        f"{'RUN_ID':<36} | {'TYPE':<18} | {'STRATEGY':<15} | {'RETURN':>8} | {'SHARPE':>7} | {'TIMESTAMP':<20}"
    )
    print(
        "-" * 36
        + "-+-"
        + "-" * 18
        + "-+-"
        + "-" * 15
        + "-+-"
        + "-" * 8
        + "-+-"
        + "-" * 7
        + "-+-"
        + "-" * 20
    )

    for _, row in df.iterrows():
        run_id = str(row.get("run_id", "-"))[:36]
        run_type = str(row.get("run_type", "-"))[:18]
        strategy = str(row.get("strategy_key", "-") or "-")[:15]
        total_return = format_percent(row.get("total_return"))
        sharpe = format_float(row.get("sharpe"))
        timestamp = str(row.get("timestamp", "-"))[:20]

        print(
            f"{run_id:<36} | {run_type:<18} | {strategy:<15} | {total_return:>8} | {sharpe:>7} | {timestamp:<20}"
        )

    print()
    print(f"Gefunden: {len(df)} Experiment(s)")
    print()


if __name__ == "__main__":
    main()
