---
docs_token: DOCS_TOKEN_CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1
status: active
scope: Cap 2.2 offline historical evidence time semantics owner decision; no historical collection; no walk-forward run; no ranking activation
capability: CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1
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

# Cap 2.2 Historical Evidence Time Semantics Owner Decision V1

Owner-GO
`PEAK_TRADE_CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1`
ratifies only the minimum offline historical evidence time semantics
required later to use the already-implemented offline MVR harness for
point-in-time / walk-forward evidence. This document is subordinate to
`docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`.
It does **not** replace §4.5–§4.5.11, does **not** run historical
collection, does **not** run walk-forward, does **not** ratify a
policy winner, does **not** activate ranking, does **not** schedule
the Economic-MD producer, does **not** close PDF Step 5, does
**not** authorize `apply_rotation`, does **not** allow PDF Step 7,
does **not** grant runtime, and does **not** join a host.

Typed contract:
`src&#47;ops&#47;cap22_historical_evidence_time_semantics_contract_v1.py`.

Harness remains
`src&#47;ops&#47;cap22_offline_mvr_evidence_harness_v1&#47;`.
This slice does **not** mutate harness ranking code.

```text
DOCUMENT_CLASS=TYPED_CONTRACT_AND_OWNER_DECISION
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1
BOUND_ORIGIN_MAIN_SHA=d8cbee19cf8318eca0ac23febc61289b4272aaff
CONTRACT_ID=CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1
DECISION_ID=CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1
SCHEMA_VERSION=cap22_historical_evidence_time_semantics.v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=OFFLINE_HISTORICAL_EVIDENCE_TIME_SEMANTICS_ONLY
AUTHORITY_SCOPE=OFFLINE_HISTORICAL_EVIDENCE_ONLY
PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED=false
RANKING_CADENCE_RATIFIED=true
RANKING_CADENCE_ID=PT1M_15_MINUTE_ANCHORS_V1
FORWARD_LABEL_HORIZON_RATIFIED=true
FORWARD_LABEL_HORIZON_SET_ID=CAP22_MVR_FORWARD_LABEL_HORIZONS_V1
FORWARD_LABEL_HORIZONS=15m;30m;60m;120m
FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME=true
FORWARD_ABS_RETURN_DEFINITION_RATIFIED=true
FORWARD_REALIZED_VOL_DEFINITION_RATIFIED=true
FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED=false
WALK_FORWARD_REQUIRED=true
WALK_FORWARD_PRIMARY_MODE=ALL_VALID_15M_ANCHORS
WALK_FORWARD_ROBUSTNESS_MODE=NON_OVERLAPPING_BY_HORIZON
HISTORICAL_REPLAY_HORIZON_RATIFIED=true
HISTORICAL_REPLAY_HORIZON_MODE=MINIMUM_COVERAGE_PLUS_AVAILABLE_HISTORY
HISTORICAL_REPLAY_HORIZON_ID=MIN_90D_PLUS_AVAILABLE_VALID_HISTORY_V1
MINIMUM_HISTORICAL_COVERAGE_DAYS=90
STRONGER_CANONICAL_MINIMUM_COVERAGE_DAYS_FOUND=false
CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_AT_T_REQUIRED=true
IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_REQUIRED=true
NEW_LISTING_WARMUP_FAIL_CLOSED=true
MINIMUM_VOLATILITY_WARMUP=61_PT1M_MARKS_60_LOG_RETURNS
NO_IMPLICIT_FILL=true
FINALIZED_ONLY=true
FUTURE_LEAKAGE_FORBIDDEN=true
STALE_SECONDS_RATIFIED=false
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED=false
AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND=false
POLICY_B_THRESHOLD_SET_RATIFIED=false
POLICY_B_SINGLE_THRESHOLD_RATIFIED=false
FINAL_SCORE_FORMULA_RATIFIED=false
FINAL_WEIGHTS_RATIFIED=false
CROSS_SECTIONAL_NORMALIZATION_RATIFIED=false
NEAR_ZERO_THRESHOLD_RATIFIED=false
POLICY_RATIFICATION_JUSTIFIED=false
NO_CHALLENGER_WINS_BY_THIS_SLICE=true
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY=true
HISTORICAL_EVIDENCE_GENERATED=false
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_RANK_ACTIVATED=false
PDF_STEP_5_STATUS=UNRESOLVED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_STATUS=FORBIDDEN
RUNTIME_AUTHORITY_GRANTED=false
PRODUCTIVE_MF_HOST_JOIN=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
NEXT_CANONICAL_DECISION=PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION
NEXT_CAP22_DEPENDENCY=SEPARATE_OWNER_GO_REQUIRED_TO_RUN_HISTORICAL_PIT_WALK_FORWARD_WITHOUT_WIRING
```

