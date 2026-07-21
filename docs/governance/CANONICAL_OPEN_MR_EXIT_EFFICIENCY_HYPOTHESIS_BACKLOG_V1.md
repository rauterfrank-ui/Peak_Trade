# Canonical open MR exit-efficiency hypothesis backlog v1

---
docs_token: DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1
STATUS: OPEN_BACKLOG
scope: research, offline-only, non-authorizing, terminal-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for Mean-Reversion exit-efficiency
research candidates. Open preregistered queue is empty after the sole midband
hypothesis terminated as infrastructure inconclusive. No rerun under that
preregistration. No holdout access. No runtime activation. No productive
trading-logic mutation.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Terminal hypotheses

Exactly one:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `EVALUATION_STARTED=true`
  — `EVALUATION_COMPLETED=false`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v1&#47;`

## Preregistered hypotheses

Empty.

## Explicit exclusions

- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- No V2 preregistration in this closeout slice
- Open unpreregistered exit-efficiency candidates: empty

## Next separate action

Not authorized here: fix generic runner lifecycle&#47;observability synthetically,
then optionally consider a separate V2 preregistration with a new hypothesis ID
and run count 0 under a new Operator-GO.
