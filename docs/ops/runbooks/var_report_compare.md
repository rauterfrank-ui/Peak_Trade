# Runbook: VaR Report Compare & Index Tools

**Version:** 1.0  
**Date:** 2026-01-04  
**Phase:** 8E/8F  
**Status:** Production-Ready

---

## 📋 Overview

Dieses Runbook beschreibt die Verwendung der VaR Report Compare und Index Tools für Operator und DevOps. Diese Tools wurden in Phase 8D implementiert und dienen zur **deterministischen Regression-Analyse** von VaR Backtest Suite Runs.

**Constraints:**
- ✅ Keine Änderungen an VaR/Risk-Logik
- ✅ Deterministisch: stabile Sortierung, stabile Outputs, Exit-Codes als Gate
- ✅ Keine neuen Dependencies; stdlib-only

---

## 🎯 Use Cases

### 1. Regression Tracking
Vergleiche zwei VaR Suite Runs (baseline vs. candidate) um Regressions/Improvements zu identifizieren.

### 2. CI/CD Integration
Automatische Regression Gates in GitHub Actions Workflows.

### 3. Audit & Compliance
Generiere Index-Übersichten über historische VaR Backtest Runs für Audits.

---

## 🔧 Tools

### Tool 1: `report_compare` — VaR Run Comparison

**Zweck:** Vergleicht zwei VaR Suite Runs und generiert Regression Reports.

**Entry Points:**
- **CLI Script:** `scripts/risk/var_suite_compare_runs.py`
- **Python Module:** `src.risk.validation.report_compare`

**Outputs:**
- `compare.json` — Strukturiertes JSON (für Parsing/CI)
- `compare.md` — Markdown Report (für Humans)
- `compare.html` — HTML Report (für Browser)

---

### Tool 2: `report_index` — VaR Report Index Generator

**Zweck:** Entdeckt alle VaR Runs in einem Report-Root und generiert eine Index-Übersicht.

**Entry Points:**
- **CLI Script:** `scripts/risk/var_suite_build_index.py`
- **Python Module:** `src.risk.validation.report_index`

**Outputs:**
- `index.json` — Strukturiertes JSON (für Parsing/CI)
- `index.md` — Markdown Report (für Humans)
- `index.html` — HTML Report (für Browser)

---

## 📖 Operator Guide

### Scenario 1: Manual Regression Check

**Situation:** Du möchtest zwei VaR Suite Runs manuell vergleichen.

**Steps:**

```bash
# 1. Lokalisiere die Run-Verzeichnisse
BASELINE="results/var_suite/run_20260101_120000"
CANDIDATE="results/var_suite/run_20260104_150000"

# 2. Führe den Compare aus
python scripts/risk/var_suite_compare_runs.py \
  --baseline "$BASELINE" \
  --candidate "$CANDIDATE" \
  --out results/var_suite/compare_20260104

# 3. Prüfe die Outputs
ls -lh results/var_suite/compare_20260104/
# Erwartete Dateien:
# - compare.json
# - compare.md
# - compare.html

# 4. Öffne den HTML Report im Browser
open results/var_suite/compare_20260104/compare.html

# 5. Prüfe Regressions in JSON (für Scripting)
python3 -c "
import json
with open('results/var_suite/compare_20260104/compare.json') as f:
    data = json.load(f)
    if data['regressions']:
        print('⚠️  REGRESSIONS FOUND:')
        for reg in data['regressions']:
            print(f\"  - {reg['type']}: {reg['message']} (severity: {reg['severity']})\")
        exit(1)
    else:
        print('✅ No regressions')
        exit(0)
"
```

**Exit Codes:**
- `0` — Compare erfolgreich (keine Script-Fehler)
- `≠0` — Compare fehlgeschlagen (Script-Error, z.B. Dateien nicht gefunden)

**WICHTIG:** Das Script selbst hat KEINEN "Regression Gate" Exit-Code. Du musst den JSON-Output parsen, um Regressions zu detektieren.

---

### Scenario 2: Generate Report Index

**Situation:** Du möchtest einen Index über alle VaR Runs in einem Report-Root generieren.

**Steps:**

```bash
# 1. Definiere Report-Root
REPORT_ROOT="results/var_suite"

# 2. Generiere Index
python scripts/risk/var_suite_build_index.py \
  --report-root "$REPORT_ROOT" \
  --formats json md html

# 3. Prüfe die Outputs (im Report-Root)
ls -lh "$REPORT_ROOT/"
# Erwartete Dateien:
# - index.json
# - index.md
# - index.html

# 4. Öffne den HTML Index
open "$REPORT_ROOT/index.html"

# 5. Prüfe Run-Count in JSON
python3 -c "
import json
with open('$REPORT_ROOT/index.json') as f:
    data = json.load(f)
    print(f\"Found {len(data['runs'])} VaR runs\")
    for run in data['runs']:
        result = run['metrics'].get('overall_result', 'UNKNOWN')
        print(f\"  - {run['run_id']}: {result}\")
"
```

