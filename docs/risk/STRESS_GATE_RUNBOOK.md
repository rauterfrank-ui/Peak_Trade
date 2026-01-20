# Stress Gate Runbook

## Overview

**Stress Gate** ist ein szenario-basiertes Risk Gate, das Portfolio-Positionen gegen deterministische Stress-Szenarien testet. Es evaluiert worst-case Verluste und blockiert oder warnt basierend auf konfigurierten Schwellenwerten.

**Position in der Risk Layer Hierarchie:**
```
KillSwitch → VaR Gate → Stress Gate → Order Validation
```

**Status:** ✅ Production-Ready (P1)

---

## Quick Reference

### Default Config

```toml
[risk.stress_gate]
enabled = true
max_stress_loss_pct = 0.04      # BLOCK bei -4% worst-case loss
warn_stress_loss_pct = 0.03     # WARN bei -3% worst-case loss

[[risk.stress_gate.scenarios]]
name = "equity_down_5pct"
description = "5% equity market decline"
shock_type = "return_shift"
shock_params = { shift = -0.05 }

[[risk.stress_gate.scenarios]]
name = "equity_down_10pct"
description = "10% equity market decline"
shock_type = "return_shift"
shock_params = { shift = -0.10 }

[[risk.stress_gate.scenarios]]
name = "vol_spike"
description = "Volatility spike (2x)"
shock_type = "vol_spike"
shock_params = { multiplier = 2.0 }
```

### Severity Levels

| Severity | Condition | Action |
|----------|-----------|--------|
| **OK** | `worst_case_loss_pct > -max_stress_loss_pct` | Allow order |
| **WARN** | `worst_case_loss_pct ≤ -warn_stress_loss_pct` | Allow with warning |
| **BLOCK** | `worst_case_loss_pct ≤ -max_stress_loss_pct` | Block order |

### Violation Codes

- `STRESS_LIMIT_EXCEEDED` (CRITICAL): Worst-case loss exceeds block threshold
- `STRESS_NEAR_LIMIT` (WARNING): Worst-case loss near block threshold

---

## How It Works

### 1. Inputs

Stress Gate benötigt folgende Inputs aus dem `context` dict:

```python
context = {
    "returns_df": pd.DataFrame,  # Asset returns (columns = assets)
    "weights": dict | list,       # Portfolio weights
}
```

### 2. Scenario Types

#### Return Shift

Verschiebt alle Returns um einen festen Betrag:

```toml
shock_type = "return_shift"
shock_params = { shift = -0.10 }  # -10% shift
```

**Calculation:**
```python
stressed_returns = original_returns + shift
```

#### Vol Spike

Skaliert Volatilität durch Multiplikation der demeaned returns:

```toml
shock_type = "vol_spike"
shock_params = { multiplier = 2.0 }  # 2x volatility
```

**Calculation:**
```python
mean = original_returns.mean()
demeaned = original_returns - mean
stressed_returns = (demeaned * multiplier) + mean
```

### 3. Worst-Case Evaluation

Für jedes Szenario:
1. Apply shock to returns
2. Calculate portfolio loss: `dot(weights, mean_stressed_returns)`
3. Track worst-case (most negative) loss

### 4. Threshold Check

```python
if worst_case_loss_pct <= -max_stress_loss_pct:
    return BLOCK
elif warn_stress_loss_pct and worst_case_loss_pct <= -warn_stress_loss_pct:
    return WARN
else:
    return OK
```

---

## Configuration Profiles

### Conservative (Low Risk Tolerance)

```toml
[risk.stress_gate]
enabled = true
max_stress_loss_pct = 0.02      # Block at -2%
warn_stress_loss_pct = 0.015    # Warn at -1.5%

[[risk.stress_gate.scenarios]]
name = "equity_down_3pct"
shock_type = "return_shift"
shock_params = { shift = -0.03 }

[[risk.stress_gate.scenarios]]
name = "equity_down_5pct"
shock_type = "return_shift"
shock_params = { shift = -0.05 }

[[risk.stress_gate.scenarios]]
name = "vol_spike_15x"
shock_type = "vol_spike"
shock_params = { multiplier = 1.5 }
```

### Moderate (Balanced)

