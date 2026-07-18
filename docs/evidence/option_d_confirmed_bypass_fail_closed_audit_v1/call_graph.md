# Call Graph

## Callees (inside `run_realistic`)

```text
strategy_signal_fn(df, params) → pd.Series{+1,-1,0}
  → bar loop:
       signal==1 & flat → open LONG trade (local Trade object)
       signal==-1 & open → close long
  → optional Paper/ExecutionPipeline accounting (research)
```

No call to:

- `transition_state`
- `evaluate_double_play_composition_matrix_v1`
- `normalize_strategy_signal_to_suitability_agreement_material_v1`
- `resolve_agreement_bound_directional_cycle_v1`
- `build_canonical_order_intent_v1`

## Callers (productive research &#47; demos &#47; tests)

Many scripts under `scripts&#47;` (e.g. `run_backtest.py`, `run_strategy_from_config.py`, research CLI) and tests under `tests&#47;` &#47; `tests&#47;risk&#47;`.

These are **classic offline research** entry points — not Master-V2 Integrated Replay and not the runtime bridge.

## Integrated &#47; MV2 parallel path (non-bypass)

```text
bollinger.generate_signals
  → strategy_signal_binding_v1
  → normalize_..._material_v1  (OBL_B07: entry_side=NONE)
  → resolve_agreement_bound_directional_cycle_v1 → None
  → integrated_offline_trading_logic_replay_v1
       (CMC → scope → DA → suitability → composition → transition_state)
  → (gated) build_canonical_order_intent_v1
```
