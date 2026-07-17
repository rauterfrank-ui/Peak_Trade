# Double-Play Specialists (Bull/Bear) — Scaffold (Safe Default OFF)

## Goal
Provide a deterministic **specialist selection** layer:
- `bull` specialist
- `bear` specialist
- selection controlled by Switch-Gate state

## Authority (Slice E — required read)

Ops specialist evaluation is **`LEGACY_NON_AUTHORITATIVE`** (annotation-only / non-authorizing).

- **Boundary contract owner:** `trading.master_v2.evaluate_double_play_authority_boundary_v0`
- **Productive module:** `src/ops/double_play/specialists.py` — `evaluate_double_play` annotates eligibility/details only
- **Canonical offline authority:** `trading.master_v2.double_play_composition_matrix_v1` / `integrated_offline_trading_logic_replay_v1`
- **Normative map:** [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](../specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) — section **Slice E authority boundary**

Specialists do **not** grant live, order, runtime, scheduler, or Master-V2 decision authority.

## Safety Defaults
- `double_play_enabled` defaults to **False**
- When disabled: selection is **NOOP** (no behavior change)
- When enabled: selector only **annotates** decisions / eligibility details; execution remains governed by existing live gates.

## Inputs (context)
- `context["double_play_enabled"]` bool (default False)
- `context["switch_gate"]`:
  - `score` float (regime score)
  - `state` dict (active, hold_remaining, cooldown_remaining) optional; default active="bull"
  - `cfg` dict (hysteresis, min_hold_steps, cooldown_steps)

## Output
- `details["double_play"] = {enabled, active_specialist, switch_state, reasons}`
- Authority fields projected from the boundary owner remain non-authorizing (see Slice E).
