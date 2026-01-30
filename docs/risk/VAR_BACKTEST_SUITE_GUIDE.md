# VaR Backtest Suite – Operator Guide

**Phases 9A/9B/10** · **Status:** ✅ Live on main

---

## Zweck

Die **VaR Backtest Suite** erweitert das bestehende VaR-Validierungs-Framework (Kupiec POF + Christoffersen Tests + Basel Traffic Light) um zwei neue **optionale Diagnostics**:

1. **Duration-Based Independence Diagnostic (Phase 9A)**  
   Prüft, ob VaR-Verletzungen zeitlich geclustert auftreten (Hinweis auf Modellschwächen)

2. **Rolling-Window Evaluation (Phase 9B)**  
   Führt Backtest-Tests über mehrere überlappende/nicht-überlappende Zeitfenster aus, um Modell-Stabilität über Zeit zu bewerten

3. **Operator Snapshot Runner (Phase 10)**  
   Single-Command CLI-Tool für schnelle Backtest-Snapshots (mit optionalen Diagnostics)

---

## Komponenten-Übersicht

### Core Tests (bereits vorhanden, Risk Layer v1.0)

- **Kupiec POF Test**: Testet, ob die VaR-Verletzungsrate statistisch korrekt ist
- **Christoffersen Independence Test**: Prüft, ob Verletzungen unabhängig sind
- **Christoffersen Conditional Coverage Test**: Kombinierter Test (POF + Independence)
- **Basel Traffic Light System**: Regulatorische Zonen (Green/Yellow/Red)

### Phase 9A: Duration Diagnostic (Optional)

- **Modul:** `src.risk_layer.var_backtest.duration_diagnostics`
- **Was:** Analysiert die *Zeitdauer zwischen VaR-Verletzungen*
- **Warum:** Wenn Verletzungen geclustert auftreten (kurze Abstände), ist das Modell in bestimmten Phasen schwach
- **Output:**
  - `duration_ratio`: Observed/Expected mean duration (< 0.5 → Clustering)
  - `clustering_score`: Absolute Abweichung vom erwarteten Wert
  - Optional: Exponential Goodness-of-Fit Test

**Wichtig:** Dies ist ein **Diagnostic**, kein Hypothesis-Test. Verwende es als *ergänzende Evidenz*, nicht als alleinige Basis für Modell-Ablehnung.

### Phase 9B: Rolling Evaluation (Optional)

- **Modul:** `src.risk_layer.var_backtest.rolling_evaluation`
- **Was:** Führt UC/IND/CC-Tests über mehrere Rolling Windows aus
- **Warum:** Zeigt, ob das Modell über Zeit stabil ist oder in bestimmten Perioden versagt
- **Output:**
  - `all_pass_rate`: Anteil der Windows, in denen ALLE Tests bestanden wurden
  - `worst_p_value`: Niedrigster p-Wert über alle Windows (kritischstes Fenster)
  - `verdict_stability`: Konsistenz der Verdicts über Zeit

**Use Cases:**
- Time-varying Model Quality (Regime-Wechsel)
- Early Warning (degradierende Performance)
- Identifikation problematischer Zeitperioden

### Phase 10: Snapshot Runner (CLI)

- **Script:** `scripts&#47;risk&#47;run_var_backtest_suite_snapshot.py`
- **Was:** Single-Command CLI für schnelle Backtest-Snapshots mit optionalen Diagnostics
- **Output:**
  - Console: Kompakte Zusammenfassung
  - File: `reports&#47;var_backtest&#47;var_backtest_suite_snapshot_YYYYMMDD_HHMMSS.md`

---

## Quickstart

### A) Library Usage (Python)

#### Basic Suite (Core Tests Only)

