"""
Trace Context Propagation for Observability
============================================
Thread-safe context propagation for distributed tracing.

Design:
- Context variables for thread-safe propagation
- TraceContext with run_id + trace_id for correlation
- Integration with ReproContext for deterministic run_id
- Context manager for scoped propagation

Usage:
    from src.core.trace_context import trace_context, get_run_id, get_trace_id
    
    # Automatic context propagation
    with trace_context(run_id="abc123"):
        logger.info("Processing")  # Logs include run_id and trace_id
        
    # Manual access
    run_id = get_run_id()  # Get current run_id from context
    trace_id = get_trace_id()  # Get current trace_id from context
"""
from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional
import uuid

# Context variables for thread-safe propagation
_run_id_var: ContextVar[Optional[str]] = ContextVar('run_id', default=None)
_trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


@dataclass
class TraceContext:
    """Trace context for observability."""
    run_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    
    @classmethod
    def create(cls, run_id: Optional[str] = None) -> "TraceContext":
        """Create new trace context with generated IDs."""
        # Import here to avoid circular dependency
        from src.live.run_logging import generate_run_id
        
        # Generate run_id if not provided
        if run_id is None:
            # Use a simple UUID-based run_id as fallback
            run_id = str(uuid.uuid4())
        
        return cls(
            run_id=run_id,
            trace_id=str(uuid.uuid4())[:8]
        )
    
    def set_active(self):
        """Set as active context for current thread."""
        _run_id_var.set(self.run_id)
        _trace_id_var.set(self.trace_id)
    
    @classmethod
    def get_active(cls) -> Optional["TraceContext"]:
        """Get active context from current thread."""
        run_id = _run_id_var.get()
        trace_id = _trace_id_var.get()
        if run_id and trace_id:
            return cls(run_id=run_id, trace_id=trace_id)
        return None


def get_run_id() -> Optional[str]:
    """Get current run_id from context."""
    return _run_id_var.get()


def get_trace_id() -> Optional[str]:
    """Get current trace_id from context."""
    return _trace_id_var.get()


@contextmanager
def trace_context(run_id: Optional[str] = None, trace_id: Optional[str] = None):
    """Context manager for trace propagation.
    
    Args:
        run_id: Optional run_id to use (generated if not provided)
        trace_id: Optional trace_id to use (generated if not provided)
        
    Yields:
        TraceContext instance
        
    Example:
        >>> with trace_context(run_id="my_run_123") as ctx:
        ...     print(f"Run ID: {ctx.run_id}")
        ...     print(f"Trace ID: {ctx.trace_id}")
    """
    ctx = TraceContext.create(run_id=run_id)
    if trace_id:
        ctx.trace_id = trace_id
    
    # Set context
    ctx.set_active()
    
    try:
        yield ctx
    finally:
        # Clear context
        _run_id_var.set(None)
        _trace_id_var.set(None)
