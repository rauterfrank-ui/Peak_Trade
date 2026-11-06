# PEAK_TRADE_ECONOMIC_RANKING_RUNTIME_V1 (B06)

```text
CAPABILITY_ID: CAP22_PEAK_TRADE_RANKING_RUNTIME_V1
B06_IMPLEMENTED: true
ECONOMIC_RANK_ACTIVATED: true
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED: true
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION: false
INPUT2_MAX_AGE_SECONDS_RATIFIED: false
CAP23_SOLE_SELECTION_OWNER: true
CROSS_UNIVERSE_AUTHORITY: NONE
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
MAX_POSITIONS_EFFECTIVE: 1
LIVE_EXTERNAL_EFFECT_AUTHORIZED: false
RUNTIME_AUTHORIZATION_EFFECT: NONE
```

## Purpose

B06 binds the productive Cap 2.2 ranking seam to the B03-ratified Peak_Trade
economic ranking policy. It consumes B04 feature-contract witnesses and B05
raw feature production snapshots. It does **not** select, bind, activate live
trading, or invent ranking policy.

## Ordering

```text
ORDER_PRIMARY=balanced_movement_score DESC
ORDER_SECONDARY=venue_native_id ASC
ORDER_TERTIARY=canonical_instrument_id ASC
```

`venue_native_id` is the deterministic final fallback after economic ties only.

## Inputs

- Cap 2.1 governed universe snapshot (structural eligibility only)
- B05 `RankingFeatureProductionSnapshotV1` with READY
  `CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1` and
  `CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1`

Missing or invalid required feature snapshots&#47;values fail closed. No silent
neutral score and no disguised venue-native primary order.

## Non-claims

- `ECONOMIC_RANK_ACTIVATED=true` ≠ `PRODUCTIVE_ECONOMIC_RANK_ACTIVATION`
- Cap 2.2 does not become Cap 2.3 selection owner
- No MV2&#47;Double Play&#47;execution rerank
- No Input-2 max-age policy invented
