---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BINDING_V1
status: active
scope: Phase 9.2 Step-6 productive real-network session executor binding; no session activation
capability: PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-6 Governed Productive Real-Network Session Executor Binding V1

## Problem / Root Cause

After Step-6 execution binding merge, a governed real-TTY session attempt
correctly `HARD_STOP`ed:

```text
REAL_TTY_REQUIRED / HIDDEN_PTY_STDIN_NOT_TTY
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED=false
NO_STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_ON_EXECUTION_SHA
```

Execution binding and stale-control wiring exist, but no productive
real-network session executor package (Step-5 pattern) is present.

## Goal

Close **only** the productive executor binding gap:

```text
tracked productive executor package + CLI
+ ephemeral NETWORK_SESSION_GO gate (Step-5 pattern)
+ reuse bind_stale_control_into_runtime_overrides_v1
+ reuse GovernedInjectedStaleDataControlV1 / RECEIVE_LAG
+ reuse run_productive_wallclock_session_v1 symbol
+ Hidden-PTY/real-TTY confirm handoff contract
+ offline failure-injection matrix + verifier/evidence
```

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_CONSUMED=false
SESSION_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=OPEN
STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND=true
READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION=true
MAX_NETWORK_SESSION_COUNT=1
NETWORK_CALLS_DURING_BINDING_CAPABILITY=0
PREDECESSOR_NETWORK_SESSION_ALLOWED_UNCHANGED=true
```

This capability does **not** authorize or execute a real Public-MD network
session and does not issue or consume authorization or confirm tokens.

## Call graph

### CALL_GRAPH_BEFORE

```text
Step-6 execution binding CLI
→ HARD_STOP on real-network session attempt
   (productive executor absent; permanent NETWORK_SESSION_ALLOWED=false)
```

### CALL_GRAPH_AFTER

```text
PROVE_BINDING_ONLY
→ ephemeral NETWORK_SESSION_GO gate (default false; parameter-only)
→ reuse bind_stale_control_into_runtime_overrides_v1
→ reuse GovernedInjectedStaleDataControlV1 + RECEIVE_LAG schedule
→ reuse run_productive_wallclock_session_v1 symbol (later session only)
→ Hidden-PTY confirm handoff gate (real TTY required for session mode)
→ GOVERNED_REAL_NETWORK_SESSION gate (fail-closed without Owner-GO+TTY)
→ NETWORK_SESSION_STARTED=false in this capability
```

## Modes

| Mode | Network | Auth consume | Confirm consume |
| --- | --- | --- | --- |
| `PROVE_BINDING_ONLY` | false | false | false |
| `GOVERNED_REAL_NETWORK_SESSION` | blocked in this binding; later Owner-GO+TTY only | blocked here | blocked here |

Session-mode gate requires:

```text
OWNER_GO=true
OPERATOR_AUTHORIZATION_EXPLICIT=true
NETWORK_SESSION_GO=true   # ephemeral parameter
PUBLIC_MD_ONLY=true
AUTHORIZATION_VALID=true
CONFIRM_TOKEN_VALID=true
REAL_TTY_REQUIRED=true
GOVERNED_STALE_CONTROL_PRESENT=true
```

## Later separate governed session invocation

After this binding merges, a **separate** Owner-GO on a real terminal:

```text
scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_executor_v1.py \
  execute-governed-session \
  --owner-go \
  --operator-authorization-explicit \
  --network-session-go \
  --request-real-network \
  --enable-receive-lag
```

Confirm token via hidden PTY/stdin getpass only. Permanent package constants
stay `NETWORK_SESSION_ALLOWED=false`. Predecessor
`phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1.NETWORK_SESSION_ALLOWED`
must not be flipped.

## Entrypoint

`scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_executor_v1.py`

Commands: `preflight`, `prove-binding`, `materialize-evidence`,
`prove-failure-injection`, `request-real-network`, `execute-governed-session`
(all offline fail-closed for network side effects in this capability).

## Activation state

```text
PRODUCTIVE_EXECUTOR_BOUND=true
STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND=true
GOVERNED_STALE_CONTROL_BOUND=true
WALLCLOCK_OWNER_REUSED=true
NETWORK_SESSION_STARTED=false
SESSION_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=OPEN
READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION=true
```

Ladder step closes only after a later executed+verified governed session.

## Out of scope

- Real Step-6 Public-MD session execution in this PR
- Authorization / confirm-token issuance or consumption side effects
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety / Exit changes
- Dashboard / presentation / Notion / ruleset mutation
- Step-7 multi-session campaign
- Permanent unscoped enable flag / flip of predecessor NETWORK_SESSION_ALLOWED
