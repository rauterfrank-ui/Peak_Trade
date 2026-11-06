# Peak_Trade — POS_MODE Forensic Binding Implementation and Closure v1

status: ACTIVE
last_updated: 2026-08-30
owner: Peak_Trade
purpose: Bind Peak_Trade POS_MODE to the First-Party authenticated account-config GET field posMode, wire the productive consumer, and persist one current production forensic observation. Not a second SSOT. Not restoration reopen. Not live or trading authority. Not MARGIN_MODE, AVAILABLE_MARGIN, ACCOUNT_MODE, or INSTRUMENT_STATE closure. Not set-position-mode. Not a TTL. Not an operative cache. Not posSide. Not acctLv. Not historical BTC reuse. Not a silent rewrite of raw net_mode to net.
docs_token: DOCS_TOKEN_PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_LEVERAGE_FORENSIC_BINDING=docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
EVIDENCE_PACK=evidence/ops/pos_mode_forensic_binding_implementation_and_closure_v1/20260829T233351Z
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
CHANGED_RUNTIME_FILES=pos_mode_observation_v1.py,pos_mode_consumer_v1.py,order_plan_v1.py,submit_transport_v1.py,constants_v1.py
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
SET_POSITION_MODE_EXECUTED=false
POSITION_MODE_MUTATION_PERFORMED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
AUTH_REQUIRED=true
AUTH_HEADER_SENT=true
```

This document is subordinate to the Master Runbook. Historical
`BTC-USD_UM_XPERP-310404` account-config observations remain true as
BTC-era account GETs and remain non-transferable as a current SUI
reobservation. GATE_21 historical `posMode=net` remains classified as
historical internal presentation, not exchange-raw `posMode`. Leverage
`posSide=net` remains a different domain. This persist binds a fresh
authenticated Production GET of `&#47;api&#47;v5&#47;account&#47;config`.

