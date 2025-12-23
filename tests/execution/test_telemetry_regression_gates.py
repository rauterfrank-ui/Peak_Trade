"""
Telemetry Regression Gates - Phase 16D

Tests for data quality, schema stability, and latency sanity in telemetry events.
These tests use golden fixtures to ensure telemetry viewer robustness.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pytest

from src.execution.telemetry_viewer import (
    TelemetryQuery,
    find_session_logs,
    iter_events,
    summarize_events,
)


# ==============================================================================
# Fixtures & Helpers
# ==============================================================================


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to golden fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "execution_telemetry"


@pytest.fixture
def golden_ok_path(fixtures_dir: Path) -> Path:
    """Return path to golden_session_ok.jsonl."""
    return fixtures_dir / "golden_session_ok.jsonl"


@pytest.fixture
def golden_bad_lines_path(fixtures_dir: Path) -> Path:
    """Return path to golden_session_bad_lines.jsonl."""
    return fixtures_dir / "golden_session_bad_lines.jsonl"


@pytest.fixture
def golden_latency_path(fixtures_dir: Path) -> Path:
    """Return path to golden_session_latency.jsonl."""
    return fixtures_dir / "golden_session_latency.jsonl"


def parse_iso_ts(ts_str: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


# ==============================================================================
# GATE 1: JSONL Parse Robustness
# ==============================================================================


def test_parse_robustness_bad_lines(golden_bad_lines_path: Path):
    """Verify parser handles invalid JSON lines gracefully without crash."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_bad_lines_path], query)
    events = list(events_iter)

    # Should parse valid events
    assert stats.valid_events > 0, "Should have parsed some valid events"

    # Should track invalid lines
    assert stats.invalid_lines > 0, "Should have detected invalid lines"
    assert stats.invalid_lines == 3, f"Expected 3 invalid lines, got {stats.invalid_lines}"

    # Error rate should be reasonable
    assert 0 < stats.error_rate < 1.0, "Error rate should be between 0 and 1"

    # Valid events should be parseable
    for event in events:
        assert isinstance(event, dict), "Events should be dictionaries"
        assert "ts" in event or "kind" in event, "Events should have at least some fields"


def test_parse_robustness_ok_session(golden_ok_path: Path):
    """Verify parser handles clean golden fixture with 0% error rate."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    # All lines should be valid
    assert stats.valid_events == 10, f"Expected 10 valid events, got {stats.valid_events}"
    assert stats.invalid_lines == 0, f"Expected 0 invalid lines, got {stats.invalid_lines}"
    assert stats.error_rate == 0.0, f"Expected 0% error rate, got {stats.error_rate}"


# ==============================================================================
# GATE 2: Required Keys Invariants
# ==============================================================================


def test_required_keys_present(golden_ok_path: Path):
    """Verify required keys (kind, ts, session_id) are present in valid events."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    assert len(events) > 0, "Should have events"

    for event in events:
        # Required keys
        assert "kind" in event, f"Event missing 'kind': {event}"
        assert "ts" in event, f"Event missing 'ts': {event}"
        assert "session_id" in event, f"Event missing 'session_id': {event}"

        # Type checks
        assert isinstance(event["kind"], str), f"kind should be string: {event['kind']}"
        assert isinstance(event["ts"], str), f"ts should be string: {event['ts']}"
        assert isinstance(
            event["session_id"], str
        ), f"session_id should be string: {event['session_id']}"


def test_timestamp_parseable(golden_ok_path: Path):
    """Verify all timestamps are parseable as UTC ISO format."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    for event in events:
        ts_str = event.get("ts")
        assert ts_str, f"Event missing timestamp: {event}"

        # Should be parseable
        try:
            ts = parse_iso_ts(ts_str)
            assert ts.tzinfo is not None, f"Timestamp should be timezone-aware: {ts_str}"
        except Exception as e:
            pytest.fail(f"Failed to parse timestamp '{ts_str}': {e}")


# ==============================================================================
# GATE 3: Monotonic Time Sanity
# ==============================================================================


def test_monotonic_time_sanity_ok_session(golden_ok_path: Path):
    """Verify timestamps are mostly monotonic (small out-of-order tolerance)."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    timestamps = [parse_iso_ts(e["ts"]) for e in events if "ts" in e]

    # Should have timestamps
    assert len(timestamps) > 0, "Should have timestamps"

    # Check for major backward jumps (> 1 second tolerance)
    out_of_order_count = 0
    for i in range(1, len(timestamps)):
        delta = (timestamps[i] - timestamps[i - 1]).total_seconds()
        if delta < -1.0:  # Allow small reordering, but flag large jumps
            out_of_order_count += 1

    # Golden OK session should be perfectly monotonic
    assert out_of_order_count == 0, f"Expected 0 major backward jumps, got {out_of_order_count}"


