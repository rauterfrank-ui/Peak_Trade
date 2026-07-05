# Phase 8E/8F – Expected CI Behavior

**Version:** 1.0  
**Date:** 2026-01-04  
**Workflow:** `.github/workflows/var_report_regression_gate.yml`

---

## 📊 Exit Codes

### Commands

| Command | Success | Failure | Notes |
|---------|---------|---------|-------|
| `pytest tests&#47;risk&#47;validation&#47;test_report_compare.py` | 0 | ≠0 | 12 tests must pass |
| `pytest tests&#47;risk&#47;validation&#47;test_report_index.py` | 0 | ≠0 | 10 tests must pass |
| `python3 scripts/risk/var_suite_compare_runs.py ...` | 0 | ≠0 | Script execution (warns if regressions found) |
| `python3 scripts/risk/var_suite_build_index.py ...` | 0 | ≠0 | Script execution |
| Verify compare outputs exist | 0 | 1 | Check for `compare.{json,md,html}` |
| Verify index outputs exist | 0 | 1 | Check for `index.{json,md,html}` |
| Verify JSON validity | 0 | 1 | `json.load()` must succeed |
| Verify deterministic sorting | 0 | 1 | Run IDs must be sorted alphabetically |

---

## 🚦 Gate Logic

```python
def ci_gate_logic():
    """Pseudo-code for CI gate decision."""

    # Step 1: Run Tests
    if pytest_report_compare() != 0:
        return FAIL  # Exit 1

    if pytest_report_index() != 0:
        return FAIL  # Exit 1

    # Step 2: Run Compare (with fixtures)
    if run_compare_script() != 0:
        return FAIL  # Exit 1

    if not compare_outputs_exist():
        return FAIL  # Exit 1

    if not compare_json_valid():
        return FAIL  # Exit 1

    # Step 3: Run Index (with fixtures)
    if run_index_script() != 0:
        return FAIL  # Exit 1

    if not index_outputs_exist():
        return FAIL  # Exit 1

    if not index_json_valid():
        return FAIL  # Exit 1

    if not index_run_ids_sorted():
        return FAIL  # Exit 1

    # Step 4: All checks passed
    return PASS  # Exit 0
```

---

## ✅ Success Criteria

Gate **PASSES** when:

1. ✅ All `test_report_compare.py` tests pass (12/12)
2. ✅ All `test_report_index.py` tests pass (10/10)
3. ✅ Compare script executes without errors
4. ✅ Compare outputs exist: `compare.{json,md,html}`
5. ✅ `compare.json` is valid JSON
6. ✅ Index script executes without errors
7. ✅ Index outputs exist: `index.{json,md,html}`
8. ✅ `index.json` is valid JSON
9. ✅ Run IDs in `index.json` are sorted alphabetically (deterministic)
10. ✅ CLI smoke tests pass (help commands)

**Result:** Gate exits with code **0**

---

## ❌ Failure Scenarios

Gate **FAILS** when:

### Scenario 1: Test Failures
- ❌ Any test in `test_report_compare.py` fails
- ❌ Any test in `test_report_index.py` fails
- **Exit Code:** ≠0 from pytest
- **CI Status:** ❌ Failed

### Scenario 2: Script Errors
- ❌ `var_suite_compare_runs.py` exits with error (e.g., baseline not found)
- ❌ `var_suite_build_index.py` exits with error (e.g., report-root not found)
- **Exit Code:** ≠0 from script
- **CI Status:** ❌ Failed

### Scenario 3: Output Missing
- ❌ `compare.json` not created
- ❌ `compare.md` not created
- ❌ `compare.html` not created
- ❌ `index.json` not created
- ❌ `index.md` not created
- ❌ `index.html` not created
- **Exit Code:** 1 from verification step
- **CI Status:** ❌ Failed

### Scenario 4: Invalid JSON
- ❌ `compare.json` is not valid JSON (syntax error)
- ❌ `index.json` is not valid JSON (syntax error)
- **Exit Code:** 1 from `python3 -c "import json; json.load(...)"`
- **CI Status:** ❌ Failed

### Scenario 5: Non-Deterministic Output
- ❌ Run IDs in `index.json` are not sorted alphabetically
- **Exit Code:** 1 from sorting verification
- **CI Status:** ❌ Failed

### Scenario 6: CLI Smoke Test Failure
- ❌ `var_suite_compare_runs.py --help` fails
- ❌ `var_suite_build_index.py --help` fails
- **Exit Code:** ≠0 from CLI command
- **CI Status:** ❌ Failed

---

## 🔍 Debugging Failed Gates

### Check 1: Test Logs

```bash
# View test output in CI logs
# Look for:
# - "FAILED tests/risk/validation/test_report_compare.py::test_name"
# - "AssertionError: ..."
# - "FileNotFoundError: ..."
```

