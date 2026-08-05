# Productive Pure-Stack Owner Values — Two-Stage Ratification v1

```text
DOCUMENT_TYPE=OWNER_VALUES_TWO_STAGE_RATIFICATION
DOCUMENT_VERSION=1
STATUS=STAGE1_STRUCTURAL_RATIFIED_STAGE2_CALIBRATION_PROTOCOL_ONLY
BASELINE_ORIGIN_MAIN_SHA=631dca43601e4efad53a35c19ddf9bf70ebfd177
PARENT_AUTHORITY_RATIFICATION=docs/ops/PRODUCTIVE_PURE_STACK_INPUT_AUTHORITIES_OWNER_RATIFICATION_V1.md
STRUCTURAL_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json
CALIBRATION_PROTOCOL=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md

SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD_ROLE=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
RESULTV1_MAPPING_AUTHORIZED=false
NEW_TRADING_AUTHORITY_AUTHORIZED=false
INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT=false
INPUT_AUTHORITY_SURVIVAL_ENVELOPE=false
INPUT_AUTHORITY_SUITABILITY_PROJECTION=false
INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG=false
INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
STAGE1_PRODUCERS_PRODUCTIVE_ACTIVATION=false
RUNTIME_IMPLEMENTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
ARCHIVE_MUTATIONS=false
CMC_VOLATILITY_ESTIMATE_AS_REALIZED_VOLATILITY=false
FIXTURE_SCENARIO_WEBUI_AS_AUTHORITY=false
```

## 0. Purpose

This document is the Owner two-stage ratification for the 34
`OWNER_VALUE_*` tokens named in
`PRODUCTIVE_PURE_STACK_INPUT_AUTHORITIES_OWNER_RATIFICATION_V1.md`.

**Stage 1** ratifies only semantic and structural authorities: observation
identity, formulas, units, horizons/windows, taxonomy IDs, score scales and
definitions, sequence-metric definitions, strategy-side schema, capital-slot
time quantum, and the cashflow reinvest mechanical coupling.

**Stage 2** does **not** set productive numeric thresholds. It binds the
no-order, fail-closed, reproducible shadow calibration protocol in
`PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md`. Calibration
outputs remain Evidence until a **separate** Owner sign-off promotes each
number into productive config.

## 1. Non-negotiable invariants

```text
INV_NO_INVENTED_PRODUCTIVE_NUMERIC_THRESHOLDS=true
INV_NO_CMC_VOLATILITY_AS_REALIZED_VOLATILITY=true
INV_NO_RESULTV1_MAPPING=true
INV_NO_FIXTURE_SCENARIO_WEBUI_AUTHORITY=true
INV_DASHBOARD_READ_ONLY_CONSUMER=true
INV_SOLE_TRADING_AUTHORITY_ONLY=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_STAGE1_PRODUCERS_NOT_PRODUCTIVELY_ACTIVATED=true
INV_NO_ORDERS_TESTNET_LIVE=true
INV_NO_AUTO_PROMOTION_OF_CALIBRATION_OUTPUTS=true
INV_MISSING_OR_INVALID_FAIL_CLOSED=true
INV_FRESHNESS_INDEPENDENT_OF_CMC_NUMERIC_MAX_AGE=true
```

## 2. Classification summary

Machine-authoritative classification lives in
`docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json`.

| Category | Count | Meaning |
|---|---:|---|
| `STRUCTURAL_RATIFIED` | 15 | Stage-1 identifiers and structural parameters ratified here |
| `MECHANICALLY_COUPLED` | 1 | `REINVEST_FRACTION = 1 - CASHFLOW_LOCK_FRACTION` |
| `NUMERIC_CALIBRATION_REQUIRED` | 18 | Stage-2 calibration; productive number null |
| `DEFERRED_FAIL_CLOSED` | 0 | Unused in this revision |

```text
TOKEN_COUNT=34
PRODUCTIVE_NUMERIC_VALUES_SET=0
```

## 3. Forbidden sources (unchanged)

```text
FORBIDDEN_CMC_VOLATILITY_ESTIMATE_AS_REALIZED_VOLATILITY
FORBIDDEN_RESULTV1_TO_PURE_STACK_MAPPING
FORBIDDEN_DASHBOARD_PRESENTATION_AS_AUTHORITY
FORBIDDEN_FIXTURE_SCENARIO_WEBUI_THRESHOLDS_AS_PRODUCTIVE_LAW
FORBIDDEN_SYNTHETIC_DEFAULT_SCALARS
FORBIDDEN_PARALLEL_TRADING_AUTHORITY
FORBIDDEN_AUTO_PROMOTION_CALIBRATION_TO_CONFIG
```

---

## 4. Stage 1 — Structural ratification

All Stage-1 producers remain **unauthorized for productive activation**.
Definitions may later be implemented under Sole Trading Authority only after
a separate GO that still keeps `INPUT_AUTHORITY_*=false` until numeric Stage-2
sign-off and binding are complete.

Observation identity (all Stage-1 market formulas):

