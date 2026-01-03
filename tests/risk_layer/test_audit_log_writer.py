"""
Tests for AuditLogWriter
"""

import json
from pathlib import Path

import pytest

from src.risk_layer.audit_log import AuditLogWriter


def test_audit_log_writer_creates_parent_dirs(tmp_path: Path) -> None:
    """Test that AuditLogWriter creates parent directories if needed."""
    log_path = tmp_path / "nested" / "dir" / "audit.jsonl"
    writer = AuditLogWriter(str(log_path))

    assert writer.path == log_path
    assert writer.path.parent.exists()


def test_audit_log_writer_writes_single_event(tmp_path: Path) -> None:
    """Test writing a single event to the audit log."""
    log_path = tmp_path / "audit.jsonl"
    writer = AuditLogWriter(str(log_path))

    event = {"action": "test", "value": 42}
    writer.write(event)

    # Verify file exists and contains one line
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    # Verify JSON is valid
    parsed = json.loads(lines[0])
    assert parsed["action"] == "test"
    assert parsed["value"] == 42
    assert "timestamp_utc" in parsed  # Auto-added


def test_audit_log_writer_writes_multiple_events(tmp_path: Path) -> None:
    """Test writing multiple events to the audit log."""
    log_path = tmp_path / "audit.jsonl"
    writer = AuditLogWriter(str(log_path))

    events = [
        {"event": "order_1", "symbol": "BTCUSDT"},
        {"event": "order_2", "symbol": "ETHUSDT"},
        {"event": "order_3", "symbol": "SOLUSDT"},
    ]

    for event in events:
        writer.write(event)

    # Verify all events are written
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3

    # Verify each line is valid JSON
    for i, line in enumerate(lines):
        parsed = json.loads(line)
        assert parsed["event"] == f"order_{i + 1}"


def test_audit_log_writer_preserves_timestamp_if_present(tmp_path: Path) -> None:
    """Test that existing timestamp_utc is not overwritten."""
    log_path = tmp_path / "audit.jsonl"
    writer = AuditLogWriter(str(log_path))

    custom_timestamp = "2025-01-01T00:00:00Z"
    event = {"action": "test", "timestamp_utc": custom_timestamp}
    writer.write(event)

    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    parsed = json.loads(lines[0])
    assert parsed["timestamp_utc"] == custom_timestamp


def test_audit_log_writer_handles_unicode(tmp_path: Path) -> None:
    """Test that unicode characters are handled correctly."""
    log_path = tmp_path / "audit.jsonl"
    writer = AuditLogWriter(str(log_path))

    event = {"message": "Test with unicode: 🚀 € ñ"}
    writer.write(event)

    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    parsed = json.loads(lines[0])
    assert parsed["message"] == "Test with unicode: 🚀 € ñ"


def test_audit_log_writer_raises_on_invalid_path() -> None:
    """Test that creating writer with invalid path raises error."""
    # Use a path that cannot be created (e.g., /dev/null/invalid)
    # This will fail during mkdir in __init__
    with pytest.raises((OSError, NotADirectoryError)):
        AuditLogWriter("/dev/null/invalid/audit.jsonl")
