#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/analyze_experiments.py
"""
Peak_Trade – Experiment-Analyse CLI
===================================
CLI-Tool für Aggregationen und Analysen der Experiment-Registry.

Modi:
    - summary: Strategie-Übersicht mit Durchschnittswerten
    - top-runs: Top-N Runs nach Metrik
    - portfolios: Portfolio-Backtests analysieren
    - compare: Strategien vergleichen

Usage:
    # Strategie-Übersicht (Backtests)
    python scripts/analyze_experiments.py --mode summary --run-type backtest

    # Top 10 Backtests nach Sharpe
    python scripts/analyze_experiments.py --mode top-runs --metric sharpe --limit 10

    # Portfolio-Runs analysieren
    python scripts/analyze_experiments.py --mode portfolios --metric total_return --limit 10

    # Strategien vergleichen
    python scripts/analyze_experiments.py --mode compare --strategies ma_crossover,rsi_reversion

    # Markdown-Report schreiben
    python scripts/analyze_experiments.py --mode summary --run-type backtest --write-report reports/strategy_summary.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.experiments import VALID_RUN_TYPES
from src.analytics.experiments_analysis import (
    StrategySummary,
    PortfolioSummary,
    load_experiments_df_filtered,
    filter_backtest_runs,
    filter_portfolio_backtest_runs,
    summarize_strategies,
    summarize_portfolios,
    top_runs_by_metric,
    compare_strategies,
    write_markdown_report,
    write_portfolio_markdown_report,
    write_top_runs_markdown_report,
)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Experiment-Analyse und Aggregationen.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modi:
    summary     - Strategie-Übersicht mit Durchschnittswerten
    top-runs    - Top-N Runs nach Metrik (z.B. Sharpe, Return)
    portfolios  - Portfolio-Backtests analysieren
    compare     - Strategien vergleichen

Beispiele:
    python scripts/analyze_experiments.py --mode summary --run-type backtest
    python scripts/analyze_experiments.py --mode top-runs --metric sharpe --limit 10
    python scripts/analyze_experiments.py --mode portfolios --limit 10
    python scripts/analyze_experiments.py --mode compare --strategies ma_crossover,rsi_reversion
    python scripts/analyze_experiments.py --mode summary --run-type backtest --write-report reports/summary.md
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["summary", "top-runs", "portfolios", "compare"],
        default="summary",
        help="Analyse-Modus (Default: summary)",
    )

    parser.add_argument(
        "--run-type",
        choices=VALID_RUN_TYPES,
        default=None,
        help="Filter nach run_type (z.B. backtest, portfolio_backtest)",
    )

    parser.add_argument(
        "--strategy",
        default=None,
        help="Filter nach strategy_key (z.B. ma_crossover)",
    )

    parser.add_argument(
        "--strategies",
        default=None,
        help="Komma-separierte Liste von Strategien für Vergleich (z.B. ma_crossover,rsi_reversion)",
    )

    parser.add_argument(
        "--symbol",
        default=None,
        help="Filter nach Symbol (z.B. BTC/EUR)",
    )

    parser.add_argument(
        "--tag",
        default=None,
        help="Filter nach Tag aus Metadata",
    )

    parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Sortierung/Analyse (z.B. sharpe, total_return, max_drawdown). Default: sharpe",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximale Anzahl Ergebnisse (Default: 20)",
    )

    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (Default: absteigend)",
    )

    parser.add_argument(
        "--write-report",
        default=None,
        help="Pfad für Markdown-Report (z.B. reports/summary.md)",
    )

    return parser.parse_args(argv)


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


def print_strategy_summaries(summaries: List[StrategySummary]) -> None:
    """Druckt Strategie-Übersicht tabellarisch."""
    print()
    print(f"{'STRATEGY':<20} | {'RUNS':>5} | {'AVG RETURN':>10} | {'AVG SHARPE':>10} | {'AVG MAX DD':>10} | {'BEST RUN':<12}")
    print("-" * 20 + "-+-" + "-" * 5 + "-+-" + "-" * 10 + "-+-" + "-" * 10 + "-+-" + "-" * 10 + "-+-" + "-" * 12)

    for s in summaries:
        avg_ret = format_percent(s.avg_total_return)
        avg_sh = format_float(s.avg_sharpe)
        avg_dd = format_percent(s.avg_max_drawdown)
        best_id = s.best_run_id[:12] if s.best_run_id else "-"

        print(f"{s.strategy_key:<20} | {s.run_count:>5} | {avg_ret:>10} | {avg_sh:>10} | {avg_dd:>10} | {best_id:<12}")

    print()


def print_portfolio_summaries(summaries: List[PortfolioSummary]) -> None:
    """Druckt Portfolio-Übersicht tabellarisch."""
    print()
    print(f"{'PORTFOLIO':<20} | {'RUNS':>5} | {'AVG RETURN':>10} | {'AVG SHARPE':>10} | {'AVG MAX DD':>10} | {'BEST RUN':<12}")
    print("-" * 20 + "-+-" + "-" * 5 + "-+-" + "-" * 10 + "-+-" + "-" * 10 + "-+-" + "-" * 10 + "-+-" + "-" * 12)

    for s in summaries:
        avg_ret = format_percent(s.avg_total_return)
        avg_sh = format_float(s.avg_sharpe)
        avg_dd = format_percent(s.avg_max_drawdown)
        best_id = s.best_run_id[:12] if s.best_run_id else "-"

        print(f"{s.portfolio_name:<20} | {s.run_count:>5} | {avg_ret:>10} | {avg_sh:>10} | {avg_dd:>10} | {best_id:<12}")

    print()


def print_top_runs(df: pd.DataFrame, metric: str) -> None:
    """Druckt Top-Runs tabellarisch."""
    print()
    print(f"{'RANK':>4} | {'RUN_ID':<12} | {'TYPE':<18} | {'STRATEGY':<15} | {'RETURN':>8} | {'SHARPE':>7} | {'MAX DD':>8}")
    print("-" * 4 + "-+-" + "-" * 12 + "-+-" + "-" * 18 + "-+-" + "-" * 15 + "-+-" + "-" * 8 + "-+-" + "-" * 7 + "-+-" + "-" * 8)

    for rank, (_, row) in enumerate(df.iterrows(), 1):
        run_id = str(row.get("run_id", "-"))[:12]
        run_type = str(row.get("run_type", "-"))[:18]
        strategy = str(row.get("strategy_key", "-") or "-")[:15]
        total_ret = format_percent(row.get("total_return"))
        sharpe = format_float(row.get("sharpe"))
        max_dd = format_percent(row.get("max_drawdown"))

        print(f"{rank:>4} | {run_id:<12} | {run_type:<18} | {strategy:<15} | {total_ret:>8} | {sharpe:>7} | {max_dd:>8}")

    print()


def print_comparison(df: pd.DataFrame) -> None:
    """Druckt Strategie-Vergleich tabellarisch."""
    print()
    print(f"{'STRATEGY':<20} | {'RUNS':>5} | {'AVG RETURN':>10} | {'STD RETURN':>10} | {'AVG SHARPE':>10} | {'STD SHARPE':>10}")
    print("-" * 20 + "-+-" + "-" * 5 + "-+-" + "-" * 10 + "-+-" + "-" * 10 + "-+-" + "-" * 10 + "-+-" + "-" * 10)

    for _, row in df.iterrows():
        strat = str(row.get("strategy_key", "-"))[:20]
        runs = int(row.get("run_count", 0))
        avg_ret = format_percent(row.get("avg_total_return"))
        std_ret = format_percent(row.get("std_total_return"))
        avg_sh = format_float(row.get("avg_sharpe"))
        std_sh = format_float(row.get("std_sharpe"))

        print(f"{strat:<20} | {runs:>5} | {avg_ret:>10} | {std_ret:>10} | {avg_sh:>10} | {std_sh:>10}")

    print()


def mode_summary(args: argparse.Namespace) -> int:
    """Strategie-Übersicht."""
    print("\n" + "=" * 90)
    print("  Peak_Trade – Strategie-Analyse")
    print("=" * 90)

    # Filter vorbereiten
    run_types = [args.run_type] if args.run_type else None
    strategy_keys = [args.strategy] if args.strategy else None
    symbols = [args.symbol] if args.symbol else None
    tags = [args.tag] if args.tag else None

    try:
        df = load_experiments_df_filtered(
            run_types=run_types,
            strategy_keys=strategy_keys,
            symbols=symbols,
            tags=tags,
        )
    except FileNotFoundError as e:
        print(f"\nFEHLER: {e}")
        return 1

    if df.empty:
        print("\nKeine Experiments mit diesen Filtern gefunden.")
        return 0

    # Filter-Info
    filters = []
    if args.run_type:
        filters.append(f"run_type={args.run_type}")
    if args.strategy:
        filters.append(f"strategy={args.strategy}")
    if args.symbol:
        filters.append(f"symbol={args.symbol}")
    if args.tag:
        filters.append(f"tag={args.tag}")

    if filters:
        print(f"\nFilter: {', '.join(filters)}")
    print(f"Gefunden: {len(df)} Experiment(s)")

    # Zusammenfassung berechnen
    summaries = summarize_strategies(df)

    if not summaries:
        print("\nKeine Strategien mit auswertbaren Daten gefunden.")
        return 0

    print_strategy_summaries(summaries)

    # Optional: Report schreiben
    if args.write_report:
        report_path = Path(args.write_report)
        write_markdown_report(
            summaries,
            report_path,
            title="Peak_Trade Strategy Report",
            run_type=args.run_type,
        )
        print(f"Markdown-Report geschrieben: {report_path}")

    return 0


def mode_top_runs(args: argparse.Namespace) -> int:
    """Top-Runs nach Metrik."""
    print("\n" + "=" * 90)
    print(f"  Peak_Trade – Top Runs nach {args.metric}")
    print("=" * 90)

    run_types = [args.run_type] if args.run_type else None
    strategy_keys = [args.strategy] if args.strategy else None
    symbols = [args.symbol] if args.symbol else None
    tags = [args.tag] if args.tag else None

    try:
        df = load_experiments_df_filtered(
            run_types=run_types,
            strategy_keys=strategy_keys,
            symbols=symbols,
            tags=tags,
        )
    except FileNotFoundError as e:
        print(f"\nFEHLER: {e}")
        return 1

    if df.empty:
        print("\nKeine Experiments mit diesen Filtern gefunden.")
        return 0

    # Top-Runs berechnen
    top_df = top_runs_by_metric(
        df,
        metric=args.metric,
        n=args.limit,
        ascending=args.ascending,
    )

    if top_df.empty:
        print(f"\nKeine Runs mit Metrik '{args.metric}' gefunden.")
        return 0

    print(f"\nTop {len(top_df)} Runs nach {args.metric} ({'asc' if args.ascending else 'desc'})")
    print_top_runs(top_df, args.metric)

    # Optional: Report schreiben
    if args.write_report:
        report_path = Path(args.write_report)
        write_top_runs_markdown_report(
            top_df,
            report_path,
            title=f"Peak_Trade Top Runs ({args.metric})",
            metric=args.metric,
        )
        print(f"Markdown-Report geschrieben: {report_path}")

    return 0


def mode_portfolios(args: argparse.Namespace) -> int:
    """Portfolio-Analyse."""
    print("\n" + "=" * 90)
    print("  Peak_Trade – Portfolio-Analyse")
    print("=" * 90)

    try:
        df = load_experiments_df_filtered(run_types=["portfolio_backtest"])
    except FileNotFoundError as e:
        print(f"\nFEHLER: {e}")
        return 1

    if df.empty:
        print("\nKeine Portfolio-Backtests gefunden.")
        return 0

    print(f"\nGefunden: {len(df)} Portfolio-Backtest(s)")

    # Zusammenfassung berechnen
    summaries = summarize_portfolios(df)

    if not summaries:
        print("\nKeine Portfolios mit auswertbaren Daten gefunden.")
        return 0

    # Limit anwenden
    summaries = summaries[: args.limit]

    print_portfolio_summaries(summaries)

    # Top-Runs nach Metrik
    print(f"Top Portfolio-Runs nach {args.metric}:")
    top_df = top_runs_by_metric(
        df,
        metric=args.metric,
        n=args.limit,
        ascending=args.ascending,
    )
    print_top_runs(top_df, args.metric)

    # Optional: Report schreiben
    if args.write_report:
        report_path = Path(args.write_report)
        write_portfolio_markdown_report(
            summaries,
            report_path,
            title="Peak_Trade Portfolio Report",
        )
        print(f"Markdown-Report geschrieben: {report_path}")

    return 0


def mode_compare(args: argparse.Namespace) -> int:
    """Strategien vergleichen."""
    print("\n" + "=" * 90)
    print("  Peak_Trade – Strategie-Vergleich")
    print("=" * 90)

    if not args.strategies:
        print("\nFEHLER: --strategies erforderlich (z.B. --strategies ma_crossover,rsi_reversion)")
        return 1

    strategies = [s.strip() for s in args.strategies.split(",")]

    try:
        df = load_experiments_df_filtered()
    except FileNotFoundError as e:
        print(f"\nFEHLER: {e}")
        return 1

    if df.empty:
        print("\nKeine Experiments gefunden.")
        return 0

    # Vergleich berechnen
    comparison_df = compare_strategies(df, strategies)

    if comparison_df.empty:
        print(f"\nKeine Daten für Strategien: {', '.join(strategies)}")
        return 0

    print(f"\nVergleich: {', '.join(strategies)}")
    print_comparison(comparison_df)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point."""
    args = parse_args(argv)

    if args.mode == "summary":
        return mode_summary(args)
    elif args.mode == "top-runs":
        return mode_top_runs(args)
    elif args.mode == "portfolios":
        return mode_portfolios(args)
    elif args.mode == "compare":
        return mode_compare(args)
    else:
        print(f"Unbekannter Modus: {args.mode}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
