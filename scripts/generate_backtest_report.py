#!/usr/bin/env python3
"""
Peak_Trade – Generate Backtest Report (Phase 30)
=================================================

CLI-Script zur Generierung von Backtest-Reports im Markdown-Format.

Usage:
    # Aus gespeichertem Result (Parquet/CSV)
    python scripts/generate_backtest_report.py \\
        --results-file results/btc_ma_crossover.parquet \\
        --output reports/btc_ma_crossover.md

    # Mit Equity-Curve aus separater Datei
    python scripts/generate_backtest_report.py \\
        --results-file results/stats.csv \\
        --equity-file results/equity.parquet \\
        --output reports/backtest_report.md

    # HTML-Output
    python scripts/generate_backtest_report.py \\
        --results-file results/btc_ma_crossover.parquet \\
        --output reports/report.html \\
        --format html

Examples:
    # Quick report from recent backtest
    python scripts/generate_backtest_report.py \\
        --results-file reports/experiments/ma_crossover_abc123.csv \\
        --output reports/ma_crossover_report.md

    # With custom title
    python scripts/generate_backtest_report.py \\
        --results-file results/rsi_btc.parquet \\
        --output reports/rsi_btc.md \\
        --title "RSI Strategy - BTC/EUR Backtest"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Füge src zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporting.backtest_report import (
    build_backtest_report,
    save_backtest_report,
)
from src.backtest.stats import compute_drawdown


def parse_args() -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Generate Backtest Report from results file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--results-file",
        type=str,
        required=True,
        help="Path to results file (CSV or Parquet) with metrics",
    )

    parser.add_argument(
        "--equity-file",
        type=str,
        default=None,
        help="Optional: Path to equity curve file (Parquet/CSV with 'equity' column)",
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

    return parser.parse_args()


def load_results(filepath: Path) -> pd.DataFrame:
    """Lädt Results aus CSV oder Parquet."""
    if filepath.suffix == ".parquet":
        return pd.read_parquet(filepath)
    elif filepath.suffix == ".csv":
        return pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def load_equity(filepath: Path) -> pd.Series | None:
    """Lädt Equity-Curve aus Datei."""
    try:
        if filepath.suffix == ".parquet":
            df = pd.read_parquet(filepath)
        else:
            df = pd.read_csv(filepath)

        # Finde Equity-Spalte
        for col in ["equity", "Equity", "portfolio_value", "value"]:
            if col in df.columns:
                # Versuche Index als Datetime zu parsen
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    return pd.Series(df[col].values, index=df["timestamp"])
                elif "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    return pd.Series(df[col].values, index=df["date"])
                else:
                    return df[col]

        print(f"Warning: No equity column found in {filepath}")
        return None

    except Exception as e:
        print(f"Warning: Could not load equity from {filepath}: {e}")
        return None


def extract_metrics(df: pd.DataFrame) -> dict:
    """
    Extrahiert Metriken aus Results DataFrame.

    Unterstützt verschiedene Formate:
    - Einzelne Zeile mit Metrik-Spalten
    - Stats-Dict als JSON-Spalte
    - Metric-prefixed Spalten
    """
    metrics = {}

    if len(df) == 0:
        return metrics

    # Wenn nur eine Zeile, nimm alle numerischen Spalten
    if len(df) == 1:
        row = df.iloc[0]
        for col in df.columns:
            val = row[col]
            # Numerische Werte übernehmen
            if isinstance(val, (int, float)) and not pd.isna(val):
                # Entferne Prefixes
                key = col.replace("metric_", "").replace("stats_", "")
                metrics[key] = float(val)
    else:
        # Mehrere Zeilen: versuche metric_* Spalten
        metric_cols = [c for c in df.columns if c.startswith("metric_")]
        if metric_cols:
            # Nimm Mittelwerte
            for col in metric_cols:
                key = col.replace("metric_", "")
                metrics[key] = df[col].mean()
        else:
            # Versuche direkt numerische Spalten
            for col in df.select_dtypes(include=["number"]).columns:
                metrics[col] = df[col].mean()

    return metrics


def extract_params(df: pd.DataFrame) -> dict:
    """Extrahiert Parameter aus Results DataFrame."""
    params = {}

    if len(df) == 0:
        return params

    row = df.iloc[0]

    # param_* Spalten
    param_cols = [c for c in df.columns if c.startswith("param_")]
    for col in param_cols:
        key = col.replace("param_", "")
        val = row[col]
        if not pd.isna(val):
            params[key] = val

    # Andere bekannte Parameter-Spalten
    for col in ["strategy_name", "symbol", "timeframe"]:
        if col in df.columns and not pd.isna(row[col]):
            params[col] = row[col]

    return params


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    results_path = Path(args.results_file)
    output_path = Path(args.output)

    # Validierung
    if not results_path.exists():
        print(f"Error: Results file not found: {results_path}")
        return 1

    # Lade Results
    print(f"Loading results from {results_path}...")
    df = load_results(results_path)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # Extrahiere Metriken und Parameter
    metrics = extract_metrics(df)
    params = extract_params(df)

    if not metrics:
        print("Warning: No metrics found in results file")

    # Lade Equity (optional)
    equity = None
    drawdown = None

    if args.equity_file:
        equity_path = Path(args.equity_file)
        if equity_path.exists():
            print(f"Loading equity from {equity_path}...")
            equity = load_equity(equity_path)
            if equity is not None:
                drawdown = compute_drawdown(equity)
                print(f"  Equity curve: {len(equity)} points")

    # Title
    title = args.title
    if not title:
        # Derive from filename
        stem = results_path.stem.replace("_", " ").title()
        title = f"Backtest Report: {stem}"

    # Images directory
    images_dir = args.images_dir
    if images_dir:
        images_dir = Path(images_dir)
    else:
        images_dir = output_path.parent / "images"

    # Baue Report
    print(f"Building report...")
    report = build_backtest_report(
        title=title,
        metrics=metrics,
        equity_curve=equity,
        drawdown_series=drawdown,
        params=params if params else None,
        output_dir=images_dir,
        metadata={
            "source_file": str(results_path),
        },
    )

    # Speichere Report
    output_format = args.format
    if output_path.suffix == ".html":
        output_format = "html"

    save_backtest_report(report, output_path, format=output_format)
    print(f"Report saved to: {output_path}")

    # Summary
    print("\n--- Report Summary ---")
    print(f"Title: {title}")
    print(f"Metrics: {len(metrics)}")
    print(f"Parameters: {len(params)}")
    print(f"Sections: {len(report.sections)}")

    if metrics:
        print("\nKey Metrics:")
        for key in ["total_return", "sharpe", "max_drawdown", "win_rate"]:
            if key in metrics:
                print(f"  {key}: {metrics[key]:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
