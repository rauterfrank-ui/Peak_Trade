# Christoffersen Independence & Conditional Coverage Tests

**Status:** Phase 8B Complete  
**Date:** 2025-12-28  
**Module:** `src.risk_layer.var_backtest.christoffersen_tests`

---

## 📌 TL;DR

**Christoffersen Tests erweitern VaR Backtesting um zwei kritische Aspekte:**

1. **Independence Test (LR-IND):** Sind Violations unabhängig (keine Clustering)?
2. **Conditional Coverage (LR-CC):** Korrekte Coverage UND unabhängige Violations?

**Quick Start:**

```python
from src.risk_layer.var_backtest import (
    christoffersen_lr_ind,    # Independence Test
    christoffersen_lr_cc,     # Conditional Coverage
)

# Independence Test
result = christoffersen_lr_ind(exceedances)
print(result.verdict)  # "PASS" or "FAIL"

# Conditional Coverage Test
result = christoffersen_lr_cc(exceedances, alpha=0.01)
print(result.verdict)  # "PASS" or "FAIL"
```

**CLI:**
```bash
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR --tests all
# Shows UC + IND + CC in unified summary
```

---

## 🎯 Why Christoffersen Tests?

### The Problem with Kupiec POF Alone

**Kupiec POF Test (Unconditional Coverage)** prüft nur:
- ✅ Ist die Violations-Rate korrekt? (z.B. ~1% bei 99% VaR)

**Was es NICHT prüft:**
- ❌ Sind Violations zeitlich unabhängig?
- ❌ Gibt es Clustering (Violations häufen sich)?

### Real-World Example

**Szenario:** 99% VaR, 250 Beobachtungen

**Fall 1: Scattered Violations**
```
Violations: [Day 10, Day 50, Day 100, Day 150, Day 200]
Kupiec POF: PASS (5/250 = 2%, nahe 1%)
Independence: PASS ✅ (Violations verteilt)
```

**Fall 2: Clustered Violations**
```
Violations: [Day 246, Day 247, Day 248, Day 249, Day 250]
Kupiec POF: PASS (5/250 = 2%, nahe 1%)
Independence: FAIL ❌ (Violations clustered!)
```

**Interpretation:**
- Fall 1: Modell ist gut kalibriert UND Violations sind unabhängig ✅
- Fall 2: Modell hat richtige Rate, ABER unterschätzt Risiko während Stress-Phasen ❌

---

## 📚 Theory

### 1. Independence Test (LR-IND)

**Hypothesen:**
- **H₀:** Violations sind zeitlich unabhängig (π₀₁ = π₁₁)
- **H₁:** Violations sind abhängig (π₀₁ ≠ π₁₁)

**Transition Probabilities:**
- **π₀₁:** P(Violation today | No violation yesterday)
- **π₁₁:** P(Violation today | Violation yesterday)

**Test Statistic:**
```
LR-IND = -2 * (log L_restricted - log L_unrestricted)

wo:
  L_restricted: π₀₁ = π₁₁ = π (H₀: unabhängig)
  L_unrestricted: π₀₁ ≠ π₁₁ (H₁: abhängig)

LR-IND ~ χ²(1) unter H₀
```

**Transition Matrix:**
```
        Today
        No V   Viol
Yesterday
No V    n00    n01
Viol    n10    n11
```

**Interpretation:**
- **Low π₁₁:** Violations folgen nicht aufeinander (gut)
- **High π₁₁:** Violations clustern (schlecht - Modell unterschätzt Stress)

### 2. Conditional Coverage Test (LR-CC)

**Joint Hypothesis:**
- **H₀:** Modell hat korrekte Coverage UND Violations sind unabhängig
- **H₁:** Modell versagt bei Coverage ODER Independence (oder beides)

**Test Statistic:**
```
LR-CC = LR-UC + LR-IND

wo:
  LR-UC: Kupiec POF Statistik (unconditional coverage)
  LR-IND: Independence Statistik

LR-CC ~ χ²(2) unter H₀
```

**Interpretation:**
- **PASS:** Modell ist vollständig valide (Coverage + Independence) ✅
- **FAIL:** Prüfe welcher Teil versagt (UC oder IND)

---

## 📖 API Reference

### Independence Test

