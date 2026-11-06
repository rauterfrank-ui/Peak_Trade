---
docs_token: DOCS_TOKEN_P08_READ_ONLY_CLOSURE_MAX_SAFE_LEVERAGE_V3
status: active
scope: Exhaustive read-only P08 identifier-recovery GETs; no POST; empty orders/fills/algo is not zero
capability: P08_READ_ONLY_CLOSURE_V3
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P08 Read-Only Closure Max Safe Leverage V3

## Goal

Exhaust the remaining compatible first-party authenticated private GET
class for `EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN`.
Do not repeat equivalent `&#47;account&#47;positions` empty-envelope
probes. Do not repeat consumed V2 history &#47; risk probes. Empty
`data=[]` is not zero. Empty orders is not never-held and not current
zero. Empty fills is not never-held and not current zero. Empty algo
pending is not current zero. Absence of a target row is not zero.
`posId` is never invented.

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
ORDERS_EMPTY_IS_NEVER_HELD=false
ORDERS_EMPTY_IS_CURRENT_ZERO=false
FILLS_EMPTY_IS_NEVER_HELD=false
FILLS_EMPTY_IS_CURRENT_ZERO=false
HISTORICAL_STATE_IS_CURRENT_STATE=false
EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED=false
P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED
```

## Authority

Reuses `LiveCanaryHttpClientV1`, `build_okx_live_canary_auth_headers_v1`,
`classify_position_observation_v1`, `build_account_positions_query_v1`
(posId path only), and
`build_category_c_orders_algo_pending_endpoint_v1`. Same live-canary
SecretRef as the predecessor P08 packages. Identifier-recovery channels
are not canonical P08 authority. Does not authorize POST, flatten, P09
work, funding, balance GET, config GET, unfiltered &#47; instId &#47;
instType positions GETs, positions-history, account-position-risk, or
Submit-Body `posSide` proof.

## Census dispositions

Consumed &#47; redundant: unfiltered, instId, and instType
`&#47;account&#47;positions`; target and typed positions-history;
FUTURES account-position-risk.

Semantically insufficient: unfiltered risk; instFamily positions;
balance; config &#47; posMode; max-size; leverage-info; bills; asset
balances; public instruments.

Identifier not proven until recovery: `positions?posId=`;
`GET &#47;trade&#47;order` without `ordId`.

Distinct unconsumed (executed in this package):
1. `GET &#47;api&#47;v5&#47;trade&#47;orders-pending?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404`
2. `GET &#47;api&#47;v5&#47;trade&#47;orders-history?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404&limit=100`
3. `GET &#47;api&#47;v5&#47;trade&#47;orders-algo-pending` Category-C
   `ordType` variants `conditional,oco`, `trigger`, `move_order_stop`
4. `GET &#47;api&#47;v5&#47;trade&#47;fills?instType=FUTURES&instId=SUI-USD_UM_XPERP-310404&limit=100`
5. `GET &#47;api&#47;v5&#47;account&#47;positions?posId=` only if a unique
   target `posId` is first independently proven. Never invent posId.

## Out of scope

- POST &#47; order submit &#47; position creation &#47; flatten
- Repeating unfiltered, instId, or instType `&#47;account&#47;positions`
  empty-envelope probes
- Repeating V2 positions-history or account-position-risk
- Funding GET &#47; balance GET &#47; config GET &#47; max-size GET
- IP whitelist &#47; credential mutation
- P09 or later prerequisite workpackages
- Submit-Body posSide probe
- Treating empty orders, fills, algo pending, or history as zero
- Promoting historical or indirect evidence to current state

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_p08_read_only_closure_v1&#47;execute_v1.py` |
| Channel classifiers | `src&#47;ops&#47;section_11_13_5_p08_read_only_closure_v1&#47;classify_v1.py` |
| Query grammar | `src&#47;ops&#47;section_11_13_5_p08_read_only_closure_v1&#47;query_grammar_v1.py` |
| Census | `src&#47;ops&#47;section_11_13_5_p08_read_only_closure_v1&#47;census_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p08_read_only_closure_v1&#47;persist_v1.py` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_p08_read_only_closure_v1/20260903T210317Z/
OWNER_GO_CONSUMED=true
GET_REQUEST_COUNT=6
HTTP_EXCHANGE_COUNT=6
RETRY_COUNT=0
HTTP_STATUS=200
OKX_CODE=0
RESULT_CLASS=HTTP_200_OKX_0
POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO
GET_ROLES_PERFORMED=TARGET_ORDERS_PENDING;TARGET_ORDERS_HISTORY;TARGET_ALGO_PENDING_CONDITIONAL_OCO;TARGET_ALGO_PENDING_TRIGGER;TARGET_ALGO_PENDING_MOVE_ORDER_STOP;TARGET_FILLS
IDENTIFIER_OBSERVATION_CLASS=IDENTIFIER_CHANNEL_EMPTY_NOT_NEVER_HELD_NOT_CURRENT_ZERO
POSID_POSITIONS_GET_PERFORMED=false
TARGET_POS_ID_PROVEN=false
EMPTY_DATA_IS_ZERO=false
ORDERS_EMPTY_IS_NEVER_HELD=false
ORDERS_EMPTY_IS_CURRENT_ZERO=false
FILLS_EMPTY_IS_NEVER_HELD=false
FILLS_EMPTY_IS_CURRENT_ZERO=false
P08_CLOSED=false
P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED
P08_VERDICT=P08_NOT_CLOSED_READ_ONLY_IDENTIFIER_CHANNELS_DO_NOT_PROVE_CURRENT_NONZERO
TARGET_POSITION_ZERO_PROVEN=false
TARGET_POSITION_NONZERO_PROVEN=false
POSITION_STATE_OBSERVED=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
IDENTIFIER_BODY_SHA256=fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a
BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true
```
