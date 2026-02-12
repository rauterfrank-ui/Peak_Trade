# Risk Metrics Schema

## Overview

This document describes the canonical risk metrics schema used across the Peak_Trade Risk Layer.

**Goal:** Provide a stable, typed, and deterministic interface for risk metrics extraction and serialization.

**Status:** ✅ Implemented (PR5: Metrics Plumbing v1)

## Canonical Schema

### RiskMetrics

The `RiskMetrics` dataclass (previously in `src\&#47;risk_layer\&#47;metrics.py`, now refactored) represents the canonical schema:

```python
@dataclass(frozen=True)
class RiskMetrics:
    daily_pnl_pct: float | None = None
    current_drawdown_pct: float | None = None
    realized_vol_pct: float | None = None
    timestamp_utc: str | None = None
```

### Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `daily_pnl_pct` | `float \| None` | Daily PnL as percentage (decimal) | `-0.06` = -6% loss |
| `current_drawdown_pct` | `float \| None` | Current drawdown from peak (decimal) | `0.21` = 21% drawdown |
| `realized_vol_pct` | `float \| None` | Realized volatility as percentage (decimal) | `0.25` = 25% vol |
| `timestamp_utc` | `str \| None` | ISO8601 timestamp when metrics captured | `"2025-12-25T12:00:00Z"` |

**Important:** All percentage values are expressed as **decimals**, not basis points.
- ✅ Correct: `-0.05` for -5%
- ❌ Wrong: `-5.0` for -5%

## Extraction API

### `extract_risk_metrics(context)`

Extracts risk metrics from a context dict (tolerant to various layouts).

**Supported layouts:**

1. **Nested under `metrics` (recommended):**
   ```python
   context = {"metrics": {"daily_pnl_pct": -0.05}}
   ```

2. **Nested under `risk.metrics`:**
   ```python
   context = {"risk": {"metrics": {"daily_pnl_pct": -0.05}}}
   ```

3. **Direct keys:**
   ```python
   context = {"daily_pnl_pct": -0.05}
   ```

**Priority:** `metrics` > `risk.metrics` > direct keys

**Behavior:**
- Missing keys → `None`
- Invalid types → `None` (no crash)
- String numbers → converted to float (e.g., `"-0.05"` → `-0.05`)
- Non-numeric strings → `None`

**Example:**

```python
from src.risk_layer.metrics import extract_risk_metrics

context = {"metrics": {"daily_pnl_pct": -0.03, "current_drawdown_pct": 0.10}}
metrics = extract_risk_metrics(context)

print(metrics.daily_pnl_pct)  # -0.03
print(metrics.realized_vol_pct)  # None (not provided)
```

## Serialization API

### `metrics_to_dict(metrics)`

Converts `RiskMetrics` to dict with stable key order.

**Output format:**

```python
{
    "daily_pnl_pct": -0.05,
    "current_drawdown_pct": 0.10,
    "realized_vol_pct": None,
    "timestamp_utc": None
}
```

**Guarantees:**
- Keys always in same order (even if values are `None`)
- JSON-serializable
- Deterministic (no dict iteration randomness)

**Example:**

```python
from src.risk_layer.metrics import RiskMetrics, metrics_to_dict

metrics = RiskMetrics(daily_pnl_pct=-0.05, current_drawdown_pct=0.10)
d = metrics_to_dict(metrics)

import json
print(json.dumps(d, indent=2))
```

Output:
```json
{
  "daily_pnl_pct": -0.05,
  "current_drawdown_pct": 0.1,
  "realized_vol_pct": null,
  "timestamp_utc": null
}
```

## Usage in Risk Layer

### RiskGate

```python
from src.risk_layer.risk_gate import RiskGate

gate = RiskGate(cfg)

order = {"symbol": "BTCUSDT", "qty": 1.0}
context = {"metrics": {"daily_pnl_pct": -0.03}}

result = gate.evaluate(order, context)
# Internally uses extract_risk_metrics(context)
```

### KillSwitch

```python
from src.risk_layer.kill_switch import KillSwitchLayer
from src.risk_layer.metrics import RiskMetrics

ks = KillSwitchLayer(cfg)

# Option 1: Use RiskMetrics (recommended)
metrics = RiskMetrics(daily_pnl_pct=-0.06, current_drawdown_pct=0.15)
status = ks.evaluate(metrics)

# Option 2: Use dict (backwards compatible)
metrics_dict = {"daily_pnl_pct": -0.06, "current_drawdown_pct": 0.15}
status = ks.evaluate(metrics_dict)
```

## Audit Logs

All risk audit logs include a `kill_switch.metrics_snapshot` field with canonical structure:

```json
{
  "timestamp_utc": "2025-12-25T12:00:00Z",
  "decision": {...},
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
  },
  "order": {...},
  "context": {...}
}
```

**Key properties:**
- Always present (even if kill switch disabled)
- Stable key order (deterministic)
- `None` values preserved (not filtered)

## Migration Guide

### From Dict-Based Metrics

**Before (ad-hoc dict):**
```python
metrics = {"daily_pnl_pct": -0.05, "custom_field": 123}
status = kill_switch.evaluate(metrics)
```

**After (canonical RiskMetrics):**
```python
from src.risk_layer.metrics import RiskMetrics

metrics = RiskMetrics(daily_pnl_pct=-0.05)
status = kill_switch.evaluate(metrics)
# Custom fields should go in separate context, not metrics
```

### From Nested Context

No change needed! The extractor handles all layouts transparently:

```python
# All of these work:
context1 = {"metrics": {"daily_pnl_pct": -0.05}}
context2 = {"risk": {"metrics": {"daily_pnl_pct": -0.05}}}
context3 = {"daily_pnl_pct": -0.05}

gate.evaluate(order, context1)  # ✅
gate.evaluate(order, context2)  # ✅
gate.evaluate(order, context3)  # ✅
```

## Testing

Comprehensive tests in `tests&#47;risk_layer&#47;test_metrics.py`:

- ✅ Nested vs direct extraction (35 tests)
- ✅ Missing keys / None values
- ✅ Invalid types (strings, lists, dicts)
- ✅ Type conversion (string → float)
- ✅ Stable serialization order
- ✅ Round-trip (extract → serialize → extract)
- ✅ Edge cases (zero, negative zero, large/small values)

Run tests:
```bash
python3 -m pytest -v tests/risk_layer/test_metrics.py
```

## Design Principles

1. **Tolerant extraction:** Accept various input layouts (nested/direct)
2. **Non-crashing:** Invalid data → `None` instead of exception
3. **Deterministic:** Stable key order for audit logs
4. **Typed:** Use dataclass for IDE support and validation
5. **Backwards compatible:** Dict input still works alongside RiskMetrics

## Future Extensions

Potential additions for future versions:

- `position_size_pct`: Position sizing metrics
- `leverage_ratio`: Current leverage
- `margin_usage_pct`: Margin utilization
- `sharp_ratio_trailing`: Rolling Sharpe ratio
- `max_consecutive_losses`: Loss streak counter

## Related Documentation

- `docs/risk/KILL_SWITCH_RUNBOOK.md`: Kill Switch operator guide
- `src/risk_layer/` (implementation refactored into multiple modules)
- `tests/risk_layer/` (test suite)

## Support

For questions or issues:
1. Check tests in `tests/risk_layer/`
2. Review risk layer implementation in `src/risk_layer/`
3. See usage examples in this doc
