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
