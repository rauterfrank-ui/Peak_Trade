---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-6 productive Real-Network execution path implementation; no session activation
capability: PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-6 Productive Real-Network Execution Path Implementation V1

## Problem / Root Cause

After Binding-only executor merge, Owner-GO real-TTY attempts correctly
`HARD_STOP`ed on:

```text
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY
REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_BINDING_CAPABILITY
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED=false
STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT=true
```

Binding package remains correct and must stay fail-closed. The remaining
gap is a **separate** Owner-GO-capable productive Real-Network execution
path (Step-5 pattern), not ephemeral patches against Binding-only
`execute-governed-session`.

## Goal

Close **only** the productive Real-Network execution-path gap:

```text
BINDING_EXECUTOR preserved fail-closed
+ PRODUCTIVE_REAL_NETWORK_EXECUTOR package present
+ ephemeral NETWORK_SESSION_GO gate (Step-5 pattern)
+ reuse Step-6 governed stale-control / failure-injection
+ Public-MD-only + orders/credentials unreachable
+ reuse wallclock / productive runtime owner
+ Hidden-PTY confirm handoff bound for later session only
+ Step-6 verifier + evidence bound
+ STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT=true
```

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
CONFIRM_TOKEN_MINTED=false
CONFIRM_TOKEN_CONSUMED=false
AUTHORIZATION_CONSUMED=false
SESSION_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=OPEN
PHASE_9_2_STEP_7_STATUS=OPEN
STEP7_STARTED=false
```

This capability does **not** authorize or execute a real Public-MD network
session and does not issue or consume authorization or confirm tokens.

## Executor contrast

| Role | Package | Real-Network under Owner-GO+TTY |
| --- | --- | --- |
| `BINDING_EXECUTOR` | `phase_9_2_step_6_governed_productive_real_network_session_executor_v1` | Always forbidden |
| `PRODUCTIVE_REAL_NETWORK_EXECUTOR` | `phase_9_2_step_6_productive_real_network_execution_path_v1` | Structural `network_session_may_start` only under ephemeral GO; start deferred to later session |

Only the productive executor can authorize `network_session_may_start=true`
for a later separate Owner-GO Real-TTY session. Binding-only remains
permanently fail-closed.

## Call graph

### CALL_GRAPH_BEFORE

```text
BINDING_EXECUTOR execute-governed-session
→ REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY
→ STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT=true
```

### CALL_GRAPH_AFTER

```text
BINDING_EXECUTOR preserved fail-closed
PRODUCTIVE_REAL_NETWORK_EXECUTOR path present
→ ephemeral NETWORK_SESSION_GO (default false)
→ reuse stale-control + failure-injection + wallclock owner
→ Hidden-PTY handoff bound (later session only)
→ Step-6 verifier/evidence bound
→ NETWORK_SESSION_STARTED=false in this capability
```

## Entrypoint

`scripts&#47;ops&#47;run_phase_9_2_step_6_productive_real_network_execution_path_v1.py`

Commands: `preflight`, `prove-path`, `prove-contrast`,
`materialize-evidence`, `prove-failure-injection`,
`execute-governed-session` (offline fail-closed for network side effects).

## Later separate governed session

After this path merges, a **separate** Owner-GO Real-TTY session capability
may invoke the productive executor under ephemeral `NETWORK_SESSION_GO`.
Confirm mint&#47;consume and Hidden-PTY handoff occur only in that later
session. Binding-only CLI must not be reinterpreted.

## Out of scope

- Real Step-6 Public-MD session execution in this PR
- Confirm-token mint or consume
- Live &#47; Testnet &#47; Paper exchange orders &#47; credentials &#47; capital
- Master V2 &#47; Double Play &#47; Bull-Bear &#47; Dynamic Scope &#47; Risk &#47; Safety changes
- Dashboard &#47; presentation &#47; Notion &#47; ruleset mutation
- Step-6 ladder closeout
- Step-7 start
- Weakening Binding-only forbid constants
