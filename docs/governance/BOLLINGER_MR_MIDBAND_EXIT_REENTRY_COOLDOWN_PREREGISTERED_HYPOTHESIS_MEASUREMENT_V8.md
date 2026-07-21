---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V8
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-only preregistration
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR midband exit reentry-cooldown — preregistered hypothesis measurement V8

> **Non-authorizing.** Definition-only preregistration. No evaluation. No panel&#47;holdout
> access. No runtime&#47;orders. No V8 auto-evaluation. Separate Operator-GO required for
> the single authorized DEVELOPMENT evaluation run.

## Status

`DEFINITION_ONLY_PREREGISTERED`

- `EVALUATION_RUN_COUNT=0`
- `EVALUATION_AUTHORIZED=false`
- `RUNNER_STARTED=false`
- `RUN_SLOT_CONSUMED=false`
- `RUNTIME_IMPLEMENTATION_IN_THIS_SLICE=false`
- Digest: `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`
- Cooldown: `24` PT1H bars; scope `instrument_id + direction`
- Control: exact V6 composite midband&#47;max-hold semantics
- Treatment: V6 semantics + same-side reentry cooldown after forced midband exit
- Structural hardening vs V7: complete `exit_mechanism.frozen_parameters` SSOT +
  pre-authorization parity validator (fail-closed before runner authorization &#47; slot)

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8`
- Mechanism: `canonical_bollinger_side_aware_midband_exit_with_frozen_max_holding_and_same_side_reentry_cooldown_v1`
- Contract: `config&#47;research&#47;bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v8.json`
- Evidence: `docs&#47;evidence&#47;preregister_bollinger_mr_midband_exit_reentry_cooldown_hypothesis_v8&#47;`
- Predecessor V7: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7`
  (`INCONCLUSIVE_INFRASTRUCTURE_FAILURE`, `FROZEN_EXIT_PARAMETERS_MISMATCH`, run count `1`, no reopen)
- Attribution: `docs&#47;evidence&#47;attribute_bollinger_mr_midband_exit_efficiency_v6_failure&#47;`
- Pre-auth validator: `src&#47;research&#47;bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v8.py::validate_pre_authorization_frozen_parameter_parity`

## Causal boundary

`forced_exit_execution -> cooldown_state_activation -> subsequent_same_side_entry_eligibility`

## Explicit non-actions

No V8 evaluation in this slice. No V7 reopen&#47;retry. No V6 rerun. No holdout.
No midband&#47;max-hold retune. No entry-signal change. No dynamic cooldown tuning.
No runtime&#47;orders. No Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation.
No V9 auto-create. No second exit-parameter truth. No implicit frozen-parameter defaults.
