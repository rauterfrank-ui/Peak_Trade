# Canonical open MR entry-eligibility hypothesis backlog v1

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for open Mean-Reversion entry-eligibility
research candidates. Definition-only governance. No further evaluation, no holdout
access, no runtime activation, no productive trading-logic mutation in this slice.
Open candidates are empty. Exactly zero hypotheses are `DEFINITION_ONLY_PREREGISTERED`.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type for future preregistrations:
  `ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER`

## Terminal hypotheses

Seven terminal hypotheses remain (six `TERMINAL_FAIL`, one `TERMINAL_PASS`):

- Six prior `TERMINAL_FAIL` families remain forbidden for open candidates
- `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1` remains
  `TERMINAL_PASS` for DEVELOPMENT; its holdout V1 remains terminal
  `ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN` (run count `1&#47;1`)
- Successor holdout V2
  `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2`
  executed once and terminated as `HOLDOUT_EVALUATION_EXECUTED_TERMINAL` / `FAIL` / `NET_PROFIT_FACTOR_NOT_IMPROVED` (run count `1&#47;1`)

## Preregistered hypotheses

None. Holdout V2 is no longer preregistered; it is terminal-executed.

## Forbidden reopen

- No V1 holdout rerun
- No second V2 holdout run without a new hypothesis ID
- No post-result tuning
- Economic gate closed; promotion closed; no runtime/orders

## Next step

`REVIEW_TERMINAL_HOLDOUT_FAIL_NO_RETRY`

## Explicit locks

- `PROMOTION_ELIGIBLE=false`
- `open_candidates=[]`
- ADX DI DEVELOPMENT remains `TERMINAL_PASS` / `ALL_PASS_REQUIRES_MET`
- Economic offline gate remains closed
- Do **not** re-run the ADX DI holdout V1 evaluation. Do **not** re-run holdout V2.

