# VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1 — Strategy Implementation Only

DOCS_TOKEN_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_ONLY_V1

## Scope

Materializes the preregistered VCEB v1 strategy producer and exit state machine:

- RV(24) close-to-close log-return stdev + WEAK_LEQ percentile(120)
- 8-bar contraction (percentile ≤ 0.30) then expansion jump (≥0.65, rise ≥0.25, RV rising)
- same-bar directed 20-bar channel break (joint coincidence)
- ENTRY_EVENT on confirmation bar t; fill conceptually open of t+1 (signal_lag=1)
- pairable exits: INITIAL_STOP > OPPOSITE_BREAK_INVALIDATION > REGIME_INVALIDATION(<0.40) > TIME_EXIT(48) > EOI > EOP
- trailing stop forbidden
- productive PnL evaluator referenced from VCB package (not duplicated)

## Non-actions

- No Development evaluation authorization or execution
- No holdout access
- No parameter / hypothesis mutation (measurement digest frozen)
- No Shadow / Testnet / Live / Orders
- No VCB / VEP / VDB / VDBX retry

## Binding

`config/research/volatility_contraction_expansion_breakout_v1_strategy_implementation_binding_v1.json`