```python
from src.risk_layer.var_backtest import (
    VaRBacktestRunner,
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
    basel_traffic_light,
)
import pandas as pd

# Lade Daten (Returns & VaR-Schätzungen)
returns = pd.read_csv("portfolio_returns.csv", index_col=0, parse_dates=True)["return"]
var_estimates = pd.read_csv("var_estimates.csv", index_col=0, parse_dates=True)["var_99"]

# 1. Kupiec POF Test
runner = VaRBacktestRunner(confidence_level=0.99, significance_level=0.05)
result = runner.run(returns, var_estimates, symbol="PORTFOLIO")

print(f"Kupiec POF: {'PASS' if result.kupiec.is_valid else 'FAIL'}")
print(f"p-value: {result.kupiec.p_value:.4f}")

# Violations extrahieren
violations = result.violations.violations.tolist()  # Boolean list
n_violations = result.violations.n_violations

# 2. Christoffersen Independence Test
independence = christoffersen_independence_test(violations, alpha=0.05)
print(f"Independence: {'PASS' if independence.passed else 'FAIL'}")

# 3. Christoffersen Conditional Coverage Test
cc = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.01)
print(f"Conditional Coverage: {'PASS' if cc.passed else 'FAIL'}")

# 4. Basel Traffic Light
traffic_light = basel_traffic_light(
    n_violations,
    result.violations.n_observations,
    confidence_level=0.99
)
print(f"Basel Zone: {traffic_light.zone.value.upper()}")
```

#### Phase 9A: Duration Diagnostic (Optional)

```python
from src.risk_layer.var_backtest import (
    duration_independence_diagnostic,
    format_duration_diagnostic,
)

# Nach Core-Tests: violations bereits vorhanden
duration_result = duration_independence_diagnostic(
    exceedances=violations,
    expected_rate=0.01,  # 1% für 99% VaR
    timestamps=result.violations.dates,  # Optional: DatetimeIndex
    enable_exponential_test=False,  # Optional: Goodness-of-Fit
)

# Output
print(f"Duration Ratio: {duration_result.duration_ratio:.4f}")
print(f"Clustering Suspicious: {duration_result.is_suspicious()}")
print(f"Notes: {duration_result.notes}")

# Formatierte Ausgabe
print(format_duration_diagnostic(duration_result))

# Export
duration_dict = duration_result.to_dict()
```

**Interpretation:**
- `duration_ratio < 0.5`: ⚠️ Clustering verdächtig → Verifiziere mit Christoffersen IND Test
- `duration_ratio > 1.5`: ⚠️ Verletzungen zu selten → Modell evtl. zu konservativ
- `duration_ratio ∈ [0.5, 1.5]`: ✅ Kein starker Clustering-Hinweis

#### Phase 9B: Rolling Evaluation (Optional)

```python
from src.risk_layer.var_backtest import (
    rolling_evaluation,
    format_rolling_summary,
    get_failing_windows,
    get_worst_window,
)

# Rolling-Window Evaluation
rolling_result = rolling_evaluation(
    violations=violations,
    window_size=250,  # 250 Beobachtungen pro Window
    step_size=50,     # 50er Schritte (Overlap)
    var_alpha=0.01,   # 99% VaR
    test_alpha=0.05,  # 5% Test-Signifikanz
    timestamps=result.violations.dates,  # Optional
)

# Summary Statistics
summary = rolling_result.summary
print(f"Windows Evaluated: {summary.n_windows}")
print(f"All-Pass Rate: {summary.all_pass_rate:.1%}")
print(f"Worst Kupiec p-value: {summary.worst_kupiec_p_value:.4f}")
print(f"Verdict Stability: {summary.verdict_stability:.1%}")

# Formatierte Ausgabe
print(format_rolling_summary(rolling_result))

# Failing Windows identifizieren
failing = get_failing_windows(rolling_result)
for w in failing:
    print(f"Window {w.window_id}: Failed at idx {w.start_idx}-{w.end_idx}")

# Worst Window (nach Kriterium)
worst = get_worst_window(rolling_result, criterion="kupiec_p_value")
print(f"Worst Window: {worst.window_id} (p={worst.kupiec.p_value:.4f})")

# Export to DataFrame
df = rolling_result.to_dataframe()
print(df[["window_id", "all_passed", "kupiec_p_value"]])
```

