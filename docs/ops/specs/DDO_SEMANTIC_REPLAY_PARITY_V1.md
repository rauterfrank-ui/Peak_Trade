---
docs_token: DOCS_TOKEN_DDO_SEMANTIC_REPLAY_PARITY_V1
status: active
scope: Offline typed Double-Play producer-output semantic replay from immutable DDO observation evidence; not classifier replay; no producer-function re-execution; no trading authority
capability: DDO_SEMANTIC_REPLAY_PARITY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# DDO Semantic Replay Parity V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_OWNER_GO_DDO_SEMANTIC_REPLAY_PARITY_V1
BOUND_ORIGIN_MAIN_SHA=aa89b71ef510e4568f73c9d817685f5c6b3e74be
PREDECESSOR_GIT_FACT=CURRENT_DOUBLE_PLAY_CAPTURE_PARITY_PROVEN_CURRENT
DDO_SEMANTIC_REPLAY_PARITY_V1=BOUND
RUNTIME_AUTHORIZATION_EFFECT=NONE
OFFLINE_EVALUATION_AUTHORITY=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
REPLAY_PRODUCTIVE_AUTHORITY=NONE
HINDSIGHT_LEAKAGE_ALLOWED=false
```

Navigation-only. Master Runbook remains SSOT. This contract does **not**
authorize Live, Testnet, orders, credentials, producer-function re-execution,
outcome-horizon, attribution, or promotion.

## 1. Closed slice

Current typed Double-Play observation evidence stores the producer canonical
output payload. Offline semantic replay reconstructs that typed producer
object, reuses the producer serializer/digest helpers, and compares against the
persisted projection and generic DecisionEvent mapping.

```text
SEMANTIC_REPLAY_STATUS=TYPED_PRODUCER_OUTPUT_PARITY_PROVEN_CURRENT
CLASSIFIER_REPLAY_REMAINS_DISTINCT=true
PRODUCER_FUNCTION_REPLAY_STATUS=NOT_REPLAYABLE
PRODUCER_FUNCTION_REPLAY_REASON=PRODUCER_INPUT_NOT_IN_IMMUTABLE_EVIDENCE
```

## 2. Explicit remaining gap

`DoublePlayEntryExitPolicyInputV0` is not persisted on the current DDO
observation. `input_digest` is a hash, not the input. Capture `args`/`kwargs`
are not stored. Therefore
`evaluate_double_play_entry_exit_policy_v0` is **not** invoked by replay.
That gap is named, not filled by invented inputs.

## 3. Authority

```text
MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true
SECOND_TRADING_AUTHORITY_CREATED=false
DDO_MAY_REWRITE_PRODUCER_SEMANTICS=false
DECISION_RESULT_TRADE_TOKEN_EXPANSION_UNLOCKED=false
A1_WAL_REUSED_AS_DDO_LEDGER=false
NEW_STORAGE_OWNER_CREATED=false
```
