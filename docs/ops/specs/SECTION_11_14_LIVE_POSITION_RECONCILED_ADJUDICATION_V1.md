---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_POSITION_RECONCILED_ADJUDICATION_V1
status: active
scope: §11.14 LIVE_POSITION_RECONCILED identity-bound private positions GET adjudication; position true; accounting ineligible; section 11.14 incomplete
capability: SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# Section 11.14 LIVE_POSITION_RECONCILED Adjudication V1

## Goal

Persist the identity-bound productive Live position reconciliation and the
bound `LIVE_POSITION_RECONCILED` adjudication. Do not POST. Do not retry.
Do not second-submit. Do not flatten. Do not promote
`LIVE_ACCOUNTING_RECONSTRUCTED`. Do not mark §11.14 complete.

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
LIVE_FILL_OBSERVED=true
LIVE_FEE_OBSERVED=true
LIVE_POSITION_RECONCILED=true
LIVE_ACCOUNTING_RECONSTRUCTED=false
CASE_ADJUDICATION=CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE
POSITION_SOURCE_KIND=GOVERNED_CURRENT_PRIVATE_GET
BOUND_ORDID=3893505043080286208
BOUND_CLORDID=ptokxeprod1fec928b1fec928b00
BOUND_INSTID=SUI-USD_UM_XPERP-310404
BOUND_POS_SIDE=net
BOUND_FILL_SZ=1
RAW_POSITION_QTY_IF_OBSERVED=1
RAW_POS_ID_IF_OBSERVED=3891385768441942017
EMPTY_DATA_IS_ZERO=false
POST_PERFORMED=false
GET_PERFORMED=true
RETRY_DEFAULT=false
SECOND_SUBMIT_DEFAULT=false
LIVE_AUTHORIZED=false
SUBMIT_UNLOCKED=false
EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_ACCOUNTING_RECONSTRUCTED
NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_ACCOUNTING_RECONSTRUCTED
RUNTIME_AUTHORIZATION_EFFECT=NONE
ATLAS_AUTHORITY=NONE
```

## Bound outcome

`LIVE_POSITION_RECONCILED` is true from a current governed private
`GET &#47;api&#47;v5&#47;account&#47;positions` on `eea.okx.com`, source
`GOVERNED_CURRENT_PRIVATE_GET`, producer
`adjudicate_live_position_reconciled_v1`, conjunction HTTP 200 + code 0 +
exactly one data row whose `instId` and `posSide` equal the bound Peak_Trade
Live fill identity and whose venue-native `pos` is present, nonempty,
Decimal-parseable, and Decimal-equal to the bound `fillSz`. Raw values
`pos=1`, `posSide=net`, `posId=3891385768441942017`.

Empty data is not this field and is not zero. A `pos=0` row is not this
field. Fill quantity alone is not this field. Fee is not this field.
`LIVE_RECONCILIATION_PROVEN` is not this field. Historical position evidence
is not this field. `LIVE_ACCOUNTING_RECONSTRUCTED` remains false.
`SECTION_11_14_COMPLETE` remains false. This GO is consumed. No POST.
