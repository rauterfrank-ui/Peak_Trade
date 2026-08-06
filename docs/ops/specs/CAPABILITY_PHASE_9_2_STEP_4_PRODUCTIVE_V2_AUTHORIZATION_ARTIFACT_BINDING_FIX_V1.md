---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_PRODUCTIVE_V2_AUTHORIZATION_ARTIFACT_BINDING_FIX_V1
status: active
scope: Phase 9.2 Step-4 productive V2 authorization artifact scope/digest binding fix; no network session
capability: PHASE_9_2_STEP_4_PRODUCTIVE_V2_AUTHORIZATION_ARTIFACT_BINDING_FIX_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Step-4 Productive V2 Authorization Artifact Binding Fix V1

## Forensic gap (after PR #5760)

Governed Step-4 network derivation compared unrelated layers as strings:

| Layer | Canonical value |
| --- | --- |
| `authorization_artifact_v2.network_scope` | `PUBLIC_MARKET_DATA_ONLY` |
| Operator-GO `network_scope` | `okx_eea_futures_public_md_observe_v1` |

and compared unrelated digest domains when both were 64-hex:

| Domain | Owner / payload |
| --- | --- |
| `activation_config` | `single_future_stateful_no_order_runtime_activation_v1.config_digest` |
| `wallclock_config_identity` | `sha256(WALLCLOCK_CONFIG_IDENTITY)` from productive issuer |
| `effective_session_config` | V2 `session_config_digest` / `config_digests.effective_session_config` |

Real productive issuance + verify passed; Step-4 adapter fail-closed with
`ARTIFACT_NETWORK_SCOPE_MISMATCH`, `AUTHORIZATION_CONFIG_MISMATCH`, and
`NETWORK_ALLOWED_MISSING_FROM_AUTHORIZATION`.

## Closed by this capability

1. Explicit two-layer scope binding (artifact `PUBLIC_MARKET_DATA_ONLY` + GO venue scope).
2. Domain-typed config digest binding (no cross-schema 64-hex compare).
3. V2 internal session-config integrity via canonical mandatory binding validator.
4. Producer-parity checks for wallclock/code identity digests.
5. Unconsumed authorization after adapter validation; consumed/revoked states fail-closed.
6. Session-request adapter governed path binds `wallclock_config_identity` domain for V2.

## Call graph before / after

Before:

```text
Operator-GO.network_scope
+ artifact.network_scope  →  string equality against okx_eea…  (wrong layer)
expected activation digest
+ artifact.wallclock_config_identity → 64-hex equality (wrong domain)
```

After:

```text
artifact.network_scope == PUBLIC_MARKET_DATA_ONLY
AND Operator-GO.network_scope == okx_eea_futures_public_md_observe_v1
AND Operator-GO.network_authorized == true
AND domain-typed digest bind (wallclock_config_identity | effective_session_config | …)
→ network_allowed
```

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
NETWORK_SESSION_STARTED=false
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```
