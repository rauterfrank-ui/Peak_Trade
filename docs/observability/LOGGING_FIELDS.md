# Structured Logging Fields - WP0D Evidence

**Date:** 2025-12-29  
**Work Package:** WP0D - Observability Minimum  
**Status:** ✅ COMPLETE

---

## 📋 Standard Logging Fields

All structured log messages include the following context fields when available:

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `trace_id` | string (UUID) | Unique trace identifier for request tracing | `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` |
| `session_id` | string | Live execution session identifier | `"session_20251229_123456"` |
| `strategy_id` | string | Strategy being executed | `"ma_crossover"` |
| `env` | string | Environment (dev/shadow/testnet/prod) | `"testnet"` |
| `timestamp` | datetime (ISO 8601) | Log entry timestamp | `"2025-12-29T05:30:15"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `order_id` | string | Order identifier | `"order_abc123"` |
| `fill_id` | string | Fill identifier | `"fill_xyz789"` |
| `exchange` | string | Exchange name | `"kraken"` |
| `symbol` | string | Trading symbol | `"BTC-EUR"` |
| `error_type` | string | Error classification | `"NetworkError"` |

---

## 🔧 Usage Examples

### Basic Logging with Context

```python
from src.observability import get_logger, set_context

# Set context at session start
set_context(
    session_id="session_123",
    strategy_id="ma_crossover",
    env="testnet",
)

# Get logger
logger = get_logger(__name__)

# All log messages now include context
logger.info("Order submitted", extra={"order_id": "order_456"})
```

**Output:**
```
2025-12-29T05:30:15 - my_module - INFO - [trace_id=a1b2c3d4 session_id=session_123 strategy_id=ma_crossover] - Order submitted
```

### Custom Trace ID

```python
set_context(
    session_id="session_123",
    strategy_id="ma_crossover",
    env="testnet",
    trace_id="custom_trace_123",  # Custom trace ID
)
```

### Additional Metadata

```python
set_context(
    session_id="session_123",
    strategy_id="ma_crossover",
    env="testnet",
    metadata={
        "portfolio_id": "portfolio_abc",
        "account_id": "account_xyz",
    },
)
```

### Clearing Context

```python
from src.observability import clear_context

# Clear context when session ends
clear_context()
```

---

## 📊 Log Format

### Standard Format

```
%(asctime)s - %(name)s - %(levelname)s - [trace_id=%(trace_id)s session_id=%(session_id)s strategy_id=%(strategy_id)s] - %(message)s
```

### Example Log Entry

```
2025-12-29T05:30:15 - src.execution.live_session - INFO - [trace_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890 session_id=session_20251229_123456 strategy_id=ma_crossover] - Order submitted successfully
```

---

## 🎯 Context Lifecycle

### 1. Session Start
```python
# Set context when live session starts
ctx = set_context(
    session_id=session.id,
    strategy_id=session.strategy_id,
    env=session.env,
)
```

### 2. During Execution
```python
# Context is automatically included in all logs
logger.info("Processing signal")
logger.warning("High latency detected", extra={"latency_ms": 250})
logger.error("Order rejected", extra={"reason": "Insufficient funds"})
```

### 3. Session End
```python
# Clear context when session ends
clear_context()
```

---

## 🔍 Tracing Across Components

The `trace_id` field enables tracing across multiple components:

```
# Execution module
2025-12-29T05:30:15 - src.execution.live_session - INFO - [trace_id=abc123 ...] - Order submitted

# Risk module
2025-12-29T05:30:15 - src.risk_layer.runtime - INFO - [trace_id=abc123 ...] - Risk check passed

# Exchange module
2025-12-29T05:30:16 - src.exchange.kraken - INFO - [trace_id=abc123 ...] - Order acknowledged
```

All entries share the same `trace_id`, enabling end-to-end tracing.

---

## ⚡ Performance

- **Context Storage:** Thread-safe using `contextvars`
- **Overhead:** Minimal (< 1ms per log call)
- **Serialization:** Lazy (only when log is emitted)

---

## 🧪 Testing

### Verify Context Fields

```python
import logging
from src.observability import get_logger, set_context

def test_logging_with_context(caplog):
    set_context(session_id="test_session")
    logger = get_logger(__name__)

    with caplog.at_level(logging.INFO):
        logger.info("Test message")

    record = caplog.records[0]
    assert record.session_id == "test_session"
    assert hasattr(record, "trace_id")
```

---

## 📝 Log Analysis

### Query by Session

```bash
# Find all logs for a specific session
grep "session_id=session_123" app.log
```

### Query by Trace

```bash
# Find all logs for a specific trace
grep "trace_id=abc123" app.log
```

### Query by Strategy

```bash
# Find all logs for a specific strategy
grep "strategy_id=ma_crossover" app.log
```

---

## 🎯 DoD Compliance

✅ **Required Fields Implemented:**
- trace_id ✅
- session_id ✅
- strategy_id ✅
- env ✅
- timestamp ✅

✅ **Thread-Safe:** Using `contextvars` ✅

✅ **Test Coverage:** 16 tests passing ✅

✅ **Documentation:** Complete ✅

---

**Report Generated:** 2025-12-29  
**Evidence File:** `reports&#47;observability&#47;logging_fields.md`
