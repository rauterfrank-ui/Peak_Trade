# Canonical open MR entry-eligibility hypothesis backlog v1

## Status

`AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` — explicit operator decision
`DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` recorded under the shared
research-lane post-terminal lifecycle contract. Inventories are empty; all
hypotheses are terminal; `explicit_waiting_decision=true`;
`explicit_closeout_decision=false`; `lane_auto_closed=false`. This is an
explicit operator decision, not an auto-await. No successor hypothesis has been
created or preregistered. Auto-close remains forbidden.

Lane-status vocabulary and post-terminal legality are owned solely by
`CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`.
`OPEN_BACKLOG` is invalid for this empty-inventory posture.

Definition-only governance. No further evaluation, no holdout access, no runtime
activation, no productive trading-logic mutation in this slice. Open candidates
are empty. Exactly zero hypotheses are `DEFINITION_ONLY_PREREGISTERED`.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.py`
- Lifecycle authority (sole): `config&#47;research&#47;canonical_research_lane_post_terminal_lifecycle_contract_v1.json`
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
- No lane auto-close; creating a successor or closing the lane later requires a
  further explicit operator decision under the shared lifecycle contract

## Next step

`AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_NO_EXECUTABLE_GO_WITHOUT_CONCRETE_TARGET`

The lane awaits an explicitly named successor hypothesis. Waiting is named; no
successor identity exists yet. GO alone is never executable without a concrete
target. A later `CREATE_SUCCESSOR_HYPOTHESIS` requires explicit `hypothesis_id` +
mechanism. `CLOSE_LANE_NO_FURTHER_RESEARCH` remains available only via a separate
explicit closeout decision. The historical pointer
`REVIEW_DEFINITION_ONLY_EXIT_EFFICIENCY_PREREGISTRATION_NO_ENTRY_ELIGIBILITY_REOPEN`
is no longer the current canonical next step.

## Next research question (historically consumed into exit-efficiency lane)

`Given COSTS_DESTROY_MARGINAL_EDGE on the sealed DEVELOPMENT_ONLY Bollinger&#47;MR baseline (marginal gross PF~1.01, all-SHORT book), does a cost-structure or holding&#47;exit-efficiency change class exist that preserves gross edge without retuning terminal entry-eligibility parameters or reopening exhausted filter families?`

Historically consumed by sibling exit-efficiency SSOT
`config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
as the then-preregistered hypothesis
`BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`.
Entry-eligibility `open_candidates` remains empty. No entry-eligibility reopen.
No parallel SHORT-side hypothesis. No holdout candidate.

## Explicit locks

- `PROMOTION_ELIGIBLE=false`
- `open_candidates=[]`
- `status=AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS`
- `explicit_waiting_decision=true`
- `explicit_closeout_decision=false`
- `lane_auto_closed=false`
- ADX DI DEVELOPMENT remains `TERMINAL_PASS` / `ALL_PASS_REQUIRES_MET`
- Economic offline gate remains closed
- Do **not** re-run the ADX DI holdout V1 evaluation. Do **not** re-run holdout V2.
