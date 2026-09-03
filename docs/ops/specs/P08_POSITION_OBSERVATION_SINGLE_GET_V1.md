---
docs_token: DOCS_TOKEN_P08_POSITION_OBSERVATION_SINGLE_GET_V1
status: active
scope: One-shot GET-only P08 unfiltered positions observation; no POST; no P08 close on empty data
capability: P08_POSITION_OBSERVATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P08 Position Observation Single GET V1

## Goal

Execute exactly one authenticated unfiltered GET
`&#47;api&#47;v5&#47;account&#47;positions` on the bound live-canary SecretRef
to adjudicate `EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN`
for target instrument `SUI-USD_UM_XPERP-310404`. No second GET. No POST.
Empty `data=[]` is not zero and does not close P08.

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
EMPTY_DATA_IS_ZERO=false
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`,
`classify_target_position_state_v1`, and
`build_account_positions_query_v1` unfiltered. Same live-canary SecretRef
as the post-whitelist private-auth attestation. Does not authorize POST,
flatten, P09 work, funding, or Submit-Body `posSide` proof.

## Out of scope

- POST / order submit / position creation / flatten
- Filtered `instId` GET
- Funding GET / balance GET / config GET / max-size GET
- IP whitelist / credential mutation
- P09 or later prerequisite workpackages
- Submit-Body posSide probe

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_p08_position_observation_v1&#47;execute_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p08_position_observation_v1&#47;persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_p08_position_observation_v1/20260903T190424Z/
OWNER_GO_CONSUMED=true
GET_REQUEST_COUNT=1
HTTP_EXCHANGE_COUNT=1
RETRY_COUNT=0
HTTP_STATUS=200
OKX_CODE=0
RESULT_CLASS=HTTP_200_OKX_0
POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO
DATA_ROW_COUNT=0
EMPTY_DATA_IS_ZERO=false
P08_CLOSED=false
P08_VERDICT=P08_NOT_CLOSED_EMPTY_DATA_IS_NOT_ZERO
TARGET_POSITION_NONZERO_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
BODY_SHA256=fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a
BYTE_IDENTICAL_Z2CN_EMPTY_ENVELOPE_SHA=true
BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true
NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_REQUIRED_P08_EMPTY_DATA_IS_NOT_ZERO
```