## 1) Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_PLUS_THIS_SUBORDINATE_PERSIST
RAW_OBSERVATION=EVIDENCE_PACK_THIS_SLICE
VALIDATED_FACTS=THIS_DOCUMENT_SECTION_4
ADJUDICATED_CONSUMER_CONTRACT=THIS_DOCUMENT_SECTION_5
HISTORICAL_INTERMEDIATE=GATE21_POSMODE_NET_INTERNAL_PRESENTATION_AND_BTC_ERA_ACCOUNT_CONFIG
NAVIGATION_ONLY=MAP_OF_TRUTH
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=MARGIN_MODE_AND_LATER_REQUIRED_METADATA_EDGES
CONFLICTED=NONE
```

## 2) Owner-GO and current instrument

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_POS_MODE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1
BOUND_ORIGIN_MAIN_SHA=73b8f7e06d12a1e446b5ac0a4289531e35e3642e
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

The account-config GET has no instrument query. Consumer applicability
is the current SUI pretrade path. Venue storage of `posMode` is
account-global, not per-instId.

## 3) Current operative binding

```text
POS_MODE_CANONICAL_DEFINITION=ACCOUNT_POS_MODE
POS_MODE_EDGE_ROLE=CURRENT_ACCOUNT_POSITION_MODE
POS_MODE_ENDPOINT=/api/v5/account/config
POS_MODE_SOURCE_ENDPOINT=/api/v5/account/config
POS_MODE_REQUEST_GRAMMAR=NONE
POS_MODE_RESPONSE_FIELD=posMode
POS_MODE_VENUE_ALLOWED_VALUES=net_mode,long_short_mode
POS_MODE_REQUIRED_VALUE=net_mode
POS_MODE_OUTPUT_DOMAIN=ACCOUNT_POS_MODE
POS_MODE_COMPARISON_DOMAIN=ACCOUNT_POS_MODE
POS_MODE_VENUE_SCOPE=ACCOUNT_GLOBAL
POS_MODE_CONSUMER_SCOPE=CURRENT_SUI_PRETRADE_CONSUMER
POS_MODE_FRESHNESS_POLICY=CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION
POS_MODE_TS_AGE_BOUND=UNBOUND
POS_MODE_NO_TS_FIELD=true
POS_MODE_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET
POS_MODE_FIRST_PARTY_SEMANTICS_CONFIRMED=true
POS_MODE_OBSERVATION_CLASS=SUCCESS_TOKEN
POS_MODE_SEMANTIC_VALUE=NET_POSITION_MODE
ACCTLV_IS_NOT_POS_MODE=true
POSSIDE_NET_IS_NOT_POS_MODE=true
TDMODE_CROSS_IS_NOT_POS_MODE=true
MGNMODE_CROSS_IS_NOT_POS_MODE=true
MAX_POSITIONS_IS_NOT_POS_MODE=true
SINGLE_SELECTED_FUTURE_IS_NOT_POS_MODE=true
ACCOUNT_MODE=UNPROVEN
ACCOUNT_MODE_PROOF_STATUS=UNPROVEN
LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF=false
POS_SIDE_INFERENCE_USED_AS_AUTHORITY=false
HISTORICAL_POS_MODE_REUSED=false
HISTORICAL_BTC_ACCOUNT_CONFIG_REUSED=false
DEFAULT_POS_MODE_USED=false
ZERO_NORMALIZATION_PERFORMED=false
FUTURES_SWAP_SEPARATION_PRESERVED=true
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
SET_POSITION_MODE_EXECUTED=false
POSITION_MODE_MUTATION_PERFORMED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
POS_MODE_HISTORICAL_NORMALIZATION_STATUS=CLASSIFIED_GATE21_POSMODE_NET_IS_INTERNAL_PRESENTATION_NOT_EXCHANGE_RAW
```

Owner answers:

- Q1_SOURCE=`AUTHENTICATED_ACCOUNT_CONFIG` field `posMode`
- Q2_DOMAIN=`ACCOUNT_POS_MODE` raw venue tokens `net_mode` and
  `long_short_mode`; semantic class `NET_POSITION_MODE` is a meaning
  class, not a rewrite of raw `net_mode` to `net`
- Q3_SCOPE=`ACCOUNT_GLOBAL` at the venue; consumer scope remains
  `CURRENT_SUI_PRETRADE_CONSUMER`
- Q4_FRESHNESS=`CONFIGURATION_SCOPED_CURRENT_READ_PER_PRETRADE_DECISION`;
  no invented `ts` TTL; LEVERAGE/PRICE_BAND freshness is not copied
- Q5_REQUEST_GRAMMAR=`NONE`; query string is fail-closed; no POST

First-Party: GET `&#47;api&#47;v5&#47;account&#47;config` is the documented
Read-permission account-configuration surface. The response field
`posMode` is the direct current account position-mode observation.
Documented tokens are `net_mode` and `long_short_mode`. POST
`&#47;api&#47;v5&#47;account&#47;set-position-mode` mutates account configuration
and is not authorized in this slice. Set-position-mode documentation is
semantics/constraint evidence only.

`net` belongs to the `posSide` domain. Do not equate:

- raw `posMode` `net_mode`
- historical/internal `posMode=net`
- raw `posSide` `net`

`acctLv` is a separate account-mode field. It is not POS_MODE proof.
Successful GET of account/config is not ACCOUNT_MODE closure.

First-Party documents no numeric `ts` on this response. No LEVERAGE or
PRICE_BAND age-bound is transferred. Freshness is a configuration-scoped
current read per pretrade decision. A persisted pack is not an operative
cache.

Leverage observation `posSide=net` is supporting consistency evidence
only. It is not authority for current account `posMode`.

## 4) Raw observation (this slice GET)

Filled after the authorized authenticated READ-ONLY GET. The pack is
forensic evidence for this Owner-GO. Later pretrade decisions must
perform their own GET. The pack is not an operative cache.

