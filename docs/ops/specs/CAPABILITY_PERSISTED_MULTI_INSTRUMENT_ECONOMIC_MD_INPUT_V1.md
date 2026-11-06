---
docs_token: DOCS_TOKEN_CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1
status: active
scope: Separate Economic-MD MVR raw-input producer implemented not wired; no ranking policy; no score formula; no Cap-2.2 dual-input runtime wire; no PDF Step 5 close
capability: CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-12
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
ECONOMIC_RANK_ACTIVATED: false
HARD_STOP: true
---

# Persisted Multi-Instrument Economic MD Input Producer V1

Owner-GO
`PEAK_TRADE_CAP_2_2_ECONOMIC_MD_MVR_RAW_INPUT_PRODUCER_IMPLEMENTATION_V1`
implements the already-authorized separate Economic-MD Input producer for
Cap 2.2 MVR raw input. This document is subordinate to
`docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`.
It does **not** replace §4.5–§4.5.8, does **not** close PDF Step 5,
does **not** authorize `apply_rotation`, does **not** allow PDF Step 7,
does **not** grant runtime, does **not** join a host, does **not**
rewire Cap 2.2 ranking onto dual input, and does **not** ratify a score
formula or weights. Offline spread comparison formula and identity
aggregator are persisted separately by
`docs&#47;ops&#47;specs&#47;CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_CHALLENGER_ORDER_V1.md`.
This producer still persists raw `bidPx`&#47;`askPx` only and does **not**
compute a derived spread feature.

Typed producer:
`src&#47;ops&#47;economic_md_input_producer_v1&#47;`.

Standalone entrypoint:
`scripts&#47;ops&#47;run_economic_md_input_producer_v1.py`.

```text
DOCUMENT_CLASS=IMPLEMENTATION_CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_CAP_2_2_ECONOMIC_MD_MVR_RAW_INPUT_PRODUCER_IMPLEMENTATION_V1
BOUND_ORIGIN_MAIN_SHA=ecc74a93cada6a8d605107d3958bd510f6d5bb19
CONTRACT_ID=CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1
SCHEMA_ID=economic_md_input_snapshot.v1
SCHEMA_VERSION=economic_md_input_snapshot.v1
PRODUCER_VERSION=economic_md_input_producer.v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=IMPLEMENTED_NOT_WIRED
ECONOMIC_MD_PRODUCER_IMPLEMENTED=true
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_RANK_ACTIVATED=false
CURRENT_PERSISTED_CAP22_ECONOMIC_MD_AVAILABLE=false
CAP22_CURRENT_PRODUCTIVE_INPUT=CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_ONLY
CAP22_REMAINS_RANKING_OWNER=true
CAP22_BECOMES_NETWORK_OWNER=false
CAP22_DIRECT_LIVE_VENUE_DEPENDENCY=false
CAP21_ROLE=STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY
ECONOMIC_MD_DATA_OWNER=SEPARATE_ECONOMIC_MD_INPUT_PRODUCER
ECONOMIC_MD_NETWORK_IO_OWNER=SEPARATE_ECONOMIC_MD_INPUT_PRODUCER
ECONOMIC_MD_PERSISTENCE_OWNER=SEPARATE_ECONOMIC_MD_INPUT_PRODUCER
ECONOMIC_MD_SCHEMA_OWNER=SEPARATE_ECONOMIC_MD_INPUT_PRODUCER
LIBRARY_REUSE_AUTHORITY_TRANSFER=false
CMC_AUTHORITY_TRANSFERRED=false
SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED=false
CAP52_AUTHORITY_TRANSFERRED=false
CANARY_AUTHORITY_TRANSFERRED=false
VOLATILITY_RAW_INPUT_IMPLEMENTED=true
MINIMUM_VOLATILITY_WARMUP=61_PT1M_MARKS_60_LOG_RETURNS
NO_IMPLICIT_FILL=true
SPREAD_RAW_INPUT_IMPLEMENTED=true
RAW_BID_ASK_PERSISTED=true
SNAPSHOT_REPLAYABLE=true
SNAPSHOT_DIGEST_DETERMINISTIC=true
ECONOMIC_MD_PRODUCER_MAY_RANK=false
ECONOMIC_MD_PRODUCER_MAY_SELECT=false
ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20=false
ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A=false
ECONOMIC_MD_PRODUCER_MAY_DEFINE_ACTIVE_SET=false
ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION=false
FINAL_SCORE_FORMULA_RATIFIED=false
FINAL_WEIGHTS_RATIFIED=false
SPREAD_FORMULA_RATIFIED=true
SPREAD_FORMULA_ID=RELATIVE_BID_ASK_SPREAD_OVER_MID_V1
SPREAD_FORMULA_AUTHORITY_SCOPE=OFFLINE_MVR_COMPARISON_ONLY
PRODUCER_DOES_NOT_COMPUTE_DERIVED_SPREAD=true
SPREAD_AGGREGATOR_RATIFIED=true
SPREAD_AGGREGATOR=IDENTITY_SINGLE_SAME_CYCLE_QUOTE_V1
STALE_SECONDS_RATIFIED=false
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED=false
PDF_STEP_5_STATUS=UNRESOLVED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_STATUS=FORBIDDEN
RUNTIME_AUTHORITY_GRANTED=false
PRODUCTIVE_MF_HOST_JOIN=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
NEXT_CAP22_DEPENDENCY=SEPARATE_OWNER_GO_REQUIRED_TO_RUN_HISTORICAL_PIT_WALK_FORWARD_WITHOUT_WIRING
NEXT_CANONICAL_DECISION=PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION
```

## 1. Inputs

Cap-2.1 governed futures universe snapshot is eligibility-only. The
producer reads eligible instrument IDs and venue-native IDs. It does
not re-interpret Cap-2.1 eligibility and does not add instruments.

Public-MD raw input per eligible instrument:

- finalized PT1M mark-price history (`&#47;api&#47;v5&#47;market&#47;history-mark-price-candles`)
- same-cycle `bidPx` + `askPx` (`&#47;api&#47;v5&#47;market&#47;ticker`)

Default invocation is injected&#47;offline. Network GET is optional,
explicit, public-only, and not productively scheduled.

## 2. Fail-closed raw-input eligibility

An instrument is not rankable raw-input when fewer than 61 finalized
PT1M marks exist, a required mark bar is missing, non-finalized data
would be included, bid&#47;ask is missing or non-positive, bid &gt; ask,
or provenance&#47;digest cannot be produced deterministically.

Locked market, near-zero spread, stale-second bounds, and collection
skew numeric bounds remain unratified observations.

## 3. Explicit non-claims

- This producer does not produce an economic rank or TOP20.
- This producer does not apply Policy A and does not define an Active Set.
- This producer does not wire Cap 2.2 productive ranking onto dual input.
- This producer does not ratify score formula, weights, or spread formula.
- This producer does not close PDF Step 5 and does not allow PDF Step 7.
- This producer does not grant live, testnet, order, credential, or capital rights.
