"""CLI Interface for Kill Switch.

Provides command-line interface for operators to manage kill switch.

Commands:
    - status: Show current status
    - trigger: Manually trigger kill switch
    - recover: Request recovery
    - complete-recovery: Complete an authorized recovery after cooldown
    - audit: Show audit trail
    - health: Check system health

The approval code is never accepted via argv. It is read with ``getpass`` from
the terminal or, with ``--code-stdin``, as one line from stdin. The expected code
comes from the environment variable named by ``approval_code_env``.

ACTIVE means only "kill-switch recovery completed". It never authorizes live
trading, orders or a venue POST; every other gate stays independent.

Exit codes:
    0 success
    1 configuration / unexpected error
    2 usage error (argparse, e.g. a rejected ``--code`` argument)
    3 denied (authorization, state, request binding, cooldown, journal)
    4 KILL journaled but the state write was blocked by the state lock
    5 KILL could not be made durable at all
"""

import argparse
import getpass
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Add src to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.risk_layer.kill_switch import KillSwitch, load_config
from src.risk_layer.kill_switch.audit import AuditTrail
from src.risk_layer.kill_switch.core import KillSwitchKillFailedError, KillSwitchKillPendingError
from src.risk_layer.kill_switch.recovery_attestation import (
    JournalError,
    TransitionJournal,
)
from src.risk_layer.kill_switch.exchange_probe import (
    is_exchange_probe_disabled,
    probe_exchange_http_public,
)
from src.risk_layer.kill_switch.health_check import HealthChecker


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_EXCHANGE_CONNECTED_ENV = "PEAK_KILL_SWITCH_EXCHANGE_CONNECTED"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_DENIED = 3
EXIT_KILL_PENDING = 4
EXIT_KILL_FAILED = 5

ACTIVE_IS_NOT_TRADING_AUTHORIZATION = (
    "ACTIVE = kill-switch recovery completed. It is NOT a live-trading, order or "
    "venue-POST authorization; all other gates remain closed and independent."
)


def read_approval_code(args) -> Optional[str]:
    """Approval code from stdin (``--code-stdin``) or an interactive prompt; never argv."""
    if getattr(args, "code_stdin", False):
        line = sys.stdin.readline()
        return line.rstrip("\r\n") or None
    if sys.stdin is not None and sys.stdin.isatty():
        return getpass.getpass("Enter approval code: ") or None
    return None