**Interpretation:**
- `all_pass_rate ≥ 90%`: ✅ Stabiles Modell über Zeit
- `all_pass_rate ∈ [75%, 90%)`: ⚠️ Moderate Instabilität → Failing Windows untersuchen
- `all_pass_rate ∈ [50%, 75%)`: ⚠️ Unstabil → Modell degradiert möglicherweise
- `all_pass_rate < 50%`: ❌ Kritisch → Modell versagt in mehreren Perioden

---

### B) CLI: Snapshot Runner (Phase 10)

#### Basic Usage

```bash
# Help anzeigen
python3 scripts/risk/run_var_backtest_suite_snapshot.py --help

# Basic Suite (Core Tests only)
python3 scripts/risk/run_var_backtest_suite_snapshot.py \
  --returns-file data/portfolio_returns.csv \
  --var-file data/var_estimates.csv \
  --confidence 0.99

# Mit Phase 9A Duration Diagnostic
python3 scripts/risk/run_var_backtest_suite_snapshot.py \
  --returns-file data/portfolio_returns.csv \
  --var-file data/var_estimates.csv \
  --confidence 0.99 \
  --enable-duration-diagnostic

# Mit Phase 9B Rolling Evaluation
python3 scripts/risk/run_var_backtest_suite_snapshot.py \
  --returns-file data/portfolio_returns.csv \
  --var-file data/var_estimates.csv \
  --confidence 0.99 \
  --enable-rolling \
  --rolling-window-size 250 \
  --rolling-step-size 50

# Full Diagnostics (Duration + Rolling)
python3 scripts/risk/run_var_backtest_suite_snapshot.py \
  --returns-file data/portfolio_returns.csv \
  --var-file data/var_estimates.csv \
  --confidence 0.99 \
  --enable-duration-diagnostic \
  --enable-rolling \
  --rolling-window-size 250

# Synthetic Data Demo (kein CSV benötigt)
python3 scripts/risk/run_var_backtest_suite_snapshot.py \
  --use-synthetic \
  --n-observations 500 \
  --confidence 0.99 \
  --enable-duration-diagnostic \
  --enable-rolling
```

#### Output

**Console:**
```
======================================================================
VAR BACKTEST SUITE SUMMARY - PORTFOLIO
======================================================================
VaR Confidence Level:  99.0%
Observations:          500
Violations:            5
Violation Rate:        1.00%

Core Tests:
  Kupiec POF:          ✓ PASS  (p=0.9876)
  Independence:        ✓ PASS  (p=0.7234)
  Cond. Coverage:      ✓ PASS  (p=0.8123)
  Basel Traffic Light: GREEN

Phase 9A: Duration Diagnostic (optional)
  Duration Ratio:      0.9823
  Clustering:          ✓ NO

Phase 9B: Rolling Evaluation (optional)
  Windows Evaluated:   6
  All-Pass Rate:       100.0%
  Verdict Stability:   100.0%
  Assessment:          ✅ STABLE: ≥90% of windows passed all tests...

Overall Verdict:
  Core Tests:          ✅ ALL PASSED
======================================================================

📄 Report saved to: reports/var_backtest/var_backtest_suite_snapshot_20251229_143022.md
```

**File Output:**  
`reports&#47;var_backtest&#47;var_backtest_suite_snapshot_YYYYMMDD_HHMMSS.md`

Inhalt:
- Summary (Violations, Rate)
- Core Tests (Kupiec, Independence, CC, Basel)
- Optional: Duration Diagnostic (Phase 9A)
- Optional: Rolling Evaluation (Phase 9B) mit Window-Details-Tabelle
- Overall Verdict

**Exit Codes:**
- `0`: Alle Core-Tests bestanden
- `1`: Mind. ein Core-Test versagt
- `2`: Fehler (z.B. Input-Daten)

---

### C) Tests

#### Relevante Test-Pfade

```bash
# Phase 9A: Duration Diagnostic
python3 -m pytest tests/risk_layer/var_backtest/test_duration_diagnostics.py -v

# Phase 9B: Rolling Evaluation
python3 -m pytest tests/risk_layer/var_backtest/test_rolling_evaluation.py -v

# Phase 10: Snapshot Runner
python3 -m pytest tests/scripts/test_run_var_backtest_suite_snapshot.py -v

# Alle VaR Backtest Tests
python3 -m pytest tests/risk_layer/var_backtest/ -v
```

