# Kill Switch Runbook

## Overview

The **Kill Switch** is a P0 safety mechanism in the Peak_Trade Risk Layer that immediately blocks all trading decisions when critical risk thresholds are exceeded.

**Key characteristics:**
- **Sticky behavior**: Once armed, stays armed until explicitly reset
- **Immediate blocking**: Takes precedence over all other validations
- **Metrics-driven**: Evaluates real-time risk metrics against configured thresholds

## What Does the Kill Switch Monitor?

The Kill Switch evaluates three categories of risk metrics:

### 1. Daily Loss (`daily_pnl_pct`)
- **Metric**: Daily PnL as a percentage (e.g., -0.06 = -6%)
- **Default threshold**: 5% daily loss (`-0.05`)
- **Triggers when**: `daily_pnl_pct <= -daily_loss_limit_pct`

### 2. Drawdown (`current_drawdown_pct`)
- **Metric**: Current drawdown from peak as percentage (e.g., 0.21 = 21% drawdown)
- **Default threshold**: 20% maximum drawdown (`0.20`)
- **Triggers when**: `current_drawdown_pct >= max_drawdown_pct`

### 3. Volatility (`realized_vol_pct`) [OPTIONAL]
- **Metric**: Realized volatility as percentage
- **Default threshold**: `None` (disabled by default)
- **Triggers when**: `realized_vol_pct >= max_volatility_pct` (if configured)

## Canonical Metrics Schema

The Kill Switch uses a **canonical metrics schema** for consistency and stability across the system.

### Supported Context Layouts

The metrics extraction is **tolerant** and supports multiple context layouts:

**1. Nested under `metrics` (recommended):**
```python
context = {
    "metrics": {
        "daily_pnl_pct": -0.05,
        "current_drawdown_pct": 0.10,
        "realized_vol_pct": 0.25
    }
}
```

**2. Nested under `risk.metrics`:**
```python
context = {
    "risk": {
        "metrics": {
            "daily_pnl_pct": -0.05,
            "current_drawdown_pct": 0.10
        }
    }
}
```

**3. Direct keys in context:**
```python
context = {
    "daily_pnl_pct": -0.05,
    "current_drawdown_pct": 0.10
}
```

**Priority order:** `context["metrics"]` > `context["risk"]["metrics"]` > direct keys

### Canonical Keys

All metrics use these canonical field names:
- `daily_pnl_pct`: Daily PnL as percentage (decimal, e.g., -0.06 = -6%)
- `current_drawdown_pct`: Current drawdown from peak (decimal, e.g., 0.21 = 21%)
- `realized_vol_pct`: Realized volatility (decimal, optional)
- `timestamp_utc`: ISO8601 timestamp (string, optional)

### Audit Log Structure

The audit log always includes a stable `metrics_snapshot` with canonical keys in deterministic order:

```json
{
  "kill_switch": {
    "enabled": true,
    "status": {
      "armed": false,
      "severity": "OK",
      "reason": "All thresholds within limits",
      "triggered_by": [],
      "timestamp_utc": "2025-12-25T12:00:00Z"
    },
    "metrics_snapshot": {
      "daily_pnl_pct": -0.02,
      "current_drawdown_pct": 0.05,
      "realized_vol_pct": null,
      "timestamp_utc": null
    }
  }
}
```

## Safe Defaults: Missing Data Behavior

**Important**: Missing or `None` metrics do **NOT** trigger the kill switch.

This is a safety design choice for the initial MVP:
- Missing data = no trigger (prevents false positives)
- **However**: In production, missing data may indicate a data pipeline failure
- **Recommendation**: Monitor data quality separately; do not rely on "no data = safe"

## Configuration

### Location
Kill Switch configuration lives in your main config file under `[risk.kill_switch]`.

### Example Configuration
```toml
[risk.kill_switch]
enabled = true
daily_loss_limit_pct = 0.05  # 5% daily loss limit
max_drawdown_pct = 0.20      # 20% max drawdown
max_volatility_pct = null    # optional, disabled by default
```

See `config/risk_kill_switch_example.toml` for a standalone example.

### Disabling the Kill Switch
```toml
[risk.kill_switch]
enabled = false
```

**Warning**: Only disable in testing/development. Production systems should always have the kill switch enabled.

## Sticky Behavior

Once armed, the kill switch **remains armed** until explicitly reset, even if metrics return to normal levels.

**Why sticky?**
- Prevents rapid arming/disarming cycles
- Forces operator review before resuming trading
- Ensures incidents are properly investigated

**Example:**
1. Daily loss reaches -6% → Kill switch arms
2. Metrics improve to -3% → Kill switch **still armed**
3. Operator reviews incident → Manually resets kill switch
4. Trading can resume

## Reset Procedure

### When to Reset

Before resetting the kill switch, complete this checklist:

- [ ] **Incident investigation complete**: Understand what caused the threshold breach
- [ ] **Root cause identified**: Know why the system lost money/entered drawdown
- [ ] **Risk assessment**: Confirm market conditions are suitable for resuming trading
- [ ] **Position review**: Check all open positions for anomalies
- [ ] **Data quality check**: Verify metrics pipeline is healthy
- [ ] **Strategy review**: Ensure strategies are behaving as expected
- [ ] **Authorization**: Get approval from risk manager (if applicable)

### How to Reset

#### Via Python API (Recommended)
```python
from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate

# Initialize gate
cfg = PeakConfig.from_file("config/config.toml")
gate = RiskGate(cfg)

# Reset kill switch
status = gate.reset_kill_switch(reason="post_incident_review_complete")
print(f"Kill switch reset: {status}")
```

