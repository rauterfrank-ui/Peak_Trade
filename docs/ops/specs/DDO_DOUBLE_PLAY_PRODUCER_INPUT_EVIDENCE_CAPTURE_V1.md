---
docs_token: DOCS_TOKEN_DDO_DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURE_V1
status: active
scope: Immutable Double-Play producer-input evidence capture; not producer-function replay; no trading authority
capability: DDO_DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# DDO Double-Play Producer Input Evidence Capture V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_OWNER_GO_DDO_DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURE_V1
BOUND_ORIGIN_MAIN_SHA=52ff607efd17c362a4c0139ceae110e7baa07b1e
PREDECESSOR_GIT_FACT=TYPED_PRODUCER_OUTPUT_PARITY_PROVEN_CURRENT
DDO_DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURE_V1=BOUND
RUNTIME_AUTHORIZATION_EFFECT=NONE
OFFLINE_EVALUATION_AUTHORITY=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
REPLAY_PRODUCTIVE_AUTHORITY=NONE
HINDSIGHT_LEAKAGE_ALLOWED=false
PRODUCER_FUNCTION_REPLAY_IMPLEMENTED=false
```

Navigation-only. Master Runbook remains SSOT. This contract does **not**
authorize Live, Testnet, orders, credentials, producer-function re-execution,
outcome-horizon, attribution, or promotion.

## 1. Closed slice

The current Double-Play producer input
`DoublePlayEntryExitPolicyInputV0` is observed at decision time on the
existing `core.double_play_entry_exit` decorator path and persisted as
versioned DDO evidence
`double_play_entry_exit_policy_input_evidence_v1`.

```text
DOUBLE_PLAY_PRODUCER_INPUT_EVIDENCE_CAPTURED=true
INPUT_EVIDENCE_SCHEMA_VERSION=double_play_entry_exit_policy_input_evidence_v1
CAN_RECONSTRUCT_TYPED_PRODUCER_INPUT_FROM_IMMUTABLE_EVIDENCE=true
PRODUCER_FUNCTION_REPLAY_IMPLEMENTED=false
```

## 2. Digest relation

The existing producer `input_digest` remains unchanged. It hashes
`serialize_entry_exit_policy_input_canonical`, which is a reduced scope:

- PolicySignal reason codes are omitted (triggered only)
- `composition_result` is reduced to `composition_id` plus `semantic_digest`
- the caller-supplied `input_digest` field is not inside the digest payload

The DDO evidence hash covers the full typed input evidence record. Therefore:

```text
PRODUCER_INPUT_DIGEST_EQUALS_DDO_EVIDENCE_HASH=false
DIGEST_RELATION=PRODUCER_INPUT_DIGEST_IS_REDUCED_CANONICAL_SCOPE_NOT_EQUAL_TO_DDO_EVIDENCE_HASH
```

The evidence record stores the exact producer digest payload so the existing
digest can be reproduced without redefining producer semantics.

## 3. Authority

```text
MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true
SECOND_TRADING_AUTHORITY_CREATED=false
DDO_MAY_REWRITE_PRODUCER_SEMANTICS=false
A1_WAL_REUSED_AS_DDO_LEDGER=false
NEW_STORAGE_OWNER_CREATED=false
```

## 4. Remaining gap

Producer-function replay is **not** implemented by this slice. The next
named DDO dependency is a separate Owner-GO for
`DDO_DOUBLE_PLAY_PRODUCER_FUNCTION_REPLAY_V1`.
