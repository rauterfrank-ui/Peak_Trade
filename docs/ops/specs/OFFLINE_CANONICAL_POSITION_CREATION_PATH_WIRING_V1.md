---
docs_token: DOCS_TOKEN_OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_V1
status: active
scope: R4 offline canonical position-creation path wiring only; no GET; no POST; no live wire
capability: OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-02
---

# Canonical Offline Position-Creation Path Wiring V1

## Goal

Wire the missing canonical offline seam from Master V2 &#47; Double Play through
STEP-29P, replay safety, STEP-29Q PLAN_ONLY, the intended-action mapper, a
pure lineage assembler, existing Z2DB prewire &#47; request candidate, and
`OfflineRecordingTransportV1`.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
NETWORK_SESSION_STARTED=false
CREDENTIAL_ACCESS=false
ORDER_SUBMIT_REACHABLE=false
PRODUCTIVE_WIRE_REACHABLE=false
LIVE_AUTHORIZED=false
PREREQUISITE_08_CLOSED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Master V2 &#47; Double Play remains the sole trading decision core. The assembler
transforms typed upstream outputs into the existing Z2DB
`CanonicalLineageSnapshotV1`. It does not choose side, quantity, instrument,
risk, or safety.

## Out of scope

- Venue GET &#47; POST
- Credential &#47; SecretRef access
- Canary min-plan or Canary HTTP
- Live &#47; Testnet &#47; Canary activation
- Prerequisite 08 close
- Cap 7.2 host activation
- Productive transport

## Productive owners

| Surface | Owner |
| --- | --- |
| Lineage assembler | `src&#47;ops&#47;offline_execution_permission_and_position_creation_producer_wiring_v1&#47;lineage_assembler_v1.py` |
| Offline composition | `src&#47;ops&#47;offline_execution_permission_and_position_creation_producer_wiring_v1&#47;composition_v1.py` |
| Existing Z2DB boundary | `src&#47;ops&#47;offline_execution_permission_and_position_creation_producer_wiring_v1&#47;pipeline_v1.py` |
| Recording transport | `src&#47;ops&#47;offline_execution_permission_and_position_creation_producer_wiring_v1&#47;recording_transport_v1.py` |

## Safety claims

```text
CANONICAL_OFFLINE_POSITION_CREATION_PATH_IMPLEMENTED=true
OFFLINE_PATH_PROVEN=true
VENUE_PATH_PROVEN=false
LIVE_PATH_AUTHORIZED=false
HOST_GRAPH_ACTIVATION=false
GRANT_IMPLIES_LIVE_SEND=false
STEP_29Q_NOT_DIRECTLY_SUBMITTABLE=true
```
