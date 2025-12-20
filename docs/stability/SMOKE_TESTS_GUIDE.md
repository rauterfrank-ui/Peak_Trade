# Stability Smoke Tests - Quick Reference

## Overview

The stability smoke tests are a carefully curated set of fast, critical-path tests that validate the core stability & resilience features. These tests run in **< 1 second** and serve as a fast-fail gate in CI/CD pipelines.

## Running Smoke Tests

### Local Development

```bash
# Run all smoke tests (< 1 second)
pytest -m smoke -v

# Run stability smoke tests only
pytest tests/test_stability_smoke.py tests/test_data_contracts.py tests/test_error_taxonomy.py tests/test_resilience.py -m smoke -v

# Run smoke tests with coverage
pytest -m smoke --cov=src --cov-report=term-missing
```

### CI/CD Integration

Smoke tests are automatically run in GitHub Actions CI before the full test suite:

```yaml
- name: "Stability Smoke Tests (Fast Gate)"
  run: |
    pytest tests/test_stability_smoke.py tests/test_data_contracts.py tests/test_error_taxonomy.py tests/test_resilience.py -m smoke -v --tb=short
```

This provides:
- **Fast feedback** — Results in < 5 seconds
- **Early failure detection** — Catches critical issues before running full suite
- **Resource efficiency** — Reduces CI time for PRs with basic errors

## Smoke Test Coverage

### Wave A: Correctness & Determinism (4 tests)

**Data Contracts:**
- `test_validate_ohlcv_valid_strict` — Valid OHLCV passes strict validation
- `test_validate_ohlcv_missing_columns` — Missing columns are detected

**Error Taxonomy:**
- `test_peak_trade_error_base` — Base error class works correctly
- `test_peak_trade_error_with_hint` — Errors include hints in messages

### Wave B: Cache Robustness & Reproducibility (3 tests)

**Stability Smoke:**
- `test_stability_smoke_full_e2e` — Full E2E validation roundtrip
- `test_stability_smoke_contract_violation` — Contract violations are caught
- `test_stability_smoke_performance_check` — E2E runs in < 1 second

### Wave C: Resilience Patterns (2 tests)

**Resilience:**
- `test_circuit_breaker_init` — Circuit breaker initializes correctly
- `test_retry_success_first_attempt` — Retry decorator works on success

## Adding New Smoke Tests

### Criteria for Smoke Tests

A test should be marked as smoke if it meets ALL of these criteria:

1. **Fast** — Runs in < 100ms (preferably < 50ms)
2. **Critical** — Tests core functionality that would break the system if failing
3. **Deterministic** — Always produces the same result (no flakiness)
4. **No external dependencies** — No network calls, no external APIs
5. **Representative** — Tests the happy path or most common failure mode

### Adding the Marker

```python
import pytest

@pytest.mark.smoke
def test_my_critical_feature():
    """Brief description of what is being tested."""
    # Your test code here
    assert important_function() == expected_result
```

### Test Organization

Smoke tests should be distributed across test files based on the feature being tested:
- Data validation → `test_data_contracts.py`
- Error handling → `test_error_taxonomy.py`
- Cache operations → `test_cache_atomic.py`, `test_cache_manifest.py`
- Reproducibility → `test_repro.py`
- Resilience patterns → `test_resilience.py`
- End-to-end flows → `test_stability_smoke.py`

## Performance Targets

| Category | Target | Current |
|----------|--------|---------|
| Individual test | < 100ms | ✅ < 100ms |
| Full smoke suite | < 5s | ✅ 0.82s |
| CI overhead | < 10s | ✅ < 5s |

## Troubleshooting

### Smoke test failing locally but passing in CI

1. Check for environment-specific dependencies
2. Verify no test pollution (use `--forked` if needed)
3. Check git state (dirty working tree may affect repro tests)

### Smoke test is slow (> 100ms)

1. Profile the test: `pytest -m smoke --durations=10`
2. Consider mocking external dependencies
3. Use smaller test data
4. Move to integration tests if it requires heavy setup

### Smoke test is flaky

1. Smoke tests MUST be deterministic
2. Check for:
   - Time-based logic (use fixed time in tests)
   - Random numbers (use fixed seeds)
   - Concurrent operations (avoid or synchronize)
3. If unfixable, remove smoke marker and move to integration tests

## Related Documentation

- **Main Plan:** [`docs/ops/STABILITY_RESILIENCE_PLAN_V1.md`](../ops/STABILITY_RESILIENCE_PLAN_V1.md)
- **Wave A Plan:** Integrated in main plan
- **Wave B Plan:** [`docs/stability/WAVE_B_PLAN.md`](WAVE_B_PLAN.md)
- **Wave C Plan:** [`docs/stability/WAVE_C_PLAN.md`](WAVE_C_PLAN.md)
- **Pytest Configuration:** [`pytest.ini`](../../pytest.ini)

## Maintenance

### Review Schedule

- **Quarterly:** Review smoke test performance and coverage
- **Per Release:** Verify smoke tests cover new critical features
- **As Needed:** Add smoke tests for regression fixes

### Smoke Test Health Metrics

Track these metrics over time:
1. **Execution time** — Should stay < 1s total
2. **Pass rate** — Should be 100% (flaky tests should be removed)
3. **Coverage** — Should cover all critical paths in stability modules
4. **Count** — Aim for 10-20 tests (too few = gaps, too many = slow)

Current status: **9 tests, 0.82s runtime, 100% pass rate** ✅

## Examples

### Good Smoke Test

```python
@pytest.mark.smoke
def test_validate_ohlcv_valid_strict(valid_ohlcv_df):
    """Valid OHLCV passes strict validation."""
    # Fast: Just validation logic, no I/O
    # Critical: Core data contract feature
    # Deterministic: Fixed input, predictable output
    validate_ohlcv(valid_ohlcv_df, strict=True, require_tz=True)
```

### Bad Smoke Test (should not be smoke)

```python
# DON'T mark this as smoke - too slow!
def test_full_backtest_with_real_data():
    """Run complete backtest with 1 year of market data."""
    # Slow: Loads real data, runs full backtest
    # Not critical: Integration test, not core feature
    # Potentially flaky: Depends on data availability
    df = load_real_market_data("BTC/USD", "1y")
    results = run_backtest(df, strategy="ma_crossover")
    assert results.sharpe_ratio > 0.5
```

## Conclusion

Smoke tests are a critical part of the stability & resilience infrastructure. They provide fast feedback and early failure detection while maintaining high quality standards. Keep them fast, focused, and deterministic!
