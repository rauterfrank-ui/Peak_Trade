---
docs_token: DOCS_TOKEN_DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1
status: active
scope: Owner-policy plus offline in-memory isolated current-code Double-Play producer-function replay; no productive execution; no trading authority
capability: DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# DDO Double-Play Producer Function Replay V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1_OWNER_POLICY_DECISION_PERSIST_DOCS_ONLY
OWNER_GO_IMPLEMENTATION_SLICE=DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1_CURRENT_CODE_IN_MEMORY_ISOLATED_INVOCATION
BOUND_ORIGIN_MAIN_SHA=57c2b49edd8ba23ea1466d30015daf9807898d9b
IMPLEMENTATION_BOUND_ORIGIN_MAIN_SHA=a6ad2e67b443a8ab022d7f05d07837bc84e39a00
PREDECESSOR_GIT_FACT=DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURED
DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1=IMPLEMENTED_OFFLINE_IN_MEMORY_ISOLATED_NOT_PRODUCTIVE
RUNTIME_AUTHORIZATION_EFFECT=NONE
OFFLINE_EVALUATION_AUTHORITY=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
PERMISSION_AUTHORITY=NONE
REPLAY_PRODUCTIVE_AUTHORITY=NONE
HINDSIGHT_LEAKAGE_ALLOWED=false
PRODUCER_FUNCTION_REPLAY_IMPLEMENTED=true
FUNCTION_REPLAY_EXECUTED_IN_TESTS=true
PRODUCTIVE_FUNCTION_REPLAY_EXECUTED=false
PRODUCER_FUNCTION_REPLAY_EXECUTED=false
```

Navigation-only. Master Runbook remains SSOT. The Owner-policy persist did
**not** authorize implementation. A later, separate Owner-GO authorized the
offline in-memory isolated current-code Function-Replay implementation in
§10. This contract still does **not** authorize Live, Testnet, orders,
credentials, outcome-horizon, attribution, promotion, A1, A2, host wiring,
productive ledger bind, or productive producer-function replay.

## 1. Owner-bound replay class

```text
REPLAY_CLASS_LETTER=A
REPLAY_CLASS=CURRENT_CODE_REPLAY
REPLAY_CLASS_OWNER_TOKEN=A_CURRENT_CODE_REPLAY
CODE_IDENTITY_RULE=CURRENT_CODE_EXPLICITLY_ACCEPTED_WITH_NO_HISTORICAL_PARITY_CLAIM
HISTORICAL_CODE_PARITY_CLAIM_ALLOWED=false
HISTORICAL_SEMANTIC_PARITY_CLAIM_ALLOWED=false
DECISION_TIME_CODE_IDENTITY_CLAIM_ALLOWED=false
CODE_SHA_INFERENCE_ALLOWED=false
UNKNOWN_NORMALIZATION_ALLOWED=false
CODE_SHA_UNKNOWN_PRESERVED=true
```

Intended later A-pipeline, **not implemented by this persist**:

```text
historical immutable DDO typed producer-input evidence
→ reconstruct typed DoublePlayEntryExitPolicyInputV0
→ reconstruct typed DoublePlayEntryExitPolicyV0
→ current, replay-time imported/running implementation of
  evaluate_double_play_entry_exit_policy_v0