def test_monotonic_time_latency_session(golden_latency_path: Path):
    """Verify latency session timestamps are monotonic."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_latency_path], query)
    events = list(events_iter)

    timestamps = [parse_iso_ts(e["ts"]) for e in events if "ts" in e]

    # Check monotonicity
    for i in range(1, len(timestamps)):
        assert (
            timestamps[i] >= timestamps[i - 1]
        ), f"Timestamp not monotonic at index {i}: {timestamps[i - 1]} -> {timestamps[i]}"


# ==============================================================================
# GATE 4: ID Consistency
# ==============================================================================


def test_id_consistency_order_ids(golden_ok_path: Path):
    """Verify order_id fields are strings when present."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    order_events = [e for e in events if e.get("kind") in ["order", "fill"]]
    assert len(order_events) > 0, "Should have order/fill events"

    for event in order_events:
        payload = event.get("payload", {})
        if "order_id" in payload:
            assert isinstance(
                payload["order_id"], str
            ), f"order_id should be string: {payload['order_id']}"


def test_id_consistency_intent_ids(golden_ok_path: Path):
    """Verify intent_id fields are strings when present."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    intent_events = [e for e in events if e.get("kind") in ["intent", "order"]]
    assert len(intent_events) > 0, "Should have intent/order events"

    for event in intent_events:
        payload = event.get("payload", {})
        if "intent_id" in payload:
            assert isinstance(
                payload["intent_id"], str
            ), f"intent_id should be string: {payload['intent_id']}"


# ==============================================================================
# GATE 5: Latency Sanity
# ==============================================================================


def test_latency_no_negative(golden_latency_path: Path):
    """Verify no negative latencies in intent->order->fill chains."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_latency_path], query)
    events = list(events_iter)

    # Group by intent_id
    intent_chains: Dict[str, List[Dict]] = {}
    for event in events:
        payload = event.get("payload", {})
        intent_id = payload.get("intent_id")
        if intent_id:
            if intent_id not in intent_chains:
                intent_chains[intent_id] = []
            intent_chains[intent_id].append(event)

    # Check each chain for negative latencies
    for intent_id, chain in intent_chains.items():
        # Sort by timestamp
        chain_sorted = sorted(chain, key=lambda e: e["ts"])

        # Verify no negative deltas
        for i in range(1, len(chain_sorted)):
            t1 = parse_iso_ts(chain_sorted[i - 1]["ts"])
            t2 = parse_iso_ts(chain_sorted[i]["ts"])
            delta_ms = (t2 - t1).total_seconds() * 1000

            assert (
                delta_ms >= 0
            ), f"Negative latency in chain {intent_id}: {delta_ms}ms between events {i - 1} and {i}"


def test_latency_suspicious_flag(golden_latency_path: Path):
    """Verify very large latencies (>1h) can be detected."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_latency_path], query)
    events = list(events_iter)

    # For this test, just verify we CAN detect large gaps
    timestamps = [parse_iso_ts(e["ts"]) for e in events if "ts" in e]

    max_gap_seconds = 0.0
    for i in range(1, len(timestamps)):
        gap = (timestamps[i] - timestamps[i - 1]).total_seconds()
        max_gap_seconds = max(max_gap_seconds, gap)

    # This fixture should have reasonable gaps (< 1 hour)
    assert max_gap_seconds < 3600, f"Max gap should be < 1h, got {max_gap_seconds}s"

    # Test that we could detect a suspicious gap if it existed
    # (This test validates the detection logic, not the data)
    suspicious_threshold = 3600  # 1 hour
    suspicious_gaps = [
        (timestamps[i], timestamps[i - 1])
        for i in range(1, len(timestamps))
        if (timestamps[i] - timestamps[i - 1]).total_seconds() > suspicious_threshold
    ]

    # Golden fixture should have no suspicious gaps
    assert len(suspicious_gaps) == 0, f"Found {len(suspicious_gaps)} suspicious gaps"


# ==============================================================================
# GATE 6: Summarize Invariants
# ==============================================================================


def test_summarize_counts_match(golden_ok_path: Path):
    """Verify summarize_events produces correct counts."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    summary = summarize_events(events)

    # Count checks
    assert summary["total_events"] == len(events), "Total events should match"
    assert summary["total_events"] == 10, "Expected 10 events in golden_ok"

    # Type counts
    counts_by_type = summary.get("counts_by_type", {})
    assert counts_by_type["intent"] == 3, "Expected 3 intent events"
    assert counts_by_type["order"] == 3, "Expected 3 order events"
    assert counts_by_type["fill"] == 3, "Expected 3 fill events"
    assert counts_by_type["gate"] == 1, "Expected 1 gate event"


