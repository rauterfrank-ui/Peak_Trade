---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1
status: active
scope: Phase 9.2 post-unlock handoff to preexisting canonical restart runtime runner
capability: PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-03
---

# Capability — Phase 9.2 Post-Unlock Canonical Runtime Invocation V1

## Problem / Root Cause

PR #5667 made Session-GO unlock evaluation reachable
(`productive_session_execution_permitted=true`), but the productive entrypoint
command `productive-session` remained gate-evaluation-only:

```text
PRODUCTIVE_SESSION_COMMAND_IS_GATE_EVALUATION_ONLY
SIDE_EFFECTS_STILL_REQUIRE_CANONICAL_RUNTIME_INVOCATION=true
authorization_consumed=false
session_lock_acquired=false
session_started=false
```

No parallel runner may be invented. The preexisting canonical runner must be
invoked after unlock.

## Canonical runner (preexisting)

```text
src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1
  .orchestrator_v1.run_offline_productive_restart_orchestration_v1
```

This runner already binds:

- segment authorization validate + consume-once
- session lock / single-writer
- public-MD transport boundary (fake in this capability)
- PR #5665 PRE/POST restart harness (exit 82 classified)
- state reload + reconciliation-before-alpha
- bundle verifier

Wallclock runner referenced (not replaced):

```text
...productive_run_entrypoint_v1.run_productive_wallclock_session_v1
```

## Call graph

### Before

```text
Entrypoint productive-session
→ Session-GO gate
→ productive_session_execution_permitted=true
→ HARD_STOP (no canonical runtime invocation)
```

### After

```text
Entrypoint execute-post-unlock --execute
→ Session-GO gate
→ Session-GO ↔ authorization binding checks
→ invoke_post_unlock_canonical_runtime_v1
→ run_offline_productive_restart_orchestration_v1
→ consume-once → lock → PRE harness (82) → POST recovery → verifier
→ invocation manifest + lock release
```

`productive-session` remains gate-only and side-effect free.

## Goal

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false  # no real productive auth consumption
SESSION_EXECUTION_ALLOWED=false          # no real network session
POST_UNLOCK_RUNTIME_INVOCATION_ADDED=true
PRODUCTIVE_EXECUTE_MODE_EXPLICIT=true
```

## Session-GO issuance

Uses preexisting `build_session_go_authority_v1`. Session-GO CLI gains `issue`
for ephemeral ACTIVE artifacts (SHA/config/session/entrypoint/scope/expiry bound).
No static ACTIVE artifact is committed to the repository.

## Out of scope

- Real productive public-MD network session execution
- Live / Testnet / Paper exchange orders
- Exchange credentials
- Core trading-logic or numeric config changes
- Ruleset / Notion mutation
- Parallel runner or alternate authorization domain
