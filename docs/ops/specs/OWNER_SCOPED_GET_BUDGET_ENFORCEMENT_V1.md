---
docs_token: DOCS_TOKEN_OWNER_SCOPED_GET_BUDGET_ENFORCEMENT_V1
status: active
scope: Durable cumulative Owner GET budget for PL-TF-002 productive read-only transport
capability: OWNER_SCOPED_GET_BUDGET_ENFORCEMENT_V1
last_updated: 2026-10-15
---

# Owner-Scoped GET Budget Enforcement V1

## Problem

Per-process `request_count` on `FullCoreProductiveReadOnlyGetTransportV1` resets on
each new process. Owner-scoped `MAX_HTTP_REQUESTS` must apply cumulatively across
session restarts within one bounded operation.

## Enforcement boundary

Atomic **pre-send reservation** on durable grant ledger (filesystem, lock-held
mutate + atomic JSON replace). Wired into `FullCoreProductiveReadOnlyGetTransportV1.get`
immediately before wire I/O.

## Grant identity

`owner_grant_identity_digest = SHA256(canonical binding)` with binding fields:

- `owner_go`
- `work_package_id`
- `origin_main_sha`
- `cumulative_request_budget`
- `authorized_host`
- `http_method_allowlist` (GET only)

One grant ledger file per identity (append-only mint).

## PL-TF-002 integration

Optional `owner_scoped_get_budget_grant` on
`open_pl_tf_002_productive_read_only_get_session_v1`.

F1 capture requires `owner_scoped_get_budget_store_root` and
`owner_scoped_cumulative_request_budget` when `execute_network=true`. The ops runner
defaults Owner cumulative budget to `F1_OWNER_SCOPED_CUMULATIVE_GET_BUDGET` (9).
Transport technical cap `MAX_NETWORK_REQUEST_COUNT` (16) is unchanged.

## Non-claims

```text
RUNTIME_AUTHORIZATION_EFFECT=NONE
Does not mint LIVE/POST/trading authority
Does not persist credentials
Does not replace canonical durable authorization v2 wallclock artifacts
```
