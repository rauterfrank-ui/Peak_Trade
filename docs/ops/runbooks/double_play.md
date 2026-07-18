# Double-Play — Bull/Bear Specialists + Switch-Gate

## Goal
Run two specialists (bull/bear) and select which one is eligible to act using a deterministic Switch-Gate.

## Authority (Slice E / Quarantine v1 — required read)

Ops Double-Play evaluation is **`LEGACY_NON_AUTHORITATIVE`** and
**`PROJECTION_DIAGNOSTIC_ONLY`** (annotation-only / non-authorizing). Competing
SwitchGate authority is **fail-closed disabled** — `evaluate_double_play` does
**not** call `step_switch_gate` and does **not** authorize Bull/Bear switches.

- **Boundary contract owner:** `trading.master_v2.evaluate_double_play_authority_boundary_v0`
- **Sole authority quarantine:** `trading.master_v2.double_play_sole_authority_quarantine_v1`
- **Ops evaluator:** `src.ops.double_play.specialists.evaluate_double_play` — productive projection/diagnostic path; **not** system economic / Master-V2 decision authority
- **Canonical offline Bull/Bear + Switch authority:** `trading.master_v2.double_play_state.transition_state` via `integrated_offline_trading_logic_replay_v1`
- **Canonical offline composition authority:** `trading.master_v2.double_play_composition_matrix_v1`
- **Normative map:** [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) — section **Slice E authority boundary**
- **Contract:** [DOUBLE_PLAY_SOLE_AUTHORITY_FAIL_CLOSED_QUARANTINE_CONTRACT_V1.md](../specs/DOUBLE_PLAY_SOLE_AUTHORITY_FAIL_CLOSED_QUARANTINE_CONTRACT_V1.md)

This runbook does **not** authorize live trading, orders, runtime rewire, promotion, or Master-V2 decision authority.

## Components (current)
- Switch-Gate primitive: `src/ops/gates/switch_gate.py` (unit-testable; **not** wired into Double Play authority)
- Ops specialists / selector: `src/ops/double_play/specialists.py` (`evaluate_double_play`, safe default OFF, projection/diagnostic-only)
- Live safety gates: `src/live/live_gates.py`, `src/live/safety.py` (Double-Play role remains projection/diagnostic-only when present)

## Switch-Gate Controls
- **Hysteresis**: dead-band to prevent chatter around regime boundary.
- **MinHold**: minimum number of steps to keep a new regime active.
- **Cooldown**: post-switch quiet period before switching again.

## Next (out of scope here — not authority grants)
- Dynamic Leverage sizing contract (cap 50×) with monotonic safety tests — separate design/GO if ever pursued
- Elevating ops `evaluate_double_play` into the Master-V2 offline SSOT — **forbidden** without a separate Master-V2 Adapt design change
