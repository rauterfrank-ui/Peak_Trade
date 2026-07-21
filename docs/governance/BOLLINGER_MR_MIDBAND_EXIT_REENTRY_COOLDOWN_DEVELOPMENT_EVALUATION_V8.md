---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V8
STATUS: IMPLEMENTATION_WIRED_READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION
implementation_lifecycle_status: READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION
scope: research, offline-only, wiring-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR midband exit reentry-cooldown — DEVELOPMENT evaluation V8

> Wiring-only. No evaluation run. No run-slot claim. No panel&#47;holdout access.
> Immutable preregistration digest unchanged:
> `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`
> Preregistration field `evaluation_authorized` remains `false`.

## Status

`READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION`

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8`
- Owner: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V8`
- CLI: `scripts&#47;research&#47;run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8.py`
- Default CLI mode: preflight-only
- Evaluate requires hypothesis-specific authorization flag **and** effective ratification&#47;lifecycle authorization
- Pre-authorization parity validator bound before runner authorization &#47; slot
- Cooldown: `24` PT1H bars
- Predecessor V7 remains terminal: `INCONCLUSIVE_INFRASTRUCTURE_FAILURE` &#47; `FROZEN_EXIT_PARAMETERS_MISMATCH`

## Explicit non-actions

No evaluation in this slice. No slot&#47;panel. No V7 reopen. No holdout.
No LIVE&#47;ORDERS&#47;SHADOW&#47;TESTNET&#47;SCHEDULER&#47;CAPITAL.
No Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation.
