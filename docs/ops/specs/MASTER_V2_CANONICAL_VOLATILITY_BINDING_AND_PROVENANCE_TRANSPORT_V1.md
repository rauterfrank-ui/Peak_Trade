# MASTER_V2 Canonical Volatility Binding and Provenance Transport v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_BINDING_AND_PROVENANCE_TRANSPORT_V1
STATUS: CAPABILITY_AVAILABLE
scope: typed CMC transport + single validation + single legacy adaptation + evidence identity; non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_WIRING: false
RUNTIME_PRODUCER_CUTOVER: false
DEFAULT_MUTATION: false
PARAMETER_EFFECT: false
TRADING_LOGIC_EFFECT: false
VOLATILITY_MAX_AGE_VALUE_UNRESOLVED: true
HARD_STOP: true
---

> **Non-authorizing C1 scaffold.** Implements Typed-Transport Model A for
> Master V2 &#47; Double Play volatility. Reuses existing semantics, materializer,
> and typed consumption&#47;adapter owners. Does **not** mutate defaults
> (`0.2` &#47; `0.02` &#47; `1.0` &#47; `1e-9`), cut over wallclock&#47;panel producers,
> change survival&#47;futures profile semantics, authorize runtime, or invent a
> numeric max-age.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_BINDING_AND_PROVENANCE_TRANSPORT_V1
TYPED_TRANSPORT_MODEL=A
TYPED_CARRIER_END_BOUNDARY=CanonicalMarketContextV1.canonical_volatility_estimate
SINGLE_VALIDATION_BOUNDARY=validate_canonical_volatility_estimate_v1
LEGACY_ADAPTATION_BOUNDARY=adapt_canonical_volatility_estimate_to_legacy_float_v1
SECOND_ESTIMATOR_REQUIRED=false
SECOND_SEMANTICS_AUTHORITY_REQUIRED=false
GENERAL_INPUT_DIGEST_ALONE_SUFFICIENT=false
READY_FOR_RUNTIME_WIRING=false
READY_FOR_PARAMETER_RESEARCH=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
VOLATILITY_MAX_AGE_VALUE_UNRESOLVED=true
```

## Owner decisions consumed

| ID | Decision |
|---|---|
| O4 | Single canonical producer chain ratified; non-aliases unchanged |
| O9 | Typed transport Model A; CMC typed end-boundary; single adapter before float consumers |
| O10 | Full estimate identity in Decision Evidence + volatility input binding digest |
| O12 | Typed-path fail-closed domain matrix for missing&#47;invalid (legacy eligibility unchanged) |
| O13 | Equivalence target scaffolding only; no producer unification in C1 |

## Zielgraph

```
finalized PT1M mark_prices
  → materializer (REUSE)
  → CanonicalVolatilityEstimateV1
  → validate_canonical_volatility_estimate_v1          [SINGLE_VALIDATION]
  → CanonicalMarketContextV1.canonical_volatility_estimate  [TYPED_END]
  → adapt_canonical_volatility_estimate_to_legacy_float_v1  [SINGLE_LEGACY]
  → Scope Snapshot &#47; DynamicScopeRules &#47; update_dynamic_boundaries (float)
  → CanonicalTradingDecisionEvidenceV1.volatility_provenance
```

## Evidence schema

`CanonicalVolatilityDecisionEvidenceProvenanceV1` persists at least:

- `volatility_contract_version`, `value`, `unit`, `horizon`, `annualized`
- `estimator`, `observation_count`, `as_of_event_time`, `fallback_used`
- `source_digest`, `typed_estimate_digest`, `legacy_adaptation_digest`
- `stale_status`, `validation_result`, `volatility_input_binding_digest`
- `legacy_float_value` (adapted consumer value)

`input_digest` remains; alone it is **not** sufficient.

## Fail-closed matrix (typed binding path)

| Condition | Exposure | Scope init | Observation&#47;Recon | Risk&#47;Safety&#47;Exit |
|---|---|---|---|---|
| MISSING_TYPED_ESTIMATE | block | block | allowed | independent |
| INVALID &#47; FALLBACK &#47; WRONG META | block | block | allowed | independent |
| WARMUP (CMC warmup_status) | block | block | observation-only | independent |
| STALE status | transport-only in C1; numeric age unresolved | | | independent |

Legacy float-only CMC construction remains eligible under the pre-existing
eligibility function (G8 global enforcement deferred).

## Gaps

Closed by C1: `G3_TRANSPORT`, `G6_BINDING_SCAFFOLD`, `G11_EVIDENCE_SCHEMA`

Remaining: `G4`, `G5`, `G7`, `G8`, `G9`, `G10_NUMERIC_MAX_AGE`,
`G12`, `G13`, `G14`, `G15`

`G1` / `G2` default quarantine is owned by
`MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1`.

## Scope exclusions

Historical `0.2`, scenario `0.02`, rules default `1.0`, and floor `1e-9` are
owned by C2 quarantine (`MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1`).
C1 still does not cut over wallclock&#47;panel producers, survival ratio, futures
profile, risk&#47;safety&#47;exit&#47;entry&#47;composition, parameter research, or
runtime&#47;live.

## Rollback boundary

Remove typed CMC field usage, evidence provenance attachment, and binding
module; float-only paths remain behavior-compatible when typed field is
absent (`None` omitted from digests).

## Owners (reuse-before-new)

| Surface | Owner |
|---|---|
| Semantics | `canonical_volatility_estimate_feature_contract_v1` |
| Estimator | `canonical_volatility_estimate_materializer_v1` |
| Typed carrier &#47; legacy adapter | `canonical_volatility_estimate_typed_consumption_contract_v1` |
| Binding &#47; provenance transport | `canonical_volatility_binding_and_provenance_transport_v1` |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_binding_and_provenance_transport_v1.py` |
