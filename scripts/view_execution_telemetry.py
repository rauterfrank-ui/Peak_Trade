#!/usr/bin/env python3
"""
View Execution Telemetry - CLI tool for querying execution event logs.

Phase 16C: Read-only viewer for JSONL telemetry logs with filtering.

Usage:
    # View all events from a session
    python scripts/view_execution_telemetry.py --session session_123

    # Filter by event type
    python scripts/view_execution_telemetry.py --type fill --limit 50

    # Filter by symbol and time range
    python scripts/view_execution_telemetry.py --symbol BTC-USD --from 2025-01-01T00:00:00

    # Export as JSON
    python scripts/view_execution_telemetry.py --session session_123 --json

    # Summary only
    python scripts/view_execution_telemetry.py --summary --session session_123
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution.telemetry_viewer import (
    TelemetryQuery,
    build_timeline,
    find_session_logs,
    iter_events,
    summarize_events,
)


def print_summary(summary: dict, stats: any) -> None:
    """Print human-readable summary."""
    print("\n=== TELEMETRY SUMMARY ===")
    print(f"Total Events: {summary['total_events']}")
    print(f"Unique Sessions: {len(summary['unique_sessions'])}")
    print(f"Unique Symbols: {', '.join(summary['unique_symbols']) or 'None'}")

    if summary.get("first_ts"):
        print(f"Time Range: {summary['first_ts']} → {summary['last_ts']}")

    print("\nEvents by Type:")
    for kind, count in sorted(summary["counts_by_type"].items()):
        print(f"  {kind:10s}: {count:6d}")

    if "latency_ms" in summary:
        lat = summary["latency_ms"]
        print("\nIntent→Order Latency:")
        print(f"  Min:    {lat['min']:.2f} ms")
        print(f"  Median: {lat['median']:.2f} ms")
        print(f"  Max:    {lat['max']:.2f} ms")
        if lat.get("p95"):
            print(f"  P95:    {lat['p95']:.2f} ms")

    # Parse stats
    print(f"\nParse Stats:")
    print(f"  Total Lines: {stats.total_lines}")
    print(f"  Valid Events: {stats.valid_events}")
    print(f"  Invalid Lines: {stats.invalid_lines}")
    if stats.error_rate > 0:
        print(f"  Error Rate: {stats.error_rate:.2%}")


def print_timeline(timeline: list, limit: int = 20) -> None:
    """Print human-readable timeline."""
    print(f"\n=== LAST {min(len(timeline), limit)} EVENTS ===")

    for i, event in enumerate(timeline[:limit]):
        ts = event.get("ts", "")[:19]  # Truncate microseconds
        kind = event.get("type", "").upper()
        symbol = event.get("symbol", "")
        session = event.get("session_id", "")[:8]  # Truncate session

        # Build description based on type
        if kind == "INTENT":
            side = event.get("side", "").upper()
            qty = event.get("quantity", 0)
            price = event.get("price", 0)
            desc = f"{side} {qty:.6f} @ ${price:,.2f}"

        elif kind == "ORDER":
            order_id = event.get("order_id", "")[:8]
            side = event.get("side", "").upper()
            qty = event.get("quantity", 0)
            order_type = event.get("order_type", "")
            desc = f"{side} {qty:.6f} ({order_type}) [ID: {order_id}]"

        elif kind == "FILL":
            order_id = event.get("order_id", "")[:8]
            qty = event.get("filled_quantity", 0)
            price = event.get("fill_price", 0)
            fee = event.get("fill_fee", 0)
            desc = f"{qty:.6f} @ ${price:,.2f} (fee: ${fee:.4f}) [ID: {order_id}]"

        elif kind == "GATE":
            gate = event.get("gate_name", "")
            passed = "✅ PASS" if event.get("passed") else "❌ BLOCK"
            reason = event.get("reason", "")
            desc = f"[{gate}] {passed}"
            if reason:
                desc += f" - {reason}"

        elif kind == "ERROR":
            error_msg = event.get("error_message", "")
            desc = f"Error: {error_msg}"

        else:
            desc = "(unknown event type)"

        print(f"{i + 1:3d}. {ts} | {kind:6s} | {symbol:10s} | {desc}")


def main():
    parser = argparse.ArgumentParser(
        description="View execution telemetry logs (read-only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Filters
    parser.add_argument(
        "--path",
        type=str,
        default="logs/execution",
        help="Base path for telemetry logs (default: logs/execution)",
    )
    parser.add_argument("--session", type=str, help="Filter by session ID")
    parser.add_argument(
        "--type",
        type=str,
        choices=["intent", "order", "fill", "gate", "error"],
        help="Filter by event type",
    )
    parser.add_argument("--symbol", type=str, help="Filter by trading symbol")
    parser.add_argument(
        "--from", dest="ts_from", type=str, help="Filter events after ISO timestamp"
    )
    parser.add_argument("--to", dest="ts_to", type=str, help="Filter events before ISO timestamp")
    parser.add_argument(
        "--limit", type=int, default=2000, help="Maximum events to load (default: 2000)"
    )

    # Output modes
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw events as JSON lines (one per line)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=True,
        help="Show summary statistics (default: true)",
    )
    parser.add_argument("--no-summary", dest="summary", action="store_false", help="Skip summary")
    parser.add_argument(
        "--timeline",
        type=int,
        default=20,
        metavar="N",
        help="Show last N events as timeline (default: 20, 0 to skip)",
    )

    args = parser.parse_args()

    # Build query
    query = TelemetryQuery(
        session_id=args.session,
        event_type=args.type,
        symbol=args.symbol,
        ts_from=args.ts_from,
        ts_to=args.ts_to,
        limit=args.limit,
    )

    # Find log files
    base_path = Path(args.path)
    if args.session:
        # Single session
        log_path = base_path / f"{args.session}.jsonl"
        if not log_path.exists():
            print(f"❌ Error: Session log not found: {log_path}", file=sys.stderr)
            return 2  # No logs found
        paths = [log_path]
    else:
        # All sessions
        paths = find_session_logs(base_path)
        if not paths:
            print(f"❌ Error: No telemetry logs found in {base_path}", file=sys.stderr)
            return 2  # No logs found

    print(f"📂 Reading {len(paths)} log file(s)...", file=sys.stderr)

    # Read events
    event_iter, stats = iter_events(paths, query)
    events_list = list(event_iter)  # Materialize for multiple passes

    # Check error rate
    if stats.error_rate > 0.05:  # >5% errors
        print(
            f"⚠️  Warning: High error rate ({stats.error_rate:.1%}) - check log format",
            file=sys.stderr,
        )

    if not events_list:
        print("ℹ️  No events match the query filters", file=sys.stderr)
        if args.summary:
            print(f"\nParse Stats:")
            print(f"  Total Lines: {stats.total_lines}")
            print(f"  Valid Events: {stats.valid_events}")
            print(f"  Invalid Lines: {stats.invalid_lines}")
        return 0

    # JSON output mode
    if args.json:
        for event in events_list:
            print(json.dumps(event))
        return 0

    # Summary mode
    if args.summary:
        summary = summarize_events(events_list)
        print_summary(summary, stats)

    # Timeline mode
    if args.timeline > 0:
        timeline = build_timeline(events_list, max_items=args.timeline)
        print_timeline(timeline, limit=args.timeline)

    # Exit code based on error rate
    if stats.error_rate > 0.05:
        return 3  # Parse errors too high

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