```toml
[risk.stress_gate]
enabled = true
max_stress_loss_pct = 0.04      # Block at -4%
warn_stress_loss_pct = 0.03     # Warn at -3%

[[risk.stress_gate.scenarios]]
name = "equity_down_5pct"
shock_type = "return_shift"
shock_params = { shift = -0.05 }

[[risk.stress_gate.scenarios]]
name = "equity_down_10pct"
shock_type = "return_shift"
shock_params = { shift = -0.10 }

[[risk.stress_gate.scenarios]]
name = "vol_spike_2x"
shock_type = "vol_spike"
shock_params = { multiplier = 2.0 }
```

### Aggressive (High Risk Tolerance)

```toml
[risk.stress_gate]
enabled = true
max_stress_loss_pct = 0.08      # Block at -8%
warn_stress_loss_pct = 0.06     # Warn at -6%

[[risk.stress_gate.scenarios]]
name = "equity_down_10pct"
shock_type = "return_shift"
shock_params = { shift = -0.10 }

[[risk.stress_gate.scenarios]]
name = "equity_down_15pct"
shock_type = "return_shift"
shock_params = { shift = -0.15 }

[[risk.stress_gate.scenarios]]
name = "vol_spike_3x"
shock_type = "vol_spike"
shock_params = { multiplier = 3.0 }
```

---

## Operational Procedures

### Enable/Disable Stress Gate

**Enable:**
```toml
[risk.stress_gate]
enabled = true
```

**Disable:**
```toml
[risk.stress_gate]
enabled = false
```

**No restart required** - config is hot-reloadable.

### Adjust Thresholds

Edit `config/config.toml`:

```toml
[risk.stress_gate]
max_stress_loss_pct = 0.05      # Increase block threshold to -5%
warn_stress_loss_pct = 0.04     # Increase warn threshold to -4%
```

Save and reload config (or restart).

### Add Custom Scenarios

```toml
[[risk.stress_gate.scenarios]]
name = "crypto_crash"
description = "20% crypto market crash"
shock_type = "return_shift"
shock_params = { shift = -0.20 }

[[risk.stress_gate.scenarios]]
name = "extreme_vol"
description = "5x volatility spike"
shock_type = "vol_spike"
shock_params = { multiplier = 5.0 }
```

---

## Monitoring & Alerts

### Audit Log

Every evaluation is logged to `risk_audit.jsonl`:

```json
{
  "stress_gate": {
    "enabled": true,
    "result": {
      "severity": "WARN",
      "reason": "Stress loss -3.2% near limit (warn threshold -3.0%)",
      "worst_case_loss_pct": -0.032,
      "threshold_block": 0.04,
      "threshold_warn": 0.03,
      "triggered_scenarios": ["equity_down_10pct"],
      "scenarios_evaluated": 3,
      "inputs_available": true,
      "timestamp_utc": "2025-12-25T18:00:00Z"
    },
    "scenarios_meta": {
      "count": 3,
      "names": ["equity_down_5pct", "equity_down_10pct", "vol_spike"]
    }
  }
}
```

### Key Metrics to Monitor

1. **Block Rate**: Häufigkeit von `STRESS_LIMIT_EXCEEDED`
2. **Warn Rate**: Häufigkeit von `STRESS_NEAR_LIMIT`
3. **Worst-Case Loss Distribution**: Typische worst-case losses
4. **Triggered Scenarios**: Welche Szenarien am häufigsten worst-case sind

### Alert Conditions

Set up alerts for:

- **High Block Rate** (> 5% of orders): Thresholds ggf. zu streng
- **Repeated Blocks on Same Scenario**: Portfolio-Exposition zu einseitig
- **Sudden Spike in Worst-Case Loss**: Marktvolatilität gestiegen

---

## Troubleshooting

### Orders werden fälschlicherweise blockiert

**Symptom:** Stress Gate blockiert legitime Orders.

**Diagnosis:**
1. Check audit log for `worst_case_loss_pct`
2. Review triggered scenarios
3. Compare with current portfolio composition

**Fix:**
- **Option A**: Increase `max_stress_loss_pct` (höhere Risikotoleranz)
- **Option B**: Remove/modify aggressive scenarios
- **Option C**: Rebalance portfolio to reduce exposure

