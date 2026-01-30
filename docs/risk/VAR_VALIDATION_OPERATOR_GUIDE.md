# VaR Validation - Operator Guide

**Version:** 1.0  
**Date:** 2025-12-28  
**Status:** ✅ Production-Ready (Phase 2 merged to main)

---

## What is VaR Validation?

VaR Validation is a statistical framework for testing whether your VaR (Value at Risk) model is performing correctly. It includes:

1. **Kupiec POF Test** - Statistical test for breach rate
2. **Basel Traffic Light System** - Regulatory classification (Green/Yellow/Red)
3. **Breach Analysis** - Pattern detection (clustering, gaps)

---

## When to Run

**Required:**
- ✅ After backtesting (before promoting strategy to live)
- ✅ Monthly/quarterly model review
- ✅ After significant market regime changes

**Optional:**
- After parameter changes (confidence level, window size)
- When investigating unexpected losses

---

## How to Run

### Quick Start (Copy-Paste)

```python
from src.risk.var import historical_var
from src.risk.validation import run_var_backtest
import pandas as pd

# Step 1: Load your returns data
returns = pd.Series([...])  # Your actual returns

# Step 2: Calculate VaR
var_value = historical_var(returns, alpha=0.01)  # 99% VaR

# Step 3: Create VaR series (constant for simplicity)
var_series = pd.Series(var_value, index=returns.index)

# Step 4: Run validation
result = run_var_backtest(
    returns=returns,
    var_series=var_series,
    confidence_level=0.99
)

# Step 5: Check results
print(f"Breaches: {result.breaches}/{result.observations}")
print(f"Kupiec Test: {'✅ VALID' if result.kupiec.is_valid else '❌ INVALID'}")
print(f"Basel Traffic Light: {result.traffic_light.color.upper()}")

# Step 6: Generate report
print(result.to_markdown())
```

---

## Interpreting Results

### Kupiec POF Test

**Status: ✅ VALID**
- Model is performing correctly
- Breach rate is statistically reasonable
- **Action:** No changes needed

**Status: ❌ INVALID**
- Model is mis-specified
- Too many or too few breaches
- **Action:** Review VaR model, adjust parameters, or investigate data quality

**p-value Interpretation:**
- `p-value > 0.05` → VALID (cannot reject null hypothesis)
- `p-value ≤ 0.05` → INVALID (reject null hypothesis)

---

### Basel Traffic Light

**🟢 GREEN Zone (0-4 breaches at 99% for 250 obs)**
- Model is performing well
- **Action:** Continue monitoring

**🟡 YELLOW Zone (5-9 breaches at 99% for 250 obs)**
- Model may need attention
- **Action:** Investigate causes, consider parameter adjustments

**🔴 RED Zone (≥10 breaches at 99% for 250 obs)**
- Model is underperforming
- **Action:** Immediate review required, consider model replacement

**Note:** Thresholds scale with observation count and confidence level.

---

### Breach Analysis

**Max Consecutive Breaches:**
- High values (>3) indicate clustering
- May suggest volatility regime changes
- **Action:** Consider EWMA VaR or regime-switching models

**Average Gap:**
- Low values indicate frequent breaches
- May suggest VaR is too low
- **Action:** Review VaR calculation, increase confidence level

---

## Common Failure Modes

### 1. Index Alignment Issues

**Symptom:** `0 observations` in result

**Cause:** Returns and VaR series have no overlapping dates

**Fix:**
```python
# Check indices
print(f"Returns: {returns.index.min()} to {returns.index.max()}")
print(f"VaR: {var_series.index.min()} to {var_series.index.max()}")

# Align manually if needed
common_index = returns.index.intersection(var_series.index)
returns_aligned = returns.loc[common_index]
var_aligned = var_series.loc[common_index]
```

---

### 2. Too Few Observations

**Symptom:** Kupiec test unreliable, high p-value variance

**Cause:** Less than 100 observations

**Fix:**
- Use longer backtest period (250+ observations recommended)
- Or accept higher uncertainty in validation results

---

### 3. Alpha Mismatch

**Symptom:** Kupiec test always rejects

**Cause:** VaR calculated at different confidence level than validation