```text
POS_MODE_OBSERVATION_PERFORMED=true
POS_MODE_GET_PERFORMED=true
POS_MODE_OBSERVATION_AUTHENTICATED=true
POS_MODE_OBSERVATION_ENVIRONMENT=OKX_EEA_PRODUCTION
POS_MODE_GET_TIMESTAMP_UTC=2026-08-29T23:33:51.694980Z
POS_MODE_GET_REQUEST_TIMESTAMP_UTC=2026-08-29T23:33:51.380705Z
POS_MODE_GET_HTTP_STATUS=200
POS_MODE_GET_VENUE_CODE=0
POS_MODE_GET_VENUE_MSG=
POS_MODE_GET_AUTH_CLASS=AUTHENTICATED_PRIVATE_GET
POS_MODE_ENDPOINT_OBSERVED=/api/v5/account/config
POS_MODE_RAW_ROW_COUNT=1
POS_MODE_RAW_VALUE=net_mode
POS_MODE_SEMANTIC_VALUE=NET_POSITION_MODE
POS_MODE_VALIDATED_VALUE=net_mode
POS_MODE_VALIDATED_DOMAIN=ACCOUNT_POS_MODE
ACCT_LV_RAW_CONTEXTUAL=2
ACCT_LV_CANONICALLY_BOUND=false
RESPONSE_BODY_SHA256=cc422bd0667007af7207eb09c8ae5a01b5ccef20ddf48a3a0ef26c4df05d36ae
PRETRADE_DECISION_ID=pos-mode-forensic-binding-sui-20260830T0120Z
SECRET_SOURCE_REFERENCE=secretref://vault/peak-trade/live-canary-minimum-exposure/okx
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
SECRET_MATERIAL_PERSISTED=false
AUTH_REQUIRED=true
AUTH_HEADER_SENT=true
GET_REQUEST_COUNT_PUBLIC=0
GET_REQUEST_COUNT_AUTHENTICATED=1
POST_COUNT=0
SET_POSITION_MODE_EXECUTED=false
POSITION_MODE_MUTATION_PERFORMED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
ZERO_NORMALIZATION_PERFORMED=false
DEFAULT_POS_MODE_USED=false
HISTORICAL_POS_MODE_REUSED=false
LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF=false
POS_SIDE_INFERENCE_USED_AS_AUTHORITY=false
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
HISTORICAL_REUSE_PATH_EXISTS=false
ACCOUNT_MODE=UNPROVEN
```

The observed Production `posMode=net_mode` is the current account
position mode. Parser/consumer verdict is `SUCCESS_TOKEN` with semantic
class `NET_POSITION_MODE`. Raw value is not rewritten to `net`.

`acctLv=2` is persisted as a separate contextual field. It remains
`OBSERVED`, not `CANONICALLY_BOUND`. Other same-GET fields
(`uid`, `perm`, `autoLoan`, `greeksType`, `settleCcy`, `ip`, and the
remainder listed in the pack as `unbound_account_config_fields`) are
likewise observed and not bound by this slice.

Peak_Trade observation class remains `SUCCESS_TOKEN`. Venue-valid
`long_short_mode` fails this consumer because Peak_Trade requires
`net_mode`. Missing, empty, null, unknown, `net` (posSide domain),
HTTP/auth/venue-code failure, empty data, multiple config objects,
query string, historical BTC reuse, leverage-info substitution, and
set-position-mode as source fail closed.

## 5) Consumer contract

```text
POS_MODE_CONSUMER_IDENTIFIED=apply_fresh_pos_mode_pretrade_gate_v1@order_plan_v1.build_minimum_valid_canary_order_plan_v1@submit_transport_v1
POS_MODE_CONSUMER_BOUND=true
POS_MODE_FAIL_CLOSED_BOUND=true
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION=true
POS_MODE_BINDING_STATUS=PROVEN
LEVERAGE_BINDING_STATUS=PROVEN
PRICE_BAND_BINDING_STATUS=PROVEN
MAX_SIZE_BINDING_STATUS=PROVEN
MAX_AVAILABLE_BINDING_STATUS=PROVEN
ORDER_PLAN_TYPED_DOMAIN_PRESERVED=true
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
```

`submit_transport_v1` performs one authenticated GET of
`&#47;api&#47;v5&#47;account&#47;config` after the leverage GET and before
order-plan construction. The order body does not carry `posMode` or
`posSide`. Failure of this GET or of the typed domain gate prevents
downstream POST. Missing GET defaults fail-closed. Persisted evidence
is not reread as an operative cache.

Read-only consumer-contract check after raw `net_mode` was proven.
No additional distinct surface was implemented.

- Order planning: new POS_MODE gate after LEVERAGE; body still omits
  `posMode` and `posSide`. First-Party documents omitting `posSide` as
  valid in net mode.
- posSide construction: unchanged omit-on-net-mode canary contract.
  `posSide=net` is not used as POS_MODE authority.
- Flatten planning: separate emergency authority; not this slice.
- Leverage scoping: still requires unique leverage-info `posSide=net`.
  That uniqueness is not POS_MODE proof.
