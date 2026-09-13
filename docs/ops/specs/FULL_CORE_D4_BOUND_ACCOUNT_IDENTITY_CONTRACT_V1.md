---
docs_token: DOCS_TOKEN_FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT_V1
status: active
scope: Full-Core D4 bound account-identity contract; reference-only binding of checkpoint, event-taxonomy, and fresh-eq targets; no venue GET; no concrete UID observation; no event acquisition; no reconstruction engine; no C17; no mapping; no producer; no runtime binding; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_D4_BOUND_ACCOUNT_IDENTITY_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D4 Bound Account Identity Contract V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AS.

```text
OWNER_GO=D4_BOUND_ACCOUNT_IDENTITY_WORKPACKAGE_V1
SELECTED_OPTION=OPTION_D
OPTION_D_SSOT_PERSISTED=true
BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT=true
BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT=false
BOUND_ACCOUNT_IDENTITY_PROVEN=true
BOUND_ACCOUNT_CONCRETE_UID_OBSERVED=false
BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN=true
BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN=true
BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN=true
D4_IDENTITY_MEMBERS=bound_account_identity,bound_venue_identity,bound_td_mode,settlement_currency
IDENTITY_PROVENANCE_CLASS=EXPLICIT_TYPED_BINDING
CHECKPOINT_BINDS_IDENTITY_BY_REFERENCE_ONLY=true
EVENT_BINDS_IDENTITY_BY_REFERENCE_ONLY=true
EQ_TARGET_BINDS_IDENTITY_BY_REFERENCE_ONLY=true
UNKNOWN_MISSING_MISMATCH_IDENTITY_FAIL_CLOSED=true
CROSS_ACCOUNT_MIXING_FAIL_CLOSED=true
ACCOUNT_EQUITY_AUTHORITY_OWNER=ops.governed_productive_account_equity_authority_producer_v1
EXISTING_AUTHORITY_OWNER_UNCHANGED=true
RAW_EQ_SOURCE_AUTHORITY=false
EQ_RECONCILIATION_TARGET_ONLY=true
CHECKPOINT_CAN_MINT_EQUITY=false
C01_C16_REJECTION_STILL_BINDING=true
C17_CREATED=false
C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN=true
SOURCE_SELECTED=false
MAPPING_PROVEN=false
GOVERNED_PRODUCER_CREATED=false
EVENT_ACQUISITION_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
RESTART_PROVEN=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1
D4_BOUND_ACCOUNT_IDENTITY=CONTRACT_PRESENT_AND_REFERENCE_BOUND
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING
EARLIEST_OPTION_D_DEPENDENCY=D5_CHECKPOINT_OBSERVATION_ACQUISITION
AUTHORITY_EFFECT=NONE
```

This persist ratifies the typed BoundAccountIdentity contract and binds
checkpoint, event-taxonomy, and fresh-`eq` target contracts to that
identity by reference only. It does not GET venue identity, does not
observe a productive account UID, does not acquire checkpoints or
events, does not implement a reconstruction engine, does not mint C17,
and does not authorize a producer, runtime binding, or Live.
