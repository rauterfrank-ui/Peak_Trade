# Productive Pure-Stack Input / Config / State Authorities — Owner Ratification v1

```text
DOCUMENT_TYPE=OWNER_AUTHORITY_RATIFICATION
DOCUMENT_VERSION=1
STATUS=BLOCKED_OWNER_VALUES_REQUIRED
CAPABILITY_SCOPE=PRODUCTIVE_PURE_STACK_INPUT_CONFIG_STATE_AUTHORITIES
BASELINE_ORIGIN_MAIN_SHA=c23b30ae07f357debc88f34aa4f0f65a61a072b5
OPTION_A_PREREQUISITE=MERGED_AND_CONFIRMED
OPTION_A_DOC=docs/ops/PRODUCTIVE_PURE_STACK_DISPLAY_DECISION_HOST_BINDING_V1_OPTION_A_OWNER_RATIFICATION_V1.md
FORENSIC_CONTEXT=MISSING_SOURCE=40;NOT_BOUND=17
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
DASHBOARD_ROLE=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
RESULTV1_MAPPING_AUTHORIZED=false
NEW_TRADING_AUTHORITY_AUTHORIZED=false
RUNTIME_IMPLEMENTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
ARCHIVE_MUTATIONS=false
CORE_LOGIC_CHANGE=false
```

## 0. Binding effect

This document is the Owner ratification for **productive** Pure-Stack
input, config, and state authorities required before any of the five
blocked Pure-Stack Decisions can leave `MISSING_SOURCE` /
`BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT`.

It:

1. names the **canonical source authority** for every required field;
2. reuses existing pure DTOs, contracts, and kernel seams where they
   already fit exactly;
3. ratifies **new** config/state/producer authorities that do not yet
   exist as productive owners;
4. lists **forbidden** sources explicitly;
5. lists **Owner Values** that remain unresolved and therefore keep
   productive emission fail-closed.

It does **not**:

- implement runtime producers, config loaders, or state stores;
- mutate archives, dashboards, or trading logic;
- authorize Live, Testnet, orders, credentials, or real capital;
- authorize `ResultV1` → Pure-Stack mapping;
- create a second trading authority;
- invent numeric thresholds, formulas, or default scalars.

```text
DOCUMENT_STATUS=BLOCKED_OWNER_VALUES_REQUIRED
OWNERSHIP_MODEL_RATIFIED=true
PRODUCTIVE_EMISSION_AUTHORIZED=false
IMPLEMENTATION_SCAFFOLDING_AUTHORIZED=true
PRODUCTIVE_BINDING_AUTHORIZED=false
```

`IMPLEMENTATION_SCAFFOLDING_AUTHORIZED=true` means later, separately
authorized PRs may build typed producers/config/state surfaces that
**fail closed** until every listed Owner Value is ratified and bound.
It does **not** flip
`INPUT_AUTHORITY_*` flags or claim seven-Decision readiness.

## 1. Non-negotiable invariants

```text
INV_DASHBOARD_CONSUMER_ONLY=true
INV_NO_RESULTV1_CONVERSION=true
INV_NO_NEW_TRADING_AUTHORITY=true
INV_SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
INV_RISK_EXIT_SAFETY_INDEPENDENT_OF_DISPLAY_FAMILIES=true
INV_NO_ORDERS=true
INV_NO_SYNTHETIC_DEFAULTS=true
INV_NO_PARTIAL_COMPOSITION=true
INV_NO_PRESENTATION_FALLBACKS=true
INV_NO_CMC_VOLATILITY_AS_REALIZED_VOLATILITY=true
INV_NO_ACCOUNT_EQUITY_REMAP_TO_SLOT_EQUITY=true
```

## 2. Authority classes

| Class | Meaning |
|---|---|
| `EXISTING_CANONICAL` | Already present as pure DTO, contract, kernel candidate, or passthrough; may be **consumed** but is not yet a productive emitter for Pure-Stack host inputs |
| `NEW_TO_RATIFY` | Ownership/schema ratified here; productive implementation still required and blocked on Owner Values where noted |
| `FORBIDDEN` | Must never be used as productive authority |
| `OWNER_VALUE_REQUIRED` | Exact numeric/formula/enum value must be supplied by a later Owner decision before productive emission |

## 3. Existing surfaces reused (no parallel models)

