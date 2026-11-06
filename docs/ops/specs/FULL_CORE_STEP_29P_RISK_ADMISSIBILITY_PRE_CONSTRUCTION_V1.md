---
docs_token: DOCS_TOKEN_FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION_V1
status: active
scope: Full-Core STEP-29P capital/risk admissibility contract; fresh OKX-EEA GET evidence; Treasury interference proof; pre-construction boundary; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_STEP_29P_RISK_ADMISSIBILITY_PRE_CONSTRUCTION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-05
---

# Full Core STEP 29P Risk Admissibility Pre-Construction V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.Q.

```text
STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED=true
RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ENABLED=true
RISK_ADMISSIBLE_DOES_NOT_IMPLY_LIVE_ARMED=true
RISK_ADMISSIBLE_DOES_NOT_IMPLY_WIRE_SEND=true
RISK_ADMISSIBLE_DOES_NOT_IMPLY_PORT_CONSTRUCTION=true
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1
CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED=false
CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_AUTHORIZED=false
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=STEP_29P_EQUITY_DIMENSION_BINDING_MISSING
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE=NO_FURTHER_REPO_INTERNAL_SLICE_PRE_CONSTRUCTION_BOUNDARY_REACHED
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE=false
```

Persist classes remain distinct and are never collapsed:

```text
FRESH_EVIDENCE_FETCHED
FRESH_EVIDENCE_VALIDATED
CAPITAL_EVIDENCE_COMPLETE
STEP_29P_RISK_ADMISSIBLE
STANDING_GATES_SATISFIED
PORT_CONSTRUCTION_AUTHORIZED
PORT_CONSTRUCTED
WIRE_SEND_AUTHORIZED
WIRE_SEND_EXECUTED
```

`availEq` / `totalEq` / `eq` / `adjEq` / `availBal` / `cashBal` are forbidden
29P equity-authority fields. Empty positions `data` is `NOT_OBSERVED`, not zero.
Ticker last is max-size query px only, not 29P price authority.

GET execute lives in sibling package
`src/ops/full_core_step_29p_fresh_venue_evidence_v1/` so Full-Core does not
import `LiveCanaryHttpClientV1`. Fresh GET pack
`evidence/ops/full_core_step_29p_fresh_venue_evidence_v1/20260905T212436Z`
has `GETS_SUCCEEDED=8` and `NETWORK_GET_TO_OKX_OCCURRED=true`.
`STEP_29P_RISK_ADMISSIBLE` remains false while
`RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING` is unbound.
