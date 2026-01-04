# VaR Backtest Suite – Quick Start Guide

**Phase:** 8C  
**Feature:** Suite Runner & Report Formatter  
**Status:** ✅ Production-Ready  

---

## Overview

Die **VaR Backtest Suite** aggregiert alle VaR-Validierungstests in einem einzigen Lauf mit deterministischen, maschinenlesbaren (JSON) und menschenlesbaren (Markdown) Reports.

**Tests in Suite:**
1. **Kupiec POF Test** (Phase 8A) — Testet Breach-Rate
2. **Basel Traffic Light** (Phase 8A) — Regulatorische Klassifikation
3. **Christoffersen Independence Test** (Phase 8B) — Testet zeitliche Unabhängigkeit
4. **Christoffersen Conditional Coverage Test** (Phase 8B) — Kombinierter UC+IND Test

**Overall Result:** `PASS` wenn alle Tests grün, sonst `FAIL`.

---

## Quick Start

### CLI Usage

```bash
python scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.95 \
  --output-dir results/var_suite/
```

**Output:**
- `results/var_suite/suite_report.json` — Maschinenlesbarer Report (JSON)
- `results/var_suite/suite_report.md` — Menschenlesbarer Report (Markdown)

**Exit Code:**
- `0` = Suite PASSED (alle Tests grün)
- `1` = Suite FAILED (mindestens ein Test fehlgeschlagen)

---

## Python API

```python
import pandas as pd
from src.risk.validation import (
    run_var_backtest_suite,
    format_suite_result_json,
    format_suite_result_markdown,
)

# Load data
returns = pd.read_csv("data/returns.csv", index_col=0, parse_dates=True).squeeze()
var_series = pd.read_csv("data/var.csv", index_col=0, parse_dates=True).squeeze()

# Run suite
result = run_var_backtest_suite(
    returns=returns,
    var_series=var_series,
    confidence_level=0.95,
    significance=0.05,
)

# Check overall result
print(result.overall_result)  # "PASS" or "FAIL"

# Generate reports
json_report = format_suite_result_json(result)
markdown_report = format_suite_result_markdown(result)

# Save reports
with open("suite_report.json", "w") as f:
    f.write(json_report)
with open("suite_report.md", "w") as f:
    f.write(markdown_report)
```

---

## Report Structure

### JSON Report

```json
{
  "suite_metadata": {
    "breaches": 5,
    "confidence_level": 0.95,
    "observations": 100
  },
  "test_results": {
    "basel_traffic_light": {
      "result": "GREEN"
    },
    "christoffersen_cc": {
      "p_value": 0.456789,
      "result": "PASS"
    },
    "christoffersen_ind": {
      "p_value": 0.345678,
      "result": "PASS"
    },
    "kupiec_pof": {
      "p_value": 0.123456,
      "result": "PASS"
    }
  },
  "overall_result": "PASS"
}
```

**Key Properties:**
- **Deterministic:** Same input → same output (stable key order, fixed precision)
- **Precision:** P-values rounded to 6 decimals
- **Stable Keys:** Alphabetical within sections

### Markdown Report

```markdown
# VaR Backtest Suite Report

**Overall Result:** ✅ PASS

---

## Suite Metadata

- **Observations:** 100
- **Breaches:** 5
- **Confidence Level:** 95.00%

---

## Test Results

| Test | Result | Details |
|------|--------|---------|
| Kupiec POF | ✅ PASS | p-value: 0.123456 |
| Basel Traffic Light | 🟢 GREEN | Color: GREEN |
| Christoffersen IND | ✅ PASS | p-value: 0.345678 |
| Christoffersen CC | ✅ PASS | p-value: 0.456789 |

---

## Interpretation

**Summary:** All tests passed. VaR model appears well-calibrated.

- **Kupiec POF:** Breach rate statistically consistent with confidence level
- **Basel Traffic Light:** GREEN zone (acceptable breach count)
- **Christoffersen IND:** Breaches are temporally independent (no clustering)
- **Christoffersen CC:** Combined unconditional coverage + independence validated
```

---

## Interpreting Results

### Overall Result: PASS ✅

**Bedeutung:** VaR-Modell ist gut kalibriert.

- **Kupiec POF:** Breach-Rate passt statistisch zum Confidence Level
- **Basel Traffic Light:** GREEN = Akzeptable Breach-Anzahl
- **Christoffersen IND:** Breaches sind zeitlich unabhängig (kein Clustering)
- **Christoffersen CC:** Kombinierter Test bestanden

