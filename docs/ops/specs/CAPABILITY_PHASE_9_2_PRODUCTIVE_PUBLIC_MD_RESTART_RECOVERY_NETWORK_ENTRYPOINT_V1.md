---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1
status: active
scope: Phase 9.2 productive public-MD restart/recovery network entrypoint; no session activation
capability: PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-03
---

# Capability — Phase 9.2 Productive Public-MD Restart/Recovery Network Entrypoint V1

## Problem / Root Cause

PR #5665 closed the offline restart/recovery contract, harness and verifier, but
explicitly did not provide a productive Public-MD/wallclock entrypoint. A later
Owner session GO could not execute the restart ladder through a repository-
canonical path without inventing a parallel runner.

## Goal

Add a thin productive orchestration entrypoint that reuses:

- wallclock / public-MD transport + network boundary;
- productive authorization issuance/consumption path;
- PR #5665 restart session contract, checkpoint, harness and verifier.

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED=false
AUTHORIZATION_ISSUED=false
```

This capability implements readiness. It does **not** authorize or execute a
productive session.

## Distinctions

| Surface | Authority |
| --- | --- |
| Offline contract/harness/verifier | PR #5665 / `PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1` |
| Productive network entrypoint (this) | Orchestration + segment auth envelopes + fake-MD offline proof |
| Implementation readiness | Entrypoint + tests + evidence fixtures |
| Actual session activation | Separate Owner session GO only |
| Actual session evidence | Produced only by a later authorized session |

## Segment plan (unchanged)

```text
PRE_RESTART = INITIAL_RUN_AND_CHECKPOINT
POST_RESTART = CONTROLLED_RESTART_AND_RECOVERY
EXIT_CODE_82 = CONTROLLED_SEGMENT_TRANSITION
```

No third segment. No parallel segmentsemantics.

## Call graph

### Before

```text
Owner session GO
→ HARD_STOP (no productive public-MD restart entrypoint)
```

### After

```text
Preflight / Dirt bind
→ SegmentAuthorizationEnvelope(PRE) validate
→ single-use consume (once)
→ public-MD wallclock transport boundary (GET/EEA only)
→ PR#5665 checkpoint materialization
→ PRE harness (exit 82 classified)
→ SegmentAuthorizationEnvelope(POST) bound to PRE checkpoint
→ single-use consume (once)
→ POST harness recovery + reconciliation-before-alpha
→ PR#5665 bundle verifier
```

## Entrypoint

`scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py`

Commands:

- `preflight`
- `offline-integration`
- `materialize-evidence`
- `productive-session` (gate evaluation only; no runner side effects)
- `execute-post-unlock` (explicit `--execute` required; invokes preexisting
  canonical restart orchestration runner after Session-GO unlock)

## Authorization / confirm-token

- Productive envelopes reject fixtures.
- Single-use, SHA, config, session, segment and checkpoint bindings enforced.
- Confirm tokens only via file / env / stdin (never argv plaintext).
- No token plaintext in evidence.

## Activation state

```text
ENTRYPOINT_IMPLEMENTED=true
POST_UNLOCK_RUNTIME_INVOCATION_ADDED=true
PRODUCTIVE_EXECUTE_MODE_EXPLICIT=true
SESSION_ACTIVATED=false
NETWORK_SESSION_STARTED=false
```

Documentation and merge do not authorize a productive real-network session.
Unlock still requires:

```text
PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1
```

bound ACTIVE Session-GO artifact + Owner-GO + Owner-Session-GO + single-use
authorization + confirm token, then explicit `execute-post-unlock --execute`.
The permanent config flag `productive_network_session_execution_authorized`
remains `false`.

Post-unlock handoff owner:

```text
PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1
```

## Rollback

Remove the new package/config/CLI/tests/evidence and revert the additive
`authorization_preconsumed` optional flag on the PR #5665 harness if needed.
No core-logic rollback required.

## Out of scope

- Real public-MD session execution
- Real authorization issuance/consumption for the target session
- Threshold / Master V2 / Double Play / Risk / Safety changes
- Ruleset or Notion mutation
