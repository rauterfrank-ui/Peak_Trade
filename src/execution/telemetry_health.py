"""
Telemetry Health Checks - Phase 16F

Health monitoring for telemetry logs with configurable thresholds.

Exit codes:
- 0: OK (all checks pass)
- 2: WARNING (non-critical threshold exceeded)
- 3: CRITICAL (critical threshold exceeded)

Checks:
- Disk usage (telemetry directory size)
- Retention staleness (last retention run age)
- Compression failures (recent failure rate)
- Parse error rate (JSONL validity)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HealthThresholds:
    """Configurable thresholds for health checks."""

    # Disk usage (MB)
    disk_warn_mb: int = 1500  # Warn at 1.5 GB
    disk_critical_mb: int = 1900  # Critical at 1.9 GB (near 2 GB default limit)

    # Retention staleness (hours since last successful run)
    retention_warn_hours: int = 48  # Warn if no retention run in 48h
    retention_critical_hours: int = 168  # Critical if no run in 7 days

    # Compression failure rate (percentage)
    compress_warn_rate: float = 10.0  # Warn at 10% failure rate
    compress_critical_rate: float = 25.0  # Critical at 25% failure rate

    # Parse error rate (percentage)
    parse_warn_rate: float = 5.0  # Warn at 5% invalid lines
    parse_critical_rate: float = 15.0  # Critical at 15% invalid lines


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    status: str  # "ok" | "warn" | "critical"
    message: str
    value: Optional[float] = None
    threshold_warn: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class HealthReport:
    """Aggregate health report."""

    checks: List[HealthCheckResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def status(self) -> str:
        """Overall status (worst of all checks)."""
        if any(c.status == "critical" for c in self.checks):
            return "critical"
        if any(c.status == "warn" for c in self.checks):
            return "warn"
        return "ok"

    @property
    def exit_code(self) -> int:
        """Exit code for CLI (0=ok, 2=warn, 3=critical)."""
        if self.status == "critical":
            return 3
        if self.status == "warn":
            return 2
        return 0

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "exit_code": self.exit_code,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "value": c.value,
                    "threshold_warn": c.threshold_warn,
                    "threshold_critical": c.threshold_critical,
                }
                for c in self.checks
            ],
        }


def get_directory_size_mb(path: Path) -> float:
    """Calculate total size of directory in MB."""
    if not path.exists():
        return 0.0

    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except (OSError, PermissionError) as e:
        logger.warning(f"Error calculating directory size: {e}")
        return 0.0

    return total / (1024 * 1024)  # Convert to MB


def check_disk_usage(telemetry_root: Path, thresholds: HealthThresholds) -> HealthCheckResult:
    """Check telemetry directory disk usage."""
    size_mb = get_directory_size_mb(telemetry_root)

    if size_mb >= thresholds.disk_critical_mb:
        status = "critical"
        msg = f"Disk usage {size_mb:.1f} MB exceeds critical threshold"
    elif size_mb >= thresholds.disk_warn_mb:
        status = "warn"
        msg = f"Disk usage {size_mb:.1f} MB exceeds warning threshold"
    else:
        status = "ok"
        msg = f"Disk usage {size_mb:.1f} MB is within limits"

    return HealthCheckResult(
        name="disk_usage",
        status=status,
        message=msg,
        value=size_mb,
        threshold_warn=float(thresholds.disk_warn_mb),
        threshold_critical=float(thresholds.disk_critical_mb),
    )


def check_retention_staleness(
    telemetry_root: Path, thresholds: HealthThresholds
) -> HealthCheckResult:
    """Check if retention hasn't run recently."""
    # Look for marker file or recent .jsonl.gz files
    marker_file = telemetry_root / ".last_retention_run"

    last_run: Optional[datetime] = None

    if marker_file.exists():
        try:
            mtime = marker_file.stat().st_mtime
            last_run = datetime.fromtimestamp(mtime, tz=timezone.utc)
        except OSError:
            pass

    # Fallback: check for recent compressed files
    if last_run is None and telemetry_root.exists():
        try:
            gz_files = list(telemetry_root.glob("*.jsonl.gz"))
            if gz_files:
                most_recent_mtime = max(f.stat().st_mtime for f in gz_files)
                last_run = datetime.fromtimestamp(most_recent_mtime, tz=timezone.utc)
        except OSError:
            pass

    if last_run is None:
        # No retention evidence found
        return HealthCheckResult(
            name="retention_staleness",
            status="ok",
            message="No retention history found (first run or no logs)",
            value=None,
        )

    age_hours = (datetime.now(timezone.utc) - last_run).total_seconds() / 3600

    if age_hours >= thresholds.retention_critical_hours:
        status = "critical"
        msg = f"Retention hasn't run in {age_hours:.1f} hours (critical)"
    elif age_hours >= thresholds.retention_warn_hours:
        status = "warn"
        msg = f"Retention hasn't run in {age_hours:.1f} hours (warning)"
    else:
        status = "ok"
        msg = f"Retention last run {age_hours:.1f} hours ago (ok)"

    return HealthCheckResult(
        name="retention_staleness",
        status=status,
        message=msg,
        value=age_hours,
        threshold_warn=float(thresholds.retention_warn_hours),
        threshold_critical=float(thresholds.retention_critical_hours),
    )