```text
OBSERVATION_FAMILY=PUBLIC_MARKET_FINALIZED_BARS
BAR_INTERVAL=PT1M
POINT_IN_TIME_ONLY=true
NO_LOOKAHEAD=true
NO_IMPLICIT_FILL=true
PROVENANCE_REQUIRED=true
SOLE_CONSUMER_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
```

### 4.1 Realized volatility (Futures Pure-Stack; not CMC)

```text
OWNER_VALUE_REALIZED_VOLATILITY_FORMULA_ID=fps_realized_volatility.population_stdev_mark_log_returns.v1
OWNER_VALUE_REALIZED_VOLATILITY_UNIT=PER_BAR_DECIMAL_RETURN_VOLATILITY
OWNER_VALUE_REALIZED_VOLATILITY_HORIZON=PT60M
```

**Definition (versioned):**

- Price field: venue `mark_price` on finalized PT1M bars only.
- Return: `ln(mark_price_t / mark_price_t_minus_1)`.
- Estimator: population standard deviation of the last 60 contiguous log returns
  (`ddof=0`) ending at observation `t`.
- Warmup: 61 valid prices / 60 returns; else `NULL` fail-closed.
- Annualization: `NONE` (not annualized).
- Output: dimensionless per-bar decimal return volatility.

**Non-alias declaration:**

```text
CMC.volatility_estimate != FuturesVolatilityProfile.realized_volatility
CMC.canonical_volatility_estimate != FuturesVolatilityProfile.realized_volatility
fps_realized_volatility.population_stdev_mark_log_returns.v1
  IS_NOT_A_BINDING_TO_canonical_volatility_estimate_feature_contract/v1
```

Shared mathematical resemblance to the CMC feature contract, if any, does
**not** create identity, binding, or authority transfer.

### 4.2 ATR / range

```text
OWNER_VALUE_ATR_OR_RANGE_FORMULA_ID=fps_atr_or_range.wilder_atr_finalized_ohlcv.v1
OWNER_VALUE_ATR_OR_RANGE_UNIT=PRICE_QUOTE_CURRENCY_UNITS
OWNER_VALUE_ATR_OR_RANGE_WINDOW=14_PT1M_BARS
```

**Definition:**

- Input: finalized PT1M OHLCV for the selected instrument with provenance.
- True range at `t`:
  `max(high_t - low_t, abs(high_t - close_{t-1}), abs(low_t - close_{t-1}))`.
- ATR: Wilder recursive average over window `N=14` PT1M bars.
- Warmup incomplete → `NULL` fail-closed.
- Unit: price in the instrument quote currency (not percent, not annualized).

### 4.3 Volatility regime taxonomy

```text
OWNER_VALUE_VOLATILITY_REGIME_TAXONOMY_ID=fps_volatility_regime_taxonomy.v1
```

**Allowed labels (closed set):**

```text
low | mid | high | unknown
```

**Assignment rule (structural only; no productive numeric cut-points here):**

- Labels may be attached only by a Sole-Trading-Authority-authorized producer
  that documents its cut-point digest.
- Cut-points themselves are **not** productive Owner Values in this PR and must
  remain fail-closed / Evidence-only until a separate numeric Owner sign-off.
- Until cut-points exist: emit `unknown` or omit regime (`None`) → downstream
  volatility completeness rules apply.
- Dashboard regime presentation is non-authoritative and must not feed this
  taxonomy.

### 4.4 Opportunity / activity / liquidity

```text
OWNER_VALUE_OPPORTUNITY_SCORE_SCALE=UNIT_INTERVAL_0_1
OWNER_VALUE_OPPORTUNITY_SCORE_FORMULA_ID=fps_opportunity_score.fee_slippage_breakeven_movement.v1
OWNER_VALUE_ACTIVITY_OR_INACTIVITY_SCORE_FORMULA_ID=fps_activity_inactivity_score.range_volume_quiescence.v1
OWNER_VALUE_LIQUIDITY_SPREAD_SOURCE_FORMULA_ID=fps_liquidity_spread.best_bid_ask_mid_bps.v1
```

**Opportunity score (`fps_opportunity_score.fee_slippage_breakeven_movement.v1`):**

- Scale: `[0, 1]` (`UNIT_INTERVAL_0_1`).
- Semantic: monotonic transform of recent movement relative to an explicit
  fee+slippage breakeven band derived from instrument metadata and ratified
  fee/slippage model inputs under Sole Trading Authority.
- Missing fee/slippage/movement inputs → `NULL` fail-closed (no default `0`).
- Not a trade signal; not selector authority.

**Activity / inactivity (`fps_activity_inactivity_score.range_volume_quiescence.v1`):**

- Scale: `[0, 1]` where higher means more inactivity / quiescence.
- Semantic: combine short-horizon range compression and quote-volume quiescence
  on finalized PT1M bars with provenance.
- Missing inputs → `NULL` fail-closed.

**Liquidity spread (`fps_liquidity_spread.best_bid_ask_mid_bps.v1`):**

- `spread_bps = 1e4 * (best_ask - best_bid) / mid` with `mid = (best_bid + best_ask) / 2`.
- Requires explicit best bid/ask observation identity and freshness.
- Invalid/crossed/missing book → fail-closed incomplete liquidity profile.
- Not a dashboard ticker label authority.

