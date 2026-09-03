---
docs_token: DOCS_TOKEN_ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_V1
status: active
scope: Offline repo-first-party census and fail-closed adjudication for Route-C net-mode posSide submit-body contract; no GET; no POST; no live wire
capability: ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# Route-C Net-Mode posSide First-Party Contract Evidence V1

## Goal

Exhaustively census already-present repository first-party evidence bearing on
OKX `net_mode` account configuration versus Route-C create submit-body `posSide`
semantics, then adjudicate whether a normative contract can be proven or must
remain fail-closed `UNPROVEN`.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
NETWORK_CALL_PERFORMED=false
GET_EXECUTED_THIS_PERSIST=false
POST_PERFORMED=false
POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN
POSITION_MODE_FAIL_CLOSED=true
EVIDENCE_EXHAUSTION_PROVEN=true
FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND=false
CANARY_SEMANTICS_TRANSFER_USED=false
CURRENT_PRODUCTIVE_WIRE_REACHABLE=false
CREATE_PATH_CURRENTLY_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Master V2 / Double Play remain sole Trading / Decision Authority.
STEP-29P remains sole Risk / Sizing Authority. STEP-29Q remains PLAN_ONLY.
This package does not mint trading, execution, or live authority.

## Out of scope

- Any OKX GET or POST
- Credentials or browser evidence
- Transfer of Canary omit-on-net-mode to Route-C without direct proof
- Treating leverage-info `posSide=net` as submit-body proof
- Treating `posMode=net_mode` as submit-body `posSide` proof
- Funding, capacity, Prerequisite-08, productive wire, live, canary, merge

## Productive owners

| Surface | Owner |
| --- | --- |
| Census records | `src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1/route_c_net_mode_posside_first_party_census_v1.py` |
| Adjudication | `src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1/route_c_net_mode_posside_first_party_adjudicate_v1.py` |
| Standing fail-closed guard | `src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1/position_mode_submit_body_contract_v1.py` |

## Adjudicated result

```text
RESULT_CLASS=FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED
MISSING_EVIDENCE_EDGE=NO_REPOSITORY_FIRST_PARTY_OKX_SUBMIT_BODY_CONTRACT_FOR_NET_MODE_POSSIDE
POSMODE_NET_SEMANTICS=ACCOUNT_CONFIG_POSMODE_RAW_net_mode_PROVEN_SEPARATE_FROM_SUBMIT_BODY_POSSIDE
POSSIDE_ORDER_REQUEST_SEMANTICS=UNPROVEN_FAIL_CLOSED
```
