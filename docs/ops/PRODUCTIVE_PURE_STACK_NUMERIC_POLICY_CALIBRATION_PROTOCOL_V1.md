# Productive Pure-Stack Numeric Policy Calibration Protocol v1

```text
DOCUMENT_TYPE=NUMERIC_POLICY_SHADOW_CALIBRATION_PROTOCOL
DOCUMENT_VERSION=1
STATUS=PROTOCOL_RATIFIED_NO_PRODUCTIVE_NUMERIC_VALUES
BASELINE_ORIGIN_MAIN_SHA=631dca43601e4efad53a35c19ddf9bf70ebfd177
TWO_STAGE_RATIFICATION=docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_TWO_STAGE_RATIFICATION_V1.md
STRUCTURAL_MANIFEST=docs/ops/PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json

ORDERS_ALLOWED=false
TESTNET_ACTIVATION=false
LIVE_ACTIVATION=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
RUNTIME_PRODUCTIVE_BINDING=false
AUTO_PROMOTION_TO_PRODUCTIVE_CONFIG=false
RESULTV1_MAPPING_AUTHORIZED=false
DASHBOARD_ROLE=READ_ONLY_CONSUMER
SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1
INPUT_AUTHORITY_REMAINS_FALSE=true
PRODUCTIVE_NUMERIC_VALUES_SET=0
```

## 0. Purpose

This protocol defines the **only** admissible path to propose numeric values for
tokens classified `NUMERIC_CALIBRATION_REQUIRED` in the structural manifest.

It is a **no-order**, **fail-closed**, **reproducible shadow** process. Outputs
are Evidence artifacts. They must not become productive config, flip
`INPUT_AUTHORITY_*`, activate Stage-1 producers productively, mutate archives as
authority, or alter the dashboard beyond read-only consumption of Evidence
labels.

## 1. Scope

**In scope (calibration candidates only):**

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

**Out of scope / already structural:**

- All `STRUCTURAL_RATIFIED` tokens from Stage 1
- `OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION` (mechanical coupling only)

**Hard exclusions:**

- Fixtures, scenario replay scalars, WebUI hardcoded limits
- Dashboard / presentation projections as calibration truth
- `CMC.volatility_estimate` as `realized_volatility`
- ResultV1 → Pure-Stack mapping
- Optimization on isolated Sharpe or isolated profit
- Live / Testnet / orders / credentials / real capital

## 2. Binding to Stage-1 definitions

Every calibration run must pin:

1. Structural manifest SHA / digest
2. Two-stage ratification document SHA
3. Exact Stage-1 definition IDs used for features (realized vol, ATR, opportunity,
   activity, spread, sequence metric set, path-survival definition, time quantum)
4. Sole Trading Authority code SHA
5. Dataset provenance digests

If any Stage-1 ID is missing or mismatched: **abort fail-closed** (no candidate
numbers).

## 3. Mandatory protocol elements

### 3.1 Versioned dataset / observation provenance

- Stable `dataset_id`, instrument_id, exchange, market_type, bar interval
- Event-time ranges, source identifiers, freshness metadata
- Explicit write/cache flags; no silent cache mutation as truth
- Digest of the observation pack included in the Evidence manifest

### 3.2 Instrument and market-regime stratification

- Stratify by instrument and by Stage-1 taxonomy labels when available
  (`low|mid|high|unknown`), plus explicit missing-regime stratum
- Report metrics per stratum; no pooled-only claim of stability

### 3.3 Train / calibration / validation separation

- Disjoint time segments: train (optional exploratory), calibration (threshold
  proposal), validation (locked evaluation)
- No peeking validation labels into calibration selection
- Hold out at least one forward validation segment

### 3.4 Walk-forward evaluation

- Rolling or expanding walk-forward folds with frozen Stage-1 definitions
- Publish fold-level primary metrics and threshold candidates
- Fail closed if fold digests are incomplete

### 3.5 Bootstrap or Monte-Carlo confidence intervals

- Resample paths or fold residuals under a documented seed and method ID
- Report interval estimates for primary safety metrics
- Seed + method ID recorded in Evidence

### 3.6 Stress cases

Mandatory stress packs (documented, versioned):

- Observation gaps / missing bars
- Staleness near and beyond candidate freshness ages
- Spread expansion / crossed book
- Volatility shocks (high realized vol / ATR)
- Liquidation near-miss path families
- Chop / rapid switch clusters (for sequence metrics)

### 3.7 Sensitivity analysis per threshold

- For each candidate token, vary the proposed number across a documented grid
- Record how primary safety metrics move
- Identify brittle cliffs (small Δthreshold → large ΔFalse-Allow)

### 3.8 Stability across instruments and time segments

- Require qualitative consistency of safety ranking across instruments and
  walk-forward folds
