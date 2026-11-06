# Peak_Trade — MARGIN_MODE Forensic Binding Implementation and Closure v1

status: ACTIVE
last_updated: 2026-08-30
owner: Peak_Trade
purpose: Bind Peak_Trade MARGIN_MODE to the current single-selected-future execution tdMode, wire the productive consumer, and persist one current production forensic positions GET as a conflict check. Not a second SSOT. Not restoration reopen. Not live or trading authority. Not AVAILABLE_MARGIN, ACCOUNT_MODE, POS_MODE, LEVERAGE, or INSTRUMENT_STATE closure. Not a global account Cross/Isolated setting. Not set-isolated-mode. Not a TTL. Not an operative cache. Not acctLv. Not posMode. Empty positions are not a margin mode and are not zero.
docs_token: DOCS_TOKEN_PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_POS_MODE_FORENSIC_BINDING=docs/ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
PRIOR_LEVERAGE_FORENSIC_BINDING=docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
EVIDENCE_PACK=evidence/ops/margin_mode_forensic_binding_implementation_and_closure_v1/20260830T000739Z
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
CANARY_VENUE_CONSTRAINT_PLAN_RUNTIME_MUTATION=true
NEW_SEMANTIC_POLICY=true
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
EXECUTION_ELIGIBLE=false
LIVE_READINESS=EVALUATED_NOT_READY
ORDERS_AUTHORIZED=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
CHANGED_RUNTIME_FILES=margin_mode_observation_v1.py,margin_mode_consumer_v1.py,order_plan_v1.py,submit_transport_v1.py,constants_v1.py
RUNTIME_ALIGNMENT_REQUIRED=true
RUNTIME_MUTATION_JUSTIFIED=true
RUNTIME_MUTATION_PERFORMED=true
NETWORK_GET_AUTHORIZED=true
NETWORK_GET_PERFORMED=true
NETWORK_VENUE_GET_PERFORMED=true
NETWORK_AUTHENTICATED_GET_PERFORMED=true
NETWORK_POST_AUTHORIZED=false
NETWORK_POST_PERFORMED=false
TRADING_PERFORMED=false
MARGIN_MODE_MUTATION_PERFORMED=false
SET_ISOLATED_MODE_EXECUTED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
AUTH_REQUIRED=true
AUTH_HEADER_SENT=true
```

This document is subordinate to the Master Runbook. First-Party OKX has
no global account-level Cross/Isolated setting analogous to `posMode`.
Cross and isolated positions may coexist. Trade margin mode is chosen
per order via `tdMode`. Position rows may carry `mgnMode`. Empty
`data=[]` is not a margin mode. This persist binds a fresh authenticated
Production GET of `&#47;api&#47;v5&#47;account&#47;positions` as a scoped
conflict check for the current selected future. It does not bind a
global `CURRENT_ACCOUNT_MARGIN_MODE`.

## 1) Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_PLUS_THIS_SUBORDINATE_PERSIST
RAW_OBSERVATION=EVIDENCE_PACK_THIS_SLICE
VALIDATED_FACTS=THIS_DOCUMENT_SECTION_4
ADJUDICATED_CONSUMER_CONTRACT=THIS_DOCUMENT_SECTION_5
HISTORICAL_INTERMEDIATE=LEVERAGE_INFO_MGNMODE_CROSS_SUPPORTING_ONLY
NAVIGATION_ONLY=MAP_OF_TRUTH
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=AVAILABLE_MARGIN_AND_LATER_REQUIRED_METADATA_EDGES
CONFLICTED=NONE
TD_MODE_ROLE=ORDER_TRADE_MODE
MGN_MODE_ROLE=POSITION_OR_LEVERAGE_SCOPE
ACCT_LV_ROLE=ACCOUNT_MODE_NOT_MARGIN_MODE
POS_MODE_ROLE=POSITION_MODE_NOT_MARGIN_MODE
```

Do not silently normalize:

- `tdMode` into `mgnMode`
- `mgnMode` into `tdMode`
- `acctLv` into MARGIN_MODE
- `posMode` into MARGIN_MODE
- empty positions into `cross` or `isolated`

## 2) Owner-GO and current instrument

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_MARGIN_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1
BOUND_ORIGIN_MAIN_SHA=80f621a2c4eeb531b56aafe861273b6ca05850f4
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
CURRENT_REST_HOST=eea.okx.com
CURRENT_INST_TYPE=FUTURES
CURRENT_INST_FAMILY=SUI-USD_UM_XPERP
CURRENT_RULE_TYPE=xperp
CANARY_ENTRY_ORDER_TYPE=LIMIT
CANARY_ENTRY_SIDE=BUY
INST_FAMILY_PARSED_FROM_INSTID=false
```