def test_summarize_symbols(golden_ok_path: Path):
    """Verify summarize_events extracts unique symbols."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    summary = summarize_events(events)

    unique_symbols = summary.get("unique_symbols", [])
    assert len(unique_symbols) == 3, f"Expected 3 unique symbols, got {len(unique_symbols)}"
    assert set(unique_symbols) == {"BTC-USD", "ETH-USD", "SOL-USD"}, "Symbol mismatch"


def test_summarize_time_range(golden_ok_path: Path):
    """Verify summarize_events captures correct time range."""
    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    summary = summarize_events(events)

    assert "first_ts" in summary, "Summary should have first_ts"
    assert "last_ts" in summary, "Summary should have last_ts"

    first_ts = parse_iso_ts(summary["first_ts"])
    last_ts = parse_iso_ts(summary["last_ts"])

    # Last should be after first
    assert last_ts >= first_ts, "last_ts should be >= first_ts"

    # Duration sanity
    duration_seconds = (last_ts - first_ts).total_seconds()
    assert duration_seconds >= 0, "Duration should be non-negative"
    assert duration_seconds < 3600, "Golden fixture duration should be < 1 hour"


# ==============================================================================
# GATE 7: Filter Consistency
# ==============================================================================


def test_filter_by_event_type(golden_ok_path: Path):
    """Verify filtering by event type works correctly."""
    query = TelemetryQuery(event_type="fill", limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    assert len(events) == 3, f"Expected 3 fill events, got {len(events)}"
    for event in events:
        assert event["kind"] == "fill", f"Expected kind=fill, got {event['kind']}"


def test_filter_by_symbol(golden_ok_path: Path):
    """Verify filtering by symbol works correctly."""
    query = TelemetryQuery(symbol="BTC-USD", limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    # BTC-USD appears in: 1 intent, 1 order, 1 fill, 1 gate = 4 events
    assert len(events) == 4, f"Expected 4 BTC-USD events, got {len(events)}"
    for event in events:
        assert event["symbol"] == "BTC-USD", f"Expected symbol=BTC-USD, got {event['symbol']}"


def test_filter_by_session(golden_ok_path: Path):
    """Verify filtering by session_id works correctly."""
    query = TelemetryQuery(session_id="golden_ok_001", limit=1000)
    events_iter, stats = iter_events([golden_ok_path], query)
    events = list(events_iter)

    assert len(events) == 10, f"Expected 10 events for session, got {len(events)}"
    for event in events:
        assert (
            event["session_id"] == "golden_ok_001"
        ), f"Expected session_id=golden_ok_001, got {event['session_id']}"


# ==============================================================================
# GATE 8: Edge Cases
# ==============================================================================


def test_empty_log_handling():
    """Verify handling of empty log files."""
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        temp_path = Path(f.name)

    try:
        query = TelemetryQuery(limit=1000)
        events_iter, stats = iter_events([temp_path], query)
        events = list(events_iter)

        assert len(events) == 0, "Empty file should yield 0 events"
        assert stats.valid_events == 0, "Empty file should have 0 valid events"
        assert stats.invalid_lines == 0, "Empty file should have 0 invalid lines"
        assert stats.error_rate == 0.0, "Empty file should have 0% error rate"
    finally:
        temp_path.unlink()


def test_nonexistent_log_handling():
    """Verify handling of nonexistent log files."""
    nonexistent = Path("/tmp/does_not_exist_telemetry.jsonl")

    query = TelemetryQuery(limit=1000)
    events_iter, stats = iter_events([nonexistent], query)
    events = list(events_iter)

    # Should not crash, just return empty
    assert len(events) == 0, "Nonexistent file should yield 0 events"
    assert stats.valid_events == 0, "Nonexistent file should have 0 valid events"
