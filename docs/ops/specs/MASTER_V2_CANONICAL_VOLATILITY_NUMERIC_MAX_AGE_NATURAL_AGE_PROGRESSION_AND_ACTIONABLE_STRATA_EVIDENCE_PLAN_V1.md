# MASTER_V2 Canonical Volatility Numeric Max-Age Natural Age Progression And Actionable Strata Evidence Plan v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_NATURAL_AGE_PROGRESSION_AND_ACTIONABLE_STRATA_EVIDENCE_PLAN_V1
STATUS: CAPABILITY_AVAILABLE
scope: research-only natural estimate lifecycle, actionable strata evidence projection, extended counterfactual join, and additional coverage plan
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
NUMERIC_MAX_AGE_SECONDS: null
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
ENFORCEMENT_APPLIED: false
COUNTERFACTUAL_ONLY: true
THRESHOLD_SELECTED: false
SESSION_EXECUTION_AUTHORIZED: false
AUTHORIZATION_ISSUANCE_AUTHORIZED: false
BLOCKED_FOR_PARAMETER_DECISION: true
HARD_STOP: true
---

> **Research evidence-plan capability only.**
> Introduces an explicit natural VolatilityEstimate lifecycle and actionable
> strata / counterfactual impact surfaces so future productive sessions can
> observe age variation without selecting or enforcing a numeric max-age.
> Does **not** execute sessions, issue/consume authorization, mutate
> Master-V2 / Double-Play / Bull / Bear / Risk / Exit semantics, or promote a
> threshold.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_NATURAL_AGE_PROGRESSION_AND_ACTIONABLE_STRATA_EVIDENCE_PLAN_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_NATURAL_AGE_PROGRESSION_AND_ACTIONABLE_STRATA_EVIDENCE_PLAN_V1
AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME
ESTIMATE_RECOMPUTE_TRIGGER_EXPLICIT=true
ESTIMATE_REUSE_EXPLICIT=true
NO_POLICY_ENFORCEMENT=true
NUMERIC_MAX_AGE_SELECTED=false
NUMERIC_MAX_AGE_ENFORCING=false
SESSION_EXECUTED=false
HARD_STOP=true
```

## Session-02 sufficiency gap

Session 02 completed with integrity pass but policy insufficiency:

- `VALID_AGE_COUNT=68`, `MIN_AGE_SECONDS=0`, `MAX_AGE_SECONDS=0`
- `CANDIDATE_DISCRIMINATION_OBSERVED=false`
- `INCREMENTAL_ALPHA_EFFECT_OBSERVED=false`
- `STALE_PATH_EMPIRICALLY_OBSERVED=false`
- all outcomes already `blocked` / `no_selection`

Root cause: the typed runtime producer rematerializes on every distinct sample,
so `as_of_event_time == market_event_time` and natural aging never appears.
Session 02 must not be retried by this capability.

## Natural estimate lifecycle

Owner:

`src&#47;research&#47;canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1&#47;lifecycle_host_v1.py`

Contract:

`VolatilityEstimateLifecycleState` retains a typed estimate with immutable
`as_of_event_time` during reuse. Age is always:

`current_market_event_time - estimate.as_of_event_time`

No sleeps, timestamp injection, or runtime-cycle age synthesis.

## Recompute cadence vs max-age policy

The research recompute wiring decides **only** when a new estimate is produced.
It is explicitly labeled

`RESEARCH_ESTIMATE_RECOMPUTE_WIRING_NOT_MAX_AGE_POLICY`

Derived floors (not a threshold recommendation):

- `minimum_event_time_elapsed_seconds = 7201`
- `minimum_new_distinct_observations = 121`

Ordinary PT60M window sliding must not force recompute. This wiring is not an
Alpha allow&#47;block policy and not a numeric max-age selection.

## Actionable strata and counterfactual join

Each evidence projection can carry strata such as age bucket, reuse counters,
regime&#47;side&#47;decision outcomes, entry opportunity, and exit&#47;risk&#47;safety
availability flags. These fields transport existing productive outputs only.

Counterfactual candidate grid remains:

`60, 120, 300, 600, 900, 1800, 3600, 7200`

Impact aggregates include fresh&#47;stale&#47;not-evaluable counts and incremental
age-only blocks distinct from already-blocked non-age outcomes. Stale
counterfactual blocks Alpha only; exit&#47;risk&#47;safety&#47;reconciliation remain
observationally available. No enforcing stale gate is implemented.

## Additional evidence coverage plan

Frozen artifact:

`config&#47;research&#47;canonical_volatility_numeric_max_age_natural_age_progression_additional_evidence_coverage_plan_v1.json`

Requires future multi-session natural age coverage, candidate discrimination,
actionable long&#47;short&#47;entry strata, counterfactual stale records, and natural
7200s reachability — without artificial delay. This capability does **not**
register or execute those sessions.

## Productive bridge wiring (follow-on capability)

The lifecycle host is bound into the productive bridge runner by

`MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_NATURAL_AGE_LIFECYCLE_WIRING_V1`

via `ProductiveNaturalAgeLifecycleCmcBindingHostV1`. That wiring capability owns
the productive produce&#47;reuse&#47;recompute authority and Age-7200 reachability proof.
This evidence-plan capability remains the research contract owner for lifecycle,
strata, counterfactual impact, and coverage plan surfaces.

## Next later step

A separate operator-authorized Authorization &#47; Execution plan is required before
any productive session. The Numeric Max-Age Evidence Derivation phase remains
research-only. This capability stops at

`READY_FOR_ADDITIONAL_EVIDENCE_AUTHORIZATION_PLAN`.

`READY_FOR_PRODUCTIVE_SESSION_EXECUTION=false`  
`READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION=false`  
`HARD_STOP=true`