| Surface | Path / symbol | Role under this ratification |
|---|---|---|
| Futures Input pure DTO | `src&#47;trading&#47;master_v2&#47;double_play_futures_input.py` | Sole Pure-Stack snapshot shape |
| Futures Input producer adapter (packet→DTO) | `src&#47;trading&#47;master_v2&#47;double_play_futures_input_producer.py` | Shape adapter only; **not** productive source authority |
| Survival pure DTO / evaluator | `src&#47;trading&#47;master_v2&#47;double_play_survival.py` | Sole envelope evaluate surface |
| Suitability pure DTO / projector | `src&#47;trading&#47;master_v2&#47;double_play_suitability.py` | Sole suitability project surface |
| Capital Slot pure DTO / evaluators | `src&#47;trading&#47;master_v2&#47;double_play_capital_slot.py` | Sole ratchet/release pure model |
| Composition pure composer | `src&#47;trading&#47;master_v2&#47;double_play_composition.py` | Sole composition decision surface |
| Capital Slot owner boundary | `tests&#47;ops&#47;test_master_v2_capital_slot_owner_boundary_contract_v0.py` | Confirms sole Capital Slot pure-model candidate |
| Arithmetic kernel seam | `tests&#47;ops&#47;test_master_v2_arithmetic_kernel_seam_fail_closed_contract_v0.py` | Canonical kernel candidate: `src&#47;execution&#47;paper&#47;futures_accounting.py` |
| Typed CMC volatility | `CanonicalMarketContextV1.canonical_volatility_estimate` | **Not** an alias for `FuturesVolatilityProfile.realized_volatility` |
| Transition passthrough | `transition_state` inside sole trading authority | Already authorized under OPTION_A |
| Fail-closed host builders | `src&#47;ops&#47;productive_pure_stack_display_decision_host_binding_v1&#47;` | Remain fail-closed until authorities + Owner Values land |
| Instrument metadata vocabulary | `docs&#47;ops&#47;specs&#47;FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md` | Field vocabulary for currencies / settlement |
| Market-data provenance vocabulary | `docs&#47;ops&#47;specs&#47;FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md` | Freshness / provenance vocabulary |
| Futures Input contracts | Futures Input Read Model + Producer Contract v0 | Non-authorizing schema/process boundary |
| Survival contract | Arithmetic Sequence Survival Contract v0 | Vocabulary; numeric gates explicitly out of that doc |
| Suitability contract | Strategy Suitability Projection Contract v0 | Vocabulary; names/registry non-authority |
| Capital Slot contract | Capital Slot Ratchet Release Contract v0 | Vocabulary; illustrative % **not** productive law |

## 4. Forbidden sources (global)

```text
FORBIDDEN_SOURCE_CMC_VOLATILITY_ESTIMATE_AS_REALIZED_VOLATILITY
FORBIDDEN_SOURCE_DASHBOARD_LABELS_OR_PRESENTATION_PROJECTIONS
FORBIDDEN_SOURCE_EVIDENCE_PACKS_AS_TRADING_INPUT_AUTHORITY
FORBIDDEN_SOURCE_SURVIVAL_RESULT_V1_MAPPING
FORBIDDEN_SOURCE_SUITABILITY_RESULT_V1_MAPPING
FORBIDDEN_SOURCE_COMPOSITION_RESULT_V1_MAPPING
FORBIDDEN_SOURCE_SCENARIO_REPLAY_FIXTURE_THRESHOLDS
FORBIDDEN_SOURCE_WEBUI_HARDCODED_LIMITS_OR_CONFIGS
FORBIDDEN_SOURCE_STRATEGY_NAME_OR_REGISTRY_LABEL_SIDE_INFERENCE
FORBIDDEN_SOURCE_SYMBOL_STRING_CURRENCY_OR_MARKET_TYPE_INFERENCE
FORBIDDEN_SOURCE_ACCOUNT_EQUITY_AS_SLOT_EQUITY
FORBIDDEN_SOURCE_SYNTHETIC_DEFAULT_SCALARS
FORBIDDEN_SOURCE_PARTIAL_COMPOSITION_OR_DISPLAY_FALLBACK
FORBIDDEN_SOURCE_PARALLEL_ARITHMETIC_KERNEL
FORBIDDEN_SOURCE_PARALLEL_TRADING_AUTHORITY
```

Scenario / test / WebUI scalars such as `profit_step_pct=0.10`,
`min_path_survival_ratio=0.5`, or `min_opportunity_score=0.2` are
**fixtures only**. They are **not** productive Owner Values under this
ratification.

---

## 5. FuturesInputSnapshot authority matrix

**DTO owner (shape):** `trading.master_v2.double_play_futures_input`  
**Productive producer owner (to implement):**
`trading.master_v2.productive_futures_input_snapshot_producer_v1`
(new; must run under / be authorized by
`run_integrated_offline_trading_logic_replay_v1`; packet adapter may be
reused for shape conversion only).

**Missing behaviour (global):** omit field → fail-closed readiness block
via `evaluate_futures_input_snapshot`; never invent defaults; never
claim `DATA_READY`.

### 5.1 Field authorities

