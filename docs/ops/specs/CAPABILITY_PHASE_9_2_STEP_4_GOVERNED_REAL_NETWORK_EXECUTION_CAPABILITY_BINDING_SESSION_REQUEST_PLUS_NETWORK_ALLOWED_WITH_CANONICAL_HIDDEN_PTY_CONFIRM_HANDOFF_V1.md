---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_GOVERNED_REAL_NETWORK_EXECUTION_CAPABILITY_BINDING_SESSION_REQUEST_PLUS_NETWORK_ALLOWED_WITH_CANONICAL_HIDDEN_PTY_CONFIRM_HANDOFF_V1
status: active
scope: Phase 9.2 Step-4 governed real-network execution binding; no real network session
capability: PHASE_9_2_STEP_4_GOVERNED_REAL_NETWORK_EXECUTION_CAPABILITY_BINDING_SESSION_REQUEST_PLUS_NETWORK_ALLOWED_WITH_CANONICAL_HIDDEN_PTY_CONFIRM_HANDOFF_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Step-4 Governed Real-Network Execution Binding V1

## Forensic gap (after PR #5756)

The session_request CLI adapter could assemble a signature-compatible request, but:

```text
ADAPTER_FORBIDS_USE_REAL_NETWORK=true
SESSION_REQUEST_ADAPTER_CAPABILITY_FORBIDS_NETWORK_SESSION=true
network_allowed could not be derived from issuance
Hidden-PTY confirm handoff was not bound on the productive Step-4 path
```

## Closed by this capability

1. `derive_network_allowed_from_issuance_authorization_v1` — `network_allowed`
   only from validated Operator-GO + authorization artifact bindings
   (SHA, scope, public-MD network scope, no orders/credentials).
2. Adapter governed mode (`request_governed_public_network=true`) no longer
   blanket-forbids a governed public network request when issuance authorizes it.
3. `acquire_confirm_token_via_canonical_hidden_pty_v1` — Hidden-PTY / secure
   getpass only; missing PTY fails closed with no insecure fallback.
4. `execute_governed_step4_execution_binding_v1` — validate → `SessionLockV1`
   → exactly-once auth/token consume → injected runner stub only.
5. CLI requires `--governed-execution-binding-only` when
   `--network-session-allowed` is combined with issuance artifacts.
   Real sockets/HTTP remain unauthorized by this capability.

## Call graph

```text
Authorization issuance artifacts
→ build_canonical_session_request_from_issuance_artifacts_v1
→ explicit governed-public-network mode
→ network_allowed=true only from validated authorization scope
→ canonical hidden-PTY confirm-token acquisition
→ validate_authorization_binding_v1
→ validate_confirm_token_binding_v1
→ SessionLockV1.acquire
→ consume_authorization_binding_v1
→ consume_confirm_token_binding_v1
→ run_productive_wallclock_session_v1 (injected stub only in this capability)
```

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false (permanent default)
GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED=false
NETWORK_SESSION_EXECUTED=false
REAL_NETWORK_REQUEST_COUNT=0
CONFIRM_TOKEN_PLAINTEXT_EXPOSED=false
PUBLIC_MD_ALLOWLIST=OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY
HTTP_METHOD_ALLOWLIST=GET_ONLY
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Out of scope

- Starting a real Public-MD network session (separate Owner-GO after merge)
- Minting productive authorization / confirm tokens in this PR
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Risk / Safety / Exit changes
- Dashboard / presentation / Notion / ruleset mutation
