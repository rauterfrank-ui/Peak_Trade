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