**Fix:**
```python
# Ensure consistency
var_value = historical_var(returns, alpha=0.01)  # 99% VaR
result = run_var_backtest(
    returns, var_series,
    confidence_level=0.99  # Must match: 1 - alpha
)
```

---

### 4. All NaNs

**Symptom:** `0 observations` after alignment

**Cause:** Returns or VaR series contains only NaNs

**Fix:**
```python
# Remove NaNs before validation
returns_clean = returns.dropna()
var_clean = var_series.dropna()
```

---

## Performance Expectations

| Observations | Expected Time |
|--------------|---------------|
| 100 | <10ms |
| 250 | <20ms |
| 1000 | <50ms |
| 5000 | <200ms |

**Target:** <100ms for 250 observations ✅ Achieved

---

## Example Workflow

### Full Validation Pipeline

```python
from src.risk.var import historical_var, parametric_var
from src.risk.validation import run_var_backtest
import pandas as pd

# Load data
returns = pd.read_csv("returns.csv", index_col=0, parse_dates=True)["returns"]

# Split: 80% training, 20% validation
split_idx = int(len(returns) * 0.8)
returns_train = returns[:split_idx]
returns_test = returns[split_idx:]

# Calculate VaR on training set
var_hist = historical_var(returns_train, alpha=0.01)
var_param = parametric_var(returns_train, alpha=0.01)

# Create VaR series for testing
var_hist_series = pd.Series(var_hist, index=returns_test.index)
var_param_series = pd.Series(var_param, index=returns_test.index)

# Validate both methods
result_hist = run_var_backtest(returns_test, var_hist_series, confidence_level=0.99)
result_param = run_var_backtest(returns_test, var_param_series, confidence_level=0.99)

# Compare
print("Historical VaR:")
print(f"  Breaches: {result_hist.breaches}")
print(f"  Kupiec: {'✅' if result_hist.kupiec.is_valid else '❌'}")
print(f"  Traffic Light: {result_hist.traffic_light.color}")

print("\nParametric VaR:")
print(f"  Breaches: {result_param.breaches}")
print(f"  Kupiec: {'✅' if result_param.kupiec.is_valid else '❌'}")
print(f"  Traffic Light: {result_param.traffic_light.color}")

# Export reports
with open("var_validation_hist.md", "w") as f:
    f.write(result_hist.to_markdown())

with open("var_validation_param.md", "w") as f:
    f.write(result_param.to_markdown())
```

---

## Best Practices

### ✅ DO

- Use at least 250 observations for validation
- Run validation on out-of-sample data (not training set)
- Document validation results in strategy review
- Re-validate after parameter changes
- Monitor traffic light color over time

### ❌ DON'T

- Don't validate on training data (overfitting)
- Don't ignore RED traffic light warnings
- Don't mix confidence levels (VaR vs validation)
- Don't skip validation before live deployment
- Don't use less than 100 observations

---

## Troubleshooting

### Q: Why do I get 0 observations?

**A:** Index alignment issue. Check that returns and VaR series have overlapping dates.

### Q: Why is Kupiec test always rejecting?

**A:** Either (1) VaR model is mis-specified, (2) alpha mismatch, or (3) too few observations.

### Q: What if I'm in YELLOW zone?

**A:** Investigate breach patterns. If clustering, consider EWMA VaR. If random, may be acceptable.

### Q: Can I use this for live trading?

**A:** Yes, but validate monthly and monitor traffic light. RED zone requires immediate action.

---

## References

- **Kupiec POF Test:** Kupiec, P. (1995). "Techniques for Verifying the Accuracy of Risk Measurement Models"
- **Basel Traffic Light:** Basel Committee on Banking Supervision (1996)
- **Implementation:** Phase 2 VaR Validation (PR #413)

---

## Support

**Questions?**
1. Check Integration Guide (planned) for workflows
2. Check [Tests](../../tests/risk/validation/) for usage examples
3. Run tests: `python3 -m pytest tests&#47;risk&#47;validation&#47; -v`

**Issues?**
- Check Troubleshooting section above
- Review test failures for similar cases
- Check linter: `read_lints` tool

---

**Last Updated:** 2025-12-28  
**Version:** 1.0  
**Status:** ✅ Production-Ready
