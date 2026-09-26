---
docs_token: DOCS_TOKEN_PEAK_TRADE_RANKING_MATRIX_POLICY_V1
status: active
scope: Owner-ratified Cap 2.2 ranking matrix policy persistence; CAP22_RANKING_POLICY_AUTHORITY only; no runtime wiring; no economic rank activation
capability: CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
ECONOMIC_RANK_ACTIVATED: false
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION: false
HARD_STOP: true
---

# Peak Trade Ranking Matrix Policy V1 (B03)

Owner-GO `PEAK_TRADE_B03_GOVERNANCE_PERSISTENCE_V1` persists the
Owner-ratified productive Cap 2.2 ranking policy matrix. This document
is subordinate to
`docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`.

Typed validator:
`src&#47;ops&#47;peak_trade_ranking_matrix_policy_v1.py`.

This persist does **not** implement B06 productive economic rank wiring,
does **not** activate economic rank, and does **not** grant Cap 2.3
selection, execution, live, testnet, or multi-future authority. B04 typed
feature contract and B05 Cap-2.1 raw-feature production are separate
bounded slices.

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_PEAK_TRADE_RANKING_MATRIX_POLICY
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_B03_GOVERNANCE_PERSISTENCE_V1
BOUND_ORIGIN_MAIN_SHA=9911495cb95776be55d32f2628cbd1c8dd702b59
POLICY_ID=PEAK_TRADE_RANKING_MATRIX_POLICY_V1
POLICY_VERSION=v1
SCHEMA_VERSION=peak_trade_ranking_matrix_policy.v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=CAP22_RANKING_POLICY_AUTHORITY_PERSIST_ONLY
B03_RATIFIED=true
POLICY_RATIFIED=true
RUNTIME_ACTIVATED=false
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION=false
ECONOMIC_RANK_ACTIVATED=false
CAP22_RANKING_POLICY_AUTHORITY=true
CAP23_SELECTION_AUTHORITY_ADDED=false
SOLE_PRODUCTIVE_SELECTION_OWNER=true
CROSS_UNIVERSE_AUTHORITY=NONE
```

## 1. Ranking objective

```text
RANKING_OBJECTIVE=BALANCED_MOVEMENT_STRUCTURE
EQUAL_IMPORTANCE_POLICY_AXIOM=true
AUTHORITY_SCOPE=CAP22_RANKING_ONLY
RANKING_OBJECTIVE_RATIFIED=true
```

Volatility and Amplitude are V1 co-equal normative factors for Cap 2.2
economic ranking semantics. This is not an empirically estimated
weighting and not an MV2/Double-Play trading decision.

## 2. Volatility policy

```text
VOLATILITY_POLICY_ID=CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1
VOLATILITY_INPUT=61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES
RETURN_COUNT=60
MARK_COUNT=61
DDOF=0
ANNUALIZED=false
VOLATILITY_UNITS=PER_BAR_DECIMAL_RETURN_VOLATILITY
VOLATILITY_DIRECTION=HIGHER_IS_BETTER
VOLATILITY_RAW_FEATURE_NORMALIZATION=NONE
VOLATILITY_POLICY_RATIFIED=true
```

Population σ over 60 log returns from 61 contiguous finalized PT1M
mark prices. Offline-MVR/MV2 formulas remain algorithm/evidence
reference only; Cap 2.2 owns this policy ID and authority.

## 3. Amplitude policy

```text
AMPLITUDE_POLICY_ID=CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1
AMPLITUDE_INPUT=SAME_61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES
AMPLITUDE_FORMULA=(MAX_MARK-MIN_MARK)/((MAX_MARK+MIN_MARK)/2)
AMPLITUDE_UNITS=DIMENSIONLESS_FRACTION
AMPLITUDE_DIRECTION=HIGHER_IS_BETTER
AMPLITUDE_RAW_FEATURE_NORMALIZATION=NONE
AMPLITUDE_POLICY_RATIFIED=true
```

Requires `p_min > 0` and `mid > 0`. Volatility and Amplitude must
share the same authoritative Input-2 collection cycle / measured-fact
provenance (ARCH-B).

## 4. Structural / economic separation

```text
STRUCTURAL_ECONOMIC_SEPARATION=HARD_INVARIANT
```

Cap 2.1 structural eligibility remains a separate witness and is not
numerically summed with Volatility or Amplitude. Volatility and
Amplitude are not 7th/8th structural binary components.

## 5. Complete economic rank set

```text
COMPLETE_ECONOMIC_RANK_SET=S_STAR
```

Membership requires Cap 2.1 structural PASS, complete valid Volatility
and Amplitude inputs, valid feature provenance, and non-stale/non-invalid
Input-2 snapshot. Normalization and ranking run only over `S_STAR`.

## 6. Score construction

```text
SCORE_CONSTRUCTION=EQUAL_WEIGHT_CROSS_SECTIONAL_MIDRANK_PERCENTILE_COMPOSITE_V1
TIE_RANK_METHOD=MIDRANK_DETERMINISTIC
FEATURE_PERCENTILE_FORMULA_N_GT_1=(N-FEATURE_MIDRANK)/(N-1)
VOLATILITY_WEIGHT=0.5
AMPLITUDE_WEIGHT=0.5
NORMATIVE_EQUAL_IMPORTANCE_WEIGHTS=true
EMPIRICALLY_ESTIMATED=false
FINAL_SCORE_FORMULA_RATIFIED=true
FINAL_WEIGHTS_RATIFIED=true
CROSS_SECTIONAL_NORMALIZATION_RATIFIED=true
SCORE_CONSTRUCTION_RATIFIED=true
```

Order: `balanced_movement_score DESC`, then `venue_native_id ASC`,
then `canonical_instrument_id ASC`. Venue-native order has no
market-attractiveness semantics.

## 7. Small-N semantics

```text
N=0: ECONOMIC_RANK_STATE=NO_COMPLETE_ECONOMIC_CANDIDATES
N=1: SINGLETON_CROSS_SECTION_STATE=NEUTRAL
     volatility_percentile=0.5 amplitude_percentile=0.5 balanced_movement_score=0.5
