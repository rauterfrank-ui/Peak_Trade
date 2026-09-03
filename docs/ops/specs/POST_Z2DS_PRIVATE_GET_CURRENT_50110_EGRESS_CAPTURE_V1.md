---
docs_token: DOCS_TOKEN_POST_Z2DS_PRIVATE_GET_CURRENT_50110_EGRESS_CAPTURE_V1
status: active
scope: One-shot GET-only post-Z2DS 50110 egress IPv4 capture; no POST; no whitelist
capability: POST_Z2DS_PRIVATE_GET_CURRENT_50110_EGRESS_CAPTURE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# Post-Z2DS Private GET Current 50110 Egress Capture V1

## Goal

Execute exactly one authenticated GET
`&#47;api&#47;v5&#47;account&#47;config` on the bound live-canary SecretRef to capture a
current OKX 50110-reported egress IPv4 as forensic input for the already
authorized, not-consumed whitelist GO. No whitelist mutation. No P08 close.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
WHITELIST_MUTATION_PERFORMED=false
ORDER_PERFORMED=false
POSITION_CREATION_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
PREREQUISITE_08_CLOSED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`, and
the live-canary SecretRef. Does not consume
`PEAK_TRADE_OWNER_GO_OKX_EEA_EXTERNAL_IP_WHITELIST_MINIMUM_ADD_CURRENT_50110_EGRESS_V1`.

## Out of scope

- POST / order submit / position creation / flatten
- IP whitelist mutation
- Positions GET / P08 observation
- Funding GET
- Historical Z2DS IP fallback

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1&#47;execute_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1&#47;persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1/20260903T171133Z/
GET_REQUEST_COUNT=1
HTTP_STATUS=401
OKX_CODE=50110
RESULT_CLASS=HTTP_401_OKX_50110
OKX_REPORTED_EGRESS_IPV4=176.5.200.177
HISTORICAL_Z2DS_IP_USED=false
WHITELIST_MUTATION_PERFORMED=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
```
