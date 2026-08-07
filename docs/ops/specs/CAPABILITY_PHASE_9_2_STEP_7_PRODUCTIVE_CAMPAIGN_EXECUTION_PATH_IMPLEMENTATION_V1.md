---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-7 productive campaign execution path implementation; no campaign activation
capability: PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-7 Productive Campaign Execution Path Implementation V1

## Problem / Root Cause

After Step-7 campaign binding&#47;harness&#47;verifier merge, Owner-GO campaign
execution attempts correctly `HARD_STOP`ed on:

```text
PRODUCTIVE_STEP7_CAMPAIGN_EXECUTION_PACKAGE_ABSENT
PRODUCTIVE_STEP7_CAMPAIGN_EXECUTION_ENTRYPOINT_ABSENT
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED=false
```

Binding package remains correct and must stay fail-closed. The remaining
gap is a **separate** Owner-GO-capable productive campaign execution path
(Step-6 path pattern), not ephemeral patches against Binding-only CLI.

## Goal

Close **only** the productive Step-7 campaign execution-path gap:

```text
BINDING_CAMPAIGN_EXECUTOR preserved fail-closed
+ PRODUCTIVE_CAMPAIGN_EXECUTOR package present
+ ephemeral NETWORK_SESSION_GO gate (Step-5 pattern)
+ reuse Step-7 campaign harness + verifier + per-session evidence
+ reuse Step-3 restart / Step-4 reconnect / Step-6 stale-adverse
+ Public-MD-only + orders/credentials unreachable
+ reuse wallclock / productive runtime owner
+ Hidden-PTY confirm handoff bound for later campaign only
+ MULTI_SESSION_REQUIREMENT_EXPRESSION=>1
+ STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT=true
```

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
CONFIRM_TOKEN_MINTED=false
CONFIRM_TOKEN_CONSUMED=false
AUTHORIZATION_CONSUMED=false
CAMPAIGN_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=CLOSED_PASS
PHASE_9_2_STEP_7_STATUS=OPEN
PHASE_9_2_SESSION_LADDER_COMPLETE=false
STEP7_STARTED=false
```

This capability does **not** authorize or execute a real Public-MD
multi-session campaign and does not issue or consume authorization or
confirm tokens.

## Executor contrast

| Role | Package | Real-Network under Owner-GO+TTY |
| --- | --- | --- |
| `BINDING_CAMPAIGN_EXECUTOR` | `phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1` | Always forbidden |
| `PRODUCTIVE_CAMPAIGN_EXECUTOR` | `phase_9_2_step_7_productive_campaign_execution_path_v1` | Structural `campaign_may_start` only under ephemeral GO and session count `>1`; start deferred to later campaign |

Only the productive campaign executor can authorize
`campaign_may_start=true` &#47; `network_session_may_start=true` for a later
separate Owner-GO Real-TTY campaign. Binding-only remains permanently
fail-closed.

## Call graph

### CALL_GRAPH_BEFORE

```text
BINDING_CAMPAIGN_EXECUTOR wire-harness / verify-bundle
→ REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY
→ STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT=true
```

### CALL_GRAPH_AFTER

```text
BINDING_CAMPAIGN_EXECUTOR preserved fail-closed
PRODUCTIVE_CAMPAIGN_EXECUTOR path present
→ ephemeral NETWORK_SESSION_GO (default false)
→ reuse Step-7 harness/verifier + wallclock owner
→ Hidden-PTY handoff bound (later campaign only)
→ MULTI_SESSION_REQUIREMENT =>1
→ NETWORK_SESSION_STARTED=false in this capability
```

## Entrypoint

`scripts&#47;ops&#47;run_phase_9_2_step_7_productive_campaign_execution_path_v1.py`

Commands: `preflight`, `prove-path`, `prove-contrast`,
`materialize-evidence`, `prove-failure-injection`,
`execute-governed-campaign` (offline fail-closed for network side effects).

## Later separate governed campaign

After this path merges, a **separate** Owner-GO Real-TTY campaign
capability may invoke the productive campaign executor under ephemeral
`NETWORK_SESSION_GO` with planned session count `>1`. Confirm mint&#47;consume
and Hidden-PTY handoff occur only in that later campaign. Binding-only CLI
must not be reinterpreted.

## Out of scope

- Real Step-7 Public-MD campaign execution in this PR
- Confirm-token mint or consume
- Live &#47; Testnet &#47; Paper exchange orders &#47; credentials &#47; capital
- Master V2 &#47; Double Play &#47; Bull-Bear &#47; Dynamic Scope &#47; Risk &#47; Safety changes
- Dashboard &#47; presentation &#47; Notion &#47; ruleset mutation
- Step-7 ladder closeout &#47; `PHASE_9_2_SESSION_LADDER_COMPLETE`
- Invented numeric minimum session count beyond `>1`
- Weakening Binding-only forbid constants
