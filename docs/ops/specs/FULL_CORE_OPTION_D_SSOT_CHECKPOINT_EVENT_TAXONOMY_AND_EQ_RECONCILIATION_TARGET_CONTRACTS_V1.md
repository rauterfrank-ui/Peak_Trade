---
docs_token: DOCS_TOKEN_FULL_CORE_OPTION_D_SSOT_CHECKPOINT_EVENT_TAXONOMY_AND_EQ_RECONCILIATION_TARGET_CONTRACTS_V1
status: active
scope: Full-Core OPTION_D SSOT persist; dimension split; typed checkpoint; typed event taxonomy; typed fresh-eq reconciliation-target contracts; no event acquisition; no reconstruction engine; no C17; no mapping; no producer; no runtime binding; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_OPTION_D_SSOT_CHECKPOINT_EVENT_TAXONOMY_AND_EQ_RECONCILIATION_TARGET_CONTRACTS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core OPTION_D SSOT Checkpoint Event Taxonomy And Eq Reconciliation Target Contracts V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AR.

```text
SELECTED_OPTION=OPTION_D
OPTION_D_SSOT_PERSISTED=true
OPTION_A_REJECTED_AS_LONG_TERM_TARGET=true
OPTION_B_FORBIDDEN=true
OPTION_C_FAIL_CLOSED_FALLBACK_ONLY=true
RAW_EQ_SOURCE_AUTHORITY=false
EQ_RECONCILIATION_TARGET_ONLY=true
CHECKPOINT_CAN_MINT_EQUITY=false
UNCLASSIFIED_EVENT_FAIL_CLOSED=true
DIMENSION_SPLIT_PERSISTED=true
ACCOUNT_EQUITY_AUTHORITY_OWNER=ops.governed_productive_account_equity_authority_producer_v1
EXISTING_AUTHORITY_OWNER_UNCHANGED=true
C01_C16_REJECTION_STILL_BINDING=true
C17_CREATED=false
C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN=true
SOURCE_SELECTED=false
MAPPING_PROVEN=false
GOVERNED_PRODUCER_CREATED=false
EVENT_ACQUISITION_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
RESTART_PROVEN=false
BOUND_ACCOUNT_IDENTITY_PROVEN=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING
EARLIEST_OPTION_D_DEPENDENCY=D4_BOUND_ACCOUNT_IDENTITY
AUTHORITY_EFFECT=NONE
```

This persist ratifies OPTION_D as the long-term productive Running
Account Equity architecture and records typed contracts for checkpoint
anchor state, event taxonomy, and fresh-`eq` reconciliation targets.
It does not revive C01-C16, does not mint C17, does not acquire events,
does not implement a reconstruction engine, does not GET venue `eq`,
and does not authorize a producer, runtime binding, or Live.
