# VaR Gate Runbook

## Overview

The **VaR Gate** is a portfolio-level risk control that evaluates Value-at-Risk (VaR) against configured thresholds before allowing trades.

**Key characteristics:**
- **Portfolio-level**: Evaluates overall portfolio risk, not individual positions
- **Safe defaults**: Missing data → OK (not applicable)
- **Flexible methods**: Parametric (fast) or Historical (non-parametric)
- **Warning thresholds**: Optional early warning before blocking

## What is VaR?

Value-at-Risk (VaR) answers: *"What is the maximum loss I can expect with X% confidence over Y days?"*

**Example:**
- 95% 1-day VaR = 2.5% means: "With 95% confidence, I won't lose more than 2.5% tomorrow"
- Or inversely: "There's a 5% chance I'll lose more than 2.5% tomorrow"

## VaR Methods

### 1. Parametric VaR (Default)
- **Assumption**: Returns are normally distributed
- **Formula**: `VaR = z_α * σ_portfolio * sqrt(horizon)`
- **Pros**: Fast, smooth, works with limited data
- **Cons**: Underestimates tail risk (fat tails)
- **Best for**: Short horizons (1-5 days), stable markets

### 2. Historical VaR
- **Assumption**: None (uses empirical distribution)
- **Formula**: `VaR = -quantile(returns, 1 - confidence)`
- **Pros**: No distribution assumption, captures actual tail behavior
- **Cons**: Requires more data (100+ bars), backward-looking
- **Best for**: Sufficient historical data, non-normal returns

## Configuration

### Location
VaR Gate configuration lives in your main config file under `[risk.var_gate]`.

### Example Configuration
```toml
[risk.var_gate]
enabled = true
method = "parametric"      # or "historical"
confidence = 0.95          # 95% confidence level
horizon_days = 1           # 1-day horizon
max_var_pct = 0.03         # 3% block threshold
warn_var_pct = 0.02        # 2% warning threshold (optional)
```

See `config/risk_var_gate_example.toml` for more examples.

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable VaR gate |
| `method` | str | `"parametric"` | VaR method: "parametric" or "historical" |
| `confidence` | float | `0.95` | Confidence level (e.g., 0.95 = 95%) |
| `horizon_days` | int | `1` | Risk horizon in days |
| `max_var_pct` | float | `0.03` | Block threshold (3% = block if VaR ≥ 3%) |
| `warn_var_pct` | float | `None` | Warning threshold (optional) |

## How It Works

### Evaluation Flow

```
Order → RiskGate
  ↓
1. Kill Switch (P0, always first)
  ↓
2. VaR Gate (P1, portfolio-level)
  ↓
3. Order Validation (basic checks)
  ↓
Decision (ALLOW / WARN / BLOCK)
```

### Input Requirements

VaR Gate needs these inputs in the `context`:
- `returns_df`: pandas DataFrame with asset returns (rows=time, columns=assets)
- `weights`: dict or array with portfolio weights (e.g., `{"BTC": 0.6, "ETH": 0.4}`)

**If missing:** VaR Gate returns OK (not applicable) - safe default.

### Thresholds

**Block Threshold (`max_var_pct`):**
- If `VaR >= max_var_pct` → **BLOCK** order
- Violation code: `VAR_LIMIT_EXCEEDED`

**Warning Threshold (`warn_var_pct`, optional):**
- If `warn_var_pct <= VaR < max_var_pct` → **WARN** (allow but flag)
- Violation code: `VAR_NEAR_LIMIT`

## Usage Examples

### Basic Usage
```python
from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate
import pandas as pd

cfg = PeakConfig.from_file("config/config.toml")
gate = RiskGate(cfg)

# Prepare context with VaR inputs
returns_df = pd.DataFrame({
    "BTC": [0.01, -0.02, 0.03, -0.01],
    "ETH": [0.02, -0.01, 0.02, 0.01]
})
weights = {"BTC": 0.6, "ETH": 0.4}

order = {"symbol": "BTCUSDT", "qty": 1.0}
context = {"returns_df": returns_df, "weights": weights}

result = gate.evaluate(order, context)
print(f"Allowed: {result.decision.allowed}")
print(f"Reason: {result.decision.reason}")
```

### Check VaR Without Placing Order
```python
# Get VaR gate status directly
from src.risk_layer.var_gate import VaRGate

var_gate = VaRGate(cfg)
context = {"returns_df": returns_df, "weights": weights}

status = var_gate.evaluate(context)
print(f"VaR: {status.var_pct:.2%}")
print(f"Severity: {status.severity}")
print(f"Threshold: {status.threshold_block:.2%}")
```

## Audit Logs

All VaR evaluations are logged in the risk audit log.

### Audit Structure
```json
{
  "timestamp_utc": "2025-12-25T12:00:00Z",
  "decision": {...},
  "kill_switch": {...},
  "var_gate": {
    "enabled": true,
    "result": {
      "severity": "OK",
      "reason": "VaR 1.85% within limits",
      "var_pct": 0.0185,
      "threshold_block": 0.03,
      "threshold_warn": 0.02,
      "confidence": 0.95,
      "horizon_days": 1,
      "method": "parametric",
      "inputs_available": true,
      "timestamp_utc": "2025-12-25T12:00:00Z"
    }
  },
  "order": {...},
  "context": {...}
}
```

