---
docs_token: DOCS_TOKEN_P11_POS_TO_SZ_UNIT_IDENTITY_INDEPENDENT_PROOF_V1
status: active
scope: Independent POS_TO_SZ unit-identity proof from official OKX semantics; public spec retrieval; no private GET; no POST
capability: P11_POS_TO_SZ_UNIT_IDENTITY_INDEPENDENT_PROOF_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# P11 POS_TO_SZ Unit Identity Independent Proof V1

## Goal

Independently prove the unit identity between OKX `account&#47;positions.pos`
and Place Order `sz` for the bound instrument
`SUI-USD_UM_XPERP-310404` (`instType=FUTURES`, `ctType=linear`,
`ruleType=xperp`). Do not promote ORDER_PLAN aliases, numeric `pos==sz`,
`minSz`, or `ctVal` into the proof. Do not POST. Do not flatten. Do not
unlock Live or Canary.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
PRIVATE_AUTH_USED=false
RUNTIME_GET_REQUIRED=false
RUNTIME_GET_PERFORMED=false
PUBLIC_SPEC_RETRIEVAL_PERFORMED=true
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
P08_CLOSED=true
P10_CLOSED=true
TARGET_POSITION_QTY_NUMERIC=PASS
TARGET_POSITION_QTY_UNIT=PROVEN
CURRENT_UNIT_CONTRACT=NUMBER_OF_CONTRACTS
POS_TO_SZ_UNIT_IDENTITY=PROVEN
POS_UNIT=NUMBER_OF_CONTRACTS
SZ_UNIT=NUMBER_OF_CONTRACTS
IDENTITY_OR_CONVERSION=IDENTITY
CONVERSION_FORMULA=NONE_IDENTITY_SZ_EQUALS_ABS_SIGNED_POS
CASE=CASE_1_SAME_QUANTITY_DOMAIN
CONFLICT_COUNT=0
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_P11
EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE
EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT=PASS
P11_DOES_NOT_GRANT_EXECUTION_READINESS=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Independent venue proof

Official REST Get-positions `pos` for `SWAP`/`FUTURES`/`OPTION` is
"number of contracts". Official fill `sz` / `accFillSz` for
`FUTURES`/`SWAP`/`OPTION` is "the unit of contract". Official `minSz` and
`maxLmtSz` for a derivatives contract are number of contracts.
`tgtCcy` is only applicable to SPOT market orders. Linear notional and
UPL formulas place both `pos` and `sz` in the `N × ctVal × price` slot.
`posCcy` is MARGIN-only. The Place Order request table still says only
"Quantity to buy or sell"; that underspecification is not a competing
unit.

`ctVal` converts contract count to face value / notional. It is not a
`pos→sz` factor. `ONE_CONTRACT_EQUALS_ONE_SUI=false` remains. ORDER_PLAN
`contracts` / `VENUE_CONTRACT_COUNT` / `SUI_OPERATIVE_ORDER_SZ` remain
separate objects.

## Code path

Peak_Trade already identity-copies `abs(signed_pos)` into Place Order
`sz` and omits `tgtCcy`. This slice makes that identity explicit and
fail-closed for the bound FUTURES class. It does not change trading
quantities and does not authorize flatten or submit.

## Out of scope

- Private GET / POST / flatten / position mutation
- Live / Testnet / Canary execute
- Merge
- `posSide` / flatten-payload / bounded-activation prerequisites
- Master V2 / Double Play Core mutation
