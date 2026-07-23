# VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1 — Strategy Implementation + Unauthorized Entry Path

DOCS_TOKEN_VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1

## Scope

Materializes the preregistered VEFCF v1 strategy producer and exit state machine:

- RV(24) close-to-close log-return stdev + WEAK_LEQ percentile(120)
- confirmed expansion (≥4 bars RV percentile ≥ 0.65)
- directional impulse via shared 20-bar channel break
- failed-continuation fade triggers (first-wins): extreme break / deep pullback (≥50%) /
  qualifying pullback window exhaustion (≥15%, ≤8 bars) without continuation
- successful VEPC-style continuation cancels fade for the sequence
- entry direction opposite the failed impulse; never on expansion confirmation bar
- no immediate breakout without failure; no VEPC continuation entry
- pairable exits: INITIAL_STOP > IMPULSE_RECLAIM_INVALIDATION > REGIME_INVALIDATION(<0.40) >
  TIME_EXIT(48) > EOI > EOP
- trailing stop forbidden
- productive PnL evaluator referenced from VCB package (not duplicated)
- canonical entry path productively bound; Development evaluation not executed

## Non-actions

- No Development evaluation execution
- No Development slot consumption
- No holdout access
- No parameter / hypothesis mutation (measurement digest frozen)
- No Shadow / Testnet / Live / Orders
- No VEPC / VCEB / VDBX / VDB / VEP / VCB retry

## Policy Critic note

RISK_LIMIT_JUSTIFICATION: literals resembling max_drawdown are frozen research economic-admission
thresholds / empty-metrics placeholders only; no productive risk-limit raise;
LIVE_AUTHORIZED=false; ORDERS=false.

## Binding

`config/research/volatility_expansion_failed_continuation_fade_v1_strategy_implementation_binding_v1.json`

## Next step

Separate operator GO for bounded Development evaluation execution.
