---
docs_token: DOCS_TOKEN_FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_V1
status: active
scope: Full-Core D6 PATH_B PACKAGE_1 D4 durable runtime binding and D5 checkpoint-window binding contracts; typed persist of caller-provided identity and window payloads only; no concrete UID mint; no timestamp invention; GET unauthorized; observation not executed; no reconstruction engine; no C17; no mapping; no producer; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D6 PATH_B PACKAGE_1 D4 Runtime Binding And D5 Window Contract V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.BA.

```text
OWNER_GO=OWNER_GO_D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_IMPLEMENTATION_V1
OWNER_GO_STATUS=CONSUMED
WORKPACKAGE=D6_PATH_B_PACKAGE_1_D4_RUNTIME_BINDING_AND_D5_WINDOW_CONTRACT_IMPLEMENTATION_V1
SELECTED_OPTION=OPTION_D
D4_RUNTIME_BINDING_CONTRACT_PRESENT=true
D4_RUNTIME_BINDING_CREATED=true
BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT=true
BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT=false
D4_CONCRETE_UID_CORROBORATED=false
BOUND_ACCOUNT_CONCRETE_UID_OBSERVED=false
IDENTITY_PROVENANCE_CLASS=EXPLICIT_TYPED_BINDING
D4_IDENTITY_MEMBERS=bound_account_identity,bound_venue_identity,bound_td_mode,settlement_currency
BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN=true
BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN=true
BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN=true
D4_OBSERVATION_MUST_NOT_MINT_IDENTITY=true
D5_WINDOW_BINDING_CONTRACT_PRESENT=true
D5_WINDOW_BINDING_CREATED=true
CHECKPOINT_OBSERVATION_ACQUISITION_CREATED=true
CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT=false
CHECKPOINT_OBSERVATION_WINDOW_RUNTIME_INSTANCE_PRESENT=false
D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT=false
WINDOW_BINDING_CLASS=EXPLICIT_TYPED_WINDOW_BINDING
OBSERVED_AT_AS_OF_RELATION_CLASS=UNPROVEN_NO_IMPLIED_EQUALITY
EVENT_COMPLETENESS_FROM_WINDOW=false
OBSERVATION_S0_STRUCTURAL_BLOCKERS_CLEARED=true
OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT=false
PACKAGE_1_PERSISTED=true
PATH_B_PREAUTHORIZATION_READY=true
EXECUTION_READY=false
OBSERVATION_EXECUTED=false
OBSERVATION_EXECUTION_AUTHORIZED=false
OBSERVATION_NETWORK_GET_AUTHORIZED=false
KIND_SET_RESOLVED=false
MS2_AUTHORIZED=false
D6_FULLY_CLOSED=false
D7_AUTHORIZED=false
C01_REHABILITATION_FORBIDDEN=true
ATLAS_AUTHORITY=NONE
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
C17_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
AUTHORITY_EFFECT=NONE
```

This persist implements the missing D4 durable/runtime typed binding and
the D5 explicit checkpoint/observation window-binding contract inside the
existing BoundAccountIdentity and D5 acquisition owner. It does not
invent or hardcode productive UID values or timestamps. Canonical
`RUNTIME_INSTANCE_PRESENT` pins remain false until a caller-provided
payload is actually persisted. Runtime binding cannot set
`CONCRETE_UID_CORROBORATED`. A later `GET &#47;api&#47;v5&#47;account&#47;config`
may only corroborate or mismatch an already-bound instance; it must not
mint D4 identity.

The D5 window must be explicit. `checkpoint_window_start` and
`checkpoint_window_end` are required. `start <= end` is required. Now,
lookback, bills/balance/venue history, and fixture defaults are forbidden.
The relation `window_end == observed_at_as_of` is not implied. Missing
relation authority remains fail-closed as
`UNPROVEN_NO_IMPLIED_EQUALITY`. The window does not prove event
completeness.

Observation S0 remains blocked while no concrete D4/D5 runtime payload
is persisted. Observation execution remains unauthorized. GET and POST
remain unauthorized.
