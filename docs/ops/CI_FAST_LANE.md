# CI Smoke Fast Lane – Operator Guide

**Issue**: #19 (G3-1) CI Pipeline with Smoke Tests (Fast Lane)
**Status**: ✅ Implemented
**Workflow**: `.github/workflows/ci_smoke_fastlane.yml`

---

## Overview

The **CI Smoke Fast Lane** is an ultra-fast, deterministic smoke test suite that runs on every PR and push. It catches critical issues FAST (< 2-3 min target) without external dependencies, secrets, or live risk.

**Purpose**: Fail-fast gate for critical issues before running full test suite.

---

## What Gets Tested

### 1. Syntax Check (compileall)
- Validates that all Python files in `src/` are syntactically correct
- Catches import errors, syntax errors, indentation issues
- **Fast**: ~5-10 seconds

### 2. Core Imports Smoke Test
- Tests that critical modules can be imported without errors
- Modules tested:
  - `src.core` (environment, experiments, peak_config, risk)
  - `src.live` (alerts, orders, risk_limits, safety)
  - `src.execution.pipeline`
  - `src.governance.go_no_go`
  - `src.strategies.ma_crossover`
  - `src.backtest.engine`
  - `src.data.loader`
  - `src.analytics.performance`
- **Fast**: ~1-2 seconds

### 3. Config Loading Smoke Test
- Validates that `config.toml` exists and is loadable
- Checks required sections (environment, general, live_risk)
- Verifies safe-by-default settings (e.g., `enable_live_trading=false`)
- **Fast**: ~0.5 seconds

### 4. Live-Gating Safety Smoke Test
- Verifies governance locks (`live_order_execution` must be "locked")
- Checks environment defaults (must be "paper")
- Validates SafetyGuard blocks live orders by default
- Ensures LiveRiskLimits have safe defaults
- **Fast**: ~1 second

**Total Runtime**: < 10 seconds (excluding setup)

---

## Scope & Philosophy

**What the Fast Lane DOES**:
- ✅ Catch syntax/import errors
- ✅ Validate config loading
- ✅ Ensure live-gating is safe
- ✅ Run in < 2-3 minutes (total, including setup)
- ✅ Zero external dependencies (no network calls, no secrets)
- ✅ 100% deterministic (no flakes)

**What the Fast Lane DOES NOT**:
- ❌ Run full test suite (use main CI for that)
- ❌ Run backtests or strategies
- ❌ Test exchange integrations
- ❌ Validate complex business logic
- ❌ Run on Windows/macOS (Linux-only for speed)

**Philosophy**: The Fast Lane is a **safety net**, not a comprehensive test. It should catch the most common breaking changes (imports, config, gating) in seconds, not minutes.

---

## Running Locally

### Quick Run

```bash
# Run smoke tests via Makefile
make ci-smoke

# Or run script directly
bash scripts/ci_smoke_fastlane.sh
```

**Expected output**:
```
=============================================================================
CI Smoke Fast Lane
=============================================================================
Repo: /path/to/Peak_Trade
Reports: /path/to/Peak_Trade/reports/ci_smoke

[1/4] Capturing environment snapshot...
✓ Environment snapshot saved

[2/4] Running Python syntax check (compileall)...
✓ Syntax check passed

[3/4] Running smoke tests...
tests/smoke/test_config_smoke.py::test_config_toml_exists PASSED       [ 20%]
tests/smoke/test_config_smoke.py::test_config_loadable PASSED          [ 40%]
tests/smoke/test_imports_smoke.py::test_core_imports PASSED            [ 60%]
tests/smoke/test_imports_smoke.py::test_live_imports PASSED            [ 80%]
tests/smoke/test_live_gating_smoke.py::test_live_execution_governance_locked PASSED [100%]
✓ Smoke tests PASSED

[4/4] Summary

========================================
✓ CI SMOKE FAST LANE: PASSED
========================================

Reports:
  - /path/to/Peak_Trade/reports/ci_smoke/junit.xml
  - /path/to/Peak_Trade/reports/ci_smoke/pytest.txt
  - /path/to/Peak_Trade/reports/ci_smoke/env.txt
```

