---
docs_token: DOCS_TOKEN_POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1
status: active
scope: One-shot GET-only post-whitelist private auth attestation; no POST; no P08
capability: POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# Post-Z2DS Post-Whitelist Private Auth Attestation Single GET V1

## Goal

Execute exactly one authenticated GET
`&#47;api&#47;v5&#47;account&#47;config` on the bound live-canary SecretRef after
the persisted OKX EEA IP-whitelist minimum add, to attest whether HTTP
401 / OKX 50110 is cleared for this endpoint at observation time. No
second GET. No P08 observation or close.

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
TARGET_POSITION_NONZERO_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`, and
the live-canary SecretRef. Does not authorize P08, positions GET, funding,
orders, or further whitelist mutation.

## Out of scope

- POST / order submit / position creation / flatten
- IP whitelist mutation
- Positions GET / P08 observation or close
- Funding GET / balance GET / max-size GET
- Submit-Body posSide inference from account/config

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1&#47;execute_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1&#47;persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1/20260903T181718Z/
OWNER_GO_CONSUMED=true
GET_REQUEST_COUNT=1
HTTP_EXCHANGE_COUNT=1
HTTP_STATUS=200
OKX_CODE=0
RESULT_CLASS=HTTP_200_OKX_0
PRIVATE_API_AUTH_SUCCESS=PROVEN_FOR_THIS_ENDPOINT_AND_OBSERVATION_TIME
RUNTIME_50110_CLEARANCE=PROVEN_FOR_THIS_ENDPOINT_AND_OBSERVATION_TIME
PRIVATE_AUTH_BLOCKER_50110=CLEARED_AT_OBSERVATION_TIME
OKX_REPORTED_EGRESS_IPV4=NONE
PREREQUISITE_08_CLOSED=false
WHITELIST_MUTATION_PERFORMED=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_FOR_P08_POSITION_OBSERVATION
```
