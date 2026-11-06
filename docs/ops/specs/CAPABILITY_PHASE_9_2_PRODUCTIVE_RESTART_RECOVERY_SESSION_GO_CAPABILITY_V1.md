---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1
status: active
scope: Phase 9.2 Session-GO authority surface; no session execution
capability: PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-03
---

# Capability — Phase 9.2 Productive Restart/Recovery Session-GO Capability V1

## Problem / Root Cause

PR #5666 merged the productive Public-MD restart/recovery network entrypoint, but
left productive session execution permanently blocked:

```text
PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED=false
productive_network_session_execution_authorized=false
```

Owner-GO and OWNER_SESSION_GO alone cannot unlock that path. A separate bound
Session-GO authority surface was required.

## Goal

Create the smallest complete Session-GO authority that makes the existing
entrypoint unlockable for a later separately authorized execution order.

```text
CORE_LOGIC_CHANGE=false
SESSION_EXECUTION_ALLOWED=false
NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_ISSUANCE_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
NO_PERMANENT_UNSCOPED_ENABLE_FLAG=true
```

This capability does **not** execute a productive session.

## Authority bindings

A Session-GO artifact must bind:

- capability_id
- session_id
- repository SHA
- config digest
- entrypoint id + path
- public-MD-only
- HTTP GET-only
- max session duration
- restart/recovery scope
- expiry window
- activation_status (`INACTIVE` | `ACTIVE` | `EXPIRED` | `REVOKED`)

## Ordering

```text
Session-GO evaluation
→ Owner-GO + Owner-Session-GO
→ single-use authorization present
→ confirm-token present
→ (only then) lock / network / session start may proceed
```

Missing, expired, inactive, revoked, or mismatched Session-GO fails closed before
authorization consumption, confirm-token processing, lock acquisition, network
access, or session start.

## Distinctions

| Surface | Authority |
| --- | --- |
| Owner-GO / Owner-Session-GO | Necessary but insufficient alone |
| Session-GO (this) | Bound unlock authority for the entrypoint |
| Single-use authorization | Separate; still required after Session-GO |
| Confirm token | Separate secure path; still required |
| Productive entrypoint | Consumer of Session-GO gate |
| Actual session execution | Later Owner execution order only |

## Entrypoints

| Role | Path |
| --- | --- |
| Session-GO CLI | `scripts&#47;ops&#47;run_phase_9_2_productive_restart_recovery_session_go_capability_v1.py` |
| Productive consumer | `scripts&#47;ops&#47;run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py` |

## Config

- Capability config: `config&#47;ops&#47;phase_9_2_productive_restart_recovery_session_go_capability_v1.json`
- Entrypoint config retains `productive_network_session_execution_authorized=false`
- Entrypoint config gains Session-GO authority references only

## Out of scope

- Real session execution
- Authorization issuance/consumption
- Confirm-token minting
- Lock acquisition
- Network requests
- Core trading logic / threshold changes
- Notion or ruleset mutation
