#!/usr/bin/env python3
"""
Telemetry Retention & Compression CLI - Phase 16E

Manage telemetry log lifecycle: compress old logs, delete expired logs.

Usage:
    # Dry-run (default, safe)
    python scripts/ops/telemetry_retention.py

    # Apply changes
    python scripts/ops/telemetry_retention.py --apply

    # Custom root directory
    python scripts/ops/telemetry_retention.py --root logs/execution

    # JSON output
    python scripts/ops/telemetry_retention.py --json

    # Custom policy
    python scripts/ops/telemetry_retention.py --apply \\
        --max-age-days 14 \\
        --keep-last-n 100 \\
        --compress-after-days 3

Safety:
- Dry-run is default (--apply required to modify files)
- Root directory validation (must contain "execution"/"telemetry"/"logs")
- Session-count protection (keeps last N sessions even if old)
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.execution.telemetry_retention import (
    RetentionPolicy,
    apply_plan,
    build_plan,
    discover_sessions,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Telemetry retention & compression (Phase 16E)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Root directory
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("logs/execution"),
        help="Telemetry logs root directory (default: logs/execution)",
    )

    # Apply changes
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default: dry-run only)",
    )

    # Policy overrides
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=30,
        help="Delete logs older than N days (default: 30)",
    )

    parser.add_argument(
        "--keep-last-n",
        type=int,
        default=200,
        help="Always keep last N sessions (default: 200)",
    )

    parser.add_argument(
        "--max-total-mb",
        type=int,
        default=2048,
        help="Max total size in MB (default: 2048)",
    )

    parser.add_argument(
        "--compress-after-days",
        type=int,
        default=7,
        help="Compress logs older than N days (default: 7, 0=disable)",
    )

    parser.add_argument(
        "--protect-keep-last",
        action="store_true",
        help="Protect last N sessions from compression",
    )

    parser.add_argument(
        "--disabled",
        action="store_true",
        help="Disable all retention (show stats only)",
    )

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    # Build policy
    policy = RetentionPolicy(
        enabled=not args.disabled,
        max_age_days=args.max_age_days,
        keep_last_n_sessions=args.keep_last_n,
        max_total_mb=args.max_total_mb,
        compress_after_days=args.compress_after_days,
        protect_keep_last_from_compress=args.protect_keep_last,
    )

    # Discover sessions
    try:
        sessions = discover_sessions(args.root)
    except ValueError as e:
        logger.error(f"Invalid root directory: {e}")
        return 2
    except Exception as e:
        logger.error(f"Failed to discover sessions: {e}")
        return 3

    if not sessions:
        logger.info(f"No telemetry logs found in {args.root}")
        return 0

    # Build plan
    plan = build_plan(sessions, policy)

    # Apply plan
    dry_run = not args.apply
    stats = apply_plan(plan, dry_run=dry_run)

    # Output
    if args.json:
        output = {
            "root": str(args.root),
            "dry_run": dry_run,
            "policy": {
                "enabled": policy.enabled,
                "max_age_days": policy.max_age_days,
                "keep_last_n_sessions": policy.keep_last_n_sessions,
                "max_total_mb": policy.max_total_mb,
                "compress_after_days": policy.compress_after_days,
                "protect_keep_last_from_compress": policy.protect_keep_last_from_compress,
            },
            "plan": {
                "sessions_total": plan.sessions_total,
                "sessions_kept": plan.sessions_kept,
                "size_before_mb": plan.size_before_mb,
                "size_after_mb": plan.size_after_mb,
                "compression_savings_mb": plan.compression_savings_mb,
                "deleted_mb": plan.deleted_mb,
                "actions": [
                    {
                        "kind": a.kind,
                        "path": str(a.path),
                        "reason": a.reason,
                        "size_mb": a.size_mb,
                    }
                    for a in plan.actions
                ],
            },
            "stats": stats,
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        mode = "DRY-RUN" if dry_run else "APPLIED"
        print(f"\n{'=' * 60}")
        print(f"Telemetry Retention & Compression - {mode}")
        print(f"{'=' * 60}")
        print(f"Root: {args.root}")
        print(f"Policy: {'ENABLED' if policy.enabled else 'DISABLED'}")

        if policy.enabled:
            print(f"  Max age: {policy.max_age_days} days")
            print(f"  Keep last: {policy.keep_last_n_sessions} sessions")
            print(f"  Max total: {policy.max_total_mb} MB")
            print(f"  Compress after: {policy.compress_after_days} days")
            print(f"  Protect from compress: {policy.protect_keep_last_from_compress}")

        print(f"\nSummary:")
        print(f"  Total sessions: {plan.sessions_total}")
        print(f"  Sessions kept: {plan.sessions_kept}")
        print(f"  Size before: {plan.size_before_mb:.1f} MB")
        print(f"  Size after: {plan.size_after_mb:.1f} MB")
        print(f"  Compression savings: {plan.compression_savings_mb:.1f} MB")
        print(f"  Deleted: {plan.deleted_mb:.1f} MB")

        if plan.actions:
            print(f"\nActions ({len(plan.actions)}):")

            # Group by kind
            compress_actions = [a for a in plan.actions if a.kind == "compress"]
            delete_actions = [a for a in plan.actions if a.kind == "delete"]

            if compress_actions:
                print(f"\n  Compress ({len(compress_actions)}):")
                for action in compress_actions[:10]:  # Show first 10
                    print(f"    - {action.path.name} ({action.size_mb:.1f} MB)")
                    print(f"      Reason: {action.reason}")

                if len(compress_actions) > 10:
                    print(f"    ... and {len(compress_actions) - 10} more")

            if delete_actions:
                print(f"\n  Delete ({len(delete_actions)}):")
                for action in delete_actions[:10]:  # Show first 10
                    print(f"    - {action.path.name} ({action.size_mb:.1f} MB)")
                    print(f"      Reason: {action.reason}")

                if len(delete_actions) > 10:
                    print(f"    ... and {len(delete_actions) - 10} more")
        else:
            print(f"\nNo actions needed.")

        if stats["errors"]:
            print(f"\nErrors ({len(stats['errors'])}):")
            for error in stats["errors"]:
                print(f"  - {error}")

        print(f"\n{'=' * 60}")

        if dry_run:
            print("DRY-RUN: No files were modified.")
            print("Use --apply to execute changes.")
        else:
            print(f"APPLIED: {stats['actions_executed']} actions executed.")
            print(f"  Compressed: {stats['compressed']}")
            print(f"  Deleted: {stats['deleted']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
