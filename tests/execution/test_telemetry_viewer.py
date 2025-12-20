# tests/execution/test_telemetry_viewer.py
"""
Tests for Telemetry Viewer (Phase 16C).

Tests read-only querying, filtering, and summarization of
execution telemetry events.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.execution.telemetry_viewer import (
    TelemetryQuery,
    build_timeline,
    find_session_logs,
    iter_events,
    summarize_events,
)


def create_test_log(path: Path, events: list[dict]) -> None:
    """Helper: Create JSONL log file with events."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def test_iter_events_basic():
    """Test basic event iteration from JSONL."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        # Create test events
        events = [
            {
                "ts": "2025-01-01T12:00:00+00:00",
                "session_id": "test_session",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "intent",
                "payload": {"side": "buy", "quantity": 1.0},
            },
            {
                "ts": "2025-01-01T12:00:01+00:00",
                "session_id": "test_session",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "order",
                "payload": {"client_id": "ord_001"},
            },
            {
                "ts": "2025-01-01T12:00:02+00:00",
                "session_id": "test_session",
                "symbol": "BTC-USD",
                "mode": "paper",
                "kind": "fill",
                "payload": {"filled_quantity": 1.0, "fill_price": 100000.0},
            },
        ]
        create_test_log(log_path, events)

        # Query all events
        query = TelemetryQuery(limit=100)
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 3
        assert stats.valid_events == 3
        assert stats.invalid_lines == 0
        assert stats.error_rate == 0.0


def test_iter_events_filter_by_type():
    """Test filtering events by type."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        events = [
            {"ts": "2025-01-01T12:00:00+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "intent"},
            {"ts": "2025-01-01T12:00:01+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "order"},
            {"ts": "2025-01-01T12:00:02+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
        ]
        create_test_log(log_path, events)

        # Filter by type
        query = TelemetryQuery(event_type="fill", limit=100)
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 1
        assert result[0]["kind"] == "fill"


def test_iter_events_filter_by_symbol():
    """Test filtering events by symbol."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        events = [
            {"ts": "2025-01-01T12:00:00+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:00:01+00:00", "session_id": "test", "symbol": "ETH-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:00:02+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
        ]
        create_test_log(log_path, events)

        # Filter by symbol
        query = TelemetryQuery(symbol="BTC-USD", limit=100)
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 2
        assert all(e["symbol"] == "BTC-USD" for e in result)


def test_iter_events_filter_by_session():
    """Test filtering events by session_id."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        events = [
            {"ts": "2025-01-01T12:00:00+00:00", "session_id": "session_1", "symbol": "BTC-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:00:01+00:00", "session_id": "session_2", "symbol": "BTC-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:00:02+00:00", "session_id": "session_1", "symbol": "BTC-USD", "kind": "fill"},
        ]
        create_test_log(log_path, events)

        # Filter by session
        query = TelemetryQuery(session_id="session_1", limit=100)
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 2
        assert all(e["session_id"] == "session_1" for e in result)


def test_iter_events_timestamp_filter():
    """Test filtering events by timestamp range."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        events = [
            {"ts": "2025-01-01T11:59:00+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:00:00+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:01:00+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
            {"ts": "2025-01-01T12:02:00+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"},
        ]
        create_test_log(log_path, events)

        # Filter by time range
        query = TelemetryQuery(
            ts_from="2025-01-01T12:00:00+00:00",
            ts_to="2025-01-01T12:01:30+00:00",
            limit=100,
        )
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 2  # 12:00:00 and 12:01:00


def test_iter_events_limit():
    """Test event limit is respected."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        # Create 100 events
        events = [
            {"ts": f"2025-01-01T12:00:{i:02d}+00:00", "session_id": "test", "symbol": "BTC-USD", "kind": "fill"}
            for i in range(100)
        ]
        create_test_log(log_path, events)

        # Query with limit
        query = TelemetryQuery(limit=10)
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 10


def test_iter_events_handles_invalid_lines():
    """Test viewer handles invalid JSON lines gracefully."""
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_session.jsonl"

        # Mix valid and invalid lines
        with log_path.open("w") as f:
            f.write('{"ts": "2025-01-01T12:00:00+00:00", "kind": "fill"}\n')
            f.write('invalid json line\n')
            f.write('{"ts": "2025-01-01T12:00:01+00:00", "kind": "fill"}\n')
            f.write('{broken json\n')
            f.write('{"ts": "2025-01-01T12:00:02+00:00", "kind": "fill"}\n')

        query = TelemetryQuery(limit=100)
        event_iter, stats = iter_events([log_path], query)
        result = list(event_iter)

        assert len(result) == 3  # Only valid events
        assert stats.valid_events == 3
        assert stats.invalid_lines == 2
        assert stats.error_rate == pytest.approx(2 / 5)


def test_summarize_events():
    """Test event summarization."""
    events = [
        {"ts": "2025-01-01T12:00:00+00:00", "session_id": "s1", "symbol": "BTC-USD", "kind": "intent"},
        {"ts": "2025-01-01T12:00:01+00:00", "session_id": "s1", "symbol": "BTC-USD", "kind": "order"},
        {"ts": "2025-01-01T12:00:02+00:00", "session_id": "s1", "symbol": "BTC-USD", "kind": "fill"},
        {"ts": "2025-01-01T12:00:03+00:00", "session_id": "s2", "symbol": "ETH-USD", "kind": "fill"},
    ]

    summary = summarize_events(events)

    assert summary["total_events"] == 4
    assert summary["counts_by_type"] == {"intent": 1, "order": 1, "fill": 2}
    assert set(summary["unique_symbols"]) == {"BTC-USD", "ETH-USD"}
    assert set(summary["unique_sessions"]) == {"s1", "s2"}
    assert summary["first_ts"] == "2025-01-01T12:00:00+00:00"
    assert summary["last_ts"] == "2025-01-01T12:00:03+00:00"


def test_summarize_events_with_latency():
    """Test latency calculation in summary."""
    events = [
        {
            "ts": "2025-01-01T12:00:00.000000+00:00",
            "symbol": "BTC-USD",
            "kind": "intent",
        },
        {
            "ts": "2025-01-01T12:00:00.050000+00:00",
            "symbol": "BTC-USD",
            "kind": "order",
        },  # 50ms later
    ]

    summary = summarize_events(events)

    assert "latency_ms" in summary
    assert summary["latency_ms"]["min"] == pytest.approx(50.0, rel=1e-2)
    assert summary["latency_ms"]["median"] == pytest.approx(50.0, rel=1e-2)


def test_build_timeline():
    """Test timeline building."""
    events = [
        {
            "ts": "2025-01-01T12:00:00+00:00",
            "session_id": "test",
            "symbol": "BTC-USD",
            "mode": "paper",
            "kind": "fill",
            "payload": {"filled_quantity": 1.0, "fill_price": 100000.0, "fill_fee": 10.0},
        },
        {
            "ts": "2025-01-01T12:00:01+00:00",
            "session_id": "test",
            "symbol": "ETH-USD",
            "mode": "paper",
            "kind": "order",
            "payload": {"client_id": "ord_001", "side": "buy", "quantity": 2.0},
        },
    ]

    timeline = build_timeline(events, max_items=10)

    assert len(timeline) == 2
    assert timeline[0]["type"] == "fill"
    assert timeline[0]["symbol"] == "BTC-USD"
    assert timeline[0]["filled_quantity"] == 1.0
    assert timeline[1]["type"] == "order"
    assert timeline[1]["order_id"] == "ord_001"


def test_build_timeline_respects_max_items():
    """Test timeline max_items limit."""
    events = [
        {"ts": f"2025-01-01T12:00:{i:02d}+00:00", "symbol": "BTC-USD", "kind": "fill", "payload": {}}
        for i in range(100)
    ]

    timeline = build_timeline(events, max_items=10)

    assert len(timeline) == 10


def test_find_session_logs():
    """Test finding session log files."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Create some log files
        (base_path / "session_1.jsonl").touch()
        (base_path / "session_2.jsonl").touch()
        (base_path / "other.txt").touch()  # Should be ignored

        logs = find_session_logs(base_path)

        assert len(logs) == 2
        assert all(log.suffix == ".jsonl" for log in logs)


def test_find_session_logs_empty_directory():
    """Test behavior with empty directory."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        logs = find_session_logs(base_path)
        assert logs == []


def test_find_session_logs_nonexistent_directory():
    """Test behavior with nonexistent directory."""
    base_path = Path("/nonexistent/path/to/logs")
    logs = find_session_logs(base_path)
    assert logs == []
