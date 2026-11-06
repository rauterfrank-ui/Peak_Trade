---
docs_token: DOCS_TOKEN_P13_EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_V1
status: active
scope: Offline EXECUTION_PREREQUISITE_12 exact flatten payload from observed position; no GET; no POST
capability: P13_EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# P13 EXECUTION_PREREQUISITE_12 Exact Flatten Payload V1

## Goal

Close `EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION`
offline from already-bound Peak_Trade producers, P11 side/posSide, P10/P11
`NUMBER_OF_CONTRACTS` identity, mapper, and serializer. Do not GET. Do not
POST. Do not flatten. Do not unlock Live or Canary. Do not mint a send-time
`px`. Do not copy P08 `avgPx` onto Place Order.

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
P11_CLOSED=true
P11_POS_TO_SZ_CLOSED=true
CASE=CASE_B_OFFLINE_CLOSABLE
EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION=PASS
P12_EXACT_FLATTEN_PAYLOAD_PROVEN=true
P12_EXACT_FLATTEN_PAYLOAD_CLOSED=true
FLATTEN_ORDER_SIDE_RULE=SELL_IF_OBSERVED_SIGNED_POS_GT_0_ELSE_BUY
REQUEST_POS_SIDE=OMITTED
CONTRACT_BOUNDARY=VENUE_NATIVE_JSON_BODY_IMMEDIATELY_BEFORE_HMAC_TRANSPORT
PX_SOURCE_CLASS=BOUND_EXTERNAL_INPUT_NOT_FROM_OBSERVED_POSITION
SEND_TIME_PX_MINTED=false
SZ_UNIT=NUMBER_OF_CONTRACTS
CONFLICT_COUNT=0
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_P13
EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED
P13_DOES_NOT_GRANT_EXECUTION_READINESS=true
EXECUTION_READY=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Contract boundary

Exact payload means the venue-native Place Order JSON object immediately
before HMAC/transport. HTTP headers, timestamp, and signature are out of
boundary.

Required keys: `clOrdId`, `instId`, `side`, `ordType`, `sz`, `tdMode`, `px`,
`reduceOnly`. `posSide` is omitted.

## Proof vs later runtime value

P13 proves the **prerequisite contract**: how the exact flatten body is
derived from an observed position plus standing configuration plus a bound
`FlattenPricePermitV1`. A later send-time request still needs a fresh
position observation, a fresh price permit, remaining send-time gates, and
separate flatten-execute authority. This persist does not authorize flatten
execute.

## Out of scope

- Private GET / POST / flatten / position mutation
- Live / Testnet / Canary execute
- Merge
- Productive urllib send (prerequisite 16)
- Master V2 / Double Play Core mutation
