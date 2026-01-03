"""
Tests for WP0D - Structured Logging

Tests structured logging with observability context fields.
"""

import pytest
import logging

from src.observability.logging import (
    ObservabilityContext,
    set_context,
    get_context,
    clear_context,
    get_logger,
    configure_logging,
)


class TestObservabilityContext:
    """Test ObservabilityContext dataclass."""

    def test_context_default_trace_id(self):
        """Context should generate trace_id by default."""
        ctx = ObservabilityContext()
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) > 0

    def test_context_to_dict(self):
        """Context should convert to dict."""
        ctx = ObservabilityContext(
            trace_id="trace_123",
            session_id="session_456",
            strategy_id="ma_crossover",
            env="testnet",
        )
        d = ctx.to_dict()
        assert d["trace_id"] == "trace_123"
        assert d["session_id"] == "session_456"
        assert d["strategy_id"] == "ma_crossover"
        assert d["env"] == "testnet"

    def test_context_to_dict_removes_none(self):
        """Context to_dict should remove None values."""
        ctx = ObservabilityContext(
            trace_id="trace_123",
            session_id=None,  # Should be filtered out
        )
        d = ctx.to_dict()
        assert "trace_id" in d
        assert "session_id" not in d


class TestContextManagement:
    """Test context setting and retrieval."""

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_set_and_get_context(self):
        """Should be able to set and get context."""
        ctx = set_context(
            session_id="session_123",
            strategy_id="ma_crossover",
            env="testnet",
        )
        retrieved_ctx = get_context()
        assert retrieved_ctx is not None
        assert retrieved_ctx.session_id == "session_123"
        assert retrieved_ctx.strategy_id == "ma_crossover"
        assert retrieved_ctx.env == "testnet"

    def test_clear_context(self):
        """Should be able to clear context."""
        set_context(session_id="session_123")
        assert get_context() is not None
        clear_context()
        assert get_context() is None

    def test_context_with_custom_trace_id(self):
        """Should accept custom trace_id."""
        ctx = set_context(
            session_id="session_123",
            trace_id="custom_trace_id",
        )
        assert ctx.trace_id == "custom_trace_id"

    def test_context_auto_generates_trace_id(self):
        """Should auto-generate trace_id if not provided."""
        ctx = set_context(session_id="session_123")
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) > 0

    def test_context_with_metadata(self):
        """Should store metadata."""
        ctx = set_context(
            session_id="session_123",
            metadata={"order_id": "order_456"},
        )
        assert ctx.metadata["order_id"] == "order_456"


class TestStructuredLogging:
    """Test structured logging integration."""

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_get_logger_without_context(self):
        """Should get logger even without context."""
        logger = get_logger(__name__)
        assert logger is not None
        # Should not raise
        logger.info("Test message without context")

    def test_get_logger_with_context(self, caplog):
        """Logger should include context fields."""
        set_context(
            session_id="session_123",
            strategy_id="ma_crossover",
            env="testnet",
        )
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Test message with context")

        # Check that context was added to log record
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert hasattr(record, "session_id")
        assert record.session_id == "session_123"
        assert record.strategy_id == "ma_crossover"
        assert record.env == "testnet"

    def test_logger_with_extra_fields(self, caplog):
        """Logger should support extra fields alongside context."""
        set_context(session_id="session_123")
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Order submitted", extra={"order_id": "order_456"})

        record = caplog.records[0]
        assert record.session_id == "session_123"
        assert record.order_id == "order_456"


class TestConfigureLogging:
    """Test logging configuration."""

    def test_configure_logging_default(self):
        """Should configure logging with defaults."""
        configure_logging()
        # Should not raise

    def test_configure_logging_custom_level(self):
        """Should configure logging with custom level."""
        # Note: logging.basicConfig only works on first call in a Python process
        # This test just verifies the function doesn't raise an exception
        configure_logging(level="DEBUG")
        # Should not raise

    def test_configure_logging_custom_format(self):
        """Should configure logging with custom format."""
        configure_logging(format_string="%(levelname)s - %(message)s")
        # Should not raise


class TestLoggingFields:
    """Test that all required logging fields are present."""

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_all_required_fields_present(self, caplog):
        """All DoD-required fields should be present."""
        set_context(
            session_id="session_123",
            strategy_id="ma_crossover",
            env="testnet",
            trace_id="trace_456",
        )
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        record = caplog.records[0]
        # DoD required fields
        assert hasattr(record, "trace_id")
        assert hasattr(record, "session_id")
        assert hasattr(record, "strategy_id")
        assert hasattr(record, "env")

    def test_multiple_loggers_share_context(self, caplog):
        """Multiple loggers should share same context."""
        set_context(session_id="session_123")

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        with caplog.at_level(logging.INFO):
            logger1.info("Message from logger1")
            logger2.info("Message from logger2")

        # Both should have same context
        assert caplog.records[0].session_id == "session_123"
        assert caplog.records[1].session_id == "session_123"
