---
docs_token: DOCS_TOKEN_P10_TARGET_POSITION_QTY_UNIT_FORENSIC_ADJUDICATION_PERSIST_V1
status: active
scope: Offline forensic census and fail-closed adjudication of TARGET_POSITION_QTY unit; no GET; no POST
capability: P10_TARGET_POSITION_QTY_UNIT_FORENSIC_ADJUDICATION_PERSIST_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P10 TARGET_POSITION_QTY Unit Forensic Adjudication Persist V1

## Goal

Adjudicate `EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT` from
repository evidence only. Enumerate the current producer to execution-
boundary lineage. Persist the census. Keep the unit UNPROVEN unless an
unbroken explicit unit chain exists. Do not GET. Do not POST. Do not
flatten. Do not invent a unit.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
SECOND_GET_PERFORMED=false
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
P08_CLOSED=true
TARGET_POSITION_QTY_NUMERIC=PASS
TARGET_POSITION_QTY_UNIT=UNPROVEN
CURRENT_UNIT_CONTRACT=UNPROVEN
QTY_UNIT_CENSUS_COMPLETE=true
QTY_UNIT_LINEAGE_COMPLETE=true
EARLIEST_MISSING_QTY_UNIT_PROOF=POS_TO_SZ_UNIT_IDENTITY
CONFLICT_COUNT=0
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_P10
EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT
P10_DOES_NOT_GRANT_EXECUTION_READINESS=true
P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Reuses `classify_target_position_state_v1`,
`adjudicate_prerequisite_08_window_v1`, `UNIT_CHAIN_VERDICT`, the P08
captured `pos=1` row, and the already-bound order-plan typed contract-
count domain. Does not authorize a new GET, POST, flatten, funding,
whitelist mutation, Live, Testnet, or Canary execute. Does not promote
`ORDER_PLAN_QTY_UNIT=contracts`, `SUI_OPERATIVE_ORDER_SZ`, `minSz`,
`ctVal`, or numeric `pos==sz` into `TARGET_POSITION_QTY_UNIT`.

## Adjudication

Canonical current producer copies venue `pos` / `posSize` as a decimal
string and hardcodes `TARGET_POSITION_QTY_UNIT=UNPROVEN`. Flatten
planning takes `abs(signed_pos)` and identity-copies that number into
Place Order `sz`. That passthrough is implementation, not unit proof.
`UNIT_CHAIN_VERDICT=PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN` remains
the current contract.

Order-plan `VENUE_CONTRACT_COUNT` / `SUI_OPERATIVE_ORDER_SZ` is a
separate already-adjudicated ENTRY object. It is not
`TARGET_POSITION_QTY`. Historical MAX_SIZE normalization and BTC
denomination work are not current TARGET_POSITION_QTY unit proof.
STEP-29P, STEP-29Q, and SimulatedExecutionPort are not producers of
TARGET_POSITION_QTY. Authorized P08 capture has no `posCcy`. Original
wire bytes are unavailable.

No current authoritative source states a single proven physical unit for
TARGET_POSITION_QTY. No two current authorities claim two different
proven units for that field. The missing proof is independent identity
of OKX `account&#47;positions.pos` to Place Order `sz` for
`SUI-USD_UM_XPERP-310404`.

## Out of scope

- New GET / second GET / polling
- POST / order submit / flatten / position creation
- Funding / credential or whitelist mutation
- Declaring TARGET_POSITION_QTY_UNIT=PROVEN
- Merge
- Live / Testnet / Canary execute
- Master V2 / Double Play Core mutation

## Productive owners

| Surface | Owner |
| --- | --- |
| Lineage census | `src&#47;ops&#47;section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1&#47;lineage_v1.py` |
| Fail-closed adjudication | `src&#47;ops&#47;section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1&#47;adjudicate_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1&#47;persist_v1.py` |
| Assemble | `src&#47;ops&#47;section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1&#47;assemble_v1.py` |
| Canonical persist | `docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md` |
