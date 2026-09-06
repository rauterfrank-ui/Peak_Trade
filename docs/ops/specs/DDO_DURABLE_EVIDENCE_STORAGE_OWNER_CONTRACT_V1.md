---
docs_token: DOCS_TOKEN_DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1
status: active
scope: DDO durable evidence storage owner contract; path ownership; environment/account/system scoping; observation-only durability failure policy; no productive host binding
capability: DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-06
---

# DDO Durable Evidence Storage Owner Contract V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_OWNER_GO_DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1
BOUND_ORIGIN_MAIN_SHA=c14730e99f1b1303b69a117fdc0d6896ee1c1e51
PREDECESSOR_GIT_FACT=PR_6300_DOUBLE_PLAY_CAPTURE_PARITY
DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1=BOUND
DDO_PRODUCTIVE_HOST_LEDGER_BINDING=false
PRODUCTIVE_HOST_LEDGER_BINDING=false
DDO_RUNTIME_PATH_BOUND=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

This contract creates the **DDO durable evidence storage authority**.
It does **not** bind a productive `ledger_path`. It does **not** create a
runtime file. It does **not** make DDO a trading authority.

## 1. Authority class

```text
DDO_AUTHORITY_OWNER=NONE
DDO_CAPTURE_RUNTIME_EFFECT=OBSERVATION_ONLY
DDO_STORAGE_AUTHORITY_CLASS=DDO_DURABLE_EVIDENCE_STORAGE_OWNER
DDO_DURABLE_EVIDENCE_STORAGE_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER
DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY=false
DDO_STORAGE_OWNER_CAN_CHANGE_DECISION=false
DDO_STORAGE_OWNER_CAN_BLOCK_CURRENT_PRODUCER_RETURN=false
MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true
MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_DECISION_CORE=true
CORE_DECISION_AUTHORITY=MASTER_V2_PLUS_DOUBLE_PLAY
NEW_DDO_STORAGE_IMPLEMENTATION_CREATED=false
```

This owner **does** own:

- persistent DDO DecisionEvents
- persistent producer observation records, including the typed Double-Play
  observation projection v1
- correlation and cycle identities carried on those records
- append-only correction and supersession lineage
- later Outcome and Attribution references that consume this same DDO
  evidence domain contract

This owner **does not** own:

- trading decisions
- Bull/Bear state
- Double-Play policy
- selection
- risk / sizing
- safety
- planning
- execution permission
- execution
- reconciliation truth
- promotion authority
- runtime learned-artifact activation

`DDO_AUTHORITY_OWNER=NONE` remains the trading-authority marker. The storage
owner is a separate evidence-domain class. It is **not** a second
Master V2 / Double-Play decision core.

## 2. Reused library, no second store

```text
DDO_DURABLE_LEDGER_IMPLEMENTATION=AppendOnlyDdoLedgerV0
DDO_DURABLE_LEDGER_IMPLEMENTATION_PATH=src/learning/deterministic_decision_outcome_v0/ledger_v0.py
DDO_LEDGER_DEFAULT_FILENAME=ddo_ledger_v0.jsonl
SECOND_DDO_STORAGE_IMPLEMENTATION_CREATED=false
SQLITE_STORE_CREATED=false
RESEARCH_REGISTRY_REUSED_AS_DDO_OWNER=false
EXPERIMENT_MEMORY_REUSED_AS_DDO_OWNER=false
LIBRARY_ACTIVATED_ON_PRODUCTIVE_HOST=false
DDO_PRODUCTIVE_HOST_LEDGER_BINDING=false
```

`AppendOnlyDdoLedgerV0` is the ratified technical implementation for this
domain. This slice does **not** activate it on the productive host.

## 3. Path owner

```text
PATH_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER
DDO_DURABLE_EVIDENCE_PATH_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER
RUNTIME_STATE_ROOT_SEMANTICS=OUTSIDE_REPOSITORY_CHECKOUT
PATH_SOURCE_CLASS=EXPLICIT_ABSOLUTE_RUNTIME_STATE_ROOT
LOGICAL_CONFIG_KEY=ddo.durable_evidence.runtime_state_root
PATH_SOURCE_IMPLEMENTATION=UNBOUND
FORBIDDEN_GIT_TREE_MUTABLE_RUNTIME_STATE=true
FORBIDDEN_RESEARCH_TREE=true
FORBIDDEN_DOCS_TREE=true
FORBIDDEN_TESTS_TREE=true
FORBIDDEN_PER_WORKTREE_PRODUCTIVE_STATE=true
FORBIDDEN_TREASURY_AUTH_EXECUTION_FOREIGN_STATE_ROOT=true
FORBIDDEN_CWD_AS_PATH_SOURCE=true
FORBIDDEN_HARDCODED_HOME_DIRECTORY=true
FORBIDDEN_RELATIVE_REPO_PATH=true
DDO_RUNTIME_PATH_BOUND=false
```

