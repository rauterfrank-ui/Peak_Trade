#!/usr/bin/env python3
"""
VaR Backtest Suite Report Index Builder.

Discovers run artifacts from a report root and generates index.{json,md,html}
for navigation and audit.

Phase 8D: Report Index + Compare + HTML Summary

Usage:
    python scripts/risk/var_suite_build_index.py \\
        --report-root results/var_suite \\
        --formats json md html

Example:
    python scripts/risk/var_suite_build_index.py \\
        --report-root /tmp/var_suite_reports
"""

import argparse
import sys
from pathlib import Path

# Add src/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.risk.validation.report_index import write_index


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build VaR Backtest Suite Report Index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--report-root",
        type=str,
        required=True,
        help="Root directory containing run subdirectories",
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

    report_root = Path(args.report_root)

    if not report_root.exists():
        print(f"ERROR: Report root not found: {report_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Building index for: {report_root}")
    print(f"Output formats: {', '.join(formats)}")

    try:
        created_files = write_index(
            report_root=report_root,
            formats=formats,
            deterministic=True,
        )

        print(f"\n✓ Index created successfully:")
        for path in created_files:
            print(f"  - {path}")

        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: Failed to build index: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
