#!/usr/bin/env python3
"""
Telemetry Health Check CLI - Phase 16F

Check health of telemetry logs (disk usage, retention, compression, parse errors).

Exit codes:
- 0: OK (all checks pass)
- 2: WARNING (non-critical threshold exceeded)
- 3: CRITICAL (critical threshold exceeded)

Usage:
    # Default checks
    python scripts/telemetry_health_check.py

    # Custom root
    python scripts/telemetry_health_check.py --root logs/execution

    # JSON output
    python scripts/telemetry_health_check.py --json

    # Custom thresholds
    python scripts/telemetry_health_check.py --disk-warn-mb 1000 --disk-critical-mb 1800
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution.telemetry_health import (
    HealthThresholds,
    run_health_checks,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Telemetry health check CLI (Phase 16F)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default checks
    python scripts/telemetry_health_check.py

    # JSON output
    python scripts/telemetry_health_check.py --json

    # Custom thresholds
    python scripts/telemetry_health_check.py --disk-warn-mb 1000 --disk-critical-mb 1800

Exit codes:
    0 = OK (all checks pass)
    2 = WARNING (non-critical threshold exceeded)
    3 = CRITICAL (critical threshold exceeded)
        """,
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=Path("logs/execution"),
        help="Telemetry logs root directory (default: logs/execution)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Threshold overrides
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
        "--retention-warn-hours",
        type=int,
        default=48,
        help="Retention staleness warning threshold in hours (default: 48)",
    )
    parser.add_argument(
        "--retention-critical-hours",
        type=int,
        default=168,
        help="Retention staleness critical threshold in hours (default: 168)",
    )
    parser.add_argument(
        "--compress-warn-rate",
        type=float,
        default=10.0,
        help="Compression failure rate warning threshold in %% (default: 10.0)",
    )
    parser.add_argument(
        "--compress-critical-rate",
        type=float,
        default=25.0,
        help="Compression failure rate critical threshold in %% (default: 25.0)",
    )
    parser.add_argument(
        "--parse-warn-rate",
        type=float,
        default=5.0,
        help="Parse error rate warning threshold in %% (default: 5.0)",
    )
    parser.add_argument(
        "--parse-critical-rate",
        type=float,
        default=15.0,
        help="Parse error rate critical threshold in %% (default: 15.0)",
    )

    args = parser.parse_args()

    # Build thresholds
    thresholds = HealthThresholds(
        disk_warn_mb=args.disk_warn_mb,
        disk_critical_mb=args.disk_critical_mb,
        retention_warn_hours=args.retention_warn_hours,
        retention_critical_hours=args.retention_critical_hours,
        compress_warn_rate=args.compress_warn_rate,
        compress_critical_rate=args.compress_critical_rate,
        parse_warn_rate=args.parse_warn_rate,
        parse_critical_rate=args.parse_critical_rate,
    )

    # Run checks
    report = run_health_checks(args.root, thresholds)

    # Output
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("=== TELEMETRY HEALTH CHECK ===")
        print(f"Root: {args.root}")
        print(f"Timestamp: {report.timestamp.isoformat()}")
        print(f"Overall Status: {report.status.upper()}")
        print()

        for check in report.checks:
            status_emoji = {
                "ok": "✅",
                "warn": "⚠️ ",
                "critical": "🔴",
            }.get(check.status, "❓")

            print(f"{status_emoji} {check.name.upper()}: {check.status.upper()}")
            print(f"   {check.message}")
            if check.value is not None:
                print(f"   Value: {check.value:.1f}")
            if check.threshold_warn is not None:
                print(
                    f"   Thresholds: warn={check.threshold_warn:.1f}, critical={check.threshold_critical:.1f}"
                )
            print()

        print(f"Exit code: {report.exit_code}")

    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
