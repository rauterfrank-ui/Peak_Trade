# Dynamic Leverage — Live Path Integration (Safe Defaults)

## Goal
Expose a deterministic leverage multiplier in the live eligibility pipeline **without changing live execution behavior unless explicitly enabled**.

## Inputs (Live Context)
- `context["strength"]` in `[0,1]` (optional; default 0.0)
- Optional config in context:
  - `context["dynamic_leverage_enabled"]` (bool; default False)
  - `context["dynamic_leverage_cfg"]` (dict; optional; defaults to min=1, max=50, gamma=2)

## Output
- Live gate result adds:
  - `details["dynamic_leverage"] = {"enabled": bool, "strength": float, "leverage": float, "cap": 50.0, "gamma": float}`
- If `enabled==False`: `leverage` is omitted (or set to `min_leverage`) and **no eligibility change** occurs.
- If `enabled==True`: leverage is computed and attached; **eligibility is unchanged** (still governed by safety gates) — leverage is a sizing hint only.

## Safety
- Hard cap 50× enforced by `src/risk/dynamic_leverage.py`.
- Fail-closed: invalid cfg raises -> integration returns enabled=False and records reason, without enabling live execution.
