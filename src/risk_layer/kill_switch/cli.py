"""CLI Interface for Kill Switch.

Provides command-line interface for operators to manage kill switch.

Commands:
    - status: Show current status
    - trigger: Manually trigger kill switch
    - recover: Request recovery
    - audit: Show audit trail
    - health: Check system health
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.risk_layer.kill_switch import KillSwitch, load_config, get_approval_code
from src.risk_layer.kill_switch.audit import AuditTrail
from src.risk_layer.kill_switch.health_check import HealthChecker
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.recovery import RecoveryManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_EXCHANGE_CONNECTED_ENV = "PEAK_KILL_SWITCH_EXCHANGE_CONNECTED"


def resolve_exchange_connected_for_health(cli_choice: str) -> bool:
    """
    Resolve ``exchange_connected`` for ``kill-switch health`` (NO-LIVE).

    Parameters
    ----------
    cli_choice:
        ``\"true\"`` / ``\"false\"`` — explicit override.
        ``\"auto\"`` — read :envvar:`PEAK_KILL_SWITCH_EXCHANGE_CONNECTED` if set
        (1/0, true/false, yes/no); otherwise default ``True`` (preserves prior
        CLI behaviour when operators do not configure anything).
    """
    if cli_choice == "true":
        return True
    if cli_choice == "false":
        return False
    raw = os.environ.get(_EXCHANGE_CONNECTED_ENV, "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return True


def cmd_status(args, kill_switch: KillSwitch):
    """Show kill switch status."""
    status = kill_switch.get_status()

    print("┌────────────────────────────────────────┐")
    print("│ KILL SWITCH STATUS                     │")
    print("├────────────────────────────────────────┤")

    # State with emoji
    state = status["state"]
    if state == "ACTIVE":
        emoji = "🟢"
    elif state == "KILLED":
        emoji = "🔴"
    elif state == "RECOVERING":
        emoji = "🟡"
    else:
        emoji = "⚪"

    print(f"│ State:         {emoji} {state:<20} │")

    # Last trigger
    if status["killed_at"]:
        killed_at = datetime.fromisoformat(status["killed_at"])
        print(f"│ Last Trigger:  {killed_at.strftime('%Y-%m-%d %H:%M:%S'):<20} │")
    else:
        print(f"│ Last Trigger:  {'Never':<20} │")

    # Cooldown info
    if "cooldown_remaining_seconds" in status:
        remaining = status["cooldown_remaining_seconds"]
        print(f"│ Cooldown:      {remaining:.0f}s remaining{'':>8} │")

    # Event count
    print(f"│ Events:        {status['event_count']:<20} │")

    print("└────────────────────────────────────────┘")


def cmd_trigger(args, kill_switch: KillSwitch):
    """Manually trigger kill switch."""
    reason = args.reason or "Manual trigger via CLI"

    # Confirmation
    if not args.confirm:
        print("⚠️  This will STOP all trading immediately!")
        print(f"Reason: {reason}")
        response = input("Are you sure? (type 'yes' to confirm): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    # Trigger
    success = kill_switch.trigger(reason, triggered_by="manual_cli")

    if success:
        print(f"🚨 KILL SWITCH TRIGGERED: {reason}")
        print("Trading is now BLOCKED.")
    else:
        print("❌ Failed to trigger (already killed or disabled)")


def cmd_recover(args, kill_switch: KillSwitch):
    """Request kill switch recovery."""
    reason = args.reason or "Recovery via CLI"

    # Get approval code
    code = args.code
    if not code:
        code = input("Enter approval code: ")

    # Request recovery
    success = kill_switch.request_recovery(
        approved_by=args.approved_by or os.getenv("USER", "operator"),
        approval_code=code,
    )

    if success:
        print(f"⏳ RECOVERY STARTED")
        print(f"Reason: {reason}")
        print("Cooldown active. Use 'status' to check progress.")
    else:
        print("❌ Recovery request failed")
        print("Possible reasons:")
        print("  - Not in KILLED state")
        print("  - Invalid approval code")


def cmd_audit(args, config: dict):
    """Show audit trail."""
    audit_dir = config.get("kill_switch", {}).get("audit_dir", "data/kill_switch/audit")
    audit = AuditTrail(audit_dir)

    # Parse time filters
    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
        except ValueError:
            # Try relative time (e.g., "24h")
            if args.since.endswith("h"):
                hours = int(args.since[:-1])
                since = datetime.utcnow() - timedelta(hours=hours)
            elif args.since.endswith("d"):
                days = int(args.since[:-1])
                since = datetime.utcnow() - timedelta(days=days)

    # Get events
    events = audit.get_events(since=since, limit=args.limit)

    if not events:
        print("No audit events found.")
        return

    print(f"\n📋 AUDIT TRAIL ({len(events)} events)\n")
    print(f"{'Timestamp':<20} {'Previous':<12} {'New State':<12} {'Triggered By':<15} Reason")
    print("─" * 100)

    for event in reversed(events):  # Most recent first
        timestamp = datetime.fromisoformat(event["timestamp"])
        print(
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20} "
            f"{event['previous_state']:<12} "
            f"{event['new_state']:<12} "
            f"{event['triggered_by']:<15} "
            f"{event['trigger_reason']}"
        )

    # Statistics
    stats = audit.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")


def cmd_health(args, config: dict):
    """Check system health."""
    recovery_config = config.get("kill_switch.recovery", {})
    checker = HealthChecker(recovery_config)

    mode = getattr(args, "exchange_connected_mode", "auto")
    exchange_ok = resolve_exchange_connected_for_health(mode)

    # Build context if possible
    context = {
        "exchange_connected": exchange_ok,
        "last_price_update": datetime.utcnow(),
    }

    print("Running health checks...\n")
    result = checker.check_all(context)

    if result.is_healthy:
        print("✅ HEALTH CHECK PASSED")
        print(f"   {result.checks_passed} checks passed")
    else:
        print("❌ HEALTH CHECK FAILED")
        print(f"   {result.checks_passed} passed, {result.checks_failed} failed")
        print("\nIssues:")
        for issue in result.issues:
            print(f"   - {issue}")

    # Show metadata
    print("\nDetails:")
    for key, value in result.metadata.items():
        print(f"   {key}: {value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Kill Switch CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        help="Path to config file",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    subparsers.add_parser("status", help="Show kill switch status")

    # Trigger command
    trigger_parser = subparsers.add_parser("trigger", help="Trigger kill switch")
    trigger_parser.add_argument("--reason", help="Reason for trigger")
    trigger_parser.add_argument("--confirm", action="store_true", help="Skip confirmation")

    # Recover command
    recover_parser = subparsers.add_parser("recover", help="Request recovery")
    recover_parser.add_argument("--code", help="Approval code")
    recover_parser.add_argument("--reason", help="Reason for recovery")
    recover_parser.add_argument("--approved-by", help="Approver name")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Show audit trail")
    audit_parser.add_argument(
        "--since", help="Events since (ISO date or relative like '24h', '7d')"
    )
    audit_parser.add_argument("--limit", type=int, default=50, help="Max events to show")

    # Health command
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.add_argument(
        "--exchange-connected",
        dest="exchange_connected_mode",
        choices=("auto", "true", "false"),
        default="auto",
        help=(
            "Assume exchange connectivity for the health check: "
            "'auto' reads PEAK_KILL_SWITCH_EXCHANGE_CONNECTED or defaults to true when unset."
        ),
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load configuration
    try:
        config = load_config(args.config)
        kill_switch_config = config.get("kill_switch", {})
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1

    # Initialize kill switch for most commands
    if args.command in ["status", "trigger", "recover"]:
        try:
            kill_switch = KillSwitch(kill_switch_config, logger=logger)
        except Exception as e:
            logger.error(f"Failed to initialize kill switch: {e}")
            return 1

    # Execute command
    try:
        if args.command == "status":
            cmd_status(args, kill_switch)
        elif args.command == "trigger":
            cmd_trigger(args, kill_switch)
        elif args.command == "recover":
            cmd_recover(args, kill_switch)
        elif args.command == "audit":
            cmd_audit(args, config)
        elif args.command == "health":
            cmd_health(args, config)
        else:
            parser.print_help()
            return 1

        return 0

    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
