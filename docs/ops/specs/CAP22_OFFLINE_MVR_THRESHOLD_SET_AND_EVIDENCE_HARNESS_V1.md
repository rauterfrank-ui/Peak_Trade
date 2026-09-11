---
docs_token: DOCS_TOKEN_CAP22_OFFLINE_MVR_THRESHOLD_SET_AND_EVIDENCE_HARNESS_V1
status: active
scope: Cap 2.2 injected Policy-B offline threshold-set contract and deterministic offline MVR evidence harness; no policy ratification; no productive activation
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

# Cap 2.2 Offline MVR Threshold Set And Deterministic Evidence Harness V1

Owner-GO
`PEAK_TRADE_CAP22_OFFLINE_MVR_THRESHOLD_SET_AND_EVIDENCE_HARNESS_V1`
implements a typed injected Policy-B offline threshold-set contract
and a fully deterministic, replayable offline MVR evidence harness for
challengers A&#47;B&#47;C&#47;D plus the structural negative control. This
document is subordinate to
`docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`.
It does **not** replace §4.5–§4.5.10, does **not** ratify any Policy-B
threshold, does **not** close PDF Step 5, does **not** authorize
`apply_rotation`, does **not** allow PDF Step 7, does **not** grant
runtime, does **not** join a host, does **not** wire productive Cap 2.2
economic ranking, and does **not** claim historical walk-forward
evidence.

Typed contract:
`src&#47;ops&#47;cap22_offline_mvr_threshold_set_and_evidence_harness_contract_v1.py`.

Harness package:
`src&#47;ops&#47;cap22_offline_mvr_evidence_harness_v1&#47;`.

Standalone entrypoint:
`scripts&#47;ops&#47;run_cap22_offline_mvr_evidence_harness_v1.py`.

Spread semantics remain
`docs&#47;ops&#47;specs&#47;CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_CHALLENGER_ORDER_V1.md`.

```text
DOCUMENT_CLASS=TYPED_CONTRACT_AND_OFFLINE_HARNESS
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_CAP22_OFFLINE_MVR_THRESHOLD_SET_AND_EVIDENCE_HARNESS_V1
BOUND_ORIGIN_MAIN_SHA=ea7582f298c4fbc032f50c18db756face6310497
CONTRACT_ID=CAP22_OFFLINE_MVR_THRESHOLD_SET_AND_EVIDENCE_HARNESS_V1
SCHEMA_VERSION=cap22_offline_mvr_evidence_harness.v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=OFFLINE_THRESHOLD_SET_AND_DETERMINISTIC_EVIDENCE_HARNESS_ONLY
AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND=false
POLICY_B_THRESHOLD_MODE=VERSIONED_OFFLINE_THRESHOLD_SET
POLICY_B_THRESHOLD_SET_ID=CAP22_MVR_POLICY_B_INJECTED_THRESHOLD_SET_V1
POLICY_B_THRESHOLD_SET_RATIFIED=false
POLICY_B_SINGLE_THRESHOLD_RATIFIED=false
POLICY_B_TEST_ONLY_VALUES_USED=true
NEAR_ZERO_THRESHOLD_RATIFIED=false
FINAL_SCORE_FORMULA_RATIFIED=false
FINAL_WEIGHTS_RATIFIED=false
CROSS_SECTIONAL_NORMALIZATION_RATIFIED=false
RANKING_CADENCE_RATIFIED=false
FORWARD_LABEL_HORIZON_RATIFIED=false
HISTORICAL_REPLAY_HORIZON_RATIFIED=false
POLICY_RATIFICATION_JUSTIFIED=false
NO_CHALLENGER_WINS_BY_THIS_SLICE=true
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY=true
ECONOMIC_MD_PRODUCER_IMPLEMENTED=true
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false
ECONOMIC_RANK_ACTIVATED=false
HARNESS_NETWORK_READ_REQUIRED=false
TOP20_DIAGNOSTIC_ONLY=true
POLICY_WINNER_OUTPUT_PRESENT=false
FORWARD_LABEL_METRICS_PRESENT=false
HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT=false
PDF_STEP_5_STATUS=UNRESOLVED
ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5
PDF_STEP_7_STATUS=FORBIDDEN
RUNTIME_AUTHORITY_GRANTED=false
PRODUCTIVE_MF_HOST_JOIN=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
NEXT_CANONICAL_DECISION=PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION
NEXT_CAP22_DEPENDENCY=SEPARATE_OWNER_GO_REQUIRED_TO_RATIFY_RANKING_CADENCE_FORWARD_LABEL_AND_HISTORICAL_REPLAY_HORIZONS_THEN_RUN_WALK_FORWARD_WITHOUT_WIRING
```

## 1. Policy-B threshold set is injected and unratified

Repo-internal census found no canonical Cap-22 MVR spread-threshold
scale with authority. This slice therefore implements a typed
`INJECTED_THRESHOLD_SET` contract. Fixture members are explicitly
`TEST_ONLY_NON_CANONICAL` values in
`RELATIVE_SPREAD_DECIMAL_FRACTION`. No member is economically
optimal or productively valid.

```text
CHALLENGER_A=CAP22_MVR_VOLATILITY_RANK_ONLY_V1
CHALLENGER_B=CAP22_MVR_HARD_SPREAD_GATE_THEN_VOL_V1
CHALLENGER_C=CAP22_MVR_VOLATILITY_TO_SPREAD_RATIO_V1
CHALLENGER_D=CAP22_MVR_LEXICOGRAPHIC_SPREAD_THEN_VOL_V1
NEGATIVE_CONTROL=CAP22_MVR_STRUCTURAL_NEGATIVE_CONTROL_V1
OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A=true
```

## 2. Harness

The harness loads an Economic-MD snapshot from injected or persisted
input, validates digest and provenance, binds the Cap-2.1 universe
snapshot at the same T, enforces identical candidate-universe
membership, computes features locally, and evaluates every challenger
deterministically. Policy B is evaluated once per injected threshold
member. TOP20 is a non-authoritative diagnostic projection only.

Allowed evidence classes:

- `OFFLINE_FIXTURE_EVIDENCE`
- `OFFLINE_PERSISTED_SNAPSHOT_REPLAY`

Forbidden evidence classes:

- `HISTORICAL_PIT_WALK_FORWARD_EVIDENCE`
- `PRODUCTIVE_EVIDENCE`
- `POLICY_RATIFICATION_EVIDENCE`

Same input and config yield the same
`RAW_INPUT_DIGEST`, `FEATURE_DIGEST`, `CANDIDATE_UNIVERSE_DIGEST`,
`RANKING_OUTPUT_DIGEST`, and `HARNESS_RUN_ID`.
