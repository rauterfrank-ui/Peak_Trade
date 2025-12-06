#!/usr/bin/env python3
"""
Peak_Trade Auto-Portfolio-Builder
==================================
Generiert automatisch Portfolio-Kandidaten aus Sweep- und Market-Scan-Ergebnissen.

Features:
- Selektion der besten Sweep-Ergebnisse nach Metrik (Sharpe, Return)
- Export als TOML-Config für run_portfolio_backtest.py
- Dry-Run-Modus für Vorschau
- Filterung nach Tag, Strategie, Mindest-Sharpe

Usage:
    # Dry-Run (nur Vorschläge anzeigen)
    python scripts/build_auto_portfolios.py --dry-run

    # Portfolios generieren und speichern
    python scripts/build_auto_portfolios.py \
        --metric sharpe \
        --min-sharpe 0.5 \
        --max-components 3 \
        --output-dir config/portfolios

    # Mit Tag-Filter
    python scripts/build_auto_portfolios.py \
        --metric sharpe \
        --tag optimization-v1 \
        --prefix auto_ma
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.experiments import load_experiments_df
from src.analytics.experiments_analysis import filter_sweeps, filter_market_scans
from src.analytics.portfolio_builder import (
    build_portfolio_candidates_from_sweeps_and_scans,
    build_multiple_portfolio_candidates,
    write_portfolio_candidate_to_toml,
    format_portfolio_candidate_summary,
)


def parse_args(argv=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Auto-generate portfolio candidates from sweep/scan results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run: show what would be generated
  python scripts/build_auto_portfolios.py --dry-run

  # Generate with Sharpe filter
  python scripts/build_auto_portfolios.py \\
      --metric sharpe \\
      --min-sharpe 0.5 \\
      --max-components 3 \\
      --output-dir config/portfolios

  # Filter by tag
  python scripts/build_auto_portfolios.py \\
      --tag optimization-v1 \\
      --prefix auto_ma

  # Generate one portfolio per strategy
  python scripts/build_auto_portfolios.py \\
      --mode per-strategy \\
      --output-dir config/portfolios
        """
    )

    parser.add_argument(
        "--metric",
        type=str,
        default="sharpe",
        choices=["sharpe", "total_return", "cagr"],
        help="Metric for ranking components (default: sharpe)"
    )

    parser.add_argument(
        "--min-sharpe",
        type=float,
        default=None,
        help="Minimum Sharpe ratio for inclusion"
    )

    parser.add_argument(
        "--min-return",
        type=float,
        default=None,
        help="Minimum total return for inclusion"
    )

    parser.add_argument(
        "--max-components",
        type=int,
        default=5,
        help="Maximum components per portfolio (default: 5)"
    )

    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Filter on specific tag from sweep/scan runs"
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Filter on specific strategy (comma-separated for multiple)"
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="combined",
        choices=["combined", "per-strategy"],
        help="Generation mode: 'combined' for single portfolio, 'per-strategy' for one per strategy"
    )

    parser.add_argument(
        "--allocation",
        type=str,
        default="equal",
        choices=["equal", "metric_weighted"],
        help="Allocation method for portfolio weights (default: equal)"
    )

    parser.add_argument(
        "--initial-equity",
        type=float,
        default=10000.0,
        help="Initial equity for portfolio (default: 10000.0)"
    )

    parser.add_argument(
        "--prefix",
        type=str,
        default="auto_portfolio",
        help="Prefix for portfolio names (default: auto_portfolio)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="config/portfolios",
        help="Output directory for TOML files (default: config/portfolios)"
    )

    parser.add_argument(
        "--include-scans",
        action="store_true",
        help="Also include market-scan results (backtest-lite mode)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be generated, don't write files"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Main entry point."""
    args = parse_args(argv)

    print("\n" + "=" * 70)
    print("Peak_Trade Auto-Portfolio-Builder")
    print("=" * 70)

    # 1. Experiments laden
    print("\n[1/4] Loading experiments from registry...")
    try:
        df = load_experiments_df()
        print(f"      Loaded {len(df)} experiments")
    except FileNotFoundError:
        print("      ERROR: No experiments found. Run some sweeps first.")
        print("      Example: python scripts/run_sweep.py --strategy ma_crossover --grid config/sweeps/ma_crossover.toml")
        return 1

    # 2. Sweeps/Scans filtern
    print("\n[2/4] Filtering sweeps and scans...")
    df_sweeps = filter_sweeps(df)
    df_scans = filter_market_scans(df) if args.include_scans else None

    print(f"      Sweeps: {len(df_sweeps)}")
    if df_scans is not None:
        print(f"      Market-Scans: {len(df_scans)}")

    if df_sweeps.empty:
        print("\n      WARNING: No sweep results found.")
        print("      Run sweeps first to generate portfolio candidates.")
        print("      Example: python scripts/run_sweep.py --strategy ma_crossover --grid config/sweeps/ma_crossover.toml")
        return 1

    # Strategie-Filter
    strategies = None
    if args.strategy:
        strategies = [s.strip() for s in args.strategy.split(",")]
        print(f"      Filtering to strategies: {strategies}")

    # 3. Portfolio-Kandidaten bauen
    print("\n[3/4] Building portfolio candidates...")
    print(f"      Mode: {args.mode}")
    print(f"      Metric: {args.metric}")
    print(f"      Max components: {args.max_components}")
    if args.min_sharpe:
        print(f"      Min Sharpe: {args.min_sharpe}")
    if args.min_return:
        print(f"      Min Return: {args.min_return}")
    if args.tag:
        print(f"      Tag filter: {args.tag}")

    if args.mode == "combined":
        # Ein kombiniertes Portfolio
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df_sweeps,
            df_scans=df_scans,
            metric=args.metric,
            max_components=args.max_components,
            min_sharpe=args.min_sharpe,
            min_return=args.min_return,
            name_prefix=args.prefix,
            allocation_method=args.allocation,
            initial_equity=args.initial_equity,
            tag=args.tag,
        )
    else:
        # Ein Portfolio pro Strategie
        candidates = build_multiple_portfolio_candidates(
            df=df_sweeps,
            strategies=strategies,
            metric=args.metric,
            max_components_per_portfolio=args.max_components,
            min_sharpe=args.min_sharpe,
            name_prefix=args.prefix,
            initial_equity=args.initial_equity,
        )

    if not candidates:
        print("\n      WARNING: No portfolio candidates generated.")
        print("      Try lowering min-sharpe or running more sweeps.")
        return 1

    print(f"\n      Generated {len(candidates)} portfolio candidate(s)")

    # 4. Anzeigen / Speichern
    print("\n[4/4] Processing candidates...")

    output_dir = Path(args.output_dir)

    for i, candidate in enumerate(candidates, 1):
        print(f"\n{'=' * 60}")
        print(f"Portfolio Candidate {i}/{len(candidates)}")
        print("=" * 60)
        print(format_portfolio_candidate_summary(candidate))

        if not args.dry_run:
            # TOML-Datei schreiben
            output_dir.mkdir(parents=True, exist_ok=True)
            toml_path = output_dir / f"{candidate.name}.toml"
            write_portfolio_candidate_to_toml(candidate, toml_path)
            print(f"\n      Saved: {toml_path}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"  Candidates generated: {len(candidates)}")

    if args.dry_run:
        print("  Mode: DRY-RUN (no files written)")
        print("\n  To save these portfolios, run without --dry-run:")
        print(f"    python scripts/build_auto_portfolios.py {' '.join(sys.argv[1:]).replace('--dry-run', '')}")
    else:
        print(f"  Output directory: {output_dir}")
        print("\n  Next steps:")
        print("  1. Review the generated TOML files")
        print("  2. Run backtests with:")
        for candidate in candidates[:3]:  # Show first 3
            toml_path = output_dir / f"{candidate.name}.toml"
            print(f"     python scripts/run_portfolio_backtest.py --config {toml_path}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