**Action:** VaR-Modell kann weiter verwendet werden. Monitoring fortsetzen.

### Overall Result: FAIL ❌

**Bedeutung:** Mindestens ein Test fehlgeschlagen → VaR-Modell überprüfen.

**Mögliche Ursachen:**

| Test Failed | Interpretation | Action |
|-------------|---------------|--------|
| **Kupiec POF** | Zu viele/wenige Breaches | VaR-Kalibrierung anpassen (zu konservativ/aggressiv) |
| **Basel Traffic Light YELLOW/RED** | Breach-Count über Threshold | Erhöhe VaR-Konservativität, Model Review |
| **Christoffersen IND** | Breaches clustern | Volatilitäts-Persistenz unterschätzt → EWMA/GARCH |
| **Christoffersen CC** | UC oder IND failed | Kombiniertes Problem (siehe Einzeltests) |

**Action:** Model Review, ggf. Alternative Methode (Historical → Parametric, EWMA, etc.)

---

## Input Data Format

### Returns File

```csv
date,return
2024-01-01,0.01
2024-01-02,-0.02
2024-01-03,0.015
...
```

**Requirements:**
- CSV with header
- Index column: date (parseable by pandas)
- Single column: return (daily returns)

### VaR File

```csv
date,var
2024-01-01,0.02
2024-01-02,0.02
2024-01-03,0.021
...
```

**Requirements:**
- CSV with header
- Index column: date (must match returns index)
- Single column: var (positive values = loss magnitude)
- **Index Alignment:** Must have identical index as returns

---

## Example: Fixture Run

```bash
# Run suite with fixtures
python scripts/risk/run_var_backtest_suite.py \
  --returns-file tests/fixtures/var/returns_100d.csv \
  --var-file tests/fixtures/var/var_95.csv \
  --confidence 0.95 \
  --output-dir /tmp/var_suite_test/ \
  --print-markdown

# Output:
# ✓ JSON report written to: /tmp/var_suite_test/suite_report.json
# ✓ Markdown report written to: /tmp/var_suite_test/suite_report.md
# ✅ Suite PASSED (all tests green)
```

---

## Regression Testing

Die Suite ist **deterministisch** und eignet sich für Regression Tests:

```bash
# Golden Test
pytest tests/risk/validation/test_suite_golden.py -v

# Check: Same input → same output (across runs)
python scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.95 \
  --output-dir /tmp/run1/

python scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.95 \
  --output-dir /tmp/run2/

diff /tmp/run1/suite_report.json /tmp/run2/suite_report.json
# Should be identical (no diff)
```

---

## Troubleshooting

### Error: "must have same length"

**Ursache:** Returns und VaR haben unterschiedliche Längen.

**Lösung:**
```python
print(f"Returns: {len(returns)}, VaR: {len(var_series)}")
# Align indices
common_index = returns.index.intersection(var_series.index)
returns = returns.loc[common_index]
var_series = var_series.loc[common_index]
```

### Error: "must have identical indices"

**Ursache:** Returns und VaR haben verschiedene Datums-Indizes.

**Lösung:**
```python
# Reindex var_series to match returns
var_series = var_series.reindex(returns.index)
```

### Warning: All tests FAIL

**Ursache:** VaR-Modell ist schlecht kalibriert ODER falsche Datenformatierung.

**Debug:**
```python
# Check breach count
breaches = (returns < -var_series).sum()
expected = len(returns) * (1 - confidence_level)
print(f"Breaches: {breaches}, Expected: {expected:.1f}")

# If breaches == 0 or breaches == len(returns): Data issue!
# If breaches >> expected: VaR zu aggressiv
# If breaches << expected: VaR zu konservativ
```

---

## References

### Documentation
- **Phase 8A:** Kupiec POF + Basel Traffic Light → `docs/risk/KUPIEC_POF_THEORY.md`
- **Phase 8B:** Christoffersen Tests → `docs/risk/CHRISTOFFERSEN_TESTS_GUIDE.md`
- **Phase 8C:** Suite Runner (this guide)

### Code
- **Suite Runner:** `src/risk/validation/suite_runner.py`
- **Report Formatter:** `src/risk/validation/report_formatter.py`
- **CLI Script:** `scripts/risk/run_var_backtest_suite.py`

### Tests
- **Unit Tests:** `tests/risk/validation/test_suite_runner.py`, `test_report_formatter.py`
- **Golden Tests:** `tests/risk/validation/test_suite_golden.py`

---

**Last Updated:** 2026-01-04  
**Phase:** 8C  
**Status:** ✅ Production-Ready Human: continue
