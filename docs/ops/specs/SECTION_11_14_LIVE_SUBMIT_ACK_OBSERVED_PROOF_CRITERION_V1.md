---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1
status: active
scope: §11.14 LIVE_SUBMIT_ACK_OBSERVED proof criterion and producer contract; no POST; ACK remains false; CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO; section 11.14 incomplete
capability: SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# Section 11.14 LIVE_SUBMIT_ACK_OBSERVED Proof Criterion V1

## Goal

Bind the unique §11.14 producer and the minimum sufficient synchronous
proof criterion for `LIVE_SUBMIT_ACK_OBSERVED` against current
`origin&#47;main`. Do not POST. Do not GET. Do not promote the standing
ladder field. Do not weaken single-submit or `UNKNOWN_SUBMIT_NO_BLIND_RETRY`.

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
LIVE_SUBMIT_ACK_OBSERVED=false
LIVE_FILL_OBSERVED=false
CASE_ADJUDICATION=CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO
LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND=true
LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND=true
HTTP_STATUS_REQUIRED=200
TOP_LEVEL_CODE_REQUIRED=0
EXACTLY_ONE_DATA_ROW_REQUIRED=true
SCODE_0_REQUIRED=true
NONEMPTY_ORDID_REQUIRED=true
RETURNED_CLORDID_REQUIRED=true
RETURNED_CLORDID_MUST_EQUAL_SENT=true
READ_ONLY_RECON_IS_NOT_SYNCHRONOUS_ACK=true
COLLECTOR_ACTIVATED=false
POST_PERFORMED=false
GET_PERFORMED=false
CREDENTIAL_USE=false
LIVE_AUTHORIZED=false
SUBMIT_UNLOCKED=false
AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX=1
RETRY_DEFAULT=false
SECOND_SUBMIT_DEFAULT=false
TIMEOUT_MUST_NOT_AUTO_POST=true
EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_SUBMIT_ACK_OBSERVED
NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_EXACT_SINGLE_LIVE_SUBMIT_POST
RUNTIME_AUTHORIZATION_EFFECT=NONE
ATLAS_AUTHORITY=NONE
```

## Canonical producer

Unique §11.14 owner of the ACK *criterion*, not of a live observation:

`src&#47;ops&#47;section_11_14_live_order_and_economic_evidence_ladder_v1&#47;submit_ack_observed_adjudication_v1.py`

symbol `adjudicate_live_submit_ack_observed_v1`

The productive HTTP evidence surface remains
`_entry_submit_returned_payload_v1`. Transport ok is not this field.
Flatten, Cap 11.12.8, and lifecycle ACK handlers are not SSOT. Selected
conjuncts are adopted onto that HTTP surface by this Owner-GO.

## Bound answers to the ACK semantic questions

| Question | Bound answer |
|---|---|
| Does HTTP 200 contribute to ACK? | Yes. Required exactly. Other 2xx is not ACK. |
| Does top-level `code=0` contribute to ACK? | Yes. Required. |
| Is exactly one `data` row required? | Yes. |
| Is `sCode=0` required? | Yes, on that single row. |
| Is nonempty `ordId` required? | Yes. |
| Is returned `clOrdId` required? | Yes. |
| If returned `clOrdId` exists, must it equal sent `clOrdId`? | Yes. Mismatch is UNKNOWN, not ACK and not REJECT. |
| What constitutes explicit REJECT? | Parseable, no redirect, and (`code` nonempty and `!=0`) OR (`code=0` and exactly one data row and `sCode` present and `!=0`). |
| What constitutes UNKNOWN? | Timeout or network after possible send; parse failure; HTTP `!=200` without explicit reject code; redirect; `data_count!=1` on a would-be success; missing `ordId` &#47; `sCode` &#47; `clOrdId`; identity mismatch; contradictory response; `submit_count!=1`. |
| Can later read-only recon resolve existence without reclassifying ACK? | Yes. Pending then history by `clOrdId` may resolve existence. It must not reclassify the original submit response as an observed ACK. |

## Standing field conjunction

`LIVE_SUBMIT_ACK_OBSERVED` is true iff all of:

1. `LIVE_ORDER_PLAN_OBSERVED` already true
2. current productive `POST &#47;api&#47;v5&#47;trade&#47;order` of a fresh plan
3. the synchronous response conjunction above
4. source `GOVERNED_CURRENT_LIVE_POST`
5. not fixture, testnet, or simulated

This GO forbids POST, so the standing field remains false. Injected
offline evidence may satisfy the response conjunction without promoting
the live field.

## Semantics preserved

Transport ok is not `LIVE_SUBMIT_ACK_OBSERVED`.
`CANARY_EXECUTED` is not `LIVE_SUBMIT_ACK_OBSERVED`.
UNKNOWN submit is not ACK.
Read-only recon match by `clOrdId` is not a historically observed
synchronous ACK.
Single-submit and `UNKNOWN_SUBMIT_NO_BLIND_RETRY` remain in force.
Timeout after possible send must not auto-POST.
Historical order-plan artifact reuse for POST remains forbidden.
`LIVE_FILL_OBSERVED` remains ineligible until ACK is true.
Standing Live gates remain false.
No Testnet, fixture or simulated result may satisfy a Live evidence field.
Cap 11.7-11.11 remain contracts-only and are not this field's SSOT.
