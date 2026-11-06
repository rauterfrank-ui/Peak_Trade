# WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1

**Capability ID:** `WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1`  
**Mode:** Fail-closed local-admin authentication for WebUI administrative write/trigger surfaces. **Non-authorizing for trading.**  
**Does not:** provide OAuth/SSO/IdP, remote-internet-grade authentication, TLS termination, reverse-proxy design, or Live/Testnet/Order/Scheduler/Capital authority.

## Objective

Prevent unauthenticated callers that can reach the local/operator WebUI HTTP process from:

- triggering `POST &#47;ops&#47;ci-health&#47;run` (subprocess + report writes)
- mutating Knowledge state via WebUI POST endpoints

## Threat boundary

The local/operator WebUI process may be reachable by another local process, an unintended browser tab, or a LAN-adjacent client when bound beyond loopback. This capability closes the **unauthenticated administrative write/trigger** gap. It does **not** claim remote exposure approval or market-dashboard authentication.

`&#47;market` remains a pure read-only consumer. No Market Dashboard controls were added.

## Canonical owner

| Role | Path |
|------|------|
| Auth owner | [`src/webui/local_admin_write_auth_v1.py`](../../../src/webui/local_admin_write_auth_v1.py) |
| Consumers | [`src/webui/ops_ci_health_router.py`](../../../src/webui/ops_ci_health_router.py), [`src/webui/knowledge_api.py`](../../../src/webui/knowledge_api.py) |
| UI | [`templates/peak_trade_dashboard/ops_ci_health.html`](../../../templates/peak_trade_dashboard/ops_ci_health.html) |
| Redaction (reuse only) | [`scripts/security/secret_hygiene_redaction_v1.py`](../../../scripts/security/secret_hygiene_redaction_v1.py) |

A second auth/redaction/scanner/ruleset owner is forbidden.

## Protected route inventory

| Method | Path | Side effects when authorized |
|--------|------|------------------------------|
| `POST` | `&#47;ops&#47;ci-health&#47;run` | Runs local check scripts; may persist `reports&#47;ops&#47;ci_health_latest.*` |
| `POST` | `&#47;api&#47;knowledge&#47;snippets` | Mutates Knowledge snippet store |
| `POST` | `&#47;api&#47;knowledge&#47;strategies` | Mutates Knowledge strategy store |

GET/read-only routes are unchanged by this auth capability (no Local-Admin requirement on GET). CI-health GET side-effect elimination is a separate capability: `WEBUI_CI_HEALTH_READ_SURFACE_SIDE_EFFECT_ELIMINATION_V1`.

## Auth model

| Item | Value |
|------|-------|
| Environment variable (name only) | `PEAK_TRADE_WEBUI_LOCAL_ADMIN_TOKEN` |
| Request header | `X-Peak-Trade-Local-Admin-Token` |
| Comparison | SHA-256 digests compared with `hmac.compare_digest` (constant-time) |
| Accepted sources | Request header only |
| Rejected sources | Query parameters, URL paths, form fields, cookies, aliases |

### Default-deny semantics

| Condition | HTTP | Error code |
|-----------|------|------------|
| Server token absent / empty / whitespace-only | 503 | `LOCAL_ADMIN_AUTH_NOT_CONFIGURED` |
| Request header missing or empty | 401 | `LOCAL_ADMIN_AUTH_MISSING` |
| Request token present but invalid | 403 | `LOCAL_ADMIN_AUTH_INVALID` |
| Request token valid | proceed | — |

Environment write flags (`KNOWLEDGE_READONLY`, `KNOWLEDGE_WEB_WRITE_ENABLED`) remain **policy gates**, not caller identity. Knowledge POSTs require **both** local-admin auth and those existing gates. Successful authentication never bypasses the Knowledge env policy gates.

## Redaction and logging

- Prefer categorical diagnostics (`LOCAL_ADMIN_AUTH_*`); do not log raw tokens.
- Reuse the canonical redaction owner at logging/diagnostic boundaries when serializing untrusted payloads.
- Do not create a parallel redaction helper.
- Tokens must not appear in HTTP responses, exception detail, HTML/JS templates, or durable browser storage.

## Browser / UI credential handling

The CI-health Run-now control may prompt ephemerally for the token for a single request:

- Token is sent only in `X-Peak-Trade-Local-Admin-Token`
- Token is never embedded in rendered HTML from server configuration
- Token must not be written to `localStorage`, `sessionStorage`, cookies, IndexedDB, or durable browser state
- Client-side credential reference must be cleared after the request completes
- No general login/session/OAuth/SSO framework is introduced

## Operator usage example (placeholder only)

```bash
export PEAK_TRADE_WEBUI_LOCAL_ADMIN_TOKEN='<set-locally-never-commit>'
curl -X POST 'http://127.0.0.1:8000/ops/ci-health/run' \
  -H 'Accept: application/json' \
  -H 'X-Peak-Trade-Local-Admin-Token: <set-locally-never-commit>'
```

## Proof / test matrix

| Proof | Owner |
|-------|-------|
| Canonical deny/allow + constant-time compare | `tests/webui/test_webui_local_admin_write_surface_auth_gate_v1.py` |
| CI-health POST side-effect denial + GET unchanged | `tests/webui/test_ops_ci_health_router.py` |
| Knowledge env+auth composition | `tests/webui/test_webui_local_admin_write_surface_auth_gate_v1.py` |
| Template header name without embedded token | same |

## Rollback

Revert the Capability PR. Without the auth dependency, previous unauthenticated POST behavior would return; operators should treat rollback as a temporary security regression and restore promptly.

## Explicit non-goals

- OAuth / SSO / external IdP / user accounts / RBAC
- TLS termination / reverse-proxy design / remote exposure approval
- Securing unrelated read-only GET routes
- Market Dashboard `&#47;market` authentication or write controls
- Migrating legacy redaction consumers
- Semgrep / CodeQL / Dependabot / Git-history purge / uv pinning
- GitHub ruleset or required-check mutation
- Runtime / Live / Testnet / Shadow / Paper / Orders / Scheduler / Capital activation
- Trading / risk / execution authority changes

## Authority statement

This capability does **not** change trading, risk, execution, scheduler, runtime, promotion, or capital semantics. GitHub rulesets/settings are not mutated by this capability. Notion is not an enforcement owner.