```python
from src.risk_layer.var_backtest import christoffersen_lr_ind

result = christoffersen_lr_ind(
    exceedances,           # Boolean sequence (True = exceedance)
    p_threshold=0.05,      # Significance level
)

# Result attributes
print(result.verdict)      # "PASS" or "FAIL"
print(result.lr_ind)       # LR-IND statistic
print(result.p_value)      # p-value from χ²(1)
print(result.n00, result.n01)  # Transition counts
print(result.n10, result.n11)
print(result.pi_01)        # P(V | ¬V)
print(result.pi_11)        # P(V | V)
print(result.notes)        # Interpretation text
```

**Return Type:** `ChristoffersenIndResult` (frozen dataclass)

### Conditional Coverage Test

```python
from src.risk_layer.var_backtest import christoffersen_lr_cc

result = christoffersen_lr_cc(
    exceedances,           # Boolean sequence
    alpha,                 # Expected exceedance rate (e.g., 0.01 for 99% VaR)
    p_threshold=0.05,      # Significance level
)

# Result attributes
print(result.verdict)      # "PASS" or "FAIL"
print(result.lr_uc)        # Kupiec component
print(result.lr_ind)       # Independence component
print(result.lr_cc)        # Combined (lr_uc + lr_ind)
print(result.p_value)      # p-value from χ²(2)
print(result.notes)        # Interpretation text
```

**Return Type:** `ChristoffersenCCResult` (frozen dataclass)

### Legacy API (Backward Compatible)

```python
from src.risk_layer.var_backtest import (
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
)

# Independence Test (legacy)
result = christoffersen_independence_test(violations, alpha=0.05)
print(result.passed)       # True or False
print(result.lr_statistic)
print(result.transition_matrix)  # ((n00, n01), (n10, n11))

# Conditional Coverage (legacy)
result = christoffersen_conditional_coverage_test(
    violations, alpha=0.05, var_alpha=0.01
)
print(result.passed)       # True or False
```

---

## 🖥️ CLI Usage

### Integrated VaR Backtest CLI

```bash
# Run all tests (UC + IND + CC)
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --confidence 0.99 \
  --tests all

# Run only Independence test
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests ind

# Run only Conditional Coverage test
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests cc

# CI mode (compact output)
PYTHONPATH=. python3 scripts/risk/run_var_backtest.py \
  --symbol BTC-EUR \
  --tests all \
  --ci-mode
# Output: BTC-EUR: UC:ACCEPT IND:FAIL CC:FAIL (4/366 violations)
```

### Standalone Christoffersen Demo

```bash
# Test scattered violations
PYTHONPATH=. python3 scripts/risk/run_christoffersen_demo.py \
  --pattern scattered --verbose

# Test clustered violations
PYTHONPATH=. python3 scripts/risk/run_christoffersen_demo.py \
  --pattern clustered

# Custom pattern
PYTHONPATH=. python3 scripts/risk/run_christoffersen_demo.py \
  --custom "FFTFFTFF"
```

---

## 💡 Usage Examples

### Example 1: Full VaR Backtest

```python
import pandas as pd
from src.risk_layer.var_backtest import (
    VaRBacktestRunner,
    christoffersen_lr_ind,
    christoffersen_lr_cc,
)

# Prepare data
returns = pd.Series([...])  # Your returns
var_estimates = pd.Series([...])  # Your VaR estimates

# Run Kupiec POF (UC)
runner = VaRBacktestRunner(confidence_level=0.99)
result = runner.run(returns, var_estimates, symbol="BTC-EUR")

print(f"UC Test: {result.kupiec.result.value}")
print(f"Violations: {result.kupiec.n_violations}/{result.kupiec.n_observations}")

# Extract violations
exceedances = result.violations.violations.tolist()

# Run Independence Test
ind_result = christoffersen_lr_ind(exceedances)
print(f"\nIND Test: {ind_result.verdict}")
print(f"LR-IND: {ind_result.lr_ind:.4f}, p-value: {ind_result.p_value:.4f}")
print(f"π₀₁: {ind_result.pi_01:.4f}, π₁₁: {ind_result.pi_11:.4f}")

# Run Conditional Coverage Test
cc_result = christoffersen_lr_cc(exceedances, alpha=0.01)
print(f"\nCC Test: {cc_result.verdict}")
print(f"LR-CC: {cc_result.lr_cc:.4f} (= {cc_result.lr_uc:.4f} + {cc_result.lr_ind:.4f})")
print(f"p-value: {cc_result.p_value:.4f}")

# Overall assessment
if result.is_valid and ind_result.verdict == "PASS" and cc_result.verdict == "PASS":
    print("\n✅ Model is fully validated")
else:
    print("\n❌ Model has issues:")
    if not result.is_valid:
        print("  - Coverage is incorrect")
    if ind_result.verdict == "FAIL":
        print("  - Violations are clustered")
```