Logical path template, **not** a live write and **not** a default that a
host may silently apply:

`<RUNTIME_STATE_ROOT>&#47;ddo&#47;<environment>&#47;<account_scope>&#47;<system_scope>&#47;ddo_ledger_v0.jsonl`

The later binding slice must supply an **absolute** runtime-state root from
`LOGICAL_CONFIG_KEY`. Until `PATH_SOURCE_IMPLEMENTATION` is bound, productive
host binding remains blocked.

## 4. Environment / account / system scoping

```text
DDO_EVIDENCE_ENVIRONMENT_SCOPED=true
DDO_EVIDENCE_ACCOUNT_SCOPED=true
DDO_EVIDENCE_STRATEGY_OR_SYSTEM_SCOPE_BOUND=true
ENVIRONMENT_IDENTITY_OWNER=EXISTING_GOVERNANCE_EXECUTION_ENVIRONMENT
ENVIRONMENT_IDENTITY_OWNER_PATH=src/governance/live_mode_gate.py
ENVIRONMENT_IDENTITY_MEMBERS=dev,shadow,testnet,prod
ENVIRONMENT_TOKEN_CURRENT_OBSERVATION_HOST=REQUIRED_BUT_UNBOUND
ACCOUNT_IDENTITY_OWNER=EXISTING_CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY
ACCOUNT_IDENTITY_OWNER_PATH=src/ops/capability_11_2_credential_authorization_and_account_identity_boundary_v1
ACCOUNT_SCOPE_VALUE_CURRENT_OBSERVATION_HOST=REQUIRED_BUT_UNBOUND
SYSTEM_SCOPE_OWNER=ONE_CANONICAL_TRADING_PATH
SYSTEM_SCOPE_TOKEN=canonical_trading_path
SYSTEM_SCOPE_IS_RESEARCH_STRATEGY_ID=false
NEW_ENVIRONMENT_IDENTITY_DOMAIN_CREATED=false
NEW_ACCOUNT_IDENTITY_DOMAIN_CREATED=false
EVIDENCE_MIXING_ACROSS_ENVIRONMENT_OR_ACCOUNT_FORBIDDEN=true
```

Reuse existing identity owners. Do **not** mint a parallel identity domain.
The current observation-only host does not already expose a proven
`ExecutionEnvironment` member or Cap 11.2 account identity for DDO evidence.
Those values stay `REQUIRED_BUT_UNBOUND`. A later binding slice stays blocked
until they are bound to those existing owners.

`SYSTEM_SCOPE_TOKEN=canonical_trading_path` reuses the already canonical
`ONE_CANONICAL_TRADING_PATH` / Master V2 + Double-Play system. It is **not**
a research `strategy_id` and **not** a Strategy Registry row.

## 5. Durability failure policy

```text
DDO_PERSIST_FAILURE_CHANGES_CURRENT_DECISION=false
DDO_DURABILITY_FAILURE_POLICY_CURRENT_STAGE=FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE
A1_OR_RISK_INCREASING_RUNTIME_DURABILITY_POLICY=NOT_AUTHORIZED_BY_THIS_SLICE
DDO_DURABILITY_FAILURE_POLICY_FOR_A1=UNBOUND_NOT_AUTHORIZED
SILENT_PERSIST_SUCCESS_FORBIDDEN=true
RETRY_THAT_DUPLICATES_DECISIONS_FORBIDDEN=true
LIVE_OR_EXECUTION_AUTHORITY_NOT_DERIVED_FROM_THIS_POLICY=true
```

Current-stage meaning:

- the already-produced canonical trading return stays unchanged
- capture/persist failure must be explicitly observable
- no silent success
- no retry that duplicates DecisionEvents
- this policy does **not** mint Live, execution, or supervisor authority

A later unattended / Live / A1 slice must decide separately whether durable
audit evidence becomes a precondition for further risk-increasing cycles.
The current observation-only fail-open policy **must not** mutate into that
Live policy by reuse of this GO.

## 6. Required pre-binding contract

A later productive host-binding slice is **not** authorized until all of the
following are true:

```text
REQUIRED_PRE_BINDING_EXPLICIT_PATH_SOURCE=true
REQUIRED_PRE_BINDING_PATH_OWNER=true
REQUIRED_PRE_BINDING_ENVIRONMENT_ACCOUNT_SCOPING=true
REQUIRED_PRE_BINDING_CAPTURE_DURABLE_WRITE_RETRY_SEMANTICS=true
REQUIRED_PRE_BINDING_CAPTURED_IDS_AFTER_DURABLE_PERSIST=true
REQUIRED_PRE_BINDING_WRITE_FAILURE_OBSERVABILITY=true
REQUIRED_PRE_BINDING_RESTART_READABILITY=true
REQUIRED_PRE_BINDING_DUPLICATE_IDEMPOTENCY_PRESERVED=true
REQUIRED_PRE_BINDING_CORRUPTION_DETECTION=true
REQUIRED_PRE_BINDING_SINGLE_WRITER_ASSUMPTION_BOUND=true
```

