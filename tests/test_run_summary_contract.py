"""
Tests for RunSummary Contract
==============================

Fast, deterministic tests for the run summary contract.
No network access, <0.5s total.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.experiments.tracking.run_summary import RunSummary


@pytest.fixture
def valid_summary_data():
    """Valid run summary data."""
    return {
        "run_id": "test-run-123",
        "started_at_utc": "2025-01-15T10:00:00+00:00",
        "finished_at_utc": "2025-01-15T10:05:00+00:00",
        "status": "FINISHED",
        "tags": {"experiment": "test", "version": "v1"},
        "params": {
            "fast_period": 10,
            "slow_period": 20,
            "threshold": 0.5,
            "enabled": True,
        },
        "metrics": {
            "sharpe": 1.5,
            "total_return": 0.25,
            "max_drawdown": -0.12,
        },
        "artifacts": ["results/equity_curve.png", "results/trades.csv"],
        "git_sha": "abc123def456",
        "worktree": "clever-varahamihira",
        "hostname": "test-machine",
        "tracking_backend": "null",
    }


@pytest.fixture
def valid_summary(valid_summary_data):
    """Valid RunSummary instance."""
    return RunSummary(**valid_summary_data)


def test_validate_contract_happy_path(valid_summary):
    """Valid summary passes contract validation."""
    errors = valid_summary.validate_contract(strict=True)
    assert errors == [], f"Expected no errors, got: {errors}"
    assert valid_summary.is_valid(strict=True)


def test_validate_contract_missing_run_id():
    """Missing run_id fails validation."""
    summary = RunSummary(
        run_id="",  # Empty
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
    )

    errors = summary.validate_contract()
    assert any("run_id" in e for e in errors)
    assert not summary.is_valid()


def test_validate_contract_invalid_status():
    """Invalid status fails validation."""
    summary = RunSummary(
        run_id="test-123",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="INVALID_STATUS",
    )

    errors = summary.validate_contract()
    assert any("status" in e for e in errors)


def test_validate_contract_invalid_timestamp():
    """Invalid timestamp fails validation."""
    summary = RunSummary(
        run_id="test-123",
        started_at_utc="not-a-timestamp",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
    )

    errors = summary.validate_contract()
    assert any("started_at_utc" in e for e in errors)


def test_validate_contract_invalid_backend():
    """Invalid tracking backend fails validation."""
    summary = RunSummary(
        run_id="test-123",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
        tracking_backend="invalid",
    )

    errors = summary.validate_contract()
    assert any("tracking_backend" in e for e in errors)


def test_validate_contract_strict_mode(valid_summary):
    """Strict mode enforces type constraints."""
    # Modify metrics to have invalid type
    valid_summary.metrics = {"invalid": "not-a-number"}

    errors = valid_summary.validate_contract(strict=True)
    assert any("metrics" in e for e in errors)


def test_roundtrip_json(valid_summary, tmp_path):
    """JSON serialization roundtrip preserves data."""
    # Write to file
    json_path = tmp_path / "test_summary.json"
    valid_summary.write_json(json_path)

    # Verify file exists
    assert json_path.exists()

    # Read back
    loaded_summary = RunSummary.read_json(json_path)

    # Verify all fields match
    assert loaded_summary.run_id == valid_summary.run_id
    assert loaded_summary.started_at_utc == valid_summary.started_at_utc
    assert loaded_summary.finished_at_utc == valid_summary.finished_at_utc
    assert loaded_summary.status == valid_summary.status
    assert loaded_summary.tags == valid_summary.tags
    assert loaded_summary.params == valid_summary.params
    assert loaded_summary.metrics == valid_summary.metrics
    assert loaded_summary.artifacts == valid_summary.artifacts
    assert loaded_summary.git_sha == valid_summary.git_sha
    assert loaded_summary.worktree == valid_summary.worktree
    assert loaded_summary.hostname == valid_summary.hostname
    assert loaded_summary.tracking_backend == valid_summary.tracking_backend


def test_to_json_dict(valid_summary):
    """to_json_dict returns valid dictionary."""
    data = valid_summary.to_json_dict()

    assert isinstance(data, dict)
    assert data["run_id"] == valid_summary.run_id
    assert data["status"] == valid_summary.status
    assert data["metrics"] == valid_summary.metrics


def test_from_json_dict(valid_summary_data):
    """from_json_dict creates valid instance."""
    summary = RunSummary.from_json_dict(valid_summary_data)

    assert summary.run_id == valid_summary_data["run_id"]
    assert summary.status == valid_summary_data["status"]
    assert summary.metrics == valid_summary_data["metrics"]


def test_from_json_dict_missing_required_field():
    """from_json_dict fails with missing required field."""
    data = {
        "run_id": "test-123",
        # Missing other required fields
    }

    with pytest.raises(ValueError, match="Missing required fields"):
        RunSummary.from_json_dict(data)


def test_write_json_creates_parent_dirs(tmp_path):
    """write_json creates parent directories if needed."""
    nested_path = tmp_path / "level1" / "level2" / "summary.json"

    summary = RunSummary(
        run_id="test-123",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
    )

    # Should not raise
    summary.write_json(nested_path)

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_read_json_file_not_found():
    """read_json raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        RunSummary.read_json("/nonexistent/path.json")


def test_json_format_is_human_readable(valid_summary, tmp_path):
    """JSON output is formatted for human readability."""
    json_path = tmp_path / "summary.json"
    valid_summary.write_json(json_path)

    # Read raw JSON
    with open(json_path) as f:
        content = f.read()

    # Should be indented (not minified)
    assert "\n" in content
    assert "  " in content  # Indentation

    # Should be valid JSON
    data = json.loads(content)
    assert data["run_id"] == valid_summary.run_id


def test_optional_fields_can_be_none():
    """Optional fields can be None."""
    summary = RunSummary(
        run_id="test-123",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
        git_sha=None,
        worktree=None,
        hostname=None,
    )

    errors = summary.validate_contract()
    assert errors == []


def test_empty_collections_are_valid():
    """Empty tags/params/metrics/artifacts are valid."""
    summary = RunSummary(
        run_id="test-123",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
        tags={},
        params={},
        metrics={},
        artifacts=[],
    )

    errors = summary.validate_contract(strict=True)
    assert errors == []


def test_all_valid_statuses():
    """All documented status values are accepted."""
    valid_statuses = ["FINISHED", "FAILED", "RUNNING", "KILLED"]

    for status in valid_statuses:
        summary = RunSummary(
            run_id="test-123",
            started_at_utc="2025-01-15T10:00:00+00:00",
            finished_at_utc="2025-01-15T10:05:00+00:00",
            status=status,
        )

        errors = summary.validate_contract()
        assert errors == [], f"Status '{status}' should be valid"


def test_all_valid_backends():
    """All documented backend values are accepted."""
    valid_backends = ["null", "mlflow"]

    for backend in valid_backends:
        summary = RunSummary(
            run_id="test-123",
            started_at_utc="2025-01-15T10:00:00+00:00",
            finished_at_utc="2025-01-15T10:05:00+00:00",
            status="FINISHED",
            tracking_backend=backend,
        )

        errors = summary.validate_contract()
        assert errors == [], f"Backend '{backend}' should be valid"
