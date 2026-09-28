# CURRENT productive persistent Natural-ENTER convergence v1

```text
CONTRACT_VERSION=v1
OWNER=full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
CONTINUOUS_RUN_AUTHORIZED=false
POST_COMPOSED=false
CAP23_PER_CYCLE_REINVOKE=false
CAP24_PER_CYCLE_REINVOKE=false
ATLAS_AUTHORITY=NONE
```

## Purpose

Offline/test and preflight surface for **fixed** S8 occupied-lane roots with bounded S6
continuous sequencing and S7 durable MV2+Double Play cursor persist across cycles.
Targets natural confirmation progression and PRE_EXTERNAL terminal without POST.

## Reused authorities

| Layer | Symbol |
|-------|--------|
| S8 | `build_s8_occupied_lane_pairs_v1` + Cap24 provenance handoff (read-only) |
| S6 | `run_current_productive_governed_continuous_cycle_run_v1` |
| S5/T2 | `invoke_occupied_lane_governed_cycle_n1_consumer_v1` → `compose_occupied_lane_mv2_dp_durable_cycle_v1` |
| S7 | `persist_occupied_lane_mv2_dp_decision_state_cursor_v1` |

## Invariants

- `cursor_store_root == lane_state_root` for `LANE_1`
- `selected_future == bound_future == S6 authorization native_id`
- `MAX_POSITIONS_EFFECTIVE == 1`, `MULTI_FUTURE_RUNTIME_AUTHORIZED == false`
- Native bounds: `max_cycles_per_run <= 4`, `max_run_duration_seconds <= 180`
- No Cap21→23 writer and no Cap24 canonical writer per S6 cycle
- Productive network GET/POST forbidden on this module; fail-closed without continuous productive authorization elsewhere

## Ops entry

`scripts/ops/run_current_productive_persistent_natural_enter_convergence_offline_v1.py`
(preflight-only; does not execute S6 productive loops)

## Tests

`tests/ops/test_current_productive_persistent_natural_enter_convergence_v1.py`
