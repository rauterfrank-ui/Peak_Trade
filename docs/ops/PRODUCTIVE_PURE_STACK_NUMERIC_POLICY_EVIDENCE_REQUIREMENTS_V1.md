# Productive Pure-Stack Numeric Policy Evidence Requirements v1

```text
DOCUMENT_TYPE=STAGE2_NUMERIC_POLICY_EVIDENCE_REQUIREMENTS
DOCUMENT_VERSION=1
STATUS=SCAFFOLDING_ONLY_NO_CALIBRATION_EXECUTED
BASELINE_ORIGIN_MAIN_SHA=80977448775bd4819cbeef9122364e6330d7100f
STRUCTURAL_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json
CALIBRATION_PROTOCOL=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md
EVIDENCE_PACK_SCHEMA=docs/ops/schemas/productive_pure_stack_numeric_policy_evidence_pack_v1.schema.json
CAMPAIGN_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD_ROLE=READ_ONLY_CONSUMER
PRODUCTIVE_NUMERIC_VALUES_SET=0
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
TOKEN_COUNT=18
```

## 0. Purpose

This document specifies the **per-token Evidence requirements** for the exact 18
`NUMERIC_CALIBRATION_REQUIRED` Owner Values. It is scaffolding for later
shadow/replay calibration Evidence packs. It does **not** propose, set, or
ratify any productive number.

```text
CALIBRATION_EXECUTED=false
PRODUCTIVE_NUMERIC_VALUE=null_for_all_18
OWNER_RATIFICATION=false
GROUP_AUTO_RATIFICATION=FORBIDDEN
```

## 1. Global invariants

```text
INV_NO_PRODUCTIVE_NUMERIC_VALUES=true
INV_INPUT_AUTHORITY_REMAINS_FALSE=true
INV_RUNTIME_IMPLEMENTED_FALSE=true
INV_DASHBOARD_READ_ONLY_CONSUMER=true
INV_SOLE_TRADING_AUTHORITY_ONLY=true
INV_NO_FIXTURE_SCENARIO_WEBUI_AUTHORITY=true
INV_NO_CMC_VOLATILITY_AS_REALIZED_VOLATILITY=true
INV_NO_SURVIVALRESULTV1_OR_SUITABILITYRESULTV1_NUMERIC_AUTHORITY=true
INV_NO_PARALLEL_ARITHMETIC_VOLATILITY_OPPORTUNITY_KERNEL=true
INV_PRIMARY_SAFETY_BEFORE_ECONOMICS=true
INV_PER_TOKEN_OWNER_RATIFICATION_REQUIRED=true
INV_REINVEST_FRACTION_MECHANICAL_COUPLING_ONLY=true
INV_TIME_QUANTUM_IS_CYCLE_INDEX_NOT_WALLCLOCK=true
INV_INITIAL_SLOT_BASE_NOT_ACCOUNT_EQUITY=true
```

## 2. Token inventory (exactly 18)

1. `OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS`
2. `OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO`
3. `OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY`
4. `OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99`
5. `OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX`
6. `OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE`
7. `OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY`
8. `OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE`
9. `OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE`
10. `OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER`
11. `OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS`
12. `OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT`
13. `OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION`
14. `OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY`
15. `OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE`
16. `OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP`
17. `OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE`
18. `OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE`

`OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION` is **not** in this set. It remains
mechanically coupled: `1 - OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION`.

---

## 3. Per-token requirements

For every token below:

```text
productive_numeric_value=null
input_authority=false
runtime_implemented=false
owner_ratification_status=NOT_RATIFIED
```

### 3.1 OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS

| Field | Requirement |
|---|---|
| semantic role | Futures Input readiness/safety max age for provenance `freshness_state`; independent of CMC numeric max-age alpha |
| required producer | market-data provenance producer feeding `FuturesMarketDataProvenanceStatus` |
| required observations | public market finalized PT1M bars; futures market-data provenance status; event-time freshness metadata |
| required stratification | instrument_id; volatility regime taxonomy (`low&#47;mid&#47;high&#47;unknown`); missing-regime stratum; time segment |
| required stress families | observation gaps / missing bars; staleness near and beyond candidate; spread expansion / crossed book |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; stale_unknown_block_rate |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | CMC numeric-max-age alpha reuse; fixture/WebUI/CMC/dashboard authority source; primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch |
| dependency tokens | none |
| allowed calibration output type | `THRESHOLD_SECONDS` |
| productive_numeric_value | `null` |

