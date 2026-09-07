---
docs_token: DOCS_TOKEN_SECTION_11_14_CURRENT_SUI_XPERP_POS_1_FLATTEN_AUTHORITY_AND_PRE_EXECUTION_REPAIR_V1
status: active
scope: §11.14 current pos=1 flatten authority contract, current-SHA wrapper, GET-only SELL preflight, capture wiring, static restart path; no POST; no flatten; no Owner Flatten GO issued or consumed
capability: SECTION_11_14_CURRENT_SUI_XPERP_POS_1_FLATTEN_AUTHORITY_AND_PRE_EXECUTION_REPAIR_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Current SUI XPERP pos=1 Flatten Authority And Pre-Execution Repair V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
AUTHORITY=NONE
MAP_OF_TRUTH_AUTHORITY=NONE
ATLAS_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
CANARY_AUTHORIZED=false
OWNER_EXECUTION_AUTHORIZED=false
OWNER_FLATTEN_GO_PRESENT=false
FLATTEN_AUTHORIZED=false
GET_PERFORMED=true
POST_PERFORMED=false
LIVE_SUBMIT_EXECUTED=false
WIRE_SEND_EXECUTED=false
POSITION_MUTATION_EXECUTED=false
FLATTEN_EXECUTED=false
RESTART_EXECUTED=false
CRASH_TEST_EXECUTED=false
SUBMIT_ATTEMPT_COUNT=0
AUTOMATIC_RESUBMIT=false
RETRY_ALLOWED=false
SECOND_SUBMIT_ALLOWED=false
```

This spec is not SSOT. The Master Runbook persist is SSOT.

## Authority contract

This slice defines a current §11.14 Flatten-GO **schema**. It does **not** issue
an Owner Flatten GO. Mechanism expected-values in source are not authority.

```text
ACTION=FLATTEN_EXISTING_POSITION
SECTION=11.14
ENTRY_OWNER_GO_CANNOT_AUTHORIZE_FLATTEN=true
FLATTEN_OWNER_GO_CANNOT_AUTHORIZE_ENTRY=true
CONSUMED_GO_CANNOT_BE_REUSED=true
SINGLE_USE=true
RETRY_ALLOWED=false
SECOND_SUBMIT_ALLOWED=false
PRE_SUBMIT_FRESH_GET_REQUIRED=true
POST_SUBMIT_POSITION_RECON_REQUIRED=true
CAPTURE_REQUIRED=true
VENUE_REDUCE_ONLY_NO_FLIP=UNPROVEN
```

The consumed Entry Owner Execution GO cannot authorize flatten. Historical
§11.13.5&#47;G12 flatten GO strings cannot authorize this path. No token in this
spec is an issued GO.

## GET-only SELL preflight

Additive surface `section_11_14_current_flatten_get_only_preflight_v1`.
GET-only. Distinct from the Entry BUY envelope.

Flatten envelope for `pos &gt; 0`:

```text
SIDE=SELL
QTY=abs(pos)
QTY_UNIT=CONTRACTS_SZ
REDUCE_ONLY=true
ORDER_TYPE=LIMIT
REQUEST_POS_SIDE=OMITTED_FROM_VENUE_NATIVE_BODY
REFERENCE=bidPx
LIMIT=ROUND_DOWN_TO_tickSz
ENDPOINT=POST &#47;api&#47;v5&#47;trade&#47;order
CLOSE_POSITION_ALLOWLISTED=false
```

`max-size` is evaluated at the exact flatten SELL limit price.
Pending orders are sampled via GET `&#47;api&#47;v5&#47;trade&#47;orders-pending`.
`data=[]` with `code=0` means zero pending rows. That is not position
`EMPTY_DATA_IS_ZERO` semantics.

## Wrapper

Current-SHA wrapper. Historical productive wrapper SHA
`a23cb998d4d9121a7f06816cc54c0c6ce19a5992` is not unfrozen.
Without Owner Flatten GO, session arming, capture readiness, and a current
SELL envelope the wrapper fail-closes. Productive POST is unbound in this
repair.

## Capture and restart

Capture stages are wired statically and not executed here.
ACK uses `FLATTEN_ACK_ARTIFACT_DISTINCT_FROM_HANDOFF_HOOK`.
Static restart path defaults to `NO_SUBMIT`.
`HOST_CRASH_DURABILITY=UNPROVEN`.
`LIVE_RESTART_RECONSTRUCTED=false`.

## Next authority

Flatten remains unauthorized until a separate Owner Flatten GO is issued
after this repair is merged. This repair does not consume or mint that GO.
Merge requires a separate `OWNER_MERGE_GO`.
