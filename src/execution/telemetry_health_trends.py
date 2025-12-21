"""
Telemetry Health Trends - Phase 16H

Historical health metrics tracking with time series analysis.

Storage:
- JSONL append-only snapshots (telemetry_health_snapshots.jsonl)
- Versioned schema for future compatibility
- Automatic pruning (90 days default retention)

Features:
- Load snapshots with time filtering
- Compute rollups (min/avg/max, severity counts)
- Trend analysis (degradation detection)
- Graceful degradation (missing data handled)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SNAPSHOT_SCHEMA_VERSION = 1


@dataclass
class HealthSnapshot:
    """Single point-in-time health snapshot."""

    schema_version: int
    ts_utc: datetime
    severity: str  # "ok" | "warn" | "critical"

    # Metrics (numeric values for trending)
    disk_usage_mb: float
    disk_usage_pct: float  # vs threshold
    retention_staleness_hours: Optional[float]
    compression_failure_rate: float
    parse_error_rate: float

    # Raw check results
    checks: List[Dict]

    @classmethod
    def from_health_report(cls, report, max_disk_mb: int = 2048):
        """Create snapshot from HealthReport."""
        from src.execution.telemetry_health import HealthReport

        if not isinstance(report, HealthReport):
            raise TypeError(f"Expected HealthReport, got {type(report)}")

        # Extract metrics from checks
        disk_mb = 0.0
        retention_hours = None
        compression_rate = 0.0
        parse_rate = 0.0

        for check in report.checks:
            if check.name == "disk_usage":
                disk_mb = check.value or 0.0
            elif check.name == "retention_staleness":
                retention_hours = check.value
            elif check.name == "compression_failures":
                compression_rate = check.value or 0.0
            elif check.name == "parse_error_rate":
                parse_rate = check.value or 0.0

        return cls(
            schema_version=SNAPSHOT_SCHEMA_VERSION,
            ts_utc=report.timestamp,
            severity=report.status,
            disk_usage_mb=disk_mb,
            disk_usage_pct=(disk_mb / max_disk_mb * 100) if max_disk_mb > 0 else 0.0,
            retention_staleness_hours=retention_hours,
            compression_failure_rate=compression_rate,
            parse_error_rate=parse_rate,
            checks=[c.__dict__ if hasattr(c, "__dict__") else c for c in report.checks],
        )

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "ts_utc": self.ts_utc.isoformat() if isinstance(self.ts_utc, datetime) else self.ts_utc,
            "severity": self.severity,
            "metrics": {
                "disk_usage_mb": self.disk_usage_mb,
                "disk_usage_pct": self.disk_usage_pct,
                "retention_staleness_hours": self.retention_staleness_hours,
                "compression_failure_rate": self.compression_failure_rate,
                "parse_error_rate": self.parse_error_rate,
            },
            "checks": self.checks,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Load snapshot from dict."""
        ts_str = data.get("ts_utc", "")
        ts_utc = (
            datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts_str
            else datetime.now(timezone.utc)
        )

        metrics = data.get("metrics", {})

        return cls(
            schema_version=data.get("schema_version", 1),
            ts_utc=ts_utc,
            severity=data.get("severity", "ok"),
            disk_usage_mb=metrics.get("disk_usage_mb", 0.0),
            disk_usage_pct=metrics.get("disk_usage_pct", 0.0),
            retention_staleness_hours=metrics.get("retention_staleness_hours"),
            compression_failure_rate=metrics.get("compression_failure_rate", 0.0),
            parse_error_rate=metrics.get("parse_error_rate", 0.0),
            checks=data.get("checks", []),
        )


@dataclass
class TrendRollup:
    """Aggregated health metrics over a time period."""

    period_start: datetime
    period_end: datetime

    # Severity counts
    ok_count: int = 0
    warn_count: int = 0
    critical_count: int = 0

    # Disk usage stats (MB)
    disk_min: float = 0.0
    disk_avg: float = 0.0
    disk_max: float = 0.0

    # Parse error rate stats (%)
    parse_error_min: float = 0.0
    parse_error_avg: float = 0.0
    parse_error_max: float = 0.0

    # Compression failure stats (%)
    compression_failure_min: float = 0.0
    compression_failure_avg: float = 0.0
    compression_failure_max: float = 0.0

    # Worst severity in period
    worst_severity: str = "ok"

    # Total snapshots analyzed
    snapshot_count: int = 0


