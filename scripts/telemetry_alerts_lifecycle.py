#!/usr/bin/env python3
"""
Telemetry Alerts Lifecycle CLI - Phase 16J

Extended CLI for alert history, operator actions, and statistics.

Usage:
    # View alert history
    python scripts/telemetry_alerts_lifecycle.py history --limit 50 --since 24h

    # Acknowledge alert
    python scripts/telemetry_alerts_lifecycle.py ack --dedupe-key "health_critical:..." --ttl 2h

    # Snooze rule
    python scripts/telemetry_alerts_lifecycle.py snooze --rule-id degradation_detected --ttl 30m

    # Unsnooze rule
    python scripts/telemetry_alerts_lifecycle.py unsnooze --rule-id degradation_detected

    # View statistics
    python scripts/telemetry_alerts_lifecycle.py stats --since 7d

Exit codes:
    0 = Success
    1 = Invalid args or state disabled
    2 = Operation failed
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution.alerting import AlertHistory, OperatorState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_time_delta(time_str: str) -> timedelta:
    """Parse time delta from string (e.g., '24h', '7d', '30m')."""
    try:
        unit = time_str[-1]
        value = int(time_str[:-1])

        if unit == "s":
            return timedelta(seconds=value)
        elif unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            raise ValueError(f"Unknown time unit: {unit}")
    except Exception as e:
        raise ValueError(
            f"Invalid time delta format: {time_str} (use format like '24h', '7d', '30m')"
        )


def cmd_history(args):
    """View alert history."""
    history = AlertHistory(
        history_path=Path(args.history_path),
        enabled=True,
    )

    # Parse since
    since = None
    if args.since:
        delta = parse_time_delta(args.since)
        since = datetime.now(timezone.utc) - delta

    # Query history
    entries = history.query(
        since=since,
        severity=args.severity,
        rule_id=args.rule_id,
        limit=args.limit,
    )

    if not entries:
        print("No alert history found")
        return 0

    # Display
    print(f"📋 Alert History ({len(entries)} entries)")
    print()

    for entry in entries:
        severity = entry.get("severity", "unknown")
        severity_emoji = {"info": "ℹ️", "warn": "⚠️", "critical": "🔴"}.get(severity, "⚠️")

        print(f"{severity_emoji} [{severity.upper()}] {entry.get('title', 'Unknown')}")
        print(f"   Time: {entry.get('timestamp_utc', 'Unknown')}")
        print(f"   Source: {entry.get('source', 'Unknown')}")
        print(f"   Dedupe Key: {entry.get('dedupe_key', 'Unknown')}")
        print(f"   Delivery: {entry.get('delivery_status', 'Unknown')}")
        print()

    return 0


def cmd_ack(args):
    """Acknowledge alert."""
    state = OperatorState(
        state_path=Path(args.state_path),
        enabled=args.enable_operator_actions,
    )

    if not state.enabled:
        print("❌ Operator actions disabled (use --enable-operator-actions)")
        return 1

    # Parse TTL
    ttl_seconds = None
    if args.ttl:
        delta = parse_time_delta(args.ttl)
        ttl_seconds = int(delta.total_seconds())

    # ACK
    success = state.ack(
        dedupe_key=args.dedupe_key,
        ttl_seconds=ttl_seconds,
        operator=args.operator,
        reason=args.reason,
    )

    if success:
        ttl_str = f" (TTL: {args.ttl})" if args.ttl else " (permanent)"
        print(f"✅ Acknowledged: {args.dedupe_key}{ttl_str}")
        return 0
    else:
        print(f"❌ Failed to acknowledge: {args.dedupe_key}")
        return 2


def cmd_snooze(args):
    """Snooze rule."""
    state = OperatorState(
        state_path=Path(args.state_path),
        enabled=args.enable_operator_actions,
    )

    if not state.enabled:
        print("❌ Operator actions disabled (use --enable-operator-actions)")
        return 1

    # Parse TTL (required for snooze)
    delta = parse_time_delta(args.ttl)
    ttl_seconds = int(delta.total_seconds())

    # SNOOZE
    success = state.snooze(
        rule_id=args.rule_id,
        ttl_seconds=ttl_seconds,
        operator=args.operator,
        reason=args.reason,
    )

    if success:
        print(f"✅ Snoozed rule: {args.rule_id} (TTL: {args.ttl})")
        return 0
    else:
        print(f"❌ Failed to snooze rule: {args.rule_id}")
        return 2


def cmd_unsnooze(args):
    """Unsnooze rule."""
    state = OperatorState(
        state_path=Path(args.state_path),
        enabled=args.enable_operator_actions,
    )

    if not state.enabled:
        print("❌ Operator actions disabled (use --enable-operator-actions)")
        return 1

    # UNSNOOZE
    success = state.unsnooze(args.rule_id)

    if success:
        print(f"✅ Unsnoozed rule: {args.rule_id}")
        return 0
    else:
        print(f"❌ Failed to unsnooze rule: {args.rule_id}")
        return 2


def cmd_stats(args):
    """View alert statistics."""
    history = AlertHistory(
        history_path=Path(args.history_path),
        enabled=True,
    )

    # Parse since
    since = None
    if args.since:
        delta = parse_time_delta(args.since)
        since = datetime.now(timezone.utc) - delta

    # Get stats
    stats = history.get_stats(since=since)

    print(f"📊 Alert Statistics (since {args.since if args.since else 'all time'})")
    print()
    print(f"Total Alerts: {stats['total']}")
    print()

    # By severity
    print("By Severity:")
    for severity, count in sorted(stats["by_severity"].items()):
        emoji = {"info": "ℹ️", "warn": "⚠️", "critical": "🔴"}.get(severity, "⚠️")
        print(f"  {emoji} {severity.upper()}: {count}")
    print()

    # By rule (top 10)
    print("Top 10 Noisy Rules:")
    sorted_rules = sorted(stats["by_rule"].items(), key=lambda x: x[1], reverse=True)
    for rule_id, count in sorted_rules[:10]:
        print(f"  {rule_id}: {count}")
    print()

    # By delivery status
    print("Delivery Status:")
    for status, count in sorted(stats["by_status"].items()):
        print(f"  {status}: {count}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Telemetry Alerts Lifecycle CLI (Phase 16J)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # === HISTORY ===
    history_parser = subparsers.add_parser("history", help="View alert history")
    history_parser.add_argument(
        "--history-path",
        type=str,
        default="data/telemetry/alerts/alerts_history.jsonl",
        help="Path to history file",
    )
    history_parser.add_argument("--limit", type=int, default=50, help="Maximum results")
    history_parser.add_argument("--since", type=str, help="Time delta (e.g., 24h, 7d)")
    history_parser.add_argument("--severity", type=str, help="Filter by severity")
    history_parser.add_argument("--rule-id", type=str, help="Filter by rule ID")

    # === ACK ===
    ack_parser = subparsers.add_parser("ack", help="Acknowledge alert")
    ack_parser.add_argument(
        "--state-path",
        type=str,
        default="data/telemetry/alerts/alerts_state.json",
        help="Path to state file",
    )
    ack_parser.add_argument(
        "--enable-operator-actions",
        action="store_true",
        help="Enable operator actions (required)",
    )
    ack_parser.add_argument("--dedupe-key", required=True, help="Dedupe key to ACK")
    ack_parser.add_argument("--ttl", type=str, help="TTL (e.g., 2h, 30m)")
    ack_parser.add_argument("--operator", default="cli", help="Operator name")
    ack_parser.add_argument("--reason", help="Reason for ACK")

    # === SNOOZE ===
    snooze_parser = subparsers.add_parser("snooze", help="Snooze rule")
    snooze_parser.add_argument(
        "--state-path",
        type=str,
        default="data/telemetry/alerts/alerts_state.json",
        help="Path to state file",
    )
    snooze_parser.add_argument(
        "--enable-operator-actions",
        action="store_true",
        help="Enable operator actions (required)",
    )
    snooze_parser.add_argument("--rule-id", required=True, help="Rule ID to snooze")
    snooze_parser.add_argument("--ttl", required=True, help="TTL (e.g., 30m, 2h)")
    snooze_parser.add_argument("--operator", default="cli", help="Operator name")
    snooze_parser.add_argument("--reason", help="Reason for snooze")

    # === UNSNOOZE ===
    unsnooze_parser = subparsers.add_parser("unsnooze", help="Unsnooze rule")
    unsnooze_parser.add_argument(
        "--state-path",
        type=str,
        default="data/telemetry/alerts/alerts_state.json",
        help="Path to state file",
    )
    unsnooze_parser.add_argument(
        "--enable-operator-actions",
        action="store_true",
        help="Enable operator actions (required)",
    )
    unsnooze_parser.add_argument("--rule-id", required=True, help="Rule ID to unsnooze")

    # === STATS ===
    stats_parser = subparsers.add_parser("stats", help="View alert statistics")
    stats_parser.add_argument(
        "--history-path",
        type=str,
        default="data/telemetry/alerts/alerts_history.jsonl",
        help="Path to history file",
    )
    stats_parser.add_argument("--since", type=str, help="Time delta (e.g., 7d, 30d)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch
    if args.command == "history":
        return cmd_history(args)
    elif args.command == "ack":
        return cmd_ack(args)
    elif args.command == "snooze":
        return cmd_snooze(args)
    elif args.command == "unsnooze":
        return cmd_unsnooze(args)
    elif args.command == "stats":
        return cmd_stats(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