### Run Individual Smoke Tests

```bash
# Run only import tests
pytest tests/smoke/test_imports_smoke.py -v

# Run only config tests
pytest tests/smoke/test_config_smoke.py -v

# Run only gating tests
pytest tests/smoke/test_live_gating_smoke.py -v

# Run all smoke tests with pytest directly
pytest tests/smoke/ -v
```

---

## CI Integration

### Workflow Details

**File**: `.github/workflows/ci_smoke_fastlane.yml`

**Triggers**:
- `push` to `main` or `master`
- `pull_request` to `main` or `master`

**Concurrency**: Cancel in-progress runs for same branch/PR

**Timeout**: 5 minutes (hard timeout)

**Job**: `smoke-fastlane`
- Runs on: `ubuntu-latest`
- Python: `3.11`
- Steps:
  1. Checkout code
  2. Setup Python + cache pip
  3. Install minimal dependencies
  4. Run `make ci-smoke`
  5. Upload artifacts (on failure only)
  6. Display summary

### Artifacts (on failure only)

When smoke tests fail, the following artifacts are uploaded:

- **`reports/ci_smoke/junit.xml`** - JUnit XML report (parseable by CI tools)
- **`reports/ci_smoke/pytest.txt`** - Full pytest output
- **`reports/ci_smoke/env.txt`** - Environment snapshot (Python version, packages, git state)
- **`logs/`** - Any log files generated (if present)

**Retention**: 7 days

**Access**: GitHub Actions → Workflow run → Artifacts section

---

## Debugging Failures

### Local Debugging

```bash
# 1. Run smoke tests locally
make ci-smoke

# 2. If tests fail, check reports
cat reports/ci_smoke/pytest.txt

# 3. Run specific failing test with verbose output
pytest tests/smoke/test_imports_smoke.py::test_core_imports -vvs

# 4. Check environment snapshot
cat reports/ci_smoke/env.txt
```

### CI Debugging

1. **View workflow run**: GitHub → Actions → CI Smoke Fast Lane → [failing run]
2. **Download artifacts**: Scroll to bottom → Artifacts → `ci-smoke-failure-XXX`
3. **Check summary**: Workflow logs → "Display smoke test summary" step
4. **Inspect logs**:
   - `reports/ci_smoke/pytest.txt` - Full test output
   - `reports/ci_smoke/env.txt` - Python version, packages
5. **Reproduce locally**:
   ```bash
   # Check Python version from env.txt
   python3 --version

   # Install dependencies
   pip install -r requirements.txt
   pip install pytest

   # Run smoke tests
   make ci-smoke
   ```

### Common Failure Scenarios

#### 1. Import Error

**Symptom**: `test_imports_smoke.py` fails with `ImportError` or `ModuleNotFoundError`

**Cause**: Missing dependency or circular import

**Fix**:
```bash
# Check which import failed
pytest tests/smoke/test_imports_smoke.py -v

# Try importing manually
python3 -c "from src.core import environment"

# If missing dependency:
pip install <missing-package>
```

#### 2. Config Error

**Symptom**: `test_config_smoke.py` fails

**Cause**: Invalid `config.toml` or missing required section

**Fix**:
```bash
# Validate TOML syntax
python3 -c "import tomli; print(tomli.load(open('config.toml', 'rb')))"

# Check required sections
grep -E "^\[environment\]|^\[general\]|^\[live_risk\]" config.toml
```

#### 3. Gating Error

**Symptom**: `test_live_gating_smoke.py` fails

**Cause**: Live-gating not properly configured (safety issue!)

**Fix**:
```bash
# Check governance status
python3 -c "from src.governance.go_no_go import get_governance_status; print(get_governance_status('live_order_execution'))"
# Should print: locked

# Check environment default
python3 -c "from src.core.environment import create_default_environment; print(create_default_environment().environment.value)"
# Should print: paper
```

---

## Extending the Smoke Suite

### Adding a New Smoke Test

