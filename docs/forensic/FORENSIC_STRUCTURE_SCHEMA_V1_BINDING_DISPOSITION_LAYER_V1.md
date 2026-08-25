# FORENSIC_STRUCTURE_SCHEMA_V1 Binding Disposition Layer

```text
DOCUMENT_ROLE=TECHNICAL_IMPLEMENTATION_NOTE
DOCUMENT_AUTHORITY=NONE
OUTPUT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
RESIDUAL_CLOSE_PERFORMED=false
NOT_MASTER_RUNBOOK=true
NOT_MAP_OF_TRUTH=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
```

Additive derived layer for residual cluster SW-R-002 / SW-R-004 / SW-R-009.
It does not replace stages A–L, the retained transformation dataset, the
bound Source, or the bound Sidecar.

Structuring is not canonization. Deterministic derivation is not semantic
truth. Git tracking is not authority.

## Bound inputs

Observational locators (not Desktop, not Downloads):

```text
SOURCE=/Users/frnkhrz/Documents/Peak_Trade/forensics/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md
SIDECAR=/Users/frnkhrz/Documents/Peak_Trade/forensics/derived/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.structure-v1.json
EXPECTED_SOURCE_SHA256=a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212
EXPECTED_SIDECAR_SHA256=6f2928e67d45de2162df1589de77ea530061652181ba6efd9a0f528ca7e6ad6e
```

## What this layer records

1. RELATION_DISPOSITION — multiclass mechanical/documentary/not-graph-edge labels
2. ENDPOINT_DISPOSITION — alias/overlay/marker/documentary/unbound classes
3. VIEW_PARENT_DISPOSITION — documentary hint vs ABSENT_UNINTERPRETED

OCCURRENCE_BINDING_PROVEN and PROVEN_PARENTAGE stay unused unless Source
explicitly proves them. Currently both counts are 0.

## Guard gaps closed

| Id | Forbidden implication | Active guard |
|----|------------------------|--------------|
| G1 | PREFIX_EPOCH_SUCCEEDS → CURRENT/SUPERSEDED/WINNER/dependency | `forbid_epoch_succession_currentness` |
| G2 | ABSENT view.parents → NO_PARENT/ROOT/CHILDLESS | `forbid_absent_view_parents_as_no_parent` |
| G3 | T4 directionality identity with Layer-3 relation_type | `forbid_t4_directionality_identity_with_layer3_relation_type` |
| G4 | T4 CONTAINS identity with WRAPPER_CONTAINS | `forbid_t4_contains_fusion_with_wrapper_contains` |
| G5 | Layer-3 ORDERED_BEFORE as T4 (source_src_id, target_ref) | `forbid_layer3_ordered_before_as_t4_src_target_pair` |
| G6 | SECTION_22→§22 or sidecar from_id as Source identity | `forbid_section_22_rewrite_as_source_identity`, `forbid_sidecar_dependency_subject_as_source_identity` |

Previously defined but unwired wrappers are now invoked from
`GuardProgram` and the retained-output audit path:

- `forbid_alias_occurrence_bind`
- `forbid_documentary_string_auto_resolution`
- `forbid_view_parents_parentage`
- `forbid_epoch_succession_currentness`

## Persist

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_disposition_layer --persist
```

Artifacts: `forensics&#47;derived&#47;FORENSIC_STRUCTURE_SCHEMA_V1_BINDING_DISPOSITION_V1&#47;`
