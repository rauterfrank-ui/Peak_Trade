# VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1 — Strategy Implementation + Unauthorized Entry Path

DOCS_TOKEN_VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1

## Scope

Materializes the preregistered VEPC v1 strategy producer and exit state machine:

- RV(24) close-to-close log-return stdev + WEAK_LEQ percentile(120)
- confirmed expansion (≥4 bars RV percentile ≥ 0.65)
- directional impulse via shared 20-bar channel break
- bounded pullback 15–50% of impulse range within ≤8 bars
- entry only on continuation resume; never on expansion confirmation bar
- no immediate breakout without pullback
- pairable exits: INITIAL_STOP > PULLBACK_STRUCTURE_INVALIDATION > REGIME_INVALIDATION(<0.40) > TIME_EXIT(48) > EOI > EOP
- trailing stop forbidden
- productive PnL evaluator referenced from VCB package (not duplicated)
- canonical entry point productively bound; Development evaluation not executed

## Non-actions

- No Development evaluation execution
- No Development slot consumption
- No holdout access
- No parameter / hypothesis mutation (measurement digest frozen)
- No Shadow / Testnet / Live / Orders
- No VCEB / VDBX / VDB / VEP / VCB retry

## Policy Critic note

RISK_LIMIT_JUSTIFICATION: literals resembling max_drawdown are frozen research economic-admission thresholds / empty-metrics placeholders only; no productive risk-limit raise; LIVE_AUTHORIZED=false; ORDERS=false.

## Binding

`config/research/volatility_expansion_pullback_continuation_v1_strategy_implementation_binding_v1.json`
