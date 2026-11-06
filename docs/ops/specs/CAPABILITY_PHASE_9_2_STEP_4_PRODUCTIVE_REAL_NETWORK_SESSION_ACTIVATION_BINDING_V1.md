---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_ACTIVATION_BINDING_V1
status: active
scope: Phase 9.2 Step-4 productive session activation binding; no network session start
capability: PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_ACTIVATION_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Step-4 Productive Real-Network Session Activation Binding V1

## Forensic gap (predecessor wiring)

After `PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_WIRING_V1` (#5753):

```text
CURRENT_PRODUCTIVE_ENTRYPOINT=
  scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py
CURRENT_PRODUCTIVE_EXECUTOR=
  productive_executor_v1.execute_productive_rate_limit_reconnect_session_wiring_v1
EXISTING_WALLCLOCK_RUNNER=
  run_productive_wallclock_session_v1
CURRENT_READY_FOR_PRODUCTIVE_SESSION_EXECUTION=true
CURRENT_WALLCLOCK_RUNNER_INVOKED=false
CURRENT_NETWORK_SESSION_ALLOWED=false
CURRENT_REQUEST_REAL_NETWORK_BLOCKED=true
PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE=false
```

Wiring bound the Gate→Runner symbols but never closed the productive call graph
to a gated runner invocation.

## Call graph before / after

Before:

```text
Session-GO → Gate → boundary → fault bind → import runner symbol → evidence template
(WALLCLOCK_RUNNER_INVOKED=false always)
```

After:

```text
Session-GO + Owner-GO + Owner-Session-GO
→ --request-real-network
→ network_session_allowed
→ authorization validation
→ confirm-token validation
→ public-MD-only boundary
→ authorization + confirm-token consumption at start boundary
→ existing run_productive_wallclock_session_v1 (injected double in tests)
→ existing fault / rate-limit / reconnect / heartbeat / stale owners
→ existing evidence + verifier
```

Without full Gate PASS: `WALLCLOCK_RUNNER_INVOKED=false`,
`AUTHORIZATION_CONSUMED=false`, `CONFIRM_TOKEN_CONSUMED=false`,
`NETWORK_REQUEST_COUNT=0`.

## Gate order

1. OWNER_GO / OWNER_SESSION_GO
2. REQUEST_REAL_NETWORK
3. NETWORK_SESSION_ALLOWED (runtime; permanent constant remains false)
4. PUBLIC_MARKET_DATA_ONLY + forbidden Live/Testnet/Private/Credential/Capital scopes
5. Session-GO binding gate (`real_network_may_proceed`)
6. Public-MD network boundary
7. Authorization validate
8. Confirm-token validate
9. Consume auth + confirm-token (start boundary only)
10. Invoke existing wallclock runner exactly once

## Boundaries

```text
DEFAULT_NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_CONSUMED_ONLY_AT_START_BOUNDARY=true
CONFIRM_TOKEN_CONSUMED_ONLY_AT_START_BOUNDARY=true
CONFIRM_TOKEN_PLAINTEXT never in argv/logs/evidence/diffs
NO_DIRECT_UNGOVERNED_RUNNER_CALL=true
CLI refuses uninjected canonical runner invoke
IMPLEMENTATION_CAPABILITY_NETWORK_SESSION_STARTED=false
RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Reuse

- Wallclock runner: `run_productive_wallclock_session_v1`
- Confirm-token: `confirm_token_v1` (file|env|in-memory)
- Fault/429/backoff/reconnect/stale: existing Step-4 / wallclock owners
- No new session / fault / retry / backoff / reconnect semantics

## Out of scope

- Starting a real Public-MD network session in this PR
- Live / Testnet / Paper exchange orders / credentials / capital
- Core trading logic / effective trading values
- Dashboard / presentation / Notion / ruleset mutation
