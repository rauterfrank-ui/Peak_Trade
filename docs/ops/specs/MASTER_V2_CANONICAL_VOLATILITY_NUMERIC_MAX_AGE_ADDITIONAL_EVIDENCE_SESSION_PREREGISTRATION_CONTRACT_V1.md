# MASTER_V2 Canonical Volatility Numeric Max-Age Additional Evidence Session Preregistration Contract v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_PREREGISTRATION_CONTRACT_V1
STATUS: CAPABILITY_AVAILABLE
scope: versioned contract for future additional productive evidence session preregistrations; no session instantiation; no authorization; no network; no execution
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

> **Contract capability only.**
> Defines versioned floors, uniqueness guards, authorization-binding schema, and
> fail-closed candidate validation for additional productive Numeric-Max-Age
> evidence sessions after exhausted s01/s02. Does **not** create a session
> preregistration, issue or consume authorization, open network, execute a
> session, select a threshold, enable enforcement, or mutate Master-V2 /
> Double-Play / Entry-Exit / Risk / Safety semantics.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_PREREGISTRATION_CONTRACT_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_PREREGISTRATION_CONTRACT_V1
HARDENING_CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_CONTRACT_HARDENING_V1
SCHEMA=canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract/v1
CANDIDATE_SCHEMA_VERSION=canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate/v1
BOUND_REPOSITORY_SHA=bb5b1f4572deb451d238f890482254c690c164d2
MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS=2
MINIMUM_SESSION_DURATION_SECONDS=10860
MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS=7260
MINIMUM_MAXIMUM_CYCLES_PER_SESSION=182
MINIMUM_MAXIMUM_REQUESTS_PER_SESSION=182
TARGET_AGE_BUCKETS_SECONDS=[60,120,300,600,900,1800,3600,7200]
EXPECTED_VENUE=OKX
EXPECTED_INSTRUMENT=ETH-USD_UM_XPERP-310404
EXPECTED_NETWORK_SCOPE=OKX_EEA_FUTURES_PUBLIC_MARKET_DATA_READ_ONLY
EXPECTED_SESSION_SCOPE=ADDITIONAL_NATURAL_AGE_EVIDENCE_SESSION_V1
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
S01_S02_REUSE_FORBIDDEN=true
SESSION_PREREGISTRATION_CREATION_AUTHORIZED=false
AUTHORIZATION_ISSUANCE_AUTHORIZED=false
PREREGISTRATION_CREATED=false
AUTHORIZATION_ISSUED=false
SESSION_EXECUTED=false
NUMERIC_MAX_AGE_SELECTED=false
NUMERIC_MAX_AGE_ENFORCING=false
HARD_STOP=true
```

Candidate validation notes:

- Required field presence alone is not sufficient; every security-relevant
  binding value must match exactly.
- A correctly recomputed digest must not make a semantically invalid candidate
  valid.
- Unknown fields are not accepted as forward compatibility; new schema fields
  require a new explicit candidate schema version.
- See also
  `MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_CONTRACT_HARDENING_V1.md`.

## Why this contract exists

PR #5626 bound `NaturalAgeProgressionLifecycleHostV1` into the productive
bridge. Session-02 evidence remains age-invariant and non-decisive. The
existing campaign authorization binds exactly two exhausted session IDs with
`maximum_cycles_per_session=128`, which cannot reach natural Age-7200 under
PT1M warmup + reuse floors. This contract defines the minimum lawful shape for
**future** additional-session preregistrations.

## Bound floors

| Floor | Value |
|---|---:|
| `minimum_session_duration_seconds` | 10860 |
| `minimum_post_first_produce_event_span_seconds` | 7260 |
| `minimum_maximum_cycles_per_session` | 182 |
| `recommended_maximum_cycles_per_session` | 200 |
| `minimum_maximum_requests_per_session` | 182 |
| `recommended_maximum_requests_per_session` | 200 |
| `minimum_interval_seconds` | 2.0 |
| `maximum_requests_per_cycle` | 3 |
| `minimum_additional_productive_sessions` | 2 |

## Target age buckets

Exact bind: `[60, 120, 300, 600, 900, 1800, 3600, 7200]`.

Required observations per future session candidate:

- first produce
- natural age progression across distinct PT1M samples
- Age-7200 observation
- recompute after research age floor
- post-recompute fresh observation

## Uniqueness / non-reuse

- Existing campaign `cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe` is exhausted.
- Exhausted session IDs s01/s02 must never be reused.
- Each additional session requires its own session id, preregistration digest,
  session-specific authorization, single-use consumption, and terminal evidence.
- Session IDs must be generated inside the contract candidate builders / later
  preregistration owner — not invented outside the contract.

## Forbidden artificial controls

All must be `false` / forbidden:

- `ARTIFICIAL_DELAY_INJECTION`
- `SYNTHETIC_EVENT_TIME_ADVANCE`
- `AGE_OVERRIDE`
- `AS_OF_OVERRIDE`
- `RECOMPUTE_FORCE_FLAG`
- `LIFECYCLE_STATE_EDIT`
- `EVIDENCE_BACKFILL`

## Authorization binding schema

Future authorization artifacts must bind exactly one `session_id`, require
`single_use=true`, forbid optional/reusable authorization, and forbid reuse of
s01/s02 authorizations. This capability only defines the schema.

## Operator workflow (exact later sequence)

```
CONTRACT_CAPABILITY_MERGE
  → CREATE_ADDITIONAL_SESSION_PREREGISTRATION
  → ISSUE_SESSION_SPECIFIC_AUTHORIZATION
  → EXECUTE_EXACTLY_ONE_SESSION
  → VERIFY_TERMINAL_EVIDENCE
  → REPEAT_FOR_SECOND_SESSION
  → DERIVE_NUMERIC_MAX_AGE_EVIDENCE
  → POLICY_DECISION_SEPARATE
```

## Owners

| Surface | Owner |
|---|---|
| Contract package | `src&#47;research&#47;canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1&#47;` |
| Frozen contract artifact | `config&#47;research&#47;canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.json` |
| Focused tests | `tests&#47;research&#47;test_canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.py` |

## Explicit non-goals

- no additional session preregistration creation in this PR
- no authorization issuance / consumption
- no productive session execution / network
- no numeric max-age selection or enforcement
- no Master-V2 / Double-Play / Entry-Exit / Risk / Safety mutation
- no second age or decision authority
- no mutation of existing s01/s02 evidence or preregistration artifacts

## Terminal readiness

```
READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION=false
READY_FOR_AUTHORIZATION_ISSUANCE=false
READY_FOR_PRODUCTIVE_SESSION_EXECUTION=false
READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION=false
HARD_STOP=true
```

After this contract capability merges, a **separate** operator-authorized step
may create additional session preregistrations that satisfy this contract.

## Migration note (repository SHA semantics)

v1 `repository_sha` tip-of-main equality is **not** lawful for new
authorization readiness. Successor contract:

`canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract/v2`

See
`MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_REPOSITORY_SHA_SEMANTICS_RESOLUTION_V1.md`.

v1 remains parseable for historical evidence. New authorization readiness for
v1 candidates is fail-closed unsupported. PR #5629 tip-rebase approach is
superseded.
