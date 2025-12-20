# Peak_Trade Resilience & Stability Guide
**Circuit Breaker, Rate Limiting, and Health Monitoring**

Version: 1.0  
Last Updated: December 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Circuit Breaker Pattern](#circuit-breaker-pattern)
3. [Rate Limiting](#rate-limiting)
4. [Metrics & Monitoring](#metrics--monitoring)
5. [Health Checks](#health-checks)
6. [Configuration](#configuration)
7. [Integration Guide](#integration-guide)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Peak_Trade implements comprehensive resilience patterns to ensure system stability and graceful degradation under failure conditions. The resilience system provides:

- **Circuit Breakers**: Prevent cascading failures by failing fast when dependencies are unavailable
- **Rate Limiting**: Control request rates to external services to prevent overload
- **Metrics Collection**: Monitor system health with Prometheus-compatible metrics
- **Health Checks**: Proactive monitoring of system components

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Backtest, Portfolio, Risk, Live Operations)               │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Resilience Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Circuit       │  │Rate          │  │Health        │     │
│  │Breakers      │  │Limiters      │  │Checks        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Metrics & Observability                         │
│  (Prometheus, Logging, Event Tracking)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Circuit Breaker Pattern

### What is a Circuit Breaker?

A circuit breaker protects your application from cascading failures. When a dependency (e.g., data source, API) fails repeatedly, the circuit breaker "opens" and fails fast without attempting the operation, allowing the failing service time to recover.

### Circuit States

```
     CLOSED ──[failures >= threshold]──> OPEN
        ▲                                  │
        │                                  │
        │                          [timeout elapsed]
        │                                  │
        │                                  ▼
        └──────[call succeeds]────── HALF_OPEN
```

- **CLOSED**: Normal operation, all calls pass through
- **OPEN**: Circuit is open, calls fail immediately without executing
- **HALF_OPEN**: Testing recovery, one call allowed through

### Using Circuit Breakers

#### Method 1: Using the Decorator (Recommended)

```python
from src.core.resilience_helpers import with_resilience

@with_resilience("backtest", "data_load")
def load_market_data(symbol: str):
    """Load market data with circuit breaker protection."""
    # Your implementation here
    return fetch_data(symbol)
```

#### Method 2: Using Direct Circuit Breaker

```python
from src.core.resilience_helpers import create_module_circuit_breaker

# Create circuit breaker for your module
breaker = create_module_circuit_breaker("portfolio", "calculation")

@breaker.call
def calculate_portfolio_metrics():
    """Calculate portfolio metrics with circuit breaker."""
    # Your implementation here
    pass
```

#### Method 3: Manual Circuit Breaker

```python
from src.core.resilience import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60.0,    # Try recovery after 60 seconds
    name="my_operation"
)

@breaker.call
def risky_operation():
    """Operation protected by circuit breaker."""
    # Your implementation here
    pass
```

### Circuit Breaker Configuration

Configure circuit breakers in `config.toml`:

```toml
[resilience]
circuit_breaker_enabled = true
circuit_breaker_threshold = 5
circuit_breaker_timeout = 60

[resilience.portfolio]
circuit_breaker_threshold = 3
circuit_breaker_timeout = 30
```

---

## Rate Limiting

### What is Rate Limiting?

Rate limiting controls the rate of requests to protect both your application and external services from overload. Peak_Trade uses a Token Bucket algorithm for smooth rate limiting with burst support.

### Using Rate Limiters

#### Basic Usage

```python
from src.core.rate_limiter import RateLimiter

# Create rate limiter: 100 requests per 60 seconds
limiter = RateLimiter(max_requests=100, window_seconds=60)

# Try to acquire permission for a request
if limiter.acquire():
    # Request allowed
    make_api_call()
else:
    # Rate limited
    logger.warning("Rate limit exceeded")
```

#### Endpoint-Specific Limits

```python
limiter = RateLimiter(max_requests=100, window_seconds=60)

# Add endpoint-specific limits
limiter.add_endpoint("fetch_ohlcv", max_requests=50, window_seconds=60)
limiter.add_endpoint("fetch_ticker", max_requests=200, window_seconds=60)

# Use endpoint-specific limits
if limiter.acquire("fetch_ohlcv"):
    fetch_ohlcv_data()
```

#### Using with Resilience Helpers

```python
from src.core.resilience_helpers import with_resilience

@with_resilience(
    "data",
    "api_fetch",
    use_rate_limiter=True,
    use_circuit_breaker=True
)
def fetch_data_from_api():
    """Fetch data with both rate limiting and circuit breaker."""
    # Your implementation here
    pass
```

### Rate Limiter Configuration

```toml
[resilience]
rate_limit_enabled = true
rate_limit_requests = 100
rate_limit_window = 60

[resilience.data]
rate_limit_requests = 200
rate_limit_window = 60
```

---

## Metrics & Monitoring

### Prometheus Metrics

Peak_Trade exposes Prometheus-compatible metrics for monitoring:

#### Circuit Breaker Metrics

- `peak_trade_circuit_breaker_state`: Current state (0=closed, 1=half_open, 2=open)
- `peak_trade_circuit_breaker_failures_total`: Total failures
- `peak_trade_circuit_breaker_state_changes_total`: State transitions

#### Rate Limiter Metrics

- `peak_trade_rate_limit_hits_total`: Total requests
- `peak_trade_rate_limit_rejections_total`: Rejected requests
- `peak_trade_rate_limit_tokens_available`: Available tokens

#### Request Metrics

- `peak_trade_request_duration_seconds`: Request latency histogram
- `peak_trade_operation_failures_total`: Operation failures by type
- `peak_trade_operation_successes_total`: Successful operations

### Using Metrics

```python
from src.core.metrics import metrics

# Track operation latency
with metrics.track_latency("data_fetch"):
    fetch_data()

# Record circuit breaker state change
metrics.record_circuit_breaker_state_change(
    name="portfolio",
    from_state="closed",
    to_state="open"
)

# Record rate limit hit
metrics.record_rate_limit_hit("api", "fetch_ohlcv")

# Record operation failure
metrics.record_operation_failure("backtest", "ValueError")
```

### Accessing Metrics

1. **Prometheus Endpoint**: `GET /health/prometheus`
2. **JSON Format**: `GET /health/metrics`
3. **In-Memory Snapshots**:

```python
from src.core.metrics import metrics

# Get recent snapshots
snapshots = metrics.get_snapshots(limit=100)

# Get summary
summary = metrics.get_summary()
```

---

## Health Checks

### Health Check API

Peak_Trade provides REST endpoints for health monitoring:

- `GET /health`: Basic health status (200 OK if healthy)
- `GET /health/detailed`: Detailed diagnostics
- `GET /health/metrics`: Current metrics in JSON
- `GET /health/prometheus`: Prometheus metrics export

### Registering Health Checks

```python
from src.core.resilience import health_check

def check_database_connection():
    """Check if database is accessible."""
    try:
        # Your check logic
        result = database.ping()
        return True, "Database is healthy"
    except Exception as e:
        return False, f"Database check failed: {e}"

# Register the check
health_check.register("database", check_database_connection)

# Run all checks
results = health_check.run_all()
is_healthy = health_check.is_system_healthy()
```

### Built-in Health Checks

The system automatically registers health checks for:

- Metrics system
- Resilience system
- Circuit breakers
- Exchange connectivity (if configured)

---

## Configuration

### Configuration File Structure

All resilience settings are configured in `config.toml`:

```toml
# ============================================================================
# RESILIENCE & STABILITY
# ============================================================================
[resilience]
# Global settings
circuit_breaker_enabled = true
circuit_breaker_threshold = 5
circuit_breaker_timeout = 60
rate_limit_enabled = true
rate_limit_requests = 100
rate_limit_window = 60
metrics_enabled = true

# Module-specific settings override global defaults
[resilience.backtest]
circuit_breaker_threshold = 5
circuit_breaker_timeout = 60

[resilience.portfolio]
circuit_breaker_threshold = 3
circuit_breaker_timeout = 30

[resilience.risk]
circuit_breaker_threshold = 3
fail_safe_defaults = true

[resilience.live]
circuit_breaker_threshold = 2
circuit_breaker_timeout = 120
rate_limit_requests = 30
```

### Environment-Specific Configuration

You can override configuration via environment variables:

```bash
export PEAK_TRADE_CIRCUIT_BREAKER_THRESHOLD=10
export PEAK_TRADE_RATE_LIMIT_REQUESTS=200
```

---

## Integration Guide

### Step-by-Step Integration

#### 1. Add Resilience to Your Module

```python
# your_module.py
import logging
from src.core.resilience_helpers import with_resilience

logger = logging.getLogger(__name__)

@with_resilience("your_module", "operation_name")
def your_function():
    """Your function with resilience."""
    # Your implementation
    pass
```

#### 2. Configure Module Settings

Add to `config.toml`:

```toml
[resilience.your_module]
circuit_breaker_enabled = true
circuit_breaker_threshold = 5
rate_limit_requests = 100
```

#### 3. Register Health Checks

```python
from src.core.resilience import health_check

def check_your_module():
    # Check logic
    return True, "Module is healthy"

health_check.register("your_module", check_your_module)
```

#### 4. Monitor Metrics

Access metrics via:
- Prometheus: `GET /health/prometheus`
- JSON: `GET /health/metrics`
- Logs: Check application logs for resilience events

---

## Best Practices

### Circuit Breakers

1. **Set Appropriate Thresholds**
   - Higher for non-critical operations (5-10 failures)
   - Lower for critical operations (2-3 failures)
   - Consider impact of false positives

2. **Choose Recovery Times Wisely**
   - 30-60s for transient network issues
   - 120s+ for service restarts
   - Match to expected recovery time of dependency

3. **Handle Open Circuit Gracefully**
   ```python
   try:
       result = protected_function()
   except Exception as e:
       if "CircuitBreaker" in str(e):
           # Use fallback or cached data
           result = get_cached_data()
       else:
           raise
   ```

### Rate Limiting

1. **Match Limits to Provider**
   - Check API provider's rate limits
   - Set limits to 80% of provider's limit
   - Use endpoint-specific limits for different tiers

2. **Handle Rate Limit Errors**
   ```python
   if not limiter.acquire():
       wait_time = limiter.get_wait_time()
       logger.warning(f"Rate limited, wait {wait_time}s")
       # Implement backoff or queuing
   ```

3. **Monitor Token Utilization**
   ```python
   stats = limiter.get_stats()
   if stats["rejection_rate"] > 0.1:  # 10%
       logger.warning("High rate limit rejection rate")
   ```

### Metrics

1. **Track Critical Operations**
   - Data fetches
   - Portfolio calculations
   - Risk checks
   - Order submissions

2. **Use Labels Effectively**
   ```python
   metrics.record_operation_failure(
       operation="backtest.calculate",
       error_type="ValueError"
   )
   ```

3. **Set Up Alerts**
   - Circuit breaker opens
   - High rate limit rejection
   - Prolonged OPEN state
   - Health check failures

---

## Troubleshooting

### Common Issues

#### Circuit Breaker Stuck Open

**Symptoms**: Circuit breaker remains OPEN despite service recovery

**Solutions**:
1. Check if recovery timeout is too long
2. Verify underlying issue is resolved
3. Manually reset if needed:
   ```python
   from src.core.resilience_helpers import get_all_circuit_breakers
   breakers = get_all_circuit_breakers()
   breakers["your_breaker"].reset()
   ```

#### High Rate Limit Rejections

**Symptoms**: Many requests rejected by rate limiter

**Solutions**:
1. Increase rate limits in config.toml
2. Implement request queuing
3. Add caching to reduce requests
4. Review calling patterns

#### Health Check Failures

**Symptoms**: `/health` returns 503

**Solutions**:
1. Check individual checks: `GET /health/detailed`
2. Review logs for specific failures
3. Verify external dependencies are available
4. Check network connectivity

#### Performance Impact

**Symptoms**: System slowdown after adding resilience

**Solutions**:
1. Disable unnecessary features in config
2. Check metrics overhead
3. Review circuit breaker placement
4. Optimize rate limiter configuration

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("src.core.resilience").setLevel(logging.DEBUG)
logging.getLogger("src.core.rate_limiter").setLevel(logging.DEBUG)
logging.getLogger("src.core.metrics").setLevel(logging.DEBUG)
```

Check metrics for issues:

```python
from src.core.metrics import metrics
summary = metrics.get_summary()
print(summary)
```

---

## Examples

### Complete Example: Resilient Data Fetcher

```python
from src.core.resilience_helpers import (
    with_resilience,
    create_module_circuit_breaker,
    create_module_rate_limiter
)
from src.core.resilience import health_check
from src.core.metrics import metrics
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.circuit_breaker = create_module_circuit_breaker("data", "fetch")
        self.rate_limiter = create_module_rate_limiter("data", "api")
        
        # Register health check
        health_check.register("data_fetcher", self._health_check)
    
    @with_resilience("data", "fetch", use_rate_limiter=True)
    def fetch_market_data(self, symbol: str):
        """Fetch market data with full resilience."""
        try:
            # Your fetch logic here
            data = self._fetch_from_api(symbol)
            logger.info(f"Successfully fetched data for {symbol}")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            # Try cache as fallback
            return self._get_cached_data(symbol)
    
    def _health_check(self):
        """Health check for data fetcher."""
        try:
            # Quick check
            self.fetch_market_data("BTC/EUR")
            return True, "Data fetcher operational"
        except Exception as e:
            return False, f"Data fetcher error: {e}"
    
    def _fetch_from_api(self, symbol: str):
        # Actual API call
        pass
    
    def _get_cached_data(self, symbol: str):
        # Fallback to cache
        pass
```

---

## Further Reading

- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Peak_Trade Architecture Documentation](./ARCHITECTURE.md)

---

## Support

For issues or questions:
1. Check this guide first
2. Review logs and metrics
3. Check `/health/detailed` endpoint
4. Review GitHub Issues
5. Contact the development team

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Maintainer**: Peak_Trade Team
