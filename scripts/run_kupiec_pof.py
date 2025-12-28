#!/usr/bin/env python3
"""
Phase 7 CLI: Minimal Kupiec POF Test Runner

Accepts n/x/alpha parameters or exceedances CSV and prints formatted report.
Always exits with code 0 (CI-friendly).
"""

import argparse
import sys
from pathlib import Path

from src.risk_layer.var_backtest import kupiec_from_exceedances, kupiec_lr_uc


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Kupiec POF Test with n/x/alpha interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Direct n/x/alpha interface
  python scripts/run_kupiec_pof.py --n 1000 --x 10 --alpha 0.01

  # From exceedances CSV (one boolean per line: True/False)
  python scripts/run_kupiec_pof.py --exceedances-csv data/exceedances.csv --alpha 0.01

  # Custom p-threshold
  python scripts/run_kupiec_pof.py --n 250 --x 5 --alpha 0.01 --p-threshold 0.01
        """,
    )

    # Direct n/x/alpha interface
    parser.add_argument("--n", type=int, help="Total observations")
    parser.add_argument("--x", type=int, help="Number of exceedances")
    parser.add_argument(
        "--alpha",
        type=float,
        required=True,
        help="Expected exceedance rate (e.g., 0.01 for 99%% VaR)",
    )

    # Alternative: CSV input
    parser.add_argument(
        "--exceedances-csv",
        type=Path,
        help="Path to CSV with exceedances (one boolean per line: True/False)",
    )

    # Test parameters
    parser.add_argument(
        "--p-threshold",
        type=float,
        default=0.05,
        help="Significance level for verdict (default: 0.05)",
    )

    return parser.parse_args()


def load_exceedances_csv(path: Path) -> list[bool]:
    """Load exceedances from CSV file."""
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    exceedances = []
    with open(path) as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip().lower()
            if line in ("true", "1", "yes"):
                exceedances.append(True)
            elif line in ("false", "0", "no"):
                exceedances.append(False)
            else:
                print(
                    f"WARNING: Invalid value at line {line_num}: {line!r} (skipping)",
                    file=sys.stderr,
                )

    return exceedances


def print_report(result):
    """Print formatted report."""
    print("=" * 60)
    print("KUPIEC POF TEST REPORT (Phase 7)")
    print("=" * 60)
    print(f"Observations (n):      {result.n}")
    print(f"Exceedances (x):       {result.x}")
    print(f"Expected Rate (alpha): {result.alpha:.4f} ({result.alpha * 100:.2f}%)")
    print(f"Observed Rate (phat):  {result.phat:.4f} ({result.phat * 100:.2f}%)")
    print()
    print("Test Statistics:")
    print(f"  LR Statistic:        {result.lr_uc:.4f}")
    print(f"  p-value:             {result.p_value:.4f}")
    print()
    print(f"VERDICT:               {result.verdict}")
    print()
    print(f"Notes: {result.notes}")
    print("=" * 60)


def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Determine input mode
        if args.exceedances_csv:
            # Load from CSV
            exceedances = load_exceedances_csv(args.exceedances_csv)
            print(f"Loaded {len(exceedances)} exceedances from {args.exceedances_csv}")
            result = kupiec_from_exceedances(
                exceedances, alpha=args.alpha, p_threshold=args.p_threshold
            )
        else:
            # Direct n/x/alpha
            if args.n is None or args.x is None:
                print("ERROR: Must provide either --n/--x OR --exceedances-csv", file=sys.stderr)
                sys.exit(1)

            result = kupiec_lr_uc(
                n=args.n, x=args.x, alpha=args.alpha, p_threshold=args.p_threshold
            )

        # Print report
        print_report(result)

        # Always exit 0 (CI-friendly)
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
