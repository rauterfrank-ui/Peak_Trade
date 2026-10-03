---
title: "Scope Init min/max_scope_band Semantic Class Owner Decision v1"
status: "OWNER_DECISION_PERSISTED_DOCS_ONLY"
owner: "trading.master_v2.canonical_scope_initialization_v1"
last_updated: "2026-09-17"
docs_token: "DOCS_TOKEN_SCOPE_INIT_MIN_MAX_SEMANTIC_CLASS_OWNER_DECISION_V1"
---

# Scope Init min/max_scope_band Semantic Class Owner Decision v1

Canonical persist of the Owner classification captured under
`OWNER_GO_BOUNDED_SCOPE_INIT_MIN_MAX_SEMANTIC_CLASS_DECISION_DOCS_ONLY_V1`.

Semantic authority for these two fields lives in Master Runbook §9.2.10.
This file is the decision record and navigation twin. It is **not** a second
numeric owner, **not** a Cap 6.3 persist, **not** a runtime bind, and **not**
numeric calibration of `50.0` / `500.0`.

```text
DOCUMENT_CLASS=OWNER_DECISION_RECORD_DOCS_ONLY
OWNER_GO=OWNER_GO_BOUNDED_SCOPE_INIT_MIN_MAX_SEMANTIC_CLASS_DECISION_DOCS_ONLY_V1
OWNER_GO_STATUS=CONSUMED
RECOVERY_WP=SCOPE_INIT_MIN_MAX_SEMANTIC_CLASS_RECOVERY_V1
RECOVERY_VERDICT=B
RECOVERY_CLASS_WAS=GENUINELY_UNSPECIFIED
AUTHORITY_CLASS=R1_OFFLINE_DOCS_ONLY
DECISION_KIND=DIMENSIONAL_IDENTITY_ONLY
EXPECTED_ORIGIN_MAIN=e93495de691455d8f27a269452ca0833e9fd6724
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Owner fields persisted

```text
SCOPE_INIT_MIN_MAX_UNIT_CLASS=PRICE_DISTANCE_BOUNDS
MIN_SCOPE_BAND_ROLE=LOWER_BOUND
MAX_SCOPE_BAND_ROLE=UPPER_BOUND
BOUNDED_QUANTITY=INITIAL_VOLATILITY_DISTANCE
DIMENSIONAL_DOMAIN=SAME_PRICE_DISTANCE_DOMAIN_AS_VOL_TIMES_REFERENCE_PRICE
MIN_MAX_SAME_CLASS=true
OWNER=CanonicalScopeInitializationPolicyV1
OWNER_SURFACE=_default_policies
MIN_SCOPE_BAND_OWNER=NOT_CAP63
MIN_SCOPE_BAND_IN_SCOPE=NO_KEEP_SEPARATE_OWNER
```

## Semantics (dimensional identity only)

Both fields bound `initial_volatility_distance`.

```text
typed_vol_unit=PER_BAR_DECIMAL_RETURN_VOLATILITY
initial_volatility_distance = typed_volatility * reference_price
scope_band = clamp(initial_volatility_distance, min_scope_band, max_scope_band)
```

- `min_scope_band` is the lower bound of the permitted price-distance interval.
- `max_scope_band` is the upper bound of the same permitted price-distance interval.
- Values are expressed in the same price-distance domain as
  `initial_volatility_distance`, `scope_band`, and the resulting
  `reference_price ± scope_band` boundaries.

This classification describes **dimensional identity only**.

```text
NUMERIC_CALIBRATION_ADJUDICATED=false
CURRENT_50_500_CHANGED=true
CURRENT_50_500_COMMENSURABILITY=UNADJUDICATED
INSTRUMENT_NORMALIZATION_AUTHORIZED=false
THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false
SCOPE_INITIALIZATION_FORMULA_CHANGED=false
PRICE_DISTANCE_BOUNDS_IMPLIES_MAGNITUDE=false
VOL_TIMES_PRICE_REQUIRES_MIN_MAX_TO_SCALE=false
```

It does **not** declare the CURRENT numeric literals `50.0` / `500.0`
economically appropriate, instrument-commensurate, volatility-relative,
normalized, tick-derived, safety-calibrated, or legacy-compatible.

## Productive scope policy (CURRENT after instrument-relative cutover v1)

Bounded-policy fields on `CanonicalScopeInitializationPolicyV1` remain the owner type for
**explicit legacy absolute** modes. The **CURRENT productive** integrated-replay / core-bridge
path injects `default_instrument_relative_scope_initialization_policy_v1()` (σ×mark magnitude;
no legacy [50,500] clamp on that path).

```text
PRODUCTIVE_SCOPE_POLICY=canonical_scope_initialization_policy_instrument_relative_v1
PRODUCTIVE_SCOPE_MAGNITUDE=sigma_times_mark
RAW_SCOPE_CANONICAL_OWNER=compute_raw_volatility_times_price_scope_distance_v1
LEGACY_ABSOLUTE_50_500_ON_PRODUCTIVE_PATH=false
CURRENT_50_500_CHANGED=true
SCOPE_INITIALIZATION_FORMULA_CHANGED=false
RUNTIME_BEHAVIOR_CHANGED=true
PRODUCTIVE_BRIDGE_OWNER_SURFACE=canonical_core_runtime_integration_bridge_v0._default_policies
PARITY_HARNESS_OWNER_SURFACE=integrated_vs_scenario_replay_full_system_parity_harness_v0
CUTOVER_EVIDENCE_PACKAGE=evidence/research/raw_scope_instrument_relative_cutover_v1
```

Supported non-default explicit absolute calibration (mechanics tests / legacy mode):

```text
min_scope_band=50.0
max_scope_band=500.0
EXPLICIT_LEGACY_BOUNDED_POLICY_SUPPORTED=true
```

## Historical owner persist baseline (pre-cutover classification record)

```text
CURRENT_50_500_COMMENSURABILITY=UNADJUDICATED
SCOPE_INITIALIZATION_FORMULA_CHANGED=false
TYPED_VOL_UNIT=PER_BAR_DECIMAL_RETURN_VOLATILITY
NEUTRAL_ARMED_TRAILING_REFRESH=false
OQ_C1_BOUND=false
OQ_C2_BOUND=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
GENERATOR_INPUT_RETIREMENT_AUTHORIZED=false
SECTION_9_2_9_METADATA_TRACK=ORTHOGONAL
CAP65_PROFIT_PROTECTION_OWNER=SEPARATE
CAP63_AUTHORITY_CHANGED=false
CAP65_AUTHORITY_CHANGED=false
MODEL_B_STATUS=PRESERVE_AS_CURRENT_BASELINE
MODEL_C_BOUND=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
up_distance=200.0
adverse_exit_distance=80.0
reversal_distance=120.0
PROFIT_PROTECTION_DISTANCE=200.0
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
REAL_VENUE_POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
MAX_POSITIONS=1
```

## Explicit non-authorizations

```text
CONFIG_MUTATION_AUTHORIZED=false
SRC_RUNTIME_MUTATION_AUTHORIZED=false
NUMERIC_MIGRATION_AUTHORIZED=false
PERCENT_PRICE_NORMALIZATION_AUTHORIZED=false
ATR_NORMALIZATION_AUTHORIZED=false
TICK_NORMALIZATION_AUTHORIZED=false
MULTIPLIER_NORMALIZATION_AUTHORIZED=false
DERIVE_V1_BIND_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
TOML_RETIREMENT_AUTHORIZED=false
CAP63_OWNER_MERGE_AUTHORIZED=false
CAP65_OWNER_MERGE_AUTHORIZED=false
NEUTRAL_ARMED_TRAILING_MUTATION_AUTHORIZED=false
C3_C4_SIDESTATE_ENTRY_EXIT_MUTATION_AUTHORIZED=false
S6_AUTHORIZED=false
REACHABILITY_REPAIR_AUTHORIZED=false
```

## Consequence (classification does not repair reachability)

The semantic classification alone does **not** repair reachability.

With CURRENT literals, the following remains possible / current forensic
behavior:

```text
initial_volatility_distance≈0.0025
→ clamp(..., 50.0, 500.0)=50.0
→ current_hysteresis_band=50.0
```

That numeric outcome is **not** re-adjudicated here.

```text
NEXT_UNRESOLVED_DEPENDENCY=NONE_FOR_BOUNDED_CUTOVER_V1
EXACT_NEXT_OWNER_GO_TOKEN=NOT_MINTED
NEXT_NAMED_OPEN_GATE=SCOPE_PRODUCTIVE_IR_CUTOVER_IMPLEMENTATION_V1
NEXT_NAMED_OPEN_GATE_IS_NOT_AN_OWNER_GO_TOKEN=true
NUMERIC_POLICY_QUESTION_ANSWERED=true
HARD_STOP_AFTER_THIS_PERSIST=false
IMPLEMENTATION_READY=true
BOUNDED_CUTOVER_REQUIRES_SEPARATE_OWNER_MERGE_GO=true
```
