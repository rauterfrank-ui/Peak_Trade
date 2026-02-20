# Double-Play Specialists (Bull/Bear) — Scaffold (Safe Default OFF)

## Goal
Provide a deterministic **specialist selection** layer:
- `bull` specialist
- `bear` specialist
- selection controlled by Switch-Gate state

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