#### Fast Check

```bash
# Linter
ruff check src/risk_layer/var_backtest/duration_diagnostics.py
ruff check src/risk_layer/var_backtest/rolling_evaluation.py
ruff check scripts/risk/run_var_backtest_suite_snapshot.py

# Targeted Tests (schnell)
python3 -m pytest -q tests/risk_layer/var_backtest/test_duration_diagnostics.py
python3 -m pytest -q tests/risk_layer/var_backtest/test_rolling_evaluation.py
python3 -m pytest -q tests/scripts/test_run_var_backtest_suite_snapshot.py
```

---

## Design Notes

### Determinismus & Reproduzierbarkeit

**Snapshot-Stabilität:**
- Alle Outputs sind deterministisch (keine Zufallszahlen im Output)
- Timestamps explizit formatiert (`YYYYMMDD_HHMMSS`)
- Dict-Keys in stabiler Reihenfolge
- Markdown-Reports haben fixes Format

**Wichtig für:**
- CI/CD-Pipelines
- Snapshot-Diffs
- Audit-Trails

### Erwartete Failure-Modes

#### Unzureichende Daten

**Symptom:**
```python
ValueError: window_size (250) exceeds total observations (100)
```

**Lösung:**
- Für Rolling Evaluation: `window_size` reduzieren
- Mindestens 100 Beobachtungen pro Window empfohlen
- Für 99% VaR: Mind. 500 Beobachtungen total (für sinnvolle Statistik)

#### Zu kurze Fenster

**Symptom:**
```python
ValueError: window_size (50) must be >= min_window_size (100)
```

**Lösung:**
- `min_window_size` ist hardcoded auf 100 (für statistisch sinnvolle Tests)
- Für kürzere Windows: `min_window_size`-Parameter anpassen (auf eigenes Risiko)

#### NaN/Inf in Daten

**Symptom:**
```python
# Duration Ratio = nan
# Clustering Score = nan
```

**Ursache:**
- Zu wenig Verletzungen (< 2) → Keine Durations berechenbar
- Expected Rate = 0 → Division by zero

**Lösung:**
- Prüfe Input-Daten: `violations.sum() >= 2`
- Prüfe VaR-Level: 99.9% VaR mit 100 Observations → wahrscheinlich 0 Violations

#### Keine Rolling Windows möglich

**Symptom:**
```python
ValueError: Insufficient data for even one window
```

**Lösung:**
- `n_total >= window_size` erforderlich
- Entweder mehr Daten laden oder `window_size` reduzieren

---

## Erweiterungen

### Neue Rolling-Metrik hinzufügen

**Beispiel:** Mean Duration pro Window

1. **Erweitere `RollingWindowResult` (rolling_evaluation.py):**

```python
@dataclass
class RollingWindowResult:
    # ... existing fields ...
    mean_duration: Optional[float] = None  # NEW
```

2. **Compute in `rolling_evaluation()` loop:**

```python
# Nach Christoffersen Tests
duration_result = duration_independence_diagnostic(window_violations, ...)
mean_duration = duration_result.mean_duration if duration_result else None

window_result = RollingWindowResult(
    # ... existing args ...
    mean_duration=mean_duration,
)
```

3. **Update `to_dict()` method:**

```python
def to_dict(self) -> dict:
    result = {
        # ... existing keys ...
        "mean_duration": self.mean_duration,
    }
    return result
```

4. **Add to Summary (optional):**

```python
@dataclass
class RollingSummary:
    # ... existing fields ...
    mean_duration_avg: float = 0.0  # NEW
```

5. **Tests updaten:** `tests&#47;risk_layer&#47;var_backtest&#47;test_rolling_evaluation.py`

### Neue Diagnostic hinzufügen

**Beispiel:** Autocorrelation-basierte Diagnostic

1. **Erstelle neues Modul:** z.B. `autocorr_diagnostic.py`
2. **Implementiere Hauptfunktion:**

```python
def autocorr_diagnostic(violations: Sequence[bool], lag: int = 1) -> AutocorrResult:
    """Compute autocorrelation of violations at given lag."""
    # Implementation
    pass
```