| Field | Class | Canonical Source Authority | Unit / Semantics | Freshness | Validation | Missing behaviour |
|---|---|---|---|---|---|---|
| `candidate.base_currency` | NEW_TO_RATIFY | Venue-native instrument metadata record bound for the selected instrument (vocabulary: FUTURES_INSTRUMENT_METADATA_CONTRACT_V0 `base_currency`) | ISO-like currency code of base asset; explicit string | Must match instrument-metadata record as_of selected binding epoch | Non-empty; must equal metadata record; no symbol parse | `INSTRUMENT_METADATA_INCOMPLETE` / fail-closed |
| `candidate.quote_currency` | NEW_TO_RATIFY | Same venue-native instrument metadata record (`quote_currency`) | Quote currency of the contract | Same as base | Non-empty; equals metadata | fail-closed |
| settlement currency / rule | NEW_TO_RATIFY | Same record: `settle_currency` + `settlement_asset_known` / margin-settlement rule from instrument metadata | Settlement currency and explicit settle rule (linear/inverse etc. via `contract_type`) | Same as base | Futures/perp require explicit settle currency; unknown → fail-closed | fail-closed; no symbol inference |
| `provenance.freshness_state` | EXISTING_CANONICAL + OWNER_VALUE_REQUIRED | Market-data provenance producer feeding `FuturesMarketDataProvenanceStatus` (vocabulary: FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0) | Enum `fresh` / `stale` / `unknown` | Owner Value `OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS` required before productive `fresh` may be asserted | Must be explicit; stale/unknown block downstream | `FRESHNESS_STALE` / `FRESHNESS_UNKNOWN` |
| `volatility.volatility_regime` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | Dedicated regime label producer authorized by sole trading authority; **not** dashboard regime presentation | Versioned regime enum/string per Owner taxonomy | Tied to volatility observation window Owner Value | Only labels from ratified taxonomy | Leave `None` → `VOLATILITY_INCOMPLETE` for dynamic-scope paths |
| `volatility.atr_or_rolling_range` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | ATR/range producer under sole trading authority; window/unit Owner Values required | Price-units over Owner-defined window (not annualized) | Observation as_of must be fresh under freshness Owner Value | Finite; `> 0` when claimed; window documented on producer digest | `None` → volatility incomplete |
| `volatility.realized_volatility` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | Dedicated `RealizedVolatilityProfileProducerV1` under sole trading authority | Owner-defined horizon + unit (explicit); **not** CMC `volatility_estimate` / typed CMC carrier | Same freshness gate as ATR | Finite; unit/horizon present on digest; no silent annualization swap | `None` → volatility incomplete |
| `opportunity.opportunity_score` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | `OpportunityScoreProducerV1` under sole trading authority | Dimensionless score on Owner-defined scale | Tied to market observation freshness | Finite; scale documented | `None` allowed for futures readiness base path; capital-slot release paths that require it fail closed when missing at that layer |
| `opportunity.inactivity_score` / activity | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | Same opportunity producer family (`ActivityOrInactivityScoreProducerV1`) | Dimensionless; higher inactivity = less activity per Owner definition | Same | Explicit; no default zero meaning “active” | Missing → explicit incomplete for consumers that require it |

### 5.2 Additional FuturesInputSnapshot members (summary)

| Member | Authority class | Rule |
|---|---|---|
| `candidate.instrument_id` / `symbol` / `exchange` / `market_type` | NEW_TO_RATIFY | Venue-native instrument binding; `market_type` explicit; unknown fails closed |
| `instrument.*` completeness flags | NEW_TO_RATIFY | Instrument metadata status must be complete for productive claims |
| `provenance.*` | NEW_TO_RATIFY | Provenance complete for claimed prices/OHLCV/funding |
| `liquidity.*` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | Spread + volume/quote_volume required for capital-slot/suitability readiness; formula Owner Value for spread source |
| `derivatives.funding_*` | NEW_TO_RATIFY | Required for perpetual/swap; missing → `PERPETUAL_FUNDING_INCOMPLETE` |
| `ranking.*` | EXISTING_CANONICAL | Non-authoritative context only |
| `dashboard_label` / `ai_summary` | FORBIDDEN as authority | Display-only; never confer readiness |

### 5.3 Explicit non-aliases for volatility

```text
CMC.volatility_estimate != FuturesVolatilityProfile.realized_volatility
CMC.canonical_volatility_estimate != FuturesVolatilityProfile.realized_volatility
regime_presentation_projection != volatility_regime
feature_regime_pipeline_volatility != realized_volatility
ATR_IS_NOT_REALIZED_VOLATILITY=true
```

Reference: `MASTER_V2_CANONICAL_VOLATILITY_ESTIMATE_TYPED_CONSUMPTION_CONTRACT_V1`
non-alias section.

---

## 6. DoublePlaySurvivalEnvelope authority matrix

