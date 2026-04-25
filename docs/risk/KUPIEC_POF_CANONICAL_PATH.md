# Kupiec POF: Canonical Import Path Guide


## Authority and epoch note

This guide preserves historical and component-level Kupiec POF canonical-path context. Phrases such as active status, canonical path, valid model, migration complete, or test success are not, by themselves, current Master V2 approval, Doubleplay authority, First-Live readiness, operator authorization, model certification, or permission to route orders into any live capital path.

Kupiec POF can support VaR / risk review and model-quality discussions, but it is not a standalone promotion gate. Canonical import guidance does not collapse validation-suite and risk-layer surfaces into a single trading-authority path. Any live or first-live promotion remains governed by current gate, evidence, and signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, and staged Execution Enablement. This note is docs-only and changes no runtime behavior.

**Version:** Phase 8A (2025-12-28)  
**Status:** ✅ Active

---

## 🎯 Übersicht

Seit **Phase 8A** ist die Kupiec POF Implementierung in einem **kanonischen Modul** konsolidiert, während das Legacy-Modul als **Thin Wrapper** erhalten bleibt.

### Canonical Engine

**Empfohlener Import-Pfad:**

```python
from src.risk_layer.var_backtest.kupiec_pof import (
    kupiec_lr_uc,           # Direct n/x/alpha API
    kupiec_from_exceedances, # Boolean series helper
    KupiecLRResult,         # Phase 7 result dataclass
)
```

### Legacy Wrapper (Deprecated)

**Weiterhin unterstützt, aber veraltet:**

```python
from src.risk.validation.kupiec_pof import (
    kupiec_pof_test,        # Wrapper → kupiec_lr_uc
    kupiec_lr_statistic,    # Wrapper → _compute_lr_statistic
    chi2_p_value,           # Wrapper → chi2_df1_sf
    KupiecResult,           # Adapter dataclass
)
```

⚠️ **Deprecation Warning:** Das Legacy-Modul zeigt eine Warnung beim Import (kann mit `PEAK_TRADE_SILENCE_DEPRECATIONS=1` unterdrückt werden).

---

## 📦 API-Referenz

### Canonical API (src.risk_layer.var_backtest.kupiec_pof)

#### `kupiec_lr_uc(n, x, alpha, *, p_threshold=0.05) -> KupiecLRResult`

**Beschreibung:** Direkte Kupiec Unconditional Coverage (LR-UC) Test.

**Parameter:**
- `n` (int): Anzahl Beobachtungen (muss > 0 sein)
- `x` (int): Anzahl Exceedances/Violations (0 ≤ x ≤ n)
- `alpha` (float): Erwartete Exceedance-Rate (z.B. 0.01 für 99% VaR)
- `p_threshold` (float): Signifikanzniveau für Verdict (default: 0.05)

**Rückgabe:** `KupiecLRResult` mit:
- `n`, `x`, `alpha`: Eingabewerte
- `phat`: Beobachtete Exceedance-Rate (x/n)
- `lr_uc`: Likelihood Ratio Statistik
- `p_value`: p-Wert aus χ²(df=1)
- `verdict`: "PASS" wenn p_value ≥ p_threshold, sonst "FAIL"
- `notes`: Zusätzlicher Kontext

**Beispiel:**
```python
from src.risk_layer.var_backtest.kupiec_pof import kupiec_lr_uc

# 99% VaR: 10 Violations in 1000 Tagen
result = kupiec_lr_uc(n=1000, x=10, alpha=0.01)

print(result.verdict)    # "PASS"
print(result.p_value)    # ~0.92
print(result.lr_uc)      # ~0.01
```

---

#### `kupiec_from_exceedances(exceedances, alpha, *, p_threshold=0.05) -> KupiecLRResult`

**Beschreibung:** Kupiec Test aus Boolean-Sequenz.

**Parameter:**
- `exceedances` (Sequence[bool]): Boolean-Liste (True = Violation)
- `alpha` (float): Erwartete Exceedance-Rate
- `p_threshold` (float): Signifikanzniveau (default: 0.05)

**Rückgabe:** `KupiecLRResult` (wie oben)