3. **Export in `__init__.py`:**

```python
from src.risk_layer.var_backtest.autocorr_diagnostic import (
    AutocorrResult,
    autocorr_diagnostic,
)

__all__ = [
    # ... existing ...
    "AutocorrResult",
    "autocorr_diagnostic",
]
```

4. **Füge zu Snapshot Runner hinzu:** `scripts&#47;risk&#47;run_var_backtest_suite_snapshot.py`

```python
# In parse_args()
parser.add_argument("--enable-autocorr", action="store_true", help="...")

# In run_suite()
if enable_autocorr:
    autocorr_result = autocorr_diagnostic(violations, lag=1)
```

5. **Tests:** `tests&#47;risk_layer&#47;var_backtest&#47;test_autocorr_diagnostic.py`

---

## Related Documentation

- **[VaR Validation Operator Guide](VAR_VALIDATION_OPERATOR_GUIDE.md)** – Core VaR Validation (Kupiec + Basel)
- **[Risk Layer v1 Operator Guide](RISK_LAYER_V1_OPERATOR_GUIDE.md)** – Vollständige Risk-Layer-Doku
- **Integration Guide** (planned) – Workflows mit mehreren Risk-Komponenten
- **[Kupiec POF Backtest Roadmap](roadmaps/KUPIEC_POF_BACKTEST_ROADMAP.md)** – Original Roadmap
- **Implementation Reports:**
  - Phase 9A: `PHASE9A_IMPLEMENTATION_SUMMARY.md` (Duration Diagnostic)
  - Phase 9B: `PHASE9B_IMPLEMENTATION_SUMMARY.md` (Rolling Evaluation)
  - Phase 10: `PHASE10_IMPLEMENTATION_SUMMARY.md` (Snapshot Runner)

---

## Quick Decision Tree

```
Brauche ich Duration Diagnostic?
├─ Ja → Wenn ich clustering/temporal patterns in Violations vermute
├─ Ja → Für Regime-Change-Analyse
└─ Nein → Core Tests (Kupiec + Christoffersen) reichen

Brauche ich Rolling Evaluation?
├─ Ja → Wenn ich time-varying model quality prüfen will
├─ Ja → Für Early Warning System (degrading performance)
├─ Ja → Wenn ich problematische Zeitperioden identifizieren will
└─ Nein → Single-Window Backtest reicht

Wann Snapshot Runner verwenden?
├─ Schnelle Ad-hoc-Checks
├─ CI/CD-Integration (exit codes)
├─ Operator-friendly Output (Console + Markdown)
└─ Wenn ich nicht selbst Python-Code schreiben will
```

---

## Support & Troubleshooting

**Tests schlagen fehl?**
1. Prüfe Input-Daten: `violations.sum() >= 2` für Duration Diagnostic
2. Prüfe Window-Size: `window_size >= min_window_size` (100)
3. Prüfe Total Observations: `n_total >= window_size` für Rolling

**Unerwartete NaN-Werte?**
1. Duration Diagnostic: Braucht mind. 2 Violations
2. Rolling Evaluation: Jedes Window braucht mind. 100 Observations
3. Expected Rate = 0: Prüfe VaR-Level (zu konservativ?)

**Performance-Probleme?**
1. Rolling Evaluation: Reduziere Overlap (`step_size` erhöhen)
2. Exponential Test: Deaktiviere `enable_exponential_test=False`
3. Große Datensätze: Nutze Non-Overlapping Windows (`step_size = window_size`)

**Fragen?**
1. Check Tests: `tests&#47;risk_layer&#47;var_backtest&#47;` – Konkrete Usage-Beispiele
2. Check Core Docs: `docs&#47;risk&#47;VAR_VALIDATION_OPERATOR_GUIDE.md`
3. Run Tests: `python3 -m pytest tests&#47;risk_layer&#47;var_backtest&#47; -v`

---

**Last Updated:** 2025-12-29 (Phase 11)  
**Authors:** Agent C (Phase 9A/9B/10), Agent D (Phase 11 Doku)  
**Status:** ✅ Production-Ready (Backtest/Research only)
