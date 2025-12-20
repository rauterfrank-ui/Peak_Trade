"""
Tests for telemetry health trends module (Phase 16H).
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.execution.telemetry_health import (
    HealthReport,
    HealthCheckResult,
    HealthThresholds,
)
from src.execution.telemetry_health_trends import (
    HealthSnapshot,
    TrendRollup,
    SNAPSHOT_SCHEMA_VERSION,
    append_snapshot,
    load_snapshots,
    prune_old_snapshots,
    compute_rollup,
    detect_degradation,
)


@pytest.fixture
def temp_snapshots_file(tmp_path):
    """Create a temporary snapshots file."""
    return tmp_path / "test_snapshots.jsonl"


def create_mock_health_report(severity="ok", disk_mb=100.0) -> HealthReport:
    """Create a mock HealthReport for testing."""
    checks = [
        HealthCheckResult(
            name="disk_usage",
            status=severity,
            message=f"Disk {disk_mb} MB",
            value=disk_mb,
            threshold_warn=1500.0,
            threshold_critical=1900.0,
        ),
        HealthCheckResult(
            name="retention_staleness",
            status="ok",
            message="Recent",
            value=10.0,
        ),
        HealthCheckResult(
            name="compression_failures",
            status="ok",
            message="No failures",
            value=0.0,
        ),
        HealthCheckResult(
            name="parse_error_rate",
            status="ok",
            message="No errors",
            value=0.0,
        ),
    ]
    
    report = HealthReport(checks=checks)
    return report


def test_snapshot_from_health_report():
    """Test creating snapshot from HealthReport."""
    report = create_mock_health_report(severity="ok", disk_mb=250.0)
    
    snapshot = HealthSnapshot.from_health_report(report, max_disk_mb=2048)
    
    assert snapshot.schema_version == SNAPSHOT_SCHEMA_VERSION
    assert snapshot.severity == "ok"
    assert snapshot.disk_usage_mb == 250.0
    assert 12.0 < snapshot.disk_usage_pct < 13.0  # ~250/2048 * 100
    assert isinstance(snapshot.ts_utc, datetime)
    assert len(snapshot.checks) == 4


def test_snapshot_to_dict():
    """Test snapshot serialization."""
    report = create_mock_health_report()
    snapshot = HealthSnapshot.from_health_report(report)
    
    data = snapshot.to_dict()
    
    assert "schema_version" in data
    assert "ts_utc" in data
    assert "severity" in data
    assert "metrics" in data
    assert "checks" in data
    
    assert data["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert data["severity"] == "ok"
    assert "disk_usage_mb" in data["metrics"]


def test_snapshot_from_dict():
    """Test snapshot deserialization."""
    data = {
        "schema_version": 1,
        "ts_utc": "2025-12-20T10:00:00+00:00",
        "severity": "ok",
        "metrics": {
            "disk_usage_mb": 100.0,
            "disk_usage_pct": 5.0,
            "retention_staleness_hours": 10.0,
            "compression_failure_rate": 0.0,
            "parse_error_rate": 0.0,
        },
        "checks": [],
    }
    
    snapshot = HealthSnapshot.from_dict(data)
    
    assert snapshot.schema_version == 1
    assert snapshot.severity == "ok"
    assert snapshot.disk_usage_mb == 100.0
    assert snapshot.disk_usage_pct == 5.0


def test_append_snapshot(temp_snapshots_file):
    """Test appending snapshot to file."""
    report = create_mock_health_report()
    snapshot = HealthSnapshot.from_health_report(report)
    
    success = append_snapshot(temp_snapshots_file, snapshot)
    
    assert success
    assert temp_snapshots_file.exists()
    
    # Verify content
    with open(temp_snapshots_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["severity"] == "ok"


def test_append_multiple_snapshots(temp_snapshots_file):
    """Test appending multiple snapshots."""
    for i in range(5):
        report = create_mock_health_report(disk_mb=100.0 + i * 10)
        snapshot = HealthSnapshot.from_health_report(report)
        append_snapshot(temp_snapshots_file, snapshot)
    
    with open(temp_snapshots_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 5


def test_load_snapshots_empty_file(temp_snapshots_file):
    """Test loading snapshots from non-existent file."""
    snapshots = load_snapshots(temp_snapshots_file)
    
    assert snapshots == []


def test_load_snapshots_basic(temp_snapshots_file):
    """Test loading snapshots from file."""
    # Create snapshots
    for i in range(3):
        report = create_mock_health_report()
        snapshot = HealthSnapshot.from_health_report(report)
        append_snapshot(temp_snapshots_file, snapshot)
    
    # Load
    snapshots = load_snapshots(temp_snapshots_file)
    
    assert len(snapshots) == 3
    assert all(isinstance(s, HealthSnapshot) for s in snapshots)


def test_load_snapshots_with_time_filter(temp_snapshots_file):
    """Test loading snapshots with time filtering."""
    now = datetime.now(timezone.utc)
    
    # Create snapshots at different times
    for i in range(5):
        report = create_mock_health_report()
        snapshot = HealthSnapshot.from_health_report(report)
        snapshot.ts_utc = now - timedelta(days=i)
        append_snapshot(temp_snapshots_file, snapshot)
    
    # Load recent only (last 2 days)
    since_ts = now - timedelta(days=2)
    snapshots = load_snapshots(temp_snapshots_file, since_ts=since_ts)
    
    assert len(snapshots) <= 3  # days 0, 1, 2


def test_load_snapshots_with_limit(temp_snapshots_file):
    """Test loading snapshots with limit."""
    for i in range(10):
        report = create_mock_health_report()
        snapshot = HealthSnapshot.from_health_report(report)
        append_snapshot(temp_snapshots_file, snapshot)
    
    snapshots = load_snapshots(temp_snapshots_file, limit=5)
    
    assert len(snapshots) == 5


def test_load_snapshots_ordering(temp_snapshots_file):
    """Test that snapshots are ordered by timestamp."""
    now = datetime.now(timezone.utc)
    
    # Create snapshots in reverse order
    for i in range(5, 0, -1):
        report = create_mock_health_report()
        snapshot = HealthSnapshot.from_health_report(report)
        snapshot.ts_utc = now - timedelta(days=i)
        append_snapshot(temp_snapshots_file, snapshot)
    
    snapshots = load_snapshots(temp_snapshots_file)
    
    # Should be ordered oldest first
    for i in range(len(snapshots) - 1):
        assert snapshots[i].ts_utc <= snapshots[i + 1].ts_utc


def test_prune_old_snapshots(temp_snapshots_file):
    """Test pruning old snapshots."""
    now = datetime.now(timezone.utc)
    
    # Create snapshots: 5 old, 5 recent
    for i in range(10):
        report = create_mock_health_report()
        snapshot = HealthSnapshot.from_health_report(report)
        snapshot.ts_utc = now - timedelta(days=100 - i * 10)
        append_snapshot(temp_snapshots_file, snapshot)
    
    # Prune (keep last 60 days)
    removed, kept = prune_old_snapshots(temp_snapshots_file, days=60)
    
    assert removed > 0
    assert kept > 0
    
    # Verify
    snapshots = load_snapshots(temp_snapshots_file)
    cutoff = now - timedelta(days=60)
    
    for snapshot in snapshots:
        assert snapshot.ts_utc >= cutoff


def test_compute_rollup_empty():
    """Test computing rollup with no snapshots."""
    rollup = compute_rollup([])
    
    assert rollup.snapshot_count == 0
    assert rollup.worst_severity == "ok"


def test_compute_rollup_basic(temp_snapshots_file):
    """Test computing rollup from snapshots."""
    # Create snapshots with varying disk usage
    disk_values = [100.0, 150.0, 200.0, 175.0, 125.0]
    
    snapshots = []
    for disk_mb in disk_values:
        report = create_mock_health_report(disk_mb=disk_mb)
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    rollup = compute_rollup(snapshots)
    
    assert rollup.snapshot_count == 5
    assert rollup.ok_count == 5
    assert rollup.warn_count == 0
    assert rollup.critical_count == 0
    assert rollup.worst_severity == "ok"
    
    assert rollup.disk_min == 100.0
    assert rollup.disk_max == 200.0
    assert 140.0 < rollup.disk_avg < 160.0  # Average of disk_values


def test_compute_rollup_with_warnings():
    """Test computing rollup with warnings."""
    snapshots = []
    
    # Create mixed severity snapshots
    for severity in ["ok", "warn", "critical", "ok", "warn"]:
        report = create_mock_health_report(severity=severity)
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    rollup = compute_rollup(snapshots)
    
    assert rollup.snapshot_count == 5
    assert rollup.ok_count == 2
    assert rollup.warn_count == 2
    assert rollup.critical_count == 1
    assert rollup.worst_severity == "critical"


def test_detect_degradation_insufficient_data():
    """Test degradation detection with insufficient data."""
    snapshots = []
    for i in range(5):
        report = create_mock_health_report()
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    result = detect_degradation(snapshots, window_size=10)
    
    assert not result["degrading"]
    assert result["reason"] == "insufficient data"


def test_detect_degradation_no_issues():
    """Test degradation detection with healthy snapshots."""
    snapshots = []
    for i in range(20):
        report = create_mock_health_report(severity="ok", disk_mb=100.0)
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    result = detect_degradation(snapshots, window_size=10)
    
    assert not result["degrading"]
    assert result["critical_count"] == 0
    assert result["warn_count"] == 0


def test_detect_degradation_high_critical_rate():
    """Test degradation detection with high critical rate."""
    snapshots = []
    
    # First 10: OK
    for i in range(10):
        report = create_mock_health_report(severity="ok")
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    # Last 10: mostly critical
    for i in range(10):
        severity = "critical" if i < 7 else "ok"
        report = create_mock_health_report(severity=severity)
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    result = detect_degradation(snapshots, window_size=10)
    
    assert result["degrading"]
    assert result["critical_count"] >= 5


def test_detect_degradation_disk_increasing():
    """Test degradation detection with increasing disk usage."""
    snapshots = []
    
    # Disk usage increasing over time
    for i in range(20):
        disk_mb = 100.0 + i * 20.0  # 100 -> 480 MB
        report = create_mock_health_report(severity="ok", disk_mb=disk_mb)
        snapshot = HealthSnapshot.from_health_report(report)
        snapshots.append(snapshot)
    
    result = detect_degradation(snapshots, window_size=10)
    
    assert result["degrading"]
    assert any("increasing" in r for r in result["reasons"])


def test_snapshot_schema_golden():
    """Golden test for snapshot schema."""
    report = create_mock_health_report()
    snapshot = HealthSnapshot.from_health_report(report)
    
    data = snapshot.to_dict()
    
    # Validate golden schema
    required_keys = {"schema_version", "ts_utc", "severity", "metrics", "checks"}
    assert required_keys.issubset(set(data.keys()))
    
    required_metrics = {
        "disk_usage_mb",
        "disk_usage_pct",
        "retention_staleness_hours",
        "compression_failure_rate",
        "parse_error_rate",
    }
    assert required_metrics.issubset(set(data["metrics"].keys()))
    
    assert isinstance(data["schema_version"], int)
    assert data["schema_version"] == 1
    assert isinstance(data["severity"], str)
    assert data["severity"] in ("ok", "warn", "critical")
