# CI Pipeline Documentation

## Overview

Peak_Trade uses GitHub Actions for continuous integration. The primary workflow is `.github/workflows/ci.yml`.

## CI: RL v0.1 Fast Lane (Smoke)

### Dual Execution Strategy

We execute the RL v0.1 Smoke-Test **twice** in the CI pipeline:

1. **Fast Lane** (direct after dependency install, Linux-only)
   - Step: `Smoke: RL v0.1 Contract Test`
   - Command: `pytest -q tests/test_rl_v0_1_smoke.py`
   - Purpose: Quick fail-fast for RL contract violations
   - Runs before full test suite for early detection

2. **Full Suite** (later in regular pytest run)
   - Step: `Run tests`
   - Command: `pytest tests/ -v --tb=short`
   - Purpose: Additional safeguard against integration/ordering effects

### Artifact Upload Strategy

RL validation reports are uploaded **only on failure** of either:
- `Smoke: RL v0.1 Contract Test` step (id: `rl_v0_1_smoke`), OR
- `Validate RL v0.1 Contract` step (id: `rl_v0_1_contract`)

Upload paths:
- `reports/rl/**/*`
- `reports/rl_v0_1/**/*`
- `logs/rl/**/*`

Retention: 7 days

### Test Execution Order

1. Checkout
2. Set up Python (matrix: 3.9, 3.10, 3.11)
3. Cache pip
4. Install dependencies
5. **Smoke: RL v0.1 Contract Test** ← Fast Lane
6. **Validate RL v0.1 Contract** ← Bash script validation
7. **Upload RL validation reports on failure** ← Conditional artifact upload
8. Run tests (full suite)
9. Run tests with coverage (Python 3.11 only)

### Notes

- All RL validation steps run **Linux-only** (`runner.os == 'Linux'`)
- Smoke test skips gracefully if validation script doesn't exist yet
- Fast Lane provides early visibility into contract violations
- Full suite execution provides defense against test ordering bugs

### Local Validation

Local: `make rl-v0-1-validate` (or `./scripts/validate_rl_v0_1.sh`)

Reports:
- JSON: `reports/rl_v0_1/validate_rl_v0_1.json`
- Log: `reports/rl_v0_1/validate_rl_v0_1.log`

Expected outcomes:
- **SB3 not installed**: exit 0, status `"skipped"` (per v0.1 spec)
- **SB3 installed + tests pass**: exit 0, status `"passed"`
- **Tests fail**: exit 1, status `"failure"` with `smoke_rc`/`extra_rc`

### CI Failure Triage

When RL validation steps fail in CI:

1. **Check CI step logs** for immediate failure reason
   - Fast Lane smoke test (step 5)
   - Bash contract validation (step 6)

2. **Download artifacts** (7-day retention)
   - Go to failed workflow run → "Artifacts" section
   - Download: `rl-validation-reports-Linux-<python-version>`
   - Contains: `reports/rl_v0_1/validate_rl_v0_1.{json,log}`

3. **Parse JSON report** for structured failure info
   ```bash
   jq . reports/rl_v0_1/validate_rl_v0_1.json
   ```
   - `status`: "failure" (or "skipped"/"passed")
   - `reason`: failure category (e.g., "pytest_failed", "missing_smoke_test")
   - `smoke_rc`/`extra_rc`: pytest exit codes (if reason="pytest_failed")
   - `ts`: failure timestamp
   - `log`: path to detailed log

4. **Common failure causes**
   - **Missing SB3 but test tried to import**: v0.1 allows SB3-optional; script should skip gracefully
   - **Contract test regression**: RL API changed; review test expectations
   - **Flaky test**: rerun CI; if persistent, investigate test stability
   - **Script not executable**: check `chmod +x scripts/validate_rl_v0_1.sh`

5. **Reproduce locally**
   ```bash
   make rl-v0-1-validate
   cat reports/rl_v0_1/validate_rl_v0_1.json
   cat reports/rl_v0_1/validate_rl_v0_1.log
   ```

6. **If artifacts missing**
   - Check workflow upload condition: `steps.rl_v0_1_smoke.outcome == 'failure' || steps.rl_v0_1_contract.outcome == 'failure'`
   - Artifacts only upload on step failure (not pass/skip)
