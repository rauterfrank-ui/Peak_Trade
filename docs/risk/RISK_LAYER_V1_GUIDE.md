# Risk Layer v1.0 - User Guide

**Version:** 1.0  
**Date:** 2025-12-28  
**Agent:** A6 (Integration & Documentation)

---

## Overview

Risk Layer v1.0 provides comprehensive portfolio risk management capabilities for Peak_Trade, including:

- **VaR/CVaR Calculation:** Multiple methods (Historical, Parametric, Cornish-Fisher, EWMA)
- **Component VaR:** Risk attribution and decomposition
- **VaR Backtesting:** Statistical validation (Kupiec POF, Christoffersen, Basel Traffic Light)
- **Monte Carlo VaR:** Simulation-based risk estimation
- **Stress Testing:** Historical scenarios and reverse stress testing

---

## Quick Start

### 1. Configuration

Add to your `config.toml`:

```toml
[risk_layer_v1]
enabled = true

[risk_layer_v1.var]
enabled = true
methods = ["historical", "parametric", "ewma"]
confidence_level = 0.95
window = 252

[risk_layer_v1.component_var]
enabled = true

[risk_layer_v1.monte_carlo]
enabled = true
n_simulations = 10000
method = "normal"
seed = 42

[risk_layer_v1.stress_test]
enabled = true
scenarios_dir = "data/scenarios"

[risk_layer_v1.backtest]
enabled = false
```

### 2. Basic Usage

```python
from src.risk import RiskLayerManager
from src.core.peak_config import load_config
import pandas as pd

# Load config
config = load_config()

# Initialize Risk Layer Manager
manager = RiskLayerManager(config)

# Prepare data
returns_df = pd.DataFrame({
    "BTC-EUR": [...],  # Historical returns
    "ETH-EUR": [...],
})

weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
portfolio_value = 100000

# Run full risk assessment
assessment = manager.full_risk_assessment(
    returns_df=returns_df,
    weights=weights,
    portfolio_value=portfolio_value,
    alpha=0.05  # 95% VaR
)

# Print results
print(f"VaR (Historical): ${assessment.var['historical']:,.2f}")
print(f"CVaR (Historical): ${assessment.cvar['historical']:,.2f}")

# Generate report
report = manager.generate_report(assessment, format="markdown")
print(report)
```

---

## Components

### 1. VaR/CVaR Calculation

**Methods:**
- `historical`: Empirical quantile of historical returns
- `parametric`: Assumes normal distribution
- `cornish_fisher`: Adjusts for skewness and kurtosis
- `ewma`: Exponentially weighted moving average

**Usage:**
```python
from src.risk import historical_var, historical_cvar

returns = pd.Series([...])
var = historical_var(returns, alpha=0.05)  # 95% VaR
cvar = historical_cvar(returns, alpha=0.05)  # Expected Shortfall
```

**Properties:**
- VaR is always positive (represents loss)
- CVaR >= VaR (tail risk always greater)
- More data → better estimates

---

### 2. Component VaR

**Risk Attribution:**
- Marginal VaR: Risk contribution of each asset
- Incremental VaR: VaR change when adding/removing asset
- Diversification Benefit: Risk reduction from diversification

**Usage:**
```python
from src.risk import ComponentVaRCalculator

calc = ComponentVaRCalculator()
result = calc.calculate(
    returns=returns_df,
    weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    portfolio_value=100000,
    alpha=0.05
)

print(f"Portfolio VaR: ${result.portfolio_var:,.2f}")
for asset, contrib in result.component_var.items():
    print(f"{asset}: ${contrib:,.2f}")
```

---

### 3. Monte Carlo VaR

**Simulation Methods:**
- `bootstrap`: Resample historical returns
- `normal`: Multivariate normal distribution
- `student_t`: Student-t distribution (heavier tails)

**Usage:**
```python
from src.risk import MonteCarloVaRCalculator, MonteCarloVaRConfig

config = MonteCarloVaRConfig(
    n_simulations=10000,
    method="normal",
    seed=42
)

calc = MonteCarloVaRCalculator(returns_df, config)
result = calc.calculate(
    weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    portfolio_value=100000
)

print(f"MC VaR: ${result.var:,.2f}")
print(f"MC CVaR: ${result.cvar:,.2f}")
```

**Features:**
- Deterministic (same seed → same results)
- Horizon scaling (multi-day VaR)
- Correlation stress testing
- Equity path simulation

---

### 4. VaR Backtesting

**Statistical Tests:**
- **Kupiec POF:** Tests if violation rate matches expected
- **Christoffersen Independence:** Tests if violations are clustered
- **Basel Traffic Light:** Classifies model into GREEN/YELLOW/RED zones