### Stress Gate läuft nicht

**Symptom:** `inputs_available: false` in audit log.

**Diagnosis:**
1. Check if `returns_df` and `weights` are provided in context
2. Verify DataFrame format

**Fix:**
Ensure context contains:
```python
context = {
    "returns_df": pd.DataFrame(...),
    "weights": {"BTC": 0.6, "ETH": 0.4},
}
```

### Worst-Case Loss unerwartet

**Symptom:** `worst_case_loss_pct` scheint falsch.

**Diagnosis:**
1. Check scenario definitions (shift amounts)
2. Verify portfolio mean returns
3. Manual calculation:
   ```python
   portfolio_mean = dot(weights, returns_df.mean())
   shocked_mean = portfolio_mean + shift
   ```

**Fix:**
- Review scenario parameters
- Validate returns data quality

---

## Integration

### Python API

```python
from src.risk_layer.stress_gate import StressGate
from src.core.peak_config import PeakConfig

cfg = PeakConfig.from_file("config/config.toml")
gate = StressGate(cfg)

context = {
    "returns_df": returns_df,
    "weights": {"BTC": 0.6, "ETH": 0.4},
}

status = gate.evaluate(context)

if status.severity == "BLOCK":
    print(f"Order blocked: {status.reason}")
elif status.severity == "WARN":
    print(f"Warning: {status.reason}")
else:
    print("Stress test passed")
```

### RiskGate Integration

Stress Gate ist automatisch in `RiskGate` integriert:

```python
from src.risk_layer.risk_gate import RiskGate

gate = RiskGate(cfg)
result = gate.evaluate(order, context)

# Stress Gate wird nach VaR Gate, vor Order Validation evaluiert
```

---

## Testing

### Unit Tests

```bash
pytest tests/risk_layer/test_stress_gate.py -v
```

### Integration Tests

```bash
pytest tests/risk_layer/test_risk_gate.py -k stress -v
```

### Manual Verification

```python
import pandas as pd
from src.core.peak_config import PeakConfig
from src.risk_layer.stress_gate import StressGate

# Setup
cfg = PeakConfig.from_dict({
    "risk": {
        "stress_gate": {
            "enabled": True,
            "max_stress_loss_pct": 0.04,
            "scenarios": [
                {
                    "name": "test_shock",
                    "shock_type": "return_shift",
                    "shock_params": {"shift": -0.10}
                }
            ]
        }
    }
})

gate = StressGate(cfg)

# Test case: Portfolio with +2% mean returns
returns_df = pd.DataFrame({"A": [0.02, 0.02, 0.02]})
weights = {"A": 1.0}

status = gate.evaluate({"returns_df": returns_df, "weights": weights})

# Expected: worst_case_loss_pct = 0.02 - 0.10 = -0.08 → BLOCK
assert status.severity == "BLOCK"
assert abs(status.worst_case_loss_pct - (-0.08)) < 0.001
print("✓ Manual verification passed")
```

---

## Safe Defaults

Stress Gate folgt dem **safe-by-default** Prinzip:

1. **Disabled → OK**: Wenn disabled, werden alle Orders erlaubt
2. **Missing inputs → OK**: Wenn returns/weights fehlen, nicht applicable
3. **Calculation error → OK**: Bei Fehler wird Order erlaubt (logged)

**Rationale:** Falsche Blocks (false positives) sind teurer als verpasste Blocks (false negatives) im Live-Trading.

---

## Version History

- **v1.0** (2025-12-25): Initial implementation
  - Return shift scenarios
  - Vol spike scenarios
  - Conservative/Moderate/Aggressive profiles
  - Full RiskGate integration
  - Comprehensive test coverage

---

## See Also

- [VAR_GATE_RUNBOOK.md](./VAR_GATE_RUNBOOK.md) - VaR Gate documentation
- [KILL_SWITCH_RUNBOOK.md](./KILL_SWITCH_RUNBOOK.md) - Kill Switch documentation
- [RISK_LAYER_V1_PRODUCTION_READY_REPORT.md](./RISK_LAYER_V1_PRODUCTION_READY_REPORT.md) - Risk Layer overview
