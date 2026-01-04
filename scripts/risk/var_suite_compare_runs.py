#!/usr/bin/env python3
"""
VaR Backtest Suite Run Comparison Tool.

Compares two VaR suite runs (baseline vs candidate) and generates
compare.{json,md,html} reports for regression tracking.

Phase 8D: Report Index + Compare + HTML Summary

Usage:
    python scripts/risk/var_suite_compare_runs.py \\
        --baseline results/var_suite/run_baseline \\
        --candidate results/var_suite/run_candidate \\
        --out results/var_suite/compare

Example:
    python scripts/risk/var_suite_compare_runs.py \\
        --baseline /tmp/var_suite/run_20260101 \\
        --candidate /tmp/var_suite/run_20260102 \\
        --out /tmp/var_suite/compare
"""

import argparse
import sys
from pathlib import Path

# Add src/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.risk.validation.report_compare import write_compare


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare two VaR Backtest Suite runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--baseline",
        type=str,
        required=True,
        help="Baseline run directory (must contain suite_report.json)",
    )
    parser.add_argument(
        "--candidate",
        type=str,
        required=True,
        help="Candidate run directory (must contain suite_report.json)",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output directory for comparison reports",
    )
    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        default=["json", "md", "html"],
        choices=["json", "md", "html"],
        help="Output formats (default: json md html)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Generate only JSON output (shortcut for --formats json)",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip HTML generation",
    )

    args = parser.parse_args()

    # Resolve format flags
    if args.json_only:
        formats = ("json",)
    else:
        formats = tuple(args.formats)
        if args.no_html:
            formats = tuple(f for f in formats if f != "html")

    baseline_dir = Path(args.baseline)
    candidate_dir = Path(args.candidate)
    out_dir = Path(args.out)

    # Validate inputs
    if not baseline_dir.exists():
        print(f"ERROR: Baseline directory not found: {baseline_dir}", file=sys.stderr)
        sys.exit(1)

    if not candidate_dir.exists():
        print(f"ERROR: Candidate directory not found: {candidate_dir}", file=sys.stderr)
        sys.exit(1)

    baseline_json = baseline_dir / "suite_report.json"
    if not baseline_json.exists():
        print(
            f"ERROR: suite_report.json not found in baseline: {baseline_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    candidate_json = candidate_dir / "suite_report.json"
    if not candidate_json.exists():
        print(
            f"ERROR: suite_report.json not found in candidate: {candidate_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Comparing runs:")
    print(f"  Baseline:  {baseline_dir}")
    print(f"  Candidate: {candidate_dir}")
    print(f"  Output:    {out_dir}")
    print(f"  Formats:   {', '.join(formats)}")

    try:
        created_files = write_compare(
            out_dir=out_dir,
            baseline_dir=baseline_dir,
            candidate_dir=candidate_dir,
            formats=formats,
            deterministic=True,
        )

        print(f"\n✓ Comparison created successfully:")
        for path in created_files:
            print(f"  - {path}")

        # Check for regressions (exit code based on compare.json)
        compare_json_path = out_dir / "compare.json"
        if compare_json_path.exists():
            import json

            with open(compare_json_path, "r") as f:
                compare_data = json.load(f)

            if compare_data.get("regressions"):
                print(f"\n⚠️  WARNING: {len(compare_data['regressions'])} regression(s) detected")
                sys.exit(1)
            else:
                print("\n✅ No regressions detected")
                sys.exit(0)

    except Exception as e:
        print(f"\nERROR: Failed to compare runs: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
