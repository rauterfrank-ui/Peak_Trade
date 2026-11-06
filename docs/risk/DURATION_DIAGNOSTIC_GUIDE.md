# Duration-Based Independence Diagnostic Guide


## Authority and epoch note

This guide preserves historical and component-level duration-diagnostic context. Duration diagnostics can support VaR / risk review, independence analysis, and model-quality discussions, but they are not, by themselves, current Master V2 approval, Doubleplay authority, First-Live readiness, operator authorization, a primary production rejection gate, or permission to route orders into any live capital path.

Duration diagnostics do not replace Christoffersen / Kupiec validation, current gate, evidence, and signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, or staged Execution Enablement. This note is docs-only and changes no runtime behavior.

**Phase 9A Implementation**  
**Status:** ✅ Optional Diagnostic (NOT a primary gate)  
**Purpose:** Supplementary evidence for VaR violation independence

---

## 🎯 Overview

Das **Duration-Based Independence Diagnostic** ist ein optionales, ergänzendes Werkzeug für VaR-Backtesting. Es analysiert die Zeit zwischen VaR-Überschreitungen (Durations) als zusätzlichen Hinweis auf Clustering oder Unabhängigkeit.

### ⚠️ WICHTIG: Nur Diagnostik, kein Gate

- **NICHT** als primäres Validierungs-Gate verwenden
- **NICHT** als alleinige Grundlage für Modell-Ablehnung
- **NUR** als ergänzende Evidenz neben Kupiec POF und Christoffersen Tests
- **NUR** für Research und explorative Analyse

### Wann verwenden?

✅ **Empfohlen:**
- Als zusätzliche Plausibilitätsprüfung nach Christoffersen Test
- Zur Visualisierung und Exploration von Violation-Mustern
- In Research-Reports zur erweiterten Dokumentation

❌ **NICHT empfohlen:**
- Als alleiniges Independence-Kriterium
- Als automatisches Rejection-Gate in Production
- Als Ersatz für Christoffersen Independence Test

---

## 📊 Theorie

### Unabhängigkeitsannahme

Wenn VaR-Violations unabhängig sind, sollten die **Zeiten zwischen Violations (Durations)** einer **Exponentialverteilung** folgen:

\[
T_i \sim \text{Exp}(\lambda = p)
\]

wobei:
- \( T_i \) = Duration zwischen Violation \( i \) und \( i+1 \)
- \( p \) = Erwartete Violation Rate (z.B. 0.01 für 99% VaR)
- \( \lambda = p \) = Rate-Parameter

**Eigenschaften der Exponentialverteilung:**
- Mean: \( E[T] = 1/p \)
- Std: \( \sigma[T] = 1/p \)
- Coefficient of Variation: \( CV = 1.0 \)

### Clustering-Detektion

**Clustering** (Violations treten gehäuft auf):
- → Durations kürzer als erwartet
- → Mean duration < Expected duration
- → Duration Ratio < 1.0

**Sparse Violations** (Violations zu weit auseinander):
- → Durations länger als erwartet
- → Mean duration > Expected duration
- → Duration Ratio > 1.0

---

## 🛠️ API Referenz

### Hauptfunktion

```python
from src.risk_layer.var_backtest import duration_independence_diagnostic

result = duration_independence_diagnostic(
    exceedances,                    # Boolean list/Series: True = Violation
    expected_rate=0.01,             # Erwartete Rate (z.B. 0.01 für 99% VaR)
    timestamps=None,                # Optional: DatetimeIndex für zeitbasierte Durations
    enable_exponential_test=False,  # Optional: Exponential-Test aktivieren
    significance_level=0.05,        # Signifikanz für exponential test
)
```

