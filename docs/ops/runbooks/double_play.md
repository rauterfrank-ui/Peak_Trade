# Double-Play — Bull/Bear Specialists + Switch-Gate

## Goal
Run two specialists (bull/bear) and select which one is eligible to act using a deterministic Switch-Gate.

## Authority (Slice E — required read)

Ops Double-Play evaluation is **`LEGACY_NON_AUTHORITATIVE`** (annotation-only / non-authorizing).

- **Boundary contract owner:** `trading.master_v2.evaluate_double_play_authority_boundary_v0`
- **Ops evaluator:** `src.ops.double_play.specialists.evaluate_double_play` — productive annotation path; **not** system economic / Master-V2 decision authority
- **Canonical offline authority:** `trading.master_v2.double_play_composition_matrix_v1` via `integrated_offline_trading_logic_replay_v1`
- **Normative map:** [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) — section **Slice E authority boundary**

This runbook does **not** authorize live trading, orders, runtime rewire, promotion, or Master-V2 decision authority.

## Components (current)
- Switch-Gate primitive: `src/ops/gates/switch_gate.py`
- Ops specialists / selector: `src/ops/double_play/specialists.py` (`evaluate_double_play`, safe default OFF, annotation-only)
- Live safety gates: `src/live/live_gates.py`, `src/live/safety.py` (Double-Play role remains annotation-only when present)

## Switch-Gate Controls
- **Hysteresis**: dead-band to prevent chatter around regime boundary.
- **MinHold**: minimum number of steps to keep a new regime active.
- **Cooldown**: post-switch quiet period before switching again.

## Next (out of scope here — not authority grants)
- Dynamic Leverage sizing contract (cap 50×) with monotonic safety tests — separate design/GO if ever pursued
- Elevating ops `evaluate_double_play` into the Master-V2 offline SSOT — **forbidden** without a separate Master-V2 Adapt design change