### 3.2 OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO

| Field | Requirement |
|---|---|
| semantic role | Minimum path survival ratio gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.3 OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY

| Field | Requirement |
|---|---|
| semantic role | Maximum early loss toxicity gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.4 OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99

| Field | Requirement |
|---|---|
| semantic role | Minimum margin buffer at risk 99 gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.5 OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX

| Field | Requirement |
|---|---|
| semantic role | Maximum sequence fragility index gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.6 OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE

| Field | Requirement |
|---|---|
| semantic role | Maximum liquidation near-miss rate gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.7 OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY

| Field | Requirement |
|---|---|
| semantic role | Maximum governance breach frequency gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.8 OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE

| Field | Requirement |
|---|---|
| semantic role | Minimum chop/switch survival score gate for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_RATIO_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.9 OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE

| Field | Requirement |
|---|---|
| semantic role | Maximum effective leverage layer limit for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_NONNEGATIVE_REAL` |
| productive_numeric_value | `null` |

### 3.10 OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER

| Field | Requirement |
|---|---|
| semantic role | Minimum liquidation buffer layer limit for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_NONNEGATIVE_REAL` |
| productive_numeric_value | `null` |

### 3.11 OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS

| Field | Requirement |
|---|---|
| semantic role | Maximum adverse fill loss layer limit for DoublePlaySurvivalEnvelope |
| required producer | DoublePlay survival-envelope shadow calibration under Sole Trading Authority |
| required observations | Stage-1 sequence metric set; Stage-1 path-survival ratio; canonical futures accounting kernel projection |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; OOS fail; incomplete stress; Stage-1 digest mismatch; fixture/WebUI/CMC/dashboard authority; SurvivalResultV1 / SuitabilityResultV1 numeric authority; parallel arithmetic kernel |
| dependency tokens | `OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID`; `OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID` |
| allowed calibration output type | `THRESHOLD_NONNEGATIVE_REAL` |
| productive_numeric_value | `null` |

### 3.12 OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT

| Field | Requirement |
|---|---|
| semantic role | Capital-slot profit step as fraction of effective slot base |
| required producer | `capital_slot_config.v1` shadow calibration under Sole Trading Authority |
| required observations | capital-slot cashflow step events; effective slot base observations |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; isolated Sharpe/profit optimization; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress |
| dependency tokens | none |
| allowed calibration output type | `THRESHOLD_PERCENT_FRACTION` |
| productive_numeric_value | `null` |

### 3.13 OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION

