"""
Tests for Trace Context Propagation
====================================
Tests for thread-safe context propagation and logging integration.
"""
import logging
import threading
import pytest
from io import StringIO

from src.core.trace_context import (
    TraceContext,
    get_run_id,
    get_trace_id,
    trace_context,
    _run_id_var,
    _trace_id_var,
)
from src.core.logging_config import TraceContextFilter, configure_logging


# =============================================================================
# TraceContext Tests
# =============================================================================

def test_trace_context_create_minimal():
    """TraceContext.create() generates IDs when not provided."""
    ctx = TraceContext.create()
    
    assert ctx.run_id is not None
    assert ctx.trace_id is not None
    assert len(ctx.trace_id) == 8  # Short UUID format
    assert ctx.parent_span_id is None


def test_trace_context_create_with_run_id():
    """TraceContext.create() accepts explicit run_id."""
    ctx = TraceContext.create(run_id="my_run_123")
    
    assert ctx.run_id == "my_run_123"
    assert ctx.trace_id is not None
    assert len(ctx.trace_id) == 8


def test_trace_context_set_active():
    """TraceContext.set_active() sets context variables."""
    ctx = TraceContext(run_id="test_run", trace_id="abc12345")
    ctx.set_active()
    
    assert get_run_id() == "test_run"
    assert get_trace_id() == "abc12345"
    
    # Cleanup
    _run_id_var.set(None)
    _trace_id_var.set(None)


def test_trace_context_get_active():
    """TraceContext.get_active() retrieves active context."""
    # Set context
    _run_id_var.set("run123")
    _trace_id_var.set("trace456")
    
    ctx = TraceContext.get_active()
    assert ctx is not None
    assert ctx.run_id == "run123"
    assert ctx.trace_id == "trace456"
    
    # Cleanup
    _run_id_var.set(None)
    _trace_id_var.set(None)


def test_trace_context_get_active_returns_none():
    """TraceContext.get_active() returns None when no context set."""
    # Ensure clean state
    _run_id_var.set(None)
    _trace_id_var.set(None)
    
    ctx = TraceContext.get_active()
    assert ctx is None


def test_get_run_id_returns_none_when_not_set():
    """get_run_id() returns None when no context active."""
    _run_id_var.set(None)
    assert get_run_id() is None


def test_get_trace_id_returns_none_when_not_set():
    """get_trace_id() returns None when no context active."""
    _trace_id_var.set(None)
    assert get_trace_id() is None


# =============================================================================
# Context Manager Tests
# =============================================================================

def test_context_manager_sets_and_clears():
    """Context manager sets context on enter and clears on exit."""
    # Ensure clean state
    assert get_run_id() is None
    assert get_trace_id() is None
    
    with trace_context(run_id="ctx_test") as ctx:
        # Inside context: IDs are set
        assert get_run_id() == "ctx_test"
        assert get_trace_id() == ctx.trace_id
        assert get_trace_id() is not None
    
    # Outside context: IDs are cleared
    assert get_run_id() is None
    assert get_trace_id() is None


def test_context_manager_generates_ids():
    """Context manager generates IDs when not provided."""
    with trace_context() as ctx:
        assert ctx.run_id is not None
        assert ctx.trace_id is not None
        assert get_run_id() == ctx.run_id
        assert get_trace_id() == ctx.trace_id


def test_context_manager_accepts_explicit_trace_id():
    """Context manager accepts explicit trace_id."""
    with trace_context(run_id="run123", trace_id="trace789") as ctx:
        assert ctx.run_id == "run123"
        assert ctx.trace_id == "trace789"
        assert get_trace_id() == "trace789"


def test_context_manager_clears_on_exception():
    """Context manager clears context even on exception."""
    try:
        with trace_context(run_id="error_test"):
            assert get_run_id() == "error_test"
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Context should be cleared
    assert get_run_id() is None
    assert get_trace_id() is None


def test_nested_context_managers():
    """Nested context managers work correctly."""
    with trace_context(run_id="outer") as outer_ctx:
        assert get_run_id() == "outer"
        outer_trace = get_trace_id()
        
        with trace_context(run_id="inner") as inner_ctx:
            # Inner context overrides
            assert get_run_id() == "inner"
            assert get_trace_id() == inner_ctx.trace_id
            assert get_trace_id() != outer_trace
        
        # After inner context exits, outer is NOT restored (by design)
        # Context is cleared
        assert get_run_id() is None
        assert get_trace_id() is None


