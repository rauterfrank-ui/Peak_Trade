---
docs_token: DOCS_TOKEN_P12_EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE_V1
status: active
scope: Offline EXECUTION_PREREQUISITE_11 position-side and request-posSide contract; no GET; no POST
capability: P12_EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# P12 EXECUTION_PREREQUISITE_11 Position Side / posSide V1

## Goal

Close `EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE` offline from
already-bound Peak_Trade contracts. Do not GET. Do not POST. Do not
flatten. Do not unlock Live or Canary. Do not copy P08 row `posSide=net`
onto Place Order. Do not rewrite account `posMode=net_mode` into request
`posSide=net`.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
PRIVATE_AUTH_USED=false
RUNTIME_GET_REQUIRED=false
RUNTIME_GET_PERFORMED=false
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
P08_CLOSED=true
P10_CLOSED=true
P11_POS_TO_SZ_CLOSED=true
CASE=CASE_B_OFFLINE_CLOSABLE
EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE=PASS
P11_PROVEN=true
P11_CLOSED=true
FLATTEN_ORDER_SIDE_RULE=SELL_IF_OBSERVED_SIGNED_POS_GT_0_ELSE_BUY
REQUEST_POS_SIDE_POLICY=OMITTED_FROM_VENUE_NATIVE_BODY
REQUEST_POS_SIDE=OMITTED
POSITION_ROW_POS_SIDE_IS_NOT_REQUEST_POS_SIDE=true
POS_MODE_IS_NOT_POSITION_SIDE=true
LONG_SHORT_IS_NOT_BUY_SELL=true
HISTORICAL_EVIDENCE_PROMOTED_TO_CURRENT_AUTHORITY=false
CONFLICT_COUNT=0
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_P12
EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION
P12_DOES_NOT_GRANT_EXECUTION_READINESS=true
EXECUTION_READY=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Semantic objects

This prerequisite is a combination of two already-bound objects, kept
separate from two other objects:

1. `FLATTEN_ORDER_SIDE` — Place Order `side` `BUY`/`SELL` derived from
   observed `signed_pos` (`SELL` if `signed_pos > 0` else `BUY`).
2. `REQUEST_POS_SIDE` — Place Order `posSide`. Current flatten mapper
   omits the field.
3. `POSITION_ROW_POS_SIDE` — positions-response `posSide`. P08 observed
   `net` for `SUI-USD_UM_XPERP-310404`. Not a request field.
4. `ACCOUNT_POS_MODE` — account `posMode`. Required venue token
   `net_mode` is a separate POS_MODE binding. It does not imply request
   `posSide=net`.

Long/short/net are not aliases of buy/sell.

## Proof vs later runtime value

P12 proves the **prerequisite contract**: how flatten order-side is
derived, and that request `posSide` is omitted on the current venue-native
flatten body. A later send-time request still needs
`EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION`
and remaining send-time gates. This persist does not mint a productive
request body and does not authorize flatten execute.

## Out of scope

- Private GET / POST / flatten / position mutation
- Live / Testnet / Canary execute
- Merge
- Exact flatten payload (prerequisite 12)
- Master V2 / Double Play Core mutation
