# Derived forensic transformation artifacts

```text
DOCUMENT_ROLE=DERIVED_FORENSIC_STRUCTURE
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SIDECAR_AUTHORITY=NONE
OUTPUT_IS_CANONICAL=false
OUTPUT_IS_SOURCE_REPLACEMENT=false
OUTPUT_IS_ADJUDICATED_TRUTH=false
OUTPUT_IS_MASTER_RUNBOOK=false
OUTPUT_IS_MAP_OF_TRUTH=false
CANONICALIZATION_PERFORMED=false
AUTHORITY_PROMOTION_PERFORMED=false
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

This directory holds **derived, non-authoritative** transformation reports
for FORENSIC_STRUCTURE_SCHEMA_V1. A more complete structure does not
create authority.

The bound source and sidecar remain outside git. Observational locators
are recorded in `transformation_manifest.json`. Historical Desktop or
Downloads strings inside the source stay historical strings.

## Git persistence

Reports and the transformation manifest are git-tracked here.

The full transformed dataset shards are too large for a reviewable git
blob. They are generated to the external derived directory and checksummed
in `transformation_manifest.json`.

```text
DATASET_GIT_PERSISTENCE=MANIFEST_ONLY
REGENERATION_COMMAND=./scripts/pt scripts/ops/run_forensic_structure_schema_v1_transformer.py --persist-retained-derived
```

## Residuals

SW-R-001 through SW-R-015 and DR-001, DR-002, DR-003, DR-006, DR-007,
DR-008 remain `OPEN`. Transformation success does not close a residual.
This output does not claim `RESOLVED_BY_TRANSFORMATION`.
