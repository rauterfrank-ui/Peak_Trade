---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-6 governed productive Real-Network session execution implementation; no session activation
capability: PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-6 Governed Productive Real-Network Session Execution Implementation V1

## Problem / Root Cause

PR #5779 closed the productive Real-Network **path** gap, but path
`execute-governed-session --request-real-network` remains permanently
fail-closed with:

```text
REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY
NETWORK_SESSION_START_DEFERRED_TO_LATER_SESSION
```

Binding-only remains correctly fail-closed. A separate session-owner
package (Step-5 pattern) is required so a later Owner-GO Real-TTY session
can be executed without weakening Binding/Path forbid constants.

## Goal

```text
BINDING preserved fail-closed
+ PATH_IMPLEMENTATION preserved (non-starting)
+ SESSION_EXECUTION package present (this capability)
+ consumes productive path as dependency edge
+ session-owned may-start under ephemeral Owner-GO + NETWORK_SESSION_GO + Real-TTY
+ reuse stale-control / failure-injection / wallclock / Public-MD fetcher
+ Hidden-PTY confirm handoff reachable
+ Step-6 verifier + evidence writer wiring present
+ NETWORK_SESSION_STARTED=false in this capability
+ PHASE_9_2_STEP_6_STATUS=OPEN
```

## Layer contrast

| Layer | Package | Real-Network under Owner-GO+TTY |
| --- | --- | --- |
| `BINDING_EXECUTOR` | `phase_9_2_step_6_governed_productive_real_network_session_executor_v1` | Always forbidden |
| `PATH_IMPLEMENTATION` | `phase_9_2_step_6_productive_real_network_execution_path_v1` | Structural may_start only; side effects forbidden |
| `SESSION_EXECUTION` | `phase_9_2_step_6_governed_productive_real_network_session_execution_v1` | Session-owned may_start; start deferred in this implementation capability |

## Entrypoint

`scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_execution_v1.py`

Commands: `preflight`, `prove-implementation`, `prove-failure-injection`,
`materialize-evidence`, `execute-governed-session` (offline fail-closed).

## Later separate governed session

After merge, a separate Owner-GO Real-TTY session may invoke:

```text
execute-governed-session --owner-go --operator-authorization-explicit \
  --network-session-go --request-real-network
```

Confirm mint/consume and Hidden-PTY handoff occur only in that later
session. Binding-only and Path-implementation CLIs must not be
reinterpreted as the session owner.

## Out of scope

- Real Step-6 Public-MD session execution in this PR
- Confirm-token mint or consume
- Weakening Binding-only or Path-implementation forbid constants
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety
- Dashboard / presentation / Notion / ruleset mutation
- Step-6 ladder closeout
- Step-7 start