The positions GET is unfiltered. Query grammar is none. Consumer
applicability is the current SUI pretrade path. Other-instrument
`mgnMode` rows are contextual and are not this edge's authority.

## 3) Current operative binding

```text
MARGIN_MODE_CANONICAL_DEFINITION=CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION_TDMODE
MARGIN_MODE_EDGE_ROLE=CROSS_OR_ISOLATED_COMPATIBILITY
MARGIN_MODE_REQUIRED_EDGE_SEMANTICS=ACCOUNT_OR_ORDER_TDMODE_MARGIN_MODE
MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS=false
MARGIN_MODE_BINDING_SCOPE=CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION
MARGIN_MODE_ENDPOINT=/api/v5/account/positions
MARGIN_MODE_SOURCE_ENDPOINT=/api/v5/account/positions
MARGIN_MODE_REQUEST_GRAMMAR=NONE
MARGIN_MODE_POSITION_RESPONSE_FIELD=mgnMode
MARGIN_MODE_ORDER_FIELD=tdMode
MARGIN_MODE_VENUE_ALLOWED_VALUES=cross,isolated
MARGIN_MODE_REQUIRED_ORDER_TD_MODE=cross
MARGIN_MODE_OUTPUT_DOMAIN=ORDER_TDMODE
MARGIN_MODE_COMPARISON_DOMAIN=ORDER_TDMODE
MARGIN_MODE_VENUE_SCOPE=CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION
MARGIN_MODE_CONSUMER_SCOPE=CURRENT_SUI_PRETRADE_CONSUMER
MARGIN_MODE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION
MARGIN_MODE_TS_AGE_BOUND=UNBOUND
MARGIN_MODE_NO_TS_FIELD=true
MARGIN_MODE_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET
MARGIN_MODE_FIRST_PARTY_SEMANTICS_CONFIRMED=true
MARGIN_MODE_OBSERVATION_CLASS=SUCCESS_NOT_OBSERVED
MARGIN_MODE_SEMANTIC_VALUE=CURRENT_SINGLE_SELECTED_FUTURE_ORDER_TDMODE_CROSS
ORDER_PLAN_TD_MODE=cross
MAX_SIZE_TD_MODE=NOT_APPLICABLE_PUBLIC_INSTRUMENTS_MAXLMTSZ
MAX_AVAILABLE_TD_MODE=cross
FLATTEN_TD_MODE=cross
EXECUTION_TD_MODE=cross
PLANNING_EXECUTION_TD_MODE_CONSISTENT=true
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
ACCTLV_IS_NOT_MARGIN_MODE=true
POSMODE_IS_NOT_MARGIN_MODE=true
CTISOMODE_IS_NOT_MARGIN_MODE=true
MGNISOMODE_IS_NOT_MARGIN_MODE=true
LEVERAGE_MGNMODE_IS_NOT_MARGIN_MODE_AUTHORITY=true
EMPTY_DATA_IS_NOT_ZERO=true
ABSENT_OR_NOT_RETURNED_IS_NOT_ZERO=true
EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY=false
POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY=false
LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCOUNT_MODE=UNPROVEN
ACCOUNT_MODE_PROOF_STATUS=UNPROVEN
DEFAULT_TD_MODE_USED_AS_GLOBAL_ACCOUNT_CLAIM=false
ZERO_NORMALIZATION_PERFORMED=false
FUTURES_SWAP_SEPARATION_PRESERVED=true
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
MARGIN_MODE_MUTATION_PERFORMED=false
SET_ISOLATED_MODE_EXECUTED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
```

Owner answers:

- Q1_SOURCE=`ORDER_TDMODE` from the canonical selected-future order
  plan / execution request, required token `cross`; positions GET is
  a scoped conflict check, not a global mode source
