# MASTER_V2 Canonical Volatility Hot-Path Contract Closure v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_HOT_PATH_CONTRACT_CLOSURE_V1
STATUS: CAPABILITY_AVAILABLE
scope: typed volatility contract + single productive producer + Double-Play hot-path wiring closure
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
PARAMETER_SELECTION: false
NUMERIC_MAX_AGE_DECIDED: false
MAX_AGE_ENFORCEMENT_ENABLED: false
HARD_STOP: true
---

> Closes confirmed Volatility Contract and Hot-Path wiring gaps so the
> productive Master-V2 &#47; Double-Play decision chain consumes exactly one
> canonical, typed, versioned, evidence-bound `VolatilityEstimateV1`.
> Does **not** select numeric max-age, enable enforcement, redefine Alpha &#47;
> CHOP &#47; State &#47; Cadence, or change trading-intent semantics.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_HOT_PATH_CONTRACT_CLOSURE_V1
CANONICAL_UNIT=PER_BAR_DECIMAL_RETURN_VOLATILITY
CANONICAL_HORIZON=PT60M
CANONICAL_ESTIMATOR=POPULATION_STANDARD_DEVIATION_OF_LOG_RETURNS
CANONICAL_ESTIMATOR_VERSION=population_std_ddof_0/v1
CANONICAL_DDOF=0
CANONICAL_ANNUALIZED=false
SINGLE_PRODUCTIVE_PRODUCER=true
TYPED_HOT_PATH_WIRED=true
NAKED_FLOAT_PRODUCTIVE_BINDING_REMOVED=true
COMPETING_BRIDGE_PRODUCER_REMOVED_OR_QUARANTINED=true
LEGACY_0_02_EXPLICIT_QUARANTINE_ONLY=true
LEGACY_0_2_SILENT_FALLBACK_FORBIDDEN=true
LEGACY_1_0_NOT_PRODUCTIVE=true
NUMERIC_MAX_AGE_DECIDED=false
NUMERIC_MAX_AGE_VALUE_UNRESOLVED=true
MAX_AGE_THRESHOLD_SELECTED=false
MAX_AGE_ENFORCEMENT_ENABLED=false
ALPHA_SEMANTICS_CHANGED=false
STATE_SEMANTICS_CHANGED=false
COMPOSITION_AUTHORITY_CHANGED=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
```

## Producer &#47; Consumer Graph

```
NormalizedPublicMarketData / Mark Samples
  → DistinctMarketObservationAcceptorV1
  → CanonicalVolatilityTypedRuntimeProducerScaffoldV1
  → canonical_volatility_estimate_materializer_v1
       (log returns, population stdev ddof=0, PT1M×60=PT60M, annualized=false)
  → VolatilityEstimateV1 (= CanonicalVolatilityEstimateV1)
  → typed presence &#47; trust gate
  → CanonicalMarketContextV1
  → update_dynamic_boundaries (adapted typed float only)
  → Double-Play composition / state / entry-exit path
```

Regime-classification proxy in `feature_regime_pipeline_v2`
(`sample variance ddof=1 × sqrt(n)`) remains **quarantined** and is not
CMC &#47; Double-Play volatility authority.

## Unit &#47; Horizon &#47; Estimator

| Field | Canonical value |
|---|---|
| unit | `PER_BAR_DECIMAL_RETURN_VOLATILITY` |
| bar duration | `PT1M` |
| horizon | `PT60M` (60 bars) |
| estimator | population standard deviation of log returns |
| ddof | `0` |
| annualized | `false` |
| estimator version | `population_std_ddof_0/v1` |

Config digest is the ratified feature-contract digest
(`config&#47;governance&#47;canonical_volatility_estimate_feature_contract_v1.json`).
Hot-path closure config binds that digest and adds policy fields without
duplicating estimator semantics.

## Legacy quarantine

| Path | Disposition |
|---|---|
| Replay default `0.02` | Explicit quarantine only |
| Historical bind default `0.2` | Silent fallback forbidden |
| Constructor default `1.0` | Not productive |
| Bridge `ddof=1 × sqrt(n)` | Quarantined non-productive authority |
| Naked float productive binding | Forbidden |

## Fail-closed semantics

Non-`VALID` statuses block ENTRY &#47; INCREASE. Exit &#47; Reduce &#47;
Reconciliation and `EXIT_ONLY` remain available. No automatic substitute
value. Full reason-code evidence required.

Statuses include: `VALID`, `INSUFFICIENT_HISTORY`, `UNKNOWN_UNIT`,
`UNKNOWN_HORIZON`, `UNKNOWN_ESTIMATOR`, `INVALID_VALUE`, `STALE`,
`OUT_OF_ORDER`, `DUPLICATE_NO_ADVANCE`, `SOURCE_DIGEST_MISMATCH`,
`CONFIG_DIGEST_MISMATCH`, `LEGACY_QUARANTINED`, `UNAVAILABLE`.

## Max-Age boundary

Numeric Max Age remains unresolved and enforcement remains disabled.
Structural age fields (`as_of_event_time`, oldest observation time,
diagnostic `volatility_age_seconds`) are present for later research only.
`max_age_threshold=null`, `max_age_enforcement_enabled=false`.

## Explicit non-goals

- numeric max-age threshold &#47; recommendation
- enforcement activation
- parameter selection
- Alpha &#47; CHOP &#47; State &#47; Cadence redefinition
- Live &#47; Testnet &#47; order routing
- Promotion &#47; economic-validity decision

## Owners (reuse-before-new)

| Surface | Owner |
|---|---|
| Closure | `src&#47;trading&#47;master_v2&#47;canonical_volatility_hot_path_contract_closure_v1.py` |
| Closure config | `config&#47;governance&#47;canonical_volatility_hot_path_contract_closure_v1.json` |
| Semantics | `canonical_volatility_estimate_feature_contract_v1` |
| Materializer | `canonical_volatility_estimate_materializer_v1` |
| Typed carrier | `canonical_volatility_estimate_typed_consumption_contract_v1` |
| CMC bind | `canonical_volatility_productive_runtime_cmc_typed_binding_v1` |
| Presence gate | `double_play_runtime_typed_volatility_presence_gate_v1` |
| Spec | this document |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_hot_path_contract_closure_v1.py` |