## 1. Existing authority adopted; no implicit import

Repo adjudication found **no** previously ratified Cap-22 ranking
cadence, forward-label horizon set, historical replay calendar horizon,
or walk-forward overlap mode. Those fields were explicitly
`RATIFIED=false` in §4.5.8–§4.5.11.

Already canonical Cap-22 constraints adopted, not reinvented:

```text
PIT_REPLAY_REQUIRED=true
FINALIZED_ONLY_REQUIRED=true
NO_LOOKAHEAD_REQUIRED=true
AUTHORIZED_VOLATILITY_BASE_GRID=FINALIZED_PT1M
AUTHORIZED_VOLATILITY_WARMUP=61_PT1M_MARKS_60_LOG_RETURNS
NO_IMPLICIT_FILL=true
UNIVERSE_MEMBERSHIP_AT_HISTORICAL_T_REQUIRED=true
IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_COMPARISON=true
WALK_FORWARD_REQUIRED=true
FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME=true
```

No authority is taken from research, PDF Step 5, forensic, CMC, or
Cap 5.2. No contradictory ratified Cap-22 time semantics were found.
No stricter canonical Cap-22 minimum coverage duration was found;
this slice therefore ratifies 90 days as the floor, not a ceiling.

## 2. Ranking cadence

```text
CAP22_OFFLINE_HISTORICAL_RANKING_CADENCE=PT1M_15_MINUTE_ANCHORS_V1
RANKING_CADENCE_RATIFIED=true
RANKING_CADENCE_ID=PT1M_15_MINUTE_ANCHORS_V1
ANCHOR_GRID=UTC_MINUTE_MOD_15_EQUALS_0
PIT_AVAILABLE_OR_FINALIZED_AT_ANCHOR_ONLY=true
NO_FUTURE_DATA=true
NO_INTRABAR_RECOMPUTE_BETWEEN_ANCHORS=true
PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED=false
```

Ranking snapshots for offline historical evidence occur every 15
minutes. The anchor timestamp lies exactly on UTC minutes where
`minute % 15 == 0`. Only data that were PIT-available or finalized at
the anchor may be used. Future data are forbidden. No intrabar
recalculation is authorized between anchors.

This cadence is **offline historical evidence only**. It does **not**
authorize a productive Cap-22 runtime cadence.

## 3. Forward label horizons

```text
FORWARD_LABEL_HORIZON_SET_ID=CAP22_MVR_FORWARD_LABEL_HORIZONS_V1
FORWARD_LABEL_HORIZONS=15m;30m;60m;120m
FORWARD_LABEL_HORIZON_MINUTES=15;30;60;120
FORWARD_LABEL_HORIZON_RATIFIED=true
FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME=true
FEATURE_BAR_MUST_NOT_ENTER_FORWARD_WINDOW=true
LABELS_ARE_EVALUATION_HORIZONS_NOT_HOLD_DURATION=true
```

A small explicit offline label set is ratified. Labels start strictly
after the feature / ranking anchor. The feature bar must not enter the
forward window. These horizons are evaluation horizons, not a hold
duration or execution instruction.

## 4. Forward label definitions

### 4.1 FORWARD_ABS_RETURN

```text
FORWARD_ABS_RETURN_DEFINITION_RATIFIED=true
ANCHOR_PRICE=LAST_FINALIZED_PT1M_MARK_PRICE_AT_OR_AS_OF_ANCHOR_PIT
FUTURE_PRICE=FINALIZED_PT1M_MARK_PRICE_AT_HORIZON_END
FORWARD_ABS_RETURN=ABS_LOG_FUTURE_OVER_ANCHOR
```

