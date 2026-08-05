# Stage-2 Surface B Regime Coverage Producer v1

```text
DOCUMENT_TYPE=DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER_SPEC
DOCUMENT_VERSION=1
STATUS=IMPLEMENTED_AUTHORIZE_DETAILS_BOUND
CAPABILITY_SCOPE=SURFACE_B_REGIME_COVERAGE_PRODUCER_V1
OWNER_IMPL_GO_BASE_SHA=52af83870a775ee9a4647107273964fa4857322b
PACKAGE=src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/
DECISION=docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md
AUTHORITY_SURFACE=B
VERSIONED_PRODUCER_ID=productive_pure_stack_stage2_surface_b_regime_coverage_producer/v1
TIME_BASIS=EVENT_TIME_PT1M_FINALIZED_BAR_CLOSE_UTC
PIT_SAFE=true
DETERMINISTIC=true
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
PRODUCTIVE_EMISSION=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
NO_INVENTED_THRESHOLDS=true
NO_INVENTED_LOOKBACKS=true
NO_INVENTED_COVERAGE_COUNTS=true
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS=false
TESTNET=false
LIVE=false
```

## 1. Purpose

Provide the dedicated, versioned, deterministic, PIT-safe Surface-B regime
coverage producer authorized by `DEC_REGIME_COVERAGE_PRODUCER` without inventing
Owner numeric thresholds or campaign coverage counts.

## 2. Package layout

```text
src/ops/productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1/
  __init__.py
  constants_v1.py
  models_v1.py
  label_semantics_v1.py
  pit_rules_v1.py
  digest_contract_v1.py
  determinism_contract_v1.py
  reproducibility_contract_v1.py
  boundary_guards_v1.py
  producer_v1.py
```

## 3. Label policy under unset thresholds

While `threshold_authority_ref=OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1` and
`lookback_window_authority_ref=OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1`:

- complete finalized bars → `missing`
- incomplete inputs → `unknown`
- `low` / `mid` / `high` classification without Owner thresholds is forbidden
- `coverage_counts` and `regime_coverage_instance` remain null

## 4. PIT / determinism

- event time must be PT1M bucket open
- observations after exclusive as-of tip are rejected
- unfinalized bars are rejected
- identical inputs reproduce identical digests and observation sequences

## 5. Explicit non-effects

```text
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
RAW_INPUT_PACK_CREATED=false
CAMPAIGN_STARTED=false
REGIME_COVERAGE_PRODUCER_AVAILABLE=false
PRODUCTIVE_NUMERIC_VALUES_SET=0
TRADING_LOGIC_CHANGED=false
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS_TESTNET_LIVE=false
```
