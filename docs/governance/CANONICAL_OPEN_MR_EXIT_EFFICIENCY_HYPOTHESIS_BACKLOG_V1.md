# Canonical open MR exit-efficiency hypothesis backlog v1

## Current SSOT status

- Lane status: `POST_TERMINAL_OPERATOR_DECISION_REQUIRED` under shared lifecycle contract V1
- Explicit operator decision pending (no awaiting/closeout/successor recorded in this slice)
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`
- Auto-close: forbidden (`lane_auto_closed=false`)
- Explicit waiting: `explicit_waiting_decision=false`
- Explicit closeout: `explicit_closeout_decision=false` (lane is **not** closed)
- Preregistered: none (`preregistered_count_exact=0`)
- Terminal: V1&#47;V2&#47;V7 `INCONCLUSIVE_INFRASTRUCTURE_FAILURE`; V3&#47;V6 `FAIL`; V4&#47;V5 `INFRASTRUCTURE_FAILURE`; V8 `TERMINAL_PASS`
- Holdout V1 terminal FAIL: `RESULT_CLASS=FAIL`; `REASON=NET_PROFIT_FACTOR_NOT_IMPROVED`; `HOLDOUT_RUN_COUNT=1`; evidence under `docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/`
- V7 remains terminal unreopened: `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`; `FAILURE_CLASS=FROZEN_EXIT_PARAMETERS_MISMATCH`; `FAILURE_TIMING=BEFORE_PANEL_ACCESS`
- V8 terminal PASS: `RESULT_CLASS=PASS`; `DECISION_REASON=ALL_PASS_REQUIRES_MET`; `EVALUATION_RUN_COUNT=1`; `RUN_SLOT_CONSUMED=true`; `RERUN_ALLOWED=false`; `V8_REOPEN_ALLOWED=false`
- V8 digest: `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c` (immutable)
- V8 panel digest: `4a1978fe0e69a6cd7b19b32f5f95882cfdc3e36397aaec87bce2c4139ab1cfca`
- Development run count: `8`
- No V8&#47;V7&#47;V6&#47;V5&#47;V4&#47;V3&#47;V2&#47;V1 rerun. No V7&#47;V8 reopen. No V9 auto-create. No second holdout run. No runtime promotion from DEVELOPMENT PASS.
- `NEXT_CANONICAL_ACTION=REVIEW_TERMINAL_HOLDOUT_FAIL_NO_RETRY`
- Economic&#47;promotion gates closed. No runtime&#47;orders.

---
docs_token: DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1
STATUS: POST_TERMINAL_OPERATOR_DECISION_REQUIRED_AFTER_HOLDOUT_V1_TERMINAL_FAIL
scope: research, offline-only, non-authorizing, terminal-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

## Status

`POST_TERMINAL_OPERATOR_DECISION_REQUIRED` — after the single authorized holdout
successor terminated as `FAIL` / `NET_PROFIT_FACTOR_NOT_IMPROVED`, inventories are
empty and no explicit awaiting, closeout, or successor-creation decision is
recorded yet. Auto-close is forbidden.

Lane-status vocabulary and post-terminal legality are owned solely by
`CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`.
`OPEN_BACKLOG` is invalid for this empty-inventory posture.
The non-canonical cross-lane label `CLOSED_NO_OPEN_CANDIDATES` remains removed; the
sibling Entry Eligibility status mirror uses the canonical lifecycle status only.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Lifecycle authority (sole): `config&#47;research&#47;canonical_research_lane_post_terminal_lifecycle_contract_v1.json`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Preregistered hypotheses

None (`preregistered_count_exact=0`).

## Terminal hypotheses

