# Volatility Regime Hypothesis Backlog v1

## Status

`OPEN_BACKLOG` — exactly one definition-only preregistered successor
(`VOLATILITY_DECAY_BREAKOUT_V1`) after terminal
`VOLATILITY_EXPANSION_PERSISTENCE_V1` `FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`
and prior terminal `VOLATILITY_COMPRESSION_BREAKOUT_V1` `FAIL_CLOSED_NO_RETRY`.

## Identity

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Preregistered hypothesis: `VOLATILITY_DECAY_BREAKOUT_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_DECAY_BREAKOUT_V1`
- Signal family: `VOLATILITY_REGIME`
- Terminal: `VOLATILITY_COMPRESSION_BREAKOUT_V1`, `VOLATILITY_EXPANSION_PERSISTENCE_V1`
  (both `FAIL_CLOSED_NO_RETRY`; retry forbidden)

## Binding

- SSOT: `config/research/volatility_regime_hypothesis_backlog_v1.json`
- Validator: `src/research/volatility_regime_hypothesis_backlog_v1.py`
- Forensic prior: `docs/evidence/forensic_classify_vep_v1_unpairable_entry_no_exit_v1/`
- Measurement contract: `config/research/volatility_decay_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Strategy implementation binding: `config/research/volatility_decay_breakout_v1_strategy_implementation_binding_v1.json` (`implementation_present=true`; evaluation still unauthorized)

## Inventory

- open_unpreregistered=0
- preregistered=1 (`VOLATILITY_DECAY_BREAKOUT_V1`, run_count=0)
- terminal=2 (VCB + VEP)
- sibling lanes closed / reopen forbidden

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
