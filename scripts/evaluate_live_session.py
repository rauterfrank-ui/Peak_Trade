#!/usr/bin/env python3
"""
Offline live session evaluation CLI.

Reads fills.csv from a session directory and computes metrics including:
- Fill counts, symbols, time range
- Notional, total quantity, VWAP
- Side breakdown (buy/sell)
- Realized PnL using FIFO matching

Usage:
    python scripts/evaluate_live_session.py --session-dir <path> [options]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.live_eval import read_fills_csv, compute_metrics


def format_text_output(metrics: Dict[str, Any], session_dir: Path) -> str:
    """Format metrics as human-readable text."""
    lines = []
    lines.append(f"Session Directory: {session_dir}")
    lines.append("")
    lines.append("=== Fill Summary ===")
    lines.append(f"Total Fills: {metrics['total_fills']}")
    lines.append(f"Symbols: {', '.join(metrics['symbols']) if metrics['symbols'] else 'None'}")
    lines.append(f"Time Range: {metrics['start_ts']} to {metrics['end_ts']}")
    lines.append("")
    lines.append("=== Aggregate Metrics ===")
    lines.append(f"Total Notional: {metrics['total_notional']:.2f}")
    lines.append(f"Total Quantity: {metrics['total_qty']:.4f}")
    vwap = metrics["vwap_overall"]
    lines.append(f"VWAP (Overall): {vwap:.2f}" if vwap else "VWAP (Overall): N/A")
    lines.append("")

    # VWAP per symbol
    if metrics.get("vwap_per_symbol"):
        lines.append("=== VWAP per Symbol ===")
        for symbol, vwap_val in sorted(metrics["vwap_per_symbol"].items()):
            lines.append(f"  {symbol}: {vwap_val:.2f}" if vwap_val else f"  {symbol}: N/A")
        lines.append("")

    lines.append("=== Side Breakdown ===")
    for side in ["buy", "sell"]:
        stats = metrics["side_breakdown"][side]
        lines.append(f"{side.upper()}:")
        lines.append(f"  Count: {stats['count']}")
        lines.append(f"  Quantity: {stats['qty']:.4f}")
        lines.append(f"  Notional: {stats['notional']:.2f}")
    lines.append("")

    lines.append("=== Realized PnL (FIFO) ===")
    lines.append(f"Total Realized PnL: {metrics['realized_pnl_total']:.2f}")

    if metrics["realized_pnl_per_symbol"]:
        lines.append("Per Symbol:")
        for symbol, pnl in sorted(metrics["realized_pnl_per_symbol"].items()):
            lines.append(f"  {symbol}: {pnl:.2f}")

    return "\n".join(lines)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate live session fills from CSV (offline tool)"
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        required=True,
        help="Path to session directory containing fills CSV",
    )
    parser.add_argument(
        "--fills-csv",
        type=str,
        default="fills.csv",
        help="Name of fills CSV file (default: fills.csv)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write JSON report to session-dir/live_eval_report.json",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on parsing/validation errors (default: best-effort)",
    )

    args = parser.parse_args()

    # Validate session directory
    if not args.session_dir.is_dir():
        print(f"ERROR: Session directory does not exist: {args.session_dir}", file=sys.stderr)
        sys.exit(2)

    fills_path = args.session_dir / args.fills_csv

    # Read fills
    try:
        fills = read_fills_csv(fills_path, strict=args.strict)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"ERROR: Invalid CSV format: {e}", file=sys.stderr)
        sys.exit(1 if args.strict else 2)
    except Exception as e:
        print(f"ERROR: Failed to read fills: {e}", file=sys.stderr)
        sys.exit(2)

    # Compute metrics
    try:
        metrics = compute_metrics(fills, strict=args.strict)
    except ValueError as e:
        print(f"ERROR: Metric computation failed: {e}", file=sys.stderr)
        sys.exit(1 if args.strict else 2)
    except Exception as e:
        print(f"ERROR: Unexpected error during metric computation: {e}", file=sys.stderr)
        sys.exit(2)

    # Output
    if args.format == "json":
        print(json.dumps(metrics, indent=2))
    else:
        print(format_text_output(metrics, args.session_dir))

    # Write report if requested
    if args.write_report:
        report_path = args.session_dir / "live_eval_report.json"
        try:
            with report_path.open("w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            print(f"\nReport written to: {report_path}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to write report: {e}", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
