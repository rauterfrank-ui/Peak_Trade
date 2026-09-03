---
docs_token: DOCS_TOKEN_P08_NONZERO_POSITION_ADJUDICATION_PERSIST_CLOSE_V1
status: active
scope: Offline P08 CASE_A nonzero adjudication persist and close of already-captured GET; no new GET; no POST
capability: P08_NONZERO_POSITION_ADJUDICATION_PERSIST_CLOSE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P08 Nonzero Position Adjudication Persist Close V1

## Goal

Adjudicate the already-captured unfiltered
`GET &#47;api&#47;v5&#47;account&#47;positions` target row against the
existing CASE_A contract. Persist a canonical evidence pack. Close
`EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN` and P08 if
and only if that contract accepts the captured row. Do not GET. Do not
POST. Do not flatten. Do not invent original wire bytes.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
SECOND_GET_PERFORMED=false
ORDER_PERFORMED=false
POSITION_CREATION_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
PREREQUISITE_08_CLOSED=true
TARGET_POSITION_ZERO_PROVEN=false
TARGET_POSITION_NONZERO_PROVEN=true
G_POSMODE_SUBMIT_BODY_PROVEN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EMPTY_DATA_IS_ZERO=false
P08_CLOSED=true
POSITION_OBSERVATION_CLASS=CASE_A_TARGET_NONZERO
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_P08
EARLIEST_UNRESOLVED_DEPENDENCY=EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT
P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS=true
ORIGINAL_WIRE_BODY_BYTES_AVAILABLE=false
```

## Authority

Reuses `classify_target_position_state_v1`,
`classify_position_observation_v1`, `qty_numeric_status_v1`, and
`adjudicate_prerequisite_08_window_v1`. Binds the already executed
unfiltered positions GET from
`PEAK_TRADE_OWNER_GO_P08_UNFILTERED_ACCOUNT_POSITIONS_OBSERVATION_AFTER_QTY1_ORDER_ACCEPTANCE_V1`.
Does not authorize a new GET, POST, flatten, P09 unit work, funding,
whitelist mutation, Live, Testnet, or Canary execute. `posSide=net` in
the captured row is observation, not G-POSMODE submit-body proof.
`query_completeness_proven=false` does not invalidate the observed
nonzero target row.

## Closure condition

Canonical P08 close remains CASE_A on unfiltered
`GET &#47;api&#47;v5&#47;account&#47;positions`: HTTP 200, OKX 0, exactly one
target-instrument row, canonically nonzero `pos`. Empty `data[]` is not
zero. Absent target row is not zero. Zero row does not close P08. Source
of the row is irrelevant if the observation is proven. Peak_Trade create
is not required.

Captured authorized forensic row:

```text
instId=SUI-USD_UM_XPERP-310404
pos=1
posSide=net
mgnMode=cross
lever=3
avgPx=0.7774
ccy=USDC
posId=3891385768441942017
tradeId=1047017
```

If CASE_A qty-numeric is PASS, the next unresolved dependency is
`EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT`. Qty unit remains
UNPROVEN. Flatten remains a separate Owner-GO.

## Out of scope

- New GET &#47; second GET &#47; polling
- POST &#47; order submit &#47; position creation &#47; flatten
- Funding GET &#47; transfer &#47; credential or whitelist mutation
- Reconstructing uncaptured wire fields
- Merge
- Live &#47; Testnet &#47; Canary execute
- Master V2 &#47; Double Play Core mutation

## Productive owners

| Surface | Owner |
| --- | --- |
| Captured payload bind | `src&#47;ops&#47;section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1&#47;captured_payload_v1.py` |
| CASE_A adjudication | `src&#47;ops&#47;section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1&#47;adjudicate_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1&#47;persist_v1.py` |
| Assemble | `src&#47;ops&#47;section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1&#47;assemble_v1.py` |
| Existing CASE_A classifier | `src&#47;ops&#47;section_11_13_5_p08_position_observation_v1&#47;execute_v1.py` |
| Canonical persist | `docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md` |
