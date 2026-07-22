# Volatility Regime Research Program v1

## Status

`DEFINITION_ONLY_PROGRAM_OPEN`

## Active hypothesis

- `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1`
- Predecessor terminal: `VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1`
  (`FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`)
- Also terminal: `VOLATILITY_DECAY_BREAKOUT_V1`, `VOLATILITY_EXPANSION_PERSISTENCE_V1`,
  `VOLATILITY_COMPRESSION_BREAKOUT_V1`

## Binding

- SSOT: `config/research/volatility_regime_research_program_v1.json`
- Backlog: `config/research/volatility_regime_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/volatility_contraction_expansion_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Gates

- Definition-only preregistration (no Development evaluation executed)
- Holdout unbound / forbidden
- Live / orders / scheduler closed
- No retry of terminal VDBX/VDB/VEP/VCB without new separate Operator-GO

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY_PROGRAM_OPEN
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
