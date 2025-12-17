# Monitoring & Logging

## Overview

Peak Trade's monitoring system provides structured logging, performance metrics, and alerting for comprehensive system observability.

## Components

1. **Structured Logger** - JSON-based logging for better log analysis
2. **Metrics Collector** - Performance metrics tracking
3. **Alert Manager** - System-wide alert management

## Structured Logging

### Configuration

Configure logging in `config.toml`:

```toml
[monitoring]
log_level = "INFO"                # DEBUG, INFO, WARNING, ERROR, CRITICAL
structured_logging = true          # Use JSON structured logging
log_file = "logs/peak_trade.log"  # Log file path
```

### Usage

```python
from src.infra.monitoring import get_structured_logger

logger = get_structured_logger(__name__)

# Simple log
logger.info("Order executed")

# Structured log with extra fields
logger.info(
    "Order executed",
    extra={
        "order_id": "12345",
        "symbol": "BTC/EUR",
        "quantity": 0.1,
        "price": 45000.0,
    }
)
```

### JSON Output

Structured logs are output as JSON for easy parsing:

```json
{
  "timestamp": "2025-12-17T16:20:39.123456Z",
  "level": "INFO",
  "logger": "src.backtest.engine",
  "message": "Order executed",
  "module": "engine",
  "function": "execute_order",
  "line": 123,
  "extra": {
    "order_id": "12345",
    "symbol": "BTC/EUR",
    "quantity": 0.1,
    "price": 45000.0
  }
}
```

### Configure Logging Programmatically

```python
from src.infra.monitoring import configure_logging

configure_logging(
    level="DEBUG",
    structured=True,
    output_file="logs/my_app.log"
)
```

## Performance Metrics

### Using the Decorator

```python
from src.infra.monitoring import track_performance

@track_performance("database_query")
def query_database():
    # Your database query
    pass

@track_performance("backtest_execution")
def run_backtest():
    # Your backtest logic
    pass
```

### Direct Usage

```python
from src.infra.monitoring import MetricsCollector

metrics = MetricsCollector(name="my_component")

# Record latency
import time
start = time.time()
# ... operation ...
elapsed = time.time() - start
metrics.record_latency("operation_name", elapsed)

# Increment counter
metrics.increment_counter("requests_total")
metrics.increment_counter("errors", value=1)

# Set gauge
metrics.set_gauge("active_connections", 42)
```

### Retrieve Metrics

```python
from src.infra.monitoring import get_global_metrics

metrics = get_global_metrics()

# Get latency stats
stats = metrics.get_latency_stats("api_call")
if stats:
    print(f"Mean: {stats.mean * 1000:.2f}ms")
    print(f"Min: {stats.min * 1000:.2f}ms")
    print(f"Max: {stats.max * 1000:.2f}ms")

# Get counter value
count = metrics.get_counter("requests_total")
print(f"Total requests: {count}")

# Get all metrics
all_metrics = metrics.get_all_metrics()
print(json.dumps(all_metrics, indent=2))
```

## Alert System

### Alert Severity Levels

| Level | Usage |
|-------|-------|
| INFO | Informational alerts |
| WARNING | Potential issues that need attention |
| ERROR | Error conditions |
| CRITICAL | Critical failures requiring immediate action |

### Raising Alerts

```python
from src.infra.monitoring import get_global_alert_manager, AlertSeverity

alerts = get_global_alert_manager()

# Raise an alert
alerts.raise_alert(
    name="high_error_rate",
    severity=AlertSeverity.WARNING,
    message="Error rate above 5% threshold"
)

# Raise critical alert
alerts.raise_alert(
    name="system_failure",
    severity=AlertSeverity.CRITICAL,
    message="Critical system component failed"
)
```

### Resolving Alerts

```python
# Resolve an alert
alerts.resolve_alert("high_error_rate")

# Check if resolved
active = alerts.get_active_alerts()
print(f"Active alerts: {len(active)}")
```

### Querying Alerts

```python
# Get all active alerts
active_alerts = alerts.get_active_alerts()
for alert in active_alerts:
    print(f"[{alert.severity}] {alert.name}: {alert.message}")

# Get alert history
history = alerts.get_alert_history(limit=10)

# Get critical alerts only
critical = alerts.get_alert_history(severity=AlertSeverity.CRITICAL)

# Get summary
summary = alerts.get_summary()
print(f"Active: {summary['total_active']}")
print(f"By severity: {summary['by_severity']}")
```

