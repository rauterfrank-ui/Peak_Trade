# MASTER_V2 Canonical Volatility Numeric Max-Age Productive Bridge Natural Age Lifecycle Wiring v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_NATURAL_AGE_LIFECYCLE_WIRING_V1
STATUS: CAPABILITY_AVAILABLE
scope: bind NaturalAgeProgressionLifecycleHostV1 into the productive Canonical-Volatility evidence bridge/runner path
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

> **Research wiring capability only.**
> Binds `NaturalAgeProgressionLifecycleHostV1` fail-closed into the productive
> bridge / preregistered session runner call graph so natural Volatility ages
> can accumulate across distinct PT1M observations.
> Does **not** select or enforce a numeric max-age, issue/consume authorization,
> create preregistration, execute a productive session, mutate Master-V2 /
> Double-Play / Bull / Bear / Entry-Exit / Risk / Safety semantics, or mutate
> existing Session-02 ledger evidence.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_NATURAL_AGE_LIFECYCLE_WIRING_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_NATURAL_AGE_LIFECYCLE_WIRING_V1
NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND=true
LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE=true
SECOND_AGE_AUTHORITY_PRESENT=false
SECOND_DECISION_AUTHORITY_PRESENT=false
NUMERIC_MAX_AGE_SELECTED=false
NUMERIC_MAX_AGE_ENFORCING=false
SESSION_EXECUTED=false
HARD_STOP=true
```

## Call graph (before → after)

### Before

```
run_preregistered_productive_session_v1
  → run_productive_bridge_accumulation_session_v1
    → HardenedBridgeSessionStateV2.typed_volatility_cmc_binding_host
         = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1
      → CanonicalVolatilityTypedRuntimeProducerScaffoldV1
           rematerializes on every distinct PT1M sample
      → as_of_event_time == market_event_time ⇒ age_seconds == 0
      → presence gate / evidence / join / counterfactual consume age=0
```

### After

```
run_preregistered_productive_session_v1
  → run_productive_bridge_accumulation_session_v1
    → HardenedBridgeSessionStateV2.typed_volatility_cmc_binding_host
         = ProductiveNaturalAgeLifecycleCmcBindingHostV1
      → NaturalAgeProgressionLifecycleHostV1
           (sole produce / reuse / recompute authority)
      → evaluate_recompute_decision_v1 (research wiring, not max-age policy)
      → bind immutable reused estimate into CMC
      → age_seconds = market_event_time - as_of_event_time
      → consumers (evidence, join, counterfactual, strata, safety/risk/exit)
           project canonical age unchanged; no decision authority
```

## Lifecycle state ownership

| Concern | Owner |
|---|---|
| Produce vs reuse vs recompute | `NaturalAgeProgressionLifecycleHostV1` |
| Research recompute floors | `evaluate_recompute_decision_v1` and `ResearchEstimateRecomputePolicyV1` |
| Natural age formula | `compute_natural_age_seconds_v1` |
| Productive CMC bind adapter | `ProductiveNaturalAgeLifecycleCmcBindingHostV1` |
| Evidence / join / CF / strata / safety | consumers only |

## Produce / reuse / recompute semantics

1. **First valid produce** — immutable `as_of_event_time`, `age_seconds=0`, `distinct=0`
2. **Valid distinct reuse** — same estimate / as_of; age grows by market event time; distinct increments once
3. **Duplicate** — `DUPLICATE_NOOP`; no age / counter / estimate drift
4. **Out-of-order** — not evaluable; no counter progress; as_of unchanged
5. **Warmup / not evaluable** — no artificial age / produce
6. **Recompute** — unchanged research contract:

```
RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS=121
RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS=7201
trigger = distinct >= 121 OR elapsed >= 7201
decision evaluated before reuse increment
```

## Age-7200 timeline (PT1M)

After first produce:

| Step | prior.distinct | elapsed | decision | after.distinct | age_seconds |
|---|---:|---:|---|---:|---:|
| +7200 | 119 | 7200 | REUSE | 120 | 7200 |
| +7260 | 120 | 7260 | RECOMPUTE | 0 | 0 |

No recompute before age 7200 under the ratified research wiring.

## Fail-closed invariants

- missing / inconsistent lifecycle state → no evidence accumulation
- negative age → reject
- event-time regression → no state progress
- duplicate must not advance confirmation / distinct counters
- runtime cycle must not synthesize samples or ages
- wallclock sleep must not create productive age
- no synthetic timestamp manipulation
- replay must not be emitted as productive evidence
- Session-02 evidence remains byte-stable
- existing ledgers are append-only / not rewritten by this capability

## Explicit non-goals

- no numeric max-age selection or enforcement
- no Master-V2 / Double-Play / Bull / Bear / Entry-Exit / Risk / Safety mutation
- no second decision authority / trading permission / order activation
- no authorization issuance or consumption
- no preregistration creation
- no productive session execution / network requests
- no Session-02 or historical ledger mutation

## Later research phase

The separate phase **Numeric Max-Age Evidence Derivation** remains research-only and
requires a later operator-authorized plan. This wiring capability stops at

`READY_FOR_POST_MERGE_AUTHORIZATION_PLAN_REASSESSMENT`

with `READY_FOR_SESSION_PREREGISTRATION=false`,
`READY_FOR_AUTHORIZATION_ISSUANCE=false`,
`READY_FOR_PRODUCTIVE_SESSION_EXECUTION=false`,
`READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION=false`,
`HARD_STOP=true`.