`anchor_price` is the last finalized PT1M mark price at or as-of the
anchor under the PIT rule. `future_price` is the finalized PT1M mark
price at the horizon end. `forward_abs_return` is
`abs(log(future_price &#47; anchor_price))`.

### 4.2 FORWARD_REALIZED_VOL

```text
FORWARD_REALIZED_VOL_DEFINITION_RATIFIED=true
FORWARD_REALIZED_VOL_INPUT=FINALIZED_PT1M_MARKS_STRICTLY_AFTER_ANCHOR_THROUGH_HORIZON_END
FORWARD_REALIZED_VOL_ESTIMATOR=POPULATION_SIGMA_DDOF_0
FEATURE_RETURN_WINDOW_OVERLAP_FORBIDDEN=true
```

Only finalized PT1M marks strictly after the anchor through horizon end
are used. Log returns are computed inside that forward window.
Estimator is population sigma (`ddof=0`). The forward window must not
overlap the feature-return window.

This Owner-GO defines the offline label estimator. It does **not**
transfer CMC, Cap 5.2, selected-future, or dashboard volatility
authority.

### 4.3 FRICTION_ADJUSTED_OPPORTUNITY

```text
FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED=false
FRICTION_ADJUSTED_OPPORTUNITY_METRIC_STATUS=BLOCKED_UNTIL_SEPARATE_OWNER_GO
```

No fully ratified formula exists. This slice does **not** invent a
composite. The metric remains blocked until a later Owner-GO.

## 5. Walk-forward anchors

```text
WALK_FORWARD_REQUIRED=true
WALK_FORWARD_PRIMARY_MODE=ALL_VALID_15M_ANCHORS
WALK_FORWARD_ROBUSTNESS_MODE=NON_OVERLAPPING_BY_HORIZON
OVERLAPPING_FORWARD_LABEL_WINDOWS_ALLOWED_IN_PRIMARY=true
NON_OVERLAPPING_ROBUSTNESS_VIEW_REQUIRED=true
NO_FUTURE_WINDOW_DATA_IN_FEATURE_COMPUTATION=true
```

Primary evidence uses every valid 15-minute anchor. Overlapping
forward-label windows are allowed in the primary view. Evaluation must
also emit a non-overlapping robustness view by horizon. Example: for
`H=60m`, the robustness view uses every fourth 15-minute anchor.
Feature computation must not use data from any future window.

This persist does **not** run walk-forward.

## 6. Historical replay horizon

```text
HISTORICAL_REPLAY_HORIZON_MODE=MINIMUM_COVERAGE_PLUS_AVAILABLE_HISTORY
HISTORICAL_REPLAY_HORIZON_ID=MIN_90D_PLUS_AVAILABLE_VALID_HISTORY_V1
MINIMUM_HISTORICAL_COVERAGE_DAYS=90
USE_ALL_AVAILABLE_VALID_LONGER_HISTORY=true
TIME_SEGMENT_REPORTING_REQUIRED=true
CHERRY_PICKING_FAVORABLE_WINDOW_FORBIDDEN=true
HISTORICAL_REPLAY_HORIZON_RATIFIED=true
NO_SINGLE_SHORT_WINDOW_RATIFIED_AS_TRUTH=true
```

No single short calendar window is ratified as truth. Policy-ratification
evidence later requires at least 90 days. Any additional longer valid
history that satisfies PIT and provenance must be used in full.
Results must be reported by time segments. Cherry-picking a more
favorable window is forbidden.

## 7. Historical universe at T

```text
CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_AT_T_REQUIRED=true
NO_TODAY_UNIVERSE_MEMBERSHIP_RETROACTIVE=true
IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_REQUIRED=true
```

For every anchor T, the bound Cap-2.1 governed futures universe
snapshot at T is required. Today's universe membership must not be
applied retroactively. Only instruments eligible at historical T in
that snapshot are candidates. Every challenger at an anchor must receive
exactly the same candidate-universe digest.

## 8. Warmup / listings

An instrument is rankable at T only if all of the following hold:

- Cap-2.1 eligible at T
- Economic-MD snapshot at T valid
- 61 contiguous finalized PT1M marks available
- no implicit fills

