# VaR Backtest Suite – Quick Start Guide

**Phase:** 8C + 8D  
**Feature:** Suite Runner, Report Formatter, Index & Compare Tools  
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

⚠️ **Note:** `src/risk/validation/christoffersen.py` ist aktuell ein **Stub/Placeholder**. Die Christoffersen Tests (IND/CC) liefern dummy-Werte und sind noch nicht vollständig implementiert. Vollständige Implementation folgt in PR #422.

---

## Quick Start

### CLI Usage

```bash
python3 scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.95 \
  --output-dir results/var_suite/
```

**Output:**
- `results&#47;var_suite&#47;suite_report.json` — Maschinenlesbarer Report (JSON)
- `results&#47;var_suite&#47;suite_report.md` — Menschenlesbarer Report (Markdown)

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
python3 scripts/risk/run_var_backtest_suite.py \
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
python3 -m pytest tests/risk/validation/test_suite_golden.py -v

# Check: Same input → same output (across runs)
python3 scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.95 \
  --output-dir /tmp/run1/

python3 scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.95 \
  --output-dir /tmp/run2/

diff /tmp/run1/suite_report.json /tmp/run2/suite_report.json
# Should be identical (no diff)
```

---

## Phase 8D: Report Index & Run Comparison

**New in 8D:** Tools für Report-Navigation und Run-Vergleiche (audit-ready, deterministisch).

### Report Index Builder

Generiert `index.{json,md,html}` für alle Runs in einem Report-Root:

```bash
python3 scripts/risk/var_suite_build_index.py \
  --report-root results/var_suite/
```

**Output:**
- `results&#47;var_suite&#47;index.json` — Maschinenlesbarer Index
- `results&#47;var_suite&#47;index.md` — Markdown-Tabelle aller Runs
- `results&#47;var_suite&#47;index.html` — HTML-Dashboard (öffnen in Browser)

**Use Case:**
- Übersicht über alle historischen VaR-Runs
- Audit Trail (welche Runs existieren, wann erstellt, welches Ergebnis)
- Schneller Zugriff auf einzelne Run-Reports

**Beispiel HTML Output:**

Open `results&#47;var_suite&#47;index.html` in Browser:
- Tabelle mit allen Runs (run_id, observations, breaches, overall result)
- Clickable Links zu JSON/MD Reports
- Color-coded (PASS=grün, FAIL=rot)

### Run Comparison Tool

Vergleicht zwei Runs (baseline vs candidate) und identifiziert Regressions/Improvements:

```bash
python3 scripts/risk/var_suite_compare_runs.py \
  --baseline results/var_suite/run_20260101/ \
  --candidate results/var_suite/run_20260104/ \
  --out results/var_suite/compare/
```

**Output:**
- `results&#47;var_suite&#47;compare&#47;compare.json` — Strukturierter Diff
- `results&#47;var_suite&#47;compare&#47;compare.md` — Markdown-Report
- `results&#47;var_suite&#47;compare&#47;compare.html` — HTML-Dashboard

**Exit Code:**
- `0` = No regressions (candidate is equal or better)
- `1` = Regressions detected (see report)

**Use Case:**
- Model Update Validation: neues VaR-Modell vs altes Baseline
- CI/CD Integration: automatische Regression-Checks
- Audit: dokumentierte Änderungen zwischen Runs

**Beispiel compare.md:**

```markdown
# VaR Backtest Suite Run Comparison

## Summary
**Baseline:** run_20260101 → PASS
**Candidate:** run_20260104 → FAIL

## ⚠️ Regressions
- **overall_result**: PASS → FAIL (Severity: HIGH)
- **christoffersen_cc**: PASS → FAIL (Severity: MEDIUM)
- **basel_traffic_light**: GREEN → YELLOW (Severity: MEDIUM)

## Detailed Metrics
| Metric | Baseline | Candidate | Delta |
|--------|----------|-----------|-------|
| breaches | 5 | 8 | +3 |
| kupiec_pof_pvalue | 0.65 | 0.12 | -0.53 |
```

### Index + Compare Workflow (Typical)

**Step 1: Generate Runs**
```bash
# Baseline run
python3 scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns_2024.csv \
  --var-file data/var_baseline_2024.csv \
  --confidence 0.95 \
  --output-dir results/var_suite/run_baseline_2024/

# Candidate run (new model)
python3 scripts/risk/run_var_backtest_suite.py \
  --returns-file data/returns_2024.csv \
  --var-file data/var_candidate_2024.csv \
  --confidence 0.95 \
  --output-dir results/var_suite/run_candidate_2024/
```

**Step 2: Compare Runs**
```bash
python3 scripts/risk/var_suite_compare_runs.py \
  --baseline results/var_suite/run_baseline_2024/ \
  --candidate results/var_suite/run_candidate_2024/ \
  --out results/var_suite/compare_baseline_vs_candidate/

# Opens compare.html in browser
open results/var_suite/compare_baseline_vs_candidate/compare.html
```

**Step 3: Build Index**
```bash
python3 scripts/risk/var_suite_build_index.py \
  --report-root results/var_suite/

# Opens index.html in browser
open results/var_suite/index.html
```

### CLI Options

**Index Builder:**
```bash
# JSON only (no HTML)
python3 scripts/risk/var_suite_build_index.py \
  --report-root results/var_suite/ \
  --json-only

# Skip HTML
python3 scripts/risk/var_suite_build_index.py \
  --report-root results/var_suite/ \
  --no-html
```

**Compare Tool:**
```bash
# JSON only (CI-friendly)
python3 scripts/risk/var_suite_compare_runs.py \
  --baseline run_baseline/ \
  --candidate run_candidate/ \
  --out compare/ \
  --json-only

# Skip HTML
python3 scripts/risk/var_suite_compare_runs.py \
  --baseline run_baseline/ \
  --candidate run_candidate/ \
  --out compare/ \
  --no-html
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
- **Phase 8D Tests:** `tests/risk/validation/test_report_index.py`, `test_report_compare.py`

### Phase 8D Code
- **Report Index:** `src/risk/validation/report_index.py`
- **Report Compare:** `src/risk/validation/report_compare.py`
- **Index Builder CLI:** `scripts/risk/var_suite_build_index.py`
- **Compare Tool CLI:** `scripts/risk/var_suite_compare_runs.py`

---

**Last Updated:** 2026-01-04  
**Phase:** 8C + 8D  
**Status:** ✅ Production-Ready Human: continue
