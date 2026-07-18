# Canonical Authority Chain

```text
CanonicalMarketContext / bar input
        │
        ▼
update_dynamic_boundaries(RuntimeScopeState)     ← Scope trailing SSOT (freeze if chop_latched)
        │
        ▼
generate_deterministic_scope_event(...)            ← ScopeEvent producer (no CHOP market heuristic)
        │
        ▼
transition_state(side_state, event, RuntimeScopeState)
        │
        ├─ CHOP_DETECTED → apply_chop_scope_event_policy_v1 → chop_latched only (no SideState mutate)
        ├─ UPSCOPE/DOWNSCOPE confirm → SideState switch pipeline (blocked if chop_latched)
        └─ SCOPE_UNKNOWN → fail-closed unbound
        │
        ▼
Composition matrix (consumer): scope_chop_policy_active projection → entry block / selected_side
        │
        ▼
Entry/Exit policy + evidence envelopes (consumers; execution_eligible=false offline)
```

## Sole owners

| Role | Owner |
|------|-------|
| Scope-State SSOT | `trading.master_v2.double_play_state.RuntimeScopeState` |
| Bull/Bear SideState | `trading.master_v2.double_play_state.transition_state` |
| Switch | `trading.master_v2.double_play_state.transition_state` |
| CHOP | Scope-Policy only (`chop_latched` via `chop_scope_event_policy_binding_v1`) |
| Ordering | Dynamic Scope Update → Scope Event → `transition_state` |

## Productive orchestrator

`run_integrated_offline_trading_logic_replay_v1` is the sole productive offline/backtest orchestrator wiring the chain above. Backtest MV2 bar advance copies `intermediate.state_switch.next_side_state` / `runtime_scope_state_after` — it does not invent SideState.

## Explicitly not authorities

- Ops `evaluate_double_play` / `step_switch_gate` (fail-closed / unwired)
- Backtest position feedback (OBSERVATION_ONLY)
- Composition CHOP labels (CONSUMER_PROJECTION_ONLY)
- Scenario `tick.scope_event` (TEST_ONLY_GUARDED; still calls `transition_state`)
- WebUI dashboard fixture / event-stream validator (non-SSOT)
- Runtime bridge remains `BOUND_NOT_ACTIVATED`
