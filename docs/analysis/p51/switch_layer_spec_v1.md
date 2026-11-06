# Switch Layer v1 (Kurs steigt/sinkt) — Spec (Non-executing)

## Intent
A **market regime signal** (UP/DOWN/NEUTRAL) that can be mounted above strategies.
It must **not** place orders and must be compatible with deny-by-default gating.

## Outputs
- regime: {UP, DOWN, NEUTRAL}
- confidence: [0..1]
- evidence: deterministic feature snapshot (inputs, params, timestamp)

## Safety
- Must be pure function on input data (OHLCV + features), deterministic
- No network I/O, no model calls
- Consumers must treat as advisory; risk layer decides exposure

## Where to mount
Recommended: `strategy_layer` input surface (strategy weights / enable flags),
NOT execution layer.

## Next phase (P52)
- Implement `RegimeSwitchV1` + tests
- Wire into portfolio weighting (shadow + paper first)
