# Circuit Breaker Pattern

## Overview

The Circuit Breaker pattern prevents cascading failures by monitoring failures and automatically blocking requests when a failure threshold is exceeded. After a timeout period, it tests recovery before allowing normal operation to resume.

## States

The circuit breaker has three states:

### 🟢 CLOSED (Normal Operation)
- Requests pass through normally
- Failures are counted
- Transitions to OPEN when failure threshold is exceeded

### 🔴 OPEN (Circuit Tripped)
- All requests are immediately blocked with `CircuitBreakerError`
- System waits for timeout period before testing recovery
- Transitions to HALF_OPEN after timeout

### 🟡 HALF_OPEN (Testing Recovery)
- Limited number of test requests allowed
- Successful requests transition to CLOSED
- Failed requests transition back to OPEN

## Usage

### As a Decorator

```python
from src.infra.resilience import circuit_breaker

@circuit_breaker(
    name="exchange_api",
    failure_threshold=5,
    timeout_seconds=60
)
def call_exchange_api():
    # API call that might fail
    response = exchange.get_ticker("BTC/EUR")
    return response
```

### As a Context Manager

```python
from src.infra.resilience import get_circuit_breaker

cb = get_circuit_breaker(
    name="database",
    failure_threshold=3,
    timeout_seconds=30
)

with cb:
    # Protected database operation
    result = db.query("SELECT * FROM trades")
```

### Direct Call

```python
from src.infra.resilience import CircuitBreaker

cb = CircuitBreaker(
    name="external_service",
    failure_threshold=5,
    timeout_seconds=60
)

try:
    result = cb.call(risky_function, arg1, arg2)
except CircuitBreakerError:
    print("Circuit is open, service unavailable")
```

## Configuration

Configure circuit breakers in `config.toml`:

```toml
[resilience]
circuit_breaker_enabled = true
circuit_breaker_threshold = 5           # Failures before opening
circuit_breaker_timeout = 60            # Seconds before testing recovery
circuit_breaker_half_open_calls = 3     # Max calls in HALF_OPEN
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `name` | Unique identifier for the circuit | Required |
| `failure_threshold` | Number of failures before opening circuit | 5 |
| `timeout_seconds` | Seconds to wait before testing recovery | 60 |
| `half_open_max_calls` | Max test calls in HALF_OPEN state | 3 |

## Metrics

Circuit breakers track detailed metrics:

```python
cb = get_circuit_breaker("my_service")
metrics = cb.get_metrics()

print(f"State: {metrics.state}")
print(f"Success Count: {metrics.success_count}")
print(f"Failure Count: {metrics.failure_count}")
print(f"Total Calls: {metrics.total_calls}")
print(f"Failure Rate: {metrics.failure_count / metrics.total_calls:.2%}")
```

Available metrics:
- `state` - Current circuit state
- `failure_count` - Total failures
- `success_count` - Total successes
- `total_calls` - Total calls attempted
- `last_failure_time` - Timestamp of last failure
- `last_success_time` - Timestamp of last success
- `state_changes` - Number of state transitions

## Manual Control

### Reset Circuit

```python
cb = get_circuit_breaker("my_service")
cb.reset()  # Forces circuit to CLOSED state
```

## Best Practices

### 1. Appropriate Thresholds

Set thresholds based on service characteristics:

```python
# Fast, reliable service - lower threshold
@circuit_breaker(name="cache", failure_threshold=3, timeout_seconds=10)
def get_from_cache(key):
    return cache.get(key)

# Slow, less reliable service - higher threshold  
@circuit_breaker(name="external_api", failure_threshold=10, timeout_seconds=120)
def call_external_api():
    return api.request()
```

### 2. Shared Circuit Breakers

Use the same circuit breaker name for related operations:

```python
# Both functions share the same circuit breaker
@circuit_breaker(name="exchange_api", failure_threshold=5)
def get_ticker(symbol):
    return exchange.get_ticker(symbol)

@circuit_breaker(name="exchange_api", failure_threshold=5)
def place_order(order):
    return exchange.place_order(order)
```

### 3. Fallback Strategies

Combine with fallback mechanisms:

```python
from src.infra.resilience import circuit_breaker, with_fallback

@circuit_breaker(name="live_data", failure_threshold=5)
@with_fallback(fallback_func=get_cached_data)
def get_live_data():
    return api.fetch_live_data()
```

### 4. Monitoring

Monitor circuit breaker state changes:

```python
import logging
from src.infra.resilience import get_circuit_breaker

logger = logging.getLogger(__name__)

cb = get_circuit_breaker("critical_service")

# Log state periodically
if cb.state != CircuitState.CLOSED:
    logger.warning(f"Circuit breaker '{cb.name}' is {cb.state}")
```

## Exponential Backoff

Circuit breakers work well with exponential backoff retry logic:

```python
from src.infra.resilience import circuit_breaker, retry_with_backoff

@circuit_breaker(name="api", failure_threshold=5)
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def resilient_api_call():
    return api.call()
```

## Common Patterns

### Service Health Check Integration

```python
from src.infra.health import HealthChecker
from src.infra.resilience import get_circuit_breaker

def check_service_health():
    cb = get_circuit_breaker("external_service")
    metrics = cb.get_metrics()
    
    if cb.state == CircuitState.OPEN:
        return HealthStatus.RED, "Service circuit is open"
    elif cb.state == CircuitState.HALF_OPEN:
        return HealthStatus.YELLOW, "Service recovering"
    else:
        return HealthStatus.GREEN, "Service operational"
```

### Graceful Degradation

```python
@circuit_breaker(name="premium_feature")
def get_premium_data():
    return premium_api.fetch()

def get_data():
    try:
        return get_premium_data()
    except CircuitBreakerError:
        # Fall back to basic data
        return get_basic_data()
```

## Troubleshooting

### Circuit Stuck Open

If a circuit remains open:

1. Check the service health
2. Review failure logs
3. Consider increasing timeout
4. Manually reset if service is healthy:

```python
cb = get_circuit_breaker("stuck_circuit")
cb.reset()
```

### Too Many State Changes

Frequent OPEN/CLOSED transitions indicate:
- Threshold too low
- Intermittent service issues
- Need for retry logic

Solution:
```python
# Increase threshold and timeout
@circuit_breaker(
    name="unstable_service",
    failure_threshold=10,  # Higher threshold
    timeout_seconds=300    # Longer recovery time
)
```

### False Positives

If circuit opens on transient errors:
- Use retry logic before circuit breaker
- Filter exceptions (only count real failures)
- Increase failure threshold

## Example: Exchange API Protection

```python
from src.infra.resilience import circuit_breaker, retry_with_backoff
import ccxt

@circuit_breaker(
    name="kraken_api",
    failure_threshold=5,
    timeout_seconds=60
)
@retry_with_backoff(
    max_attempts=3,
    base_delay=1.0,
    retry_on=(ccxt.NetworkError, ccxt.ExchangeNotAvailable)
)
def fetch_kraken_ticker(symbol):
    exchange = ccxt.kraken()
    return exchange.fetch_ticker(symbol)

# Usage
try:
    ticker = fetch_kraken_ticker("BTC/EUR")
except CircuitBreakerError:
    logger.error("Kraken API circuit breaker is open")
    # Use fallback or cached data
    ticker = get_cached_ticker("BTC/EUR")
```

## See Also

- [Retry Logic](MONITORING.md#retry-logic) - Exponential backoff retry
- [Rate Limiting](MONITORING.md#rate-limiting) - API rate limiting
- [Health Checks](HEALTH_CHECKS.md) - System health monitoring
