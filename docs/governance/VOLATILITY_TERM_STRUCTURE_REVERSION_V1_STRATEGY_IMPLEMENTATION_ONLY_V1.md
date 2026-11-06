# VOLATILITY_TERM_STRUCTURE_REVERSION_V1 — Strategy Implementation Only

DOCS_TOKEN_VOLATILITY_TERM_STRUCTURE_REVERSION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1

## Scope

Materializes the preregistered VTSR v1 strategy producer and exit state machine:

- short RV(8) / long RV(48) close-to-close log-return stdev ratio
- WEAK_LEQ percentile(120) of the ratio
- elevated state (>=2 bars ratio percentile >= 0.80)
- fade entry opposite short-horizon signed return (8 bars); fill at open of t+1
- depressed-ratio entries forbidden; max one entry per elevated episode
- rearm requires ratio percentile strictly below 0.50 then a new elevated state
- pairable exits: INITIAL_STOP > TERM_STRUCTURE_NORMALIZATION_INVALIDATION(<0.55) >
  REGIME_INVALIDATION(<0.40) > TIME_EXIT(48) > EOI > EOP
- trailing stop forbidden
- productive PnL evaluator referenced from VCB package (not duplicated)
- Development evaluation unauthorized and not executed in this slice

## Non-actions

- No Development evaluation execution
- No Development slot consumption
- No holdout access
- No parameter / hypothesis mutation (measurement digest frozen)
- No Shadow / Testnet / Live / Orders
- No VEFCF / VEPC / VCEB / VDBX / VDB / VEP / VCB retry

## Policy Critic note

RISK_LIMIT_JUSTIFICATION: Not a productive risk-limit raise and not a change to Master-V2 /
Double-Play / live risk authorities. Policy Critic may match research-only literals such as
`MAXIMUM_MAX_DRAWDOWN = 0.25` (frozen preregistered economic-admission threshold from the
measurement contract). No live/runtime risk limits, leverage, daily-loss limits, or order-path
risk gates are modified. LIVE_AUTHORIZED=false; ORDERS=false; productive risk authorities
unchanged.

## Binding

`config/research/volatility_term_structure_reversion_v1_strategy_implementation_binding_v1.json`

## Next step

Separate operator GO for bounded Development evaluation.
