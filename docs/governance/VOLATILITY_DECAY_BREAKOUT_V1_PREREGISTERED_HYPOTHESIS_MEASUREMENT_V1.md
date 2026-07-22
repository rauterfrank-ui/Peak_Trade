# Volatility decay breakout v1 — preregistered hypothesis measurement

## Status

`DEFINITION_ONLY_PREREGISTERED`

## Identity

- Hypothesis: `VOLATILITY_DECAY_BREAKOUT_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_DECAY_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Target phenomenon: `VOLATILITY_DECAY_AFTER_HIGH_VOL_THEN_CHANNEL_BREAKOUT`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`

## Binding

- SSOT: `config/research/volatility_decay_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Validator: `src/research/volatility_decay_breakout_v1_hypothesis_preregistration_v1.py`
- Evidence: `docs/evidence/preregister_volatility_decay_breakout_hypothesis_v1/`
- Forensic prior: `docs/evidence/forensic_classify_vep_v1_unpairable_entry_no_exit_v1/`

## Mechanism (frozen)

- Vol estimator: ATR(14)/close percentile-rank lookback 120
- Decay confirmation on completed bar t: percentile(t-1) >= 0.70 and percentile(t) < 0.40 with strictly decreasing normalized ATR
- Entry window: t+1..t+8 (never on confirmation bar t)
- Direction: shared unconditional 20-bar channel breakout
- Event: single-use; max one entry; rearm requires percentile >= 0.70
- Exit: declarative bind to productive VCB exit/PnL evaluator (no second PnL truth)

## Material difference

- vs VEP-V1: decay (high→low) vs expansion persistence; different thresholds/window/rearm; not exit repair
- vs VCB-V1: no compression prerequisite; decay transition vs compression→expansion
- vs coiled-spring: not coincident high-vol filter; panel/baseline differ
- vs baseline: decay admission present

## Gates

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `HOLDOUT_FORBIDDEN=true` / unbound
- `DEVELOPMENT_RUN_COUNT=0` / `RUN_LIMIT=1`
- `STRATEGY_IMPLEMENTATION_PRESENT=false`
- `PROMOTION_ELIGIBLE=false` / economic gate closed

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
