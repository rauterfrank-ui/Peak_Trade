<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# Schema Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

SCHEMA is not automatically DATA_CONTRACT or dataclass. Relations recorded only if proven.

```text
SCHEMA_ENTITY_COUNT=5
SCHEMA_FIELD_INVENTORY_COMPLETE=false
SCHEMA_CENSUS_COMPLETE=true
```

Drill-down census: `docs/system_atlas/census/schema_field_inventory.yaml`.

| id | name | schema_kind | status | epistemic | evidence |
| --- | --- | --- | --- | --- | --- |
| SCHEMA:bound_instrument_dataclass_v1 | BoundInstrumentV1 dataclass shape | python_dataclass_implicit_schema | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/single_selected_future_runtime_binding_v1/models_v1.py'] |
| SCHEMA:gfu_snapshot_v1 | governed_futures_universe_snapshot.v1 | evidence_snapshot_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/governed_futures_universe_producer_v1/constants_v1.py', 'src/ops/gover |
| SCHEMA:ranking_snapshot_v1 | productive_futures_ranking_snapshot.v1 | evidence_snapshot_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/productive_futures_ranking_producer_v1/constants_v1.py', 'src/ops/prod |
| SCHEMA:runtime_binding_v1 | single_selected_future_runtime_binding.v1 | runtime_binding_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/single_selected_future_runtime_binding_v1/constants_v1.py', 'src/ops/s |
| SCHEMA:single_selected_future_selection_v1 | single_selected_future_selection.v1 | selection_snapshot_serialization | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW | ['src/ops/single_selected_future_policy_v1/constants_v1.py', 'src/ops/single_sel |