def resolve_exchange_connected_for_health(cli_choice: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Resolve ``exchange_connected`` for ``kill-switch health`` (NO-LIVE).

    Parameters
    ----------
    cli_choice:
        ``\"true\"`` / ``\"false\"`` — explicit override.
        ``\"auto\"`` — read :envvar:`PEAK_KILL_SWITCH_EXCHANGE_CONNECTED` if set
        (1/0, true/false, yes/no). If unset, run an HTTP GET to a public exchange URL
        (default Kraken ``SystemStatus``) unless :envvar:`PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED`
        is set — then returns ``True`` (air-gapped / legacy behaviour).
    """
    if cli_choice == "true":
        return True, {"exchange_connected_source": "cli_true"}
    if cli_choice == "false":
        return False, {"exchange_connected_source": "cli_false"}
    raw = os.environ.get(_EXCHANGE_CONNECTED_ENV, "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False, {"exchange_connected_source": "env", "env": _EXCHANGE_CONNECTED_ENV}
    if raw in ("1", "true", "yes", "on"):
        return True, {"exchange_connected_source": "env", "env": _EXCHANGE_CONNECTED_ENV}
    if is_exchange_probe_disabled():
        return True, {
            "exchange_connected_source": "probe_disabled_fallback",
            "note": "HTTP probe skipped (PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED).",
        }
    ok, meta = probe_exchange_http_public()
    return ok, meta


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
    if status.get("request_id"):
        print(f"Recovery request id: {status['request_id']}")
    if state == "ACTIVE":
        print(ACTIVE_IS_NOT_TRADING_AUTHORIZATION)
    return EXIT_OK


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
            return EXIT_ERROR

    persist_path = kill_switch.persistence_path
    if not persist_path:
        raise RuntimeError("kill_switch trigger did not persist state")
    try:
        success = kill_switch.trigger(reason, triggered_by="manual_cli")
    except KillSwitchKillPendingError:
        print("🚨 KILL JOURNALED; state write blocked by the state lock.")
        print(f"Every ACTIVE reader denies via the journal: {kill_switch.journal_path}")
        print("Re-run 'trigger' to persist KILLED once the lock is free.")
        return EXIT_KILL_PENDING
    except KillSwitchKillFailedError:
        print("❌ KILL could not be made durable (journal and state both failed).")
        return EXIT_KILL_FAILED

    if not success:
        print("❌ Failed to trigger (disabled)")
        return EXIT_KILL_FAILED
    print(f"🚨 KILL SWITCH TRIGGERED: {reason}")
    print("Trading is now BLOCKED.")
    print(f"Persisted state: {persist_path}")
    return EXIT_OK


def cmd_recover(args, kill_switch: KillSwitch):
    """Request kill switch recovery (KILLED → RECOVERING)."""
    reason = args.reason or "Recovery via CLI"
    persist_path = kill_switch.persistence_path
    if not persist_path:
        raise RuntimeError("kill_switch recovery did not persist state")

    success = kill_switch.request_recovery(
        approved_by=args.approved_by,
        approval_code=read_approval_code(args),
    )

    if not success:
        print(f"❌ Recovery request denied: {kill_switch.last_denial_reason}")
        return EXIT_DENIED
    print("⏳ RECOVERY STARTED")
    print(f"Reason: {reason}")
    print(f"Recovery request id: {kill_switch.pending_request_id}")
    print("Cooldown active. Use 'status' to check progress.")
    print(f"Persisted state: {persist_path} (RECOVERING still blocks trading)")
    return EXIT_OK


def cmd_complete_recovery(args, kill_switch: KillSwitch):
    """Complete an authorized recovery (RECOVERING → ACTIVE) after cooldown."""
    persist_path = kill_switch.persistence_path
    if not persist_path:
        raise RuntimeError("kill_switch completion requires durable state")

    success = kill_switch.complete_recovery(
        approved_by=args.approved_by,
        approval_code=read_approval_code(args),
        request_id=args.request_id,
    )
    if not success:
        print(f"❌ Recovery completion denied: {kill_switch.last_denial_reason}")
        return EXIT_DENIED
    print("✅ KILL SWITCH RECOVERY COMPLETED")
    print(ACTIVE_IS_NOT_TRADING_AUTHORIZATION)
    print(f"Persisted state: {persist_path}")
    print(f"Audit journal: {kill_switch.journal_path}")
    return EXIT_OK


def cmd_audit(args, config: dict):
    """Show audit trail (durable transition journal first, then legacy daily files)."""
    from src.ops.gates.risk_gate import canonical_kill_switch_state_path
    from src.risk_layer.kill_switch.recovery_attestation import journal_path_for_state_file

    journal = TransitionJournal(journal_path_for_state_file(canonical_kill_switch_state_path()))
    print(f"\n📒 TRANSITION JOURNAL: {journal.path}")
    try:
        journal_events = journal.read_events()
    except JournalError as exc:
        print(f"❌ Journal unreadable ({exc}); every ACTIVE reader denies.")
        return EXIT_DENIED
    for event in journal_events[-args.limit :]:
        print(
            f"{event.get('timestamp', ''):<27} {event.get('kind', ''):<19} "
            f"{event.get('new_state', ''):<11} {event.get('approved_by') or event.get('triggered_by') or ''} "
            f"{event.get('request_id') or ''} {event.get('reason_code') or ''}"
        )

    audit_dir = str(journal.path.parent)
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
        print("No legacy audit events found.")
        return EXIT_OK

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
    return EXIT_OK


def cmd_health(args, config: dict):
    """Check system health."""
    recovery_config = config.get("kill_switch.recovery", {})
    checker = HealthChecker(recovery_config)

    mode = getattr(args, "exchange_connected_mode", "auto")
    exchange_ok, exchange_meta = resolve_exchange_connected_for_health(mode)

    # Build context if possible
    context = {
        "exchange_connected": exchange_ok,
        "last_price_update": datetime.utcnow(),
    }

    print("Running health checks...\n")
    result = checker.check_all(context)
    result.metadata.update(exchange_meta)

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
    recover_parser.add_argument("--reason", help="Reason for recovery")
    recover_parser.add_argument("--approved-by", required=True, help="Approver identity")
    recover_parser.add_argument(
        "--code-stdin", action="store_true", help="Read the approval code from stdin"
    )

    complete_parser = subparsers.add_parser(
        "complete-recovery",
        help="Complete an authorized recovery after cooldown (not a trading authorization)",
    )
    complete_parser.add_argument("--approved-by", required=True, help="Approver identity")
    complete_parser.add_argument(
        "--request-id", required=True, help="Recovery request id printed by 'recover'"
    )
    complete_parser.add_argument(
        "--code-stdin", action="store_true", help="Read the approval code from stdin"
    )

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
            "Exchange connectivity for health: 'true'/'false' force; "
            "'auto' uses PEAK_KILL_SWITCH_EXCHANGE_CONNECTED if set, else HTTP public probe "
            "(unless PEAK_KILL_SWITCH_EXCHANGE_PROBE_DISABLED)."
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
    if args.command in ["status", "trigger", "recover", "complete-recovery"]:
        try:
            kill_switch = KillSwitch(kill_switch_config, logger=logger)
        except Exception as e:
            logger.error(f"Failed to initialize kill switch: {e}")
            return EXIT_ERROR

    # Execute command
    try:
        if args.command == "status":
            rc = cmd_status(args, kill_switch)
        elif args.command == "trigger":
            rc = cmd_trigger(args, kill_switch)
        elif args.command == "recover":
            rc = cmd_recover(args, kill_switch)
        elif args.command == "complete-recovery":
            rc = cmd_complete_recovery(args, kill_switch)
        elif args.command == "audit":
            rc = cmd_audit(args, config)
        elif args.command == "health":
            rc = cmd_health(args, config)
        else:
            parser.print_help()
            return EXIT_ERROR

        return EXIT_OK if rc is None else int(rc)

    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