## Troubleshooting

### VaR Gate Not Blocking High-Risk Orders

**Check:**
1. Is VaR gate enabled? `risk.var_gate.enabled = true`
2. Are inputs provided? Check `context` has `returns_df` and `weights`
3. Is threshold too high? Check `max_var_pct` value
4. Is data sufficient? Parametric needs 2+ bars, Historical needs 100+ bars

**Debug:**
```python
# Check VaR gate status
status = var_gate.evaluate(context)
print(f"Inputs available: {status.inputs_available}")
print(f"VaR: {status.var_pct}")
print(f"Threshold: {status.threshold_block}")
```

### VaR Calculation Fails

**Safe behavior:** If VaR calculation fails, gate returns OK (safe default) and logs warning.

**Common causes:**
- Empty returns DataFrame
- Zero volatility (all returns = 0)
- Mismatched weights/returns columns
- Insufficient data for historical VaR

**Fix:**
- Ensure returns_df has at least 2 rows (parametric) or 100+ rows (historical)
- Check that weights keys match returns_df columns
- Verify data quality (no all-NaN columns)

### VaR Too Conservative / Too Loose

**Adjust thresholds:**
```toml
# More conservative (block earlier)
max_var_pct = 0.02  # 2% instead of 3%

# Less conservative (allow more risk)
max_var_pct = 0.05  # 5% instead of 3%
```

**Adjust confidence:**
```toml
# More conservative (higher VaR)
confidence = 0.99  # 99% instead of 95%

# Less conservative (lower VaR)
confidence = 0.90  # 90% instead of 95%
```

## Best Practices

### 1. Start Conservative
- Begin with low thresholds (e.g., 2-3% for crypto)
- Monitor false positive rate
- Gradually adjust based on strategy risk profile

### 2. Use Warning Thresholds
```toml
max_var_pct = 0.03   # Hard limit
warn_var_pct = 0.02  # Early warning
```
- Alerts you before hitting hard limit
- Allows proactive risk management

### 3. Match Method to Data
- **Parametric**: Good for limited data, stable markets
- **Historical**: Better for fat tails, sufficient data

### 4. Monitor VaR Trends
- Track VaR over time in dashboards
- Alert on sustained high VaR (even if below threshold)
- Investigate sudden VaR spikes

### 5. Combine with Kill Switch
- Kill Switch: Account-level emergency stop (daily loss, drawdown)
- VaR Gate: Portfolio-level forward-looking risk
- Both provide complementary protection

## Configuration Profiles

### Conservative (Low Risk Tolerance)
```toml
[risk.var_gate]
enabled = true
method = "parametric"
confidence = 0.99      # 99% confidence
horizon_days = 1
max_var_pct = 0.02     # 2% limit
warn_var_pct = 0.015   # 1.5% warning
```

### Moderate (Balanced)
```toml
[risk.var_gate]
enabled = true
method = "parametric"
confidence = 0.95      # 95% confidence
horizon_days = 1
max_var_pct = 0.03     # 3% limit
warn_var_pct = 0.02    # 2% warning
```

### Aggressive (High Risk Tolerance)
```toml
[risk.var_gate]
enabled = true
method = "historical"  # Captures actual tail behavior
confidence = 0.95
horizon_days = 1
max_var_pct = 0.05     # 5% limit
warn_var_pct = null    # No warning
```

## Testing

### Unit Tests
```bash
pytest -v tests/risk_layer/test_var_gate.py
```

### Integration Tests
```bash
pytest -v tests/risk_layer/test_risk_gate.py -k var_gate
```

### Manual Smoke Test
```python
from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate
import pandas as pd
import numpy as np

cfg = PeakConfig.from_file("config/config.toml")
gate = RiskGate(cfg)

# Test 1: Low volatility → should allow
np.random.seed(42)
low_vol = pd.DataFrame({
    "BTC": np.random.normal(0, 0.01, 100),
    "ETH": np.random.normal(0, 0.01, 100)
})
order = {"symbol": "BTCUSDT", "qty": 1.0}
context = {"returns_df": low_vol, "weights": {"BTC": 0.5, "ETH": 0.5}}
result = gate.evaluate(order, context)
assert result.decision.allowed, "Low vol should allow"

# Test 2: High volatility → should block
high_vol = pd.DataFrame({
    "BTC": np.random.normal(0, 0.10, 100),
    "ETH": np.random.normal(0, 0.12, 100)
})
context = {"returns_df": high_vol, "weights": {"BTC": 0.5, "ETH": 0.5}}
result = gate.evaluate(order, context)
assert not result.decision.allowed, "High vol should block"

print("✅ All manual smoke tests passed")
```

## Related Documentation

- `docs/risk/KILL_SWITCH_RUNBOOK.md`: Kill Switch operator guide
- `docs/risk/RISK_METRICS_SCHEMA.md`: Metrics schema reference
- `src/risk_layer/var_backtest/`: VaR validation and backtesting implementation
- `src/risk/portfolio_var.py`: Underlying VaR calculations

## Support

For questions or issues:
1. Check this runbook
2. Review test cases in `tests/risk_layer/`
3. Inspect audit logs: `logs&#47;risk_audit.jsonl`
4. Review code documentation in source files
