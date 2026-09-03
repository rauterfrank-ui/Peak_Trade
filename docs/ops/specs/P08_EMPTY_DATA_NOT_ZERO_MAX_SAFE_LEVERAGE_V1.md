---
docs_token: DOCS_TOKEN_P08_EMPTY_DATA_NOT_ZERO_MAX_SAFE_LEVERAGE_V1
status: active
scope: Minimum-necessary GET-only P08 CASE_C follow-up; no POST; empty data is not zero
capability: P08_EMPTY_DATA_NOT_ZERO_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P08 Empty Data Not Zero Max Safe Leverage V1

## Goal

Resolve `CASE_C_EMPTY_DATA_NOT_ZERO` from the predecessor unfiltered
positions GET by the minimum necessary authenticated private GETs on
`&#47;api&#47;v5&#47;account&#47;positions` for target instrument
`SUI-USD_UM_XPERP-310404`. Empty `data=[]` is not zero. Filtered empty is
not zero. Typed empty is not zero. Absence of a target row is not zero.

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
TARGET_POSITION_ZERO_PROVEN=false
TARGET_POSITION_NONZERO_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EMPTY_DATA_IS_ZERO=false
FILTERED_EMPTY_IS_ZERO=false
TYPED_EMPTY_IS_ZERO=false
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`,
`classify_target_position_state_v1`, `classify_position_observation_v1`,
and `build_account_positions_query_v1`. Same live-canary SecretRef as the
predecessor P08 observation. Does not authorize POST, flatten, P09 work,
funding, balance GET, config GET, or Submit-Body `posSide` proof.

## GET sequence

1. Unfiltered `GET &#47;api&#47;v5&#47;account&#47;positions`.
2. If and only if GET 1 is `CASE_C_EMPTY_DATA_NOT_ZERO`: target
   `instId` GET.
3. If and only if GET 2 still did not observe the target row:
   `instType=FUTURES` GET.

## Out of scope

- POST &#47; order submit &#47; position creation &#47; flatten
- Funding GET &#47; balance GET &#47; config GET &#47; max-size GET &#47;
  positions-history GET
- IP whitelist &#47; credential mutation
- P09 or later prerequisite workpackages
- Submit-Body posSide probe
- Treating empty, filtered-empty, or typed-empty as zero

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_p08_empty_data_not_zero_v1&#47;execute_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p08_empty_data_not_zero_v1&#47;persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_p08_empty_data_not_zero_v1/20260903T193620Z/
OWNER_GO_CONSUMED=true
GET_REQUEST_COUNT=3
HTTP_EXCHANGE_COUNT=3
RETRY_COUNT=0
HTTP_STATUS=200
OKX_CODE=0
RESULT_CLASS=HTTP_200_OKX_0
POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO
EXCHANGE_CLASSES=CASE_C_EMPTY_DATA_NOT_ZERO;CASE_C_EMPTY_DATA_NOT_ZERO;CASE_C_EMPTY_DATA_NOT_ZERO
DATA_ROW_COUNT=0
EMPTY_DATA_IS_ZERO=false
FILTERED_EMPTY_IS_ZERO=false
TYPED_EMPTY_IS_ZERO=false
UNFILTERED_EMPTY_AND_TYPED_NONEMPTY=false
P08_CLOSED=false
P08_VERDICT=P08_NOT_CLOSED_EMPTY_DATA_REMAINS_NOT_ZERO
TARGET_POSITION_ZERO_PROVEN=false
TARGET_POSITION_NONZERO_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
BODY_SHA256=fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a
BYTE_IDENTICAL_HISTORICAL_P08_EMPTY_ENVELOPE_SHA=true
BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true
NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_REQUIRED_P08_STILL_NOT_CLOSED_EMPTY_DATA_REMAINS_NOT_ZERO
```