- Q2_DOMAIN=`ORDER_TDMODE`; venue tokens `cross` and `isolated`;
  semantic class `CURRENT_SINGLE_SELECTED_FUTURE_ORDER_TDMODE_CROSS`
  is a scoped meaning class, not a rewrite of empty positions to
  `cross`
- Q3_SCOPE=`CURRENT_SINGLE_SELECTED_FUTURE_EXECUTION`; not
  `ACCOUNT_GLOBAL`
- Q4_FRESHNESS=`FRESH_GET_PER_PRETRADE_DECISION`; no invented `ts`
  TTL; LEVERAGE/PRICE_BAND/POS_MODE freshness is not copied
- Q5_REQUEST_GRAMMAR=`NONE`; query string is fail-closed; no POST

First-Party: OKX does not expose a global account Cross/Isolated
setting comparable to `posMode` on `GET &#47;api&#47;v5&#47;account&#47;config`.
`acctLv` is account mode. `posMode` is position mode. Trade mode is
`tdMode` on the order. Position `mgnMode` is observed only when a
row for the current instrument is present. POST
`&#47;api&#47;v5&#47;account&#47;set-isolated-mode` mutates isolated-margin
transfer settings and is not authorized in this slice.

Do not equate:

- order `tdMode` `cross`
- position `mgnMode` `cross`
- leverage-info request/row `mgnMode` `cross`
- empty positions
- `acctLv`
- `posMode`

`GET &#47;api&#47;v5&#47;account&#47;leverage-info` `mgnMode=cross` for the
canonical SUI future remains supporting current runtime evidence
(`CURRENT_LEVERAGE_SCOPE_MARGIN_MODE_EVIDENCE`). It is not authority
for `ALL_FUTURE_ORDERS_USE_CROSS`.

Bound MAX_SIZE remains public instruments `maxLmtSz` and does not
carry `tdMode`. Bound MAX_AVAILABLE remains authenticated
`GET &#47;api&#47;v5&#47;account&#47;max-size` and must use the same `tdMode`
as later execution. Flatten planning defaults to the same required
`cross` token. Isolated can be produced if config sets
`td_mode=isolated`; the gate fails closed.

## 4) Raw observation (this slice GET)

Filled after the authorized authenticated READ-ONLY GET. The pack is
forensic evidence for this Owner-GO. Later pretrade decisions must
perform their own GET. The pack is not an operative cache.

```text
MARGIN_MODE_OBSERVATION_PERFORMED=true
MARGIN_MODE_GET_PERFORMED=true
MARGIN_MODE_OBSERVATION_AUTHENTICATED=true
MARGIN_MODE_OBSERVATION_ENVIRONMENT=OKX_EEA_PRODUCTION
MARGIN_MODE_GET_TIMESTAMP_UTC=2026-08-30T00:07:39.347441Z
MARGIN_MODE_GET_REQUEST_TIMESTAMP_UTC=2026-08-30T00:07:39.117426Z
MARGIN_MODE_GET_HTTP_STATUS=200
MARGIN_MODE_GET_VENUE_CODE=0
MARGIN_MODE_GET_VENUE_MSG=
MARGIN_MODE_GET_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET
MARGIN_MODE_ENDPOINT_OBSERVED=/api/v5/account/positions
MARGIN_MODE_RAW_ROW_COUNT=0
MARGIN_MODE_TARGET_ROW_COUNT=0
POSITION_MGN_MODE_OBSERVED=NOT_OBSERVED
POSITION_MGN_MODE_RAW=NOT_OBSERVED
POSITION_MGN_MODE_STATUS=NOT_OBSERVED
MARGIN_MODE_RAW_VALUE=NOT_OBSERVED
MARGIN_MODE_SEMANTIC_VALUE=CURRENT_SINGLE_SELECTED_FUTURE_ORDER_TDMODE_CROSS
MARGIN_MODE_VALIDATED_DOMAIN=ORDER_TDMODE
LEVERAGE_INFO_MGN_MODE_OBSERVED=cross
LEVERAGE_INFO_MGN_MODE_ROLE=SUPPORTING_CURRENT_LEVERAGE_SCOPE_ONLY
RESPONSE_BODY_SHA256=fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a
PRETRADE_DECISION_ID=margin-mode-forensic-binding-sui-20260830T0155Z
SECRET_SOURCE_REFERENCE=secretref://vault/peak-trade/live-canary-minimum-exposure/okx
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
SECRET_MATERIAL_PERSISTED=false
AUTH_REQUIRED=true
AUTH_HEADER_SENT=true
GET_REQUEST_COUNT_PUBLIC=0
GET_REQUEST_COUNT_AUTHENTICATED=1
POST_COUNT=0
MARGIN_MODE_MUTATION_PERFORMED=false
SET_ISOLATED_MODE_EXECUTED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
ZERO_NORMALIZATION_PERFORMED=false
EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY=false
POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY=false
LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY=false
HISTORICAL_MARGIN_MODE_REUSED=false
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
HISTORICAL_REUSE_PATH_EXISTS=false
ACCOUNT_MODE=UNPROVEN
```

