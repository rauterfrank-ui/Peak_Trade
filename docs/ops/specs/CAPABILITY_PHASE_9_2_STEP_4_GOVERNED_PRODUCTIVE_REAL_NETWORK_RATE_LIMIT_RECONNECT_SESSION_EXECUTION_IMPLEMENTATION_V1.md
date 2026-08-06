---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_GOVERNED_PRODUCTIVE_REAL_NETWORK_RATE_LIMIT_RECONNECT_SESSION_EXECUTION_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-4 governed productive real-network session execution implementation; no real network session
capability: PHASE_9_2_STEP_4_GOVERNED_PRODUCTIVE_REAL_NETWORK_RATE_LIMIT_RECONNECT_SESSION_EXECUTION_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Step-4 Governed Productive Real-Network Session Execution Implementation V1

## Forensic gap (after PR #5758)

The governed execution binding proved:

```text
session_request assembly
→ auth-derived network_allowed
→ Hidden-PTY confirm handoff
→ SessionLock → consume → injected stub runner
```

but kept:

```text
GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED=false
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY
injected stub only
```

The authorized productive session capability ID
`PHASE_9_2_STEP_4_GOVERNED_PRODUCTIVE_REAL_NETWORK_RATE_LIMIT_RECONNECT_SESSION_EXECUTION_V1`
was absent from HEAD.

## Closed by this capability

1. Explicit implementation capability ID and future runtime capability ID binding.
2. Productive canonical wallclock runner bind (not binding stub) on the governed path.
3. Authorization validation bindings for repository SHA, config digest, scope and expiry.
4. Hidden-PTY confirm-token handoff reuse (no argv / env / visible input fallback).
5. Public-MD GET-only network boundary reuse with negative private/order/auth proofs.
6. Offline rate-limit / retry / backoff / reconnect / staleness fault-path reuse.
7. Evidence schema + implementation manifest + verifier.
8. Fail-closed runtime execute entry that refuses consume/network until separate Owner-GO.

## Call graph before / after

Before:

```text
... → consume → run_productive_wallclock_session_v1 (injected stub only)
REAL_NETWORK_SESSION_FORBIDDEN_IN_BINDING_CAPABILITY
```

After:

```text
Canonical Session Request
→ Authorization Validation
→ Hidden-PTY Confirm Handoff
→ Governed Execution Binding (fail-closed defaults preserved)
→ Productive Wallclock Session Runner (canonical, not stub)
→ Public-MD GET-only Network Adapter
→ Rate-Limit / Retry / Backoff / Reconnect Handling
→ Evidence Manifest
→ Evidence Verifier
```

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false
REAL_NETWORK_REQUESTS_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED=false
GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED=false
NETWORK_SESSION_EXECUTED=false
REAL_NETWORK_REQUEST_COUNT=0
PUBLIC_MD_ALLOWLIST=OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY
HTTP_METHOD_ALLOWLIST=GET_ONLY
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Future runtime capability

After merge, a separately authorized session may use:

```text
PHASE_9_2_STEP_4_GOVERNED_PRODUCTIVE_REAL_NETWORK_RATE_LIMIT_RECONNECT_SESSION_EXECUTION_V1
```

That runtime path remains fail-closed until a separate Owner-GO enables side effects.
This implementation PR does not start a network session and does not consume
authorization or confirm tokens.

## Out of scope

- Starting a real Public-MD network session
- Authorization / confirm-token consumption
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Risk / Safety / Exit changes
- Dashboard / presentation / Notion / ruleset mutation
