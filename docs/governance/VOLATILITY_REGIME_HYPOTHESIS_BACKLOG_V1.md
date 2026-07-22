# Volatility Regime Hypothesis Backlog v1

## Status

`OPEN_BACKLOG` with exactly one definition-only preregistration
(`VOLATILITY_EXPANSION_PERSISTENCE_V1`) after terminal
`VOLATILITY_COMPRESSION_BREAKOUT_V1` `FAIL_CLOSED_NO_RETRY`.

## Identity

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Preregistered hypothesis: `VOLATILITY_EXPANSION_PERSISTENCE_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_EXPANSION_PERSISTENCE_V1`
- Signal family: `VOLATILITY_REGIME`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (DEVELOPMENT_ONLY; holdout unbound&#47;untouched)
- Terminal: `VOLATILITY_COMPRESSION_BREAKOUT_V1` (`FAIL_CLOSED_NO_RETRY`; retry forbidden)

## Binding

- SSOT: `config/research/volatility_regime_hypothesis_backlog_v1.json`
- Validator: `src/research/volatility_regime_hypothesis_backlog_v1.py`
- Program: `config/research/volatility_regime_research_program_v1.json`
- Measurement contract: `config/research/volatility_expansion_persistence_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Strategy implementation binding: `config/research/volatility_expansion_persistence_v1_strategy_implementation_binding_v1.json` (`implementation_present=true`; evaluation still unauthorized)

## Inventories

- open_unpreregistered=0
- preregistered=1
- terminal_hypotheses=1

## Sibling lanes (immutable)

- Entry eligibility: `LANE_CLOSED_NO_FURTHER_RESEARCH`
- Exit efficiency: `LANE_CLOSED_NO_FURTHER_RESEARCH`
- CS momentum program: `PROGRAM_CLOSED_NO_FURTHER_RESEARCH`
- Reopen forbidden

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_REGIME_HYPOTHESIS_BACKLOG_V1
STATUS: OPEN_BACKLOG
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
