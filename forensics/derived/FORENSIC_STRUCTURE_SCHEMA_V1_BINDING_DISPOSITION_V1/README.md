# Binding disposition layer (derived, non-authoritative)

```text
DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
RESIDUAL_CLOSE_PERFORMED=false
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

Navigation and provenance only. This directory does not replace the bound
Source, the bound Sidecar, or the A–L retained transformation artifacts.
Structuring is not canonization. Deterministic derivation is not semantic
truth. Git tracking is not authority.

Regenerate with:

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_disposition_layer --persist
```
