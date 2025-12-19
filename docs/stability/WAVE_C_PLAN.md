# Stability – Wave C Plan

## Goal
Implement resilience patterns (circuit breaker, retry with backoff, health checks) and CI smoke test markers for fast failure detection.

## Deliverables
1) ✅ Circuit Breaker Pattern — **DONE**
2) ✅ Retry with Exponential Backoff — **DONE**
3) ✅ Health Check System — **DONE**
4) ✅ Integration Tests — **DONE**
5) 🔜 CI Smoke Test Markers — **PENDING**

## Tasks
- [x] resilience: implement CircuitBreaker class with state machine — `src/core/resilience.py`
- [x] resilience: implement retry_with_backoff decorator — `src/core/resilience.py`
- [x] resilience: implement HealthCheck system — `src/core/resilience.py`
- [x] tests: comprehensive test suite — `tests/test_resilience.py` (28 tests)
- [x] fix: resolve datetime.utcnow() deprecation warning
- [ ] tests: add @pytest.mark.smoke markers to key tests
- [ ] ci: integrate smoke tests in GitHub Actions workflow
- [ ] docs: update main stability plan

## Implementation

### Wave C Components

1. **Circuit Breaker Pattern** (`src/core/resilience.py`)
   - `CircuitBreaker` class with CLOSED/OPEN/HALF_OPEN states
   - Configurable failure threshold and recovery timeout
   - Automatic state transitions based on success/failure patterns
   - Statistics tracking (failure count, success count, state changes)
   - Decorator factory for easy integration: `@circuit_breaker()`
   - 8 tests (all passing)

2. **Retry with Exponential Backoff** (`src/core/resilience.py`)
   - `retry_with_backoff()` decorator for transient failure handling
   - Exponential or constant backoff strategies
   - Configurable max attempts, base delay, and max delay
   - Exception type filtering
   - 6 tests (all passing)

3. **Health Check System** (`src/core/resilience.py`)
   - `HealthCheck` class for service availability monitoring
   - Global health check instance for convenience
   - `HealthCheckResult` dataclass with structured output
   - Support for multiple check registration
   - System-wide health status aggregation
   - 10 tests (all passing)

4. **Integration Tests** (`tests/test_resilience.py`)
   - Combined circuit breaker + retry patterns
   - Health checks with circuit breaker integration
   - 2 integration tests (all passing)
   - 2 global instance tests (all passing)

5. **Bug Fix: Deprecation Warning**
   - Fixed `datetime.utcnow()` deprecation by using `timezone.utc`
   - All tests now run without warnings

### Usage Examples

**Circuit Breaker:**
```python
from src.core.resilience import circuit_breaker

@circuit_breaker(failure_threshold=3, recovery_timeout=30)
def fetch_external_api():
    # Your API call here
    pass
```

**Retry with Backoff:**
```python
from src.core.resilience import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def unstable_operation():
    # Your operation here
    pass
```

**Health Check:**
```python
from src.core.resilience import health_check

def check_database():
    return True, "Database is healthy"

health_check.register("database", check_database)
results = health_check.run_all()
is_healthy = health_check.is_system_healthy()
```

**Combined Pattern:**
```python
from src.core.resilience import circuit_breaker, retry_with_backoff

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def robust_api_call():
    # Retry on transient failures, circuit breaker prevents cascading failures
    pass
```

## Pending: CI Smoke Test Markers

### C2: CI Smoke Gate
**Status:** Pending implementation

**Approach:**
1. Add `@pytest.mark.smoke` markers to fast, critical tests:
   - Data contract validation
   - Error taxonomy
   - Cache atomic operations
   - Reproducibility context
   - Circuit breaker basics
   - Retry logic
   - Health check registration

2. Update pytest configuration in `pytest.ini`:
   ```ini
   [pytest]
   markers =
       smoke: Fast smoke tests for CI (<5s total)
   ```

3. Create GitHub Actions workflow job:
   ```yaml
   smoke-tests:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v3
       - name: Run Smoke Tests
         run: pytest -m smoke --tb=short
   ```

4. Document usage in main stability plan

**Expected Runtime:** < 5 seconds for all smoke tests combined

## Acceptance Criteria
- ✅ Circuit breaker prevents cascading failures
- ✅ Retry logic handles transient failures gracefully
- ✅ Health checks provide system-wide visibility
- ✅ All tests pass without warnings
- 🔜 Smoke tests can be run via `pytest -m smoke`
- 🔜 CI pipeline includes smoke test gate

## Test Results
- **Circuit Breaker**: 8/8 tests passing
- **Retry with Backoff**: 6/6 tests passing
- **Health Check**: 10/10 tests passing
- **Integration**: 4/4 tests passing
- **Total**: 28/28 tests passing in 0.64s
- **Warnings**: 0 (fixed datetime deprecation)

## Status
✅ **MOSTLY COMPLETE** — Core resilience features implemented and tested
🔜 **PENDING** — CI smoke test markers and GitHub Actions integration

## Migration Notes

### For Operators
Wave C features are available now:

1. **Wrap external API calls with resilience patterns:**
   ```python
   from src.core.resilience import circuit_breaker, retry_with_backoff
   
   @circuit_breaker(failure_threshold=3, recovery_timeout=60)
   @retry_with_backoff(max_attempts=3, base_delay=1.0)
   def fetch_market_data():
       # Your API call
       pass
   ```

2. **Register health checks for monitoring:**
   ```python
   from src.core.resilience import health_check
   
   health_check.register("exchange_api", lambda: check_exchange_health())
   health_check.register("cache", lambda: check_cache_health())
   
   # Check overall system health
   if not health_check.is_system_healthy():
       logger.error("System health check failed")
   ```

### For Developers

1. **Use structured resilience patterns:**
   - Circuit breaker for fail-fast behavior
   - Retry for transient failure handling
   - Health checks for system monitoring

2. **Test resilience behavior:**
   ```python
   from src.core.resilience import CircuitBreaker
   
   breaker = CircuitBreaker(failure_threshold=3)
   # Test circuit opens after failures
   # Test recovery in HALF_OPEN state
   ```

## Breaking Changes
None. All features are opt-in via decorators and explicit registration.

## Next Steps
1. Add `@pytest.mark.smoke` markers to key tests
2. Update `pytest.ini` with smoke marker definition
3. Create/update GitHub Actions workflow for smoke tests
4. Update main stability plan with Wave C completion
5. Document smoke test usage in developer guide