N>=2: midrank-percentile formula above
```

## 8. Cross-sectional dependency

```text
CROSS_SECTIONAL_DEPENDENCY=EXPECTED_AND_AUTHORIZED
```

Scores are relative to the snapshot `S_STAR`. Ranking snapshots must
audit `S_STAR`, `N`, excluded economic candidates, reason codes, raw
features, midranks, percentiles, balanced score, Input-2 digest, and
policy ID/version/digest.

## 9. Incomplete feature policy

```text
FC_ECON_POLICY=INCOMPLETE_FEATURE_CANDIDATE_EXPLICIT_EXCLUSION_V1
INCOMPLETE_FEATURE_POLICY_RATIFIED=true
LESS_THAN_61_CONTIGUOUS_FINALIZED_PT1M_MARKS=INCOMPLETE_FEATURE_CANDIDATE
```

No imputation, no silent drop, structural eligibility unchanged.

## 10. Stale Input-2 and activation pins

```text
STALE_INPUT2_BEHAVIOR=SNAPSHOT_LEVEL_FAIL_CLOSED
INPUT2_MAX_AGE_SECONDS=UNRATIFIED
INPUT2_MAX_AGE_SECONDS_RATIFIED=false
OWNER_THRESHOLD_REQUIRED=true
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION=false
ECONOMIC_RANK_ACTIVATED=false
```

Numeric freshness threshold is a pre-activation Owner pin. It blocks
productive economic rank activation only, not B04/B05/B06 fail-closed
implementation or B08/B09/B10 proofs.

## 11. Profile and Input-2 venue

```text
PROFILE_PROMOTION_V1=NONE_ADDITIONAL
PROFILE_AUTHORITY_EFFECT=NONE
PROFILE_PROMOTION_V1_RATIFIED=true
PRODUCTIVE_INPUT2_VENUE=OKX_EEA
PRODUCTIVE_INPUT2_HOST=eea.okx.com
WWW_OKX_PRODUCTIVE_INPUT2_AUTHORITY=NONE
```

## 12. Subordinate architecture contracts

Ranking feature contract (B04 typed DTO seam, no runtime activation) is in
`docs&#47;ops&#47;specs&#47;PEAK_TRADE_RANKING_FEATURE_CONTRACT_V1.md` /
`src&#47;ops&#47;peak_trade_ranking_feature_contract_v1.py`.

Dual-input architecture remains in
`docs&#47;ops&#47;specs&#47;CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1.md`.
Offline MVR challenger evidence remains in
`docs&#47;ops&#47;specs&#47;CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md`
without productive authority. Current productive ranking **runtime**
remains structural until B06 wires this policy fail-closed.

## 13. Explicit non-claims

- Policy ratified ≠ runtime activated.
- This persist does not change Cap 2.3 selection behavior.
- This persist does not authorize live, testnet, orders, or external
  effects.
- Map of Truth and System Atlas remain navigation-only.
