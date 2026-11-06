# MASTER_V2 Canonical Volatility Max-Age Research Stratification v2

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_RESEARCH_STRATIFICATION_V2
STATUS: CAPABILITY_AVAILABLE
scope: research-only stratification for productive max-age evidence evaluability
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
TRADING_AUTHORITY: NONE
PROMOTION_AUTHORITY: NONE
---

## Purpose

Research-only stratification for Max-Age robustness and evaluability evidence.
Descriptive metadata only — never Alpha, policy, position, execution, or MV2/Double-Play
decision authority.

## Authority

```text
RESEARCH_STRATIFICATION_AUTHORITY=RESEARCH_ONLY
TRADING_AUTHORITY=NONE
PROMOTION_AUTHORITY=NONE
BRIDGE_FEATURE_REGIME_AUTHORITY=UNCHANGED
MV2_DP_AUTHORITY=UNCHANGED
RELATION_TO_MV2_DP=READ_ONLY_SUBORDINATE_RESEARCH_METADATA
```

## Contract version

```text
RESEARCH_STRATIFICATION_CONTRACT_VERSION=canonical_volatility_max_age_research_stratification/v2
EVIDENCE_SCHEMA_VERSION_V2=canonical_volatility_max_age_productive_research_evidence_record/v2
```

## Inputs (CURRENT only)

1. **CMC typed volatility** — `volatility_value`, unit, horizon, estimator, observation
   count, source digest. Quarantined bridge `feature_regime` volatility is forbidden
   as substitute.
2. **Research-owned observation mark path** — append-only mids from authorized public
   mark observations per cycle. Not `HardenedBridgeSessionStateV2.mid_prices`.

## Dimensions (separated)

| Dimension | Field | Role |
|-----------|-------|------|
| Volatility regime stratum | `volatility_regime_stratum_v2` | `VOLATILITY_REGIME_STRATA` |
| Market state stratum | `market_state_stratum_v2` | `MARKET_STATE_STRATA` |

Composite key: `stratification_key_v2` = versioned join of both dimensions when
`stratification_ok=true`.

## Fail-closed states

`INSUFFICIENT_DATA`, `UNCLASSIFIED`, `MISSING`, `UNKNOWN` — never count toward
minimum market or volatility regime coverage.

## Parameter authority policy

All numeric lookbacks and classification thresholds require explicit Owner-ratified
parameter authority bound in preregistration digest. No implicit defaults, no post-hoc
calibration from prior campaigns, no promotion of test fixtures to production.

When authority is `UNSET`:

- `market_state_stratum_v2=UNKNOWN`
- `volatility_regime_stratum_v2=UNKNOWN` (unless separately ratified)
- `stratification_ok=false`
- `RESEARCH_STRATIFICATION_V2_CAMPAIGN_ADMISSION=false`

## Cross-session / cross-campaign

```text
CROSS_SESSION_STATE_POLICY=RESEARCH_MARK_PATH_MAY_RESTORE_WITHIN_CAMPAIGN_ONLY
CROSS_CAMPAIGN_STATE_POLICY=NO_CARRY
```

Research mark-path restore is evaluative-only and must not affect bridge, MV2, or DP.

## Legacy v1

Existing productive records under schema v1 and legacy `regime_label` semantics are
immutable. No in-place relabel. v1/v2 coverage minima must not be mixed.

## Threshold authority (production default)

```text
MARKET_STATE_THRESHOLD_AUTHORITY=UNSET
MARKET_STATE_LOOKBACK_AUTHORITY=UNSET
VOLATILITY_STRATUM_THRESHOLD_AUTHORITY=UNSET
```