**Beispiel:**
```python
from src.risk_layer.var_backtest.kupiec_pof import kupiec_from_exceedances

# Boolean-Sequenz: 10 Violations in 1000 Tagen
violations = [False] * 990 + [True] * 10

result = kupiec_from_exceedances(violations, alpha=0.01)
print(result.verdict)    # "PASS"
```

---

### Legacy API (src.risk.validation.kupiec_pof) - DEPRECATED

#### `kupiec_pof_test(breaches, observations, confidence_level=0.99, alpha=0.05) -> KupiecResult`

**Beschreibung:** Legacy Kupiec POF Test (delegiert zu `kupiec_lr_uc`).

**Parameter:**
- `breaches` (int): Anzahl VaR-Überschreitungen
- `observations` (int): Anzahl Beobachtungen
- `confidence_level` (float): VaR-Konfidenzniveau (z.B. 0.99 für 99% VaR)
- `alpha` (float): Signifikanzniveau (default: 0.05)

**Rückgabe:** `KupiecResult` mit:
- `breaches`, `observations`: Eingabewerte
- `test_statistic`: LR-Statistik
- `p_value`: p-Wert
- `is_valid`: True wenn Test bestanden (p_value ≥ alpha)

**Beispiel:**
```python
from src.risk.validation.kupiec_pof import kupiec_pof_test

# 5 Violations in 250 Tagen, 99% VaR
result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)

print(result.is_valid)        # True oder False
print(result.p_value)         # p-Wert
```

---

## 🔄 Migration Guide

### Schritt 1: Identifiziere Legacy-Imports

Suche alle Imports des Legacy-Moduls:

```bash
rg "from src.risk.validation.kupiec_pof import"
```

### Schritt 2: Ersetze durch Canonical Imports

**Alt (Legacy):**
```python
from src.risk.validation.kupiec_pof import kupiec_pof_test, KupiecResult

result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
if result.is_valid:
    print("VaR model is valid")
```

**Neu (Canonical):**
```python
from src.risk_layer.var_backtest.kupiec_pof import kupiec_lr_uc

result = kupiec_lr_uc(n=250, x=5, alpha=0.01)  # alpha = 1 - confidence_level
if result.verdict == "PASS":
    print("VaR model is valid")
```

### Schritt 3: Update Dataclass-Zugriffe

**Mapping:**

| Legacy (`KupiecResult`)      | Canonical (`KupiecLRResult`)  |
|------------------------------|-------------------------------|
| `result.breaches`            | `result.x`                    |
| `result.observations`        | `result.n`                    |
| `result.test_statistic`      | `result.lr_uc`                |
| `result.p_value`             | `result.p_value`              |
| `result.is_valid`            | `result.verdict == "PASS"`    |
| `result.confidence_level`    | `1 - result.alpha`            |
| `result.expected_breaches`   | `result.n * result.alpha`     |

---

## 🧪 Testing

### Delegation Tests

Stelle sicher, dass Legacy-Modul korrekt delegiert:

```bash
python3 -m pytest tests/risk/validation/test_kupiec_delegation.py -v
```

**Testabdeckung:**
- ✅ Legacy-Funktionen rufen Canonical-Funktionen auf
- ✅ Ergebnisse sind identisch zwischen Legacy und Canonical
- ✅ Keine duplizierte Math-Logik im Legacy-Modul

---

## 📖 Verwandte Dokumentation

- **Hauptreport:** [`IMPLEMENTATION_REPORT_KUPIEC_POF.md`](../../IMPLEMENTATION_REPORT_KUPIEC_POF.md)
- **Roadmap:** [`docs/risk/roadmaps/KUPIEC_POF_BACKTEST_ROADMAP.md`](roadmaps/KUPIEC_POF_BACKTEST_ROADMAP.md)

---

## 💡 Best Practices

1. **Bevorzuge Canonical API** für neuen Code
2. **Legacy API bleibt stabil** für bestehenden Code (kein Breaking Change)
3. **Silence Deprecation Warnings** in Tests mit `PEAK_TRADE_SILENCE_DEPRECATIONS=1`
4. **Migriere schrittweise** ohne Hektik - beide Pfade sind voll getestet

---

**Autor:** Peak Trade Team  
**Version:** Phase 8A (2025-12-28)