**Returns:** `DurationDiagnosticResult` mit:
- `n_exceedances`: Anzahl Violations
- `n_durations`: Anzahl Durations (n_exceedances - 1)
- `mean_duration`: Durchschnittliche Duration
- `expected_duration`: Erwartete Duration unter Unabhängigkeit (1/p)
- `duration_ratio`: Observed / Expected (< 1 → Clustering)
- `clustering_score`: Normalisierte Abweichung
- `notes`: Interpretationshilfe
- `exponential_test`: Optional exponential goodness-of-fit

### Duration Extraktion

```python
from src.risk_layer.var_backtest import extract_exceedance_durations

durations = extract_exceedance_durations(
    exceedances,      # Boolean list: True = Violation
    timestamps=None,  # Optional: Timestamps für zeitbasierte Durations
)
# Returns: List[float] mit Durations zwischen Violations
```

### Formatierung

```python
from src.risk_layer.var_backtest import format_duration_diagnostic

formatted_text = format_duration_diagnostic(result)
print(formatted_text)
```

---

## 📋 Beispiele

### Beispiel 1: Normale Violations (kein Clustering)

```python
import pandas as pd
from src.risk_layer.var_backtest import duration_independence_diagnostic

# 250 Beobachtungen, ~2.5 Violations erwartet (1% Rate)
# Violations gleichmäßig verteilt
exceedances = [False] * 100 + [True] + [False] * 100 + [True] + [False] * 48

result = duration_independence_diagnostic(
    exceedances,
    expected_rate=0.01,  # 99% VaR
)

print(result.duration_ratio)  # ~1.0 (gut)
print(result.is_suspicious())  # False
print(result.notes)
# → "✓ DIAGNOSTIC: Duration ratio within normal range [0.5, 1.5]"
```

### Beispiel 2: Clustering (Krisenperiode)

```python
# Violations gehäuft in kurzer Zeit
exceedances = [False] * 100 + [True, False, True, False, True] + [False] * 145

result = duration_independence_diagnostic(
    exceedances,
    expected_rate=0.01,
)

print(result.duration_ratio)  # << 1.0 (Clustering!)
# → 0.06 (Mean duration = 2, Expected = 33.3)

print(result.is_suspicious())  # True
print(result.notes)
# → "⚠️ DIAGNOSTIC: Duration ratio < 0.5 suggests potential clustering."
```

### Beispiel 3: Mit DatetimeIndex

```python
dates = pd.date_range("2024-01-01", periods=250, freq="D")
exceedances = pd.Series([...], index=dates)

result = duration_independence_diagnostic(
    exceedances,
    expected_rate=0.01,
    timestamps=dates,  # Durations in days
)

print(result.mean_duration)  # In Tagen
```

### Beispiel 4: Mit Exponential Test

```python
result = duration_independence_diagnostic(
    exceedances,
    expected_rate=0.01,
    enable_exponential_test=True,  # Aktiviere Goodness-of-Fit Test
)

if result.exponential_test:
    print(result.exponential_test.test_statistic)
    print(result.exponential_test.passed)
    print(result.exponential_test.notes)
```

---

## 📏 Interpretation Guidelines

### Duration Ratio

| Ratio | Interpretation | Action |
|-------|----------------|--------|
| < 0.5 | **Starkes Clustering** | ⚠️ Violations gehäuft → Check Christoffersen Test |
| 0.5 - 0.8 | Leichtes Clustering | 🔍 Investigate, aber nicht unbedingt Problem |
| 0.8 - 1.2 | **Normal** | ✅ Konsistent mit Unabhängigkeit |
| 1.2 - 1.5 | Leicht sparse | 🔍 Modell evtl. zu konservativ |
| > 1.5 | **Sehr sparse** | ⚠️ Violations zu weit auseinander → Check Kupiec Test |

### Clustering Score

| Score | Interpretation |
|-------|----------------|
| < 0.2 | Sehr geringe Abweichung |
| 0.2 - 0.5 | Moderate Abweichung |
| > 0.5 | Starke Abweichung |

### Recommended Workflow

```
1. Kupiec POF Test         → Prüft Frequenz (N/T ≈ p?)
2. Christoffersen Test     → Prüft Independence (Formal)
3. Duration Diagnostic     → Ergänzende Evidenz (Optional)
```

