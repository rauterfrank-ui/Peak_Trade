# Canonical open MR exit-efficiency hypothesis backlog v1

---
docs_token: DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1
STATUS: OPEN_BACKLOG
scope: research, offline-only, non-authorizing, definition-only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for open Mean-Reversion exit-efficiency
research candidates. Definition-only governance. Exactly one hypothesis is
`DEFINITION_ONLY_PREREGISTERED`. No evaluation, no holdout access, no runtime
activation, no productive trading-logic mutation in this slice.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Preregistered hypotheses

Exactly one:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
  — `DEFINITION_ONLY_PREREGISTERED`
  — `EVALUATION_RUN_COUNT=0`
  — `EVALUATION_RUN_LIMIT=1`
  — `DEVELOPMENT_ONLY=true`
  — `HOLDOUT_ALLOWED=false`

## Explicit exclusions

- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- Open unpreregistered exit-efficiency candidates: empty

## Sibling lane

Entry-eligibility backlog remains empty for open candidates:
`config&#47;research&#47;canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json`.

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_EXIT_EFFICIENCY_PREREGISTRATION_BEFORE_ANY_DEVELOPMENT_EVALUATION`
