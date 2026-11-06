# Implementation Scope (Preparation Only)

## In scope for this PR

- Planning evidence only under
  `docs&#47;evidence&#47;bollinger_entry_side_canonical_composition_slice_plan_v1&#47;`
- Exact carry-forward of audit OPTION_D recommendation
- Documentation of deferred OPTION_B envelope (not activation)

## Out of scope (this PR and until new Operator-GO)

- Any `src&#47;` change
- Any `tests&#47;` change
- Any config mutation
- Bollinger `entry_side` activation (`LONG`&#47;`SHORT`)
- New composition module implementation
- Runtime bridge activation
- Orders &#47; shadow &#47; paper &#47; testnet &#47; live
- Classic engine reinterpretation as canonical Intent
- Economic evaluation &#47; parameter sweeps

## Audit owners (frozen)

| Role | Owner |
|------|-------|
| Direction &#47; State | `trading.master_v2.double_play_state.transition_state` |
| Composition (system) | `trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1` |
| Strategy signal | `strategies.bollinger.BollingerBandsStrategy.generate_signals` |
| Event semantics | `strategies.bollinger_event_semantic_contract_v1.classify_bollinger_raw_signal_event_v1` |
| Order intent | `governance.canonical_order_intent_v1.build_canonical_order_intent_v1` |

## Active posture

```text
ENTRY_SIDE=NONE
STRATEGY_DIRECTION=NONE
BOLLINGER_EVENT_ONLY=true
COMPETING_AUTHORITY_COUNT=0
CONFIRMED_BYPASS_COUNT=1  # Classic run_realistic LONG — non-canonical
RUNTIME_PATH_STATUS=BOUND_NOT_ACTIVATED
```
