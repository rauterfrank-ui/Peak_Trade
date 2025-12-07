#!/usr/bin/env python3
"""
Peak_Trade – Generate Experiment/Sweep Report (Phase 30)
=========================================================

CLI-Script zur Generierung von Experiment/Sweep-Reports im Markdown-Format.

Usage:
    # Basic usage
    python scripts/generate_experiment_report.py \\
        --input results/rsi_reversion_sweep.parquet \\
        --output reports/rsi_reversion_sweep_report.md

    # With sorting and top-N
    python scripts/generate_experiment_report.py \\
        --input results/ma_sweep.csv \\
        --output reports/ma_sweep_report.md \\
        --sort-metric metric_sharpe \\
        --top-n 30

    # With heatmap visualization
    python scripts/generate_experiment_report.py \\
        --input results/rsi_sweep.parquet \\
        --output reports/rsi_sweep.md \\
        --heatmap-params param_rsi_window param_lower_threshold

    # HTML output
    python scripts/generate_experiment_report.py \\
        --input results/sweep.parquet \\
        --output reports/sweep.html \\
        --format html

Examples:
    # MA Crossover sweep analysis
    python scripts/generate_experiment_report.py \\
        --input reports/experiments/ma_crossover_sweep.csv \\
        --output reports/ma_crossover_analysis.md \\
        --sort-metric metric_sharpe \\
        --top-n 20 \\
        --heatmap-params param_fast_period param_slow_period

    # RSI strategy optimization
    python scripts/generate_experiment_report.py \\
        --input results/rsi_optimization.parquet \\
        --output reports/rsi_optimization.md \\
        --sort-metric metric_total_return \\
        --ascending
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd

# Füge src zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporting.experiment_report import (
    build_experiment_report,
    save_experiment_report,
    load_experiment_results,
    summarize_experiment_results,
)


def parse_args() -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Generate Experiment/Sweep Report from results file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to experiment results file (CSV or Parquet)",
    )

    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for the report (.md or .html)",
    )

    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Report title (default: derived from filename)",
    )

    parser.add_argument(
        "--sort-metric",
        type=str,
        default="metric_sharpe",
        help="Metric to sort by (default: metric_sharpe)",
    )

    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Sort ascending (for metrics where lower is better, e.g., max_drawdown)",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of top runs to show (default: 20)",
    )

    parser.add_argument(
        "--heatmap-params",
        type=str,
        nargs=2,
        default=None,
        metavar=("PARAM1", "PARAM2"),
        help="Two parameter column names for 2D heatmap visualization",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    parser.add_argument(
        "--images-dir",
        type=str,
        default=None,
        help="Directory for plot images (default: <output_dir>/images)",
    )

    parser.add_argument(
        "--with-regime-heatmaps",
        action="store_true",
        help="Include regime-aware heatmaps for regime_aware_* sweeps",
    )

    return parser.parse_args()


def validate_columns(df: pd.DataFrame, sort_metric: str, heatmap_params: Tuple[str, str] | None) -> None:
    """Validiert, dass benötigte Spalten existieren."""
    # Check sort metric
    if sort_metric not in df.columns:
        # Versuche ohne Prefix
        possible = [c for c in df.columns if sort_metric.replace("metric_", "") in c]
        if possible:
            print(f"Warning: '{sort_metric}' not found, did you mean: {possible}?")
        else:
            print(f"Warning: Sort metric '{sort_metric}' not found in data")
            print(f"  Available metric columns: {[c for c in df.columns if c.startswith('metric_')]}")

    # Check heatmap params
    if heatmap_params:
        for param in heatmap_params:
            if param not in df.columns:
                possible = [c for c in df.columns if param.replace("param_", "") in c]
                if possible:
                    print(f"Warning: '{param}' not found, did you mean: {possible}?")
                else:
                    print(f"Warning: Heatmap parameter '{param}' not found in data")
                    print(f"  Available param columns: {[c for c in df.columns if c.startswith('param_')]}")


def print_data_overview(df: pd.DataFrame) -> None:
    """Gibt Übersicht über geladene Daten aus."""
    param_cols = [c for c in df.columns if c.startswith("param_")]
    metric_cols = [c for c in df.columns if c.startswith("metric_")]

    print("\n--- Data Overview ---")
    print(f"Total runs: {len(df)}")
    print(f"Parameter columns ({len(param_cols)}):")
    for col in param_cols[:10]:
        unique = df[col].nunique()
        print(f"  {col}: {unique} unique values")
    if len(param_cols) > 10:
        print(f"  ... and {len(param_cols) - 10} more")

    print(f"\nMetric columns ({len(metric_cols)}):")
    for col in metric_cols[:10]:
        if df[col].dtype in ["float64", "int64"]:
            print(f"  {col}: min={df[col].min():.4f}, max={df[col].max():.4f}, mean={df[col].mean():.4f}")
        else:
            print(f"  {col}: {df[col].dtype}")
    if len(metric_cols) > 10:
        print(f"  ... and {len(metric_cols) - 10} more")


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Validierung
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Lade Results
    print(f"Loading results from {input_path}...")
    try:
        df = load_experiment_results(input_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return 1

    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    if len(df) == 0:
        print("Error: No data in results file")
        return 1

    # Zeige Übersicht
    print_data_overview(df)

    # Validiere Spalten
    heatmap_params = tuple(args.heatmap_params) if args.heatmap_params else None
    validate_columns(df, args.sort_metric, heatmap_params)

    # Title
    title = args.title
    if not title:
        stem = input_path.stem.replace("_", " ").title()
        title = f"Experiment Report: {stem}"

    # Images directory
    images_dir = args.images_dir
    if images_dir:
        images_dir = Path(images_dir)
    else:
        images_dir = output_path.parent / "images"

    # Baue Report
    print(f"\nBuilding report...")
    report = build_experiment_report(
        title=title,
        df=df,
        sort_metric=args.sort_metric,
        ascending=args.ascending,
        top_n=args.top_n,
        heatmap_params=heatmap_params,
        output_dir=images_dir,
        metadata={
            "source_file": str(input_path),
        },
        with_regime_heatmaps=args.with_regime_heatmaps,
    )

    # Speichere Report
    output_format = args.format
    if output_path.suffix == ".html":
        output_format = "html"

    save_experiment_report(report, output_path, format=output_format)
    print(f"\nReport saved to: {output_path}")

    # Summary
    summary = summarize_experiment_results(df, top_n=args.top_n, sort_metric=args.sort_metric, ascending=args.ascending)

    print("\n--- Report Summary ---")
    print(f"Title: {title}")
    print(f"Sections: {len(report.sections)}")
    print(f"Sort metric: {args.sort_metric}")
    print(f"Top N: {args.top_n}")

    if "top_runs" in summary and len(summary["top_runs"]) > 0:
        print(f"\nTop 3 runs by {args.sort_metric}:")
        top3 = summary["top_runs"].head(3)
        for idx, row in top3.iterrows():
            val = row.get(args.sort_metric, "N/A")
            params = {k.replace("param_", ""): v for k, v in row.items() if k.startswith("param_")}
            print(f"  #{row.get('rank', idx)}: {args.sort_metric}={val:.4f} | {params}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
