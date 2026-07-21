---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V7
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-only preregistration
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR midband exit reentry-cooldown — preregistered hypothesis measurement V7

> **Non-authorizing.** Definition-only preregistration. No evaluation. No panel&#47;holdout
> access. No runtime&#47;orders. No V7 auto-evaluation. Separate Operator-GO required for
> the single authorized DEVELOPMENT evaluation run.

## Status

`DEFINITION_ONLY_PREREGISTERED`

- `EVALUATION_RUN_COUNT=0`
- `EVALUATION_AUTHORIZED=false`
- `RUNTIME_IMPLEMENTATION_IN_THIS_SLICE=false`
- Digest: `4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680`
- Cooldown: `24` PT1H bars; scope `instrument_id + direction`
- Control: exact V6 composite midband&#47;max-hold semantics
- Treatment: V6 semantics + same-side reentry cooldown after forced midband exit

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7`
- Mechanism: `canonical_bollinger_side_aware_midband_exit_with_frozen_max_holding_and_same_side_reentry_cooldown_v1`
- Contract: `config&#47;research&#47;bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json`
- Evidence: `docs&#47;evidence&#47;preregister_bollinger_mr_midband_exit_reentry_cooldown_hypothesis_v7&#47;`
- Predecessor V6: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6` (`FAIL`, run count `1`)
- Attribution: `docs&#47;evidence&#47;attribute_bollinger_mr_midband_exit_efficiency_v6_failure&#47;`

## Causal boundary

`forced_exit_execution -> cooldown_state_activation -> subsequent_same_side_entry_eligibility`

## Explicit non-actions

No V7 evaluation in this slice. No V6 rerun. No holdout. No midband&#47;max-hold retune.
No entry-signal change. No dynamic cooldown tuning. No runtime&#47;orders.
No Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation. No V8 auto-create.
