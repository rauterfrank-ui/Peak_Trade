"""
Tests for telemetry health check module (Phase 16F).
"""

import gzip
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.execution.telemetry_health import (
    HealthThresholds,
    check_disk_usage,
    check_retention_staleness,
    check_compression_failures,
    check_parse_error_rate,
    run_health_checks,
    get_directory_size_mb,
)


@pytest.fixture
def telemetry_root(tmp_path):
    """Create a temporary telemetry root directory."""
    root = tmp_path / "telemetry_logs"
    root.mkdir()
    return root


@pytest.fixture
def default_thresholds():
    """Default health check thresholds."""
    return HealthThresholds()


def create_log_file(root: Path, session_id: str, size_kb: int = 10, age_days: int = 0):
    """Helper to create a log file with specific size and age."""
    path = root / f"{session_id}.jsonl"

    # Create file with approximate size
    line = '{"ts": "2025-12-20T10:00:00Z", "kind": "test", "session_id": "' + session_id + '"}\n'
    line_size = len(line.encode("utf-8"))
    num_lines = (size_kb * 1024) // line_size
    content = line * num_lines
    path.write_text(content)

    # Set mtime
    if age_days > 0:
        mtime = datetime.now(timezone.utc) - timedelta(days=age_days)
        os.utime(path, (mtime.timestamp(), mtime.timestamp()))

    return path


def test_get_directory_size_mb(telemetry_root):
    """Test directory size calculation."""
    # Empty directory
    assert get_directory_size_mb(telemetry_root) == 0.0

    # Create some files
    create_log_file(telemetry_root, "session_1", size_kb=100)
    create_log_file(telemetry_root, "session_2", size_kb=200)

    size_mb = get_directory_size_mb(telemetry_root)
    assert 0.25 < size_mb < 0.35  # ~0.3 MB (accounting for overhead)


def test_get_directory_size_nonexistent():
    """Test directory size for non-existent path."""
    assert get_directory_size_mb(Path("/nonexistent")) == 0.0


def test_check_disk_usage_ok(telemetry_root, default_thresholds):
    """Test disk usage check - OK status."""
    create_log_file(telemetry_root, "session_1", size_kb=500)  # ~0.5 MB

    result = check_disk_usage(telemetry_root, default_thresholds)

    assert result.name == "disk_usage"
    assert result.status == "ok"
    assert result.value is not None
    assert result.value < 1.0  # Less than 1 MB


def test_check_disk_usage_warn(telemetry_root):
    """Test disk usage check - WARNING status."""
    thresholds = HealthThresholds(disk_warn_mb=1, disk_critical_mb=2)

    # Create ~1.2 MB
    for i in range(12):
        create_log_file(telemetry_root, f"session_{i}", size_kb=100)

    result = check_disk_usage(telemetry_root, thresholds)

    assert result.name == "disk_usage"
    assert result.status == "warn"
    assert result.value > thresholds.disk_warn_mb


def test_check_disk_usage_critical(telemetry_root):
    """Test disk usage check - CRITICAL status."""
    thresholds = HealthThresholds(disk_warn_mb=1, disk_critical_mb=2)

    # Create ~2.5 MB
    for i in range(25):
        create_log_file(telemetry_root, f"session_{i}", size_kb=100)

    result = check_disk_usage(telemetry_root, thresholds)

    assert result.name == "disk_usage"
    assert result.status == "critical"
    assert result.value > thresholds.disk_critical_mb


def test_check_retention_staleness_no_history(telemetry_root, default_thresholds):
    """Test retention staleness check - no history."""
    result = check_retention_staleness(telemetry_root, default_thresholds)

    assert result.name == "retention_staleness"
    assert result.status == "ok"
    assert "No retention history" in result.message


def test_check_retention_staleness_marker_file_ok(telemetry_root, default_thresholds):
    """Test retention staleness check - recent marker file."""
    # Create marker file
    marker = telemetry_root / ".last_retention_run"
    marker.touch()

    result = check_retention_staleness(telemetry_root, default_thresholds)

    assert result.name == "retention_staleness"
    assert result.status == "ok"
    assert result.value is not None
    assert result.value < 1.0  # Less than 1 hour


def test_check_retention_staleness_marker_file_warn(telemetry_root):
    """Test retention staleness check - old marker file (warning)."""
    thresholds = HealthThresholds(retention_warn_hours=24, retention_critical_hours=72)

    # Create old marker file
    marker = telemetry_root / ".last_retention_run"
    marker.touch()
    old_time = datetime.now(timezone.utc) - timedelta(hours=48)
    os.utime(marker, (old_time.timestamp(), old_time.timestamp()))

    result = check_retention_staleness(telemetry_root, thresholds)

    assert result.name == "retention_staleness"
    assert result.status == "warn"
    assert result.value > thresholds.retention_warn_hours


def test_check_retention_staleness_compressed_files_fallback(telemetry_root, default_thresholds):
    """Test retention staleness check - fallback to compressed files."""
    # Create compressed file
    gz_file = telemetry_root / "session_1.jsonl.gz"
    with gzip.open(gz_file, "wt") as f:
        f.write('{"test": "data"}\n')

    result = check_retention_staleness(telemetry_root, default_thresholds)

    assert result.name == "retention_staleness"
    assert result.status == "ok"


def test_check_compression_failures_ok(telemetry_root, default_thresholds):
    """Test compression failures check - OK status."""
    # Create some normal files
    create_log_file(telemetry_root, "session_1")
    create_log_file(telemetry_root, "session_2")

    result = check_compression_failures(telemetry_root, default_thresholds)

    assert result.name == "compression_failures"
    assert result.status == "ok"
    assert result.value == 0.0


