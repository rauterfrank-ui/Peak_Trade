# Peak_Trade — MAX_SIZE Freshness Owner Policy Decision v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Persist the explicit Owner-policy for operative freshness of OKX EEA public-instruments maxLmtSz and maxMktSz after closed typed venue-contract-count domain closure. Not a second SSOT. Not restoration reopen. Not runtime mutation. Not live or execution authority. Not a venue GET. Not a consumer bind. Not venue-pretrade completeness. Not a TTL. Not an event-cache. Not indefinite reuse.
docs_token: DOCS_TOKEN_PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_MASTER_RUNBOOK_SECTION_5_3
CANONICAL_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
PARENT_CONTRACT=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_BASELINE_PRESERVATION_AND_COMPATIBILITY_CONTRACT_V1.md
PRIOR_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE=docs/ops/specs/PEAK_TRADE_ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1.md
PRIOR_MAX_SIZE_NORMALIZATION_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1.md
PRIOR_MAX_SIZE_UNIT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1.md
PRIOR_EXACT_VENUE_METADATA_GET=docs/ops/specs/PEAK_TRADE_EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1.md
PRIOR_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_V1.md
PRIOR_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION=docs/ops/specs/PEAK_TRADE_POST_RESTORATION_VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_V1.md
EVIDENCE_PACK=evidence/ops/exact_venue_metadata_get_current_sui_pretrade_max_size_v1/20260829T182239Z
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_RUNTIME_MUTATION=false
DEFAULT_RUNTIME_MUTATION=false
CANARY_VENUE_CONSTRAINT_PLAN_RUNTIME_MUTATION=false
NEW_SEMANTIC_POLICY=true
NEW_RUNTIME_OWNER=false
NEW_STAGE=false
NEW_VENUE_PRETRADE_COMPONENT_REQUIRED=false
NEW_ABSTRACTION_REQUIRED=false
RESTORATION_REOPEN_REQUIRED=false
MASTER_V2_DOUBLE_PLAY_RESTORATION_COMPLETE=true
COMPATIBILITY_CONTRACT_DOES_NOT_GRANT_EXECUTION_AUTHORITY=true
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
CHANGED_RUNTIME_FILES=NONE
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
RUNTIME_MUTATION_PERFORMED=false
NETWORK_GET_AUTHORIZED=false
NETWORK_GET_PERFORMED=false
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_POST_AUTHORIZED=false
NETWORK_POST_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=false
AUTH_REQUIRED=false
AUTH_HEADER_SENT=false
```

This document is subordinate to the Master Runbook and to the post-restoration
preservation contract. It does not replace Master §5.3, Appendix A, C4, Replay
Safety, Cap 7.2, live-safety #6145, simulated-execution #6144,
accounting/portfolio #6143, venue-pretrade limit-gates #6146,
metadata-binding alignment #6147, exact venue metadata GET #6148,
MAX_SIZE unit adjudication #6149, MAX_SIZE normalization
adjudication #6150, or typed contract-count domain closure #6151.
#6151 remains the closed historical persist that
`MAX_SIZE_FRESHNESS_POLICY=UNBOUND`. This slice does **not** reverse
that historical finding. It binds the explicit Owner freshness policy
for later operative pretrade decisions.

## 1) Restoration and predecessor boundary

```text
RESTORATION_COMPLETION_CHECKPOINT_SHA=21452016ff998c1af63f24c36060f2a54020c0df
HISTORICAL_MASTER_V2_DOUBLE_PLAY_BASELINE=IMMUTABLE_NORMATIVE_BASELINE
CURRENT_SYSTEM_MUST_CONFORM_TO_HISTORICAL_CORE=true
NO_CURRENT_FIRST_ARCHITECTURE=true
P0_QUARANTINE_REMAINS_CLOSED=true
ACCOUNTING_PORTFOLIO_ALIGNMENT_REMAINS_CLOSED=true
SIMULATED_EXECUTION_PIPELINE_REMAINS_CLOSED=true
LIVE_SAFETY_GATES_REMAIN_CLOSED=true
VENUE_PRETRADE_LIMIT_GATES_ADJUDICATION_REMAINS_CLOSED=true
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_ADJUDICATION_REMAINS_CLOSED=true
EXACT_VENUE_METADATA_GET_CURRENT_SUI_PRETRADE_MAX_SIZE_V1_REMAINS_CLOSED=true
POST_6148_MAX_SIZE_UNIT_ADJUDICATION_V1_REMAINS_CLOSED=true
POST_6149_MAX_SIZE_NORMALIZATION_ADJUDICATION_V1_REMAINS_CLOSED=true
ORDER_PLAN_TYPED_CONTRACT_COUNT_DOMAIN_CLOSURE_V1_REMAINS_CLOSED=true
HISTORICAL_6148_NETWORK_GET_PERFORMED=true
HISTORICAL_6148_MAX_SIZE_UNIT=UNBOUND
HISTORICAL_6151_MAX_SIZE_FRESHNESS_POLICY=UNBOUND
HISTORICAL_6151_MAX_SIZE_NORMALIZATION_STATUS=BOUND
HISTORICAL_6151_NETWORK_VENUE_GET_PERFORMED=false
```

#6151 remains the closed typed-domain persist that left freshness
policy UNBOUND. This slice consumes the separate Owner-GO for freshness
policy only. It does not rewrite the #6148 GET observation and does not
make that historical window operatively reusable.

## 2) Protected productive owner graph

```text
CANONICAL_VENUE_PRETRADE_OWNER=section_11_13_5.order_plan_v1+exposure_v1@submit_transport_v1
VENUE_PRETRADE_OWNER_MODEL=OKX_EEA_CANARY_VENUE_CONSTRAINT_PLAN_OWNER_NOT_A_SECOND_CORE_RISK_OR_SAFETY_OWNER
SECOND_VENUE_PRETRADE_OWNER_EXISTS=false
SECOND_OWNER_REQUIRED=false
SECOND_COMPUTE_OWNER_EXISTS=false
SECOND_RISK_OWNER_EXISTS=false
SECOND_SAFETY_OWNER_EXISTS=false
SECOND_INTENT_OWNER_EXISTS=false
SECOND_EXECUTION_OWNER_EXISTS=false
CLOSED_OWNER_GRAPH_PRESERVED=true
FUTURE_MAX_SIZE_CONSUMER_LOCATION=extract_instrument_constraints_v1@submit_transport_v1_instruments_payload
FUTURE_MAX_SIZE_CONSUMER_CURRENTLY_BOUND=false
MAX_SIZE_CONSUMER_BOUND=false
MAX_SIZE_CONSUMER_CAN_NOW_BE_BOUND=true
VENUE_PRETRADE_IS_NOT_REPLAY_SAFETY=true
VENUE_PRETRADE_IS_NOT_CORE_RISK_AUTHORITY=true
VENUE_PRETRADE_IS_NOT_EXECUTION_AUTHORITY=true
KRAKEN_CURRENT_CANONICAL_ROLE=NONE
KRAKEN_METADATA_REUSED=false
KRAKEN_EVIDENCE_USED_FOR_CURRENT_OKX_PRETRADE=false
KRAKEN_EXCLUSION_CLOSED=true
```

## 3) Epistemic class separation

```text
CURRENT_RAW_EVIDENCE=PR_6148_PUBLIC_INSTRUMENTS_GET_WINDOW_20260829T182239Z
OFFICIAL_DEFINITIONAL_AUTHORITY=REUSED_FROM_POST_6148_MAX_SIZE_UNIT_ADJUDICATION_NO_NEW_DOC_FETCH
CANONICAL_AUTHORITY=MASTER_RUNBOOK_PLUS_THIS_SUBORDINATE_PERSIST
HISTORICAL_RAW_EVIDENCE=Z2AR_GET_1_AND_Z2BD_Z2BF_BODY_PARITY
ADJUDICATED_CONCLUSION=THIS_DOCUMENT
NAVIGATION_ONLY=MAP_OF_TRUTH
INTERPRETATION=NONE_USED_AS_FRESHNESS_POLICY
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING
CONFLICTED=NONE
```

Authority for the freshness rule is this Owner-ratified policy.
Authority for the historical raw numbers remains #6148. Authority for
unit remains #6149. Authority for comparison domain remains #6151.
This policy does **not** refresh, reuse, or freeze those numbers.

## 4) Current instrument and reused evidence (not re-observed)

```text
OWNER_GO_THIS_SLICE=PEAK_TRADE_MAX_SIZE_FRESHNESS_OWNER_POLICY_DECISION_V1
BOUND_ORIGIN_MAIN_SHA=ae302d2b4c0425c4d42ece494d1b5996a9e54243
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
CURRENT_REST_HOST=eea.okx.com
CURRENT_INST_TYPE=FUTURES
CURRENT_RULE_TYPE=xperp
CURRENT_MAXLMTSZ_FIELD=maxLmtSz
CURRENT_MAXLMTSZ_RAW_VALUE=100000000
CURRENT_MAXMKTSZ_FIELD=maxMktSz
CURRENT_MAXMKTSZ_RAW_VALUE=100000
MAX_SIZE_UNIT_STATUS=BOUND
MAX_SIZE_UNIT=contracts
MAX_SIZE_NORMALIZATION_STATUS=BOUND
MAX_SIZE_COMPARISON_DOMAIN=venue_contract_count
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=false
Z2AR_WINDOW_REUSED_AS_CURRENT=false
Z2BD_WINDOW_REUSED=false
Z2BF_WINDOW_REUSED=false
```

The #6148 pack remains historical evidence. This slice does not
re-GET it, does not treat it as an operative cache, and does not
assert that those values remain valid for a later pretrade decision.

## 5) Policy options adjudicated

Exactly two Owner-policy options were in scope. No third option was
invented.

```text
OPTION_A=FRESH_GET_PER_PRETRADE_DECISION
OPTION_B=FAIL_CLOSED_NO_OPERATIVE_REUSE_UNTIL_SEPARATELY_AUTHORIZED
OPTION_COUNT=2
THIRD_OPTION_INVENTED=false
FIXED_TTL_OPTION_CONSIDERED=false
INDEFINITE_REUSE_OPTION_CONSIDERED=false
EVENT_INVALIDATED_CACHE_OPTION_CONSIDERED=false
```

### 5.1 Option A — FRESH_GET_PER_PRETRADE_DECISION

Each later operative pretrade decision must obtain `maxLmtSz` and
`maxMktSz` from a venue observation authorized for **that** decision.
A persisted historical window is not an operative cache. Missing or
frustrated freshness evidence fails closed. The policy itself does not
authorize the GET, the network session, or trading.

### 5.2 Option B — FAIL_CLOSED_NO_OPERATIVE_REUSE_UNTIL_SEPARATELY_AUTHORIZED

Refuse operative reuse of the historical window, and leave the
positive freshness rule to a later Owner-GO. This would keep the
MAX_SIZE chain blocked on an unbound freshness policy even after
unit and normalization are bound. It is a deferral, not an operative
freshness rule.

### 5.3 Rejected non-options

```text
FIXED_TTL_DEFINED=false
FIXED_TTL_REJECTED=true
INDEFINITE_REUSE_REJECTED=true
EVENT_INVALIDATED_CACHE_DEFINED=false
EVENT_INVALIDATED_CACHE_REJECTED=true
EVENT_CACHE_REQUIRES_AUTHORITATIVE_COHERENCE_SEMANTICS=true
AUTHORITATIVE_EVENT_COHERENCE_SEMANTICS_PROVEN=false
WEBSOCKET_COHERENCE_CONTRACT_ASSERTED=false
PERMANENT_CACHE_ASSERTED=false
```

No time-to-live was invented. No indefinite reuse was allowed. No
WebSocket or event-invalidated cache was derived, because complete
authoritative coherence semantics are not proven.

## 6) Chosen Owner policy

```text
MAX_SIZE_FRESHNESS_POLICY_STATUS=BOUND
MAX_SIZE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION
CHOSEN_OPTION=A
REJECTED_OPTION=B
REJECTED_OPTION_VALUE=FAIL_CLOSED_NO_OPERATIVE_REUSE_UNTIL_SEPARATELY_AUTHORIZED
MAX_SIZE_FRESHNESS_STATUS=POLICY_BOUND_HISTORICAL_WINDOW_NOT_OPERATIVE
HISTORICAL_MAX_SIZE_REUSE_ALLOWED=false
PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false
FIXED_TTL_DEFINED=false
EVENT_INVALIDATED_CACHE_DEFINED=false
FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION=true
FAIL_CLOSED_ON_FRUSTRATED_FRESHNESS_EVIDENCE=true
THIS_POLICY_AUTHORIZES_VENUE_GET=false
THIS_POLICY_AUTHORIZES_NETWORK_SESSION=false
THIS_POLICY_AUTHORIZES_TRADING=false
NETWORK_ACCESS_REMAINS_SEPARATE_OWNER_GO=true
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
```

Semantic binding:

- `maxLmtSz` and `maxMktSz` MUST NOT be operatively reused from a
  historical or persisted observation window.
- Every later operative pretrade decision MUST take its max-size
  values from a fresh venue observation authorized for exactly that
  decision.
- No time-TTL is asserted.
- No permanent cache is asserted.
- No WebSocket or event-coherence contract is asserted.
- Missing or frustrated freshness evidence MUST fail closed.
- This policy does not itself authorize a venue GET or trading.

## 7) Historical window is not made fresh

```text
CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false
CURRENT_REUSABLE_MAXMKTSZ_PROVEN=false
HISTORICAL_6148_WINDOW_REMAINS_NON_OPERATIVE=true
POLICY_BIND_DOES_NOT_REFRESH_HISTORICAL_VALUES=true
POLICY_BIND_DOES_NOT_FREEZE_CURRENT_NUMERIC=true
CURRENT_MAXLMTSZ_RAW_VALUE=100000000
CURRENT_MAXMKTSZ_RAW_VALUE=100000
```

The #6148 observation remains a historical raw window.
`CURRENT_REUSABLE_MAXLMTSZ_PROVEN` and
`CURRENT_REUSABLE_MAXMKTSZ_PROVEN` stay false. Binding the policy
does not make old values fresh.

## 8) Consumer firewall

```text
MAX_SIZE_CONSUMER_BOUND=false
MAX_SIZE_CONSUMER_CAN_NOW_BE_BOUND=true
EXISTING_EXTRACTOR_REQUIRED_TUPLE=minSz,lotSz,tickSz,ctVal
EXISTING_EXTRACTOR_DOES_NOT_READ_MAXLMTSZ=true
RUNTIME_ALIGNMENT_REQUIRED=false
RUNTIME_MUTATION_JUSTIFIED=false
RUNTIME_MUTATION_PERFORMED=false
CHANGED_RUNTIME_FILES=NONE
CONSUMER_WIRING_AUTHORIZED=false
```

Unit, normalization, comparison domain, and now freshness policy are
bound. A later consumer may be bound under a separate Owner-GO. This
slice does not implement that consumer and does not read `maxLmtSz`
or `maxMktSz` in runtime.

## 9) Required edge reassessment

Status vocabulary is exactly `PROVEN`, `PARTIALLY_BOUND`, `UNBOUND`,
`CONFLICTED`, `NOT_REQUIRED`.

| EDGE_ID | CURRENT_STATUS | Reason after this freshness-policy bind |
|---|---|---|
| MAX_SIZE | PARTIALLY_BOUND | Current raw `maxLmtSz=100000000` historically observed; unit `contracts`; quantity domain `VENUE_CONTRACT_COUNT`; comparison domain bound; freshness policy now `FRESH_GET_PER_PRETRADE_DECISION`; historical window not operatively reusable; consumer remains unbound |
| MAX_MKT_SZ | NOT_REQUIRED | LIMIT-only entry; peer unit `contracts`; same freshness policy applies to `maxMktSz` when MARKET is later in scope; still not a substitute for `maxLmtSz` |
| MAX_AVAILABLE | UNBOUND | `maxAvailSize` MISSING on instruments row; official max-avail surface is authenticated account GET |
| PRICE_BAND | UNBOUND | Raw price-limit percent fields observed; field-to-gate semantic proof and consumer unbound |
| LEVERAGE | UNBOUND | Raw instrument `lever=20` observed; not an account leverage gate |
| POS_MODE | UNBOUND | Not supplied by the public instruments GET |
| MARGIN_MODE | UNBOUND | Not supplied by the public instruments GET |
| AVAILABLE_MARGIN | UNBOUND | Not supplied by the public instruments GET |
| INSTRUMENT_STATE | PARTIALLY_BOUND | Current raw `state=live` observed; consumer and freshness policy for this edge remain independently unbound |

```text
REQUIRED_METADATA_EDGE_COUNT=8
REQUIRED_EDGE_IDS=MAX_SIZE,MAX_AVAILABLE,PRICE_BAND,LEVERAGE,POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN,INSTRUMENT_STATE
BOUND_METADATA_EDGE_COUNT=0
PARTIAL_METADATA_EDGE_COUNT=2
PARTIAL_EDGE_IDS=MAX_SIZE,INSTRUMENT_STATE
UNBOUND_METADATA_EDGE_COUNT=6
UNBOUND_EDGE_IDS=MAX_AVAILABLE,PRICE_BAND,LEVERAGE,POS_MODE,MARGIN_MODE,AVAILABLE_MARGIN
CONFLICTED_METADATA_EDGE_COUNT=0
NOT_REQUIRED_PEER_EDGE_IDS=MAX_MKT_SZ
ALL_REQUIRED_METADATA_EDGES_BOUND=false
EARLIEST_REMAINING_UNBOUND_EDGE=MAX_SIZE
EARLIEST_REMAINING_CONFLICT=NONE
EARLIEST_REMAINING_MAX_SIZE_GAP=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING
REMAINING_MAX_SIZE_SUBDEPENDENCIES=MAX_SIZE_FRESH_OBSERVATION,MAX_SIZE_CONSUMER
BEGINNING_AT=MAX_SIZE
EARLIEST_UNRESOLVED_DEPENDENCY=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING
```

`MAX_SIZE` remains earliest because `PARTIALLY_BOUND` is not `PROVEN`.
Freshness **policy** is closed. The remaining MAX_SIZE subdependency is
a separately authorized fresh observation plus consumer wiring. This
slice does **not** jump to MAX_AVAILABLE or any later required edge,
and does **not** authorize that fresh GET.

## 10) Adjudication result

```text
ADJUDICATION_RESULT=PARTIAL
SOURCE_ADJUDICATION_RESULT=MAX_SIZE_FRESHNESS_POLICY_BOUND_FRESH_GET_PER_PRETRADE_DECISION_HISTORICAL_WINDOW_NOT_OPERATIVE_CONSUMER_UNBOUND
VENUE_PRETRADE_METADATA_BINDING_ALIGNMENT_STATUS=PARTIAL
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
MAX_SIZE_BINDING_STATUS=PARTIALLY_BOUND
CURRENT_SELECTED_INSTRUMENT=SUI-USD_UM_XPERP-310404
CURRENT_VENUE=OKX_EEA
NEXT_DISTINCT_SURFACE=MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING
NEXT_DISTINCT_SURFACE_AUTHORIZED=false
```

Not `COMPLETE`. Not `BLOCKED_BY_MISSING_SOURCE`. Not
`BLOCKED_BY_CONFLICT`. The Owner policy is bound. Consumer and a
fresh operative observation remain later work.

## 11) Negative / non-equivalence contracts

```text
POLICY_BIND_IS_NOT_VENUE_GET=true
POLICY_BIND_IS_NOT_CONSUMER_BIND=true
POLICY_BIND_IS_NOT_CURRENT_NUMERIC_FREEZE=true
POLICY_BIND_IS_NOT_TTL=true
POLICY_BIND_IS_NOT_EVENT_CACHE=true
POLICY_BIND_IS_NOT_INDEFINITE_REUSE=true
POLICY_BIND_IS_NOT_NETWORK_AUTHORIZATION=true
POLICY_BIND_IS_NOT_TRADING_AUTHORIZATION=true
HISTORICAL_6148_WINDOW_IS_NOT_OPERATIVE_CACHE=true
HISTORICAL_6151_FRESHNESS_POLICY_UNBOUND_IS_NOT_THIS_SLICE=true
THIS_SLICE_DOES_NOT_REWRITE_6151_HISTORICAL_UNBOUND=true
UPCCHG_IS_NOT_FRESHNESS_POLICY=true
MAXLMTSZ_IS_NOT_MAXMKTSZ=true
MAXLMTSZ_IS_NOT_POSITION_TIER_MAXSZ=true
MAXLMTSZ_IS_NOT_MAXAVAILSIZE=true
EXPOSURE_MAX_NOTIONAL_IS_NOT_VENUE_MAX_SIZE=true
KRAKEN_IS_NOT_CURRENT_CANONICAL_VENUE=true
ONE_CONTRACT_EQUALS_ONE_SUI=false
STRATEGY_LOGIC_CHANGED=false
SIGNAL_LOGIC_CHANGED=false
POSITION_LOGIC_CHANGED=false
RISK_APPETITE_CHANGED=false
MAX_POSITIONS_CHANGED=false
```

## 12) Guards (not SSOT)

Exact proof file:

`tests/ops/test_peak_trade_max_size_freshness_owner_policy_decision_v1.py`

Guards must keep:

- this spec and Master §5.3 name the freshness-policy persist and
  `MAX_SIZE_FRESHNESS_POLICY=FRESH_GET_PER_PRETRADE_DECISION`
- #6151 spec remains historically `MAX_SIZE_FRESHNESS_POLICY=UNBOUND`
  for that typed-domain slice
- #6148 spec remains historically a GET window, not an operative cache
- `HISTORICAL_MAX_SIZE_REUSE_ALLOWED=false`
- `PERSISTED_OBSERVATION_IS_OPERATIVE_CACHE=false`
- `FIXED_TTL_DEFINED=false`
- `EVENT_INVALIDATED_CACHE_DEFINED=false`
- `FAIL_CLOSED_ON_MISSING_FRESH_OBSERVATION=true`
- `CURRENT_REUSABLE_MAXLMTSZ_PROVEN=false`
- `CURRENT_REUSABLE_MAXMKTSZ_PROVEN=false`
- `MAX_SIZE_CONSUMER_BOUND=false`
- `MAX_SIZE_CONSUMER_CAN_NOW_BE_BOUND=true`
- required metadata edges remain 8; bound 0; partial 2; unbound 6; conflicted 0
- earliest remaining unbound edge `MAX_SIZE`; earliest remaining MAX_SIZE gap
  `MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING`
- Kraken exclusion closed; BTC not resurrected
- extract_instrument_constraints required tuple remains `minSz, lotSz, tickSz, ctVal`
- `maxLmtSz` / `maxMktSz` / `maxAvailSize` remain absent from order_plan, exposure, and submit_transport source
- no venue GET/POST this slice; no new official-doc fetch; no runtime mutation
- #6143–#6151 remain closed as historical persists
- standing Live / Testnet / Canary authorization remain false

## 13) Out of scope this slice

```text
MAX_SIZE_CONSUMER_IMPLEMENTATION=NOT_THIS_SLICE
MAX_SIZE_FRESH_OBSERVATION=NOT_THIS_SLICE
MAX_AVAILABLE_IMPLEMENTATION=NOT_THIS_SLICE
PRICE_BAND_IMPLEMENTATION=NOT_THIS_SLICE
LEVERAGE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
ACCOUNT_MODE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
INSTRUMENT_STATE_GATE_IMPLEMENTATION=NOT_THIS_SLICE
AUTHENTICATED_GET=NOT_THIS_SLICE
NETWORK_VENUE_GET=NOT_THIS_SLICE
NETWORK_POST=NOT_THIS_SLICE
NETWORK_DOCUMENTATION_FETCH=NOT_THIS_SLICE
CANARY_EXECUTE=NOT_THIS_SLICE
FLATTEN=NOT_THIS_SLICE
KRAKEN_RUNTIME_MUTATION=NOT_THIS_SLICE
CURRENT_NUMERIC_FREEZE=NOT_THIS_SLICE
FIXED_TTL_INVENTION=NOT_THIS_SLICE
EVENT_CACHE_INVENTION=NOT_THIS_SLICE
INDEFINITE_REUSE=NOT_THIS_SLICE
RESTORATION_REOPEN=NOT_THIS_SLICE
MERGE=NOT_THIS_SLICE
CORE_RUNTIME_MUTATION=false
```

## 14) Existing guards reused (not duplicated)

| Invariant | Current guard |
|---|---|
| #6151 typed contract-count domain closure | `tests/ops/test_peak_trade_order_plan_typed_contract_count_domain_closure_v1.py` |
| #6150 post-6149 MAX_SIZE normalization | `tests/ops/test_peak_trade_post_6149_max_size_normalization_adjudication_v1.py` |
| #6149 post-6148 MAX_SIZE unit | `tests/ops/test_peak_trade_post_6148_max_size_unit_adjudication_v1.py` |
| #6148 exact venue metadata GET | `tests/ops/test_peak_trade_exact_venue_metadata_get_current_sui_pretrade_max_size_v1.py` |
| #6147 metadata-binding PARTIAL persist | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_metadata_binding_alignment_adjudication_v1.py` |
| #6146 venue-pretrade limit gates | `tests/ops/test_peak_trade_post_restoration_venue_pretrade_limit_gates_adjudication_v1.py` |
| Preservation / compatibility contract | `tests/ops/test_peak_trade_post_restoration_baseline_preservation_and_compatibility_contract_v1.py` |
| Live safety gates | `tests/ops/test_peak_trade_post_restoration_live_safety_gates_adjudication_v1.py` |
| Simulated execution pipeline | `tests/ops/test_peak_trade_post_restoration_simulated_execution_pipeline_adjudication_v1.py` |
| Accounting / portfolio alignment | `tests/ops/test_peak_trade_post_restoration_accounting_portfolio_alignment_adjudication_v1.py` |
| Canary submit transport / order plan | `tests/ops/test_section_11_13_5_canary_submit_transport_v1.py` |
| Cap 11.9 fixture unreachable | `tests/ops/test_capability_11_9_live_canary_order_execution_v1.py` |

