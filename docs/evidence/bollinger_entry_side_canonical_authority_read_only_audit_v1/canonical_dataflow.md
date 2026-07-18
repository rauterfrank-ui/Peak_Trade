# Canonical Dataflow

## A. Strategy: Bollinger Inputs → Signal&#47;Intent

```text
OHLCV → BollingerBandsStrategy.generate_signals → raw {+1,-1,0}
       → classify_bollinger_raw_signal_event_v1
            +1 → ENTRY_EVENT
            -1 → EXIT_EVENT
             0 → FLAT_NO_EVENT
       → direction=NONE, entry_side=NONE  (OBL_B07 EVENT_ONLY)
```

**Darf Bollinger LONG&#47;SHORT liefern?** Nein.  
**Nur neutrales Signal&#47;Setup?** Ja für Direction&#47;Side; Events sind Entry&#47;Exit&#47;Flat ohne Side.

## B. Master V2 &#47; Double Play: Scope → Bull&#47;Bear → Direction

```text
CanonicalMarketContextV1
  → CanonicalScopeSnapshotV1 / RuntimeScopeState (Dynamic Scope)
  → Directional Assessment (bull&#47;bear)
  → Survival
  → Suitability
  → evaluate_double_play_composition_matrix_v1
  → transition_state  ← CANONICAL_DIRECTION_OWNER
```

Strategy signals must not overwrite Bull&#47;Bear or SideState.

## C. Composition: Strategy Signal + Canonical State → ENTRY_SIDE

**Current Bollinger reality:**

```text
Agreement Material (event_kind + entry_side=NONE)
  → resolve_agreement_bound_directional_cycle_v1 → None
  → no executable directional cycle
  → ENTRY_SIDE remains NONE (fail-closed)
```

**Who may cut Signal with Bull&#47;Bear?**  
Only Master V2 composition (`evaluate_double_play_composition_matrix_v1`) for system selected_side — **not** Bollinger, and **not** by projecting DP state into strategy `entry_side` (that would be circular&#47;competing).

**When must result be NONE?**

- Bollinger `entry_side` always NONE under OBL_B07
- Missing&#47;invalid raw → UNKNOWN_FAIL_CLOSED
- Composition conflict &#47; both-sides &#47; blocked → `selected_side=NONE`
- ENTRY_EXIT without ratified carrier → no directional cycle

**Is ENTRY_SIDE a projection or unbound?**  
For Bollinger: **explicitly unbound &#47; fail-closed NONE** — not projected from Bull&#47;Bear. Carrier type exists for producer-scoped ratification (e.g. trend_following LONG); Bollinger not authorized.

**Existing composition owner?**  
`trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1`

## D. Consumers: ENTRY_SIDE → Order&#47;Backtest&#47;Replay

```text
integrated_offline_trading_logic_replay_v1
  → selected_side from composition / transition_state
  → (gated) build_canonical_order_intent_v1
```

Bridge: `canonical_core_runtime_integration_bridge_v0` = `BOUND_NOT_ACTIVATED`, `authority_effect=NONE`.

## Owners (exact)

| Role | module.symbol |
|------|----------------|
| CANONICAL_DIRECTION_OWNER | `trading.master_v2.double_play_state.transition_state` |
| CANONICAL_COMPOSITION_OWNER | `trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1` |
| STRATEGY_SIGNAL_OWNER | `strategies.bollinger.BollingerBandsStrategy.generate_signals` (+ event: `strategies.bollinger_event_semantic_contract_v1.classify_bollinger_raw_signal_event_v1`) |
| ORDER_INTENT_OWNER | `governance.canonical_order_intent_v1.build_canonical_order_intent_v1` |