### Check 2: Script Output

```bash
# View script output in CI logs
# Look for:
# - "ERROR: Baseline run not found"
# - "ERROR: compare.json not generated"
# - Traceback
```

### Check 3: Verification Logs

```bash
# View verification output in CI logs
# Look for:
# - "❌ ERROR: compare.json not generated"
# - "Traceback (most recent call last):"
# - "AssertionError: Run IDs not sorted"
```

### Check 4: Artifacts

```bash
# Download artifacts from failed run
# - var-report-compare-<run_number>.zip
# - Contains: compare.json, compare.md, compare.html
# - Inspect for anomalies
```

---

## 🎯 Expected Outputs

### Compare Outputs

```
reports/var_suite/ci_compare/
├── compare.json      (1-2 KB, valid JSON)
├── compare.md        (500-1000 bytes, markdown)
└── compare.html      (4-5 KB, HTML with CSS)
```

### Index Outputs

```
tests/fixtures/var_suite_reports/
├── index.json        (1-2 KB, valid JSON)
├── index.md          (500-1000 bytes, markdown)
└── index.html        (4-5 KB, HTML with CSS)
```

---

## 📈 Performance Expectations

| Step | Expected Duration | Timeout |
|------|-------------------|---------|
| Checkout | ~5s | 1 min |
| Setup Python | ~10s | 2 min |
| Install dependencies | ~30s | 5 min |
| Test `report_compare` | ~2s | 1 min |
| Test `report_index` | ~1s | 1 min |
| Compare gate | ~1s | 1 min |
| Index gate | ~1s | 1 min |
| Upload artifacts | ~5s | 2 min |
| **Total** | **~55s** | **10 min** |

---

## 🔔 Notification Strategy

### On Success
- ✅ Green checkmark in PR
- ✅ No notifications
- ✅ Artifacts available for download (30 days)

### On Failure
- ❌ Red X in PR
- ❌ Email notification to PR author
- ❌ Comment on PR with failure reason (optional)
- ❌ Artifacts available for debugging

---

## 🛡️ Safety Guarantees

### What This Gate Validates

✅ **Correctness:**
- ✅ report_compare logic (12 tests)
- ✅ report_index logic (10 tests)
- ✅ CLI entry points (smoke tests)
- ✅ Deterministic output (sorting, formatting)

✅ **Compatibility:**
- ✅ Fixtures remain valid
- ✅ JSON schema stability
- ✅ Output file generation

✅ **Regression Detection:**
- ✅ Changes that break tests → Gate FAILS
- ✅ Changes that break CLI → Gate FAILS
- ✅ Changes that break determinism → Gate FAILS

### What This Gate Does NOT Validate

❌ **Out of Scope:**
- ❌ VaR calculation correctness (separate tests)
- ❌ Risk validation logic (separate tests)
- ❌ Live trading behavior (not applicable)
- ❌ Performance benchmarks (not implemented)
- ❌ Semantic regressions in reports (requires human review)

---

## 📝 Example CI Run

### Successful Run

```
✅ Checkout repository
✅ Set up Python 3.11
✅ Install dependencies
✅ Run report_compare tests (12 passed)
✅ Run report_index tests (10 passed)
✅ Run deterministic compare gate
   ✓ All comparison files generated successfully
   ✓ compare.json is valid JSON
✅ Run deterministic index gate
   ✓ All index files generated successfully
   ✓ index.json is valid JSON
   ✓ Run IDs are deterministically sorted
   ✓ Cleaned up generated index files
✅ Upload comparison artifacts
✅ Smoke: var_suite_compare_runs.py --help
✅ Smoke: var_suite_build_index.py --help
✅ VaR Report Gate Summary
   ✅ Gate PASSED
```

**Exit Code:** 0  
**CI Status:** ✅ Passed

---

### Failed Run (Example: Test Failure)

```
✅ Checkout repository
✅ Set up Python 3.11
✅ Install dependencies
❌ Run report_compare tests
   FAILED tests/risk/validation/test_report_compare.py::test_deterministic_output
   AssertionError: Output not deterministic
❌ VaR Report Gate Summary
   ❌ Gate FAILED
```

**Exit Code:** 1  
**CI Status:** ❌ Failed

---

## 🔗 Related

- **Workflow:** `.github/workflows/var_report_regression_gate.yml`
- **Runbook:** `docs/ops/runbooks/var_report_compare.md`
- **PR:** `PHASE8E_8F_CI_INTEGRATION_PR.md`
- **Tests:** `tests&#47;risk&#47;validation&#47;test_report_*.py`

---

**Version History:**
- **v1.0** (2026-01-04) — Initial version
