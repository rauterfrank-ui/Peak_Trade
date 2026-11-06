"""
Structured Logging - Phase 0 WP0D

Provides structured logging with context fields for live execution tracing.

Standard Fields:
- trace_id: Unique trace identifier across system
- session_id: Live session identifier
- strategy_id: Strategy being executed
- env: Environment (dev/shadow/testnet/prod)
- timestamp: ISO 8601 timestamp
"""

import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar


# Context variable for thread-safe context storage
_observability_context: ContextVar[Optional["ObservabilityContext"]] = ContextVar(
    "_observability_context", default=None
)


@dataclass
class ObservabilityContext:
    """Observability context fields for structured logging."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    strategy_id: Optional[str] = None
    env: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dict for logging."""
        d = asdict(self)
        # Remove None values for cleaner logs
        return {k: v for k, v in d.items() if v is not None}


def set_context(
    session_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    env: Optional[str] = None,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ObservabilityContext:
    """
    Set observability context for current execution.

    Args:
        session_id: Live session ID
        strategy_id: Strategy ID
        env: Environment (dev/shadow/testnet/prod)
        trace_id: Optional custom trace ID (auto-generated if None)
        metadata: Additional metadata

    Returns:
        ObservabilityContext instance

    Example:
        >>> ctx = set_context(
        ...     session_id="session_123",
        ...     strategy_id="ma_crossover",
        ...     env="testnet",
        ... )
        >>> logger = get_logger(__name__)
        >>> logger.info("Order submitted")  # Includes context fields
    """
    ctx = ObservabilityContext(
        trace_id=trace_id or str(uuid.uuid4()),
        session_id=session_id,
        strategy_id=strategy_id,
        env=env,
        metadata=metadata or {},
    )
    _observability_context.set(ctx)
    return ctx


def get_context() -> Optional[ObservabilityContext]:
    """Get current observability context."""
    return _observability_context.get()


def clear_context() -> None:
    """Clear observability context."""
    _observability_context.set(None)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds observability context to all log records."""

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add context fields to log record."""
        ctx = get_context()
        if ctx:
            extra = kwargs.get("extra", {})
            extra.update(ctx.to_dict())
            kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str) -> logging.Logger:
    """
    Get structured logger with observability context.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance that includes context fields

    Example:
        >>> set_context(session_id="session_123", strategy_id="ma_crossover")
        >>> logger = get_logger(__name__)
        >>> logger.info("Order submitted", extra={"order_id": "order_456"})
        # Output includes: trace_id, session_id, strategy_id, order_id
    """
    base_logger = logging.getLogger(name)
    return StructuredLoggerAdapter(base_logger, {})


def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
) -> None:
    """
    Configure logging for Peak_Trade observability.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (uses default if None)

    Example:
        >>> configure_logging(level="DEBUG")
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message with context")
    """
    if format_string is None:
        # Default format with observability fields
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[trace_id=%(trace_id)s session_id=%(session_id)s strategy_id=%(strategy_id)s] - "
            "%(message)s"
        )

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
