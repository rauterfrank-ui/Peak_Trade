# Double-Play Specialists (Bull/Bear) — Scaffold (Safe Default OFF)

## Goal
Provide a deterministic **specialist selection** layer:
- `bull` specialist
- `bear` specialist
- selection controlled by Switch-Gate state

## Authority (Slice E / Quarantine v1 — required read)

Ops specialist evaluation is **`LEGACY_NON_AUTHORITATIVE`** and
**`PROJECTION_DIAGNOSTIC_ONLY`** (annotation-only / non-authorizing). SwitchGate
decisions are fail-closed disabled for Double Play authority.

- **Boundary contract owner:** `trading.master_v2.evaluate_double_play_authority_boundary_v0`
- **Sole authority quarantine:** `trading.master_v2.double_play_sole_authority_quarantine_v1`
- **Productive module:** `src/ops/double_play/specialists.py` — `evaluate_double_play` projects frozen input labels only
- **Canonical offline Bull/Bear + Switch authority:** `trading.master_v2.double_play_state.transition_state` / `integrated_offline_trading_logic_replay_v1`
- **Canonical offline composition authority:** `trading.master_v2.double_play_composition_matrix_v1`
- **Normative map:** [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) — section **Slice E authority boundary**

Specialists do **not** grant live, order, runtime, scheduler, or Master-V2 decision authority.

## Safety Defaults
- `double_play_enabled` defaults to **False**
- When disabled: selection is **NOOP** (no behavior change)
- When enabled: selector only **projects** frozen switch_gate input state into details; it does **not** advance SwitchGate or authorize switches; execution remains governed by existing live gates.

## Inputs (context)
- `context["double_play_enabled"]` bool (default False)
- `context["switch_gate"]`:
  - `score` float (regime score)
  - `state` dict (active, hold_remaining, cooldown_remaining) optional; default active="bull"
  - `cfg` dict (hysteresis, min_hold_steps, cooldown_steps)

## Output
- `details["double_play"] = {enabled, active_specialist, switch_state, reasons}`
- Authority fields projected from the boundary owner remain non-authorizing (see Slice E).