**Exit Codes:**
- `0` — Index erfolgreich generiert
- `≠0` — Index fehlgeschlagen (z.B. Report-Root nicht gefunden)

---

### Scenario 3: CI Integration (GitHub Actions)

**Situation:** Du möchtest report_compare/index als CI Gate einbinden.

**Implementation:** Siehe `.github/workflows/var_report_regression_gate.yml`

**Key Steps:**

1. **Path Filters:** Nur bei Änderungen an `src/risk/validation/**`, `tests/risk/validation/**`, etc. triggern.

2. **Run Tests:**
   ```bash
   pytest tests/risk/validation/test_report_compare.py -v --tb=short
   pytest tests/risk/validation/test_report_index.py -v --tb=short
   ```

3. **Run Compare Gate:**
   ```bash
   python scripts/risk/var_suite_compare_runs.py \
     --baseline tests/fixtures/var_suite_reports/run_baseline \
     --candidate tests/fixtures/var_suite_reports/run_candidate \
     --out reports/var_suite/ci_compare

   # Verify outputs exist
   [ -f reports/var_suite/ci_compare/compare.json ] || exit 1
   [ -f reports/var_suite/ci_compare/compare.md ] || exit 1
   [ -f reports/var_suite/ci_compare/compare.html ] || exit 1
   ```

4. **Run Index Gate:**
   ```bash
   python scripts/risk/var_suite_build_index.py \
     --report-root tests/fixtures/var_suite_reports

   # Verify outputs exist
   [ -f tests/fixtures/var_suite_reports/index.json ] || exit 1

   # Verify deterministic ordering
   python3 -c "
   import json
   data = json.load(open('tests/fixtures/var_suite_reports/index.json'))
   run_ids = [r['run_id'] for r in data['runs']]
   assert run_ids == sorted(run_ids), 'Run IDs not sorted'
   "
   ```

5. **Upload Artifacts:**
   ```yaml
   - name: Upload comparison artifacts
     uses: actions/upload-artifact@v4
     if: always()
     with:
       name: var-report-compare-${{ github.run_number }}
       path: |
         reports/var_suite/ci_compare/compare.json
         reports/var_suite/ci_compare/compare.md
         reports/var_suite/ci_compare/compare.html
       retention-days: 30
   ```

**Expected CI Behavior:**
- ✅ Tests pass → Gate PASS
- ❌ Tests fail → Gate FAIL
- ❌ Compare/Index Script error → Gate FAIL
- ❌ Output files missing → Gate FAIL
- ❌ JSON invalid → Gate FAIL
- ❌ Non-deterministic ordering → Gate FAIL

---

## 🔍 Troubleshooting

### Problem: "ERROR: Baseline run not found"

**Ursache:** Baseline-Verzeichnis existiert nicht oder enthält keine `suite_report.json`.

**Lösung:**
```bash
# Prüfe, ob Baseline existiert
ls -lh "$BASELINE/"
# Erwartete Dateien:
# - suite_report.json
# - suite_report.md (optional)

# Falls nicht vorhanden: Korrekten Pfad verwenden
```

---

### Problem: "compare.json is not valid JSON"

**Ursache:** JSON-Generierung fehlgeschlagen (wahrscheinlich ein Bug).

**Lösung:**
```bash
# Prüfe JSON manuell
cat compare.json | python -m json.tool

# Falls Bug: Erstelle Issue mit Reproducer
```

---

### Problem: "Run IDs not sorted"

**Ursache:** `report_index` erzeugt nicht-deterministische Sortierung (Bug).

**Lösung:**
```bash
# Prüfe, ob Bug reproduzierbar ist
python scripts/risk/var_suite_build_index.py --report-root "$REPORT_ROOT"
python3 -c "
import json
data = json.load(open('$REPORT_ROOT/index.json'))
run_ids = [r['run_id'] for r in data['runs']]
print('Run IDs:', run_ids)
print('Sorted:', sorted(run_ids))
"

# Falls Bug: Erstelle Issue mit Reproducer
```

---

## 📊 Expected CI Behavior

### Exit Codes