## 15) Negative contract

```text
RUNTIME_CORE_MUTATION=false
TRADING_LOGIC_MUTATION=false
ORDER_PLAN_MUTATED=false
EXPOSURE_MUTATED=false
SUBMIT_TRANSPORT_MUTATED=false
HTTP_CLIENT_MUTATED=false
KRAKEN_RUNTIME_MUTATED=false
MAX_SIZE_IMPLEMENTED=false
MAX_AVAILABLE_IMPLEMENTED=false
PRICE_BAND_IMPLEMENTED=false
LEVERAGE_GATE_IMPLEMENTED=false
VENUE_PRETRADE_LIMIT_GATES_COMPLETE=false
CHANGED_RUNTIME_FILES_EXPECTED=NONE
LIVE_READINESS_MUTATION=false
ORDER_SUBMIT_PERFORMED=false
FLATTEN_PERFORMED=false
TRADING_PERFORMED=false
LIVE_AUTHORITY_CHANGED=false
NETWORK_VENUE_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
NETWORK_DOCUMENTATION_READ_PERFORMED=false
RECOVERY_MUTATION=false
FORENSIC_REFERENCE_AUTHORITY=NONE
MAP_OF_TRUTH_STATUS=NAVIGATION_ONLY
SECOND_VENUE_PRETRADE_OWNER_CREATED=false
BTC_METADATA_REUSED=false
SUI_OTHER_INSTRUMENT_METADATA_REUSED=false
FAMILY_SCOPED_METADATA_REUSED=false
VENUE_GLOBAL_METADATA_REUSED=false
KRAKEN_METADATA_REUSED=false
MERGE_PERFORMED=false
SEE_ALSO_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING=docs/ops/specs/PEAK_TRADE_MAX_SIZE_FRESH_OBSERVATION_AND_CONSUMER_WIRING_V1.md
```
