# Risk Module (Legacy/Core)

**Location:** `src/risk/`  
**Purpose:** Core risk management for backtesting and portfolio analysis  
**Status:** Active (primarily for backtest/research workflows)

---

## Purpose

This module provides **core risk management functionality** for:
1. **Backtesting:** Risk metrics calculation (Sharpe, max DD, VaR, etc.)
2. **Portfolio Analysis:** Position sizing, risk limits
3. **Research:** Monte Carlo simulations, stress testing, component VaR

**Primary Use Cases:**
- Backtest risk metrics (Sharpe ratio, drawdown, win rate)
- Position sizing calculations (PositionSizer)
- Risk limit enforcement in backtest (RiskLimits)
- VaR and stress testing for portfolio analysis

---

## Relationship to `src/risk_layer/`

**Two Separate Systems (By Design):**

| Aspect | `src/risk/` (This Module) | `src/risk_layer/` |
|--------|---------------------------|-------------------|
| **Purpose** | Backtest/Research Risk | Live Trading Risk |
| **Context** | Offline analysis | Real-time trading |
| **Primary Use** | Metrics calculation | Order blocking |
| **Components** | VaR, Stress Test, Monte Carlo | Kill Switch, Alerting, Live Limits |
| **State** | Stateless (per-backtest) | Stateful (persistent) |

**Key Distinction:**
- **`src/risk/`** = "What risk did we take?" (post-hoc analysis)
- **`src/risk_layer/`** = "Should we take this risk now?" (pre-trade gate)

---

## Key Components

### PositionSizer (`position_sizer.py`)
Calculates position sizes based on risk parameters:
- Risk per trade (e.g., 2% of capital)
- Stop loss distance
- Max position size limits

**Used In:** Backtest engine, portfolio analysis

### RiskLimits (`risk_limits.py`)
Enforces risk limits in backtest:
- Max drawdown (%)
- Max daily loss
- Max position size (%)
- Equity floor

**Used In:** Backtest engine (pre-trade checks in simulation)

### VaR Calculation (`var.py`)
Value at Risk calculation for portfolio:
- Historical VaR
- Parametric VaR
- Component VaR (risk attribution)

**Used In:** Portfolio analysis, risk reporting

### Stress Testing (`stress_test.py`, `stress.py`)
Portfolio stress testing:
- Scenario analysis (e.g., 2008 crisis)
- Sensitivity analysis
- Correlation stress

**Used In:** Risk reporting, portfolio validation

### Monte Carlo (`monte_carlo.py`)
Monte Carlo simulation for:
- Portfolio robustness testing
- Path-dependent analysis
- Confidence intervals

**Used In:** Research, strategy validation

---

## When to Use This Module

**Use `src/risk/` for:**
- ✅ Backtest risk metrics (Sharpe, DD, VaR)
- ✅ Position sizing in backtest
- ✅ Portfolio risk analysis
- ✅ Research and strategy development
- ✅ Reporting and visualization

**Use `src/risk_layer/` for:**
- ✅ Live trading order gates
- ✅ Kill switch (emergency halt)
- ✅ Real-time risk monitoring
- ✅ Alert dispatching
- ✅ Operational risk management

---

## Migration Status

**No migration planned.** Both modules serve different purposes:
- `src/risk/` is for **analytical risk** (what happened, what could happen)
- `src/risk_layer/` is for **operational risk** (should we do this now)

**Overlap:** Some concepts (e.g., position limits) appear in both, but contexts differ:
- `src/risk/` enforces limits in **simulated backtest**
- `src/risk_layer/` enforces limits on **real orders**

---

## Dependencies

**Imports from this module:**
- `src.risk.PositionSizer` - Used in backtest engine
- `src.risk.RiskLimits` - Used in backtest engine
- `src.risk.calc_var` - Used in reporting

**Does NOT depend on:**
- `src/risk_layer/` - Completely independent

---

## Examples

### Position Sizing in Backtest

```python
from src.risk import PositionSizer, PositionSizerConfig

sizer = PositionSizer(PositionSizerConfig(
    risk_pct=0.02,  # 2% risk per trade
    max_position_pct=0.25  # Max 25% per position
))

position_request = PositionRequest(
    equity=10000,
    price=50000,
    stop_loss=48000,
    direction=1
)

size = sizer.calc_position_size(position_request)
print(f"Position size: {size}")
```

### VaR Calculation

```python
from src.risk import calc_var

returns = portfolio.returns
var_95 = calc_var(returns, confidence=0.95)
print(f"95% VaR: ${var_95:.2f}")
```

---

## Files in This Module

```
src/risk/
├── __init__.py
├── position_sizer.py       # Position sizing
├── risk_limits.py          # Risk limits (backtest)
├── var.py                  # VaR calculation
├── stress_test.py          # Stress testing
├── stress.py               # Additional stress tests
├── monte_carlo.py          # Monte Carlo simulation
├── component_var.py        # Component VaR
├── portfolio.py            # Portfolio risk metrics
├── enforcement.py          # Risk enforcement (backtest)
├── covariance.py           # Covariance estimation
└── validation/             # VaR validation (backtesting)
    ├── kupiec.py           # Kupiec POF test
    ├── traffic_light.py    # Basel traffic light
    └── backtest_runner.py  # VaR backtest runner
```

---

## For Live Trading

**Do NOT use this module directly for live trading order gates.**

Use `src/risk_layer/` instead:
- `src.risk_layer.kill_switch` - Emergency halt
- `src.live.risk_limits.LiveRiskLimits` - Live order checks

---

## Questions?

- **"Which module for live trading?"** → `src/risk_layer/`
- **"Which module for backtest metrics?"** → `src/risk/` (this module)
- **"Can I use both?"** → Yes! Use both in their respective contexts
- **"Are they integrated?"** → No, by design (separation of concerns)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-30 | 1.0 | Initial README for FND-0002 remediation |
