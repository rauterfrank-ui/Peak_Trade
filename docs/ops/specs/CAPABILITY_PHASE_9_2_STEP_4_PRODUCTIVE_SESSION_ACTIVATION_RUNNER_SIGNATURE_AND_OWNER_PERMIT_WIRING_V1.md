---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_PRODUCTIVE_SESSION_ACTIVATION_RUNNER_SIGNATURE_AND_OWNER_PERMIT_WIRING_V1
status: active
scope: Phase 9.2 Step-4 owner-session permit transport and wallclock runner signature binding; no network session
capability: PHASE_9_2_STEP_4_PRODUCTIVE_SESSION_ACTIVATION_RUNNER_SIGNATURE_AND_OWNER_PERMIT_WIRING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Step-4 Activation Runner Signature And Owner Permit Wiring V1

## Forensic gap (predecessor activation binding)

After `PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_ACTIVATION_BINDING_V1` (#5754):

```text
CLI_HARDCODES_permit_canonical_runner_invoke=False
ACTIVATION_INVOKES_runner(session_request=...)
CANONICAL_RUNNER_REJECTS_unexpected_keyword_session_request
PRODUCTIVE_SESSION_PATH_RUNTIME_REACHABLE_FOR_REAL_NETWORK=false
HARD_STOP_REASON=CLI_PERMIT_FALSE_AND_RUNNER_SIGNATURE_MISMATCH
```

## Closed by this capability

1. Explicit typed CLI Owner Session Permit:
   `--permit-canonical-runner-invoke`
   Distinct from `--owner-go`, `--owner-session-go`, and
   `--network-session-allowed`. Default remains false (fail-closed).

2. Signature-compatible invoke binding to existing
   `run_productive_wallclock_session_v1` keyword-only parameters
   via `runner_invoke_binding_v1.build_canonical_wallclock_runner_kwargs_v1`.

3. Two-stage gating:
   - missing permit → `OWNER_SESSION_PERMIT_REQUIRED` (no consume, no runner)
   - `network_session_allowed=false` → `DRY_NO_NETWORK` (no consume, no runner)
   - structural reachability claims remain true when permit + signature bind

## Call graph

```text
CLI --permit-canonical-runner-invoke
→ execute_productive_rate_limit_reconnect_session_activation_v1
→ owner session and network gates
→ build_canonical_wallclock_runner_kwargs_v1
→ (only if network_session_allowed) auth and confirm validate+consume
→ run_productive_wallclock_session_v1(**exact_kwargs)
```

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false (capability default)
NETWORK_SESSION_STARTED=false
AUTHORIZATION_CONSUMED=false on dry path
CONFIRM_TOKEN_CONSUMED=false on dry path
NO_NEW_SESSION_LOGIC=true
NO_NEW_RETRY_BACKOFF_RECONNECT_POLICY=true
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Out of scope

- Starting a real Public-MD network session
- Auth or Confirm-Token consumption under this capability order
- Live, Testnet, Paper exchange, credentials, or capital
- Core trading logic or effective trading values
- Dashboard, presentation, Notion, or ruleset mutation
