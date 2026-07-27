# WEBUI_CI_HEALTH_READ_SURFACE_SIDE_EFFECT_ELIMINATION_V1

**Capability ID:** `WEBUI_CI_HEALTH_READ_SURFACE_SIDE_EFFECT_ELIMINATION_V1`  
**Mode:** Make CI-health GET surfaces strictly read-only. **Non-authorizing for trading.**  
**Does not:** change Local-Admin auth, Knowledge POSTs, Market Dashboard, Runtime, Orders, Host/CSRF/Bind gates, GitHub, or Notion.

## Objective

Ensure:

- `GET &#47;ops&#47;ci-health`
- `GET &#47;ops&#47;ci-health&#47;status`

are safe and idempotent:

- no check execution
- no subprocess
- no git command
- no snapshot write / directory creation
- no hidden refresh

Only authenticated `POST &#47;ops&#47;ci-health&#47;run` may execute checks and refresh snapshots.

## Canonical owners (reuse)

| Role | Path |
|------|------|
| Router / runner / writer / reader | [`src/webui/ops_ci_health_router.py`](../../../src/webui/ops_ci_health_router.py) |
| Local-admin write auth (unchanged) | [`src/webui/local_admin_write_auth_v1.py`](../../../src/webui/local_admin_write_auth_v1.py) |
| Snapshot JSON | `reports&#47;ops&#47;ci_health_latest.json` |
| Redaction boundary (reuse) | [`scripts/security/secret_hygiene_redaction_v1.py`](../../../scripts/security/secret_hygiene_redaction_v1.py) |
| UI | [`templates/peak_trade_dashboard/ops_ci_health.html`](../../../templates/peak_trade_dashboard/ops_ci_health.html) |

A second CI-health router/runner/writer/auth owner is forbidden.

## Route contracts

| Method | Path | Behavior |
|--------|------|----------|
| `GET` | `&#47;ops&#47;ci-health` | Render persisted snapshot state only |
| `GET` | `&#47;ops&#47;ci-health&#47;status` | Return persisted snapshot JSON projection only |
| `POST` | `&#47;ops&#47;ci-health&#47;run` | Auth-gated execution + snapshot write (unchanged auth model) |

### GET contract

- safe, idempotent
- no subprocess / git / filesystem mutation / background task / hidden execution
- missing snapshot => controlled `SNAPSHOT_ABSENT` (no file/dir creation)
- invalid JSON/structure/size/encoding => controlled `SNAPSHOT_INVALID`
- aged snapshot => `SNAPSHOT_STALE` (data still returned when parseable)
- fresh valid snapshot => `SNAPSHOT_AVAILABLE`

### POST /run contract

Owned by `WEBUI_LOCAL_ADMIN_WRITE_SURFACE_AUTH_GATE_V1`:

- fail-closed Local-Admin token gate
- runner + writer allowed only after auth
- token transport/redaction unchanged

## Snapshot read states

| State | Meaning |
|-------|---------|
| `SNAPSHOT_ABSENT` | Canonical JSON file not present |
| `SNAPSHOT_INVALID` | Unreadable, oversized, non-UTF8, non-JSON, or wrong structure |
| `SNAPSHOT_STALE` | Valid payload older than 24h |
| `SNAPSHOT_AVAILABLE` | Valid payload within freshness window |

Reader constraints:

- fixed path only (`reports&#47;ops&#47;ci_health_latest.json`)
- no request-derived paths
- bounded file size
- controlled UTF-8/JSON parsing
- WebUI redaction via `redact_for_webui_payload`
- no host/traceback leakage in client payloads

## Explicit non-goals

- Changing Local-Admin auth semantics
- Securing unrelated GET routes outside CI-health
- Market Dashboard authentication
- Trading / risk / execution / runtime / order authority
- Snapshot schema redesign beyond controlled reading
- Host/CSRF/bind gates

## Proof owners

| Proof | Owner |
|-------|-------|
| GET no side effects + snapshot states | `tests/webui/test_ops_ci_health_router.py` |
| POST auth + runner/writer | `tests/webui/test_ops_ci_health_router.py` |
| Local-admin owner uniqueness | `tests/webui/test_webui_local_admin_write_surface_auth_gate_v1.py` |

## Authority statement

This capability does **not** change trading, risk, execution, scheduler, runtime, promotion, or capital semantics. It only removes execution/write side effects from CI-health GET surfaces.