- max-size / max-avail requests: unchanged.
- Live readiness GATE_21 historical `posMode=net` SATISFIED text remains
  historical internal presentation. Current bind is this §5.3 persist.

## 6) Required edge reassessment

| EDGE_ID | CURRENT_STATUS | Reason |
|---|---|---|
| MAX_SIZE | PROVEN | unchanged |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only canary entry; MARKET max-size gate still bound |
| MAX_AVAILABLE | PROVEN | unchanged |
| PRICE_BAND | PROVEN | unchanged |
| LEVERAGE | PROVEN | unchanged; `posSide=net` on leverage-info is not POS_MODE proof |
| POS_MODE | PROVEN | Owner-adjudicated authenticated `account&#47;config.posMode=net_mode`; consumer bound; `net` not used as raw; no set-position-mode |
| MARGIN_MODE | UNBOUND | `acctLv` and `mgnMode` on other surfaces are not margin-mode proof |
| AVAILABLE_MARGIN | UNBOUND | unchanged |
| INSTRUMENT_STATE | PARTIALLY_BOUND | unchanged |

```text
REQUIRED_METADATA_EDGE_COUNT=8
BOUND_METADATA_EDGE_COUNT=5
PARTIAL_METADATA_EDGE_COUNT=1
PARTIAL_EDGE_IDS=INSTRUMENT_STATE
UNBOUND_METADATA_EDGE_COUNT=2
UNBOUND_EDGE_IDS=MARGIN_MODE,AVAILABLE_MARGIN
ALL_REQUIRED_METADATA_EDGES_BOUND=false
EARLIEST_REMAINING_UNBOUND_EDGE=MARGIN_MODE
EARLIEST_REMAINING_CONFLICT=NONE
EARLIEST_UNRESOLVED_DEPENDENCY=MARGIN_MODE
POS_MODE_BINDING_STATUS=PROVEN
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
ADJUDICATION_RESULT=PARTIAL
NEXT_DISTINCT_SURFACE=MARGIN_MODE
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

## 7) Negative contract

```text
HISTORICAL_BTC_ACCOUNT_CONFIG_IS_NOT_CURRENT_SUI_REOBSERVATION=true
HISTORICAL_POS_MODE_REUSED=false
DEFAULT_POS_MODE_USED=false
POSMODE_NET_IS_NOT_EXCHANGE_RAW=true
POSSIDE_NET_IS_NOT_POS_MODE=true
ACCTLV_IS_NOT_POS_MODE=true
TDMODE_CROSS_IS_NOT_POS_MODE=true
MGNMODE_CROSS_IS_NOT_POS_MODE=true
MAX_POSITIONS_IS_NOT_POS_MODE=true
SINGLE_SELECTED_FUTURE_IS_NOT_POS_MODE=true
LEVERAGE_INFO_IS_NOT_POS_MODE_SOURCE=true
POSITIONS_ARE_NOT_POS_MODE_SOURCE=true
SET_POSITION_MODE_IS_NOT_THIS_SLICE=true
ACCOUNT_MODE_IS_NOT_POS_MODE=true
SUCCESSFUL_GET_IS_NOT_ACCOUNT_MODE_PROOF=true
LONG_SHORT_MODE_IS_VENUE_VALID_AND_PEAK_TRADE_MISMATCH=true
QUERY_STRING_IS_FORBIDDEN=true
ZERO_NORMALIZATION_PERFORMED=false
POLICY_BIND_IS_NOT_TTL=true
PERSISTED_PACK_IS_NOT_OPERATIVE_CACHE=true
TS_AGE_BOUND_NOT_INVENTED=true
LEVERAGE_FAMILY_SCOPE_NOT_TRANSFERRED_TO_POS_MODE=true
SET_POSITION_MODE_EXECUTED=false
POSITION_MODE_MUTATION_PERFORMED=false
ACCOUNT_MODE_MUTATION_PERFORMED=false
POS_SIDE_INFERENCE_USED_AS_AUTHORITY=false
NETWORK_POST_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
FLATTEN_IS_NOT_ENTRY_VENUE_PRETRADE_OWNER=true
SEE_ALSO_LEVERAGE=docs/ops/specs/PEAK_TRADE_LEVERAGE_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md
SEE_ALSO_METADATA_BINDING=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
```
