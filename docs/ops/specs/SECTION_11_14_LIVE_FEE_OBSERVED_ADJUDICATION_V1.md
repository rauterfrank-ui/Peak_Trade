---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_FEE_OBSERVED_ADJUDICATION_V1
status: active
scope: §11.14 LIVE_FEE_OBSERVED identity-bound private fills GET adjudication; fee true; position ineligible; section 11.14 incomplete
capability: SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# Section 11.14 LIVE_FEE_OBSERVED Adjudication V1

## Goal

Persist the identity-bound productive Live fee observation and the bound
`LIVE_FEE_OBSERVED` adjudication. Do not POST. Do not retry. Do not
second-submit. Do not promote `LIVE_POSITION_RECONCILED`.

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
LIVE_POSITION_RECONCILED=false
CASE_ADJUDICATION=CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE
FEE_SOURCE_KIND=GOVERNED_CURRENT_PRIVATE_GET
BOUND_ORDID=3893505043080286208
BOUND_CLORDID=ptokxeprod1fec928b1fec928b00
BOUND_INSTID=SUI-USD_UM_XPERP-310404
RAW_FEE_IF_OBSERVED=-0.000374
RAW_FEE_CCY_IF_OBSERVED=USDC
FEE_INFERRED_FROM_RATE=false
FEE_INFERRED_FROM_PRICE_TIMES_QTY=false
POST_PERFORMED=false
GET_PERFORMED=true
RETRY_DEFAULT=false
SECOND_SUBMIT_DEFAULT=false
LIVE_AUTHORIZED=false
SUBMIT_UNLOCKED=false
EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_POSITION_RECONCILED
NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_POSITION_RECONCILED
RUNTIME_AUTHORIZATION_EFFECT=NONE
ATLAS_AUTHORITY=NONE
```

## Bound outcome

`LIVE_FEE_OBSERVED` is true from a current governed private
`GET &#47;api&#47;v5&#47;trade&#47;fills` on `eea.okx.com`, source
`GOVERNED_CURRENT_PRIVATE_GET`, producer `adjudicate_live_fee_observed_v1`,
conjunction HTTP 200 + code 0 + at least one data row whose `ordId`,
`clOrdId`, and `instId` equal the bound Peak_Trade Live submit identity and
whose venue-native `fee` is present, nonempty, and Decimal-parseable and
whose `feeCcy` is nonempty. Raw values `fee=-0.000374` and `feeCcy=USDC`.

Fill quantity is not this field. Fill price is not this field. A static
rate is not this field. `fillPx` times `fillSz` is not this field.
Historical fill evidence is not this field. `LIVE_POSITION_RECONCILED`
remains false. This GO is consumed. No POST.
