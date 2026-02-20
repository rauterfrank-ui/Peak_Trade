# Double-Play — Bull/Bear Specialists + Switch-Gate

## Goal
Run two specialists (bull/bear) and select which one is eligible to act using a deterministic Switch-Gate.

## Components (current)
- Switch-Gate primitive: `src/ops/gates/switch_gate.py`
- Live safety gates: `src/live/live_gates.py`, `src/live/safety.py`

## Switch-Gate Controls
- **Hysteresis**: dead-band to prevent chatter around regime boundary.
- **MinHold**: minimum number of steps to keep a new regime active.
- **Cooldown**: post-switch quiet period before switching again.

## Next (not implemented here)
- Specialist interfaces + portfolio selector
- Dynamic Leverage sizing contract (cap 50×) with monotonic safety tests
