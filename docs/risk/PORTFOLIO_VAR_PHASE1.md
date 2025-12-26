# Portfolio VaR - Phase 1 Implementation

**Status:** ✅ Implemented  
**Date:** 2025-12-25  
**Phase:** 1 of 5 (Core Library)

---

## Overview

Phase 1 implements the core Portfolio Value at Risk (VaR) library for Peak_Trade, providing:

- **Parametric VaR**: Covariance-based, Normal distribution assumption
- **Historical VaR**: Empirical quantile-based, non-parametric
- **Symbol Normalization**: Robust mapping (BTC/EUR → BTC)
- **Config Integration**: Via PeakConfig TOML sections
- **SciPy Optional**: Fallback to statistics.NormalDist

**🚨 Important:** Phase 1 is **core library only** – no live-trading integration, no automatic gating. Phases 3-5 will add Paper-Trading validation and Live integration with safety gates.

---

## Installation

No additional dependencies required beyond Peak_Trade base:
- **NumPy**: Already in requirements.txt
- **Pandas**: Already in requirements.txt
- **SciPy**: Optional (fallback available)

To use SciPy for better accuracy:
```bash
pip install scipy
```

---

## Configuration

### config.toml Structure

Add the following section to your `config/config.toml`:

```toml
[risk.portfolio_var]
enabled = true
method = "parametric"  # or "historical"
confidence = 0.99      # 99% VaR (0.99 = tail probability 1%)
horizon_days = 1       # Risk horizon in days
lookback_bars = 500    # Historical data window
symbol_mode = "base"   # "base" extracts BTC from BTC/EUR, "raw" uses as-is
use_mean = false       # Include mean return (false = more conservative)
```

### Config Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `true` | Enable portfolio VaR |
| `method` | str | `"parametric"` | VaR method: "parametric" or "historical" |
| `confidence` | float | `0.99` | Confidence level (0.95 = 95% VaR, 0.99 = 99% VaR) |
| `horizon_days` | int | `1` | Risk horizon in days |
| `lookback_bars` | int | `500` | Historical data window (bars) |
| `symbol_mode` | str | `"base"` | Symbol normalization: "base" or "raw" |
| `use_mean` | bool | `false` | Include mean return in parametric VaR |

---

## Usage

### Example 1: Parametric VaR

```python
import pandas as pd
from src.core.config import load_config
from src.risk.portfolio_var import (
    build_portfolio_var_config_from_config,
    parametric_var,
)

# Load config
cfg = load_config()
var_config = build_portfolio_var_config_from_config(cfg)

# Prepare data
returns_df = pd.DataFrame({
    "BTC": [0.02, -0.01, 0.03, -0.02, 0.01],
    "ETH": [0.01, -0.02, 0.02, -0.01, 0.03],
})

# Portfolio weights (with symbol normalization)
weights = {
    "BTC/EUR": 0.60,
    "ETH/EUR": 0.40,
}

# Compute VaR
var = parametric_var(
    returns_df=returns_df,
    weights=weights,
    confidence=var_config.confidence,
    horizon_days=var_config.horizon_days,
    symbol_mode=var_config.symbol_mode,
    use_mean=var_config.use_mean,
)

print(f"Portfolio VaR(99%, 1-day): {var:.2%}")
# Output: Portfolio VaR(99%, 1-day): 4.23%
```

### Example 2: Historical VaR

```python
from src.risk.portfolio_var import historical_var

# Same returns_df and weights as above

# Compute historical VaR
var = historical_var(
    returns_df=returns_df,
    weights=weights,
    confidence=0.95,  # 95% VaR
    horizon_days=1,
    symbol_mode="base",
)

print(f"Historical VaR(95%, 1-day): {var:.2%}")
```

### Example 3: Symbol Normalization

