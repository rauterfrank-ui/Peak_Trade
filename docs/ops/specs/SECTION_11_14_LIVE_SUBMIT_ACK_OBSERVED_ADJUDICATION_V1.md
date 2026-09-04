---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION_V1
status: active
scope: §11.14 LIVE_SUBMIT_ACK_OBSERVED exact-single live POST adjudication; ACK true; fill ineligible; section 11.14 incomplete
capability: SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# Section 11.14 LIVE_SUBMIT_ACK_OBSERVED Adjudication V1

## Goal

Persist the exact-single productive Live entry submit and the bound
`LIVE_SUBMIT_ACK_OBSERVED` adjudication. Do not retry. Do not second-submit.
Do not promote `LIVE_FILL_OBSERVED`.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=none
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
LIVE_EXECUTION_CODE_EXISTS=true
LIVE_EXECUTION_PATH_REACHABLE=true
LIVE_PRIVATE_READ_ONLY_PROVEN=true
LIVE_ORDER_PLAN_OBSERVED=true
LIVE_SUBMIT_ACK_OBSERVED=true
LIVE_FILL_OBSERVED=false
CASE_ADJUDICATION=CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE
ACK_SOURCE_KIND=GOVERNED_CURRENT_LIVE_POST
HISTORICAL_ORDER_PLAN_ARTIFACT_REUSE_FOR_POST=false
AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX=1
RETRY_DEFAULT=false
SECOND_SUBMIT_DEFAULT=false
POST_PERFORMED=true
SUBMIT_COUNT=1
LIVE_AUTHORIZED=false
SUBMIT_UNLOCKED=false
EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FILL_OBSERVED
NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_FILL_OBSERVED
RUNTIME_AUTHORIZATION_EFFECT=NONE
ATLAS_AUTHORITY=NONE
```

## Bound outcome

`LIVE_SUBMIT_ACK_OBSERVED` is true from one `POST /api/v5/trade/order` of a
fresh plan on `eea.okx.com`, source `GOVERNED_CURRENT_LIVE_POST`, producer
`adjudicate_live_submit_ack_observed_v1`, conjunction HTTP 200 + code 0 +
one data row + sCode 0 + nonempty ordId + returned clOrdId equals sent.

Transport ok is not this field by itself. Read-only recon is not ACK.
`LIVE_FILL_OBSERVED` remains false. This GO is consumed. No second POST.