This slice documents those requirements. It does **not** implement them.

Known library/host gap that remains open:

```text
CAPTURED_IDS_DURABLE_WRITE_BUG_STATUS=OPEN
CAPTURED_IDS_MARKED_BEFORE_LEDGER_APPEND=true
DURABLE_LOSS_ON_APPEND_FAILURE_THEN_CYCLE_SKIP=PROVEN_IN_CAPTURE_ADAPTER
REQUIRED_FIX_BEFORE_HOST_BINDING=true
```

## 7. Concurrency

```text
DDO_LEDGER_SINGLE_WRITER_REQUIRED=true
MULTI_PROCESS_SHARED_LEDGER_WRITES_ALLOWED=false
MULTI_PROCESS_SHARED_WRITES_ALLOWED=false
LOCK_IMPLEMENTATION_ADDED_BY_THIS_SLICE=false
FENCING_IMPLEMENTATION_ADDED_BY_THIS_SLICE=false
NEW_SINGLE_WRITER_OWNER_CREATED=false
```

`AppendOnlyDdoLedgerV0` has no lock. This contract binds the authority
assumption only. Existing trading-state single-writer helpers are **not**
reused as DDO owners. A later hardening slice may enforce the assumption
without creating a second fencing authority domain.

## 8. Fsync / atomicity classification

```text
FILE_FSYNC_PRESENT=true
DIRECTORY_FSYNC_HARD_GUARANTEE=false
ATOMIC_RECORD_APPEND=PARTIAL
CRASH_DURABILITY_FULLY_PROVEN=false
DDO_LEDGER_DURABILITY_HARDENING_REQUIRED_BEFORE_STRONG_DURABLE_AUTHORITY_CLAIM=true
DURABILITY_HARDENING_REQUIRED=true
```

The library has file `fsync` after append. Directory `fsync` is best-effort
and swallows `OSError`. Append is `O_APPEND` of one JSONL line, not
tempfile-replace. This contract **must not** claim stronger crash safety
than that implementation.

## 9. Correction / lineage

Reuse existing library semantics. No new correction engine.

```text
DDO_EVIDENCE_APPEND_ONLY=true
DDO_SOURCE_EVIDENCE_OVERWRITE_ALLOWED=false
DDO_CORRECTION_MODE=APPEND_ONLY_SUPERSESSION
DDO_DUPLICATE_IDENTICAL_RECORD=IDEMPOTENT_REPLAY
DDO_DUPLICATE_CONFLICT=FAIL_CLOSED_FOR_LEDGER_WRITE
UNKNOWN_SCHEMA=REJECT
```

## 10. Non-goals

```text
NO_PRODUCTIVE_LEDGER_BINDING=true
NO_LEDGER_PATH_IN_HOST=true
NO_RUNTIME_FILE_CREATION=true
NO_NEW_DB=true
NO_SQLITE=true
NO_SECOND_DDO_LEDGER=true
NO_DOUBLE_PLAY_CHANGE=true
NO_TRADING_SEMANTIC_CHANGE=true
NO_SELECTION_CHANGE=true
NO_29P_CHANGE=true
NO_SAFETY_CHANGE=true
NO_29Q_CHANGE=true
NO_MAPPER_CHANGE=true
NO_EXECUTION_PERMISSION_CHANGE=true
NO_EXECUTION_CHANGE=true
NO_LIVE_FLAG_CHANGE=true
NO_WIRE_SEND=true
NO_CREDENTIAL_CHANGE=true
NO_TREASURY_CHANGE=true
NO_PROMOTION_ACTIVATION=true
NO_LEARNED_ARTIFACT_RUNTIME_CONSUMPTION=true
NO_SUPERVISOR_ACTIVATION=true
WP_FA_08_AUTHORIZED=false
CURRENT_CANONICAL_SECTION_REPLACED=false
```

## 11. Next DDO step

```text
NEXT_DDO_STEP=PEAK_TRADE_DDO_LEDGER_DURABILITY_HARDENING_AND_HOST_BINDING_PREP_V1
NEXT_DDO_STEP_IS_NOT_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1=true
NEXT_OWNER_GO_REQUIRED=true
PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1_AUTHORIZED_BY_THIS_SLICE=false
```

Do **not** jump to `PEAK_TRADE_DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1`.
The hardening/prep slice must still keep productive `ledger_path` unbound
unless a later Owner-GO explicitly authorizes that binding after the
pre-binding contract is satisfied.