def append_snapshot(path: Path, snapshot: HealthSnapshot) -> bool:
    """
    Append health snapshot to JSONL file.

    Returns:
        True if successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "a", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f)
            f.write("\n")

        return True
    except Exception as e:
        logger.error(f"Failed to append snapshot: {e}")
        return False


def load_snapshots(
    path: Path,
    since_ts: Optional[datetime] = None,
    until_ts: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> List[HealthSnapshot]:
    """
    Load health snapshots from JSONL file.

    Args:
        path: Path to snapshots file
        since_ts: Only load snapshots after this timestamp (inclusive)
        until_ts: Only load snapshots before this timestamp (inclusive)
        limit: Maximum number of snapshots to return (most recent first)

    Returns:
        List of HealthSnapshot objects, ordered by timestamp (oldest first)
    """
    if not path.exists():
        logger.debug(f"Snapshots file not found: {path}")
        return []

    snapshots = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    snapshot = HealthSnapshot.from_dict(data)

                    # Apply time filters
                    if since_ts and snapshot.ts_utc < since_ts:
                        continue
                    if until_ts and snapshot.ts_utc > until_ts:
                        continue

                    snapshots.append(snapshot)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_no}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to parse snapshot at line {line_no}: {e}")

        # Sort by timestamp (oldest first)
        snapshots.sort(key=lambda s: s.ts_utc)

        # Apply limit (keep most recent)
        if limit and len(snapshots) > limit:
            snapshots = snapshots[-limit:]

        return snapshots

    except Exception as e:
        logger.error(f"Failed to load snapshots: {e}")
        return []


def prune_old_snapshots(path: Path, days: int = 90) -> Tuple[int, int]:
    """
    Remove snapshots older than N days.

    Args:
        path: Path to snapshots file
        days: Keep snapshots from last N days

    Returns:
        Tuple of (removed_count, kept_count)
    """
    if not path.exists():
        return (0, 0)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        # Read all snapshots
        snapshots = load_snapshots(path)

        # Filter recent ones
        recent_snapshots = [s for s in snapshots if s.ts_utc >= cutoff]

        removed_count = len(snapshots) - len(recent_snapshots)

        if removed_count > 0:
            # Rewrite file with recent snapshots only
            path.unlink()
            for snapshot in recent_snapshots:
                append_snapshot(path, snapshot)

            logger.info(f"Pruned {removed_count} old snapshots (kept {len(recent_snapshots)})")

        return (removed_count, len(recent_snapshots))

    except Exception as e:
        logger.error(f"Failed to prune snapshots: {e}")
        return (0, 0)


def compute_rollup(snapshots: List[HealthSnapshot]) -> TrendRollup:
    """
    Compute aggregated metrics from a list of snapshots.

    Args:
        snapshots: List of HealthSnapshot objects

    Returns:
        TrendRollup with min/avg/max stats
    """
    if not snapshots:
        return TrendRollup(
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
        )

    # Sort by timestamp
    snapshots_sorted = sorted(snapshots, key=lambda s: s.ts_utc)

    rollup = TrendRollup(
        period_start=snapshots_sorted[0].ts_utc,
        period_end=snapshots_sorted[-1].ts_utc,
        snapshot_count=len(snapshots),
    )

    # Count severities
    for snapshot in snapshots:
        if snapshot.severity == "ok":
            rollup.ok_count += 1
        elif snapshot.severity == "warn":
            rollup.warn_count += 1
        elif snapshot.severity == "critical":
            rollup.critical_count += 1

    # Determine worst severity
    if rollup.critical_count > 0:
        rollup.worst_severity = "critical"
    elif rollup.warn_count > 0:
        rollup.worst_severity = "warn"
    else:
        rollup.worst_severity = "ok"

    # Compute disk usage stats
    disk_values = [s.disk_usage_mb for s in snapshots]
    if disk_values:
        rollup.disk_min = min(disk_values)
        rollup.disk_max = max(disk_values)
        rollup.disk_avg = sum(disk_values) / len(disk_values)

    # Compute parse error stats
    parse_values = [s.parse_error_rate for s in snapshots]
    if parse_values:
        rollup.parse_error_min = min(parse_values)
        rollup.parse_error_max = max(parse_values)
        rollup.parse_error_avg = sum(parse_values) / len(parse_values)

    # Compute compression failure stats
    compress_values = [s.compression_failure_rate for s in snapshots]
    if compress_values:
        rollup.compression_failure_min = min(compress_values)
        rollup.compression_failure_max = max(compress_values)
        rollup.compression_failure_avg = sum(compress_values) / len(compress_values)

    return rollup


def detect_degradation(snapshots: List[HealthSnapshot], window_size: int = 10) -> Dict:
    """
    Detect health degradation trends.

    Args:
        snapshots: List of HealthSnapshot objects (ordered by time)
        window_size: Number of recent snapshots to analyze

    Returns:
        Dict with degradation indicators
    """
    if len(snapshots) < window_size:
        return {
            "degrading": False,
            "reason": "insufficient data",
            "window_size": window_size,
            "available": len(snapshots),
        }

    recent = snapshots[-window_size:]

    # Check severity trend
    critical_count = sum(1 for s in recent if s.severity == "critical")
    warn_count = sum(1 for s in recent if s.severity == "warn")

    degrading = False
    reasons = []

    # Degradation indicators
    if critical_count >= window_size * 0.5:
        degrading = True
        reasons.append(f"High critical rate ({critical_count}/{window_size})")

    if warn_count + critical_count >= window_size * 0.7:
        degrading = True
        reasons.append(f"High warn+critical rate ({warn_count + critical_count}/{window_size})")

    # Disk usage trend (increasing)
    disk_values = [s.disk_usage_mb for s in recent]
    if len(disk_values) >= 3:
        # Simple trend: compare first half vs second half
        mid = len(disk_values) // 2
        first_half_avg = sum(disk_values[:mid]) / mid
        second_half_avg = sum(disk_values[mid:]) / (len(disk_values) - mid)

        if second_half_avg > first_half_avg * 1.2:  # 20% increase
            degrading = True
            reasons.append(
                f"Disk usage increasing ({first_half_avg:.1f} → {second_half_avg:.1f} MB)"
            )

    return {
        "degrading": degrading,
        "reasons": reasons,
        "critical_count": critical_count,
        "warn_count": warn_count,
        "window_size": window_size,
    }
