---
docs_token: DOCS_TOKEN_AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE_V1
status: active
scope: Authenticated private GET /api/v5/account/positions then runtime permit issuance; no POST
capability: AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# Authenticated Private Runtime Read And Runtime Permit Issuance V1

## Goal

Perform the canonical N11 authenticated private GET
`GET &#47;api&#47;v5&#47;account&#47;positions` and, if and only if every required
gate is fresh PASS, issue a runtime `RuntimeIssuedPermitV1` that binds
instrument, origin-main SHA, observation identity, size, account, and
expiry. Do not POST. Do not flatten. Do not set flatten
`network_session_authorized`. Do not unlock Live or Canary.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=true
PRIVATE_AUTH_USED=true
POSITION_GET_REQUIRED_THIS_PERSIST=true
POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO=true
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
NETWORK_SESSION_AUTHORIZED=false
FLATTEN_EXECUTE_AUTHORIZED=false
PRODUCTIVE_FLATTEN_POST_AUTHORIZED=false
EMPTY_DATA_IS_ZERO=false
FRESHNESS_POLICY_MAX_AGE_MS=5000
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE
EARLIEST_UNRESOLVED_DEPENDENCY=PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION
NEXT_AUTHORITY_BOUNDARY=PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION
NEXT_OWNER_GO_REQUIRED=NOT_PERSISTED_IN_CURRENT_REPO_EVIDENCE
THIS_GO_DOES_NOT_AUTHORIZE_POST=true
FAIL_CLOSED_IF_MARKED_FLATTEN_PROVEN_FROM_PERMIT_ALONE=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Canonical semantics

N11 is `GET https:&#47;&#47;eea.okx.com&#47;api&#47;v5&#47;account&#47;positions` unfiltered,
HMAC-signed, one-shot, no retry. Empty `data=[]` is not zero. Absent target
row is not zero. Zero row is not flattenable and denies permit issuance.
Stale observation (`age_ms > 5000`) denies issuance.

N13 runtime permit uses P16 `BoundedActivationPermitV1` fields plus
observation identity, body SHA-256, and size binding. Price remains
`FlattenPricePermitV1` at N08; public GET is not on this path.
`GatedProductiveFlattenTransportV1` cannot satisfy this GET.

Permit issuance is an authority artifact. It is not flatten execute, not
POST, and not Live unlock.