| Command | Exit Code | Bedeutung |
|---------|-----------|-----------|
| `pytest tests/risk/validation/test_report_compare.py` | 0 | Tests PASS |
| | ≠0 | Tests FAIL |
| `python scripts/risk/var_suite_compare_runs.py ...` | 0 | Compare erfolgreich |
| | ≠0 | Compare fehlgeschlagen (Script-Error) |
| `python scripts/risk/var_suite_build_index.py ...` | 0 | Index erfolgreich |
| | ≠0 | Index fehlgeschlagen (Script-Error) |

### Gate Logic

```python
# Pseudo-Code für CI Gate Logic
def ci_gate():
    # 1. Run Tests
    if pytest_test_report_compare() != 0:
        return FAIL
    if pytest_test_report_index() != 0:
        return FAIL

    # 2. Run Compare
    if run_compare_script() != 0:
        return FAIL
    if not compare_outputs_exist():
        return FAIL
    if not compare_json_valid():
        return FAIL

    # 3. Run Index
    if run_index_script() != 0:
        return FAIL
    if not index_outputs_exist():
        return FAIL
    if not index_json_valid():
        return FAIL
    if not index_run_ids_sorted():
        return FAIL

    # All checks passed
    return PASS
```

---

## 🧪 Testing

### Run Tests Locally

```bash
# All report_compare tests
pytest tests/risk/validation/test_report_compare.py -v

# All report_index tests
pytest tests/risk/validation/test_report_index.py -v

# All validation tests
pytest tests/risk/validation/ -v

# With coverage
pytest tests/risk/validation/ --cov=src/risk/validation --cov-report=term-missing
```

### Smoke Test CLI Entry Points

```bash
# Compare script help
python scripts/risk/var_suite_compare_runs.py --help

# Index script help
python scripts/risk/var_suite_build_index.py --help

# Compare with fixtures
python scripts/risk/var_suite_compare_runs.py \
  --baseline tests/fixtures/var_suite_reports/run_baseline \
  --candidate tests/fixtures/var_suite_reports/run_candidate \
  --out /tmp/var_compare_test

# Index with fixtures
python scripts/risk/var_suite_build_index.py \
  --report-root tests/fixtures/var_suite_reports
```

---

## 📚 Related Documentation

- **Phase 8D Implementation:** `PHASE8D_FINAL_SUMMARY.md`
- **Phase 8E Implementation:** `PHASE8E_IMPLEMENTATION_SUMMARY.md`
- **Phase 8F Implementation:** `PHASE8F_IMPLEMENTATION_SUMMARY.md`
- **VaR Backtest Guide:** `docs/risk/VAR_BACKTEST_GUIDE.md`
- **Report Compare Module:** `src/risk/validation/report_compare.py`
- **Report Index Module:** `src/risk/validation/report_index.py`
- **CI Workflow:** `.github/workflows/var_report_regression_gate.yml`

---

## 🔐 Safety Notes

### ✅ Safe Operations
- ✅ Lesen von VaR Suite Reports
- ✅ Generieren von Comparison/Index Reports
- ✅ Parsing von JSON/Markdown/HTML
- ✅ Deterministische Sortierung und Formatting

### ❌ No Changes to Runtime
- ❌ KEINE Änderungen an VaR/Risk-Logik
- ❌ KEINE Änderungen an Execution Paths
- ❌ KEINE Änderungen an Runtime Trading Components
- ❌ KEINE neuen Dependencies (stdlib-only)

---

## 👤 Operator Checklists

### Before Running Compare

- [ ] Baseline run existiert und enthält `suite_report.json`
- [ ] Candidate run existiert und enthält `suite_report.json`
- [ ] Output-Verzeichnis ist schreibbar
- [ ] Genug Disk Space für HTML Reports

### Before Running Index

- [ ] Report-Root existiert und enthält `run_*` Subdirectories
- [ ] Report-Root ist schreibbar
- [ ] Genug Disk Space für HTML Index

### After Running Compare

- [ ] `compare.json` existiert und ist valid JSON
- [ ] `compare.md` existiert
- [ ] `compare.html` existiert und öffnet im Browser
- [ ] Regressions reviewed (falls vorhanden)

### After Running Index

- [ ] `index.json` existiert und ist valid JSON
- [ ] `index.md` existiert
- [ ] `index.html` existiert und öffnet im Browser
- [ ] Run IDs sind sortiert (deterministisch)

---

## 🆘 Support

**Questions?** Siehe:
- **Tests:** `tests/risk/validation/test_report_*.py`
- **Fixtures:** `tests/fixtures/var_suite_reports/`
- **Module Docs:** Docstrings in `src/risk/validation/`

**Issues?** Erstelle GitHub Issue mit:
- Reproducer (Commands + Inputs)
- Expected vs. Actual Output
- Error Messages / Stack Traces

---

**Version History:**
- **v1.0** (2026-01-04) — Initial version (Phase 8E/8F)
