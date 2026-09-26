---
docs_token: DOCS_TOKEN_PEAK_TRADE_RANKING_FEATURE_PRODUCTION_V1
status: active
scope: B05 Cap-2.1 / Input-2 raw ranking feature production; B03 policy + B04 DTO only; no rank activation
capability: CAP21_FEATURE_PRODUCTION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ECONOMIC_RANK_ACTIVATED: false
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION: false
HARD_STOP: true
---

# Peak Trade Ranking Feature Production V1 (B05)

Owner-GO `PEAK_TRADE_B05_CAP21_FEATURE_PRODUCTION_V1` produces B03-ratified
economic ranking raw features from CURRENT canonical Economic-MD Input-2
snapshots into B04 typed raw DTOs. This document is subordinate to
`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`,
`docs/ops/specs/PEAK_TRADE_RANKING_MATRIX_POLICY_V1.md`, and
`docs/ops/specs/PEAK_TRADE_RANKING_FEATURE_CONTRACT_V1.md`.

Typed owner: `src/ops/peak_trade_ranking_feature_production_v1/`.

```text
DOCUMENT_CLASS=IMPLEMENTATION_PEAK_TRADE_RANKING_FEATURE_PRODUCTION
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_B05_CAP21_FEATURE_PRODUCTION_V1
BOUND_ORIGIN_MAIN_SHA=9c2edeb7d5133974c3c8b771eaa15f5df3871ec4
CAPABILITY_ID=CAP21_FEATURE_PRODUCTION_V1
PRODUCTION_VERSION=peak_trade_ranking_feature_production.v1
SCHEMA_VERSION=peak_trade_ranking_feature_production_snapshot.v1
B05_IMPLEMENTED=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=NONE
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION=false
ECONOMIC_RANK_ACTIVATED=false
INPUT2_MAX_AGE_SECONDS_RATIFIED=false
INPUT2_MAX_AGE_SECONDS=UNRATIFIED
CAP23_SOLE_SELECTION_OWNER=true
CROSS_UNIVERSE_AUTHORITY=NONE
SELECTION_EFFECT=false
BINDING_EFFECT=false
RANKING_ACTIVATION=false
CROSS_SECTIONAL_NORMALIZATION_IN_B05=false
```

## Canonical data source

```text
CANONICAL_DATA_SOURCE=src.ops.economic_md_input_producer_v1
CANONICAL_SNAPSHOT=EconomicMdInputSnapshotV1
RAW_INPUT=61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES
```

Cap 2.1 structural eligibility remains a separate witness. B05 does not
alter Cap 2.1 eligibility scoring and does not grant Cap 2.1 ranking
authority. Economic-MD Input-2 remains the CURRENT owner of finalized
PT1M mark history used as ranking feature input.

## Ratified features produced

| Feature policy ID | Formula seam | Units | Raw normalization |
| --- | --- | --- | --- |
| `CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1` | population σ (ddof=0) over 60 log returns | `PER_BAR_DECIMAL_RETURN_VOLATILITY` | `NONE` |
| `CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1` | `(MAX-MIN)&#47;((MAX+MIN)&#47;2)` | `DIMENSIONLESS_FRACTION` | `NONE` |

Cross-sectional midrank/percentile normalization remains Cap 2.2 score
construction (B06). B05 produces raw features only.

## Fail-closed readiness

Missing, non-finalized, non-contiguous, insufficient (<61), non-positive,
or non-finite required mark inputs yield explicit
`MISSING` / `INVALID` / `INCOMPLETE_WARMUP` B04 states with reason codes.
No silent default, zero-imputation, NaN coercion, or stale cache
substitution creates a valid feature.

`INPUT2_MAX_AGE_SECONDS` remains `UNRATIFIED`. Age/timestamp facts may be
transported neutrally; B05 does not invent a freshness threshold.

## Explicit non-claims

- Feature production ≠ productive economic rank activated.
- B05 does not rank, sort, select, bind, or alter Cap 2.3.
- B05 does not authorize live, testnet, orders, or external effects.
- Map of Truth and System Atlas remain navigation-only (`AUTHORITY=NONE`).
