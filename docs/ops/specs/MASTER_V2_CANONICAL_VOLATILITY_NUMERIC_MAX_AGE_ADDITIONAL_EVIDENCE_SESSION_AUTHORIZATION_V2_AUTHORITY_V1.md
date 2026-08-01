# MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_AUTHORIZATION_V2_AUTHORITY_V1

## Capability

Sole productive issuance authority for:

`canonical_volatility_numeric_max_age_additional_evidence_session_authorization&#47;v2`

OWNER=`research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2`

ADDITIONAL_EVIDENCE_AUTHORIZATION_V2_SOLE_ISSUANCE_AUTHORITY=true  
WALLCLOCK_AUTHORIZATION_WRITER_UNCHANGED=true  
CAMPAIGN_AUTHORIZATION_V1_UNCHANGED=true  
NO_SECOND_ISSUANCE_AUTHORITY=true  

HARD_STOP=true  
AUTHORIZATION_ISSUED=false  
READY_FOR_AUTHORIZATION_ISSUANCE=false  
READY_FOR_PRODUCTIVE_SESSION_EXECUTION=false  

## Problem / Blocker

The existing wallclock `authorization_artifact_v2` writer hard-binds:

- `network_scope == PUBLIC_MARKET_DATA_ONLY`
- `duration_seconds == 3600`

The additional-evidence v2 preregistration requires:

- `REQUIRED_NETWORK_SCOPE=OKX_EEA_FUTURES_PUBLIC_MARKET_DATA_READ_ONLY`
- `REQUIRED_DURATION_SECONDS=10860`

plus typed `code_baseline_sha`, `execution_sha`, `critical_surface_digest`,
`instrument`, and `session_scope`. Campaign authorization v1 remains bound to
the exhausted s01/s02 campaign and is not a v2 issuance authority.

## Authority Boundary

- Does **not** loosen wallclock writer invariants.
- Does **not** extend/reactivate campaign authorization v1.
- Does **not** issue on import.
- Does **not** open network or execute sessions.
- Issuance dry-run is the default test/operator safety path.

## Schema and Bindings

Closed-world typed fields include authorization identity/digests,
preregistration + contract bindings, repository SHA semantics, venue/
instrument/network/session scope, duration, time window, single-use,
confirm-token digests/fingerprints/bindings, and consumption/revocation
state + ledger references.

Exact enforcement:

- network scope and duration as above
- venue/instrument/session_scope from preregistration
- code baseline ancestor of execution SHA
- critical-surface digest validated at execution SHA
- unknown version/fields rejected
- cross-authority wallclock/campaign artifacts rejected

## Lifecycle and Single-use

- Single-use authorization only
- Append-only consumption and revocation ledgers
- Revocation fail-closed before consume
- Confirm-token fingerprint/digest/binding; no plaintext persistence/logging

## Consume-before-side-effects

CONSUME_BEFORE_SESSION_LOCK=true  
CONSUME_BEFORE_EVIDENCE_CREATION=true  
CONSUME_BEFORE_NETWORK=true  
CONSUME_BEFORE_RUNTIME_INITIALIZATION=true  

Order: load → validate → revocation check → confirm-token check → atomic
consume → durable confirm → only then session lock / evidence / network /
runtime initialization.

## Operator workflow

```
PREREGISTRATION_V2_READY
  → AUTHORIZATION_V2_ISSUANCE (separate operator GO)
  → EXECUTE_EXACTLY_ONE_SESSION (separate operator GO)
  → VERIFY_TERMINAL_EVIDENCE
```

This capability package only implements and tests the authorization authority.
