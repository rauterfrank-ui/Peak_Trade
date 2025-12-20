"""
Logging Integration with Trace Context
======================================
Structured logging with automatic trace context injection.

Design:
- TraceContextFilter injects run_id and trace_id into log records
- configure_logging() sets up logging with trace context support
- Follows standard Python logging patterns

Usage:
    from src.core.logging_config import configure_logging
    from src.core.trace_context import trace_context
    
    # Configure logging once at application start
    configure_logging()
    
    # All logs within context include trace IDs
    with trace_context(run_id="abc123"):
        logger.info("Starting backtest")  # Includes [abc123] [trace_id]
"""
import logging
from src.core.trace_context import get_run_id, get_trace_id


class TraceContextFilter(logging.Filter):
    """Inject trace context into log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add run_id and trace_id to log record.
        
        Args:
            record: Log record to enhance
            
        Returns:
            True (always allow record through)
        """
        record.run_id = get_run_id() or "N/A"
        record.trace_id = get_trace_id() or "N/A"
        return True


def configure_logging(level: int = logging.INFO, format_string: str = None):
    """Configure logging with trace context.
    
    Args:
        level: Logging level (default: INFO)
        format_string: Optional custom format string
        
    Example:
        >>> configure_logging()
        >>> # All subsequent logs include trace context
    """
    # Default format with trace context
    if format_string is None:
        format_string = '[%(asctime)s] [%(run_id)s] [%(trace_id)s] %(levelname)s - %(message)s'
    
    handler = logging.StreamHandler()
    handler.addFilter(TraceContextFilter())
    
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.handlers = []  # Clear existing handlers
    logging.root.addHandler(handler)
    logging.root.setLevel(level)
