# Trace Context Propagation Guide

> **Status:** Implemented  
> **Version:** 1.0  
> **Related:** `OBSERVABILITY_AND_MONITORING_PLAN.md`

---

## Overview

Trace context propagation provides request correlation across Peak_Trade components. Every backtest run, live session, and operation can be tracked using unique identifiers (`run_id` and `trace_id`) that automatically flow through logs, errors, and metrics.

**Benefits:**
- ✅ Correlate logs across distributed components
- ✅ Track request flows through the system
- ✅ Debug issues with unique run identifiers
- ✅ Link errors to specific executions
- ✅ Thread-safe context propagation

---

## Core Concepts

### TraceContext

A `TraceContext` carries correlation IDs:

```python
@dataclass
class TraceContext:
    run_id: str          # Unique run identifier (e.g., "backtest_abc123")
    trace_id: str        # Short trace ID for request tracking (8 chars)
    parent_span_id: Optional[str]  # For nested operations (future use)
```

### Context Variables

Thread-safe context storage using Python's `contextvars`:

```python
_run_id_var: ContextVar[Optional[str]] = ContextVar('run_id', default=None)
_trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
```

---

## Usage Patterns

### 1. Automatic Propagation (BacktestEngine)

The `BacktestEngine` automatically sets trace context:

```python
from src.backtest.engine import BacktestEngine

# Create engine
engine = BacktestEngine()

# Run backtest - trace context is automatically set
result = engine.run_realistic(
    df=data,
    strategy_signal_fn=my_strategy,
    strategy_params={'fast': 10, 'slow': 30},
)

# All logs during execution will include run_id and trace_id
```

### 2. Manual Context Setting

For custom operations:

```python
from src.core.trace_context import trace_context

# Use context manager for scoped propagation
with trace_context(run_id="my_operation_123"):
    logger.info("Starting operation")  # Includes [my_operation_123] [trace_id]
    
    # Call functions - context propagates automatically
    process_data()
    
    # Error enrichment is automatic
    raise ConfigError("Something went wrong")  # Includes run_id in context
```

### 3. Accessing Current Context

```python
from src.core.trace_context import get_run_id, get_trace_id

# Get current IDs
run_id = get_run_id()      # Returns "backtest_abc123" or None
trace_id = get_trace_id()  # Returns "a1b2c3d4" or None

# Use in custom logic
if run_id:
    logger.info(f"Processing {run_id}")
```

### 4. Integration with ReproContext

Trace context works seamlessly with reproducibility tracking:

```python
from src.core.repro import ReproContext
from src.core.trace_context import trace_context

# Create reproducible context
repro_ctx = ReproContext.create(seed=42)

# Use repro run_id for trace context
with trace_context(run_id=repro_ctx.run_id):
    # Both reproducibility and traceability
    result = run_experiment()
```

---

## Logging Integration

### Setup

Configure logging to include trace context:

```python
from src.core.logging_config import configure_logging

# One-time setup at application start
configure_logging()

# All logs now include trace context
logger.info("Processing data")
# Output: [2024-01-01 10:00:00] [backtest_abc123] [a1b2c3d4] INFO - Processing data
```

### Custom Format

```python
from src.core.logging_config import configure_logging

# Custom format string
configure_logging(
    level=logging.DEBUG,
    format_string='[%(run_id)s] %(levelname)s - %(message)s'
)
```

### Filter-Only Usage

If you have custom logging setup:

```python
from src.core.logging_config import TraceContextFilter
import logging

# Add filter to existing handler
handler = logging.StreamHandler()
handler.addFilter(TraceContextFilter())

# Now log records have .run_id and .trace_id attributes
```

---

## Error Context Enrichment

### Automatic Enrichment

Errors can be enriched with trace context:

```python
from src.core.errors import ConfigError, enrich_error_with_trace

try:
    # Some operation
    process_config(config)
except ConfigError as e:
    # Enrich error with trace context
    enrich_error_with_trace(e)
    
    # Error context now includes run_id and trace_id
    logger.error(f"Config error: {e.context}")
    raise
```

### In Exception Handlers

```python
from src.core.trace_context import trace_context
from src.core.errors import enrich_error_with_trace

with trace_context(run_id="operation_123"):
    try:
        risky_operation()
    except Exception as e:
        if isinstance(e, PeakTradeError):
            enrich_error_with_trace(e)
        logger.exception("Operation failed")
        # Log includes run_id and trace_id
```

---

## Thread Safety

Context variables are thread-safe by design:

```python
import threading
from src.core.trace_context import trace_context

def worker(worker_id):
    with trace_context(run_id=f"worker_{worker_id}"):
        # Each thread has its own isolated context
        logger.info("Processing")  # Shows worker_1 or worker_2

# Concurrent execution
t1 = threading.Thread(target=worker, args=("1",))
t2 = threading.Thread(target=worker, args=("2",))

t1.start()
t2.start()
```

---

## Best Practices

### 1. Use Context Managers

Prefer `with trace_context()` for automatic cleanup:

```python
# ✅ Good - automatic cleanup
with trace_context(run_id="my_run"):
    do_work()

# ❌ Avoid - manual cleanup needed
ctx = TraceContext.create(run_id="my_run")
ctx.set_active()
do_work()
# Context persists after function!
```

### 2. Generate Unique run_ids

Use descriptive, unique identifiers:

