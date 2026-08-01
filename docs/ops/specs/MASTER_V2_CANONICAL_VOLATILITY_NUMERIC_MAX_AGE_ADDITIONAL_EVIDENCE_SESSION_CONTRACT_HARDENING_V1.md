# MASTER_V2 Canonical Volatility Numeric Max-Age Additional Evidence Session Contract Hardening v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_CONTRACT_HARDENING_V1
STATUS: CAPABILITY_AVAILABLE
scope: fail-closed hardening of additional evidence session preregistration candidate validator (schema version, scope bindings, closed-world fields, authority negative contract, digest consistency)
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NETWORK_AUTHORIZED: false
EXECUTION_AUTHORIZED: false
SESSION_PREREGISTRATION_CREATION_AUTHORIZED: false
AUTHORIZATION_ISSUANCE_AUTHORIZED: false
AUTHORIZATION_CONSUMPTION_AUTHORIZED: false
EVIDENCE_WRITE_AUTHORIZED: false
PARAMETER_DECISION_AUTHORIZED: false
ENFORCEMENT_AUTHORIZED: false
COUNTERFACTUAL_ONLY: true
MAX_AGE_THRESHOLD_SELECTED: false
MAX_AGE_ENFORCEMENT_ENABLED: false
AUTO_PROMOTION_ALLOWED: false
HARD_STOP: true
---

> **Contract-/Validator-Härtung only.**
> Hardens the candidate validator introduced with PR #5627 so unknown or
> incorrectly bound schema, scope, and authority fields fail closed.
> Does **not** create a session preregistration, issue or consume
> authorization, open network, execute a session, select a numeric max-age,
> enable enforcement, or mutate Master-V2 / Double-Play / Entry-Exit / Risk /
> Safety semantics. Existing s01/s02 evidence remains untouched.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_CONTRACT_HARDENING_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_CONTRACT_HARDENING_V1
CONTRACT_CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_PREREGISTRATION_CONTRACT_V1
VALIDATOR_POLICY=FAIL_CLOSED
CANDIDATE_SCHEMA_POLICY=CLOSED_WORLD
UNKNOWN_FIELDS_REJECTED=true
UNKNOWN_AUTHORITY_FIELDS_REJECTED=true
CANDIDATE_SCHEMA_VERSION_EXACT_MATCH=true
VENUE_VALUE_EXACT_MATCH=true
INSTRUMENT_VALUE_EXACT_MATCH=true
NETWORK_SCOPE_VALUE_EXACT_MATCH=true
SESSION_SCOPE_VALUE_EXACT_MATCH=true
NORMALIZATION_OF_BINDING_VALUES_FORBIDDEN=true
CANDIDATE_SCHEMA_CLOSED_WORLD=true
NESTED_OBJECTS_PRESENT=true
PREREGISTRATION_CREATED=false
AUTHORIZATION_ISSUED=false
SESSION_EXECUTED=false
NUMERIC_MAX_AGE_SELECTED=false
NUMERIC_MAX_AGE_ENFORCING=false
HARD_STOP=true
```

## Why this hardening exists

PR #5627 introduced the additional-evidence session preregistration contract.
Three fail-open classes remained:

1. **Schema-version presence without exact bind** — `schema_version` was not
   required to equal exactly one canonical candidate schema version string.
2. **Scope field presence without exact value bind** — `venue`, `instrument`,
   `network_scope`, and `session_scope` were required to exist, but incorrect
   values (case/whitespace/alternate identifiers) were not rejected with
   dedicated binding mismatch codes.
3. **Open-world candidate fields** — unknown top-level keys, including
   authority declarations, were silently ignored; a rehashed digest could not
   make them valid, but they also did not fail closed.

## Exact candidate schema version

Exactly one admissible value:

```
CANDIDATE_SCHEMA_VERSION=
canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate/v1
```

Rejected with `candidate_schema_version_mismatch`:

- missing / null / empty
- unknown version
- contract version used instead of candidate version
- case or whitespace variants
- non-string values

No alias, fallback, or best-effort semantics.

## Exact scope bindings

| Field | Exact expected value |
|---|---|
| `venue` | `OKX` |
| `instrument` | `ETH-USD_UM_XPERP-310404` |
| `network_scope` | `OKX_EEA_FUTURES_PUBLIC_MARKET_DATA_READ_ONLY` |
| `session_scope` | `ADDITIONAL_NATURAL_AGE_EVIDENCE_SESSION_V1` |

Error codes: `venue_binding_mismatch`, `instrument_binding_mismatch`,
`network_scope_binding_mismatch`, `session_scope_binding_mismatch`.

Required field presence alone is **not** sufficient. Every security-relevant
binding value must match exactly. Normalization that would accept a
semantically different value is forbidden.

## Closed-world candidate schema

```
CANDIDATE_SCHEMA_CLOSED_WORLD=true
NESTED_OBJECTS_PRESENT=true
```

An explicit allowlist rejects every unknown top-level key with
`unknown_candidate_fields:<sorted,comma-separated-keys>`.

Nested closed-world checks apply to:

- `authorization_binding`
- `forbidden_artificial_controls`

Unknown fields are **not** accepted as forward compatibility. New schema
fields require a new explicit candidate schema version.

## Authority negative contract

Authority fields are **not** part of the candidate schema. Any declaration of
trading / selection / enforcement / issuance / consumption / session-execution /
order-routing / live / second-age / second-decision authority is rejected via
the closed-world allowlist, regardless of value (`true`, `false`, `null`, `0`,
empty).

No second parallel authority owner is introduced.

```
TRADING_DECISION_AUTHORITY_PRESENT=false
NUMERIC_MAX_AGE_SELECTION_AUTHORITY_PRESENT=false
NUMERIC_MAX_AGE_ENFORCEMENT_AUTHORITY_PRESENT=false
AUTHORIZATION_ISSUANCE_AUTHORITY_PRESENT=false
AUTHORIZATION_CONSUMPTION_AUTHORITY_PRESENT=false
SESSION_EXECUTION_AUTHORITY_PRESENT=false
ORDER_ROUTING_AUTHORITY_PRESENT=false
SECOND_AGE_AUTHORITY_PRESENT=false
SECOND_DECISION_AUTHORITY_PRESENT=false
```

## Digest semantics

A correctly recomputed digest must **not** make a semantically invalid
candidate valid. Unknown fields and wrong scope/schema bindings remain
rejected after rehash. The contract digest includes contract version,
candidate schema version, scope bindings, floors, target-age buckets,
Age-7200 / recompute / post-recompute-fresh requirements,
authorization-per-session / single-use, repository/runbook/design digest
bindings, closed-world policy, and authority negative boundaries.

## Owners

| Surface | Owner |
|---|---|
| Contract package | `src/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1/` |
| Frozen contract artifact | `config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.json` |
| Hardening spec | this document |
| Focused tests | `tests/research/test_canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.py` |

## Explicit non-goals

- no additional session preregistration creation
- no authorization issuance / consumption
- no productive session execution / network
- no numeric max-age selection or enforcement
- no Master-V2 / Double-Play / Entry-Exit / Risk / Safety mutation
- no mutation of existing s01/s02 evidence or preregistration artifacts

## Terminal readiness

```
READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION=false
READY_FOR_AUTHORIZATION_ISSUANCE=false
READY_FOR_PRODUCTIVE_SESSION_EXECUTION=false
READY_FOR_POST_MERGE_CONTRACT_ASSESSMENT=false
HARD_STOP=true
```