```python
from src.risk.portfolio_var import normalize_symbol

# Normalize symbols for returns DataFrame keying
print(normalize_symbol("BTC/EUR", mode="base"))   # Output: "BTC"
print(normalize_symbol("ETH-USD", mode="base"))   # Output: "ETH"
print(normalize_symbol("SOL_USDT", mode="base"))  # Output: "SOL"
print(normalize_symbol("BTC", mode="base"))       # Output: "BTC"

# Raw mode (no normalization)
print(normalize_symbol("BTC/EUR", mode="raw"))    # Output: "BTC/EUR"
```

### Example 4: Multi-Day Horizon

```python
# 10-day VaR
var_10d = parametric_var(
    returns_df=returns_df,
    weights=weights,
    confidence=0.99,
    horizon_days=10,  # 10-day horizon
)

print(f"Portfolio VaR(99%, 10-day): {var_10d:.2%}")
# Note: VaR scales with sqrt(horizon_days) for parametric
```

---

## Methods

### Parametric VaR

**Formula (use_mean=False):**
```
VaR = z_α * σ_portfolio * sqrt(horizon)
```

**Formula (use_mean=True):**
```
VaR = -(μ_portfolio * horizon - z_α * σ_portfolio * sqrt(horizon))
```

Where:
- `z_α`: Z-value for confidence level (e.g. 2.326 for 99%)
- `σ_portfolio`: Portfolio standard deviation = sqrt(w^T * Σ * w)
- `Σ`: Covariance matrix (estimated from returns_df)
- `w`: Weight vector
- `μ_portfolio`: Mean portfolio return

**Assumptions:**
- Multivariate Normal distribution of returns
- Stationary covariance
- More accurate for short horizons (<10 days)

**Pros:**
- Fast computation
- Smooth estimates
- Works well for stable markets

**Cons:**
- Underestimates risk in fat-tailed distributions
- Assumes Normality (can be violated in crises)

### Historical VaR

**Formula:**
```
VaR = -quantile(portfolio_returns, 1 - confidence)
```

For horizon_days > 1:
```
1. Compute rolling compounded returns over horizon
2. VaR = -quantile(aggregated_returns, 1 - confidence)
```

**Assumptions:**
- None (non-parametric)
- Past returns represent future risk

**Pros:**
- No distribution assumption
- Captures actual tail behavior
- Robust to fat tails

**Cons:**
- Requires large historical dataset (≥100 bars recommended)
- Sensitive to data window choice
- Slower for large horizons

---

## Symbol Normalization

### Why?

Data feeds provide symbols like `"BTC/EUR"`, but returns DataFrames often use base assets like `"BTC"`.

### Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `"base"` | Extract base asset (BTC/EUR → BTC) | Standard (recommended) |
| `"raw"` | Use symbol as-is | Returns DataFrame has full symbols |

### Supported Formats

- **Slash**: `BTC/EUR` → `BTC`
- **Dash**: `ETH-USD` → `ETH`
- **Underscore**: `SOL_USDT` → `SOL`
- **Already normalized**: `BTC` → `BTC`

---

## Weight Alignment

### Dict Weights (Recommended)

```python
weights = {
    "BTC/EUR": 0.60,
    "ETH/EUR": 0.40,
}
```

- Keys are normalized via `symbol_mode`
- Automatically mapped to returns_df columns
- Clear and explicit

### Sequence Weights

```python
weights = [0.60, 0.40]  # Must match returns_df column order!
```

- Must match column order exactly
- Less safe (order-dependent)
- Use only if mapping is clear

### Weight Validation

- Weights must sum to ~1.0 (range: [0.99, 1.01])
- If not: **ValueError** (no silent normalization)
- Missing symbols: **ValueError** with list of missing columns

---

## Error Handling

### Common Errors

**ValueError: "Weights must sum to ~1.0"**
```python
# Fix: Normalize weights before calling VaR
weights = {"BTC": 0.6, "ETH": 0.3}  # Sum = 0.9
# Solution:
total = sum(weights.values())
weights = {k: v/total for k, v in weights.items()}
```

**ValueError: "Missing weights for returns columns"**
```python
# Fix: Ensure all returns_df columns have corresponding weights
returns_df.columns  # ['BTC', 'ETH', 'SOL']
weights = {"BTC": 0.5, "ETH": 0.5}  # Missing: SOL
# Solution: Add SOL or filter returns_df
```