```python
from datetime import datetime
import uuid

# ✅ Good - descriptive and unique
run_id = f"backtest_{symbol}_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"

# ❌ Avoid - not unique
run_id = "backtest_run"
```

### 3. Log at Context Boundaries

Log when context changes:

```python
with trace_context(run_id=run_id) as ctx:
    logger.info(f"Starting operation with run_id={ctx.run_id}, trace_id={ctx.trace_id}")
    # ... operation ...
    logger.info(f"Completed operation")
```

### 4. Check for Context Availability

Context may not always be set:

```python
from src.core.trace_context import get_run_id

run_id = get_run_id()
if run_id:
    logger.info(f"Processing run {run_id}")
else:
    logger.warning("No trace context available")
```

---

## Querying Logs by run_id

### Find all logs for a specific run:

```bash
# Grep logs
grep "backtest_abc123" /path/to/logs/*.log

# With trace_id
grep "backtest_abc123.*a1b2c3d4" /path/to/logs/*.log
```

### Structured log analysis:

```python
import re

def extract_run_logs(log_file, run_id):
    """Extract all log lines for a specific run_id."""
    pattern = re.compile(rf'\[{re.escape(run_id)}\]')
    
    with open(log_file) as f:
        return [line for line in f if pattern.search(line)]

# Usage
logs = extract_run_logs("app.log", "backtest_abc123")
for log in logs:
    print(log)
```

---

## Troubleshooting

### Context Not Available

**Problem:** `get_run_id()` returns `None`

**Solutions:**
1. Ensure trace context is set:
   ```python
   with trace_context(run_id="my_run"):
       # Now available
   ```

2. Check if context was cleared:
   ```python
   # Context is cleared after 'with' block exits
   with trace_context(run_id="my_run"):
       assert get_run_id() is not None  # ✅ Works
   
   assert get_run_id() is None  # ✅ Expected - context cleared
   ```

### Logs Missing trace_id

**Problem:** Logs don't include `run_id` or `trace_id`

**Solutions:**
1. Configure logging with TraceContextFilter:
   ```python
   from src.core.logging_config import configure_logging
   configure_logging()
   ```

2. Check logger configuration:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   
   # Verify handlers have the filter
   for handler in logger.handlers:
       print(handler.filters)
   ```

### Thread Context Confusion

**Problem:** Wrong run_id in threaded code

**Solution:** Each thread must set its own context:

```python
def worker(run_id):
    # Set context in EACH thread
    with trace_context(run_id=run_id):
        # Work here
        pass

# Don't set context in main thread and expect it in workers!
```

---

## Testing

### Unit Tests

Test trace context in isolation:

```python
from src.core.trace_context import trace_context, get_run_id

def test_context_propagation():
    """Verify context propagates correctly."""
    with trace_context(run_id="test_123"):
        assert get_run_id() == "test_123"
    
    # Context cleared after exit
    assert get_run_id() is None
```

### Integration Tests

Test with actual components:

```python
from src.backtest.engine import BacktestEngine
from src.core.trace_context import get_run_id

def test_backtest_with_trace():
    """Verify backtest sets trace context."""
    engine = BacktestEngine()
    
    # Context is set during run
    result = engine.run_realistic(df, strategy, params)
    
    # Verify result has metadata
    assert "run_id" in result.metadata
```

---

## Future Enhancements

### 1. Prometheus Metrics Labeling

Future implementation will add run_id to metrics:

```python
from src.monitoring.prometheus_exporter import prometheus_exporter
from src.core.trace_context import get_run_id

def record_metric(operation, duration):
    prometheus_exporter.request_duration.labels(
        endpoint=operation,
        run_id=get_run_id() or "unknown"
    ).observe(duration)
```

### 2. Distributed Tracing (OpenTelemetry)

Integration with OpenTelemetry for full distributed tracing:

```python
from opentelemetry import trace
from src.core.trace_context import get_trace_id

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("operation") as span:
    span.set_attribute("peak_trade.run_id", get_run_id())
    span.set_attribute("peak_trade.trace_id", get_trace_id())
    # Operation
```

### 3. span_id for Nested Operations

Support for hierarchical tracing:

```python
with trace_context(run_id="parent") as parent_ctx:
    with trace_context(run_id="child", parent_span_id=parent_ctx.trace_id):
        # Nested operation
        pass
```

---

## References

### Related Modules

- `src/core/trace_context.py` - Core trace context implementation
- `src/core/logging_config.py` - Logging integration
- `src/core/errors.py` - Error enrichment
- `src/core/repro.py` - Reproducibility context
- `src/backtest/engine.py` - BacktestEngine integration

### Related Documentation

- `docs/OBSERVABILITY_AND_MONITORING_PLAN.md` - Overall monitoring strategy
- `docs/PHASE_32_SHADOW_PAPER_LOGGING_AND_REPORTING.md` - Live run logging
- `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md` - System architecture

### Tests

- `tests/test_trace_context.py` - Unit tests (21 tests)
- `tests/test_trace_context_integration.py` - Integration tests (4 tests)

---

## Summary

Trace context propagation enables request correlation across Peak_Trade:

✅ **Automatic** - BacktestEngine sets context automatically  
✅ **Thread-safe** - Works correctly in concurrent code  
✅ **Logging** - Automatic injection into log messages  
✅ **Errors** - Enrichment with trace context  
✅ **Flexible** - Manual control when needed  

**Key Takeaway:** Set trace context once, get correlation everywhere.
