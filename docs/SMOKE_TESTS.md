# Peak_Trade Smoke Tests

## Overview

The Peak_Trade smoke test suite provides fast, comprehensive validation of critical stability and resilience features. These tests are designed to run in CI/CD pipelines and local development workflows to ensure system health.

**Runtime:** < 2 seconds
**Coverage:** Circuit breaker, retry patterns, health checks, data contracts, cache integrity, reproducibility

## Running Smoke Tests

### Quick Run

```bash
# Using convenience script (historical, script no longer exists)
# bash scripts/run_smoke_tests.sh

# Using pytest directly (recommended)
python3 -m pytest -m smoke tests/test_resilience.py tests/test_stability_smoke.py -v
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run smoke tests
  run: python3 -m pytest -m smoke tests/test_resilience.py tests/test_stability_smoke.py -v

# GitLab CI example
smoke_tests:
  script:
    - python3 -m pytest -m smoke tests/test_resilience.py tests/test_stability_smoke.py -v
  timeout: 1 minute
```

## Test Coverage

### Resilience Tests (6 smoke tests)

**Circuit Breaker:**
- `test_circuit_breaker_init` - Initialization and configuration
- `test_circuit_breaker_opens_after_failures` - Failure threshold behavior

**Retry with Backoff:**
- `test_retry_success_first_attempt` - Successful first attempt
- `test_retry_with_backoff_success` - Recovery after transient failures

**Health Check System:**
- `test_health_check_init` - Health check initialization
- `test_health_check_run_all_success` - Successful health check execution

### Stability Tests (8 smoke tests)

**Data Contracts & Caching:**
- `test_stability_smoke_full_e2e` - Full E2E validation pipeline
- `test_stability_smoke_contract_violation` - Data contract enforcement
- `test_stability_smoke_cache_corruption_detection` - Cache integrity checks

**Reproducibility:**
- `test_stability_smoke_deterministic_run` - Deterministic execution
- `test_stability_smoke_config_hash_stability` - Config hashing stability
- `test_stability_smoke_reproducibility_context_roundtrip` - Context serialization

**Cache Manifest:**
- `test_stability_smoke_manifest_multi_file` - Multi-file tracking

**Performance:**
- `test_stability_smoke_performance_check` - Runtime < 1s validation

## Exit Codes

- `0` - All smoke tests passed (system ready)
- Non-zero - One or more tests failed (system not ready)

## Adding New Smoke Tests

To add a new smoke test:

1. Mark the test function with `@pytest.mark.smoke`:
   ```python
   @pytest.mark.smoke
   def test_my_new_feature():
       """Fast test for critical feature."""
       assert critical_feature_works()
   ```

2. Ensure the test runs in < 100ms
3. Test should validate critical functionality only
4. Avoid external dependencies when possible

## Criteria for Smoke Tests

A test qualifies as a smoke test if it:
- ✅ Runs in < 100ms (< 1s for E2E tests)
- ✅ Tests critical functionality
- ✅ Has no external dependencies (or uses mocks)
- ✅ Provides clear pass/fail indication
- ✅ Can run in parallel with other tests

## Related Documentation

- [Resilience Module Documentation](./RESILIENCE.md)
- [Stability Plan](./ops/STABILITY_RESILIENCE_PLAN_V1.md)
- [Testing Guide](TESTING.md)

## Maintenance

The smoke test suite should be kept fast and focused. If runtime exceeds 2 seconds:
1. Review individual test performance
2. Consider moving slow tests to integration suite
3. Optimize or mock external dependencies

## Support

For issues or questions about smoke tests:
- Check test output for specific failure details
- Review individual test documentation
- Consult stability plan documentation
- Open an issue with `testing` label
