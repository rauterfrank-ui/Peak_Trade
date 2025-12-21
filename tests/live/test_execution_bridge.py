# tests/live/test_execution_bridge.py
"""
Tests for Execution Bridge (Phase 16B).

Tests loading events from JSONL and mapping to Live-Track timeline.
"""

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.live.execution_bridge import (
    get_execution_timeline,
    get_execution_summary,
    _event_to_timeline_row,
    ExecutionTimelineRow,
)


def test_event_to_timeline_row_intent():
    """_event_to_timeline_row maps intent event correctly."""
    event_dict = {
        "ts": "2025-01-01T12:00:00",
        "session_id": "test",
        "symbol": "BTC-USD",
        "mode": "paper",
        "kind": "intent",
        "payload": {
            "side": "buy",
            "quantity": 1.0,
            "current_price": 100000.0,
        },
    }

    row = _event_to_timeline_row(event_dict)

    assert row is not None
    assert row.kind == "intent"
    assert row.symbol == "BTC-USD"
    assert "BUY" in row.description
    assert "1.0" in row.description or "1.000000" in row.description
    assert "$100,000" in row.description


def test_event_to_timeline_row_order():
    """_event_to_timeline_row maps order event correctly."""
    event_dict = {
        "ts": "2025-01-01T12:00:00",
        "kind": "order",
        "symbol": "BTC-USD",
        "payload": {
            "side": "sell",
            "quantity": 0.5,
            "order_type": "limit",
        },
    }

    row = _event_to_timeline_row(event_dict)

    assert row is not None
    assert row.kind == "order"
    assert "SELL" in row.description
    assert "0.5" in row.description
    assert "limit" in row.description


def test_event_to_timeline_row_fill():
    """_event_to_timeline_row maps fill event correctly."""
    event_dict = {
        "ts": "2025-01-01T12:00:00",
        "kind": "fill",
        "symbol": "BTC-USD",
        "payload": {
            "filled_quantity": 1.0,
            "fill_price": 100050.0,
            "fill_fee": 10.0,
        },
    }

    row = _event_to_timeline_row(event_dict)

    assert row is not None
    assert row.kind == "fill"
    assert "Fill" in row.description
    assert "fee" in row.description.lower()


def test_event_to_timeline_row_gate():
    """_event_to_timeline_row maps gate event correctly."""
    event_dict = {
        "ts": "2025-01-01T12:00:00",
        "kind": "gate",
        "symbol": "BTC-USD",
        "payload": {
            "gate_name": "PriceSanity",
            "passed": True,
        },
    }

    row = _event_to_timeline_row(event_dict)

    assert row is not None
    assert row.kind == "gate"
    assert "PriceSanity" in row.description
    assert "✅" in row.description or "PASS" in row.description


def test_event_to_timeline_row_invalid():
    """_event_to_timeline_row returns None for invalid event."""
    event_dict = {
        "kind": "intent",
        # Missing ts
    }

    row = _event_to_timeline_row(event_dict)

    assert row is None


def test_get_execution_timeline_loads_events():
    """get_execution_timeline loads events from JSONL."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Create test log
        log_file = base_path / "session_123.jsonl"
        events = [
            {
                "ts": "2025-01-01T12:00:00",
                "session_id": "session_123",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "intent",
                "payload": {"side": "buy", "quantity": 1.0, "current_price": 100000.0},
            },
            {
                "ts": "2025-01-01T12:00:01",
                "session_id": "session_123",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "order",
                "payload": {"side": "buy", "quantity": 1.0, "order_type": "market"},
            },
            {
                "ts": "2025-01-01T12:00:02",
                "session_id": "session_123",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "fill",
                "payload": {
                    "filled_quantity": 1.0,
                    "fill_price": 100020.0,
                    "fill_fee": 10.0,
                },
            },
        ]

        with log_file.open("w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        # Load timeline
        timeline = get_execution_timeline("session_123", base_path=str(base_path))

        assert len(timeline) == 3
        # Newest first
        assert timeline[0].kind == "fill"
        assert timeline[1].kind == "order"
        assert timeline[2].kind == "intent"


def test_get_execution_timeline_limit():
    """get_execution_timeline respects limit."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Create test log with many events
        log_file = base_path / "session_limit.jsonl"
        with log_file.open("w") as f:
            for i in range(100):
                # Use minutes instead of seconds to avoid > 59 issue
                minute = i // 60
                second = i % 60
                event = {
                    "ts": f"2025-01-01T12:{minute:02d}:{second:02d}",
                    "session_id": "session_limit",
                    "symbol": "BTC-USD",
                    "mode": "paper",
                    "kind": "intent",
                    "payload": {},
                }
                f.write(json.dumps(event) + "\n")

        # Load with limit
        timeline = get_execution_timeline("session_limit", base_path=str(base_path), limit=10)

        assert len(timeline) == 10
        # Should be last 10 events (newest first)


def test_get_execution_timeline_empty_for_nonexistent():
    """get_execution_timeline returns empty list for nonexistent session."""
    timeline = get_execution_timeline("nonexistent", base_path="/tmp")

    assert timeline == []


def test_get_execution_summary():
    """get_execution_summary returns statistics."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Create test log
        log_file = base_path / "session_summary.jsonl"
        events = [
            {
                "ts": "2025-01-01T12:00:00",
                "session_id": "session_summary",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "intent",
                "payload": {},
            },
            {
                "ts": "2025-01-01T12:00:01",
                "session_id": "session_summary",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "order",
                "payload": {},
            },
            {
                "ts": "2025-01-01T12:00:02",
                "session_id": "session_summary",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "fill",
                "payload": {},
            },
            {
                "ts": "2025-01-01T12:00:03",
                "session_id": "session_summary",
                "symbol": "ETH-USD",
                "mode": "paper",
                "kind": "intent",
                "payload": {},
            },
        ]

        with log_file.open("w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        # Get summary
        summary = get_execution_summary("session_summary", base_path=str(base_path))

        assert summary["found"]
        assert summary["event_count"] == 4
        assert summary["kind_counts"]["intent"] == 2
        assert summary["kind_counts"]["order"] == 1
        assert summary["kind_counts"]["fill"] == 1
        assert "BTC-USD" in summary["symbols"]
        assert "ETH-USD" in summary["symbols"]


def test_get_execution_summary_not_found():
    """get_execution_summary returns not-found status."""
    summary = get_execution_summary("nonexistent", base_path="/tmp")

    assert not summary["found"]
    assert summary["event_count"] == 0
