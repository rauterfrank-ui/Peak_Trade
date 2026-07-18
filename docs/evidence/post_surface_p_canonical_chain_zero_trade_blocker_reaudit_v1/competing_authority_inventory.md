# Competing Authority Inventory

**HEAD:** `43558204d4f7bcab30ce9e8357d2513a9a5f0970`  
**Scan scope:** `src/`, `tests/`, `scripts/`, `config/` (Master V2 / Double Play surfaces)

## Summary counts

| Metric | Value |
|--------|------:|
| COMPETING_AUTHORITY_COUNT | **0** |
| LEGACY_PRODUCTIVE_COUNT | **1** |
| RUNTIME_AUTHORITY_INTRODUCED | **false** |

## Inventory (grouped)

| Path | Symbol | Classification | Rationale |
|------|--------|----------------|-----------|
| `src/trading/master_v2/double_play_state.py` | `transition_state` | CANONICAL_AUTHORITY | Sole Bull/Bear + Switch writer |
| same | `RuntimeScopeState` / `update_dynamic_boundaries` | CANONICAL_AUTHORITY | Scope-state SSOT |
| `src/trading/master_v2/chop_scope_event_policy_binding_v1.py` | `apply_chop_scope_event_policy_v1` | CANONICAL_AUTHORITY | CHOP as scope policy (`chop_latched`); no Direction/Switch invent |
| `src/trading/master_v2/deterministic_scope_event_generator_v1.py` | `generate_deterministic_scope_event` | CANONICAL_AUTHORITY | Canonical scope-event producer |
| `src/trading/master_v2/canonical_scope_initialization_v1.py` | scope init | CANONICAL_AUTHORITY | Scope identity SSOT |
| `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` | offline orchestrator | CANONICAL_AUTHORITY | Calls only canonical chain |
| `src/trading/master_v2/double_play_sole_authority_quarantine_v1.py` | quarantine markers | CANONICAL_AUTHORITY | Fail-closed ownership SSOT; `RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED` |
| `src/trading/master_v2/double_play_composition_matrix_v1.py` | composition matrix | CONSUMER_PROJECTION | Composition/CHOP labels; not SideState SM |
| `src/trading/master_v2/double_play_entry_exit_policy_v0.py` | entry/exit + qty/eligibility | CONSUMER_PROJECTION | Offline `execution_eligible=false`, qty default `NOT_BOUND` |
| `src/trading/master_v2/strategy_suitability_agreement_material_v1.py` | `entry_side` / `cycle_signal_value` | CONSUMER_PROJECTION | Explicit carriers; no side from sign invention |
| `src/trading/master_v2/directional_assessment_v1.py` | DA LONG/SHORT | CONSUMER_PROJECTION | Assessment; `authority_effect=NONE` |
| `src/trading/master_v2/*_scenario_binding_adapter_v0.py` | scenario adapters | CONSUMER_PROJECTION | Thin wrappers → `transition_state` |
| `src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py` | runtime bridge | CONSUMER_PROJECTION | Bound offline; `BOUND_NOT_ACTIVATED` |
| `src/ops/double_play/specialists.py` | `evaluate_double_play` | CONSUMER_PROJECTION | Projection only |
| `src/live/live_gates.py` | DP annotation | CONSUMER_PROJECTION | No eligibility unlock via DP |
| `src/webui/double_play_dashboard_display_json_route_v0.py` | dashboard JSON | CONSUMER_PROJECTION | Read-only display |
| `src/backtest/backtest_engine_position_feedback_adapter_v1.py` | Classic feedback | CONSUMER_PROJECTION | OBSERVATION_ONLY; no SideState overwrite |
| `src/trading/master_v2/offline_double_play_scenario_replay_v0.py` | scenario replay | NON_AUTHORITY_TEST_OR_HARNESS | Injection fail-closed without test harness flag |
| `src/ops/gates/switch_gate.py` | `step_switch_gate` | LEGACY_UNREACHABLE | Not on productive DP callers |
| `src/trading/master_v2/double_play_composition.py` | `compose_double_play_decision` | LEGACY_PRODUCTIVE | Residual consumer of `SideState.CHOP_GUARD_BLOCK` (no new writer) |
| Surface-P harness / contracts | parity asserts | NON_AUTHORITY_TEST_OR_HARNESS | Offline non-authority envelopes |

## Quarantine proofs (competing paths fail-closed)

Owner: `double_play_sole_authority_quarantine_v1` + `tests/trading/master_v2/test_double_play_sole_authority_quarantine_v1.py`

1. Ops SwitchGate → fail-closed / projection-only  
2. Unmarked `tick.scope_event` injection → fail-closed  
3. Backtest SideState overwrite attempts → observation-only  

## Long / Short symmetry (authority scan)

- Switch SM (`transition_state`) symmetric LONG↔SHORT  
- DA shares LONG/SHORT contract (incl. short mirror price)  
- Agreement requires explicit `entry_side`; ENTRY `+1` does not invent LONG  
- Encoding asymmetries (`POSITIONAL_LONG01`, classic long-only observation) are consumer/encoding — not competing SideState authority  

## Post–#5327/#5328 note

Both PRs are test/harness assert + smoke fixture alignment only. No new runtime/direction/scope/switch/quantity/execution authority introduced.