### Example 2: Detect Violation Clustering

```python
from src.risk_layer.var_backtest import christoffersen_lr_ind

# Your violations (True = VaR exceedance)
exceedances = [False] * 245 + [True] * 5

result = christoffersen_lr_ind(exceedances)

if result.verdict == "FAIL":
    print("⚠️  Violations are clustered!")
    print(f"π₁₁ = {result.pi_11:.4f} (prob of violation following violation)")

    if result.pi_11 > 0.5:
        print("→ Strong clustering detected")
        print("→ Model underestimates risk during stress periods")
else:
    print("✅ Violations are independent")
```

### Example 3: Compare Models

```python
from src.risk_layer.var_backtest import christoffersen_lr_cc

models = {
    "Historical VaR": exceedances_hist,
    "Parametric VaR": exceedances_param,
    "EWMA VaR": exceedances_ewma,
}

for name, exceedances in models.items():
    result = christoffersen_lr_cc(exceedances, alpha=0.01)
    print(f"{name:20s} CC: {result.verdict:4s} (p={result.p_value:.4f})")
```

---

## 🧮 Interpretation Guide

### Understanding π₀₁ and π₁₁

**Scenario 1: Independent Violations**
```
π₀₁ = 0.01  (1% chance after no violation)
π₁₁ = 0.01  (1% chance after violation)
→ π₀₁ ≈ π₁₁ → Independent ✅
```

**Scenario 2: Positive Clustering**
```
π₀₁ = 0.005  (0.5% chance after no violation)
π₁₁ = 0.80   (80% chance after violation!)
→ π₁₁ >> π₀₁ → Strong clustering ❌
```

**Scenario 3: Negative Clustering (Alternating)**
```
π₀₁ = 0.02   (2% chance after no violation)
π₁₁ = 0.001  (0.1% chance after violation)
→ π₁₁ << π₀₁ → Alternating pattern ❌
```

### Decision Tree

```
Start with UC Test (Kupiec POF):
│
├─ UC FAIL → Coverage is wrong
│   └─ Fix VaR model calibration
│
└─ UC PASS → Coverage is correct
    │
    ├─ IND FAIL → Violations clustered
    │   ├─ π₁₁ >> π₀₁ → Positive clustering
    │   │   └─ Model underestimates stress periods
    │   │
    │   └─ π₁₁ << π₀₁ → Negative clustering
    │       └─ Model may be too reactive
    │
    └─ IND PASS → Violations independent
        │
        └─ CC PASS → Model is fully validated ✅
```

---

## ⚠️ Common Pitfalls

### 1. Insufficient Data

**Problem:** Too few violations for reliable IND test

```python
# 250 observations, 1 violation
result = christoffersen_lr_ind(violations)
# → May not have enough transitions for meaningful test
```

**Recommendation:**
- Minimum: 250 observations (Basel III)
- Better: 500-1000 observations
- Need at least 2 violations for IND test

### 2. Misinterpreting CC Failure

**Problem:** CC fails, but which component?

```python
cc_result = christoffersen_lr_cc(exceedances, alpha=0.01)
if cc_result.verdict == "FAIL":
    # Check components
    print(f"LR-UC: {cc_result.lr_uc:.4f}")  # Coverage
    print(f"LR-IND: {cc_result.lr_ind:.4f}")  # Independence

    # Decompose to identify issue
```

**Solution:** Always check UC and IND separately

### 3. Clustering in Synthetic Data

**Problem:** Test data has artificial clustering

```python
# Bad: All violations at end
violations = [False] * 245 + [True] * 5
# → Will fail IND test artificially
```

**Solution:** Use realistic data or scattered test patterns

---

## 🎓 Best Practices

### 1. Always Run All Three Tests

```python
# Complete validation
uc_result = kupiec_pof_test(violations, ...)
ind_result = christoffersen_lr_ind(violations)
cc_result = christoffersen_lr_cc(violations, alpha=...)

# Model is valid only if ALL pass
model_valid = (
    uc_result.is_valid and
    ind_result.verdict == "PASS" and
    cc_result.verdict == "PASS"
)
```