Exactly eight:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v1&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v2&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
  — `TERMINAL_FAIL`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=FAIL`
  — `REASON=identical_arms_no_exit_divergence`
  — `ACCEPTANCE_CRITERIA_MET=false`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v3&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`
  — `TERMINAL_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INFRASTRUCTURE_FAILURE`
  — `DIAGNOSTIC_CLASS=PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `ACCEPTANCE_CRITERIA_MET=false`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v4&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5`
  — `TERMINAL_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INFRASTRUCTURE_FAILURE`
  — `DIAGNOSTIC_CLASS=PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — Baseline members completed `3&#47;46`; treatment `0&#47;46`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v5&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`
  — `TERMINAL_FAIL`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=FAIL`
  — `REASON=NET_PROFIT_FACTOR_NOT_IMPROVED`
  — `ACCEPTANCE_CRITERIA_MET=false`
  — `EXIT_DIVERGENCE_OBSERVED=true`
  — Mechanism: `canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1`
  — Members completed: baseline `46&#47;46`; treatment `46&#47;46`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v6&#47;`
  — Governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6.md`
  — Failure attribution (evidence-only): `docs&#47;evidence&#47;attribute_bollinger_mr_midband_exit_efficiency_v6_failure&#47;`
  — Attribution governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION.md`


- `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `FAILURE_CLASS=FROZEN_EXIT_PARAMETERS_MISMATCH`
  — `FAILURE_TIMING=BEFORE_PANEL_ACCESS`
  — `PANEL_BACKTEST_EXECUTED=false`
  — `DEVELOPMENT_METRICS_PRODUCED=false`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `STRATEGY_FAIL=false` &#47; `ECONOMIC_FAIL=false` &#47; `MEASUREMENT_PASS=false`
  — `RERUN_ALLOWED=false` &#47; `V7_REOPEN_ALLOWED=false`
  — Digest: `4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7&#47;`
  — Governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V7.md`

- `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8`
  — `TERMINAL_PASS`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=PASS`
  — `DECISION_REASON=ALL_PASS_REQUIRES_MET`
  — `ACCEPTANCE_CRITERIA_MET=true`
  — `PANEL_BACKTEST_EXECUTED=true`
  — `RUN_SLOT_CONSUMED=true`
  — Members completed: baseline `46&#47;46`; treatment `46&#47;46`
  — Cooldown: `24` PT1H bars
  — Digest: `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`
  — `RERUN_ALLOWED=false` &#47; `V8_REOPEN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8&#47;`
  — Governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V8.md`

## Explicit exclusions

- No V1&#47;V2&#47;V3&#47;V4&#47;V5&#47;V6 rerun under consumed preregistrations
- No V3&#47;V4&#47;V5&#47;V6 partial-result, checkpoint, or economic-result reuse
- No holdout after FAIL&#47;INFRASTRUCTURE_FAILURE
- No holdout of V8 DEVELOPMENT identity (successor HOLDOUT_V1 only; now terminal)
- No retuning after FAIL&#47;INFRASTRUCTURE_FAILURE
- No V7 rerun &#47; no V7 reopen
- No V8 rerun &#47; no V8 reopen
- No runtime promotion from DEVELOPMENT PASS
- No V7 auto-create
- No V8 auto-create
- No V9 auto-create
- No parallel SHORT-side hypothesis
- No second HOLDOUT_V1 run &#47; no retry after holdout FAIL
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- No lane auto-close
- Open unpreregistered exit-efficiency candidates: empty
- Preregistered hypotheses: empty (`preregistered_count_exact=0`)

## Next separate action

`NEXT_CANONICAL_ACTION=REVIEW_TERMINAL_HOLDOUT_FAIL_NO_RETRY`

Lane is in `POST_TERMINAL_OPERATOR_DECISION_REQUIRED`. Enumerated further
operator decisions from this state (shared contract):

- `CREATE_SUCCESSOR_HYPOTHESIS` (requires explicit `hypothesis_id` + mechanism)
- `DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS` (requires explicit waiting decision; transitions toward `AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS`)
- `CLOSE_LANE_NO_FURTHER_RESEARCH` (requires explicit closeout decision)

GO alone is never executable without a concrete target. Awaiting authorizes
neither V9, nor holdout, nor runtime&#47;orders.

No V8 rerun. No V8 reopen. No holdout. No runtime&#47;orders. No V9 auto-create.

## V8 terminal evaluation closeout (not lane closeout)

V8 DEVELOPMENT evaluation consumed its one-shot slot and terminated as `PASS`
(`DECISION_REASON=ALL_PASS_REQUIRES_MET`) on the sealed DEVELOPMENT_ONLY panel.
V8 remains terminal and unreopened. PASS is a development evaluation result only
— not a trading, shadow, testnet, scheduler, or live authorization. Economic
offline gate remains closed; promotion remains closed. No V8 rerun. No V8 reopen.
No V9 auto-create.
Historical V8 economic, evaluation, run-slot, and preregistration artifacts
remain immutable, including digest
`610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`.
Evaluation closeout is not `CLOSE_LANE_NO_FURTHER_RESEARCH`.