→ resulting EntryExitPolicyDecisionV0
→ canonical serialization
→ semantic digest
→ compare against stored typed output observation
```

`CURRENT_CODE_REPLAY` is **not** historical reproduction. The later A-slice
may use the public producer symbol path that is imported at replay time.
It must not claim that this code identity equals the decision-time
implementation.

```text
HISTORICAL_CODE_REPLAY=B
STATUS=NOT_SELECTED
BLOCKED_BY=HISTORICAL_CODE_IDENTITY_ABSENT
```

`code_sha=UNKNOWN` on stored evidence must remain `UNKNOWN`. Do not infer,
backfill, or normalize it.

C and D remain distinct and already closed. Neither is Function-Replay.

```text
C=DDO_SEMANTIC_REPLAY_PARITY_V1
C_STATUS=CLOSED
C_IS_FUNCTION_REPLAY=false
D=FORENSIC_TYPED_INPUT_RECONSTRUCTION
D_OWNER=reconstruct_typed_double_play_entry_exit_policy_input_v1
D_STATUS=CLOSED
D_IS_FUNCTION_REPLAY=false
```

## 2. Input and policy reconstruction

```text
TYPED_INPUT_RECONSTRUCTION_OWNER=reconstruct_typed_double_play_entry_exit_policy_input_v1
REQUIRED_PRODUCER_INPUT_FIELD_COUNT=25
REMAINING_PRODUCER_INPUT_EVIDENCE_GAPS=NONE
POLICY_TYPE=DoublePlayEntryExitPolicyV0
POLICY_RECONSTRUCTION_SOURCE=producer_call_policy_version
TYPED_POLICY_OBJECT_RECONSTRUCTABLE=true
POLICY_IMPLEMENTATION_IDENTITY_BOUND=false
POLICY_VERSION_SUFFICIENT_FOR_TYPED_OBJECT_RECONSTRUCTION=true
POLICY_VERSION_SUFFICIENT_FOR_HISTORICAL_IMPLEMENTATION_IDENTITY=false
```

`producer_call_policy_version` is sufficient to reconstruct the typed policy
argument as `DoublePlayEntryExitPolicyV0(policy_version=<evidence value>)`.
It is **not** sufficient for historical implementation identity.

Later A-input is restricted to already persisted immutable DDO typed
producer-input evidence of the bound schema version.

```text
REPLAY_INPUT_SOURCE_ALLOWLIST_REQUIRED=true
REPLAY_INPUT_SOURCE_ALLOWLIST=IMMUTABLE_DDO_TYPED_PRODUCER_INPUT_EVIDENCE_BOUND_SCHEMA_VERSION
HINDSIGHT_DATA_ALLOWED=false
LIVE_QUERY_ALLOWED=false
CURRENT_MARKET_OR_ACCOUNT_INJECTION_ALLOWED=false
ENVIRONMENT_INJECTION_ALLOWED=false
```

## 3. Observation isolation

```text
OBSERVATION_ISOLATION=GOVERNED_CAPTURE_DISABLED_NO_WRAPPED_BYPASS
REPLAY_CAPTURE_ENABLED=false
REPLAY_CAPTURE_SESSION_ISOLATION_REQUIRED=true
REPLAY_PRODUCTIVE_LEDGER_BIND_FORBIDDEN=true
WRAPPED_BYPASS_ALLOWED=false
WRAPPED_BYPASS_STATUS=UNGOVERNED_FUNCTOOLS_MECHANISM
IMPLEMENTATION_REQUIRES_EXPLICIT_CAPTURE_DISABLED_ASSERTION=true
```

Later Function-Replay may use the public producer symbol path. DDO capture
must be explicitly disabled / isolation-governed:

- no active enabled capture session
- no new DecisionEvent observation
- no new typed output observation
- no new producer-input evidence
- no mutation of productive capture or ledger records
- no `ledger_path`

`.__wrapped__` must **not** be promoted to a governed replay API. It remains
an ungoverned `functools` mechanism.

The current capture API exposes `DdoCaptureBindingV0.enabled` and skips with
`CAPTURE_DISABLED` when disabled, but it does **not** currently provide an
explicit fail-closed replay-isolation assertion. Therefore this persist does
**not** implement isolation. Later implementation must add an explicit
capture-disabled assertion before any producer invocation; until that
predicate exists, implementation remains blocked.

## 4. Result durability

```text
RESULT_DURABILITY=IN_MEMORY_NO_WRITE
REPLAY_RESULT_DURABILITY=IN_MEMORY_ONLY
REPLAY_RESULT_LEDGER_WRITE=false
REPLAY_RESULT_FILESYSTEM_WRITE=false
REPLAY_RESULT_HOST_PERSIST=false
NEW_STORAGE_OWNER_REQUIRED=false
PRODUCTIVE_LEDGER_BIND_REQUIRED=false
```

A later replay verifier may return an immutable in-memory result. This
workpackage does not invent a new evidence schema. Durable replay evidence,
if later desired, requires a separate Owner contract and a separate slice.

## 5. Output comparison

Reuse before new. Comparator owners remain:

```text
COMPARATOR_SERIALIZER_OWNER=serialize_entry_exit_policy_decision_canonical
COMPARATOR_DIGEST_OWNER=compute_entry_exit_policy_semantic_digest
NEW_COMPARATOR_REQUIRED=false
NEW_CANONICAL_SERIALIZER_REQUIRED=false
SECOND_DIGEST_DIALECT_FORBIDDEN=true
```

Later A-comparison order:

1. canonical payload dict equality
2. semantic digest equality
3. mismatch fields enumerated deterministically

A is not C:

```text
C_OPERATION=stored typed output → reconstruct/serialize/digest
A_OPERATION=historical input evidence → CURRENT producer invocation → new typed output → canonical compare against stored output
```

## 6. Stale semantic-replay scope repair

The historical C persist recorded
`PRODUCER_FUNCTION_REPLAY_REASON=PRODUCER_INPUT_NOT_IN_IMMUTABLE_EVIDENCE`.
That was true at the time of the C persist. It is no longer a valid global
current-state claim.

```text
HISTORICAL_INTERMEDIATE_STATE=true
PRODUCER_INPUT_NOT_IN_IMMUTABLE_EVIDENCE_AT_TIME_OF_DDO_SEMANTIC_REPLAY_PARITY_V1_PERSIST=true
CURRENT_STATE=PRODUCER_INPUT_NOW_AVAILABLE_VIA_DDO_DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURE_V1
PRODUCER_INPUT_NOW_AVAILABLE_VIA_DDO_DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURE_V1=true
SEMANTIC_REPLAY_PRODUCER_FUNCTION_INVOKED=false
DDO_SEMANTIC_REPLAY_PARITY_V1_REMAINS_OUTPUT_SEMANTIC_PARITY=true
```

C remains an output-semantic-parity operation and does not invoke the
producer. This persist does not redefine C as Function-Replay.

## 7. Exception contract

There is no canonical historical exception-parity contract. Do not invent one.

```text
EXCEPTION_CONTRACT=FAIL_CLOSED_EXPLICITLY_SPECIFIED
REPLAY_EXCEPTION_PARITY_WITH_HISTORICAL_EXECUTION_REQUIRED=false
REPLAY_EXCEPTION_FAIL_CLOSED_REQUIRED=true
REPLAY_EXCEPTION_BLIND_RETRY_ALLOWED=false
```

Later A-replay fail-closed mapping:

| Failure | Result | Match treatment |
| --- | --- | --- |
| Input reconstruction failure | `REPLAY_BLOCKED` / fail-closed | never semantic match |
| Policy reconstruction failure | `REPLAY_BLOCKED` / fail-closed | never semantic match |
| Producer invocation exception | `REPLAY_INDETERMINATE` / fail-closed | never semantic match |
| Output serialization/digest failure | `REPLAY_INDETERMINATE` / fail-closed | never semantic match |

Exception class plus a sanitized deterministic reason may be retained on the
in-memory result. No retry in the same replay operation. No mutation. No
fallback onto another replay class. This persist does not add a new runtime
exception class.

## 8. Safety envelope

```text
DDO_TRADING_AUTHORITY=NONE
DDO_EXECUTION_AUTHORITY=NONE
DDO_PERMISSION_AUTHORITY=NONE
REPLAY_NETWORK_ACCESS_ALLOWED=false
REPLAY_FILESYSTEM_WRITE_ALLOWED=false
REPLAY_PRODUCTIVE_LEDGER_BIND_ALLOWED=false
REPLAY_HOST_WIRING_ALLOWED=false
REPLAY_RUNTIME_PROMOTION_ALLOWED=false
REPLAY_A1_ALLOWED=false
REPLAY_A2_ALLOWED=false
REPLAY_LEARNED_ARTIFACT_RUNTIME_CONSUMPTION_ALLOWED=false
SEND_LEASE_CONSUMED=false
INNER_SEND_INVOKED=false
WIRE_SEND_EXECUTED=false
REAL_POST_COUNT=0
POSITION_MUTATION=false
A1_ACTIVATED=false
A2_ACTIVATED=false
PROMOTION_AUTHORITY_ACTIVATED=false
LEARNED_ARTIFACT_RUNTIME_CONSUMPTION=false
```

## 9. Remaining gap (historical at Owner-policy persist)

The Owner-policy persist bound policy only. That historical statement remains
true for that persist. It must not be read as the later implementation status.

```text
HISTORICAL_AT_OWNER_POLICY_PERSIST=true
PRODUCER_FUNCTION_REPLAY_IMPLEMENTED=false
PRODUCER_FUNCTION_REPLAY_EXECUTED=false
NEXT_DDO_STEP=DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1_IMPLEMENTATION_OWNER_GO_REQUIRED_NOT_AUTHORIZED_BY_THIS_PERSIST
IMPLEMENTATION_OWNER_GO_AUTHORIZED_BY_THIS_PERSIST=false
```

## 10. Offline in-memory isolated current-code implementation

Separate Owner-GO
`DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1_CURRENT_CODE_IN_MEMORY_ISOLATED_INVOCATION`
authorized the bounded A implementation. It does not rewrite the Owner-policy
persist. C and D remain distinct and are not Function-Replay.

```text
FUNCTION_REPLAY_IMPLEMENTED=true
FUNCTION_REPLAY_EXECUTED_IN_TESTS=true
PRODUCTIVE_FUNCTION_REPLAY_EXECUTED=false
PRODUCER_FUNCTION_REPLAY_EXECUTED=false
REPLAY_CLASS_LETTER=A
REPLAY_CLASS_SEMANTIC=CURRENT_CODE_REPLAY
REPLAY_CLASS_OWNER_TOKEN=A_CURRENT_CODE_REPLAY
HISTORICAL_CODE_PARITY_CLAIM=false
OBSERVATION_ISOLATION=EXPLICIT_CAPTURE_DISABLED_FAIL_CLOSED
JOIN_RULE=EXACT_TYPED_OUTPUT_OBSERVATION_REF
RESULT_DURABILITY=IN_MEMORY_NO_WRITE
REPLAY_TIMEOUT_POLICY=UNSPECIFIED
REPLAY_OPERATION_ATTEMPT_COUNT=1
REPLAY_EXCEPTION_BLIND_RETRY_ALLOWED=false
CODE_SHA_INFERENCE_ALLOWED=false
NETWORK_SENDS=0
REAL_POSTS=0
PRODUCTIVE_LEDGER_WRITES=0
A1_ACTIVATED=false
A2_ACTIVATED=false
PROMOTION_AUTHORITY_ACTIVATED=false
OWNER_SYMBOL=replay_double_play_producer_function_current_code_v1
ISOLATION_SYMBOL=ddo_replay_capture_disabled_isolation_reason_v0
NEXT_DDO_STEP=OWNER_GO_REQUIRED_SEPARATE_SCOPED_DDO_CONTINUATION_NOT_AUTHORIZED_BY_THIS_PERSIST
```

Isolation PASS requires an explicit bound `DdoCaptureBindingV0` with
`enabled=false` and `ledger_path is None`. Unbound/None is not isolation.
The public decorated producer symbol is invoked at most once per replay
operation. `.__wrapped__` is not a replay API.

Stored `code_sha=UNKNOWN` remains `UNKNOWN`. The in-memory result carries
`replay_class_semantic=CURRENT_CODE_REPLAY` and
`historical_code_parity_claim=false`. It does not invent a historical
`code_sha`.
