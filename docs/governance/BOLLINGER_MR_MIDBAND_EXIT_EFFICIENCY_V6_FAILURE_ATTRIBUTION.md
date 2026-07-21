---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION
STATUS: EVIDENCE_ONLY_FAILURE_ATTRIBUTION_COMPLETE
scope: research, offline-only, non-authorizing, read-only attribution
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR midband exit-efficiency V6 — failure attribution governance

> **Non-authorizing.** Evidence-only attribution closeout for terminal
> `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`.
> No new evaluation. No raw panel access. No holdout access. No V7 preregistration.
> V6 remains terminal `FAIL` with run count `1`.

## Status

`EVIDENCE_ONLY_FAILURE_ATTRIBUTION_COMPLETE`

- Source result class: `FAIL`
- Source reason: `NET_PROFIT_FACTOR_NOT_IMPROVED`
- Source run count before&#47;after attribution: `1` &#47; `1`
- Primary degradation channel: cost drag from short-side re-entry churn after forced midband exits
- Top bounded V7 candidate proposal (not preregistered): re-entry cooldown after forced midband exit

## Binding

- Attribution evidence: `docs&#47;evidence&#47;attribute_bollinger_mr_midband_exit_efficiency_v6_failure&#47;`
- Source evaluation evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v6&#47;`
- Source governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6.md`
- Backlog SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Owner surface: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION`

## Explicit non-actions

No V6 rerun. No V7 auto-create&#47;preregistration. No holdout. No promotion&#47;economic gate open.
No runtime&#47;orders. No Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation.
Attribution does not authorize candidate selection or evaluation execution.
