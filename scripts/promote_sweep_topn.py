#!/usr/bin/env python3
"""
Peak_Trade Top-N Promotion CLI (Phase 42)
=========================================

Exportiert die Top-N Konfigurationen aus Sweep-Ergebnissen in TOML-Format.

Verwendung:
    # Top-5 nach Sharpe-Ratio
    python scripts/promote_sweep_topn.py --sweep-name rsi_reversion_basic

    # Top-10 nach Total Return
    python scripts/promote_sweep_topn.py \
        --sweep-name breakout_basic \
        --metric metric_total_return \
        --top-n 10

    # Mit Fallback-Metrik
    python scripts/promote_sweep_topn.py \
        --sweep-name ma_crossover_basic \
        --metric metric_sharpe_ratio \
        --fallback-metric metric_total_return \
        --top-n 5

Output:
    - reports/sweeps/{sweep_name}_top_candidates.toml
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.experiments.topn_promotion import (
    TopNPromotionConfig,
    load_sweep_results,
    select_top_n,
    export_top_n,
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
    """Erstellt den ArgumentParser für Top-N Promotion."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Top-N Promotion CLI (Phase 42)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Sweep-Auswahl
    parser.add_argument(
        "--sweep-name",
        "-s",
        type=str,
        required=True,
        help="Name des Sweeps (z.B. rsi_reversion_basic)",
    )

    # Metrik-Optionen
    parser.add_argument(
        "--metric",
        "-m",
        type=str,
        default="metric_sharpe_ratio",
        help="Primäre Metrik für Sortierung (default: metric_sharpe_ratio)",
    )
    parser.add_argument(
        "--fallback-metric",
        "-f",
        type=str,
        default="metric_total_return",
        help="Fallback-Metrik falls primary fehlt (default: metric_total_return)",
    )

    # Top-N
    parser.add_argument(
        "--top-n",
        "-n",
        type=int,
        default=5,
        help="Anzahl der Top-Konfigurationen (default: 5)",
    )

    # Output-Optionen
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="reports/sweeps",
        help="Ausgabe-Verzeichnis (default: reports/sweeps)",
    )
    parser.add_argument(
        "--experiments-dir",
        "-e",
        type=str,
        default="reports/experiments",
        help="Verzeichnis mit Experiment-Ergebnissen (default: reports/experiments)",
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


def format_params_summary(row: dict, param_cols: list) -> str:
    """
    Formatiert Parameter als kompakte Zusammenfassung.

    Args:
        row: DataFrame-Zeile als Dict
        param_cols: Liste der Parameter-Spalten

    Returns:
        Formatierter String (z.B. "rsi_period=14, oversold=30, overbought=70")
    """
    params = []
    for col in param_cols[:5]:  # Max. 5 Parameter für Übersicht
        key = col.replace("param_", "")
        val = row.get(col)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            params.append(f"{key}={val}")
    return ", ".join(params)


def run_from_args(args: argparse.Namespace) -> int:
    """Führt Top-N Promotion basierend auf Argumenten aus.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Erstelle Config
    config = TopNPromotionConfig(
        sweep_name=args.sweep_name,
        metric_primary=args.metric,
        metric_fallback=args.fallback_metric,
        top_n=args.top_n,
        output_path=Path(args.output),
        experiments_dir=Path(args.experiments_dir),
    )

    try:
        # Lade Ergebnisse
        logger.info(f"Lade Sweep-Ergebnisse für '{config.sweep_name}'...")
        df = load_sweep_results(config)

        # Wähle Top-N
        logger.info(f"Wähle Top {config.top_n} nach Metrik '{config.metric_primary}'...")
        df_top, metric_used = select_top_n(df, config)

        # Exportiere
        output_path = export_top_n(df_top, config)

        # Summary ausgeben
        print("\n" + "=" * 70)
        print("Top-N Promotion Summary")
        print("=" * 70)
        print(f"Sweep:           {config.sweep_name}")
        print(f"Metric:          {metric_used}")
        print(f"Top N:           {len(df_top)}")
        print(f"Output:          {output_path}")
        print("\nTop Konfigurationen:")
        print("-" * 70)

        # Extrahiere Spalten für Anzeige
        metric_cols = [c for c in df_top.columns if c.startswith("metric_")]
        param_cols = [c for c in df_top.columns if c.startswith("param_")]

        # Verwende die tatsächlich verwendete Metrik aus select_top_n
        used_metric = metric_used

        # Header
        header_parts = ["Rank"]
        if used_metric in df_top.columns:
            metric_display = used_metric.replace("metric_", "")
            header_parts.append(metric_display[:10].ljust(10))
        if "metric_total_return" in df_top.columns and used_metric != "metric_total_return":
            header_parts.append("Return")
        header_parts.append("Params")
        print("  ".join(f"{h:<15}" for h in header_parts))
        print("-" * 70)

        # Zeilen
        for _, row in df_top.iterrows():
            parts = [f"{int(row['rank']):<15}"]
            if used_metric in df_top.columns:
                val = row[used_metric]
                parts.append(f"{val:>10.4f}" if pd.notna(val) else "       nan")
            if "metric_total_return" in df_top.columns and used_metric != "metric_total_return":
                val = row["metric_total_return"]
                parts.append(f"{val * 100:>6.2f}%" if pd.notna(val) else "  nan%")
            # Parameter-Zusammenfassung
            params_str = format_params_summary(row.to_dict(), param_cols)
            if len(params_str) > 40:
                params_str = params_str[:37] + "..."
            parts.append(params_str)
            print("  ".join(parts))

        print("=" * 70)
        print(f"\n✅ Top-N Kandidaten exportiert: {output_path}")
        return 0

    except FileNotFoundError as e:
        print(f"❌ Fehler: {e}")
        print(f"\nTipp: Führe zuerst einen Sweep aus:")
        print(f"  python scripts/run_strategy_sweep.py --sweep-name {config.sweep_name}")
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
