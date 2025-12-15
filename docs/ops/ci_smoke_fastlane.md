# CI Smoke Fast-Lane Runbook

**Issue:** [#19] G3-1 Setup CI Pipeline with Smoke Tests
**Owner:** Engineering
**Last Updated:** 2025-12-15

---

## Overview

The CI smoke fast-lane is an ultra-fast test suite (<2-3 minutes) that validates critical live-mode entrypoints and safety gates before running the full CI test matrix.

**Purpose:** Rapid feedback on live pipeline correctness without external dependencies.

---

## What Gets Tested

### 1. Live Risk Limits (Issue #20 dependency)
- `LiveOrderRequest` creation and validation
- Direction-to-side conversion logic
- `LiveRiskConfig` dataclass integrity
- Risk limit enforcement (position size, exposure, daily loss)
- Order-level risk checks (empty and valid order lists)

### 2. Execution Pipeline
- `SignalEvent` dataclass creation
- Signal interpretation (entry/exit detection)
- Signal-to-order lifecycle validation

### 3. Core Backtest Engine
- Baseline backtest functionality
- Strategy execution without live dependencies

---

## Safety Guarantees

The smoke fast-lane enforces strict **offline-only** execution:

| Guard | Enforcement |
|-------|-------------|
| **No live exchanges** | Test config uses synthetic data only |
| **No API keys** | No environment variables or secrets loaded |
| **No external calls** | Network mocking enforced via test fixtures |
| **Deterministic** | All data is pre-generated or synthetic |

**Verification:**
- Tests use `config.test.toml` (set via `conftest.py`)
- No `KRAKEN_API_KEY` or similar environment variables
- All exchange interactions mocked or skipped

---

## Running Locally

### Quick Run
```bash
make ci-smoke
```

### Manual Run
```bash
bash scripts/ci_smoke_fastlane.sh
```

### Debug Run (verbose)
```bash
pytest tests/test_live_smoke.py tests/test_execution_pipeline_smoke.py tests/test_backtest_smoke.py -v --tb=long
```

---

## CI Integration

### Workflow Location
`.github/workflows/ci.yml` → `ci-smoke-fastlane` job

### Execution Order
1. **ci-smoke-fastlane** (runs immediately, no dependencies)
2. **tests** (main test matrix, runs in parallel)
3. **strategy-smoke** (runs after tests complete)

### Artifact Upload on Failure

When smoke tests fail, the following artifacts are uploaded to GitHub Actions:

**Artifact Name:** `ci-smoke-fastlane-debug`
**Retention:** 7 days
**Contents:**
- `junit.xml` - JUnit test results for CI integration
- `pytest_output.txt` - Full pytest output with tracebacks

**How to access:**
1. Go to failed workflow run in GitHub Actions
2. Scroll to "Artifacts" section
3. Download `ci-smoke-fastlane-debug.zip`
4. Extract and inspect `pytest_output.txt` for failure details

---

## Troubleshooting

### Smoke tests fail but full tests pass
**Cause:** Smoke test subset may hit edge cases not covered by integration tests.

**Action:**
1. Download artifact from GitHub Actions
2. Review `pytest_output.txt` for specific failure
3. Run locally: `make ci-smoke`
4. Fix the failing test or update smoke test selection

### Smoke tests timeout
**Cause:** External network calls or blocking I/O.

**Action:**
1. Verify test config uses `config.test.toml` (check `conftest.py`)
2. Ensure no live exchange initialization
3. Check for missing mocks/fixtures

### Artifacts not uploaded
**Cause:** `if: failure()` condition not met or path incorrect.

**Action:**
1. Verify `test_results/ci_smoke_fastlane/` directory exists
2. Check workflow step uses `if: failure()` (not `if: always()`)
3. Confirm pytest generates `junit.xml` output

---

## Adding Tests to Fast-Lane

### Selection Criteria

✅ **Include:**
- Core safety gate validations (risk limits, order checks)
- Live pipeline entrypoints (execution, orders, workflows)
- Fast-running (<5s per test)
- No external dependencies (mocked/synthetic data)

❌ **Exclude:**
- Integration tests requiring external APIs
- Slow tests (>10s per test)
- Tests requiring secrets or live credentials
- Full end-to-end workflows (save for integration suite)

### How to Add

1. Edit `scripts/ci_smoke_fastlane.sh`
2. Add test path to `SMOKE_TESTS` array:
   ```bash
   SMOKE_TESTS=(
       ...
       "tests/test_your_new_smoke.py::test_specific_case"
   )
   ```
3. Run locally to verify: `make ci-smoke`
4. Ensure total runtime stays <2-3 minutes

---

## Related Documentation

- Issue #19: [G3-1] Setup CI Pipeline with Smoke Tests
- Issue #20: [D1-2] Implement Live Risk Limits
- Issue #23: [E1-3] Order Execution Engine – Live Mode (blocked by #19, #20)
- `.github/workflows/ci.yml` - Full CI workflow configuration
- `scripts/ci_smoke_fastlane.sh` - Smoke test runner implementation

---

## Kill-Switch / Rollback

### Disable Fast-Lane in CI

If smoke tests are blocking CI incorrectly:

1. **Temporary bypass (emergency):**
   ```yaml
   # In .github/workflows/ci.yml
   ci-smoke-fastlane:
     if: false  # Disable temporarily
   ```

2. **Permanent removal:**
   ```bash
   # Remove job from ci.yml
   git revert <commit-sha>
   ```

### Verify Dry-Run vs Live

Fast-lane tests are **always dry-run**. To verify:

```bash
# Check test config
grep -r "PEAK_TRADE_CONFIG_PATH" tests/conftest.py

# Should output: config/config.test.toml
# NOT: config/config.live.toml or similar
```

**Live mode is IMPOSSIBLE in smoke fast-lane:**
- No API keys loaded
- Test config has `live_mode: false` enforced
- All exchange objects mocked

---

## Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Runtime** | <3 min | ~2 min (measured locally) |
| **Test count** | 10-20 tests | 9 tests (initial) |
| **Pass rate** | 100% (stable) | TBD (after first CI run) |
| **Artifact size** | <5 MB on failure | ~50 KB (junit.xml + logs) |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Initial fast-lane implementation | Claude Code (Issue #19) |
