---
docs_token: DOCS_TOKEN_POST_Z2DR_RUNTIME_READ_ONLY_EVIDENCE_MAX_LEVERAGE_V1
status: active
scope: GET-only post-Z2DR maximum-safe-leverage runtime evidence; no POST; no live wire
capability: POST_Z2DR_RUNTIME_READ_ONLY_EVIDENCE_MAX_LEVERAGE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# Post-Z2DR Runtime Read-Only Evidence Maximum Leverage V1

## Goal

After §11.13.5.Z2DR proved `OFFLINE_CLOSABLE_GAP_COUNT=0`, execute the
largest compatible read-only OKX GET bundle to refresh runtime observations
for the Z2DR blocker DAG without POST, position creation, or funding actions.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
ORDER_PERFORMED=false
POSITION_CREATION_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
CREATE_PATH_CURRENTLY_AUTHORIZED=false
PREREQUISITE_08_CLOSED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`, and
the live-canary SecretRef. Does not prove submit-body `posSide` semantics.
GET `posMode` is account-config evidence only.

## Out of scope

- POST / order submit / position creation / flatten
- Funding GET (`/api/v5/asset/balances`)
- Credential or IP whitelist mutation
- Live / testnet / canary activation

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src/ops/section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1/execute_v1.py` |
| Adjudication | `src/ops/section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1/adjudicate_v1.py` |
| Evidence persist | `src/ops/section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1/persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1/20260903T155946Z/
GET_REQUEST_COUNT=10
PUBLIC_GET_COUNT=3
PRIVATE_GET_COUNT=7
FUNDING_GET_PERFORMED=false
POST_PERFORMED=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
PRIVATE_AUTH_FAILURE=HTTP_401_OKX_50110
MAX_SAFE_READ_ONLY_RUNTIME_BUNDLE_REMAINING=0
```
