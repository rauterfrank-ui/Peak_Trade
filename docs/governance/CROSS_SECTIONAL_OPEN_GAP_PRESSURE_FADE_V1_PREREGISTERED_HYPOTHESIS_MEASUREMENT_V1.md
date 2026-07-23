# Cross-sectional open-gap pressure fade — preregistered hypothesis and measurement v1

Status: `DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract
preregistered; no evaluation.

## Identity

- SCOPE_ID: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_DEFINITION_ONLY_PREREGISTRATION_V1`
- Hypothesis: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1`
- Program: `CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1`
- Contract: `cross_sectional_open_gap_pressure_fade_v1_preregistered_economic_hypothesis_measurement_contract.v1`

## Research question

Do instruments with extreme trailing mean open-gaps
`gap_t = log(open_t / close_{t-1})` on the sealed non-BTC PT1H perpetual panel
fade enough after canonical costs that a single frozen negated-mean-gap
cross-sectional single-slot treatment passes absolute economic admission gates?

## Economic / microstructure rationale

Hourly opens that jump away from the prior close concentrate temporary inventory
and liquidity pressure. Cross-sectionally extreme open-gap pressure is expected
to mean-revert as liquidity replenishes within the holding window. The signal
isolates the discontinuous open-gap component and therefore is not a CSRHR
close-to-close reversal retune, not a CLV close-location continuation retune,
and not a path-efficiency rename.

## Treatment / baseline

- Treatment: negated mean open-gap cross-sectional single-slot rank
  (`lookback_N=30`, `rebalance_interval_bars=5`, `signal_lag_bars=1`)
- Score formula: for each lagged bar b, `gap_b=log(open_b/close_{b-1})`;
  `score_i=-mean(gap_b)`; fail-closed on non-finite OHLC / non-positive prior
  close / zero score; rank `score_desc` then `instrument_id_asc`; select top1;
  direction=`sign(top1_score)`
- Entry/exit: enter at next rebalance after lag; hold until next rebalance;
  no cooldown; no strategy stop
- Long/short: positive top1 score → LONG_TOP1 (fade extreme gap-down);
  negative top1 score → SHORT_TOP1 (fade extreme gap-up)
- Portfolio: single-slot equal-weight research sleeve combine
- Costs: fee 10 bps/side, slippage 5 bps/side, half-spread 5 bps; stress at 1.5x
- Risk/exposure: single top1 only; min eligible members=5; MaxDD gate 0.25;
  concentration worst1_abs_net_share ≤ 0.5
- Baseline: absolute economic admission against frozen thresholds

## Primary / secondary metrics

- Primary decision metric: `NET_PROFIT_FACTOR`
- Also required: gross PF/PnL, cost-stress PF@1.5x, max drawdown, trade/rebalance
  sample, universe breadth, time-segment robustness pass ratio

## Acceptance (fail-closed)

All preregistered gates must pass jointly (PF_net ≥ 1.3, gross edge present,
cost-stress survival, MaxDD ≤ 0.25, trades ≥ 50, rebalances ≥ 30,
time-segment pass ratio ≥ 0.5, concentration limit, deterministic repro).
Otherwise `DEVELOPMENT_FAIL` / `FAIL_CLOSED_NO_RETRY`.

## Forbidden post-hoc adjustments

No threshold retune, no lookback/rebalance retune, no polarity flip after
inspection, no grid search, no holdout peeking, no second development run.

## Limits

- Development run limit: 1
- Holdout run limit: 0
- `EVALUATION_AUTHORIZED=false`
- `STATUS=DEFINITION_ONLY_PREREGISTERED`
- `DEVELOPMENT_RUN_COUNT=0` / `RUN_SLOT_CONSUMED=false`
- Separate explicit DEVELOPMENT evaluation GO required before any evaluation

## Evidence

- Contract: `config/research/cross_sectional_open_gap_pressure_fade_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration evidence: `docs/evidence/preregister_cross_sectional_open_gap_pressure_fade_hypothesis_v1/`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
