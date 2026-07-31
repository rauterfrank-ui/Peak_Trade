# MASTER_V2 Canonical Volatility Estimate Typed Consumption Contract v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_ESTIMATE_TYPED_CONSUMPTION_CONTRACT_V1
STATUS: CAPABILITY_AVAILABLE
scope: typed carrier + fail-closed legacy float adapter; non-authorizing; no runtime wiring
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_WIRING: false
HOT_PATH_BINDING: false
PARAMETER_EFFECT: false
TRADING_LOGIC_EFFECT: false
---

> **Non-authorizing.** Reuses ratified
> `canonical_volatility_estimate_feature_contract&#47;v1` semantics and the existing
> canonical materializer. Provides a typed carrier and a fail-closed legacy-float
> adapter only. Does **not** wire Double Play, mutate hot-path defaults
> (`0.2` &#47; `0.02` &#47; `1.0`), change parameters, composition, entry&#47;exit,
> survival, suitability, market state, or authorize live &#47; testnet &#47; orders.

## Machine summary

```
SEMANTICS_OWNER=trading.master_v2.canonical_volatility_estimate_feature_contract_v1
ESTIMATOR_OWNER=trading.master_v2.canonical_volatility_estimate_materializer_v1
TYPED_CARRIER_OWNER=trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1
LEGACY_ADAPTER_OWNER=trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1
CANONICAL_UNIT=PER_BAR_DECIMAL_RETURN_VOLATILITY
CANONICAL_HORIZON=PT60M
CANONICAL_ESTIMATOR=POPULATION_STANDARD_DEVIATION_OF_LOG_RETURNS
OBSERVATION_REQUIREMENT=61_prices_60_returns
UNKNOWN_BEHAVIOR=FAIL_CLOSED
FALLBACK_POLICY=REJECT_FALLBACK_USED_AND_IMPLICIT_DEFAULTS
RUNTIME_EFFECT=false
TRADING_LOGIC_EFFECT=false
PARAMETER_EFFECT=false
LIVE_AUTHORIZATION=false
IMPLICIT_DEFAULT_ALLOWED=false
MV2_FALLBACK_0_2_ADMISSIBLE=false
WARMUP_BEHAVIOR=NULL_FAIL_CLOSED
READY_FOR_HOT_PATH_BINDING=false
READY_FOR_PARAMETER_RESEARCH=false
```

## Owners (reuse-before-new)

| Surface | Owner |
|---|---|
| Semantics | `trading.master_v2.canonical_volatility_estimate_feature_contract_v1` |
| Estimator &#47; materializer | `trading.master_v2.canonical_volatility_estimate_materializer_v1` |
| Typed carrier | `src&#47;trading&#47;master_v2&#47;canonical_volatility_estimate_typed_consumption_contract_v1.py` |
| Legacy float adapter | same module (`adapt_canonical_volatility_estimate_to_legacy_float_v1`) |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_estimate_typed_consumption_contract_v1.py` |

No second semantics authority and no second estimator implementation are introduced.

## Carrier

Immutable `CanonicalVolatilityEstimateV1`:

- `value`, `unit`, `bar_interval_seconds`, `lookback_bars`, `horizon_seconds`
- `annualized`, `estimator`, `observation_count`, `as_of_event_time`
- `fallback_used`, `source_digest`, `contract_version`

Fail-closed validation rejects missing &#47; non-finite &#47; negative values, wrong unit &#47;
interval &#47; lookback &#47; horizon, annualization, wrong estimator, insufficient
observations, naive event time, empty digest, unsupported contract version, and
`fallback_used=true`.

## Factory boundary

```
canonical mark-price observations
  → existing materializer (REUSE)
  → validated CanonicalVolatilityEstimateV1
```

- `REUSE_EXISTING_MATERIALIZER=true`
- `DUPLICATE_ESTIMATOR_IMPLEMENTATION=false`
- `RUNTIME_CYCLE_AS_MARKET_TIME=false`
- `POLL_COUNT_AS_OBSERVATION_COUNT=false`
- `EVENT_TIME_PRESERVED=true`
- `SOURCE_DIGEST_DETERMINISTIC=true`

## Legacy float adapter

`CanonicalVolatilityEstimateV1` → legacy float succeeds only when the estimate is
fully validated with `fallback_used=false` and canonical unit &#47; horizon &#47;
estimator &#47; observations &#47; contract version.

The adapter:

- does not insert defaults
- does not replace `None`
- does not silently insert `0.2`, `0.02`, or `1.0`
- does not guess unit &#47; horizon
- does not silently accept annualized or foreign-horizon producers

Numeric equality with `0.2` &#47; `0.02` &#47; `1.0` is allowed only when the value is a
validated typed estimate with proven canonical provenance.

## Contract gates (new path only)

```
IMPLICIT_FALLBACK_REJECTED=true
MV2_FALLBACK_0_2_REJECTED=true
UNKNOWN_PROVENANCE_REJECTED=true
UNKNOWN_UNIT_REJECTED=true
UNKNOWN_HORIZON_REJECTED=true
ANNUALIZED_INPUT_REJECTED=true
INSUFFICIENT_OBSERVATIONS_REJECTED=true
FALLBACK_USED_REJECTED=true
```

Existing legacy hot-path defaults are **not** mutated by this capability.

## Non-goals / non-aliases

Not unified with this estimate:

- `volatility_survival_ratio`
- `FuturesVolatilityProfile.realized_volatility`
- `volatility_profile_present`
- regime analytics annualized volatility
- wallclock `feature_regime_pipeline` volatility
- research panel 1h volatility
- ATR

## Open hot-path gaps (remain open)

```
G1_SILENT_0_2_IN_HISTORICAL_BIND
G2_SILENT_0_02_SCENARIO_INTEGRATED_DEFAULTS
G3_UNTYPED_EXISTING_HOT_PATH_FLOAT
G4_COMPETING_PRODUCERS_DIFFERENT_SCALING
G5_PANEL_1H_REUSES_PT1M_LOOKBACK
G6_MATERIALIZER_NOT_WIRED_TO_DOUBLE_PLAY
G7_SEPARATE_SURVIVAL_AND_SUITABILITY_VOL_CONCEPTS
G8_LEGACY_PATH_NOT_YET_GLOBALLY_ENFORCED
G9_FUTURES_PROFILE_PRIMARY_METRIC_OQ001_OPEN
```

These gaps are intentionally left open. Closing any of them requires a separate
Operator-GO and must not be performed silently under this capability.

## Forbidden without separate GO

- Runtime &#47; Double Play wiring
- Historical bind &#47; scenario &#47; integrated-replay &#47; dynamic-scope default mutation
- Parameter recommendation or change
- Composition &#47; entry&#47;exit &#47; directional &#47; survival &#47; suitability &#47; scope &#47; C1 &#47;
  confirmation changes
- Live &#47; testnet &#47; order authorization
