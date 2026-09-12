---
docs_token: DOCS_TOKEN_FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION_V1
status: active
scope: Full-Core STEP-29P account-equity source mapping Owner-ratification fail-closed persist; no value binding; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_STEP_29P_ACCOUNT_EQUITY_MAPPING_OWNER_RATIFICATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-12
---

# Full Core STEP 29P Account Equity Mapping Owner Ratification V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.R.

```text
MAPPING_PROVEN=false
IMPLEMENTATION_OF_VALUE_BINDING=false
ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED
ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE=UNRESOLVED
RUNNING_EQUITY_SOURCE_OBJECT=NONE
RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION=NONE
SOURCE_SEMANTICS=UNBOUND
LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE=false
STEP_29P_RISK_ADMISSIBLE=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=ACCOUNT_EQUITY_SOURCE_SEMANTIC_MAPPING_OWNER_RATIFICATION_REQUIRED
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE=NO_FURTHER_REPO_INTERNAL_SLICE_EQUITY_SOURCE_MAPPING_OWNER_RATIFICATION_REQUIRED
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE=false
```

STEP-29P remains the compute / risk-sizing owner. Account-equity input
authority is a separate typed owner and remains unresolved. Venue/raw
balance observations remain Evidence.

`availEq` / `totalEq` / `eq` / `adjEq` / `availBal` / `cashBal` remain
forbidden 29P equity-authority fields. Offline / default / injected equity
is not Live-Capital-Authority. Existing GET pack
`evidence/ops/full_core_step_29p_fresh_venue_evidence_v1/20260905T212436Z`
is re-read only and does not carry typed
`RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING`.
