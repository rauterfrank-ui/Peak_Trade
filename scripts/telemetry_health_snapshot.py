#!/usr/bin/env python3
"""
Telemetry Health Snapshot Capture - Phase 16H

Captures current health status and appends to historical snapshots file.

Usage:
    # Default (logs/telemetry_health_snapshots.jsonl)
    python scripts/telemetry_health_snapshot.py

    # Custom output
    python scripts/telemetry_health_snapshot.py --out snapshots/health.jsonl

    # Custom telemetry root
    python scripts/telemetry_health_snapshot.py --root logs/execution

    # Quiet mode (no console output)
    python scripts/telemetry_health_snapshot.py --quiet

Exit codes:
    0 = Success (snapshot captured)
    1 = Error (failed to capture or write)
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution.telemetry_health import run_health_checks, HealthThresholds
from src.execution.telemetry_health_trends import HealthSnapshot, append_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture telemetry health snapshot (Phase 16H)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default output
    python scripts/telemetry_health_snapshot.py

    # Custom output file
    python scripts/telemetry_health_snapshot.py --out snapshots/health.jsonl

    # Custom telemetry root + quiet
    python scripts/telemetry_health_snapshot.py --root logs/execution --quiet

Exit codes:
    0 = Success (snapshot captured)
    1 = Error (failed to capture or write)
        """,
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=Path("logs/execution"),
        help="Telemetry logs root directory (default: logs/execution)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("logs/telemetry_health_snapshots.jsonl"),
        help="Output snapshots file (default: logs/telemetry_health_snapshots.jsonl)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )

    # Threshold overrides (same as health check CLI)
    parser.add_argument(
        "--disk-warn-mb",
        type=int,
        default=1500,
        help="Disk usage warning threshold in MB (default: 1500)",
    )
    parser.add_argument(
        "--disk-critical-mb",
        type=int,
        default=1900,
        help="Disk usage critical threshold in MB (default: 1900)",
    )
    parser.add_argument(
        "--max-disk-mb",
        type=int,
        default=2048,
        help="Max disk size for percentage calculation (default: 2048)",
    )

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.WARNING)

    # Build thresholds
    thresholds = HealthThresholds(
        disk_warn_mb=args.disk_warn_mb,
        disk_critical_mb=args.disk_critical_mb,
    )

    try:
        # Run health checks
        logger.info(f"Running health checks (root: {args.root})...")
        report = run_health_checks(args.root, thresholds)

        # Create snapshot
        snapshot = HealthSnapshot.from_health_report(report, max_disk_mb=args.max_disk_mb)

        # Append to file
        logger.info(f"Appending snapshot to {args.out}...")
        success = append_snapshot(args.out, snapshot)

        if not success:
            logger.error("Failed to append snapshot")
            return 1

        if not args.quiet:
            print(f"✅ Snapshot captured at {snapshot.ts_utc.isoformat()}")
            print(f"   Severity: {snapshot.severity.upper()}")
            print(f"   Disk: {snapshot.disk_usage_mb:.1f} MB ({snapshot.disk_usage_pct:.1f}%)")
            print(f"   Parse error rate: {snapshot.parse_error_rate:.1f}%")
            print(f"   Output: {args.out}")

        return 0

    except Exception as e:
        logger.error(f"Failed to capture snapshot: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