The observed Production positions payload is `data=[]`. Peak_Trade
observation class is `SUCCESS_NOT_OBSERVED`. Empty data is not
normalized to `cross` or `isolated` and is not used as MARGIN_MODE
authority. No current SUI row with `mgnMode=isolated` was observed.
No other-instrument `mgnMode` was observed on this GET.

Parser/consumer verdict remains scoped to
`CURRENT_SINGLE_SELECTED_FUTURE_ORDER_TDMODE_CROSS`. Venue-valid
`isolated` planned `tdMode` fails this consumer because Peak_Trade
requires order `tdMode=cross`. Observed target-row `mgnMode` that
disagrees with planned `tdMode` is a scoped conflict and fails
closed. Missing GET, HTTP/auth/venue-code failure, query string,
account/config substitution, leverage-info substitution, historical
BTC reuse, empty-as-zero, and set-isolated-mode as source fail
closed.

## 5) Consumer contract

```text
MARGIN_MODE_CONSUMER_IDENTIFIED=apply_fresh_margin_mode_pretrade_gate_v1@order_plan_v1.build_minimum_valid_canary_order_plan_v1@submit_transport_v1
MARGIN_MODE_CONSUMER_BOUND=true
MARGIN_MODE_FAIL_CLOSED_BOUND=true
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION=true
MARGIN_MODE_BINDING_STATUS=PROVEN
POS_MODE_BINDING_STATUS=PROVEN
LEVERAGE_BINDING_STATUS=PROVEN
PRICE_BAND_BINDING_STATUS=PROVEN
MAX_SIZE_BINDING_STATUS=PROVEN
MAX_AVAILABLE_BINDING_STATUS=PROVEN
ORDER_PLAN_TYPED_DOMAIN_PRESERVED=true
PLANNING_EXECUTION_TD_MODE_CONSISTENT=true
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
```

`submit_transport_v1` reads `cfg.payload.td_mode` (canonical default
`cross`) and fail-closes before the max-available GET unless the
token is the required `cross`. The same `td_mode` is passed to
`GET &#47;api&#47;v5&#47;account&#47;max-size`, the order plan, and the
venue-native order body `tdMode`. One unfiltered authenticated GET
of `&#47;api&#47;v5&#47;account&#47;positions` is performed after the
POS_MODE GET and before order-plan construction. The same payload is
reused later for pre-submit / open-position cap. Failure of this GET
or of the typed domain gate prevents downstream POST. Missing GET
defaults fail-closed. Persisted evidence is not reread as an
operative cache.

Flatten planning is separate emergency authority. Its builder now
requires the same canonical execution `tdMode=cross`. Isolated
flatten `tdMode` fails closed.

Read-only consumer-contract check after scoped `tdMode=cross` was
proven. No additional distinct surface was implemented.

- Order planning: new MARGIN_MODE gate after POS_MODE; body carries
  `tdMode=cross`.
- max-size: public instruments `maxLmtSz`; `tdMode` not applicable.
- max-avail: authenticated `account&#47;max-size` with the same
  `tdMode=cross`.
- Flatten planning: same required `cross`; not this slice's execute
  authority.
- Leverage scoping: still requires unique leverage-info
  `mgnMode=cross`. That uniqueness is not MARGIN_MODE authority.
- Isolated: can be configured; gate fails closed.
- Live / Testnet / Canary authorization remain false.

## 6) Required edge reassessment

