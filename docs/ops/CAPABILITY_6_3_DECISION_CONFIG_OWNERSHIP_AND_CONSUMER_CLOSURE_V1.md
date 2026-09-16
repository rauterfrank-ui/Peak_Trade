# CAPABILITY_6_3 — Decision Config Ownership and Consumer Closure

**Capability ID:** `CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1`  
**Predecessor:** `CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1`  
**Core logic change:** `false`  
**Runtime authorization effect:** `NONE`

## Goal

Close ownership and consumer authority for runtime-relevant decision
configuration without changing any effective numeric trading value.

## Migrated keys

| Key | Effective value | Classification |
|-----|-----------------|---------------|
| `confirmation_epochs` | `2` | `CANONICAL_RUNTIME_CONFIG` |
| `up_distance` | `200.0` | `CANONICAL_RUNTIME_CONFIG` |
| `adverse_exit_distance` | `80.0` | `CANONICAL_RUNTIME_CONFIG` |
| `reversal_distance` | `120.0` | `CANONICAL_RUNTIME_CONFIG` |

Canonical typed owner:

- Config: `config/ops/canonical_decision_runtime_config_v1.toml`
- Package: `src/ops/decision_config_ownership_and_consumer_closure_v1/`
- Productive consumer: wallclock bridge v1
  (`decision_economics_cycle_bridge_v1.py`)

## Review-only (not migrated)

| Key | Classification | Reason |
|-----|----------------|--------|
| `PRICE_PATH_MAX_LEN` | `IMMUTABLE_DOMAIN_CONSTANT` | Single host buffer constant; no fallback ambiguity |
| `fee_rate_bps` | `EXECUTION_MODEL_CONFIG` | Portfolio/execution params; not decision-path drift |
| `slippage_bps` | `EXECUTION_MODEL_CONFIG` | Portfolio/execution params; not decision-path drift |

## Invariants

```text
CONFIG_RUNTIME_DRIFT=false_for_in_scope_runtime_values
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
NO_SILENT_FALLBACK=true
ONE_CONFIG_OWNER_PER_RUNTIME_VALUE=true
NO_PARALLEL_CONFIG_AUTHORITY=true
CORE_LOGIC_CHANGE=false
```

## Evidence

`docs/evidence/capability_6_3_decision_config_ownership_and_consumer_closure_v1/`

Generator:

`scripts/ops/generate_capability_6_3_evidence_v1.py`

## Owner decision persist (docs-only, not numeric)

Master Runbook §9.2.1 and
`docs/ops/specs/CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_OWNER_DECISION_V1.md`
record Owner target authority for **future** Cap 6.3 distance semantics:

```text
CAP63_UNIT_CLASS=DYNAMICALLY_DERIVED
CAP63_VALUE_SCOPE=DYNAMICALLY_DERIVED
CAP63_CROSS_INSTRUMENT_VALIDITY=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CAP63_NORMALIZATION_JOIN_REQUIRED=REPLACED_BY_DYNAMIC_DERIVATION
MIN_SCOPE_BAND_IN_SCOPE=NO_KEEP_SEPARATE_OWNER
```

Master Runbook §9.2.2 and
`docs/ops/specs/CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1.md`
record the TARGET derived-distance formula/producer **identity** as
authority-ready contract only (`derive_scope_event_distances_v1`
unimplemented; seam unbound). That persist does **not** change effective
numeric values, bind MODEL_C, or authorize a freeze-exception.

Master Runbook §9.2.3 and
`docs/ops/specs/CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md`
record Cap 6.2 digest retarget and Cap 6.5 adverse consumer identity after
later generator-input retirement (docs-only). Cap 6.5 remains a consumer of
derived OQ-C2 adverse; profit-protection remains Cap 6.5 own `200.0`. That
persist does **not** change effective numeric values, bind MODEL_C, or
authorize a freeze-exception.

This capability document does **not** change effective numeric values
`200.0` / `80.0` / `120.0`. MODEL_B remains CURRENT. MODEL_C remains
unbound. Freeze-exception is not authorized. `min_scope_band` is not a
Cap 6.3 key.