### 4.5 Sequence survival metric definitions

```text
OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID=fps_sequence_path_survival_ratio.prearm_path_fraction.v1
OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID=fps_sequence_metric_set.double_play_survival_envelope_v0_fields.v1
```

**Metric set (`fps_sequence_metric_set.double_play_survival_envelope_v0_fields.v1`):**

Exactly the pure DTO fields of `SequenceSurvivalMetrics` in
`src&#47;trading&#47;master_v2&#47;double_play_survival.py`:

```text
path_survival_ratio
early_loss_toxicity
margin_buffer_at_risk_99
sequence_fragility_index
liquidation_near_miss_rate
governance_breach_frequency
chop_switch_survival_score
```

**Path survival ratio (`fps_sequence_path_survival_ratio.prearm_path_fraction.v1`):**

- Fraction of pre-arm evaluated stress paths that remain above the governed
  ruin/liquidation barrier for the shared Long/Short pair under the arithmetic
  kernel projection.
- Path ensemble identity must be version-digested; hot-path heavy recompute is
  forbidden.
- Numeric acceptance thresholds remain Stage-2 (`OWNER_VALUE_SURVIVAL_LIMIT_*`).

### 4.6 Strategy side declaration schema

```text
OWNER_VALUE_STRATEGY_SIDE_DECLARATION_SCHEMA_ID=strategy_side_declaration.v1
```

**Required artifact fields:**

| Field | Type | Rule |
|---|---|---|
| `schema_id` | string | must equal `strategy_side_declaration.v1` |
| `strategy_id` | string | opaque non-empty |
| `declared_side` | enum | exactly `SideCompatibility`: `long_bull`, `short_bear`, `both`, `neutral_range`, `unknown` |
| `explicit_side_evidence` | bool | must be explicit; names/registry/dashboard must not set it |
| `declaration_digest` | string | non-empty content digest |
| `schema_version` | string | `v1` |

Forbidden inference sources: strategy name, family label, ECM/Armstrong surface,
dashboard label, AI summary, registry label alone.

### 4.7 Capital-slot time quantum

```text
OWNER_VALUE_CAPITAL_SLOT_TIME_QUANTUM=SOLE_TRADING_AUTHORITY_CYCLE_INDEX
```

**Meaning:** one quantum equals one Sole Trading Authority cycle index increment
for the selected future. `time_without_cashflow_step` counts these quanta.
Wallclock seconds are not the quantum unless a later Owner revision changes this
ID.

### 4.8 Cashflow reinvest mechanical coupling

```text
OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION
CATEGORY=MECHANICALLY_COUPLED
COUPLING_RULE=1 - OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION
```

- No independent productive numeric is ratified for reinvest.
- After Stage-2 Owner sign-off of `CASHFLOW_LOCK_FRACTION`, reinvest must be set
  exclusively by the coupling rule (eps per `cashflow_split_valid`).
- Independent reinvest values are invalid and fail closed.

---

## 5. Stage 2 — Numeric calibration required (no productive numbers)

The following tokens remain `productive_numeric_value=null` and
`NUMERIC_CALIBRATION_REQUIRED`. Calibration must use Stage-1 definitions only
and follow
`docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md`.

```text
OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS
OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO
OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY
OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99
OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX
OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE
OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY
OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE
OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE
OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER
OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS
OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT
OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION
OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY
OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE
OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP
OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE
OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE
```

**Freshness note:** `OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS` is an
independent Futures Input safety/readiness policy. It is **not** the demoted
CMC Numeric-Max-Age Alpha parameter (`VOLATILITY_NUMERIC_MAX_AGE_ENFORCING=false`).

Calibration Evidence must not become productive config without a **separate**
Owner decision **per token**.

## 6. Explicit non-authorization

```text
PRODUCTIVE_EMISSION_AUTHORIZED=false
STAGE1_PRODUCER_PRODUCTIVE_ACTIVATION=false
INPUT_AUTHORITY_FLIP=UNAUTHORIZED
NUMERIC_PRODUCTIVE_CONFIG_WRITE=UNAUTHORIZED
ORDERS=UNAUTHORIZED
LIVE=UNAUTHORIZED
TESTNET=UNAUTHORIZED
ARCHIVE_MUTATION=UNAUTHORIZED
DASHBOARD_MUTATION=UNAUTHORIZED
RESULTV1_MAPPING=UNAUTHORIZED
CMC_ALIAS_BINDING=UNAUTHORIZED
```

## 7. References

- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_INPUT_AUTHORITIES_OWNER_RATIFICATION_V1.md`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_DISPLAY_DECISION_HOST_BINDING_V1_OPTION_A_OWNER_RATIFICATION_V1.md`
- `src&#47;trading&#47;master_v2&#47;double_play_futures_input.py`
- `src&#47;trading&#47;master_v2&#47;double_play_survival.py`
- `src&#47;trading&#47;master_v2&#47;double_play_suitability.py`
- `src&#47;trading&#47;master_v2&#47;double_play_capital_slot.py`
- `src&#47;ops&#47;productive_pure_stack_display_decision_host_binding_v1&#47;constants_v1.py`
