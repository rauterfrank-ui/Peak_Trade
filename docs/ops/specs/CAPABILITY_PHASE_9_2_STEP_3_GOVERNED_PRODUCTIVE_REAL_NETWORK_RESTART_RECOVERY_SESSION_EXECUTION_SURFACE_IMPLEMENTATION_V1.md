---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTION_SURFACE_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-3 governed productive restart/recovery session execution surface; no session activation
capability: PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTION_SURFACE_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-3 Governed Productive Restart/Recovery Session Execution Surface Implementation V1

## Problem / Root Cause

Step-3 wallclock binding, Session-GO, offline harness/verifier and network
entrypoint exist, but no productive governed execution surface entrypoint was
available. A later Owner `NETWORK_SESSION_GO` could not execute the restart
ladder through a repository-canonical path without inventing a parallel runner.

## Goal

Implement the missing Step-3 governed execution surface that reuses:

- Step-3 real-network wallclock binding + segment_runner;
- restart/recovery session contract + harness + bundle verifier;
- Session-GO authority;
- segment authorization envelopes;
- canonical confirm-token path;
- Public-MD GET-only boundary and Phase-9.2 pacing conventions.

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
AUTHORIZATION_ISSUED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_CONSUMED=false
READY_FOR_SEPARATE_GOVERNED_REAL_NETWORK_SESSION=true
RESTART_RECOVERY_LADDER_STEP_CLOSED=false
```

This capability does **not** authorize or execute a productive real Public-MD
session.

## Distinctions

| Surface | Authority |
| --- | --- |
| Binding-only CLI | PR wallclock binding; refuses `--request-real-network` |
| This surface implementation | Productive call-graph + offline PRE→POST proof |
| Later runtime capability | `PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTION_V1` |
| Actual real-network session | Separate Owner NETWORK_SESSION_GO only |

## Call graph after

```text
Governed Step-3 execution request
→ SHA / config / contract digest gates
→ Session-GO + OWNER_GO + OPERATOR + NETWORK_SESSION_GO
→ authorization + hidden confirm-token handoff binding
→ Public-MD GET-only provider contract
→ PRE_RESTART (bound segment_runner)
→ controlled exit 82 / process boundary
→ POST_RESTART + reconciliation before alpha
→ session manifest schema
→ offline / bundle verifier bindings
→ REAL_NETWORK remains fail-closed here
```

## Entrypoint

`scripts/ops/run_phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.py`

## Out of scope

- Real Public-MD session execution
- Productive authorization/token issuance or consumption
- Threshold / Master V2 / Double Play / Risk / Safety changes
- Dashboard / Presentation mutation
- Ruleset or Notion mutation
- Permanent unscoped enable flag
