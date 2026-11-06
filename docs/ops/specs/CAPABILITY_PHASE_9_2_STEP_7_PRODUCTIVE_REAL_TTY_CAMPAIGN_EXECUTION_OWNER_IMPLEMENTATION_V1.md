---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_7_PRODUCTIVE_REAL_TTY_CAMPAIGN_EXECUTION_OWNER_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-7 productive Real-TTY campaign execution owner; no campaign activation
capability: PHASE_9_2_STEP_7_PRODUCTIVE_REAL_TTY_CAMPAIGN_EXECUTION_OWNER_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-7 Productive Real-TTY Campaign Execution Owner Implementation V1

## Problem / Root Cause

After Step-7 binding&#47;harness&#47;verifier and productive campaign path merge,
Owner-GO campaign execution attempts correctly `HARD_STOP`ed on:

```text
MISSING_PRODUCTIVE_STEP7_REAL_TTY_CAMPAIGN_START_EXECUTION_OWNER
REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY
NETWORK_SESSION_START_DEFERRED_TO_LATER_CAMPAIGN
```

Binding and Path packages remain correct and must stay fail-closed. The
remaining gap is a **separate** Real-TTY campaign start&#47;execution owner with
a productive multi-session invoke edge.

## Goal

Close **only** the productive Step-7 Real-TTY campaign owner gap:

```text
BINDING_CAMPAIGN_EXECUTOR preserved fail-closed
+ PATH_IMPLEMENTATION preserved non-starting
+ REAL_TTY_CAMPAIGN_OWNER present
+ execute_governed_step7_campaign_v1 invoke edge
+ Hidden-PTY confirm handoff bound
+ MULTI_SESSION_REQUIREMENT_EXPRESSION=>1
+ reuse Step-7 harness + verifier + campaign bundle
+ reuse Step-3 restart / Step-4 reconnect / Step-6 stale-adverse
+ copy/paste Real-TTY operator entrypoint for later Owner-GO
```

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
CONFIRM_TOKEN_MINTED=false
CONFIRM_TOKEN_CONSUMED=false
CAMPAIGN_EXECUTED=false
PHASE_9_2_STEP_6_STATUS=CLOSED_PASS
PHASE_9_2_STEP_7_STATUS=OPEN
PHASE_9_2_SESSION_LADDER_COMPLETE=false
STEP7_STARTED=false
```

This capability does **not** authorize or execute a real Public-MD
multi-session campaign and does not issue confirm tokens during
prove&#47;materialize.

## Entrypoints

- Owner CLI (prove&#47;offline):
  `scripts&#47;ops&#47;run_phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.py`
- Later Real-TTY operator entrypoint (separate Owner-GO only):
  `scripts&#47;ops&#47;run_phase_9_2_step_7_real_tty_campaign_operator_entrypoint_v1.py`
  (`AUTHORIZATION_CHANNEL=REAL_TTY_HUMAN_CONFIRM`)
- Later Delegated Cursor secure-confirm operator entrypoint (separate Owner-GO only):
  `scripts&#47;ops&#47;run_phase_9_2_step_7_delegated_cursor_secure_confirm_campaign_operator_entrypoint_v1.py`
  (`AUTHORIZATION_CHANNEL=DELEGATED_CURSOR_SECURE_CONFIRM`)
- Productive library symbol:
  `execute_governed_step7_campaign_v1`

## Confirm &#47; Authorization Channels

```text
AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM
AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
TOKEN_ROLE=EPHEMERAL_EXECUTION_LATCH
```

The confirm token is an **ephemeral execution latch**, not a proof of human
Real-TTY presence. Real-TTY channel remains fully supported. Delegated Cursor
channel is an additional governed path requiring Owner-GO, exact capability
binding, `HEAD == origin&#47;main`, tracked worktree clean, `authorization-valid`,
and explicit `--request-real-network`. Digest-only evidence; no argv&#47;env&#47;
stdout&#47;stderr plaintext; one-time use with replay fail-closed.

## Threat Model (Delegated Cursor Channel)

| Threat | Control |
| --- | --- |
| Token in argv &#47; shell history | argv&#47;env rejectors; no `--confirm-token` |
| Token in stdout&#47;stderr&#47;logs | broker never prints plaintext; evidence digest-only |
| Token persisted in evidence | SHA-256 digest only; redact mapping |
| Replay | one-time consume; `CONFIRM_TOKEN_REPLAY` fail-closed |
| Dirty&#47;drifted tree | `HEAD == origin&#47;main` + tracked worktree clean |
| Wrong capability | exact `TARGET_CAMPAIGN_CAPABILITY_ID` bind |
| Order&#47;Live&#47;Testnet escalation | unchanged public-MD-only boundary; no credential path |
| Tempfile leak | chmod 0600 outside repo&#47;evidence; cleanup on success&#47;failure |

## Out of scope

- Real Step-7 Public-MD campaign execution in this PR
- Confirm-token mint in prove&#47;materialize
- Live &#47; Testnet &#47; Paper exchange orders &#47; credentials &#47; capital
- Master V2 &#47; Double Play &#47; Bull-Bear &#47; Dynamic Scope &#47; Risk &#47; Safety changes
- Dashboard &#47; presentation &#47; Notion &#47; ruleset mutation
- Step-7 ladder closeout &#47; `PHASE_9_2_SESSION_LADDER_COMPLETE`
- Weakening Binding-only or Path-implementation forbid constants