**DTO / evaluate owner:** `trading.master_v2.double_play_survival`  
**Productive envelope assembler:** new
`trading.master_v2.productive_survival_envelope_assembler_v1`, authorized
only by the sole trading authority.

**Forbidden:** any mapping from `SurvivalResultV1`, scenario fixtures, or
WebUI `_SURV_LIMITS`.

### 6.1 Producers

| Component | Class | Producer / Owner | Semantics |
|---|---|---|---|
| `ArithmeticFingerprint` | NEW_TO_RATIFY | Producer must be an authorized projection of the existing canonical Futures arithmetic kernel candidate `src&#47;execution&#47;paper&#47;futures_accounting.py` (seam already fail-closed / unwired). No parallel kernel. | Boolean completeness of contract/fee/slippage/funding/margin/liquidation/rounding models for the selected instrument |
| `LayerArithmeticStatus` (long + short) | NEW_TO_RATIFY | Same authorized arithmetic-kernel projection; long and short layers computed separately | Leverage, liquidation buffer, fee breakeven bps, adverse fill loss, funding profile, `is_perpetual` |
| `SequenceSurvivalMetrics` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | `SequenceSurvivalMetricsProducerV1` authorized by sole trading authority (pre-arm / governance path; not hot-path heavy recompute) | Path metrics per Survival Contract §7; metric definitions require Owner Values for exact functionals |
| `StateSwitchSurvivalLimits` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | Config owner: `CapitalAndSurvivalLimitsConfigV1` (see §8 family) / dedicated `StateSwitchSurvivalLimitsConfigV1` | Versioned thresholds; comparison operators fixed below |

### 6.2 Comparison operators (fixed; values not fixed)

| Metric field | Operator vs limit | Limit field |
|---|---|---|
| `path_survival_ratio` | `<` fails | `min_path_survival_ratio` |
| `early_loss_toxicity` | `>` fails | `max_early_loss_toxicity` |
| `margin_buffer_at_risk_99` | `<` fails | `min_margin_buffer_at_risk_99` |
| `sequence_fragility_index` | `>` fails | `max_sequence_fragility_index` |
| `liquidation_near_miss_rate` | `>` fails | `max_liquidation_near_miss_rate` |
| `governance_breach_frequency` | `>` fails | `max_governance_breach_frequency` |
| `chop_switch_survival_score` | `<` fails | `min_chop_switch_survival_score` |
| layer `max_effective_leverage` | `>` fails | `max_effective_leverage` |
| layer `min_liquidation_buffer` | `<` fails | `min_liquidation_buffer` |
| layer `expected_adverse_fill_loss` | `>` fails | `max_adverse_fill_loss` |

Units: ratios in `[0,1]` unless a later Owner Value explicitly ratifies
another unit on a named field; leverage dimensionless; buffers in the
same unit family as kernel margin buffer; adverse fill loss in the
kernel’s loss unit; fee breakeven in bps.

### 6.3 Config schema / versioning / restart / audit

```text
CONFIG_SCHEMA_NAME=state_switch_survival_limits.v1
CONFIG_OWNER=trading.master_v2.state_switch_survival_limits_config_v1
MIGRATION_RULE=fail_closed_on_unknown_schema_version;no_silent_field_defaulting
RESTART_SEMANTICS=limits_reloaded_from_versioned_config_only;no_in_memory_scenario_residue
AUDIT_SEMANTICS=persist_config_digest_and_producer_digests_with_envelope_decision
live_authorization_on_limits=must_be_false_or_evaluate_still_forces_false
```

Numeric limit fields are all `OWNER_VALUE_REQUIRED` (listed in §10).

---

## 7. SuitabilityProjectionInput authority matrix

**DTO / project owner:** `trading.master_v2.double_play_suitability`  
**Forbidden:** `SuitabilityResultV1` mapping; dashboard labels; strategy
name / registry-label side inference.

| Input field | Class | Canonical Source Authority | Missing / conflict behaviour |
|---|---|---|---|
| `StrategyMetadata.strategy_id` | EXISTING_CANONICAL | Opaque strategy identity from governed strategy catalog binding under sole trading authority | Missing id → fail-closed |
| `StrategyMetadata.declared_side` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | `StrategySideDeclarationAuthorityV1` — versioned explicit side declaration artifact; **not** inferred from name/family/ECM/Armstrong/dashboard | Unknown / absent → `DECLARED_SIDE_INCOMPLETE` / `UNKNOWN_SUITABILITY` |
| `StrategyMetadata.explicit_side_evidence` | NEW_TO_RATIFY | Same side-declaration artifact must set evidence bit explicitly when side is claimed | `false` with directional/both/neutral claims → fail-closed per projector |
| `StrategyMetadata` display fields | FORBIDDEN as authority | `dashboard_label`, `name_surface`, `registry_label`, AI summary are display/context only | Ignored for classification authority |
| `InstrumentIntelligenceSummary` | NEW_TO_RATIFY | Presence flags derived only from a **canonical** `FuturesInputSnapshot` readiness evaluation (volatility/liquidity/spread/funding/freshness present). No dashboard instrument cards. | Incomplete → `INSTRUMENT_INTELLIGENCE_INCOMPLETE` |
| `survival_envelope_allows` | NEW_TO_RATIFY | Bound exclusively from productive `SurvivalEnvelopeDecision.pre_authorization_eligible` of the same cycle | Must not be invented; conflict with survival decision → fail-closed |
| `survival_block_reasons` | NEW_TO_RATIFY | Passthrough of survival block reason codes (stringified) from same cycle | Empty only when survival allows |