**Entscheidungslogik:**

```python
# ✅ RICHTIG: Duration Diagnostic als Supplement
if not christoffersen_result.passed:
    # Formal Independence test failed
    print("❌ Independence rejected by Christoffersen")

    # Check duration diagnostic for additional context
    duration_result = duration_independence_diagnostic(violations, expected_rate=0.01)
    if duration_result.is_suspicious():
        print("⚠️  Duration diagnostic confirms clustering")
    else:
        print("🤔 Duration diagnostic shows no strong clustering (investigate)")

# ❌ FALSCH: Duration Diagnostic als Gate
if duration_result.is_suspicious():
    halt_trading()  # NICHT EMPFOHLEN!
```

---

## 🧪 Exponential Goodness-of-Fit Test

**Optional:** Formaler Test ob Durations exponentialverteilt sind.

### Aktivierung

```python
result = duration_independence_diagnostic(
    exceedances,
    expected_rate=0.01,
    enable_exponential_test=True,  # Aktiviere Test
    significance_level=0.05,
)

if result.exponential_test:
    print(f"Test: {result.exponential_test.test_name}")
    print(f"Statistic: {result.exponential_test.test_statistic:.4f}")
    print(f"Result: {result.exponential_test.passed}")
```

### Implementation Details

- **Test:** Anderson-Darling-style statistic (simplified)
- **Distribution:** Exponential mit Rate = expected_rate
- **Dependencies:** Stdlib-only (kein scipy)
- **Limitation:** Approximation ohne scipy (siehe Notes im Result)

### Wann verwenden?

- Nur wenn >= 3 Durations vorhanden
- Als zusätzliche formale Prüfung
- NICHT als primäres Gate

---

## ⚙️ Integration mit Existing Tests

### Verwendung mit VaRBacktestRunner

```python
from src.risk_layer.var_backtest import (
    VaRBacktestRunner,
    duration_independence_diagnostic,
)

# Standard VaR Backtest
runner = VaRBacktestRunner(confidence_level=0.99)
backtest_result = runner.run(returns, var_estimates, symbol="BTC-EUR")

# Christoffersen Independence Test
from src.risk_layer.var_backtest import christoffersen_independence_test
violations = backtest_result.violations.violations.tolist()
christoffersen_result = christoffersen_independence_test(violations)

# Optional: Duration Diagnostic
duration_result = duration_independence_diagnostic(
    violations,
    expected_rate=0.01,
    timestamps=backtest_result.violations.dates,
)

# Report
print(f"Kupiec POF: {backtest_result.kupiec.is_valid}")
print(f"Christoffersen IND: {christoffersen_result.passed}")
print(f"Duration Ratio: {duration_result.duration_ratio:.4f}")
```

### Verwendung mit Suite Report

```python
from src.risk_layer.var_backtest import (
    run_full_var_backtest,
    duration_independence_diagnostic,
)

# Run full suite (Kupiec + Christoffersen + Traffic Light)
suite_results = run_full_var_backtest(violations, alpha=0.01)

# Add duration diagnostic
duration_result = duration_independence_diagnostic(
    violations,
    expected_rate=0.01,
)

# Custom report
report = f"""
VaR Backtest Suite Report
=========================

Kupiec POF:       {'PASS' if suite_results['kupiec'].is_valid else 'FAIL'}
Christoffersen:   {'PASS' if suite_results['independence'].passed else 'FAIL'}

Duration Diagnostic (optional):
  Mean Duration:    {duration_result.mean_duration:.2f}
  Expected:         {duration_result.expected_duration:.2f}
  Ratio:            {duration_result.duration_ratio:.4f}
  Assessment:       {duration_result.notes}
"""

print(report)
```

---

## 🚨 Limitations & Caveats

### 1. Not a Formal Test

