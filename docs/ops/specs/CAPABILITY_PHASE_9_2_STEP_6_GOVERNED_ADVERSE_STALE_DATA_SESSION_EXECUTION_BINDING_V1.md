---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_6_GOVERNED_ADVERSE_STALE_DATA_SESSION_EXECUTION_BINDING_V1
status: active
scope: Phase 9.2 Step-6 governed adverse/stale session execution binding; no session activation
capability: PHASE_9_2_STEP_6_GOVERNED_ADVERSE_STALE_DATA_SESSION_EXECUTION_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-6 Governed Adverse/Stale Session Execution Binding V1

## Problem / Root Cause

After Step-6 continuation binding merge, a governed session execution attempt
correctly `HARD_STOP`ed:

```text
GOVERNED_SESSION_EXECUTION_PACKAGE_ABSENT=true
STALE_FAULT_NOT_WIRED_INTO_WALLCLOCK_RUNTIME=true
BINDING_NETWORK_SESSION_ALLOWED_FALSE=true
HIDDEN_PTY_STDIN_NOT_TTY=true
```

Continuation surfaces existed, but:

1. no tracked execution package/CLI for
   `PHASE_9_2_STEP_6_GOVERNED_ADVERSE_STALE_DATA_SESSION_EXECUTION_V1`;
2. `GovernedInjectedStaleDataControlV1` was not wired into the productive
   Wallclock Public-MD receive classification path;
3. Real-network session gates (Owner-GO, TTY, auth, confirm) were not
   offline-proven on an execution owner.

## Goal

Close **only** the execution-binding gap:

```text
tracked execution package + CLI
+ productive wallclock receive-path stale-control wiring
+ PROVE_BINDING_ONLY vs GOVERNED_REAL_NETWORK_SESSION gates
+ Hidden-PTY/real-TTY confirm handoff contract
+ offline failure-injection matrix
```

```text
CORE_LOGIC_CHANGE=false
EFFECTIVE_TRADING_NUMERIC_VALUES_UNCHANGED=true
NETWORK_SESSION_STARTED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_CONSUMED=false
SESSION_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=OPEN
NEXT_OPEN=6_ADVERSE_STALE_DATA_SESSION
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION=true
NO_PARALLEL_STALENESS_MODEL=true
STEP4_TRANSPORT_FAULT_SEMANTICS_CHANGED=false
```

This capability does **not** authorize or execute a real Public-MD network
session and does not issue or consume authorization or confirm tokens.

## Call graph

### CALL_GRAPH_BEFORE

```text
Continuation binding CLI
→ GovernedInjectedStaleDataControlV1 (offline only)
→ HARD_STOP on governed session attempt
   (execution package absent; receive-path unwired)
```

### CALL_GRAPH_AFTER

```text
PROVE_BINDING_ONLY
→ reuse GovernedInjectedStaleDataControlV1 (default disabled)
→ bind via runtime_overrides[governed_stale_data_control]
→ WallclockSessionRuntimeV1 receive_ts classification hook
→ StalenessTrackerV1 + killstate STALE_DATA
→ Hidden-PTY confirm handoff gate (real TTY for session mode)
→ GOVERNED_REAL_NETWORK_SESSION gate (fail-closed without Owner-GO+TTY)
→ NETWORK_SESSION_STARTED=false in this capability
```

Step-4 transport fault remains separate:

```text
runtime_overrides[governed_fault_schedule]
→ wrap_fetcher_with_governed_fault_control_v1
```

## Modes

| Mode | Network | Auth consume | Confirm consume |
| --- | --- | --- | --- |
| `PROVE_BINDING_ONLY` | false | false | false |
| `GOVERNED_REAL_NETWORK_SESSION` | only under ephemeral GO + real TTY + valid auth/token; **blocked in this binding capability** | blocked here | blocked here |

Session-mode gate requires:

```text
OWNER_GO=true
OPERATOR_AUTHORIZATION_EXPLICIT=true
NETWORK_SESSION_ALLOWED=true   # ephemeral parameter
PUBLIC_MD_ONLY=true
AUTHORIZATION_VALID=true
CONFIRM_TOKEN_VALID=true
REAL_TTY_REQUIRED=true         # sys.stdin.isatty()
```

Non-TTY:

```text
HARD_STOP=true
NETWORK_SESSION_STARTED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_CONSUMED=false
```

No argv/env/file/piped-non-TTY plaintext confirm-token fallback.

## Later separate governed session invocation

After this binding merges, a **separate** Owner-GO on a real terminal:

```text
scripts/ops/run_phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.py \
  execute-governed-session \
  --owner-go \
  --operator-authorization-explicit \
  --network-session-allowed \
  --request-real-network
```

Confirm token via hidden PTY/stdin getpass only. Optional governed stale
fault schedule may be enabled only under that explicit session GO; default
remains disabled. Permanent package constants stay `NETWORK_SESSION_ALLOWED=false`.

## Entrypoint

`scripts/ops/run_phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.py`

Commands: `preflight`, `prove-binding`, `materialize-evidence`,
`prove-failure-injection`, `request-real-network`, `execute-governed-session`
(all offline fail-closed for network side effects in this capability).

Continuation CLI remains binding-only and unchanged in network authority.

## Activation state

```text
EXECUTION_PACKAGE_EXISTS=true
GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND=true
WALLCLOCK_RECEIVE_PATH_BOUND=true
STALE_CONTROL_DEFAULT_DISABLED=true
NETWORK_SESSION_STARTED=false
SESSION_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=OPEN
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION=true
```

Ladder step closes only after a later executed+verified governed session.

## Out of scope

- Real Step-6 Public-MD session execution in this PR
- Authorization / confirm-token issuance or consumption side effects
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety / Exit changes
- Dashboard / presentation / Notion / ruleset mutation
- Step-7 multi-session campaign
- Permanent unscoped enable flag
- Mutation or semantic mix of Step-4 transport-fault behavior
