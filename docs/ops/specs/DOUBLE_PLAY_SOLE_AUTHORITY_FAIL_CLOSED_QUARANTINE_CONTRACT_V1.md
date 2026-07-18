---
title: "Double Play Sole Authority Fail-Closed Quarantine Contract v1"
status: "ACTIVE"
owner: "trading.master_v2"
last_updated: "2026-07-18"
docs_token: "DOCS_TOKEN_DOUBLE_PLAY_SOLE_AUTHORITY_FAIL_CLOSED_QUARANTINE_CONTRACT_V1"
---

# Double Play Sole Authority Fail-Closed Quarantine Contract v1

## 1. Purpose

Freeze Master V2 / Double Play as the **sole** productive Bull/Bear SideState and Switch
authority. Competing Ops SwitchGate decisions, unmarked scenario `tick.scope_event`
injection, and backtest SideState overwrite are fail-closed disabled or quarantined.

This contract does **not** bind CHOP/UNKNOWN trade semantics and does **not** authorize
Live, Testnet, Orders, or Runtime-Bridge activation.

## 2. Sole owners (canonical)

| Role | Owner |
|------|-------|
| Bull/Bear SideState + Switch | `trading.master_v2.double_play_state.transition_state` |
| Trailing Scope State SSOT | `RuntimeScopeState` + `update_dynamic_boundaries` |
| Scope identity | `CanonicalScopeSnapshotV1` |
| Scope event evidence | `generate_deterministic_scope_event` |
| Offline orchestrator | `run_integrated_offline_trading_logic_replay_v1` |
| Composition selected_side | `evaluate_double_play_composition_matrix_v1` (entry selection; not SideState SM) |

## 3. Role taxonomy

| Role | Meaning |
|------|---------|
| INPUT_ONLY | Observation / signal / material — no SideState/Switch write |
| PROJECTION_DIAGNOSTIC_ONLY | May mirror frozen labels for annotation; no switch authorize |
| OBSERVATION_ONLY | Position/venue facts; must not overwrite SideState / RuntimeScopeState |
| TEST_ONLY_INJECTION | Explicit harness flag + provenance mark required |
| LEGITIMATE_DELEGATED_AUTHORITY | Canonical owners above |

## 4. Quarantine dispositions

### Ops `evaluate_double_play` / `step_switch_gate`

- **Disposition:** `FAIL_CLOSED_DISABLE` for Switch authority; callable retained as
  `PROJECTION_DIAGNOSTIC_ONLY`.
- Must **not** invoke `step_switch_gate` for Double Play decisions.
- Must **not** write SideState into Double Play.
- Must **not** authorize a Bull/Bear switch.

### Scenario `tick.scope_event`

- **Disposition:** `TEST_ONLY_INJECTION`.
- `OfflineDoublePlayScenarioReplayInputV0.allow_test_scope_event_injection` default
  `false` — fail-closed.
- Explicit opt-in requires `allow_test_scope_event_injection is True` (exact bool; no
  string coercion), an offline/test/scenario `execution_surface`, and every tick must
  carry `scope_event_provenance="TEST_INJECTION"` plus validated
  `OfflineScenarioTickProvenanceV1` (source_kind, source_id/fixture_id, tick_index,
  sequence_number, event_time_ms, provenance_version).
- `build_replay_input_from_testnet_market_input` must not hardcode injection True;
  missing field / default remains False.
- Integrated / Backtest / Runtime wiring must not accept unmarked external ScopeEvents
  as SideState authority.
- Factory: `make_offline_scenario_replay_input_for_tests_v0`.
- Provenance authorizes test injection only; it must not create Direction, Side, Scope,
  or Switch decisions.

### Backtest position feedback

- **Disposition:** `OBSERVATION_ONLY`.
- `apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1` must **not**
  overwrite `side_state`, `direction_state`, `scope_direction_state`, or
  `runtime_scope_state`.
- Capture must not invent LONG_ACTIVE/LONG_ARMED SideState from open/flat position.
- Flat/NONE remains position NONE; no Direction invention.

## 5. CHOP / UNKNOWN

- `CHOP_BINDING_STATUS=BOUND_AS_SCOPE_POLICY` (see
  `CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1`)
- `UNKNOWN_BINDING_STATUS=NOT_BOUND_FAIL_CLOSED` (unchanged)
- CHOP cannot create Direction, mutate SideState, or trigger Switch
- Composition consumes Scope-CHOP as projection only; `both_sides_confirmed` is
  composition conflict, not Scope-CHOP SSOT

## 6. Non-authority

`LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`, Runtime Bridge `BOUND_NOT_ACTIVATED`.

## 7. Code owner markers

`src/trading/master_v2/double_play_sole_authority_quarantine_v1.py`
EOF