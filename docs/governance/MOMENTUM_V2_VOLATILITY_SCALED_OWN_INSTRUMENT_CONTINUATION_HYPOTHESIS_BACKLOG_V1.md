# Momentum V2 — volatility-scaled own-instrument continuation hypothesis backlog v1

## Current SSOT status

- Lane status: `OPEN_BACKLOG`
- Program: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`
- Preregistered: exactly one (definition-only)
- Open unpreregistered candidates: empty
- Terminal: empty
- Development run count: `0`
- Implementation present: `true`
- Evaluation authorized: `false`
- Development evaluation authorized: `false`
- Run slot consumed: `false`
- Holdout: forbidden &#47; unaccessed
- Next eligible: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`

## Preregistered hypotheses

Exactly one:

- `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
  — status `DEFINITION_ONLY_PREREGISTERED_IMPLEMENTATION_PRESENT`
  — baseline `FROZEN_RAW_RETURN_MOMENTUM_1H_ENTRY_EXIT_EVENT_V1`
  — treatment `VOLATILITY_SCALED_MOMENTUM_SCORE_THRESHOLD_CROSS_V1`
  — contract: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Collision exclusions

- Closed CS relative-strength momentum: reopen forbidden
- Pending `momentum_1h&#47;v2` &#47; `MOMENTUM_HORIZON_V2_NON_BITCOIN_FUTURES_V2`: untouched, not executed
- Registry `momentum_1h` &#47; `MomentumStrategy`: unchanged
- Raw lookback &#47; entry &#47; exit threshold retune: forbidden

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_FOR_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION`

---
docs_token: DOCS_TOKEN_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_HYPOTHESIS_BACKLOG_V1
STATUS: OPEN_BACKLOG_DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
