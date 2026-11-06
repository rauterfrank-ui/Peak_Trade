# Cross-sectional short-horizon return reversal — preregistered hypothesis and measurement v1

Status: `DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract
preregistered; no evaluation.

## Identity

- Hypothesis: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1`
- Program: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1`
- Contract: `cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_hypothesis_measurement_contract.v1`

## Treatment / baseline

- Treatment: negated trailing log-return cross-sectional single-slot rank
  (`lookback_N=24`, `rebalance_interval_bars=4`, `signal_lag_bars=1`)
- Baseline: absolute economic admission against frozen thresholds (no Bollinger
  control delta; not a CS-momentum control delta)
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION` under Double-Play

## Primary / secondary metrics

- Primary decision metric: `NET_PROFIT_FACTOR`
- Also required: gross PF/PnL, cost-stress PF@1.5x, max drawdown, trade/rebalance
  sample, universe breadth, time-segment robustness pass ratio

## Acceptance (fail-closed)

All preregistered gates must pass jointly (PF_net >= 1.3, gross edge present,
cost-stress survival, MaxDD <= 0.25, trades >= 50, rebalances >= 30,
time-segment pass ratio >= 0.5, concentration limit). Otherwise
`DEVELOPMENT_FAIL` / `FAIL_CLOSED_NO_RETRY`.

## Limits

- Development run limit: 1
- Holdout run limit: 0
- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUN_SLOT_CONSUMED=false`

## Evidence

- Contract: `config/research/cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration evidence: `docs/evidence/preregister_cross_sectional_short_horizon_return_reversal_hypothesis_v1/`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