#### Via Script
```bash
# Create a simple reset script if needed
python -c "
from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate
cfg = PeakConfig.from_file('config/config.toml')
gate = RiskGate(cfg)
status = gate.reset_kill_switch('manual_reset_after_review')
print(f'Armed: {status.armed}, Reason: {status.reason}')
"
```

#### Reset Confirmation
After reset, verify the status:
```python
status = gate.get_kill_switch_status()
assert not status.armed, "Kill switch should be disarmed"
print("Kill switch successfully reset")
```

## Checking Kill Switch Status

### Without Context
```python
# Get last known status (does not require metrics)
status = gate.get_kill_switch_status()
print(f"Armed: {status.armed}")
print(f"Reason: {status.reason}")
print(f"Triggered by: {status.triggered_by}")
```

### With Current Metrics
```python
# Evaluate with fresh metrics
context = {
    "metrics": {
        "daily_pnl_pct": -0.03,
        "current_drawdown_pct": 0.10,
    }
}
status = gate.get_kill_switch_status(context)
```

## Troubleshooting

### Why is the Kill Switch Armed?

Check the status object for details:
```python
status = gate.get_kill_switch_status()
if status.armed:
    print(f"Reason: {status.reason}")
    print(f"Triggered by: {status.triggered_by}")
    print(f"Metrics snapshot: {status.metrics_snapshot}")
    print(f"Timestamp: {status.timestamp_utc}")
```

**Common triggers:**
- `daily_loss_limit`: Daily loss exceeded threshold
- `max_drawdown`: Drawdown exceeded threshold
- `max_volatility`: Volatility exceeded threshold (if configured)

### Multiple Triggers Simultaneously

The kill switch can be triggered by multiple conditions at once:
```python
status.triggered_by = ["daily_loss_limit", "max_drawdown"]
```

Each trigger will be reflected in the `reason` field:
```
"Daily loss -6.0% exceeded limit -5.0%; Drawdown 22.0% exceeded limit 20.0%"
```

### WARN vs BLOCK Severity

Currently, the kill switch has two states:
- **OK**: Not armed, `severity="OK"`
- **ARMED**: Armed, `severity="BLOCK"`

There is no WARN state in the MVP. Either trading is allowed or blocked.

Future versions may add a warning threshold that alerts but doesn't block.

### Kill Switch Won't Reset

If `reset_kill_switch()` doesn't work:

1. **Check if enabled**:
   ```python
   print(gate._kill_switch.enabled)
   ```

2. **Verify reset was called**:
   ```python
   status = gate.reset_kill_switch("debug_reset")
   assert not status.armed
   ```

3. **Check for re-triggering**:
   - If metrics still exceed thresholds, kill switch will immediately re-arm on next evaluation
   - Reset only clears the armed state; it doesn't change thresholds or metrics

### Audit Log Review

All kill switch events are logged to the risk audit log:
```bash
# Find kill switch events
grep -l "kill_switch" logs/risk_audit.jsonl | head -10

# View armed events
jq 'select(.kill_switch.armed == true)' logs/risk_audit.jsonl
```

## Verification

### Unit Tests
```bash
# Test kill switch layer
pytest -v tests/risk_layer/test_kill_switch.py

# Test risk gate integration
pytest -v tests/risk_layer/test_risk_gate.py
```

### Integration Test
```bash
# Run all risk layer tests
pytest -v tests/risk_layer/
```

### Manual Smoke Test
```python
from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate

cfg = PeakConfig.from_file("config/config.toml")
gate = RiskGate(cfg)

# Test 1: Normal operation
order = {"symbol": "BTCUSDT", "qty": 1.0}
context = {"metrics": {"daily_pnl_pct": -0.02}}
result = gate.evaluate(order, context)
assert result.decision.allowed, "Should allow with normal metrics"

# Test 2: Trigger kill switch
context = {"metrics": {"daily_pnl_pct": -0.06}}
result = gate.evaluate(order, context)
assert not result.decision.allowed, "Should block when threshold exceeded"

# Test 3: Reset
status = gate.reset_kill_switch("manual_test")
assert not status.armed, "Should be disarmed after reset"

# Test 4: Resume normal operation
context = {"metrics": {"daily_pnl_pct": -0.02}}
result = gate.evaluate(order, context)
assert result.decision.allowed, "Should allow after reset with normal metrics"

print("✅ All manual smoke tests passed")
```

## Best Practices

### 1. Monitor Kill Switch Status
- Add kill switch status to dashboards
- Set up alerts when kill switch arms
- Log all arming events for post-incident review

### 2. Regular Testing
- Test kill switch in paper trading environment monthly
- Verify reset procedure works
- Practice incident response workflow

### 3. Documentation
- Document every kill switch incident
- Track which thresholds trigger most often
- Adjust thresholds based on strategy risk profile

### 4. Gradual Rollout
- Start with conservative thresholds (lower limits)
- Monitor false positive rate
- Gradually adjust to optimal levels

### 5. Data Quality
- Monitor metrics pipeline health
- Alert on missing/stale data
- Don't rely on "no data = safe" in production

## Related Documentation

- `src/risk_layer/kill_switch/`: Kill switch implementation (module)
- `src/live/live_gates.py`: Live execution gates (includes risk enforcement)
- `config/risk_kill_switch_example.toml`: Configuration example
- `tests/risk_layer/`: Test suite

## Support

For questions or issues:
1. Check this runbook
2. Review test cases in `tests/risk_layer/`
3. Inspect audit logs: `logs&#47;risk_audit.jsonl`
4. Review code documentation in source files
