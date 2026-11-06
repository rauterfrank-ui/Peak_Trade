---
docs_token: DOCS_TOKEN_G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1
status: active
scope: Canonical persist of delayed posId-zero plus minimum P7/P9 read-only observations; G12 closed only by merged conjunction evaluator; no POST; no merge; section 11.14 unauthorized
capability: G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# G12 Canonical Delayed Zero Persist And Pending Related Observations V1

## Goal

Persist the already observed delayed explicit `posId` zero row as
governed sanitized evidence, then obtain exactly one unfiltered pending
GET and exactly one unfiltered positions GET required by the merged
delayed G12 conjunction contract. Close `G12` only if that evaluator
returns a full conjunction on admissible persisted evidence.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
P5_VENUE_GET_COUNT=0
P7_GET_COUNT=1
P9_GET_COUNT=1
TOTAL_NEW_VENUE_GET_MAX=2
PRIVATE_AUTH_USED=true
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
EMPTY_DATA_IS_ZERO=false
DELAYED_ZERO_DOES_NOT_IMPLY_PENDING_EMPTY=true
POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS=true
FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL=true
SECTION_11_14_AUTHORIZED=false
RETRY_ALLOWED=false
MERGE_AUTHORIZED_BY_THIS_PERSIST=false
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS
EARLIEST_UNRESOLVED_DEPENDENCY=SECTION_11_14_NOT_AUTHORIZED
NEXT_OWNER_GO_REQUIRED=SEPARATE_OWNER_GO_FOR_SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Semantics

P5 persists a delayed `posId`-filtered explicit `pos==0` target row.
That window proposition is not canonical SSOT zero by itself.
P7 is unfiltered `GET &#47;api&#47;v5&#47;trade&#47;orders-pending`.
P9 is unfiltered `GET &#47;api&#47;v5&#47;account&#47;positions`.
`data=[]` on P9 is not target-zero. The same-session CHOICE_B evaluator
is unchanged. This persist does not execute §11.14.
