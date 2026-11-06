# Operator Wiring — Double-Play + Dynamic Leverage (E2E Smoke)

## Goal
Provide a **single deterministic adapter** that maps operator/runtime configuration into the `context` dict consumed by `src/live/live_gates.py`.

## Safety Defaults
- If any required operator intent signal is missing: features remain OFF.
- Adapter does **not** validate the confirm token; it only passes presence/valid flags into context.
- Actual live execution is still gated by existing live safety / confirm-token logic.

## Context Keys Produced
- `enabled` (bool)
- `armed` (bool)
- `confirm_token_present` (bool)  # presence/flag only
- `allow_double_play` (bool)
- `allow_dynamic_leverage` (bool)
- `double_play_enabled` (bool)  # derived from activation gate
- `dynamic_leverage_enabled` (bool)  # derived from activation gate
- `strength` (float in [0,1])  # optional operator-provided normalized strength
- `switch_gate` (dict)         # optional operator-provided switch-gate inputs/state
- `dynamic_leverage_cfg` (dict) # optional cfg; default cap 50x

## E2E Smoke
A test ensures:
- Defaults -> features OFF
- With enabled+armed+confirm+allow flags -> activation ON, and live_gates attaches `details["features"]`, `details["dynamic_leverage"]`, `details["double_play"]`.
