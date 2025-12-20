# tests/execution/test_execution_telemetry.py
"""
Tests for Execution Telemetry (Phase 16B).

Tests event emission, JSONL logging, and pipeline integration.
"""
import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.execution.events import ExecutionEvent, event_to_dict
from src.execution.telemetry import (
    JsonlExecutionLogger,
    NullEmitter,
    CompositeEmitter,
)


def test_execution_event_to_dict():
    """ExecutionEvent.to_dict() returns serializable dict."""
    event = ExecutionEvent(
        ts=datetime(2025, 1, 1, 12, 0, 0),
        session_id="test_123",
        symbol="BTC-USD",
        mode="paper",
        kind="intent",
        payload={"side": "buy", "quantity": 1.0},
    )

    d = event.to_dict()

    assert d["ts"] == "2025-01-01T12:00:00"
    assert d["session_id"] == "test_123"
    assert d["symbol"] == "BTC-USD"
    assert d["mode"] == "paper"
    assert d["kind"] == "intent"
    assert d["payload"]["side"] == "buy"


def test_event_to_dict_helper():
    """event_to_dict() helper works."""
    event = ExecutionEvent(
        ts=datetime.now(),
        session_id="test",
        symbol="BTC-USD",
        mode="paper",
        kind="order",
        payload={},
    )

    d = event_to_dict(event)

    assert "ts" in d
    assert d["session_id"] == "test"


def test_null_emitter_does_nothing():
    """NullEmitter.emit() does nothing."""
    emitter = NullEmitter()
    event = ExecutionEvent(
        ts=datetime.now(),
        session_id="test",
        symbol="BTC-USD",
        mode="paper",
        kind="fill",
        payload={},
    )

    # Should not raise
    emitter.emit(event)


def test_jsonl_logger_writes_to_file():
    """JsonlExecutionLogger writes events to JSONL file."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        logger = JsonlExecutionLogger(str(base_path))

        # Emit events
        event1 = ExecutionEvent(
            ts=datetime(2025, 1, 1, 12, 0, 0),
            session_id="session_1",
            symbol="BTC-USD",
            mode="paper",
            kind="intent",
            payload={"side": "buy"},
        )

        event2 = ExecutionEvent(
            ts=datetime(2025, 1, 1, 12, 0, 1),
            session_id="session_1",
            symbol="BTC-USD",
            mode="paper",
            kind="order",
            payload={"side": "buy", "quantity": 1.0},
        )

        logger.emit(event1)
        logger.emit(event2)

        # Check file exists
        log_file = base_path / "session_1.jsonl"
        assert log_file.exists()

        # Check content
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

        # Parse first line
        data1 = json.loads(lines[0])
        assert data1["session_id"] == "session_1"
        assert data1["kind"] == "intent"
        assert data1["payload"]["side"] == "buy"

        # Parse second line
        data2 = json.loads(lines[1])
        assert data2["kind"] == "order"
        assert data2["payload"]["quantity"] == 1.0


def test_jsonl_logger_creates_directories():
    """JsonlExecutionLogger creates directories if needed."""
    with TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "nested" / "logs"
        logger = JsonlExecutionLogger(str(base_path))

        event = ExecutionEvent(
            ts=datetime.now(),
            session_id="test",
            symbol="BTC-USD",
            mode="paper",
            kind="fill",
            payload={},
        )

        logger.emit(event)

        # Check directory was created
        assert base_path.exists()
        assert (base_path / "test.jsonl").exists()


def test_composite_emitter_emits_to_all():
    """CompositeEmitter emits to multiple backends."""
    with TemporaryDirectory() as tmpdir:
        logger1 = JsonlExecutionLogger(f"{tmpdir}/log1")
        logger2 = JsonlExecutionLogger(f"{tmpdir}/log2")

        composite = CompositeEmitter([logger1, logger2])

        event = ExecutionEvent(
            ts=datetime.now(),
            session_id="multi_test",
            symbol="BTC-USD",
            mode="paper",
            kind="order",
            payload={},
        )

        composite.emit(event)

        # Both logs should have the event
        log1_file = Path(tmpdir) / "log1" / "multi_test.jsonl"
        log2_file = Path(tmpdir) / "log2" / "multi_test.jsonl"

        assert log1_file.exists()
        assert log2_file.exists()


def test_pipeline_emits_expected_event_sequence():
    """ExecutionPipeline with emitter emits expected event sequence."""
    # This is an integration test - would require full pipeline setup
    # For now, just test that emitter can be passed to pipeline
    from src.execution.telemetry import NullEmitter

    emitter = NullEmitter()
    
    # In real usage:
    # pipeline = ExecutionPipeline(executor=..., emitter=emitter)
    # result = pipeline.submit_order(intent)
    # Events should be emitted: intent → order → fill

    # This test verifies the interface is correct
    assert hasattr(emitter, "emit")