Conflict rule: if side-declaration digest disagrees with any attempted
name-based hint, **declaration wins only when explicit evidence is
true**; otherwise fail closed to `UNKNOWN_SUITABILITY`. Names never win.

---

## 8. CapitalSlotConfig authority matrix

**Pure DTO owner:** `trading.master_v2.double_play_capital_slot.CapitalSlotConfig`  
**Productive config owner (new):**
`trading.master_v2.capital_slot_config_v1`  
**Schema:** `capital_slot_config.v1`  
**Default policy:** **no silent defaults**; missing field → fail-closed;
`live_authorization` must be `false` or ratchet/release reject via
`CONFIG_LIVE_AUTHORIZATION_CONTRADICTION`.  
**Migration:** unknown schema version → fail-closed; additive fields
require schema bump; no remapping from account equity config.

| Field | Unit | Allowed range (structural) | Default policy | Config Owner | Version / migration |
|---|---|---|---|---|---|
| `profit_step_pct` | fraction of effective slot base per step | finite; `> 0`; upper bound Owner Value | no default | `capital_slot_config.v1` | Owner Value `OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT` |
| `cashflow_lock_fraction` | fraction in `[0,1]` | `[0,1]`; with reinvest must sum to 1 within eps | no default | same | `OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION` |
| `reinvest_fraction` | fraction in `[0,1]` | `[0,1]`; sum-to-1 with lock | no default | same | `OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION` |
| `min_realized_volatility` | same unit family as productive realized vol | finite; `>= 0` | no default | same | `OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY` |
| `min_atr_or_range` | same unit family as productive ATR/range | finite; `>= 0` | no default | same | `OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE` |
| `max_time_without_cashflow_step` | integer time quanta (Owner-defined quantum) | integer; `>= 0`; `0` disables time-breach per pure model | no default | same | `OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP` + `OWNER_VALUE_CAPITAL_SLOT_TIME_QUANTUM` |
| `min_opportunity_score` | same scale as opportunity producer | finite | no default | same | `OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE` |
| `allow_auto_top_up` | bool | must be `false` until separate Owner GO for reserve top-up | forced fail-closed if true under current pure v0 semantics for reserve top-up | same | reserved; no productive top-up authorized |
| `live_authorization` | bool | must be `false` | forced false | same | contradiction blocks |

Illustrative “10%” language in the Capital Slot contract remains
**non-binding** and is **not** adopted as
`OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT`.

---

## 9. CapitalSlotState authority matrix

**Pure DTO owner:** `trading.master_v2.double_play_capital_slot.CapitalSlotState`  
**Productive state owner (new):**
`trading.master_v2.capital_slot_state_store_v1`  
**Persistence schema:** `capital_slot_state.v1`  
**Filename constant already reserved (non-productive):**
`capital_slot_state.v1.json` in the Pure-Stack host package — may be
reused only after this authority is implemented and Owner Values for
initialization are set.

| Field | Class | Authority / semantics |
|---|---|---|
| `initial_slot_base` | NEW_TO_RATIFY + OWNER_VALUE_REQUIRED | Explicit Owner initialization value for the selected future slot; never derived from ambient account equity |
| `active_slot_base` | NEW_TO_RATIFY | Monotone restart-safe; follows ratchet / loss-following pure rules only |
| `realized_or_settled_slot_equity` | NEW_TO_RATIFY | From futures accounting / settlement projection for **this slot** only; `None` → ratchet fail-closed; **no** remap from general account equity |
| `time_without_cashflow_step` / last cashflow step | NEW_TO_RATIFY | Persist last cashflow-step identity and counter; restart must reload atomically |
| `survival_allows_slot` | NEW_TO_RATIFY | Bound from productive survival decision of the cycle (same rule family as suitability) |
| state version | NEW_TO_RATIFY | `capital_slot_state.v1`; mismatch → fail-closed |
| cycle / session identity | NEW_TO_RATIFY | Persist `cycle_id` / trading-epoch / selected_future with state |