| Field | Requirement |
|---|---|
| semantic role | Capital-slot cashflow lock fraction in unit interval; mechanically couples reinvest fraction |
| required producer | `capital_slot_config.v1` shadow calibration under Sole Trading Authority |
| required observations | capital-slot cashflow split observations |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; independent reinvest fraction value; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress |
| dependency tokens | `OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION` (mechanical coupling only; not an independent Stage-2 token) |
| allowed calibration output type | `THRESHOLD_FRACTION_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.14 OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY

| Field | Requirement |
|---|---|
| semantic role | Minimum realized volatility gate in Stage-1 Pure-Stack units; not `CMC.volatility_estimate` |
| required producer | `capital_slot_config.v1` shadow calibration under Sole Trading Authority |
| required observations | `fps_realized_volatility.population_stdev_mark_log_returns.v1` outputs |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | CMC.volatility_estimate as realized-volatility alias; primary safety fail; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress; Stage-1 unit mismatch |
| dependency tokens | `OWNER_VALUE_REALIZED_VOLATILITY_FORMULA_ID`; `OWNER_VALUE_REALIZED_VOLATILITY_UNIT`; `OWNER_VALUE_REALIZED_VOLATILITY_HORIZON` |
| allowed calibration output type | `THRESHOLD_NONNEGATIVE_REAL` |
| productive_numeric_value | `null` |

### 3.15 OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE

| Field | Requirement |
|---|---|
| semantic role | Minimum ATR/range gate in Stage-1 price quote currency units |
| required producer | `capital_slot_config.v1` shadow calibration under Sole Trading Authority |
| required observations | `fps_atr_or_range.wilder_atr_finalized_ohlcv.v1` outputs |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; Stage-1 unit mismatch; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress |
| dependency tokens | `OWNER_VALUE_ATR_OR_RANGE_FORMULA_ID`; `OWNER_VALUE_ATR_OR_RANGE_UNIT`; `OWNER_VALUE_ATR_OR_RANGE_WINDOW` |
| allowed calibration output type | `THRESHOLD_PRICE_QUOTE_UNITS` |
| productive_numeric_value | `null` |

### 3.16 OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP

| Field | Requirement |
|---|---|
| semantic role | Maximum Sole Trading Authority cycle-index quanta without cashflow step |
| required producer | `capital_slot_config.v1` shadow calibration under Sole Trading Authority |
| required observations | Sole Trading Authority cycle index; cashflow step event times counted in cycle quanta |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | wallclock seconds as time quantum; primary safety fail; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress |
| dependency tokens | `OWNER_VALUE_CAPITAL_SLOT_TIME_QUANTUM` |
| allowed calibration output type | `THRESHOLD_INTEGER_CYCLE_QUANTA` |
| productive_numeric_value | `null` |

### 3.17 OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE

| Field | Requirement |
|---|---|
| semantic role | Minimum opportunity score gate on Stage-1 unit interval scale |
| required producer | `capital_slot_config.v1` shadow calibration under Sole Trading Authority |
| required observations | `fps_opportunity_score.fee_slippage_breakeven_movement.v1` outputs |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | primary safety fail; Stage-1 scale mismatch; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress |
| dependency tokens | `OWNER_VALUE_OPPORTUNITY_SCORE_FORMULA_ID`; `OWNER_VALUE_OPPORTUNITY_SCORE_SCALE` |
| allowed calibration output type | `THRESHOLD_SCORE_UNIT_INTERVAL` |
| productive_numeric_value | `null` |

### 3.18 OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE

| Field | Requirement |
|---|---|
| semantic role | Initial capital slot base; Owner policy amount, not ambient account equity remap |
| required producer | `capital_slot_state_store.v1` shadow calibration under Sole Trading Authority |
| required observations | Owner-declared slot-base candidate observations only |
| required stratification | instrument_id; regime taxonomy; missing-regime stratum; time segment |
| required stress families | gaps; staleness; spread expansion; volatility shocks; liquidation near-miss families; chop / rapid switch clusters |
| primary safety metrics | block_allow_rate; false_allow_rate; false_block_rate; path_survival; early_loss_toxicity; liquidation_near_miss_rate; governance_breach_frequency; effective_leverage; liquidation_buffer; adverse_fill_loss |
| secondary metrics | profit_factor; max_drawdown; turnover; fees; slippage; opportunity_cost |
| mandatory rejection criteria | account-equity derivation; primary safety fail; fixture/WebUI/CMC/dashboard authority; OOS fail; incomplete stress |
| dependency tokens | none |
| allowed calibration output type | `THRESHOLD_NONNEGATIVE_REAL` |
| productive_numeric_value | `null` |

---

## 4. Explicit non-authorization

```text
EVIDENCE_PACK_SCAFFOLDING_ONLY=true
CALIBRATION_EXECUTED=false
PRODUCTIVE_CONFIG_WRITE=UNAUTHORIZED
INPUT_AUTHORITY_FLIP=UNAUTHORIZED
ORDERS=UNAUTHORIZED
LIVE=UNAUTHORIZED
TESTNET=UNAUTHORIZED
ARCHIVE_AUTHORITY_MUTATION=UNAUTHORIZED
DASHBOARD_AUTHORITY_EFFECT=NONE
AUTO_GROUP_RATIFICATION=UNAUTHORIZED
```

## 5. References

- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_TWO_STAGE_RATIFICATION_V1.md`
- `docs&#47;ops&#47;schemas&#47;productive_pure_stack_numeric_policy_evidence_pack_v1.schema.json`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_EVIDENCE_PACK_SCAFFOLDING_V1.md`