### 2. Use Appropriate Significance Level

```python
# Standard: 5%
result = christoffersen_lr_ind(exceedances, p_threshold=0.05)

# Conservative: 10% (less likely to reject)
result = christoffersen_lr_ind(exceedances, p_threshold=0.10)

# Strict: 1% (more likely to reject)
result = christoffersen_lr_ind(exceedances, p_threshold=0.01)
```

### 3. Document Test Results

```python
# Save to JSON for audit trail
results = {
    "date": datetime.now().isoformat(),
    "symbol": "BTC-EUR",
    "uc_test": uc_result.to_dict() if hasattr(uc_result, 'to_dict') else {...},
    "ind_test": ind_result.to_dict(),
    "cc_test": cc_result.to_dict(),
    "overall_valid": model_valid,
}

with open("backtest_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

### 4. Monitor Over Time

```python
# Track tests over rolling windows
for window_end in date_range:
    window_start = window_end - timedelta(days=250)
    violations_window = violations[window_start:window_end]

    result = christoffersen_lr_ind(violations_window)
    results_history.append({
        "date": window_end,
        "verdict": result.verdict,
        "lr_ind": result.lr_ind,
    })

# Plot to detect deterioration
```

---

## 📊 Technical Details

### Stdlib-Only Implementation

**No scipy or numpy required:**

```python
# Chi²(1): via error function
def chi2_df1_sf(x):
    return math.erfc(math.sqrt(x / 2))

# Chi²(2): via exponential
def chi2_df2_sf(x):
    return math.exp(-x / 2)

# Transition matrix: tuple of tuples
transition_matrix = ((n00, n01), (n10, n11))
```

### Numerical Stability

**Eps clamping for transition probabilities:**

```python
# Avoid log(0) errors
pi_01 = max(EPS, min(1 - EPS, pi_01))
pi_11 = max(EPS, min(1 - EPS, pi_11))
```

### Edge Cases Handled

- ✅ No violations (n₁ = 0): Returns PASS with p=1.0
- ✅ All violations (n₀ = 0): Returns PASS with p=1.0
- ✅ Single violation: Not enough data for transitions
- ✅ Alternating pattern: Detected as clustering (FAIL)

---

## 🔗 Related Documentation

- **Kupiec POF:** `docs/risk/KUPIEC_POF_CANONICAL_PATH.md`
- **CLI Integration:** `PHASE8B_CLI_INTEGRATION.md`
- **Implementation:** `PHASE8B_MERGE_LOG.md`
- **Theory:** Christoffersen (1998), "Evaluating Interval Forecasts"

---

## 📚 References

### Academic Papers

1. **Christoffersen, P. F. (1998)**
   "Evaluating Interval Forecasts"
   *International Economic Review*, 39(4), 841-862
   - Original paper introducing LR-IND and LR-CC tests

2. **Kupiec, P. (1995)**
   "Techniques for Verifying the Accuracy of Risk Measurement Models"
   *Journal of Derivatives*
   - Foundation for unconditional coverage test

3. **Christoffersen, P. F. (2012)**
   "Elements of Financial Risk Management" (2nd ed.)
   - Comprehensive treatment of VaR backtesting

### Basel Committee

- **Basel Committee on Banking Supervision (1996)**
  "Supervisory Framework for the Use of 'Backtesting' in Conjunction with the Internal Models Approach to Market Risk Capital Requirements"

---

## 🎯 Summary

**Christoffersen Tests add critical validation:**

✅ **Independence Test (LR-IND)**
- Detects violation clustering
- Identifies stress-period weaknesses
- stdlib-only, no scipy

✅ **Conditional Coverage (LR-CC)**
- Joint test: Coverage + Independence
- Complete model validation
- Decomposes to UC + IND

✅ **Integrated CLI**
- Unified UC/IND/CC summary
- Flexible test selection
- CI-friendly output

**Use Cases:**
- Model validation (research)
- Regulatory compliance (Basel III)
- Risk monitoring (operations)
- Model comparison

**Key Insight:**
> *Correct coverage is necessary but not sufficient.  
> Violations must also be independent.*

---

**Documentation Complete! 📚**

For questions or issues, see:
- CLI usage: `python3 scripts/risk/run_var_backtest.py --help`
- Demo: `python3 scripts/risk/run_christoffersen_demo.py --help`
- Tests: `tests/risk_layer/var_backtest/test_christoffersen.py`
