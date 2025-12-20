#!/usr/bin/env python3
"""
Telemetry Alerts Runner - Phase 16I

Evaluates alert rules against health + trend analysis and routes alerts.

Usage:
    # Dry-run (default): print alerts but don't send
    python scripts/telemetry_alerts.py

    # Dry-run with explicit flag
    python scripts/telemetry_alerts.py --dry-run

    # Live run: send alerts to configured sinks
    python scripts/telemetry_alerts.py --no-dry-run

    # Specify sink explicitly
    python scripts/telemetry_alerts.py --sink console
    python scripts/telemetry_alerts.py --sink webhook --no-dry-run

    # Limit max alerts
    python scripts/telemetry_alerts.py --max 10

    # Custom telemetry root
    python scripts/telemetry_alerts.py --root logs/execution

    # Custom snapshots path
    python scripts/telemetry_alerts.py --snapshots logs/health_snapshots.jsonl

Exit codes:
    0 = No critical alerts and health OK
    2 = Critical alert(s) emitted OR health critical
    1 = Partial failures (e.g., webhook send failed) but engine ran
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.execution.telemetry_health import run_health_checks, HealthThresholds
from src.execution.telemetry_health_trends import load_snapshots, compute_rollup, detect_degradation
from src.execution.alerting import AlertEngine, AlertSeverity
from src.execution.alerting.rules import DEFAULT_RULES
from src.execution.alerting.adapters import ConsoleAlertSink, WebhookAlertSink
from src.execution.alerting.persistence import get_global_alert_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load alerting config (simple TOML loader)."""
    config_path = Path("config/telemetry_alerting.toml")
    
    if not config_path.exists():
        logger.warning(f"Config not found: {config_path}, using defaults")
        return {}
    
    try:
        import toml
        return toml.load(config_path)
    except ImportError:
        logger.warning("toml not available, using defaults")
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Telemetry Alerts Runner (Phase 16I)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry-run (default)
    python scripts/telemetry_alerts.py

    # Live run
    python scripts/telemetry_alerts.py --no-dry-run

    # Custom sink
    python scripts/telemetry_alerts.py --sink webhook --no-dry-run

    # Limit alerts
    python scripts/telemetry_alerts.py --max 5

Exit codes:
    0 = No critical alerts and health OK
    2 = Critical alert(s) emitted OR health critical
    1 = Partial failures (e.g., webhook send failed) but engine ran
        """,
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=Path("logs/execution"),
        help="Telemetry logs root directory (default: logs/execution)",
    )
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=Path("logs/telemetry_health_snapshots.jsonl"),
        help="Health snapshots file (default: logs/telemetry_health_snapshots.jsonl)",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Dry-run mode: print alerts but don't send (default)",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Live mode: send alerts to configured sinks",
    )
    parser.add_argument(
        "--sink",
        choices=["console", "webhook"],
        default="console",
        help="Alert sink (default: console)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=20,
        help="Maximum alerts per run (default: 20)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days of trend data to analyze (default: 30)",
    )

    args = parser.parse_args()

    # Load config
    config = load_config()
    alerting_config = config.get("telemetry", {}).get("alerting", {})

    # Check if alerting is enabled
    if not alerting_config.get("enabled", False):
        logger.warning("Alerting is disabled in config")
        print("⚠️  Alerting disabled (set telemetry.alerting.enabled = true in config)")
        return 0

    # Run health checks
    logger.info(f"Running health checks (root: {args.root})...")
    health_report = None
    
    try:
        report = run_health_checks(args.root)
        health_report = report.to_dict()
    except Exception as e:
        logger.error(f"Health checks failed: {e}", exc_info=True)
        health_report = {
            "status": "critical",
            "exit_code": 3,
            "checks": [],
            "error": str(e),
        }

    # Load trend data
    logger.info(f"Loading trend data (last {args.days} days)...")
    trend_report = None
    
    try:
        if args.snapshots.exists():
            since_ts = datetime.now(timezone.utc) - timedelta(days=args.days)
            snapshots = load_snapshots(args.snapshots, since_ts=since_ts)
            
            if snapshots:
                rollup = compute_rollup(snapshots)
                degradation = detect_degradation(snapshots, window_size=min(10, len(snapshots)))
                
                trend_report = {
                    "degradation": degradation,
                    "overall": {
                        "worst_severity": rollup.worst_severity,
                        "ok_count": rollup.ok_count,
                        "warn_count": rollup.warn_count,
                        "critical_count": rollup.critical_count,
                    },
                }
            else:
                logger.warning("No trend snapshots found")
        else:
            logger.warning(f"Snapshots file not found: {args.snapshots}")
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}", exc_info=True)

    # Build alert engine
    logger.info(f"Evaluating alert rules (max {args.max} alerts)...")
    engine = AlertEngine(rules=DEFAULT_RULES.copy(), max_alerts_per_run=args.max)

    # Evaluate rules
    alerts = engine.evaluate(health_report=health_report, trend_report=trend_report)

    if not alerts:
        print("✅ No alerts triggered")
        return 0

    # Summary
    print(f"\n🚨 {len(alerts)} alert(s) triggered:")
    print()

    critical_count = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
    warn_count = sum(1 for a in alerts if a.severity == AlertSeverity.WARN)
    info_count = sum(1 for a in alerts if a.severity == AlertSeverity.INFO)

    print(f"  🔴 CRITICAL: {critical_count}")
    print(f"  ⚠️  WARN: {warn_count}")
    print(f"  ℹ️  INFO: {info_count}")
    print()

    # Build sink
    if args.dry_run:
        print("🔧 DRY-RUN MODE (alerts will be printed but not sent)\n")
        sink = ConsoleAlertSink(color=True)
    else:
        if args.sink == "console":
            sink = ConsoleAlertSink(color=True)
        elif args.sink == "webhook":
            webhook_config = alerting_config.get("webhook", {})
            url = webhook_config.get("url", "")
            enabled = webhook_config.get("enabled", False)
            
            if not enabled or not url:
                logger.error("Webhook sink not configured (enable + URL required)")
                print("❌ Webhook sink not configured")
                return 1
            
            sink = WebhookAlertSink(url=url, enabled=True, timeout=10)
        else:
            logger.error(f"Unknown sink: {args.sink}")
            return 1

    # Send alerts + store
    send_failures = 0
    alert_store = get_global_alert_store()
    
    for alert in alerts:
        success = sink.send(alert)
        if not success:
            send_failures += 1
        
        # Store alert (for dashboard/API)
        alert_store.add(alert)

    # Exit code
    if critical_count > 0:
        return 2
    elif send_failures > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