def check_compression_failures(
    telemetry_root: Path, thresholds: HealthThresholds
) -> HealthCheckResult:
    """Check for compression failure rate."""
    # Look for compression error markers or orphaned .tmp files
    if not telemetry_root.exists():
        return HealthCheckResult(
            name="compression_failures",
            status="ok",
            message="No telemetry logs found",
            value=0.0,
        )

    try:
        all_jsonl = list(telemetry_root.glob("*.jsonl"))
        all_gz = list(telemetry_root.glob("*.jsonl.gz"))
        tmp_files = list(telemetry_root.glob("*.tmp"))

        # Heuristic: orphaned .tmp files indicate failed compressions
        total_compress_candidates = len(all_jsonl) + len(all_gz)
        failed_count = len(tmp_files)

        if total_compress_candidates == 0:
            failure_rate = 0.0
        else:
            failure_rate = (failed_count / total_compress_candidates) * 100

        if failure_rate >= thresholds.compress_critical_rate:
            status = "critical"
            msg = f"Compression failure rate {failure_rate:.1f}% (critical)"
        elif failure_rate >= thresholds.compress_warn_rate:
            status = "warn"
            msg = f"Compression failure rate {failure_rate:.1f}% (warning)"
        else:
            status = "ok"
            msg = f"Compression failure rate {failure_rate:.1f}% (ok)"

        return HealthCheckResult(
            name="compression_failures",
            status=status,
            message=msg,
            value=failure_rate,
            threshold_warn=thresholds.compress_warn_rate,
            threshold_critical=thresholds.compress_critical_rate,
        )
    except OSError as e:
        logger.warning(f"Error checking compression failures: {e}")
        return HealthCheckResult(
            name="compression_failures",
            status="warn",
            message=f"Could not check compression: {e}",
        )


def check_parse_error_rate(
    telemetry_root: Path, thresholds: HealthThresholds, sample_size: int = 1000
) -> HealthCheckResult:
    """Check JSONL parse error rate by sampling recent logs."""
    if not telemetry_root.exists():
        return HealthCheckResult(
            name="parse_error_rate",
            status="ok",
            message="No telemetry logs found",
            value=0.0,
        )

    try:
        import gzip
        import json

        # Sample most recent .jsonl or .jsonl.gz files
        jsonl_files = sorted(
            telemetry_root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        gz_files = sorted(
            telemetry_root.glob("*.jsonl.gz"), key=lambda p: p.stat().st_mtime, reverse=True
        )

        all_files = jsonl_files[:3] + gz_files[:3]  # Sample up to 6 recent files

        if not all_files:
            return HealthCheckResult(
                name="parse_error_rate",
                status="ok",
                message="No log files to check",
                value=0.0,
            )

        total_lines = 0
        error_lines = 0

        for file_path in all_files:
            if file_path.suffix == ".gz":
                opener = gzip.open(file_path, "rt", encoding="utf-8")
            else:
                opener = open(file_path, "r", encoding="utf-8")

            try:
                with opener as f:
                    for i, line in enumerate(f):
                        if i >= sample_size:
                            break
                        total_lines += 1
                        try:
                            json.loads(line.strip())
                        except json.JSONDecodeError:
                            error_lines += 1
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                continue

        if total_lines == 0:
            error_rate = 0.0
        else:
            error_rate = (error_lines / total_lines) * 100

        if error_rate >= thresholds.parse_critical_rate:
            status = "critical"
            msg = f"Parse error rate {error_rate:.1f}% ({error_lines}/{total_lines} lines)"
        elif error_rate >= thresholds.parse_warn_rate:
            status = "warn"
            msg = f"Parse error rate {error_rate:.1f}% ({error_lines}/{total_lines} lines)"
        else:
            status = "ok"
            msg = f"Parse error rate {error_rate:.1f}% ({error_lines}/{total_lines} lines sampled)"

        return HealthCheckResult(
            name="parse_error_rate",
            status=status,
            message=msg,
            value=error_rate,
            threshold_warn=thresholds.parse_warn_rate,
            threshold_critical=thresholds.parse_critical_rate,
        )
    except Exception as e:
        logger.warning(f"Error checking parse errors: {e}")
        return HealthCheckResult(
            name="parse_error_rate",
            status="warn",
            message=f"Could not check parse errors: {e}",
        )


def run_health_checks(
    telemetry_root: Path,
    thresholds: Optional[HealthThresholds] = None,
) -> HealthReport:
    """Run all health checks and return aggregate report."""
    if thresholds is None:
        thresholds = HealthThresholds()

    report = HealthReport()

    # Run checks
    report.checks.append(check_disk_usage(telemetry_root, thresholds))
    report.checks.append(check_retention_staleness(telemetry_root, thresholds))
    report.checks.append(check_compression_failures(telemetry_root, thresholds))
    report.checks.append(check_parse_error_rate(telemetry_root, thresholds))

    return report
