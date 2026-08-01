# MASTER_V2 Canonical Volatility Numeric Max-Age Policy Contract And Non-Enforcing Telemetry v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_POLICY_CONTRACT_AND_NON_ENFORCING_TELEMETRY_V1
STATUS: CAPABILITY_AVAILABLE
scope: versioned non-enforcing estimate-age policy contract and diagnostic telemetry
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
NUMERIC_THRESHOLD_SELECTED: false
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
COMPUTED_AGE_DIAGNOSTIC_ONLY: true
HARD_STOP: true
---

> **Non-enforcing policy contract.** Implements the ratified Event-Time age
> semantics for `CanonicalVolatilityEstimateV1` as typed policy &#47; evidence
> types and diagnostic telemetry attached to the existing Double-Play typed
> volatility presence gate. Does **not** select a numeric threshold, enable
> Alpha enforcement, rematerialize estimates, or create a second clock &#47;
> volatility &#47; Alpha authority.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_POLICY_CONTRACT_AND_NON_ENFORCING_TELEMETRY_V1
POLICY_NAME=canonical_volatility_numeric_max_age_policy
POLICY_VERSION=canonical_volatility_numeric_max_age_policy/v1
AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME
AGE_REFERENCE_FIELD=CanonicalMarketContextV1.market_event_time
AGE_TIMESTAMP_FIELD=CanonicalVolatilityEstimateV1.as_of_event_time
AGE_FORMULA=reference_market_event_time_-_estimate.as_of_event_time
THRESHOLD_STATUS=UNRESOLVED_MAX_AGE
NUMERIC_MAX_AGE_SECONDS=null
ENFORCEMENT_ENABLED=false
UNRESOLVED_MAX_AGE_IS_NOT_FRESHNESS_APPROVAL=true
COMPUTED_AGE_IS_DIAGNOSTIC_ONLY=true
NO_NUMERIC_THRESHOLD_SELECTED=true
NO_ALPHA_ENFORCEMENT_ENABLED=true
REMATERIALIZATION_POLICY=FORBIDDEN
GATE_OWNER=evaluate_double_play_runtime_typed_volatility_presence_gate_v1
SEPARATE_FRESHNESS_GATE_CREATED=false
SECOND_CLOCK_AUTHORITY_CREATED=false
SECOND_VOLATILITY_AUTHORITY_CREATED=false
SECOND_ALPHA_DECISION_AUTHORITY_CREATED=false
GLOBAL_STALENESS_GATE_CREATED=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
```

## Goals

- Typed policy contract with unresolved threshold
- Deterministic Event-Time age computation (`computed_age_seconds`)
- Non-enforcing evidence attached to the existing presence gate
- Compose ClockTrust &#47; DataIntegrity &#47; Presence &#47; Reuse &#47; Restart without replacing them
- Offline &#47; runtime equivalence for identical Event-Time inputs

## Non-goals

- numeric `max_age_seconds` selection or derivation
- FRESH &#47; STALE productive enforcement
- Alpha &#47; Scope &#47; Boundary &#47; Directional blocking by age
- Rematerialization
- Separate freshness gate or global staleness gate
- Live &#47; Testnet &#47; Shadow &#47; order routing
- Numeric threshold selection or parameter-research execution
  (structural research-design &#47; evidence-accumulation is a separate next capability)

Restart labels used by age telemetry: `NOT_APPLICABLE`,
`RESTART_WITHOUT_ESTIMATE`, `FIRST_PRODUCTION_AFTER_RESTART`, `UNKNOWN`.
Producer persistence restores history only and does not rematerialize a typed
estimate; therefore restore is `RESTART_WITHOUT_ESTIMATE` until PRODUCED.

## Ratified Event-Time semantics

```
volatility_estimate_age
  = reference_market_event_time
  - estimate.as_of_event_time
```

- `decision_time` is not a freshness clock
- Wallclock &#47; receive time &#47; runtime &#47; replay cycle are not freshness clocks
- Duplicate &#47; no-sample &#47; process reuse do not refresh age
- Restart &#47; restore leave age `UNDEFINED` until a regular `PRODUCED`
- Rematerialization remains `FORBIDDEN`

## Policy contract

Required structural fields and ratified unresolved values:

| Field | Value |
|---|---|
| threshold_status | `UNRESOLVED_MAX_AGE` |
| numeric_max_age_seconds | `None` |
| enforcement_enabled | `false` |
| rematerialization_policy | `FORBIDDEN` |
| duplicate_reuse_refreshes | `false` |
| no_sample_reuse_refreshes | `false` |
| restart_age_policy | `UNDEFINED_FAIL_CLOSED_UNTIL_PRODUCED` |
| restore_policy | `HISTORY_ONLY_NO_ESTIMATE_NO_FRESH_MARK` |

Illegal constructions are rejected fail-closed (unresolved + numeric threshold,
enforcement without ratified threshold, wrong reference clock, rematerialize
as freshness reset).

## Evidence schema

Evidence fields include `policy_name`, `policy_version`,
`estimate_as_of_event_time`, `reference_event_time`, `computed_age_seconds`,
`max_age_status`, `threshold_status`, `presence_status`, `clock_trust_status`,
`data_integrity_status`, `reuse_status`, `restart_status`, `source_digest`,
`decision`, `reason_code`, `enforcement_applied=false`.

`computed_age_seconds` is emitted only when both Event Times are parseable and
`reference_event_time >= estimate_as_of_event_time`.

## Reason codes

Structural codes include presence &#47; restart &#47; time-coherence codes and
composition hints for untrusted clock &#47; data. `VOLATILITY_ESTIMATE_FRESH` and
`VOLATILITY_ESTIMATE_STALE` exist structurally but are **not** emitted while
`threshold_status=UNRESOLVED_MAX_AGE`. With a computable age and unresolved
threshold the productive diagnostic reason is
`VOLATILITY_ESTIMATE_AGE_UNRESOLVED`.

## Precedence

1. Presence missing &#47; invalid &#47; restart unavailable
2. Data Integrity untrusted &#47; invalid &#47; unknown
3. Clock Trust untrusted &#47; invalid &#47; unknown
4. Volatility Age unresolved
5. Fresh &#47; Stale only after a separate ratified threshold capability

DataIntegrity and ClockTrust remain primary CMC authorities. Age evidence is
secondary &#47; diagnostic only.

## Integration

```
evaluate_double_play_runtime_typed_volatility_presence_gate_v1
  → existing presence Alpha decision (unchanged)
  → evaluate_canonical_volatility_estimate_age_policy_v1 (attached evidence)
```

- `REUSE_EXISTING_TYPED_VOLATILITY_PRESENCE_GATE=true`
- `NO_SEPARATE_FRESHNESS_GATE=true`
- Exit &#47; Risk &#47; Safety authority preserved

## Offline &#47; runtime equivalence

Identical Event-Time inputs yield identical age evidence. Wallclock and
execution duration must not affect results. Productive isolation remains via
`require_productive_typed_volatility_presence_gate`.

## Explicit remaining boundary

```
NEXT_AFTER_THIS_CAPABILITY=
MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_DESIGN_AND_EVIDENCE_ACCUMULATION_CONTRACT_V1
```

Research-design &#47; evidence-accumulation is a separate capability and must not
select a numeric threshold or enable Alpha enforcement.

## Owners

| Artifact | Path |
|---|---|
| Policy &#47; evaluation | `src&#47;trading&#47;master_v2&#47;canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py` |
| Presence-gate attach | `src&#47;trading&#47;master_v2&#47;double_play_runtime_typed_volatility_presence_gate_v1.py` |
| Spec | this document |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1.py` |
