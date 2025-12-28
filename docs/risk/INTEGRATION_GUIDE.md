# Risk Layer Integration Guide

**Version:** 1.0  
**Date:** 2025-12-28  
**Agent:** A6 (Integration & Documentation)

---

## Executive Summary

Dieser Guide zeigt, wie die verschiedenen Risk Layer Komponenten zusammen verwendet werden, um umfassende Risk Assessments durchzuführen.

**Verfügbare Komponenten:**
- ✅ VaR/CVaR Calculation (Historical, Parametric, EWMA, Cornish-Fisher)
- ✅ VaR Validation (Kupiec POF Test, Basel Traffic Light)
- ✅ Component VaR (Risk Attribution & Decomposition)
- ✅ Monte Carlo VaR (Simulation-based risk estimation)
- ✅ Stress Testing (Historical scenarios + Reverse stress)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Common Workflows](#common-workflows)
3. [Component Integration](#component-integration)
4. [Configuration](#configuration)
5. [Error Handling](#error-handling)
6. [Performance](#performance)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Minimal Example: VaR Calculation

```python
from src.risk.var import historical_var, parametric_var
import pandas as pd
import numpy as np

# Generate sample returns
returns = pd.Series(np.random.normal(0.001, 0.02, 250))

# Calculate Historical VaR
hist_var = historical_var(returns, alpha=0.05)  # 95% VaR
print(f"Historical VaR (95%): {hist_var:.4f}")

# Calculate Parametric VaR
param_var = parametric_var(returns, alpha=0.05)
print(f"Parametric VaR (95%): {param_var:.4f}")
```

### VaR + Validation Workflow

```python
from src.risk.var import historical_var
from src.risk.validation import run_var_backtest
import pandas as pd
import numpy as np

# Step 1: Calculate VaR on training data
returns_train = pd.Series(np.random.normal(0.001, 0.02, 250))
var_value = historical_var(returns_train, alpha=0.05)

# Step 2: Generate test data
returns_test = pd.Series(np.random.normal(0.001, 0.02, 250))
var_series = pd.Series(var_value, index=returns_test.index)

# Step 3: Run backtest with validation
result = run_var_backtest(
    returns=returns_test,
    var_series=var_series,
    confidence_level=0.95
)

# Step 4: Check results
print(f"Breaches: {result.n_breaches}/{result.total_observations}")
print(f"Kupiec Test: {result.kupiec.result}")
print(f"Basel Traffic Light: {result.traffic_light.color}")

# Generate report
print(result.to_markdown())
```

---

## Common Workflows

### Workflow 1: VaR Calculation → Validation → Reporting

**Use Case:** Validate VaR model performance on historical data.

**Steps:**
1. Calculate VaR on training period
2. Backtest on validation period
3. Run Kupiec POF test
4. Check Basel Traffic Light classification
5. Generate report

**Code:**

```python
from src.risk.var import parametric_var
from src.risk.validation import run_var_backtest
import pandas as pd

# 1. Train/Test split
returns = pd.Series(...)  # Your returns data
returns_train = returns[:250]
returns_test = returns[250:]

# 2. Calculate VaR
var_value = parametric_var(returns_train, alpha=0.05)

# 3. Create VaR series for testing
var_series = pd.Series(var_value, index=returns_test.index)

# 4. Run backtest
result = run_var_backtest(
    returns=returns_test,
    var_series=var_series,
    confidence_level=0.95
)

# 5. Generate report
with open("var_backtest_report.md", "w") as f:
    f.write(result.to_markdown())

# 6. Export JSON
import json
with open("var_backtest_result.json", "w") as f:
    json.dump(result.to_json(), f, indent=2)
```

**Expected Output:**
- Kupiec POF test result (accept/reject)
- Basel Traffic Light color (green/yellow/red)
- Breach analysis (if breaches occurred)
- Markdown and JSON reports

---

### Workflow 2: Portfolio VaR → Component VaR (Attribution)

**Use Case:** Understand which assets contribute most to portfolio risk.

**Steps:**
1. Calculate portfolio VaR
2. Decompose into component VaR
3. Analyze contributions

**Code:**

```python
from src.risk.component_var import ComponentVaRCalculator
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
import pandas as pd

# Setup
returns_df = pd.DataFrame({
    "BTC": [...],  # Your BTC returns
    "ETH": [...],  # Your ETH returns
    "SOL": [...],  # Your SOL returns
})

weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
portfolio_value = 100_000  # EUR

# Initialize engines
var_engine = ParametricVaR(ParametricVaRConfig(confidence_level=0.95))
cov_estimator = CovarianceEstimator(CovarianceEstimatorConfig(method="sample"))

# Calculate Component VaR
calculator = ComponentVaRCalculator(cov_estimator, var_engine)
result = calculator.calculate(
    returns_df=returns_df,
    weights=weights,
    portfolio_value=portfolio_value
)

# Print results
print(f"Total Portfolio VaR: €{result.total_var:,.2f}")
print("\nComponent VaR:")
for asset, comp_var in result.component_var.items():
    contrib_pct = result.contribution_pct[asset]
    print(f"  {asset}: €{comp_var:,.2f} ({contrib_pct:.1f}%)")

# Verify Euler property
assert abs(result.component_var.sum() - result.total_var) < 0.01
print("\n✅ Euler property verified")
```

**Expected Output:**
```
Total Portfolio VaR: €4,523.45

Component VaR:
  BTC: €3,123.45 (69.0%)
  ETH: €945.12 (20.9%)
  SOL: €454.88 (10.1%)

✅ Euler property verified
```

---

### Workflow 3: Monte Carlo VaR + Stress Testing

**Use Case:** Estimate VaR using simulations and test against historical crises.

**Steps:**
1. Run Monte Carlo simulation
2. Load historical stress scenarios
3. Apply scenarios to portfolio
4. Compare results

**Code:**

```python
from src.risk.monte_carlo import MonteCarloVaRCalculator, MonteCarloVaRConfig
from src.risk.stress_tester import StressTester
import pandas as pd

# 1. Monte Carlo VaR
returns_df = pd.DataFrame({
    "BTC": [...],
    "ETH": [...],
})

mc_config = MonteCarloVaRConfig(
    confidence_level=0.95,
    n_simulations=10_000,
    method="normal",  # or "bootstrap", "studentt"
    seed=42
)

mc_calculator = MonteCarloVaRCalculator(mc_config)
mc_result = mc_calculator.calculate(returns_df)

print(f"MC VaR (95%): {mc_result.var_95:.4f}")
print(f"MC CVaR (95%): {mc_result.cvar_95:.4f}")

# 2. Stress Testing
stress_tester = StressTester(scenarios_dir="data/scenarios")

portfolio_weights = {"BTC": 0.6, "ETH": 0.4}
portfolio_value = 100_000

# Run all available scenarios
print("\nStress Test Results:")
for scenario in stress_tester.scenarios:
    result = stress_tester.run_stress(
        portfolio_weights=portfolio_weights,
        portfolio_value=portfolio_value,
        scenario_name=scenario.name
    )
    print(f"  {scenario.name}: {result.loss_pct:.2f}% loss")
```

**Expected Output:**
```
MC VaR (95%): 0.0453
MC CVaR (95%): 0.0612

Stress Test Results:
  COVID-19 Crash March 2020: -45.23% loss
  China Ban May 2021: -35.67% loss
  LUNA Collapse May 2022: -28.45% loss
  FTX Collapse Nov 2022: -18.90% loss
  Bear Market 2018: -62.34% loss
```

---

### Workflow 4: Full Risk Assessment

**Use Case:** Comprehensive risk assessment combining all components.

**Steps:**
1. Calculate VaR (multiple methods)
2. Validate VaR
3. Attribute risk to components
4. Run stress scenarios
5. Generate comprehensive report

**Code:**

```python
from src.risk.var import historical_var, parametric_var, ewma_var
from src.risk.validation import run_var_backtest
from src.risk.component_var import ComponentVaRCalculator
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
from src.risk.monte_carlo import MonteCarloVaRCalculator, MonteCarloVaRConfig
from src.risk.stress_tester import StressTester
import pandas as pd

def full_risk_assessment(returns_df, weights, portfolio_value):
    """
    Comprehensive risk assessment.

    Args:
        returns_df: DataFrame with asset returns
        weights: Dict of asset weights
        portfolio_value: Portfolio value (EUR)

    Returns:
        dict: Comprehensive risk assessment results
    """
    results = {}

    # 1. Calculate portfolio returns
    weights_array = [weights[col] for col in returns_df.columns]
    portfolio_returns = returns_df.dot(weights_array)

    # 2. VaR Calculations (multiple methods)
    results["var"] = {
        "historical_95": historical_var(portfolio_returns, alpha=0.05),
        "parametric_95": parametric_var(portfolio_returns, alpha=0.05),
        "ewma_95": ewma_var(portfolio_returns, alpha=0.05, lbda=0.94),
        "historical_99": historical_var(portfolio_returns, alpha=0.01),
        "parametric_99": parametric_var(portfolio_returns, alpha=0.01),
    }

    # 3. Component VaR (Attribution)
    var_engine = ParametricVaR(ParametricVaRConfig(confidence_level=0.95))
    cov_estimator = CovarianceEstimator(CovarianceEstimatorConfig(method="sample"))
    calc = ComponentVaRCalculator(cov_estimator, var_engine)

    attribution = calc.calculate(returns_df, weights, portfolio_value)
    results["attribution"] = {
        "total_var": attribution.total_var,
        "component_var": attribution.component_var.to_dict(),
        "contribution_pct": attribution.contribution_pct.to_dict(),
    }

    # 4. Monte Carlo VaR
    mc_config = MonteCarloVaRConfig(
        confidence_level=0.95, n_simulations=10_000, method="normal", seed=42
    )
    mc_calc = MonteCarloVaRCalculator(mc_config)
    mc_result = mc_calc.calculate(returns_df)
    results["monte_carlo"] = {
        "var_95": mc_result.var_95,
        "cvar_95": mc_result.cvar_95,
    }

    # 5. Stress Testing
    stress_tester = StressTester(scenarios_dir="data/scenarios")
    stress_results = []
    for scenario in stress_tester.scenarios[:5]:  # First 5 scenarios
        stress_result = stress_tester.run_stress(
            portfolio_weights=weights,
            portfolio_value=portfolio_value,
            scenario_name=scenario.name
        )
        stress_results.append({
            "scenario": scenario.name,
            "loss_pct": stress_result.loss_pct
        })
    results["stress_tests"] = stress_results

    return results

# Usage
returns_df = pd.DataFrame({...})
weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
portfolio_value = 100_000

assessment = full_risk_assessment(returns_df, weights, portfolio_value)

# Print summary
print("=" * 70)
print("FULL RISK ASSESSMENT")
print("=" * 70)
print(f"\nPortfolio Value: €{portfolio_value:,}")
print("\n1. VaR Estimates (95%):")
for method, value in assessment["var"].items():
    if "95" in method:
        print(f"   {method}: {value:.4f}")

print("\n2. Component VaR:")
for asset, comp_var in assessment["attribution"]["component_var"].items():
    contrib = assessment["attribution"]["contribution_pct"][asset]
    print(f"   {asset}: €{comp_var:,.2f} ({contrib:.1f}%)")

print(f"\n3. Monte Carlo VaR (95%): {assessment['monte_carlo']['var_95']:.4f}")
print(f"   Monte Carlo CVaR (95%): {assessment['monte_carlo']['cvar_95']:.4f}")

print("\n4. Stress Test Results:")
for stress in assessment["stress_tests"]:
    print(f"   {stress['scenario']}: {stress['loss_pct']:.2f}%")
```

**Expected Output:**
```
======================================================================
FULL RISK ASSESSMENT
======================================================================

Portfolio Value: €100,000

1. VaR Estimates (95%):
   historical_95: 0.0412
   parametric_95: 0.0398
   ewma_95: 0.0421

2. Component VaR:
   BTC: €2,845.12 (68.5%)
   ETH: €945.67 (22.8%)
   SOL: €362.34 (8.7%)

3. Monte Carlo VaR (95%): 0.0405
   Monte Carlo CVaR (95%): 0.0567

4. Stress Test Results:
   COVID-19 Crash March 2020: -45.23%
   China Ban May 2021: -35.67%
   LUNA Collapse May 2022: -28.45%
   FTX Collapse Nov 2022: -18.90%
   Bear Market 2018: -62.34%
```

---

## Component Integration

### VaR Methods

**Available Methods:**
- `historical_var()` - Non-parametric, empirical quantile
- `parametric_var()` - Normal distribution assumption
- `ewma_var()` - Exponentially weighted moving average
- `cornish_fisher_var()` - Adjusts for skewness/kurtosis

**When to Use:**
- **Historical VaR:** Simple, no distribution assumption, good for stable markets
- **Parametric VaR:** Fast, smooth, good for normal-like distributions
- **EWMA VaR:** Adaptive, weights recent data more, good for changing volatility
- **Cornish-Fisher VaR:** Accounts for fat tails, good for non-normal distributions

**Example - Comparing Methods:**

```python
from src.risk.var import historical_var, parametric_var, ewma_var, cornish_fisher_var
import pandas as pd

returns = pd.Series([...])  # Your returns

var_hist = historical_var(returns, alpha=0.05)
var_param = parametric_var(returns, alpha=0.05)
var_ewma = ewma_var(returns, alpha=0.05, lbda=0.94)
var_cf = cornish_fisher_var(returns, alpha=0.05)

print(f"Historical:     {var_hist:.4f}")
print(f"Parametric:     {var_param:.4f}")
print(f"EWMA:           {var_ewma:.4f}")
print(f"Cornish-Fisher: {var_cf:.4f}")
```

---

### VaR Validation

**Components:**
1. **Kupiec POF Test** - Statistical test for breach rate
2. **Basel Traffic Light** - Regulatory classification
3. **Breach Analysis** - Pattern detection (clustering, gaps)

**Usage:**

```python
from src.risk.validation import kupiec_pof_test, basel_traffic_light, analyze_breaches
import pandas as pd

# Detect breaches
var_series = pd.Series([...])  # Your VaR estimates
returns = pd.Series([...])  # Realized returns
realized_losses = -returns
breaches = realized_losses > var_series

# 1. Kupiec POF Test
kupiec_result = kupiec_pof_test(
    n_observations=len(breaches),
    n_breaches=int(breaches.sum()),
    confidence_level=0.95
)

print(f"Kupiec Test: {kupiec_result.result}")
print(f"p-value: {kupiec_result.p_value:.4f}")

# 2. Basel Traffic Light
traffic_result = basel_traffic_light(
    n_breaches=int(breaches.sum()),
    n_observations=len(breaches),
    confidence_level=0.95
)

print(f"Basel Zone: {traffic_result.color}")

# 3. Breach Analysis (if breaches occurred)
if breaches.sum() > 0:
    breach_dates = returns.index[breaches]
    analysis = analyze_breaches(breach_dates)
    print(f"Max consecutive breaches: {analysis.max_consecutive}")
    print(f"Average gap: {analysis.avg_gap_days:.1f} days")
```

---

### Component VaR (Attribution)

**Use Cases:**
- Identify risk concentration
- Portfolio optimization
- Risk budgeting
- Rebalancing decisions

**Example - Incremental VaR:**

```python
from src.risk.component_var import calculate_incremental_var, ComponentVaRCalculator
from src.risk.parametric_var import ParametricVaR, ParametricVaRConfig
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
import pandas as pd

# Setup
returns_df = pd.DataFrame({...})
weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
portfolio_value = 100_000

var_engine = ParametricVaR(ParametricVaRConfig(confidence_level=0.95))
cov_estimator = CovarianceEstimator(CovarianceEstimatorConfig(method="sample"))
calculator = ComponentVaRCalculator(cov_estimator, var_engine)

# Calculate incremental VaR for SOL
incremental_result = calculate_incremental_var(
    calculator=calculator,
    returns_df=returns_df,
    weights=weights,
    asset_name="SOL",
    portfolio_value=portfolio_value
)

print(f"VaR with SOL: €{incremental_result.var_with_asset:,.2f}")
print(f"VaR without SOL: €{incremental_result.var_without_asset:,.2f}")
print(f"Incremental VaR: €{incremental_result.incremental_var:,.2f}")
print(f"Change: {incremental_result.pct_change:.2f}%")
```

---

## Configuration

### Config-Driven Initialization

**Example Config (`config.toml`):**

```toml
[risk]
confidence_level = 0.95
window = 252

[risk.covariance]
method = "sample"  # or "ledoit_wolf"

[risk.monte_carlo]
n_simulations = 10000
method = "normal"  # or "bootstrap", "studentt"
seed = 42

[risk.stress_test]
scenarios_dir = "data/scenarios"
```

**Loading from Config:**

```python
from src.core.peak_config import load_config

cfg = load_config()

# Access risk config
confidence_level = cfg.get("risk", {}).get("confidence_level", 0.95)
window = cfg.get("risk", {}).get("window", 252)

print(f"Confidence Level: {confidence_level}")
print(f"Window: {window}")
```

---

## Error Handling

### Graceful Degradation

**Example:**

```python
from src.risk.validation import run_var_backtest
import pandas as pd

def safe_backtest(returns, var_series, confidence_level=0.95):
    """
    Run backtest with error handling.
    """
    try:
        result = run_var_backtest(
            returns=returns,
            var_series=var_series,
            confidence_level=confidence_level
        )
        return result, None
    except ValueError as e:
        return None, f"ValueError: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"

# Usage
returns = pd.Series([...])
var_series = pd.Series([...])

result, error = safe_backtest(returns, var_series)

if result:
    print(f"✅ Backtest successful: {result.kupiec.result}")
else:
    print(f"❌ Backtest failed: {error}")
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: Empty returns` | No data provided | Check data loading |
| `ValueError: Misaligned indices` | Returns & VaR indices don't match | Align with `pd.Series.reindex()` |
| `ValueError: portfolio_value must be positive` | Invalid portfolio value | Check input validation |
| `KeyError: asset not found` | Asset missing from returns_df | Check column names |

---

## Performance

### Optimization Tips

1. **Vectorization:** Use numpy/pandas operations instead of loops
2. **Caching:** Cache covariance matrices for repeated calculations
3. **Sample Size:** Reduce simulation count for quick estimates

**Example - Caching Covariance:**

```python
from src.risk.covariance import CovarianceEstimator, CovarianceEstimatorConfig
import pandas as pd

# Initialize estimator
cov_estimator = CovarianceEstimator(CovarianceEstimatorConfig(method="sample"))

# Calculate once
returns_df = pd.DataFrame({...})
cov_matrix = cov_estimator.estimate(returns_df)

# Reuse for multiple calculations
from src.risk.parametric_var import portfolio_sigma_from_cov
import numpy as np

weights1 = np.array([0.5, 0.3, 0.2])
sigma1 = portfolio_sigma_from_cov(cov_matrix, weights1)

weights2 = np.array([0.6, 0.3, 0.1])
sigma2 = portfolio_sigma_from_cov(cov_matrix, weights2)
```

### Performance Benchmarks

| Operation | Sample Size | Time | Notes |
|-----------|-------------|------|-------|
| Historical VaR | 250 | <1ms | Very fast |
| Parametric VaR | 250 | <1ms | Very fast |
| Component VaR | 250 x 3 assets | <10ms | Fast |
| Monte Carlo (10k) | 250 x 3 assets | ~50ms | Moderate |
| Stress Testing (5 scenarios) | - | <20ms | Fast |

---

## Troubleshooting

### Issue: "All NaN returns"

**Cause:** Returns series contains only NaN values.

**Solution:**
```python
returns = returns.dropna()  # Remove NaNs before calculation
```

---

### Issue: "Euler property violated"

**Cause:** Component VaR sum doesn't equal total VaR (within tolerance).

**Solution:**
- Check that weights sum to 1.0
- Verify covariance matrix is positive semi-definite
- Increase tolerance if rounding errors

```python
# Check weights
weights_sum = sum(weights.values())
assert abs(weights_sum - 1.0) < 1e-6, f"Weights sum to {weights_sum}, not 1.0"
```

---

### Issue: "Kupiec test always rejects"

**Cause:** VaR model is mis-specified or test period is too short.

**Solution:**
- Use longer backtest period (250+ observations)
- Try different VaR methods
- Check if returns distribution has changed

---

## Summary

Dieser Guide zeigt, wie die Risk Layer Komponenten integriert werden:

✅ **VaR Calculation** - Multiple methods verfügbar  
✅ **VaR Validation** - Kupiec + Basel tests  
✅ **Component VaR** - Risk attribution  
✅ **Monte Carlo** - Simulation-based VaR  
✅ **Stress Testing** - Historical scenarios  
✅ **Full Assessment** - Alle Komponenten zusammen

**Nächste Schritte:**
1. Siehe [Examples Guide](EXAMPLES.md) für weitere Code-Beispiele
2. Siehe [API Reference](README.md) für Details zu jedem Modul
3. Siehe [Tests](../../tests/risk/) für weitere Usage-Beispiele

---

**Dokumentation Version:** 1.0  
**Letzte Aktualisierung:** 2025-12-28  
**Agent:** A6 (Integration & Documentation)
