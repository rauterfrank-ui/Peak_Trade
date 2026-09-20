---
docs_token: DOCS_TOKEN_PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1
status: active
scope: PL-TF-002 governed read-only GET session executor; ephemeral K1 Keychain; no capture; no status flip
capability: PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# PL-TF-002 Productive Read-Only Session Executor V1

## Goal

Close the governed session gap between `OWNER_GO` and productive F1/F2 GET
capture. This package authorizes **ephemeral** K1 macOS Keychain acquisition
and bind to `FullCoreProductiveReadOnlyGetTransportV1`. It does not capture
evidence, flip `PL_TF_002_STATUS`, or perform GETs by itself.

```text
WP_ID=PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1
OWNER_GO=OWNER_GO_PL_TF_002_PRODUCTIVE_READ_ONLY_SESSION_EXECUTOR_V1
EXPECTED_ORIGIN_MAIN_SHA=de4c769acdfb70a620efe465bd91684b8626c5f2
AUTHORIZED_HOST=eea.okx.com
HTTP_METHOD=GET
RUNTIME_AUTHORIZATION_EFFECT=NONE
NETWORK_EXECUTION_AUTHORIZED=false
CREDENTIAL_LOAD_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Governed transition

```text
OWNER_GO(WP-scoped)
  -> build_pl_tf_002_read_only_get_session_preflight_v1 (no secrets)
  -> bounded_ephemeral_keychain_access_v1 (consumer PL_TF_002 only)
  -> K1 opaque macOS Keychain acquisition (existing EA adapter)
  -> parse_k1_keychain_utf8_json_material_v1 (closed apiKey/secretKey/passphrase)
  -> bind_already_held_k1_venue_auth_session_v1
  -> FullCoreProductiveReadOnlyGetTransportV1(handle=...)
```

Standing module pins remain false (`MAY_PERFORM_GET`, `REAL_KEYCHAIN_ACCESS_AUTHORIZED`).
Owner-GO never substitutes for credential material.

## K1 Keychain UTF-8 JSON (closed world)

Not SecretRef. Not vault file. Not Canary JSON.

| Field | Required |
|-------|----------|
| apiKey | yes |
| secretKey | yes |
| passphrase | yes |

## Non-claims

```text
No productive GET in this capability default
No evidence persist
No PL_TF_002 status promotion
No K2 / SecretRef / file-vault reintroduction
No POST / Treasury mutation / external effect mint
PDF TARGET_AUTHORITY=NONE
```
