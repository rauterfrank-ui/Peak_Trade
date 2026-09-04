---
docs_token: DOCS_TOKEN_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_V1
status: active
scope: Fresh private reads, one reduce-only LIMIT flatten POST, read-only reconciliation; no retry; no Live unlock
capability: PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# Productive Flatten POST And Reconciliation V1

## Goal

Perform fresh authenticated private reads, issue a current-SHA runtime permit,
and if every pre-wire gate is PASS, submit exactly one reduce-only LIMIT flatten
POST for the already-bound SUI XPerp position, then read-only reconcile. Do not
ENTER. Do not reverse. Do not fund. Do not retry. Do not set standing
`LIVE_AUTHORIZED=true` or `CANARY_AUTHORIZED=true`. Empty `data=[]` is not zero.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=true
GET_PERFORMED_THIS_PERSIST=true
PRIVATE_AUTH_USED=true
ORDER_SUBMIT_USED=true
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
EMPTY_DATA_IS_ZERO=false
FRESHNESS_POLICY_MAX_AGE_MS=5000
TARGET_POSITION_ZERO_PROVEN=false
LIVE_FLATTEN_PROVABILITY_PROVEN=false
RETRY_USED=false
FUNDING_USED=false
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION
EARLIEST_UNRESOLVED_DEPENDENCY=OWNER_MERGE_GO_THEN_SECTION_11_14_IF_FLATTEN_PROVEN
NEXT_AUTHORITY_BOUNDARY=OWNER_MERGE_GO
NEXT_OWNER_GO_REQUIRED=OWNER_MERGE_GO
THIS_GO_DOES_NOT_SET_LIVE_AUTHORIZED=true
MERGE_AUTHORIZED_BY_THIS_PERSIST=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Canonical semantics

- Immediate post-action `pos=1` plus live pending reduce-only SELL is
  `POST_ACCEPTED`, not flatten proven.
- Recovery fill bound to this `clOrdId` is `ORDER_FILLED`, not
  `TARGET_POSITION_ZERO_PROVEN`.
- Recovery positions `data=[]` is `CASE_C_EMPTY_DATA_NOT_ZERO`.
- No second submit. No cancel. No merge.
