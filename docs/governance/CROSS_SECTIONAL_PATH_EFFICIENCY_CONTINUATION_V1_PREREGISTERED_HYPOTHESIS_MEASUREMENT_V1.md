# Cross-sectional path-efficiency continuation — preregistered hypothesis and measurement v1

Status: `DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract
preregistered; no evaluation.

## Identity

- Workstream: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_WORKSTREAM_V1`
- Hypothesis: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1`
- Program: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1`
- Contract: `cross_sectional_path_efficiency_continuation_v1_preregistered_economic_hypothesis_measurement_contract.v1`

## Treatment / baseline

- Treatment: path-efficiency ratio times sign(net log return) cross-sectional single-slot
  rank (`lookback_N=48`, `rebalance_interval_bars=8`, `signal_lag_bars=1`)
- Fail-closed eligibility: `path_sum==0` or `sign==0` → ineligible; eligible &lt; 5 →
  rebalance not evaluable; no fallback/adaptive selection
- Baseline: absolute economic admission against frozen thresholds
- Directional form: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION` under Double-Play
  (`trading.master_v2.double_play_state.transition_state`)

## Primary / secondary metrics

- Primary decision metric: `NET_PROFIT_FACTOR`
- Also required: gross PF/PnL, net expectancy, cost-stress PF@1.5x, max drawdown,
  trade/rebalance sample, universe breadth, time-segment robustness pass ratio,
  deterministic repro digest match

## Acceptance (fail-closed)

All preregistered gates must pass jointly (PF_net >= 1.3, gross edge present,
cost-stress survival, MaxDD <= 0.25, trades >= 50, rebalances >= 30,
time-segment pass ratio >= 0.5, concentration limit). Otherwise
`DEVELOPMENT_FAIL` / `FAIL_CLOSED_NO_RETRY`.

## Limits

- Development run limit: 1
- Holdout run limit: 0
- `EVALUATION_AUTHORIZED=false`
- `IMPLEMENTATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUN_SLOT_CONSUMED=false`
- No parameter grid; no retuning; no second development run

## Evidence

- Contract: `config/research/cross_sectional_path_efficiency_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration evidence: `docs/evidence/preregister_cross_sectional_path_efficiency_continuation_hypothesis_v1/`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
