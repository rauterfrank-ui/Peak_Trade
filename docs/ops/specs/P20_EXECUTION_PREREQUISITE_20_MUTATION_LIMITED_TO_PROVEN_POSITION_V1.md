---
docs_token: DOCS_TOKEN_P20_EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION_V1
status: active
scope: Offline EXECUTION_PREREQUISITE_20 mutation limited to proven position; no GET; no POST
capability: P20_EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# P20 EXECUTION_PREREQUISITE_20 Mutation Limited To Proven Position V1

## Goal

Close the named dependency
`EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION`
as an offline gate contract. The mutation object is the venue-native flatten
Place Order body. It must be limited to one proven nonzero target position.
Do not GET. Do not POST. Do not flatten. Do not unlock Live or Canary. Do not
issue a runtime permit. Do not authorize a network session.

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
P16_CLOSED=true
CASE=CASE_B_OFFLINE_CLOSABLE_CONTRACT
EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION=PASS_OFFLINE_CONTRACT
PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN=false
PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED=false
P20_DOES_NOT_ISSUE_RUNTIME_PERMIT=true
P20_DOES_NOT_SET_LIVE_AUTHORIZED=true
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_P20
EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_25_NO_ADDITIONAL_OWNER_DECISION_REQUIRED
P20_DOES_NOT_GRANT_EXECUTION_READINESS=true
EXECUTION_READY=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
FAIL_CLOSED_IF_PREREQUISITE_20_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE=true
```

## Proven position

A proven position is a unique target row classified by
`classify_target_position_state_v1` as `TARGET_POSITION_NONZERO_PROVEN`.
Empty `data[]` is not zero. An absent target row is not zero. An explicit
zero row is a distinct deny. P08 CASE_A closed that classifier against the
captured `SUI-USD_UM_XPERP-310404` row with `signed_pos=1`. Historical empty
envelopes are not current proof. A later send still needs a fresh observation.

## Allowed mutation

Full flatten only: `sz` equals `abs(observed pos)`, `side` is SELL if
signed_pos is greater than 0 else BUY, `instId` equals the proven target instrument.
Partial flatten, oversize, wrong instrument, wrong side, missing body, missing
proven position, and using global `LIVE_AUTHORIZED` as a substitute all deny.

## Proof vs later runtime value

P20 proves the **prerequisite contract**: a constructed flatten body is denied
unless it is limited to a proven nonzero target position. A later send still
needs a fresh position observation, remaining send-time gates, bounded runtime
permit issuance, network-session authorization, flatten-execute Owner-GO, and
HMAC. This persist does not issue that permit and does not authorize flatten
execute.

## Out of scope

- Private GET / POST / flatten / position mutation
- Live / Testnet / Canary execute
- `LIVE_AUTHORIZED=true` / `LIVE_ENABLED` / `LIVE_ARMED` activation
- Network session authorization
- Runtime permit issuance
- Merge
- Master V2 / Double Play Core mutation