### 9.1 Persistence / restart / audit requirements

```text
ATOMIC_PERSISTENCE=required
MONOTONE_RESTART_SAFE=required
AUDIT_TRAIL=required_config_and_state_digests
NO_ACCOUNT_EQUITY_REMAP=true
INITIAL_STATE_EXPLICIT_FAIL_CLOSED=true
UNREALIZED_PNL_NOT_RATCHET_BASIS=true
```

Atomic write pattern must match existing host atomic replace semantics
(tempfile + `os.replace` + fsync) or an equivalent durable store under
the sole trading authority’s state root.

---

## 10. Unresolved Owner Values (exact names)

Productive emission of the corresponding fields remains **forbidden**
until each named value is Owner-ratified in a follow-on ratification
or config manifest bound by SHA.

```text
OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS
OWNER_VALUE_REALIZED_VOLATILITY_HORIZON
OWNER_VALUE_REALIZED_VOLATILITY_UNIT
OWNER_VALUE_REALIZED_VOLATILITY_FORMULA_ID
OWNER_VALUE_ATR_OR_RANGE_WINDOW
OWNER_VALUE_ATR_OR_RANGE_UNIT
OWNER_VALUE_ATR_OR_RANGE_FORMULA_ID
OWNER_VALUE_VOLATILITY_REGIME_TAXONOMY_ID
OWNER_VALUE_OPPORTUNITY_SCORE_SCALE
OWNER_VALUE_OPPORTUNITY_SCORE_FORMULA_ID
OWNER_VALUE_ACTIVITY_OR_INACTIVITY_SCORE_FORMULA_ID
OWNER_VALUE_LIQUIDITY_SPREAD_SOURCE_FORMULA_ID
OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID
OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID
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
OWNER_VALUE_STRATEGY_SIDE_DECLARATION_SCHEMA_ID
OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT
OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION
OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION
OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY
OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE
OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP
OWNER_VALUE_CAPITAL_SLOT_TIME_QUANTUM
OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE
OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE
```

No numeric literals for these values are ratified by this document.

---

## 11. Composition ratification

```text
COMPOSITION_OWNER=trading.master_v2.double_play_composition.compose_double_play_decision
PARTIAL_COMPOSITION=FORBIDDEN
PRESENTATION_FALLBACK=FORBIDDEN
```

`DoublePlayCompositionDecision` may be productively emitted **only** when
all of the following are present as **canonical** same-cycle artifacts:

1. `FuturesInputReadinessDecision` with downstream readiness required by
   the composition path under governance (at minimum: snapshot evaluated;
   blocked snapshot cannot be patched by display);
2. `TransitionDecision` + `resulting_side_state` (passthrough from sole
   trading authority);
3. `SurvivalEnvelopeDecision` from productive envelope;
4. `SuitabilityProjectionDecision` from productive projection input;
5. required Capital Slot decisions (`CapitalSlotRatchetDecision` and
   `CapitalSlotReleaseDecision`) whenever capital-slot gating is in
   scope for the productive host (this ratification requires them for
   seven-Decision productive readiness).

If any required input is missing: **no** composition decision object for
productive display/host emission; host remains
`BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT` / `MISSING_SOURCE`.

---

## 12. Machine-readable decision matrix

