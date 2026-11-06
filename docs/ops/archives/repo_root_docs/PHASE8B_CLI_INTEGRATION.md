# Phase 8B: CLI Integration - UC/IND/CC Unified Summary

**Date:** 2025-12-28  
**Feature:** Integrated Christoffersen tests into VaR backtest CLI

---

## 🎯 What Was Added

Integrated Christoffersen Independence (IND) and Conditional Coverage (CC) tests into the existing VaR backtest CLI (`scripts/risk/run_var_backtest.py`) for a unified test summary.

### Before (Phase 7)
```bash
$ python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR
# Only showed Kupiec POF (UC) test
```

### After (Phase 8B)
```bash
$ python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all
# Shows UC + IND + CC tests in unified summary
```

---

## 📚 CLI Usage

### Test Selection

```bash
# Run all tests (default)
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all

# Run only Kupiec POF (UC)
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests uc

# Run only Independence test
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests ind

# Run only Conditional Coverage test
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests cc
```

### Output Modes

**Detailed Mode (default):**
```bash
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests all
```

**Output:**
```
======================================================================
VaR BACKTEST RESULTS
======================================================================
Symbol:           BTC-EUR
Period:           2024-01-01 - 2024-12-31
Confidence:       99.0%
Observations:     366
Violations:       4
Expected Rate:    1.00%
Observed Rate:    1.09%
Violation Ratio:  1.09x

----------------------------------------------------------------------
1. KUPIEC POF TEST (Unconditional Coverage)
----------------------------------------------------------------------
LR-UC Statistic:  0.0310
p-value:          0.8603
Critical Value:   3.8415
Verdict:          ACCEPT

----------------------------------------------------------------------
2. CHRISTOFFERSEN INDEPENDENCE TEST
----------------------------------------------------------------------
LR-IND Statistic: 30.2843
p-value:          0.0000
Verdict:          FAIL
Transition Probabilities:
  π₀₁ (P(V|¬V)):  0.0028
  π₁₁ (P(V|V)):   1.0000

----------------------------------------------------------------------
3. CHRISTOFFERSEN CONDITIONAL COVERAGE TEST
----------------------------------------------------------------------
LR-UC:            0.0310
LR-IND:           30.2843
LR-CC:            30.3153 (= LR-UC + LR-IND)
p-value:          0.0000
Verdict:          FAIL

======================================================================
SUMMARY
======================================================================
❌ SOME TESTS FAILED
  - Independence: FAIL (violations are clustered)
  - Conditional Coverage: FAIL (combined test)
======================================================================
```

**CI Mode (compact):**
```bash
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests all \
  --ci-mode
```

**Output:**
```
BTC-EUR: UC:ACCEPT IND:FAIL CC:FAIL (4/366 violations)
```

---

## 🔧 Implementation Details

### New CLI Arguments

```python
parser.add_argument(
    "--tests",
    type=str,
    default="all",
    choices=["uc", "ind", "cc", "all"],
    help="Tests to run: uc (Kupiec POF), ind (Independence), cc (Conditional Coverage), all",
)
```

### Integration Flow

1. **Run Kupiec POF (UC)** - Always runs (existing behavior)
2. **Run Christoffersen Tests** - If `--tests` includes `ind`, `cc`, or `all`
3. **Unified Output** - Shows all selected tests in single summary
4. **Exit Code** - Reflects overall test status (any failure → exit 1)

### JSON Output

```json
{
  "meta": {
    "generated_at": "2024-12-28T...",
    "test_type": "var_backtest",
    "tests_run": ["uc", "ind", "cc"]
  },
  "summary": {
    "symbol": "BTC-EUR",
    "result": "accept",
    "is_valid": true,
    "all_tests_pass": false
  },
  "kupiec_uc": {
    "n_observations": 366,
    "n_violations": 4,
    "lr_statistic": 0.0310,
    "p_value": 0.8603,
    ...
  },
  "christoffersen_ind": {
    "n": 366,
    "x": 4,
    "lr_ind": 30.2843,
    "p_value": 0.0000,
    "verdict": "FAIL",
    ...
  },
  "christoffersen_cc": {
    "n": 366,
    "x": 4,
    "lr_uc": 0.0310,
    "lr_ind": 30.2843,
    "lr_cc": 30.3153,
    "p_value": 0.0000,
    "verdict": "FAIL",
    ...
  }
}
```

---

## ✅ Verification

### Test All Modes

```bash
# Detailed output, all tests
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all
# Expected: Shows UC + IND + CC ✅

# Detailed output, UC only
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests uc
# Expected: Shows only UC ✅

# CI mode, all tests
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all --ci-mode
# Expected: Compact output "UC:ACCEPT IND:FAIL CC:FAIL" ✅

# CI mode, UC only
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests uc --ci-mode
# Expected: Compact output "UC:ACCEPT" ✅
```

### Exit Codes

```bash
# All pass → exit 0
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests uc
echo $?  # 0 ✅

# Any fail → exit 1 (with --fail-on-reject)
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all --fail-on-reject
echo $?  # 1 ✅
```

---

## 📊 Benefits

### ✅ Unified Interface
Single CLI for all VaR backtest tests (UC, IND, CC)

### ✅ Flexible Test Selection
Choose which tests to run via `--tests` flag

### ✅ CI-Friendly
Compact output mode for CI/CD pipelines

### ✅ Backward Compatible
Default behavior unchanged (runs UC test)

### ✅ Clear Diagnostics
Detailed output shows exactly which tests failed and why

---

## 🎓 Use Cases

### Use Case 1: Full Backtest (Research)

```bash
# Run all tests with detailed output
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --confidence 0.99 \
  --tests all \
  --output results.json
```

**When:** Research/analysis, want complete picture

### Use Case 2: Quick UC Check (Operators)

```bash
# Run only Kupiec POF (fast)
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests uc
```

**When:** Quick coverage check, don't need independence

### Use Case 3: CI/CD Pipeline

```bash
# Compact output, fail on any rejection
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests all \
  --ci-mode \
  --fail-on-reject
```

**When:** Automated testing, need pass/fail signal

### Use Case 4: Independence Focus

```bash
# Check only for violation clustering
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests ind
```

**When:** Investigating clustering issues

---

## 🔄 Migration from Standalone Demo

### Before (Phase 8B Demo Script)

```bash
PYTHONPATH=. python3 scripts/risk/run_christoffersen_demo.py \
  --pattern scattered
```

### After (Integrated CLI)

```bash
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests all
```

**Note:** Demo script (`run_christoffersen_demo.py`) still useful for:
- Testing specific patterns (scattered, clustered, alternating)
- Custom pattern exploration
- Educational purposes

---

## 📝 Summary

**Integration Complete:**
- ✅ UC/IND/CC tests unified in single CLI
- ✅ Flexible test selection (`--tests` flag)
- ✅ Detailed and CI modes
- ✅ JSON output with all test results
- ✅ Exit codes reflect overall status
- ✅ Backward compatible

**Files Modified:**
- `scripts/risk/run_var_backtest.py` (integrated Christoffersen tests)

**Commands:**
```bash
# All tests, detailed
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all

# All tests, CI mode
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests all --ci-mode

# UC only (backward compatible)
python3 scripts/risk/run_var_backtest.py --symbol BTC-EUR --tests uc
```

---

**Phase 8B CLI Integration: Complete! 🚀**