## Rate Limiting

### Token Bucket Algorithm

Peak Trade uses the token bucket algorithm for rate limiting:

```python
from src.infra.resilience import rate_limit

@rate_limit(name="exchange_api", requests_per_second=10)
def call_exchange():
    # API call here
    pass
```

### Direct Usage

```python
from src.infra.resilience import RateLimiter

limiter = RateLimiter(
    name="my_api",
    requests_per_second=10.0,
    burst_size=20  # Allow bursts up to 20 requests
)

# As context manager
with limiter:
    # Rate-limited operation
    result = api.call()

# Try to acquire (non-blocking)
if limiter.try_acquire():
    # Token available, proceed
    result = api.call()
else:
    # No tokens, skip or wait
    print("Rate limit reached")
```

### Configuration

```toml
[resilience.rate_limits]
exchange_api = 10          # 10 requests per second
data_api = 50              # 50 requests per second
default = 10               # Default for unspecified APIs
```

### Metrics

```python
limiter = get_rate_limiter("my_api")
metrics = limiter.get_metrics()

print(f"Total requests: {metrics.total_requests}")
print(f"Throttled: {metrics.total_throttled}")
print(f"Throttle rate: {metrics.throttle_rate:.2%}")
print(f"Total wait time: {metrics.total_wait_time_seconds:.2f}s")
```

## Retry Logic

### Exponential Backoff

```python
from src.infra.resilience import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,      # Start with 1 second
    max_delay=60.0,      # Cap at 60 seconds
    exponential_base=2.0 # Double each time (1s, 2s, 4s, ...)
)
def unstable_operation():
    # Operation that might fail transiently
    pass
```

### Retry Specific Exceptions

```python
import ccxt

@retry_with_backoff(
    max_attempts=3,
    retry_on=(ccxt.NetworkError, ccxt.ExchangeNotAvailable)
)
def fetch_ticker():
    exchange = ccxt.kraken()
    return exchange.fetch_ticker("BTC/EUR")
```

### Class-Based Retry

```python
from src.infra.resilience.retry import RetryWithBackoff

retry = RetryWithBackoff(max_attempts=3, base_delay=1.0)

for attempt in retry:
    with attempt:
        # Try operation
        result = risky_operation()
```

## Complete Example

```python
from src.infra.monitoring import (
    get_structured_logger,
    track_performance,
    get_global_alert_manager,
    AlertSeverity,
)
from src.infra.resilience import circuit_breaker, retry_with_backoff, rate_limit

logger = get_structured_logger(__name__)
alerts = get_global_alert_manager()

@track_performance("exchange_api_call")
@circuit_breaker(name="exchange_api", failure_threshold=5)
@retry_with_backoff(max_attempts=3, base_delay=1.0)
@rate_limit(name="exchange_api", requests_per_second=10)
def fetch_market_data(symbol):
    """Fetch market data with full resilience stack."""
    logger.info("Fetching market data", extra={"symbol": symbol})
    
    try:
        # API call
        data = exchange.fetch_ticker(symbol)
        logger.info("Market data fetched", extra={"symbol": symbol})
        return data
        
    except Exception as e:
        logger.error(
            f"Failed to fetch market data: {e}",
            extra={"symbol": symbol},
            exc_info=True
        )
        
        # Raise alert for repeated failures
        alerts.raise_alert(
            name=f"market_data_failure_{symbol}",
            severity=AlertSeverity.WARNING,
            message=f"Failed to fetch market data for {symbol}"
        )
        raise
```

## Best Practices

1. **Use Structured Logging**
   - Always use JSON logging in production
   - Include context in `extra` fields
   - Use appropriate log levels

2. **Track Important Metrics**
   - Latency of critical operations
   - Error rates
   - Resource usage (connections, memory)

3. **Set Up Alerts**
   - Configure alerts for critical conditions
   - Use appropriate severity levels
   - Resolve alerts promptly

4. **Combine Resilience Patterns**
   - Use circuit breakers for external services
   - Add retry logic for transient failures
   - Apply rate limiting to respect API limits

5. **Monitor System Health**
   - Run health checks regularly
   - Track metrics over time
   - Set up dashboards

## See Also

- [Health Checks](HEALTH_CHECKS.md) - System health monitoring
- [Circuit Breaker](CIRCUIT_BREAKER.md) - Failure handling patterns
- [Backup & Recovery](BACKUP_RECOVERY.md) - Data backup and recovery
