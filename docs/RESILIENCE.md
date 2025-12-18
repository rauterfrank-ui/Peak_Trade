# Peak_Trade Resilience & Stability Module

> **Status:** ✅ Implemented (December 2024)  
> **Version:** 1.0.0  
> **Related Issue:** #97

## Overview

The Resilience & Stability Module provides robust patterns for handling external dependencies and preventing cascading failures in Peak Trade. It implements three core patterns:

1. **Circuit Breaker** - Prevents cascading failures by temporarily blocking calls to failing services
2. **Retry with Backoff** - Automatically retries transient failures with exponential delays
3. **Health Check System** - Monitors system component health and availability

## Table of Contents

- [Quick Start](#quick-start)
- [Circuit Breaker](#circuit-breaker)
- [Retry with Backoff](#retry-with-backoff)
- [Health Check System](#health-check-system)
- [ResilientExchangeClient](#resilientexchangeclient)
- [Health Dashboard](#health-dashboard)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Installation

The resilience module is part of the core Peak_Trade package:

```python
from src.core.resilience import circuit_breaker, retry_with_backoff, health_check
```

### Basic Usage

```python
from src.core.resilience import circuit_breaker, retry_with_backoff

# Protect a function with circuit breaker and retry logic
@circuit_breaker(failure_threshold=3, recovery_timeout=60)
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def call_external_api(endpoint):
    """Make API call with automatic resilience."""
    # Your API call here
    return requests.get(endpoint).json()

# Use it normally
data = call_external_api("https://api.example.com/data")
```

## Circuit Breaker

### Concept

The circuit breaker pattern prevents cascading failures by monitoring errors and temporarily stopping calls to failing services.

**States:**
- **CLOSED**: Normal operation, all calls pass through
- **OPEN**: Circuit is open, calls fail immediately (fail fast)
- **HALF_OPEN**: Testing recovery, one call allowed through

### Usage

#### Decorator Pattern

```python
from src.core.resilience import circuit_breaker

@circuit_breaker(
    failure_threshold=5,      # Open after 5 consecutive failures
    recovery_timeout=60.0,    # Try recovery after 60 seconds
    expected_exception=Exception,  # Exception type to catch
    name="my_circuit"         # Optional name for logging
)
def risky_operation():
    # Your code here
    pass
```

#### Class Pattern

```python
from src.core.resilience import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    name="api_breaker"
)

@breaker.call
def call_api():
    # Your API call
    pass

# Check circuit state
if breaker.state == CircuitState.CLOSED:
    call_api()

# Manually reset if needed
breaker.reset()

# Get statistics
print(f"Failures: {breaker.stats.failure_count}")
print(f"Successes: {breaker.stats.success_count}")
```

### Configuration Guidelines

| Use Case | failure_threshold | recovery_timeout |
|----------|------------------|------------------|
| Critical API | 3-5 | 30-60s |
| Internal Service | 5-10 | 15-30s |
| External API | 3-5 | 60-120s |
| Database | 5-8 | 30-60s |

## Retry with Backoff

### Concept

Automatically retries failed operations with increasing delays between attempts, allowing transient issues to resolve.

### Usage

```python
from src.core.resilience import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,          # Maximum retry attempts
    base_delay=1.0,          # Initial delay in seconds
    max_delay=60.0,          # Maximum delay cap
    exponential=True,        # Use exponential backoff
    expected_exception=Exception  # Exception type to retry
)
def unstable_operation():
    # Your code here
    pass
```

### Backoff Strategies

#### Exponential Backoff (Default)

Delays grow exponentially: 1s, 2s, 4s, 8s, ...

```python
@retry_with_backoff(max_attempts=5, base_delay=1.0, exponential=True)
def api_call():
    pass
```

**Delay Sequence:** 1.0s → 2.0s → 4.0s → 8.0s

#### Constant Backoff

Fixed delay between retries:

```python
@retry_with_backoff(max_attempts=3, base_delay=2.0, exponential=False)
def api_call():
    pass
```

**Delay Sequence:** 2.0s → 2.0s → 2.0s

### Configuration Guidelines

| Use Case | max_attempts | base_delay | exponential |
|----------|--------------|------------|-------------|
| Network Request | 3-5 | 1.0s | Yes |
| Database Query | 2-3 | 0.5s | Yes |
| File Operation | 3-4 | 0.2s | No |
| Rate-Limited API | 3-5 | 2.0s | Yes |

## Health Check System

### Concept

Monitors system components and external dependencies to detect issues early.

### Basic Usage

```python
from src.core.resilience import health_check

# Register a health check
def check_database():
    """Check database connectivity."""
    try:
        # Perform check
        db.ping()
        return True, "Database is healthy"
    except Exception as e:
        return False, f"Database check failed: {e}"

health_check.register("database", check_database)

# Run all checks
results = health_check.run_all()

# Check system health
if health_check.is_system_healthy():
    print("✅ All systems operational")
else:
    print("❌ System unhealthy")
```

### Health Check Return Formats

Health check functions can return:

1. **Tuple:** `(bool, str)` - status and message
2. **Tuple with details:** `(bool, str, dict)` - status, message, and details
3. **Boolean:** `bool` - just status

```python
# Simple boolean
health_check.register("simple", lambda: True)

# Status + message
health_check.register("detailed", lambda: (True, "Service OK"))

# Status + message + details
health_check.register("full", lambda: (
    True,
    "Service operational",
    {"latency_ms": 50, "connections": 10}
))
```

### Getting Comprehensive Status

```python
status = health_check.get_status()

print(status)
# {
#   "healthy": true,
#   "timestamp": "2024-12-17T10:30:00",
#   "checks": {
#     "database": {...},
#     "api": {...}
#   },
#   "summary": {
#     "total": 2,
#     "passed": 2,
#     "failed": 0
#   }
# }
```

## ResilientExchangeClient

Pre-built exchange client with integrated resilience patterns.

### Usage

```python
from src.data.exchange_client import ResilientExchangeClient

# Initialize client
client = ResilientExchangeClient(
    exchange_id="kraken",
    config={"enableRateLimit": True}
)

# Fetch OHLCV data (with automatic retry and circuit breaker)
ohlcv = client.fetch_ohlcv(
    symbol="BTC/USD",
    timeframe="1h",
    limit=100
)

# Fetch balance
balance = client.fetch_balance()

# Fetch ticker
ticker = client.fetch_ticker("BTC/USD")
```

### Automatic Health Check Registration

The `ResilientExchangeClient` automatically registers a health check:

```python
from src.core.resilience import health_check

# Client registers itself automatically
client = ResilientExchangeClient("kraken")

# Health check is now available
results = health_check.run_all()
print(results["exchange_kraken"])
```

## Health Dashboard

Command-line dashboard for system health monitoring.

### Running the Dashboard

```bash
python scripts/health_dashboard.py
```

### Output

```
============================================================
PEAK TRADE HEALTH DASHBOARD
============================================================
Timestamp: 2025-12-17T15:30:00

✅ BACKTEST_ENGINE: healthy
✅ DATABASE: healthy
✅ EXCHANGE_API: healthy

------------------------------------------------------------
System Status: 🟢 HEALTHY
============================================================
```

### JSON Report

The dashboard generates a JSON report at `reports/health_check.json`:

```json
{
  "timestamp": "2025-12-17T15:30:00",
  "checks": {
    "backtest_engine": {
      "name": "backtest_engine",
      "healthy": true,
      "message": "Backtest engine is available",
      "timestamp": "2025-12-17T15:30:00"
    }
  },
  "summary": {
    "total": 3,
    "passed": 3,
    "failed": 0,
    "healthy": true
  }
}
```

### Exit Codes

- **0**: All health checks passed (system healthy)
- **1**: One or more checks failed (system unhealthy)

Useful for CI/CD pipelines:

```bash
python scripts/health_dashboard.py && echo "Deployment ready" || echo "System unhealthy"
```

## Best Practices

### 1. Combining Patterns

Stack decorators for comprehensive protection:

```python
@circuit_breaker(failure_threshold=5, recovery_timeout=60)
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def robust_api_call():
    """Combines circuit breaker with retry logic."""
    pass
```

**Decorator Order Matters:**
- Circuit breaker **first** (outer) - prevents unnecessary retries when circuit is open
- Retry **second** (inner) - handles transient failures

### 2. Appropriate Thresholds

**Don't set too aggressive:**
```python
# ❌ Too aggressive - opens too quickly
@circuit_breaker(failure_threshold=1, recovery_timeout=300)
```

**Do use reasonable values:**
```python
# ✅ Reasonable - allows for transient issues
@circuit_breaker(failure_threshold=5, recovery_timeout=60)
```

### 3. Logging Strategy

All patterns log automatically. Configure logging level:

```python
import logging

# Set logging level for resilience module
logging.getLogger("src.core.resilience").setLevel(logging.INFO)

# For debugging
logging.getLogger("src.core.resilience").setLevel(logging.DEBUG)
```

### 4. Health Check Guidelines

**Good Health Checks:**
- Fast (< 1 second)
- No side effects
- Clear pass/fail criteria
- Meaningful error messages

**Bad Health Checks:**
- Run complex operations
- Modify system state
- Take too long
- Unclear failure messages

### 5. Exception Types

Be specific about which exceptions to handle:

```python
# ✅ Specific exceptions for retry
@retry_with_backoff(expected_exception=ConnectionError)
def network_call():
    pass

# ❌ Too broad - might retry non-transient errors
@retry_with_backoff(expected_exception=Exception)
def operation():
    pass
```

## Troubleshooting

### Circuit Breaker Won't Close

**Problem:** Circuit stays open even after service recovers.

**Solutions:**
1. Check `recovery_timeout` - may be too long
2. Verify service is actually healthy
3. Check logs for errors during recovery attempts
4. Manually reset if needed: `breaker.reset()`

### Retries Exhausted Too Quickly

**Problem:** All retries fail before transient issue resolves.

**Solutions:**
1. Increase `max_attempts`
2. Increase `base_delay` or `max_delay`
3. Use exponential backoff: `exponential=True`
4. Check if errors are actually transient

### Health Checks Always Fail

**Problem:** Health checks report failures even when system works.

**Solutions:**
1. Review check implementation - may be too strict
2. Check for timeout issues - health checks should be fast
3. Review error messages in health check results
4. Test health check function independently

### Performance Impact

**Problem:** Decorators add latency.

**Solutions:**
1. Reduce retry delays for fast operations
2. Use circuit breaker to fail fast when service is down
3. Profile critical paths
4. Consider disabling retry for operations that must be fast

### Memory Leaks

**Problem:** Circuit breakers accumulate in memory.

**Solution:** Use decorator pattern instead of creating new CircuitBreaker instances:

```python
# ✅ Good - decorator reuses same breaker
@circuit_breaker(failure_threshold=5)
def api_call():
    pass

# ❌ Bad - creates new breaker each call
def api_call():
    breaker = CircuitBreaker(failure_threshold=5)
    return breaker.call(lambda: some_function())()
```

## Testing

Run resilience module tests:

```bash
# Run all resilience tests
pytest tests/test_resilience.py -v

# Run specific test
pytest tests/test_resilience.py::TestCircuitBreaker::test_circuit_breaker_opens_after_failures -v

# Run with coverage
pytest tests/test_resilience.py --cov=src.core.resilience --cov-report=html
```

## API Reference

### CircuitBreaker

```python
class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "circuit_breaker"
    )
    
    @property
    def state(self) -> CircuitState
    
    @property
    def stats(self) -> CircuitBreakerStats
    
    def call(self, func: Callable) -> Callable
    
    def reset(self) -> None
```

### Decorators

```python
def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
    name: Optional[str] = None
) -> Callable

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    expected_exception: Type[Exception] = Exception
) -> Callable
```

### HealthCheck

```python
class HealthCheck:
    def register(self, name: str, check_func: Callable) -> None
    
    def run_all(self) -> Dict[str, HealthCheckResult]
    
    def is_system_healthy(self) -> bool
    
    def get_status(self) -> Dict[str, Any]
```

## Integration Examples

### Example 1: Resilient Data Pipeline

```python
from src.core.resilience import circuit_breaker, retry_with_backoff, health_check
from src.data.exchange_client import ResilientExchangeClient

class DataPipeline:
    def __init__(self):
        self.client = ResilientExchangeClient("kraken")
        
        # Register pipeline health check
        health_check.register("data_pipeline", self._health_check)
    
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(max_attempts=3, base_delay=2.0)
    def fetch_market_data(self, symbol: str):
        """Fetch market data with full resilience."""
        return self.client.fetch_ohlcv(symbol, "1h", limit=100)
    
    def _health_check(self):
        """Check if pipeline is operational."""
        try:
            # Test fetch
            self.client.fetch_ticker("BTC/USD")
            return True, "Data pipeline operational"
        except Exception as e:
            return False, f"Pipeline check failed: {e}"
```

### Example 2: Backtest Engine Integration

```python
from src.core.resilience import health_check

def setup_backtest_health_check():
    """Register backtest engine health check."""
    
    def check_backtest_engine():
        try:
            from src.backtest.engine import BacktestEngine
            from src.core.peak_config import load_config
            
            cfg = load_config()
            # Verify engine can be instantiated
            return True, "Backtest engine is available"
        except Exception as e:
            return False, f"Backtest engine check failed: {e}"
    
    health_check.register("backtest_engine", check_backtest_engine)
```

## Further Reading

- [Martin Fowler - Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Google SRE Book - Handling Overload](https://sre.google/sre-book/handling-overload/)
- [AWS - Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

## Changelog

### Version 1.0.0 (December 2024)

- Initial implementation
- Circuit breaker pattern with CLOSED/OPEN/HALF_OPEN states
- Retry logic with exponential backoff
- Health check system
- ResilientExchangeClient for exchange API calls
- Health dashboard script
- Comprehensive test suite
- Full documentation

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review test cases in `tests/test_resilience.py`
3. Check logs with `logging.DEBUG` level
4. Open an issue on GitHub