- Instability → candidate rejected (not auto-averaged into production)

### 3.9 No isolated Sharpe / profit optimization

Forbidden objective as sole selection criterion:

```text
maximize Sharpe
maximize profit
maximize trade count
```

Economic metrics are **secondary** and may only break ties among candidates that
already pass primary safety gates.

### 3.10 Primary safety metrics

```text
block_allow_rate
false_allow_rate
false_block_rate
path_survival
early_loss_toxicity
liquidation_near_miss_rate
governance_breach_frequency
effective_leverage
liquidation_buffer
adverse_fill_loss
```

Definitions of these metrics in a calibration run must reference Stage-1 sequence
and arithmetic projection IDs where applicable.

### 3.11 Secondary economic metrics

```text
profit_factor
max_drawdown
turnover
fees
slippage
opportunity_cost
```

Secondary only; cannot override failed primary safety gates.

### 3.12 Explicit out-of-sample acceptance criteria

Each calibration Evidence pack must declare machine-readable acceptance rules,
for example (illustrative structure — **not** productive thresholds):

```text
ACCEPT_IF:
  validation.false_allow_rate <= DECLARED_MAX_FALSE_ALLOW
  validation.path_survival_ci_lower >= DECLARED_MIN_PATH_SURVIVAL_CI
  stress_pack.all_required_cases_executed = true
  stage1_definition_digests_match = true
ELSE:
  REJECT_FAIL_CLOSED
```

The numeric `DECLARED_*` acceptance bounds used **inside a calibration pack**
are Evidence hyperparameters for that pack only. They are **not** productive
Owner Values and do not set `OWNER_VALUE_*` tokens.

### 3.13 Separate Owner decision per productive number

Promotion path:

```text
Calibration Evidence (shadow)
  → per-token Owner decision record
  → productive config bind (separate PR / GO)
  → only then may INPUT_AUTHORITY considerations be revisited
```

No batch silent promotion. `REINVEST_FRACTION` still derives only from signed-off
`CASHFLOW_LOCK_FRACTION`.

### 3.14 Full audit trail

Every Evidence pack must include:

```text
config_digest
code_sha
structural_manifest_digest
stage1_definition_id_set
dataset_provenance_digest
seed_and_method_ids
fold_digests
candidate_token_values (proposed only)
acceptance_verdict
operator_notes
NO_ORDER_PROOF=true
```

## 4. Freshness calibration special rule

`OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS`:

- Calibrate against Futures Input readiness / safety outcomes
- Must not reuse or imply CMC Numeric-Max-Age Alpha enforcement
- Demoted CMC max-age research remains non-authorizing for this token

## 5. Capital-slot calibration special rules

- `INITIAL_SLOT_BASE` must not be remapped from ambient account equity
- `MIN_REALIZED_VOLATILITY` / `MIN_ATR_OR_RANGE` / `MIN_OPPORTUNITY_SCORE` must use
  Stage-1 units/scales exactly
- `MAX_TIME_WITHOUT_CASHFLOW_STEP` counts `SOLE_TRADING_AUTHORITY_CYCLE_INDEX`
  quanta
- `PROFIT_STEP_PCT` and `CASHFLOW_LOCK_FRACTION` are economic policy; secondary
  metrics may inform but primary safety gates dominate

## 6. Survival-limit calibration special rules

- Comparison operators remain those ratified in the parent Input Authorities
  ratification (not recalibrated)
- Metric functionals remain Stage-1 definition IDs
- Kernel projection must reuse the canonical futures accounting kernel candidate;
  no parallel kernel

## 7. Fail-closed defaults for this protocol

```text
IF stage1_defs_missing OR provenance_incomplete OR oos_fail OR stress_incomplete:
  CANDIDATE_STATUS=REJECTED
  PRODUCTIVE_NUMERIC_VALUE=null
  INPUT_AUTHORITY_UNCHANGED=false_flags_remain
```

## 8. Explicit non-authorization

```text
SHADOW_ONLY=true
PRODUCTIVE_CONFIG_WRITE=UNAUTHORIZED
INPUT_AUTHORITY_FLIP=UNAUTHORIZED
ORDERS=UNAUTHORIZED
LIVE=UNAUTHORIZED
TESTNET=UNAUTHORIZED
ARCHIVE_AUTHORITY_MUTATION=UNAUTHORIZED
DASHBOARD_AUTHORITY_EFFECT=NONE
AUTO_PROMOTION=UNAUTHORIZED
```

## 9. References

- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_TWO_STAGE_RATIFICATION_V1.md`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json`
- `docs&#47;ops&#47;PRODUCTIVE_PURE_STACK_INPUT_AUTHORITIES_OWNER_RATIFICATION_V1.md`
- `docs&#47;runbooks&#47;canonical&#47;PEAK_TRADE_MASTER_RUNBOOK.md`
