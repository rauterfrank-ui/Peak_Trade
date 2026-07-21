---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7
STATUS: OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY
implementation_lifecycle_status: READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION
scope: research, offline-only, non-authorizing, implementation-clarification overlay
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR midband exit reentry-cooldown — Operator Clarification Authority V7

> **Non-authorizing overlay.** Clarifies executable measurement&#47;lifecycle semantics for
> B1–B6 without mutating the immutable V7 preregistration or digest
> `4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680`.
> `evaluation_authorized=false`. `evaluation_run_count=0`. No evaluation in this slice.

## Authority

- ID: `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7`
- Contract: `config&#47;research&#47;bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7.json`
- Module: `src&#47;research&#47;bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7.py`
- Scope: `IMPLEMENTATION_CLARIFICATION_ONLY`
- Status marker: `OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY`
- Implementation lifecycle: `READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION`

## Precedence

1. Economic hypothesis and registered measurement targets remain from the unchanged preregistration.
2. For implementation ambiguities B1–B6 only, this authority is execution-binding.
3. Forbidden: new economic hypothesis, new treatment effect, post-hoc result adjustment, prereg mutation.

## B1–B6 (resolved)

| ID | Executable clarification |
|---|---|
| B1 | Pure reentry-cooldown; exit fills identical; required divergence at reentry eligibility |
| B2 | MaxDD signed negative; PASS iff `treatment >= control` |
| B3 | Incomplete infra → `INCONCLUSIVE_INFRASTRUCTURE_FAILURE` &#47; `NOT_EVALUATED` |
| B4 | Arm at t; block t..t+24; first eligible t+25; PT1H index counting |
| B5 | Explicit same-bar reentry block + counter |
| B6 | Gap&#47;dup&#47;sort&#47;freq fail-closed; panel integrity uses existing `INVALID_MEASUREMENT_*` |

B7&#47;B8 are confirmed by authority and fulfilled only via wiring + tests.

## Explicit non-actions

No evaluation. No panel&#47;holdout access. No run-slot claim. No runtime&#47;orders.
No Protected-Core mutation. No second preregistration.