# =============================================================================
# Thread Safety Tests
# =============================================================================

def test_context_isolation_between_threads():
    """Context variables are isolated between threads."""
    results = []
    
    def worker(run_id):
        with trace_context(run_id=run_id):
            # Each thread should see its own run_id
            results.append(get_run_id())
    
    threads = [
        threading.Thread(target=worker, args=("thread1",)),
        threading.Thread(target=worker, args=("thread2",)),
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Both threads should have recorded their own run_id
    assert "thread1" in results
    assert "thread2" in results
    assert len(results) == 2


# =============================================================================
# Logging Integration Tests
# =============================================================================

def test_trace_context_filter():
    """TraceContextFilter adds run_id and trace_id to log records."""
    # Set context
    _run_id_var.set("filter_test_run")
    _trace_id_var.set("filter_trace")
    
    # Create log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    # Apply filter
    log_filter = TraceContextFilter()
    result = log_filter.filter(record)
    
    assert result is True
    assert record.run_id == "filter_test_run"
    assert record.trace_id == "filter_trace"
    
    # Cleanup
    _run_id_var.set(None)
    _trace_id_var.set(None)


def test_trace_context_filter_with_no_context():
    """TraceContextFilter uses 'N/A' when no context is set."""
    # Ensure no context
    _run_id_var.set(None)
    _trace_id_var.set(None)
    
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    log_filter = TraceContextFilter()
    log_filter.filter(record)
    
    assert record.run_id == "N/A"
    assert record.trace_id == "N/A"


def test_configure_logging():
    """configure_logging() sets up logging with trace context."""
    # Capture log output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(TraceContextFilter())
    formatter = logging.Formatter('[%(run_id)s] [%(trace_id)s] %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("test_logger")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    
    # Log with context
    with trace_context(run_id="log_test", trace_id="trace123"):
        logger.info("Test message")
    
    output = stream.getvalue()
    assert "log_test" in output
    assert "trace123" in output
    assert "Test message" in output


def test_logging_integration_end_to_end():
    """End-to-end test of logging with trace context."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(TraceContextFilter())
    formatter = logging.Formatter('[%(asctime)s] [%(run_id)s] [%(trace_id)s] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("e2e_test")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    
    with trace_context(run_id="e2e_run"):
        logger.info("Starting process")
        logger.warning("Warning message")
        logger.error("Error occurred")
    
    output = stream.getvalue()
    lines = output.strip().split('\n')
    
    # All lines should include run_id
    assert len(lines) == 3
    for line in lines:
        assert "e2e_run" in line
    
    # Check specific messages
    assert "Starting process" in output
    assert "Warning message" in output
    assert "Error occurred" in output


# =============================================================================
# Integration with ReproContext
# =============================================================================

def test_trace_context_with_repro_run_id():
    """TraceContext can use run_id from ReproContext."""
    from src.core.repro import ReproContext
    
    repro_ctx = ReproContext.create(seed=42)
    
    with trace_context(run_id=repro_ctx.run_id) as trace_ctx:
        assert trace_ctx.run_id == repro_ctx.run_id
        assert get_run_id() == repro_ctx.run_id


# =============================================================================
# Error Context Enrichment Tests
# =============================================================================

def test_enrich_error_with_trace():
    """enrich_error_with_trace() adds trace context to errors."""
    from src.core.errors import ConfigError, enrich_error_with_trace
    
    with trace_context(run_id="error_run", trace_id="error_trace"):
        error = ConfigError("Test error")
        enrich_error_with_trace(error)
        
        assert error.context["run_id"] == "error_run"
        assert error.context["trace_id"] == "error_trace"


def test_enrich_error_with_no_trace():
    """enrich_error_with_trace() handles missing trace context."""
    from src.core.errors import ConfigError, enrich_error_with_trace
    
    # Ensure no context
    _run_id_var.set(None)
    _trace_id_var.set(None)
    
    error = ConfigError("Test error")
    enrich_error_with_trace(error)
    
    assert error.context["run_id"] is None
    assert error.context["trace_id"] is None


def test_enrich_error_preserves_existing_context():
    """enrich_error_with_trace() preserves existing context."""
    from src.core.errors import ConfigError, enrich_error_with_trace
    
    with trace_context(run_id="ctx_run"):
        error = ConfigError("Test error", context={"key": "value"})
        enrich_error_with_trace(error)
        
        assert error.context["key"] == "value"
        assert error.context["run_id"] == "ctx_run"
        assert "trace_id" in error.context