```text
DECISION_MATRIX_VERSION=1
# FORMAT: INPUT|FIELD_OR_COMPONENT|AUTHORITY_CLASS|SOURCE_OWNER|STATUS|NOTES

FuturesInputSnapshot|base_currency|NEW_TO_RATIFY|venue_native_instrument_metadata|OWNER_BOUND_PENDING_IMPL|no_symbol_inference
FuturesInputSnapshot|quote_currency|NEW_TO_RATIFY|venue_native_instrument_metadata|OWNER_BOUND_PENDING_IMPL|no_symbol_inference
FuturesInputSnapshot|settlement_currency_rule|NEW_TO_RATIFY|venue_native_instrument_metadata|OWNER_BOUND_PENDING_IMPL|settle_explicit
FuturesInputSnapshot|freshness_state|EXISTING_CANONICAL+OWNER_VALUE_REQUIRED|market_data_provenance_producer|BLOCKED_OWNER_VALUE|OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS
FuturesInputSnapshot|volatility_regime|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|regime_label_producer_trading_auth|BLOCKED_OWNER_VALUE|OWNER_VALUE_VOLATILITY_REGIME_TAXONOMY_ID
FuturesInputSnapshot|atr_or_rolling_range|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|atr_range_producer_trading_auth|BLOCKED_OWNER_VALUE|window_unit_formula
FuturesInputSnapshot|realized_volatility|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|realized_volatility_profile_producer_v1|BLOCKED_OWNER_VALUE|CMC_alias_forbidden
FuturesInputSnapshot|opportunity_score|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|opportunity_score_producer_v1|BLOCKED_OWNER_VALUE|formula_scale
FuturesInputSnapshot|activity_or_inactivity_score|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|activity_inactivity_score_producer_v1|BLOCKED_OWNER_VALUE|formula
DoublePlaySurvivalEnvelope|ArithmeticFingerprint|NEW_TO_RATIFY|futures_accounting_kernel_projection|OWNER_BOUND_PENDING_IMPL|reuse_kernel_candidate
DoublePlaySurvivalEnvelope|LayerArithmeticStatus|NEW_TO_RATIFY|futures_accounting_kernel_projection|OWNER_BOUND_PENDING_IMPL|long_and_short
DoublePlaySurvivalEnvelope|SequenceSurvivalMetrics|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|sequence_survival_metrics_producer_v1|BLOCKED_OWNER_VALUE|definitions
DoublePlaySurvivalEnvelope|StateSwitchSurvivalLimits|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|state_switch_survival_limits_config_v1|BLOCKED_OWNER_VALUE|all_limit_owner_values
SuitabilityProjectionInput|StrategyMetadata.strategy_id|EXISTING_CANONICAL|strategy_catalog_binding|OWNER_BOUND_PENDING_IMPL|opaque_id
SuitabilityProjectionInput|declared_side|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|strategy_side_declaration_authority_v1|BLOCKED_OWNER_VALUE|no_name_inference
SuitabilityProjectionInput|explicit_side_evidence|NEW_TO_RATIFY|strategy_side_declaration_authority_v1|OWNER_BOUND_PENDING_IMPL|explicit_bit
SuitabilityProjectionInput|InstrumentIntelligenceSummary|NEW_TO_RATIFY|futures_input_readiness_presence_flags|OWNER_BOUND_PENDING_IMPL|snapshot_only
SuitabilityProjectionInput|survival_envelope_allows|NEW_TO_RATIFY|survival_envelope_decision_same_cycle|OWNER_BOUND_PENDING_IMPL|no_invent
CapitalSlotConfig|profit_step_pct|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT
CapitalSlotConfig|cashflow_lock_fraction|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION
CapitalSlotConfig|reinvest_fraction|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION
CapitalSlotConfig|min_realized_volatility|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY
CapitalSlotConfig|min_atr_or_range|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE
CapitalSlotConfig|max_time_without_cashflow_step|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP
CapitalSlotConfig|min_opportunity_score|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_config_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE
CapitalSlotState|initial_slot_base|NEW_TO_RATIFY+OWNER_VALUE_REQUIRED|capital_slot_state_store_v1|BLOCKED_OWNER_VALUE|OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE
CapitalSlotState|active_slot_base|NEW_TO_RATIFY|capital_slot_state_store_v1|OWNER_BOUND_PENDING_IMPL|monotone_restart_safe
CapitalSlotState|realized_or_settled_slot_equity|NEW_TO_RATIFY|slot_settlement_projection_via_futures_accounting|OWNER_BOUND_PENDING_IMPL|no_account_equity_remap
CapitalSlotState|last_cashflow_step|NEW_TO_RATIFY|capital_slot_state_store_v1|OWNER_BOUND_PENDING_IMPL|atomic_audit
CapitalSlotState|survival_allows_slot|NEW_TO_RATIFY|survival_envelope_decision_same_cycle|OWNER_BOUND_PENDING_IMPL|same_cycle
CapitalSlotState|state_version|NEW_TO_RATIFY|capital_slot_state.v1|OWNER_BOUND_PENDING_IMPL|fail_closed_mismatch
CapitalSlotState|cycle_session_identity|NEW_TO_RATIFY|capital_slot_state_store_v1|OWNER_BOUND_PENDING_IMPL|persist_with_state
DoublePlayCompositionDecision|compose_gate|NEW_TO_RATIFY|compose_double_play_decision|OWNER_BOUND_PENDING_IMPL|no_partial_composition
TransitionDecision|passthrough|EXISTING_CANONICAL|transition_state_in_sole_trading_authority|AUTHORIZED_PASSTHROUGH|OPTION_A
```

---

## 13. Implementation order and dependency graph

### 13.1 Ordered implementation slices (docs → later code; this PR is docs-only)

