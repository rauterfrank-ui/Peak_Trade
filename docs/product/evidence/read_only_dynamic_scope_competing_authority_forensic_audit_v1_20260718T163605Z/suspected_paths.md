# Suspected Paths (post-audit)

## Productive Competing Authorities

**None found.** `COMPETING_AUTHORITY_COUNT=0`.

## Residual / non-productive suspects (not Live Side/Switch authorities)

### S1 — Scenario generator bypass (TEST_ONLY)
- **Path:** `offline_double_play_scenario_replay_v0` `tick.scope_event`
- **Risk:** MED
- **Productive reachable:** no (requires `allow_test_scope_event_injection=True` + `scope_event_provenance=TEST_INJECTION`)
- **Effect:** bypasses deterministic generator as event *source*; still calls `transition_state`
- **Action:** KEEP `TEST_ONLY_GUARDED` / FAIL_CLOSED default

### S2 — Testnet completion wiring defaults injection flag
- **Path:** `ops/bounded_master_v2_testnet_completion_path_wiring_v0.build_replay_input_from_testnet_market_input`
- **Risk:** MED
- **Productive reachable:** no Live/Orders (module is non-executing / zero-order admission); yes for bounded offline evidence wiring
- **Effect:** sets `allow_test_scope_event_injection=True` when mapping admitted testnet ticks into scenario replay input
- **Action:** FAIL_CLOSED tighten in a **separate** small PR — require explicit per-tick provenance; do not treat as Live authority today
- **Priority:** 1 among follow-ups

### S3 — Six-node offline graph synthetic default
- **Path:** `offline_master_v2_replay_six_node_validation_graph_binding_v0` default input
- **Risk:** LOW
- **Productive reachable:** no
- **Action:** KEEP TEST_ONLY

### S4 — Legacy `SideState.CHOP_GUARD_BLOCK` consumers
- **Path:** `double_play_composition.py`, scenario adapters, residual hold/clear in `transition_state`
- **Risk:** LOW
- **Productive reachable:** only if residual SideState still present; new CHOP no longer writes it
- **Action:** CONSUMER_ONLY / later DELETE residual after fixture cleanup
- **Priority:** 3

### S5 — Composition label dualism (`CompositionStatus.CHOP_GUARD_BLOCK`)
- **Path:** `double_play_composition_matrix_v1` both_sides_confirmed + scope projection
- **Risk:** LOW (not Scope-CHOP SSOT; documented)
- **Action:** optional CONSUMER_ONLY rename in docs/labels — not authority repair
- **Priority:** 4

### S6 — Ops SwitchGate primitive still exists
- **Path:** `ops&#47;gates&#47;switch_gate.step_switch_gate`
- **Risk:** LOW (unwired from Double Play)
- **Action:** KEEP quarantine; never rewire without Operator-GO
- **Priority:** 5

### S7 — Runtime bridge not activated
- **Path:** `canonical_core_runtime_integration_bridge_v0`
- **Risk:** structural — Backtest/Runtime authority parity is FULL on offline chain; Live runtime path not activated
- **Action:** no activation in this audit; wait Operator-GO for Slice B
- **Priority:** n/a (policy)

## Transition bypass / override (productive)

| Kind | Count | Notes |
|------|-------|-------|
| TRANSITION_STATE_BYPASS_PATHS (productive Side writer) | 0 | |
| TRANSITION_RESULT_OVERRIDE_PATHS | 0 | |
| Generator-source bypass (TEST_ONLY) | 1 | S1 |
| Generator-source bypass flag default (offline wiring) | 1 | S2 |

## Repair matrix (do **not** fix in this audit)

| Order | Path | Risk | Reachable | Measure |
|------:|------|------|-----------|---------|
| 1 | testnet completion `allow_test_scope_event_injection=True` default | MED | offline evidence only | FAIL_CLOSED / require tick provenance |
| 2 | scenario injection docs+guards ratify | MED | TEST_ONLY | KEEP / CONSUMER_ONLY docs |
| 3 | residual `SideState.CHOP_GUARD_BLOCK` fixtures | LOW | residual | DELETE / CONSUMER_ONLY cleanup |
| 4 | composition CHOP label rename | LOW | consumer | CONSUMER_ONLY |
| 5 | `step_switch_gate` keep unwired | LOW | tests | QUARANTINE |
