# VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1 — Development Evaluation Entry Point

## Status

`RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`

Historical development slot status: `CONSUMED_NO_RETRY`.
Accounting defect does not authorize retry. No evaluation re-execution.
Baseline declarative EOI/EOP pairing is aligned to the canonical productive ledger
policy in a separate non-evaluating governance scope.

Canonical decision record:
`docs/governance/VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_HISTORICAL_SLOT_CONSUMED_NO_RETRY_AND_BASELINE_END_OF_SERIES_PAIRING_V1.md`

## Canonical entry point

`scripts/research/run_evaluate_volatility_expansion_pullback_continuation_development_v1.py`

## Binding

`config/research/volatility_expansion_pullback_continuation_v1_development_evaluation_entry_point_binding_v1.json`

## Safety

- `DEVELOPMENT_EVALUATION_EXECUTED=false`
- `DEVELOPMENT_RUN_COUNT=1`
- `DEVELOPMENT_SLOT_CONSUMED=true`
- `HISTORICAL_VEPC_SLOT_STATUS=CONSUMED_NO_RETRY`
- `EVALUATION_RETRY_AUTHORIZED=false`
- `HOLDOUT_ACCESSED=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- Productive PnL evaluator reused (not duplicated)

docs_token: DOCS_TOKEN_VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