- Duration Diagnostic ist **kein formaler Hypothesentest**
- Thresholds (0.5, 1.5) sind **heuristische Richtwerte**
- Für formales Testing: **Christoffersen Independence Test**

### 2. Small Sample Issues

- Benötigt >= 2 Violations für Durations
- Bei < 10 Durations: **sehr unsichere Schätzungen**
- Empfohlen: >= 20 Durations für robuste Diagnostik

### 3. Exponential Test Limitations

- Stdlib-Implementation ist **Approximation**
- Für exakte Tests: `scipy.stats.anderson` oder `scipy.stats.kstest`
- p-values werden **nicht** berechnet (nur Test-Statistic)

### 4. Time-Series Dependencies

- Duration-Test ignoriert **multi-step dependencies**
- Christoffersen Test mit Transition-Matrix ist **robuster**
- Duration-Test als **Supplement**, nicht Ersatz

---

## 📚 References

1. **Kupiec, P. (1995):** Techniques for Verifying the Accuracy of Risk Measurement Models.
   *Journal of Derivatives*, 2(2), 73-84.

2. **Christoffersen, P. F. (1998):** Evaluating Interval Forecasts.
   *International Economic Review*, 39(4), 841-862.

3. **Haas, M. (2005):** Improved Duration-Based Backtesting of Value-at-Risk.
   *Journal of Risk*, 8(2), 17-38.

4. **Basel Committee (2006):** International Convergence of Capital Measurement and Capital Standards.
   *Basel II Framework*.

---

## 🔧 Developer Notes

### File Locations

```
src/risk_layer/var_backtest/
├── duration_diagnostics.py      # ⭐ Phase 9A Implementation
├── kupiec_pof.py                # Kupiec POF Test
├── christoffersen_tests.py      # Christoffersen Independence/CC
├── var_backtest_runner.py       # Backtest Orchestration
└── __init__.py                  # Public API exports

tests/risk_layer/var_backtest/
└── test_duration_diagnostics.py # ⭐ Phase 9A Tests
```

### API Exports

```python
from src.risk_layer.var_backtest import (
    # Phase 9A: Duration Diagnostic
    DurationDiagnosticResult,
    ExponentialTestResult,
    extract_exceedance_durations,
    duration_independence_diagnostic,
    format_duration_diagnostic,
)
```

### Dependencies

- **Stdlib only:** `math`, `dataclasses`, `typing`
- **Optional:** `pandas` (für DatetimeIndex support)
- **NO scipy** (by design für Phase 9A)

---

## ✅ Testing & Validation

### Test Coverage

```bash
# Run Duration Diagnostic Tests
python3 -m pytest tests/risk_layer/var_backtest/test_duration_diagnostics.py -v

# Expected: ~30 tests, all passing
```

### Test Scenarios

- ✅ Basic duration extraction
- ✅ Duration ordering and temporal consistency
- ✅ Clustered violations (ratio < 0.5)
- ✅ Sparse violations (ratio > 1.5)
- ✅ DatetimeIndex support
- ✅ Edge cases (0, 1, 2 exceedances)
- ✅ Exponential goodness-of-fit test

---

## 🎯 Summary

**Phase 9A Duration-Based Independence Diagnostic:**

✅ **Was es ist:**
- Optional diagnostic tool
- Supplementary evidence für independence
- Stdlib-only implementation

✅ **Was es tut:**
- Extrahiert Durations zwischen Violations
- Berechnet Duration Ratio (observed/expected)
- Optional: Exponential goodness-of-fit test

❌ **Was es NICHT ist:**
- KEIN primäres Validierungs-Gate
- KEIN Ersatz für Christoffersen Test
- KEIN formaler Hypothesentest

**Empfohlene Verwendung:**
1. Kupiec POF → Frequenz prüfen
2. Christoffersen → Independence formal testen
3. Duration Diagnostic → Zusätzliche Evidenz (optional)

**Fragen?** Siehe `src/risk_layer/var_backtest/duration_diagnostics.py` für Implementation Details.
