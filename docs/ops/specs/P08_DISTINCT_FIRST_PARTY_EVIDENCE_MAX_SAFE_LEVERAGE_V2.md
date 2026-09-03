---
docs_token: DOCS_TOKEN_P08_DISTINCT_FIRST_PARTY_EVIDENCE_MAX_SAFE_LEVERAGE_V2
status: active
scope: Distinct first-party GET-only P08 follow-up; no POST; empty/history/risk absence is not zero
capability: P08_DISTINCT_FIRST_PARTY_EVIDENCE_V2
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P08 Distinct First-Party Evidence Max Safe Leverage V2

## Goal

Maximize evidential resolution of `CASE_C_EMPTY_DATA_NOT_ZERO` using
distinct first-party authenticated private GET channels. Do not repeat
equivalent `&#47;account&#47;positions` empty-envelope probes. Empty
`data=[]` is not zero. History empty is not never-held and not current
zero. Risk `posData=[]` is not zero. Absence of a target row is not
zero. `posId` is never invented.

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
TARGET_POS_ID_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EMPTY_DATA_IS_ZERO=false
HISTORY_EMPTY_IS_NEVER_HELD=false
HISTORY_EMPTY_IS_CURRENT_ZERO=false
RISK_POSDATA_EMPTY_IS_ZERO=false
CROSS_CHECK_IS_CANONICAL_AUTHORITY=false
HISTORICAL_STATE_IS_CURRENT_STATE=false
EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED=false
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`,
`classify_target_position_state_v1`, `classify_position_observation_v1`,
and `build_account_positions_query_v1` (posId path only). Same
live-canary SecretRef as the predecessor P08 packages. History and risk
query grammars are the already-proven Z2CH / Z2V first-party bindings.
Does not authorize POST, flatten, P09 work, funding, balance GET, config
GET, unfiltered/instId/instType positions GETs, or Submit-Body `posSide`
proof.

## Distinct GET sequence

1. Target `GET &#47;api&#47;v5&#47;account&#47;positions-history?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404`
   for posId recovery in the first-party last-3-months window.
2. If and only if GET 1 is empty and did not prove a posId: typed
   history `instType=FUTURES` to discriminate filter incompleteness.
3. Independent cross-check `GET &#47;api&#47;v5&#47;account&#47;account-position-risk?instType=FUTURES`.
   Risk `posData` is not canonical P08 authority.
4. `GET &#47;api&#47;v5&#47;account&#47;positions?posId=` only if a target
   `posId` is first independently proven. Never invent posId.

## Out of scope

- POST &#47; order submit &#47; position creation &#47; flatten
- Repeating unfiltered, instId, or instType `&#47;account&#47;positions`
  empty-envelope probes
- Funding GET &#47; balance GET &#47; config GET &#47; max-size GET
- IP whitelist &#47; credential mutation
- P09 or later prerequisite workpackages
- Submit-Body posSide probe
- Treating empty, history-empty, typed-empty, or risk-empty as zero
- Promoting historical H0 or documentation semantics to current state

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_p08_distinct_first_party_evidence_v1&#47;execute_v1.py` |
| Channel classifiers | `src&#47;ops&#47;section_11_13_5_p08_distinct_first_party_evidence_v1&#47;classify_v1.py` |
| Query grammar | `src&#47;ops&#47;section_11_13_5_p08_distinct_first_party_evidence_v1&#47;query_grammar_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p08_distinct_first_party_evidence_v1&#47;persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_p08_distinct_first_party_evidence_v1/20260903T200738Z/
OWNER_GO_CONSUMED=true
GET_REQUEST_COUNT=3
HTTP_EXCHANGE_COUNT=3
RETRY_COUNT=0
HTTP_STATUS=200
OKX_CODE=0
RESULT_CLASS=HTTP_200_OKX_0
POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO
GET_ROLES_PERFORMED=TARGET_POSITIONS_HISTORY;TYPED_POSITIONS_HISTORY;ACCOUNT_POSITION_RISK
HISTORY_OBSERVATION_CLASS=HISTORY_EMPTY_NOT_NEVER_HELD_NOT_CURRENT_ZERO
RISK_OBSERVATION_CLASS=RISK_POSDATA_EMPTY_NOT_ZERO
POSID_POSITIONS_GET_PERFORMED=false
TARGET_POS_ID_PROVEN=false
EMPTY_DATA_IS_ZERO=false
HISTORY_EMPTY_IS_NEVER_HELD=false
HISTORY_EMPTY_IS_CURRENT_ZERO=false
RISK_POSDATA_EMPTY_IS_ZERO=false
P08_CLOSED=false
P08_VERDICT=P08_NOT_CLOSED_DISTINCT_CHANNELS_DO_NOT_PROVE_CURRENT_ZERO_OR_NONZERO
TARGET_POSITION_ZERO_PROVEN=false
TARGET_POSITION_NONZERO_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
HISTORY_BODY_SHA256=fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a
RISK_BODY_SHA256=c43be6927e571d74be5ebe5fd656bb26b827f39b3e1d5300f8df97ea23f7a4f3
BYTE_IDENTICAL_HISTORICAL_EMPTY_ENVELOPE_SHA=true
BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true
NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_REQUIRED_P08_STILL_NOT_CLOSED_DISTINCT_CHANNELS_DO_NOT_PROVE_CURRENT_STATE
```