def test_check_compression_failures_warn(telemetry_root):
    """Test compression failures check - WARNING status."""
    thresholds = HealthThresholds(compress_warn_rate=5.0, compress_critical_rate=20.0)

    # Create files + some .tmp files (indicating failures)
    create_log_file(telemetry_root, "session_1")
    create_log_file(telemetry_root, "session_2")
    (telemetry_root / "session_3.tmp").touch()  # Failed compression

    result = check_compression_failures(telemetry_root, thresholds)

    assert result.name == "compression_failures"
    # 1 failure / 3 total = 33% (should be warn or critical)
    assert result.status in ("warn", "critical")


def test_check_parse_error_rate_ok(telemetry_root, default_thresholds):
    """Test parse error rate check - OK status."""
    # Create valid JSONL
    log_file = telemetry_root / "session_1.jsonl"
    with open(log_file, "w") as f:
        for i in range(10):
            f.write(json.dumps({"ts": "2025-12-20T10:00:00Z", "kind": "test"}) + "\n")

    result = check_parse_error_rate(telemetry_root, default_thresholds, sample_size=100)

    assert result.name == "parse_error_rate"
    assert result.status == "ok"
    assert result.value == 0.0


def test_check_parse_error_rate_warn(telemetry_root):
    """Test parse error rate check - WARNING status."""
    thresholds = HealthThresholds(parse_warn_rate=5.0, parse_critical_rate=15.0)

    # Create JSONL with some invalid lines
    log_file = telemetry_root / "session_1.jsonl"
    with open(log_file, "w") as f:
        for i in range(90):
            f.write(json.dumps({"ts": "2025-12-20T10:00:00Z", "kind": "test"}) + "\n")
        for i in range(10):
            f.write("INVALID JSON LINE\n")  # 10% error rate

    result = check_parse_error_rate(telemetry_root, thresholds, sample_size=200)

    assert result.name == "parse_error_rate"
    assert result.status == "warn"
    assert result.value >= thresholds.parse_warn_rate


def test_check_parse_error_rate_compressed(telemetry_root, default_thresholds):
    """Test parse error rate check with compressed files."""
    # Create compressed JSONL
    gz_file = telemetry_root / "session_1.jsonl.gz"
    with gzip.open(gz_file, "wt") as f:
        for i in range(10):
            f.write(json.dumps({"ts": "2025-12-20T10:00:00Z", "kind": "test"}) + "\n")

    result = check_parse_error_rate(telemetry_root, default_thresholds, sample_size=100)

    assert result.name == "parse_error_rate"
    assert result.status == "ok"


def test_check_parse_error_rate_no_files(telemetry_root, default_thresholds):
    """Test parse error rate check with no log files."""
    result = check_parse_error_rate(telemetry_root, default_thresholds)

    assert result.name == "parse_error_rate"
    assert result.status == "ok"
    assert result.value == 0.0


def test_run_health_checks_all_ok(telemetry_root):
    """Test full health check run - all OK."""
    # Create small, recent, valid log
    log_file = telemetry_root / "session_1.jsonl"
    with open(log_file, "w") as f:
        f.write(json.dumps({"ts": "2025-12-20T10:00:00Z", "kind": "test"}) + "\n")

    report = run_health_checks(telemetry_root)

    assert len(report.checks) == 4
    assert report.status == "ok"
    assert report.exit_code == 0
    assert all(c.status == "ok" for c in report.checks)


def test_run_health_checks_with_warnings(telemetry_root):
    """Test full health check run - with warnings."""
    thresholds = HealthThresholds(
        disk_warn_mb=1,
        disk_critical_mb=10,
    )

    # Create ~2 MB of logs
    for i in range(20):
        create_log_file(telemetry_root, f"session_{i}", size_kb=100)

    report = run_health_checks(telemetry_root, thresholds)

    assert report.status == "warn"
    assert report.exit_code == 2
    assert any(c.status == "warn" for c in report.checks)


def test_run_health_checks_with_critical(telemetry_root):
    """Test full health check run - with critical."""
    thresholds = HealthThresholds(
        disk_warn_mb=1,
        disk_critical_mb=2,
    )

    # Create ~3 MB of logs
    for i in range(30):
        create_log_file(telemetry_root, f"session_{i}", size_kb=100)

    report = run_health_checks(telemetry_root, thresholds)

    assert report.status == "critical"
    assert report.exit_code == 3
    assert any(c.status == "critical" for c in report.checks)


def test_health_report_to_dict(telemetry_root, default_thresholds):
    """Test health report JSON serialization."""
    report = run_health_checks(telemetry_root, default_thresholds)

    data = report.to_dict()

    assert "timestamp" in data
    assert "status" in data
    assert "exit_code" in data
    assert "checks" in data
    assert isinstance(data["checks"], list)
    assert len(data["checks"]) == 4

    # Validate check structure
    for check in data["checks"]:
        assert "name" in check
        assert "status" in check
        assert "message" in check
        assert check["status"] in ("ok", "warn", "critical")


def test_health_check_golden_schema():
    """Golden test for health check JSON schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "logs"
        root.mkdir()

        # Create minimal valid log
        log_file = root / "test.jsonl"
        log_file.write_text('{"ts": "2025-12-20T10:00:00Z"}\n')

        report = run_health_checks(root)
        data = report.to_dict()

        # Golden schema assertions
        assert set(data.keys()) == {"timestamp", "status", "exit_code", "checks"}
        assert data["status"] in ("ok", "warn", "critical")
        assert data["exit_code"] in (0, 2, 3)
        assert isinstance(data["checks"], list)

        for check in data["checks"]:
            required_keys = {"name", "status", "message"}
            assert required_keys.issubset(set(check.keys()))
            assert check["status"] in ("ok", "warn", "critical")