**Usage:**
```python
from src.risk_layer.var_backtest import VaRBacktestRunner

runner = VaRBacktestRunner(confidence_level=0.99)
result = runner.run(
    returns=portfolio_returns,
    var_estimates=var_series,
    symbol="BTC/EUR"
)

print(f"Violations: {result.kupiec.n_violations}")
print(f"p-value: {result.kupiec.p_value:.4f}")
print(f"Result: {result.kupiec.result.value}")
```

---

### 5. Stress Testing

**Historical Scenarios:**
- COVID-19 Crash (March 2020): BTC -50%, ETH -60%
- China Mining Ban (May 2021): BTC -35%, ETH -40%
- Terra/LUNA Collapse (May 2022): BTC -15%, ETH -25%, SOL -40%
- FTX Collapse (November 2022): BTC -20%, ETH -25%, SOL -55%
- Crypto Winter 2018: BTC -85%, ETH -90%

**Usage:**
```python
from src.risk import StressTester

tester = StressTester(scenarios_dir="data/scenarios")

# Run all scenarios
results = tester.run_all_scenarios(
    portfolio_weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    portfolio_value=100000
)

for result in results:
    print(f"{result.scenario_name}: {result.portfolio_loss_pct:.2%} loss")

# Reverse stress test
reverse_result = tester.reverse_stress(
    portfolio_weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    target_loss_pct=0.20  # 20% loss
)

print(f"Uniform shock needed: {reverse_result.uniform_shock:.2%}")
print(f"BTC-specific shock: {reverse_result.btc_shock:.2%}")
```

---

## Configuration Reference

### Full Config Example

```toml
[risk_layer_v1]
enabled = true  # Master switch

[risk_layer_v1.var]
enabled = true
methods = ["historical", "parametric", "cornish_fisher", "ewma"]
confidence_level = 0.95  # 95% VaR
window = 252  # Historical window
min_obs = 20  # Minimum observations

[risk_layer_v1.component_var]
enabled = true

[risk_layer_v1.monte_carlo]
enabled = true
n_simulations = 10000
method = "normal"  # or "bootstrap", "student_t"
seed = 42
horizon_days = 1
student_t_df = 5  # For student_t method
correlation_stress_multiplier = 1.0  # 1.0 = no stress

[risk_layer_v1.stress_test]
enabled = true
scenarios_dir = "data/scenarios"

[risk_layer_v1.backtest]
enabled = false
confidence_level = 0.99
significance_level = 0.05
min_observations = 250
```

---

## Best Practices

### 1. Data Hygiene
- Remove NaNs from returns
- Ensure sufficient historical data (min 20 observations)
- Align asset returns by date

### 2. VaR Method Selection
- **Historical:** No assumptions, but limited by history
- **Parametric:** Fast, assumes normal distribution
- **Cornish-Fisher:** Better for skewed distributions
- **EWMA:** Gives more weight to recent data

### 3. Portfolio Construction
- Ensure weights sum to 1.0
- Match weight keys with returns columns
- Consider diversification benefits

### 4. Stress Testing
- Run all historical scenarios regularly
- Use reverse stress for target loss planning
- Update scenarios with new events

### 5. Backtesting
- Validate VaR models with historical data
- Monitor Basel Traffic Light zones
- Recalibrate if in YELLOW/RED zones

---

## Troubleshooting

### Common Issues

#### 1. "Risk Layer v1.0 disabled in config"
**Solution:** Set `risk_layer_v1.enabled = true` in `config.toml`

#### 2. "Weights must sum to 1.0"
**Solution:** Normalize weights: `weights = {k: v&#47;sum(weights.values()) for k, v in weights.items()}`

#### 3. "Need at least 2 observations"
**Solution:** Ensure sufficient historical returns data

#### 4. "Stress Tester initialization failed"
**Solution:** Check that `data&#47;scenarios&#47;` directory exists with JSON files

#### 5. Import Errors
**Solution:** Install dependencies: `pip install pandas numpy scipy`

---

## Performance Tips

### 1. Monte Carlo Simulations
- Use fewer simulations for faster results (1000-5000)
- Use `seed` for deterministic results
- Use `method="normal"` for speed (bootstrap is slower)

### 2. Component VaR
- Calculate only when needed (not every tick)
- Cache results for stable portfolios

### 3. Stress Testing
- Run scenarios periodically (not in real-time)
- Store results for reporting

---

## API Reference

See individual module documentation:

- VaR Calculation (planned)
- Component VaR (planned)
- VaR Backtesting (planned)
- Monte Carlo VaR (planned)
- Stress Testing (planned)

---

## Support

For issues or questions:
- Check [RISK_LAYER_OVERVIEW.md](RISK_LAYER_OVERVIEW.md) for architecture
- Review [RISK_LAYER_ALIGNMENT.md](RISK_LAYER_ALIGNMENT.md) for design decisions
- See [Examples](../../examples/) for code samples

---

**Last Updated:** 2025-12-28 by Agent A6