| EDGE_ID | CURRENT_STATUS | Reason |
|---|---|---|
| MAX_SIZE | PROVEN | unchanged |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only canary entry; MARKET max-size gate still bound |
| MAX_AVAILABLE | PROVEN | unchanged; planning `tdMode` matches execution `tdMode` |
| PRICE_BAND | PROVEN | unchanged |
| LEVERAGE | PROVEN | unchanged; leverage-info `mgnMode=cross` is not MARGIN_MODE authority |
| POS_MODE | PROVEN | unchanged; `posMode` is not MARGIN_MODE |
| MARGIN_MODE | PROVEN | Owner-adjudicated current-future execution `tdMode=cross`; planning/execution consistent; positions GET `NOT_OBSERVED` not used as authority; no scoped isolated conflict |
| AVAILABLE_MARGIN | UNBOUND | unchanged |
| INSTRUMENT_STATE | PARTIALLY_BOUND | unchanged |

```text
REQUIRED_METADATA_EDGE_COUNT=8
BOUND_METADATA_EDGE_COUNT=6
PARTIAL_METADATA_EDGE_COUNT=1
PARTIAL_EDGE_IDS=INSTRUMENT_STATE
UNBOUND_METADATA_EDGE_COUNT=1
UNBOUND_EDGE_IDS=AVAILABLE_MARGIN
ALL_REQUIRED_METADATA_EDGES_BOUND=false
EARLIEST_REMAINING_UNBOUND_EDGE=AVAILABLE_MARGIN
EARLIEST_REMAINING_CONFLICT=NONE
EARLIEST_UNRESOLVED_DEPENDENCY=AVAILABLE_MARGIN
MARGIN_MODE_BINDING_STATUS=PROVEN
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
ADJUDICATION_RESULT=PARTIAL
NEXT_DISTINCT_SURFACE=AVAILABLE_MARGIN
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

## 7) Negative contract

```text
MARGIN_MODE_GLOBAL_ACCOUNT_SETTING_EXISTS=false
ACCOUNT_CONFIG_IS_NOT_MARGIN_MODE_SOURCE=true
ACCTLV_IS_NOT_MARGIN_MODE=true
POSMODE_IS_NOT_MARGIN_MODE=true
CTISOMODE_IS_NOT_MARGIN_MODE=true
MGNISOMODE_IS_NOT_MARGIN_MODE=true
LEVERAGE_INFO_IS_NOT_MARGIN_MODE_AUTHORITY=true
EMPTY_POSITIONS_ARE_NOT_CROSS=true
EMPTY_POSITIONS_ARE_NOT_ISOLATED=true
EMPTY_POSITIONS_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCOUNT_CONFIG_USED_AS_MARGIN_MODE_AUTHORITY=false
ACCT_LV_USED_AS_MARGIN_MODE_AUTHORITY=false
POS_MODE_USED_AS_MARGIN_MODE_AUTHORITY=false
LEVERAGE_USED_AS_MARGIN_MODE_AUTHORITY=false
DEFAULT_TDMODE_CROSS_IS_NOT_ACCOUNT_MODE_PROOF=true
ALL_FUTURE_ORDERS_USE_CROSS_NOT_CLAIMED_FROM_LEVERAGE=true
QUERY_STRING_IS_FORBIDDEN=true
ZERO_NORMALIZATION_PERFORMED=false
POLICY_BIND_IS_NOT_TTL=true
PERSISTED_PACK_IS_NOT_OPERATIVE_CACHE=true
TS_AGE_BOUND_NOT_INVENTED=true
SET_ISOLATED_MODE_IS_NOT_THIS_SLICE=true
ACCOUNT_MODE_IS_NOT_MARGIN_MODE=true
SUCCESSFUL_GET_IS_NOT_ACCOUNT_MODE_PROOF=true
ISOLATED_TDMODE_IS_VENUE_VALID_AND_PEAK_TRADE_MISMATCH=true
SCOPED_POSITION_ISOLATED_VS_ORDER_CROSS_IS_CONFLICT=true
MARGIN_MODE_MUTATION_PERFORMED=false
SET_ISOLATED_MODE_EXECUTED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
NETWORK_POST_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
FLATTEN_IS_NOT_ENTRY_VENUE_PRETRADE_OWNER=true
SEE_ALSO_POS_MODE=docs/ops/specs/PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
SEE_ALSO_LEVERAGE=docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
SEE_ALSO_METADATA_BINDING=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
```
