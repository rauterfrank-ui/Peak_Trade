# Volatility decay breakout with explicit decay exit v1 — preregistered hypothesis

## Status

`DEFINITION_ONLY_PREREGISTERED` (strategy + exit state machine present; Development evaluation unauthorized)

## Identity

- Hypothesis: `VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1`
- Predecessor: `VOLATILITY_DECAY_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Portfolio: `RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`

## Binding

- SSOT: `config/research/volatility_decay_breakout_with_explicit_decay_exit_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Validator: `src/research/volatility_decay_breakout_with_explicit_decay_exit_v1_hypothesis_preregistration_v1.py`
- Exit SM: `src/research/volatility_decay_breakout_with_explicit_decay_exit_v1_exit_state_machine_v1.py`
- Strategy: `src/research/volatility_decay_breakout_with_explicit_decay_exit_v1_strategy_v1.py`
- Evidence: `docs/evidence/preregister_volatility_decay_breakout_with_explicit_decay_exit_hypothesis_v1/`

## Mechanism (frozen)

- Entry: preserved VDB high→low decay + channel break in t+1..t+8
- Ex-ante reachability: suppress entry unless fill + 48 post-fill bars exist
- Exit SM precedence: INITIAL_STOP > TRAILING_STOP > SIGNAL_EXIT (>=0.70) > REGIME_INVALIDATION (<0.50) > TIME_EXIT (48) > END_OF_INSTRUMENT > END_OF_PANEL
- Same-bar: non-terminal exit on fill bar forbidden
- Productive PnL evaluator referenced (not duplicated); no second PnL/equity/stats truth

## Material difference vs predecessor

- Strategy-owned exit state machine (predecessor entry-only)
- SIGNAL_EXIT + terminal liquidation + reachability gate
- Not a VDB corrective retry; predecessor artifacts unchanged

## Gates

- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUN_LIMIT=1`
- `HOLDOUT_FORBIDDEN=true`
- `LIVE_AUTHORIZED=false` / `ORDERS=false`

## Next step

`REVIEW_AND_MERGE_THEN_SEPARATE_OPERATOR_GO_FOR_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, authorizing-only, definition-and-strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
