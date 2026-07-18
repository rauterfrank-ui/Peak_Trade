# Call Graph (post PR #5325 / quarantine)

## Productive offline / backtest

```mermaid
flowchart TD
  MKT[Market/Bar Input] --> UDB[update_dynamic_boundaries]
  UDB --> GEN[generate_deterministic_scope_event]
  GEN --> TS[transition_state]
  TS --> CHOP[apply_chop_scope_event_policy_v1]
  CHOP --> RSS[RuntimeScopeState.chop_latched]
  TS --> SS[SideState]
  RSS --> COMP[composition_matrix scope_chop_policy_active]
  SS --> COMP
  COMP --> EE[entry_exit policy consumer]
  TS --> ADV[mv2 bar advance copies next_side_state + runtime_scope_after]
  FB[backtest position feedback] -.->|position fields only| ADV
```

## Quarantined / non-authority

```mermaid
flowchart LR
  OPS[evaluate_double_play] -->|projection only| CTX[frozen switch_gate dict]
  SG[step_switch_gate] -.->|NOT CALLED| OPS
  SCEN[tick.scope_event] -->|TEST_ONLY flag+provenance| TS2[transition_state]
  GEN2[generator] -.->|bypassed for event source| SCEN
  WEB[WebUI dashboard fixture] --> TS3[transition_state local]
  VAL[event_stream validator] --> TS4[transition_state compare]
```

## Key edges verified

| Caller | Callee | Mutation of SideState/Scope SSOT? |
|--------|--------|-----------------------------------|
| `integrated_offline_trading_logic_replay_v1` | `transition_state` | yes (canonical) |
| `transition_state` | `apply_chop_scope_event_policy_v1` | scope latch only |
| `evaluate_double_play` | `step_switch_gate` | **no call** |
| `apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1` | sequence `replace` | **no** side/direction/scope |
| scenario replay (flagged) | `transition_state` | yes but TEST_ONLY |
| WebUI / event_stream | `transition_state` | ephemeral non-SSOT |

## Persistence

No path persists Bull/Bear SideState or RuntimeScopeState into Live order submission. Runtime bridge status remains `BOUND_NOT_ACTIVATED`. `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`.