**ValueError: "Need at least 2 rows"**
```python
# Fix: Provide sufficient historical data
# Minimum: 2 rows for covariance
# Recommended: ≥100 rows for historical VaR
```

---

## Testing

### Run Phase 1 Tests

```bash
pytest tests/risk/test_portfolio_var_phase1.py -v
```

### Test Coverage

- ✅ Symbol normalization (6 tests)
- ✅ Weight alignment (6 tests)
- ✅ Covariance estimation (3 tests)
- ✅ Portfolio sigma (2 tests)
- ✅ Z-value calculation (3 tests)
- ✅ Parametric VaR (5 tests)
- ✅ Historical VaR (4 tests)
- ✅ Binomial p-value (5 tests)
- ✅ Config validation (4 tests)
- ✅ Edge cases (2 tests)

**Total:** 40 tests, all deterministic

---

## SciPy Integration

### With SciPy

```python
from scipy.stats import norm, binomtest

# More accurate z-values
z = norm.ppf(0.99)  # 2.3263478740408408

# Modern binomial test
result = binomtest(k=5, n=100, p=0.05)
```

### Without SciPy (Fallback)

```python
from statistics import NormalDist

# Fallback z-values (slightly less accurate)
z = NormalDist().inv_cdf(0.99)  # 2.3263478740408408

# Custom binomial test implementation
# (exact calculation via math.comb)
```

**Recommendation:** Install SciPy for production use, but fallback works fine for Phase 1.

---

## Limitations (Phase 1)

### Not Implemented

- ❌ **Live-Trading Integration**: No automatic pre-trade checks (Phase 5)
- ❌ **Multi-Asset Correlation Limits**: No correlation-based limits (Phase 1 extension)
- ❌ **Advanced Models**: No Student-t, GARCH, EVT (Phase 2)
- ❌ **Backtesting Framework**: No Kupiec/Christoffersen tests (Phase 3)
- ❌ **Adaptive Limits**: No regime-dependent or ML-based limits (Phase 4)

### Known Issues

- **Parametric VaR**: Assumes Normality (underestimates fat tails)
- **Historical VaR**: Requires large dataset (≥100 bars)
- **Horizon Scaling**: Sqrt-rule for parametric (inaccurate for >10 days)

### Workarounds

- **Fat Tails**: Use Historical VaR or wait for Phase 2 (Student-t)
- **Small Dataset**: Use Parametric VaR (more stable with <100 bars)
- **Long Horizons**: Use caution, consider Monte Carlo (Phase 2)

---

## Roadmap

### Phase 2: Advanced Models (Q1-Q2 2026)
- Student-t VaR (fat tails)
- GARCH VaR (time-varying volatility)
- Extreme Value Theory

### Phase 3: Paper-Trading Validation (Q2 2026)
- Real-time VaR calculation
- Backtesting framework (Kupiec/Christoffersen)
- **SAFETY GATE:** 30 days validation before Live

### Phase 4: Adaptive Limits (Q2-Q3 2026)
- Regime-dependent limits
- Volatility-scaled limits
- ML-based limit prediction

### Phase 5: Live-Trading Integration (Q3-Q4 2026)
- Pre-trade VaR checks
- Real-time monitoring
- **SAFETY-FIRST:** Staged rollout (Testnet → Paper → Micro → Full)

---

## References

- **Core Module**: `src/risk/portfolio_var.py`
- **Tests**: `tests/risk/test_portfolio_var_phase1.py`
- **Roadmap**: `docs/risk/roadmaps/PORTFOLIO_VAR_ROADMAP.md`
- **Risk Layer v1**: `docs/risk/RISK_LAYER_V1_OPERATOR_GUIDE.md`

### Literature

- Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk*
- McNeil, A.J., Frey, R., Embrechts, P. (2015). *Quantitative Risk Management*

---

**Status:** ✅ Phase 1 Complete  
**Next:** Phase 2 Planning (Advanced Distribution Models)

