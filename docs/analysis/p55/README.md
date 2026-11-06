# P55 — Switch-Layer E2E + Gated Runner v1

## Goal
Provide a deterministic, end-to-end path for the Switch-Layer:
- **P52**: regime decision (deterministic)
- **P53**: orchestration hook (optional evidence)
- **P54**: routing from switch decision → routing output
- **P55**: **paper/shadow-only** runner that writes a deterministic evidence pack

## Safety
- **Deny-by-default** for `mode in {live, record}`.
- Evidence writing happens **only** when `ctx.out_dir` is set.

## API
- `src.ops.p55.switch_layer_e2e_runner_v1.P55RunContextV1`
- `src.ops.p55.switch_layer_e2e_runner_v1.run_switch_layer_e2e_v1(prices, ctx, meta=None)`

## Evidence Pack (when out_dir set)
- `meta.json`
- `switch_decision.json`
- `routing.json`
- `manifest.json`

## Notes
Routing callable is resolved from `src.ai_orchestration.switch_layer_routing_v1` via a small candidate list and a safe fallback
(function name contains `route` and ends with `_v1`).