1. Create test file in `tests/smoke/`:
   ```python
   # tests/smoke/test_my_feature_smoke.py
   import pytest

   def test_my_feature_basics():
       """Quick sanity check for my feature."""
       from src.my_module import my_function
       result = my_function()
       assert result is not None
   ```

2. Keep tests **fast** (< 1 second each):
   - No external API calls
   - No heavy computation
   - No large file I/O
   - No database access

3. Make tests **deterministic**:
   - No random values (unless seeded)
   - No time-dependent assertions
   - No network-dependent behavior

4. Run locally to verify:
   ```bash
   pytest tests/smoke/test_my_feature_smoke.py -v
   make ci-smoke
   ```

### Guidelines for Smoke Tests

**DO**:
- ✅ Test basic imports
- ✅ Test config loading
- ✅ Test critical invariants (e.g., safe defaults)
- ✅ Use simple assertions
- ✅ Keep each test < 1 second

**DON'T**:
- ❌ Test complex business logic (use full tests)
- ❌ Make external API calls
- ❌ Run backtests or simulations
- ❌ Test edge cases (use full tests)
- ❌ Add slow tests (defeats the purpose)

---

## Metrics & Monitoring

### Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Total runtime (incl. setup) | < 2-3 min | ~1-2 min |
| Test execution time | < 10 sec | ~5 sec |
| Number of tests | 10-15 | 12 |
| Failure rate | < 5% | N/A (new) |

### Monitoring

**GitHub Actions**:
- Workflow run time (check "Duration" in workflow list)
- Artifact upload frequency (should be rare - only on failure)
- Test count in "Run CI Smoke Fast Lane" step

**Local**:
- Run `make ci-smoke` and check output
- Verify runtime is < 10 seconds (excluding setup)

---

## FAQ

### Q: Why a separate fast lane instead of using main CI?

**A**: Speed. The fast lane runs in parallel with main CI and fails fast (< 2-3 min) on critical issues. Main CI runs the full test suite which can take 10-30 minutes.

### Q: Why Linux-only?

**A**: Speed. Linux runners are fastest and cheapest. If multi-platform support is needed, add it to main CI, not the fast lane.

### Q: What if smoke tests pass but full tests fail?

**A**: That's expected. Smoke tests catch only **critical** issues (imports, config, gating). Full tests catch everything else.

### Q: Can I run smoke tests without pytest?

**A**: No, pytest is required. But you can run individual imports manually:
```bash
python3 -c "from src.core import environment"
```

### Q: How do I skip smoke tests locally?

**A**: Don't run `make ci-smoke`. The workflow always runs in CI, but you control local execution.

---

## Troubleshooting

### Issue: "make: *** No rule to make target 'ci-smoke'"

**Solution**: Run from repo root:
```bash
cd /path/to/Peak_Trade
make ci-smoke
```

### Issue: "pytest: command not found"

**Solution**: Install pytest:
```bash
pip install pytest
```

### Issue: Smoke tests fail with "ModuleNotFoundError"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Workflow times out (> 5 min)

**Solution**: Check if tests are hung (should complete in < 10 sec). Investigate slow tests:
```bash
pytest tests/smoke/ -v --durations=0
```

---

## Commands Reference

```bash
# Run smoke tests (local)
make ci-smoke

# Run smoke tests (script directly)
bash scripts/ci_smoke_fastlane.sh

# Run individual smoke test file
pytest tests/smoke/test_imports_smoke.py -v

# Run all smoke tests with pytest
pytest tests/smoke/ -v

# Check syntax only (no tests)
python3 -m compileall -q src

# View smoke test reports
cat reports/ci_smoke/pytest.txt
cat reports/ci_smoke/junit.xml
cat reports/ci_smoke/env.txt

# Clean smoke reports
rm -rf reports/ci_smoke/
```

---

## See Also

- [CI Workflow](.github/workflows/ci_smoke_fastlane.yml) - GitHub Actions workflow
- [Smoke Tests](../tests/smoke/) - Test files
- [Main CI](.github/workflows/ci.yml) - Full test suite
- [Test Health](./TEST_HEALTH_AUTOMATION_V0.md) - Test health monitoring

---

**End of Guide**