```text
NEW_LISTING_WITHOUT_WARMUP=NOT_RANKABLE_AT_T
NO_RETROACTIVE_FILL=true
NEW_LISTING_WARMUP_FAIL_CLOSED=true
```

## 9. Stale / collection skew

```text
STALE_SECONDS_RATIFIED=false
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED=false
HISTORICAL_EVIDENCE_MAY_USE_ONLY_VALID_PERSISTED_SNAPSHOTS=true
```

No numeric stale or skew bound is invented. Historical evidence may use
only snapshots that the existing snapshot contract already persisted as
valid. If later real historical collection requires numeric stale/skew
bounds, that is a separate hard stop / Owner-GO.

## 10. Policy-B threshold set remains unratified

```text
AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND=false
POLICY_B_THRESHOLD_SET_RATIFIED=false
POLICY_B_SINGLE_THRESHOLD_RATIFIED=false
INJECTED_TEST_ONLY_THRESHOLD_SETS_MAY_BE_EVALUATED_LATER=true
INJECTED_THRESHOLD_EVALUATION_DOES_NOT_RATIFY_THRESHOLD=true
```

A later historical harness may evaluate injected / test-only threshold
sets. That evaluation does **not** ratify a threshold economically.

## 11. Later evidence output requirements

Later historical runs must persist at least, per
`policy_id&#47;version`, anchor, horizon, and candidate universe digest:

- ranking output digest
- feature digest
- raw input digest
- forward label digest
- provenance
- top20 projection diagnostic
- candidate coverage

Aggregated evidence may later compute:

- Cross-sectional capture TOP20
- Forward Abs Return
- Forward Realized Vol
- Spearman rank association, if separately mathematically defined
- TOP20 turnover over time
- Rank stability
- Policy-B threshold sensitivity

```text
NO_POLICY_WINNER_BY_THIS_SLICE=true
POLICY_RATIFICATION_JUSTIFIED=false
SPEARMAN_RANK_ASSOCIATION_FORMULA_RATIFIED=false
```

## 12. Explicit non-decisions

```text
FINAL_SCORE_FORMULA_RATIFIED=false
FINAL_WEIGHTS_RATIFIED=false
CROSS_SECTIONAL_NORMALIZATION_RATIFIED=false
POLICY_B_THRESHOLD_SET_RATIFIED=false
POLICY_B_SINGLE_THRESHOLD_RATIFIED=false
NEAR_ZERO_THRESHOLD_RATIFIED=false
STALE_SECONDS_RATIFIED=false
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED=false
FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED=false
POLICY_RATIFICATION_JUSTIFIED=false
ECONOMIC_RANK_ACTIVATED=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
HISTORICAL_EVIDENCE_GENERATED=false
```

## 13. Authority boundary

```text
PDF_STEP_5_STATUS=UNRESOLVED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_STATUS=FORBIDDEN
RUNTIME_AUTHORITY_GRANTED=false
PRODUCTIVE_MF_HOST_JOIN=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
THIS_SLICE_GRANTS_OFFLINE_HISTORICAL_EVIDENCE_TIME_SEMANTICS_ONLY=true
```

## 14. Forbidden overreads

```text
OVERREAD_AS_POLICY_WINNER=FORBIDDEN
OVERREAD_AS_RANKING_ACTIVATED=FORBIDDEN
OVERREAD_AS_PRODUCTIVE_RUNTIME_CADENCE=FORBIDDEN
OVERREAD_AS_WALK_FORWARD_EXECUTED=FORBIDDEN
OVERREAD_AS_HISTORICAL_EVIDENCE_GENERATED=FORBIDDEN
OVERREAD_AS_THRESHOLD_RATIFIED=FORBIDDEN
OVERREAD_AS_FRICTION_FORMULA_RATIFIED=FORBIDDEN
OVERREAD_AS_PDF_STEP_5_CLOSED=FORBIDDEN
OVERREAD_AS_PDF_STEP_7_ALLOWED=FORBIDDEN
OVERREAD_AS_HOLD_DURATION_OR_EXECUTION_INSTRUCTION=FORBIDDEN
OVERREAD_AS_CAP52_OR_CMC_AUTHORITY_TRANSFER=FORBIDDEN
```
