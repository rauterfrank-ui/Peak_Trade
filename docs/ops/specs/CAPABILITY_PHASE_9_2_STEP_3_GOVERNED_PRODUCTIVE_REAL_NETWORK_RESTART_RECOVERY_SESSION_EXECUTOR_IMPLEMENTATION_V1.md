---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTOR_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-3 governed productive restart/recovery session executor; no session activation
capability: PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTOR_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-3 Governed Productive Restart/Recovery Session Executor Implementation V1

## Problem

PR #5768 bound the Step-3 governed execution **surface**. The surface remains
fail-closed for real Public-MD (`REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION`).
A separate productive executor with an explicit side-effect boundary was missing,
so a later Owner `NETWORK_SESSION_GO` could not start a governed restart/recovery
session without inventing a parallel runner or weakening the surface.

## Current runtime truth

```text
STEP3_EXECUTION_SURFACE_FOUND=true
STEP3_EXECUTION_SURFACE_UNCHANGED_FAIL_CLOSED=true
PRODUCTIVE_REAL_NETWORK_STEP3_EXECUTOR_EXISTS=false_before_this_capability
NETWORK_SESSION_STARTED=false
RESTART_RECOVERY_LADDER_STEP_CLOSED=false
```

## Target state

```text
STEP3_PRODUCTIVE_EXECUTOR_IMPLEMENTED=true
STEP3_PRODUCTIVE_EXECUTOR_RUNTIME_REACHABLE=true
STEP3_PRODUCTIVE_EXECUTOR_DEFAULT_FAIL_CLOSED=true
SURFACE_CONSUMED_NOT_DUPLICATED=true
PRODUCTIVE_STEP3_SESSION_STARTED=false
REAL_NETWORK_SESSION_STARTED=false
AUTHORIZATION_ISSUED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_MINTED=false
CONFIRM_TOKEN_CONSUMED=false
```

## Surface versus Executor

| Layer | Role |
| --- | --- |
| Surface CLI (PR #5768) | Validation, offline campaign proof, permanent real-network refuse |
| This Executor | Separate productive side-effect boundary; consumes surface; default fail-closed |

## Call graph after

```text
Future Owner Session Command
→ Canonical Authorization Issuance (separate)
→ Hidden PTY Confirm-Token Handoff
→ Step-3 Productive Executor
→ Step-3 Execution Surface Validation
→ Session Lock / Single Writer
→ Governed Public-MD Session Start (ephemeral NETWORK_SESSION_GO only)
→ Pre-Restart State and Digest Capture
→ Controlled Process Restart (exit 82)
→ Recovery Entrypoint
→ Reconciliation Before Alpha
→ Canonical State Reload
→ Duplicate-Effect Protection
→ Post-Recovery Digest Verification
→ Evidence / Manifest Finalization
→ Session Verifier
```

## Entrypoint

`scripts/ops/run_phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.py`

## Out of scope

- Real Public-MD session execution in this capability
- Productive authorization/token issuance or consumption under permanent constants
- Weakening Surface `REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION`
- Threshold / Master V2 / Double Play / Risk / Safety changes
- Dashboard / Presentation / Ruleset / Notion mutation
