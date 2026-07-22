# Volatility contraction→expansion breakout v1 — preregistered hypothesis measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` / `PREREGISTRATION_ONLY`

## Identity

- Hypothesis: `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Target phenomenon: `VOLATILITY_CONTRACTION_TO_EXPANSION_JOINT_DIRECTIONAL_BREAKOUT`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Predecessor: `VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1`

## Binding

- SSOT: `config&#47;research&#47;volatility_contraction_expansion_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Validator: `src&#47;research&#47;volatility_contraction_expansion_breakout_v1_hypothesis_preregistration_v1.py`
- Evidence: `docs&#47;evidence&#47;preregister_volatility_contraction_expansion_breakout_hypothesis_v1&#47;`

## Mechanism (frozen)

- Vol estimator: realized volatility close-to-close log-return stdev(24) percentile-rank lookback 120
- Contraction: last 8 completed bars each have RV percentile <= 0.30
- Expansion on bar t: prior contraction through t-1; percentile(t) >= 0.65; rise >= 0.25; RV strictly increasing
- Directional break must coincide on the same bar t (joint coincidence)
- Entry window: open of t+1 only (never on trigger bar t)
- Event: single-use; max one entry; rearm requires new full 8-bar contraction
- Exit (pairable): INITIAL_STOP (1.5×ATR14) > OPPOSITE_BREAK_INVALIDATION > REGIME_INVALIDATION (<0.40) > TIME_EXIT (48) > END_OF_INSTRUMENT > END_OF_PANEL
- Trailing stop forbidden; ex-ante exit reachability required (min 48 post-fill bars)
- Productive exit/PnL evaluator referenced (no second PnL truth)

## Material difference

- vs VDBX: contraction→expansion joint break + RV estimator + opposite-break exits without trailing; not a decay-exit repair
- vs VDB: not high→low decay; joint coincidence vs post-decay window
- vs VEP: requires prior contraction; not expansion persistence
- vs VCB: no multi-bar release window; RV not ATR; joint same-bar break required
- vs coiled-spring: not coincident high-vol filter; panel/baseline differ

## Gates

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true` (awaiting separate Operator-GO; not executed)
- `DEVELOPMENT_EVALUATION_EXECUTED=false`
- `HOLDOUT_FORBIDDEN=true` (unbound)
- `DEVELOPMENT_RUN_COUNT=0`, `RUN_LIMIT=1`, `RUN_SLOT_CONSUMED=false`
- `STRATEGY_IMPLEMENTATION_PRESENT=false`
- `PROMOTION_ELIGIBLE=false` (economic gate closed)
- `LIVE_AUTHORIZED=false`, `ORDERS=false`

## Next step

`SEPARATE_OPERATOR_GO_REQUIRED_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION_AUTHORIZATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, authorizing-only, definition-only preregistration
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
