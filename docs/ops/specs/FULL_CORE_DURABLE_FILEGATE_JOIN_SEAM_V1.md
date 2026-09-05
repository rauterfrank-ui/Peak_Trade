---
docs_token: DOCS_TOKEN_FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1
status: active
scope: Full-Core durable FILEGATE runtime join seam; no GET; no POST; no arming
capability: FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-05
---

# Full Core Durable Filegate Join Seam V1

## Goal

Join the already durable FILEGATE authority into FULL_CORE_LIVE_PATH
execution admission as typed evidence. Do not arm Live. Do not GET.

```text
DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED=true
DURABLE_FILEGATE_AUTHORITY=kill_switch_should_block_trading+KillSwitchState+StatePersistence
DURABLE_FILEGATE_JOIN_SEAM=join_durable_filegate_into_admission_inputs_v1
AUTHORITY_COUNT=1
PARALLEL_PRODUCTIVE_PATH_ADDED=false
PEAK_KILL_SWITCH_IS_DURABLE_EVIDENCE=false
TRUSTED_FILEGATE_DOES_NOT_ADMIT_LIVE=true
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
FULL_CORE_SYSTEM_E2E_PROVEN=false
CURRENT_LIVE_CORE_PATH_PROVEN=false
```

## Inputs

```text
canonical_kill_switch_state_path
KillSwitchState JSON object with state in {ACTIVE, DISABLED, KILLED, RECOVERING}
```

## Outputs

```text
DurableFilegateJoinEvidenceV1
  TRUSTED_PRESENT + blocked=false | true
  MISSING
  UNKNOWN_BLOCKED
  CONTRADICTORY_BLOCKED
ExecutionAdmissionInputsV1.durable_kill_switch_evidence_status
ExecutionAdmissionInputsV1.durable_kill_switch_blocked
```

Missing, malformed, invalid, or contradictory durable state fail-closed.
Trusted present does not set LIVE_ENABLED, LIVE_ARMED, or WIRE_SEND_PERMITTED.
Admission remains `admitted=false`.

`saved_at` is recorded by StatePersistence. It is not a FILEGATE freshness
gate in the existing reader contract.

## Non-claims

```text
Integrated Replay remains unjoined
PEAK_KILL_SWITCH is overlay only
Canary remains non-productive Live authority
FRESH_GET remains unimplemented on Full-Core
LiveExecutionPort remains FORBIDDEN_IN_CAP_11_1
```

## Next remaining Full-Core building block

```text
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE=FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_WITHOUT_LIVE_ARMING_OR_GET
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE=false
NEXT_STEP_REQUIRES_OWNER_GO=true
```
