# Binding-candidate alignment index (derived, non-authoritative)

```text
DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
OCCURRENCE_BINDING_PROVEN_COUNT=0
PROVEN_PARENTAGE_COUNT=0
CURRENTNESS_ADJUDICATION_PERFORMED=false
SUPERSESSION_ADJUDICATION_PERFORMED=false
WINNER_SELECTED_COUNT=0
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

Navigation and provenance only. This directory does not replace the bound
Source, the bound Sidecar, the A–L retained transformation artifacts, or
the PR #6063 binding-disposition layer.

Candidate is never proven. Structuring is not canonization. Deterministic
derivation is not semantic truth. Git tracking is not authority.

Full T4 overlay shards are retained externally and checksummed here.

Regenerate with:

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_alignment_index --persist
```
