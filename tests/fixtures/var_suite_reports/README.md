# VaR Suite Report Fixtures

This directory contains test fixtures for the VaR backtesting suite report comparison and regression detection system.

## Fixture Overview

### CI Green-Path Fixtures (Used by Automated CI Gates)

These fixtures contain **clean, passing** VaR backtest results with no regressions:

- **`run_baseline/`** - Reference baseline run (PASS, no regressions)
- **`run_candidate/`** - Candidate run for comparison (PASS, no regressions)
- **`run_pass_all/`** - Golden "all tests pass" dataset

**Purpose:** CI regression gates compare `run_baseline` vs `run_candidate` and expect **exit code 0** (no regressions detected).

**Workflow:** `.github/workflows/var_report_regression_gate.yml`

### Negative Testing Fixtures (For Regression Detection Tests)

These fixtures contain **intentional regressions** to verify that the regression detection system works correctly:

- **`run_known_regressions_baseline/`** - Clean baseline (PASS)
- **`run_known_regressions_candidate/`** - Degraded candidate (FAIL, 4 regressions)

**Purpose:** Test that `var_suite_compare_runs.py` correctly detects and reports regressions with **exit code 1**.

**Known Regressions in `run_known_regressions_candidate`:**
1. `overall_result`: PASS → FAIL (Severity: HIGH)
2. `basel_traffic_light`: GREEN → YELLOW (Severity: MEDIUM)
3. `christoffersen_cc`: PASS → FAIL (Severity: MEDIUM)
4. `christoffersen_ind`: PASS → FAIL (Severity: MEDIUM)

**Metrics:**
- Breaches: 5 → 8 (+3)
- Christoffersen CC p-value: 0.85 → 0.03 (-0.82)
- Christoffersen Ind p-value: 0.75 → 0.04 (-0.71)

## Usage

### CI Regression Gate (Automated)

```bash
# Expect: exit 0 (no regressions)
python scripts/risk/var_suite_compare_runs.py \
  --baseline tests/fixtures/var_suite_reports/run_baseline \
  --candidate tests/fixtures/var_suite_reports/run_candidate \
  --out reports/var_suite/ci_compare
```

### Negative Testing (Manual/Test Suite)

```bash
# Expect: exit 1 (4 regressions detected)
python scripts/risk/var_suite_compare_runs.py \
  --baseline tests/fixtures/var_suite_reports/run_known_regressions_baseline \
  --candidate tests/fixtures/var_suite_reports/run_known_regressions_candidate \
  --out reports/var_suite/negative_test
```

## Fixture Structure

Each fixture directory contains:

```
run_*/
├── suite_report.json    # Structured backtest results
├── suite_report.md      # Human-readable markdown report
└── suite_report.html    # HTML visualization (optional)
```

## Maintenance

- **Do NOT modify** `run_baseline` or `run_candidate` to contain regressions - CI gates will fail
- **Do NOT delete** `run_known_regressions_*` - they are required for negative testing
- **Update** fixtures when backtest schema changes (maintain consistency across all fixtures)

## Related Files

- Compare tool: `scripts/risk/var_suite_compare_runs.py`
- Index tool: `scripts/risk/var_suite_build_index.py`
- CI workflow: `.github/workflows/var_report_regression_gate.yml`
- Tests: `tests/risk/validation/test_report_compare.py`