```text
1. Owner Values ratification manifest (all OWNER_VALUE_* names)
2. Venue-native instrument metadata → Futures candidate currencies/settlement
3. Market-data provenance + freshness max-age binding
4. RealizedVolatility + ATR/range + regime producers (non-CMC alias)
5. Opportunity / activity score producers
6. Productive FuturesInputSnapshot assembler under sole trading authority
7. ArithmeticFingerprint + LayerArithmeticStatus projection from futures_accounting kernel
8. SequenceSurvivalMetrics producer + Survival limits config bind
9. StrategySideDeclarationAuthorityV1
10. SuitabilityProjectionInput assembler (binds survival_envelope_allows)
11. CapitalSlotConfig v1 loader (Owner Values)
12. CapitalSlotState store init + atomic persistence
13. Capital ratchet/release productive emission
14. Full Composition gate (no partial)
15. Only then: flip INPUT_AUTHORITY_* in host constants under separate GO
```

### 13.2 Dependency graph

```text
OwnerValuesManifest
  ├─► FreshnessMaxAge ─┐
  ├─► RealizedVolFormula ─┐
  ├─► AtrFormula ─────────┼─► FuturesInputSnapshotProducer ─┬─► InstrumentIntelligenceSummary
  ├─► RegimeTaxonomy ─────┘                                  │
  ├─► OpportunityFormulas ───────────────────────────────────┤
  │                                                          ├─► SuitabilityProjectionInput
  ├─► StrategySideDeclarationSchema ─────────────────────────┤         ▲
  │                                                          │         │
  ├─► SurvivalLimitValues ─► SurvivalLimitsConfig ─┐         │         │
  │                                                 ├─► SurvivalEnvelope ─► survival_envelope_allows
  └─► SequenceMetricDefinitions ─► SequenceMetricsProducer ─┘         │
                                                                      │
futures_accounting kernel ─► Fingerprint+LayerStatus ─────────────────┘
                                                                      │
CapitalSlot OwnerValues ─► CapitalSlotConfig ─┐                       │
Owner initial_slot_base ─► CapitalSlotState ──┼─► Ratchet+Release ────┤
SurvivalEnvelope ─► survival_allows_slot ─────┘                       │
                                                                      ▼
TransitionDecision(passthrough) + FuturesReadiness + Survival + Suitability + Capital
                                                                      ▼
                                                    DoublePlayCompositionDecision
                                                                      ▼
                                          Dashboard READ_ONLY_CONSUMER (no authority)
```

```text
DEPENDENCY_GRAPH_COMPLETE=true
```

---

## 14. Relation to OPTION_A and host flags

OPTION_A remains valid: PR #5724 scaffolding stays fail-closed and does
**not** claim productive Pure-Stack authority.

This ratification **does not** change:

```text
INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT=false
INPUT_AUTHORITY_SURVIVAL_ENVELOPE=false
INPUT_AUTHORITY_SUITABILITY_PROJECTION=false
INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG=false
INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT=false
INPUT_AUTHORITY_TRANSITION_DECISION_PASSTHROUGH=true
RESULTV1_MAPPING_AUTHORIZED=false
FIXTURE_FALLBACK_AUTHORIZED=false
DASHBOARD_ROLE=READ_ONLY_CONSUMER
```

Flipping any `INPUT_AUTHORITY_*=true` requires a **separate** Owner GO
after Owner Values + productive producers/config/state are evidence-
bound.

---

## 15. Explicit non-authorization

```text
RUNTIME_IMPLEMENTED=false
PRODUCTIVE_EMISSION_AUTHORIZED=false
RESULTV1_TO_PURE_STACK_MAPPING=UNAUTHORIZED
NEW_TRADING_AUTHORITY=UNAUTHORIZED
PARALLEL_ARITHMETIC_KERNEL=UNAUTHORIZED
DASHBOARD_AS_TRADING_INPUT=UNAUTHORIZED
CMC_VOLATILITY_AS_REALIZED_VOLATILITY=UNAUTHORIZED
ACCOUNT_EQUITY_AS_SLOT_EQUITY=UNAUTHORIZED
FIXTURE_THRESHOLDS_AS_PRODUCTIVE_LAW=UNAUTHORIZED
ORDERS=UNAUTHORIZED
LIVE=UNAUTHORIZED
TESTNET=UNAUTHORIZED
ARCHIVE_MUTATION=UNAUTHORIZED
```

---

## 16. References

- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_DISPLAY_DECISION_HOST_BINDING_V1_OPTION_A_OWNER_RATIFICATION_V1.md`
- `docs&#47;ops&#47;specs&#47;MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md`
- `docs&#47;ops&#47;specs&#47;MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md`
- `docs&#47;ops&#47;specs&#47;MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md`
- `docs&#47;ops&#47;specs&#47;MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md`
- `docs&#47;ops&#47;specs&#47;MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md`
- `docs&#47;ops&#47;specs&#47;FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md`
- `docs&#47;ops&#47;specs&#47;FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md`
- `docs&#47;ops&#47;specs&#47;MASTER_V2_CANONICAL_VOLATILITY_ESTIMATE_TYPED_CONSUMPTION_CONTRACT_V1.md`
- `docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`
